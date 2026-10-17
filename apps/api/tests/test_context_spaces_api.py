"""Real HTTP routes/service/policy and signed OIDC tokens; test-only metadata store."""

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from app.api.security import SecurityBindings
from app.composition import ApplicationServices
from app.context.service import ManagedContextService
from app.core.models import ContextId, ContextSpace, ContextStorageUnavailable, SubjectId
from app.main import create_app
from app.policy.owner import OwnerPolicyService
from tests.test_oidc_security import build_auth, token

ALICE, BOB = SubjectId(str(uuid4())), SubjectId(str(uuid4()))


def headers(subject="external-alice", **claims):
    return {"Authorization": "Bearer " + token(sub=subject, **claims)}


class MemorySpaces:
    def __init__(self):
        self.rows = {}
        self.reads = []

    async def owner_for(self, id):
        row = self.rows.get(id)
        return row.owner_id if row else None

    async def create(self, *, subject_id, name):
        now = datetime.now(timezone.utc)
        row = ContextSpace(id=ContextId(str(uuid4())), owner_id=subject_id, name=name,
                           status="active", created_at=now, updated_at=now)
        self.rows[row.id] = row
        return row

    async def list_ids(self, *, subject_id, limit, after_id):
        return tuple(id for id in sorted(self.rows)
                     if self.rows[id].owner_id == subject_id and (after_id is None or id > after_id))[:limit]

    async def read(self, *, subject_id, context_id):
        self.reads.append(context_id)
        return self.rows.get(context_id)

    async def rename(self, *, subject_id, context_id, name):
        row = replace(self.rows[context_id], name=name, updated_at=datetime.now(timezone.utc))
        self.rows[context_id] = row
        return row


@pytest.fixture
def api():
    repo = MemorySpaces()
    auth, _ = build_auth(mapping={"external-alice": ALICE, "external-bob": BOB})
    policy = OwnerPolicyService(owner_for=repo.owner_for)
    app = create_app(services=ApplicationServices(context=ManagedContextService(repository=repo, policy=policy),
                                                 policy=policy),
                     security=SecurityBindings(authenticate=auth.authenticate, policy=policy))
    with TestClient(app) as client:
        yield client, repo


def test_alice_creates_lists_opens_renames_and_bob_cannot_access(api):
    client, repo = api
    r = client.post('/context-spaces', json={"name": "Space A 🧭"}, headers=headers())
    assert r.status_code == 201
    a = r.json()
    assert a['owner_id'] == ALICE and a['status'] == 'active'
    assert r.headers['location'] == '/context-spaces/' + a['id']
    assert client.get('/context-spaces', headers=headers()).json()['items'] == [a]
    assert client.get(r.headers['location'], headers=headers()).json() == a
    renamed = client.patch(r.headers['location'], headers=headers(), json={"name": "A renamed"})
    assert renamed.status_code == 200 and renamed.json()['created_at'] == a['created_at']
    assert renamed.json()['name'] == 'A renamed'
    reads = list(repo.reads)
    for id in [a['id'], str(uuid4())]:
        for method in ('get', 'patch'):
            args = {"json": {"name": "stolen"}} if method == 'patch' else {}
            denied = getattr(client, method)('/context-spaces/' + id, headers=headers('external-bob'), **args)
            assert denied.status_code == 404 and denied.json() == {"detail": "Context space not found"}
    assert repo.reads == reads  # Policy denies before metadata read.
    assert client.get('/context-spaces', headers=headers('external-bob')).json() == {"items": [], "next_after_id": None}
    assert repo.rows[a['id']].name == 'A renamed'


@pytest.mark.parametrize('payload', [{}, {"name": ""}, {"name": " \n"}, {"name": 5},
    {"name": None}, {"name": "x" * 257}, {"name": "x\x00y"},
    {"name": "x", "owner_id": ALICE}, {"name": "x", "id": str(uuid4())},
    {"name": "x", "status": "active"}, {"name": "x", "description": "unsupported"}])
def test_invalid_create_payload_never_persists(api, payload):
    client, repo = api
    assert client.post('/context-spaces', headers=headers(), json=payload).status_code == 422
    assert not repo.rows


@pytest.mark.parametrize('path', ['/context-spaces', '/context-spaces/' + str(uuid4())])
@pytest.mark.parametrize('auth', [{}, {"X-User-ID": ALICE}, {"Authorization": "Bearer false"},
                                  {"Authorization": "Bearer " + token(exp=1)}])
def test_missing_or_invalid_token_rejected_before_private_access(api, path, auth):
    client, repo = api
    assert client.get(path, headers=auth).status_code == 401
    assert not repo.reads


def test_owner_spoofing_queries_headers_and_claims_cannot_override_subject(api):
    client, repo = api
    bob = headers('external-bob', user_id=ALICE, owner_id=ALICE)
    bob['X-User-ID'] = ALICE
    r = client.post('/context-spaces', headers=bob, json={"name": "Bob"})
    assert r.status_code == 201 and r.json()['owner_id'] == BOB
    assert client.get('/context-spaces', headers=headers()).json()['items'] == []
    for query in ['owner_id=' + ALICE, 'subject_id=' + ALICE, 'limit=1&limit=100', 'limit=0',
                  'limit=101', 'after_id=invalid']:
        assert client.get('/context-spaces?' + query, headers=bob).status_code == 422
    assert client.get('/context-spaces/not-a-uuid', headers=headers()).status_code == 422
    assert client.get('/context-spaces', headers=[('Authorization', headers()['Authorization']),
                                                 ('Authorization', bob['Authorization'])]).status_code == 401
    assert client.get('/context-spaces', headers=headers(scope='openid')).status_code == 403
    assert not repo.reads


def test_pagination_contains_only_owned_ids_and_has_no_duplicates(api):
    client, _ = api
    ids = {client.post('/context-spaces', headers=headers(), json={"name": str(i)}).json()['id'] for i in range(3)}
    client.post('/context-spaces', headers=headers('external-bob'), json={"name": "Bob secret"})
    seen, after = [], None
    for _ in range(3):
        r = client.get('/context-spaces', headers=headers(), params=dict(limit=1, **({'after_id': after} if after else {})))
        assert r.status_code == 200
        page = r.json(); seen += [x['id'] for x in page['items']]; after = page['next_after_id']
    assert set(seen) == ids and len(seen) == len(set(seen)) and after is None


def test_storage_failure_is_sanitized_and_no_delete_or_retrieval_route(api, monkeypatch, caplog):
    client, repo = api
    async def broken(**kwargs):
        raise ContextStorageUnavailable('private-connection-detail')
    monkeypatch.setattr(repo, 'list_ids', broken)
    r = client.get('/context-spaces', headers=headers())
    assert r.status_code == 503 and r.json() == {"detail": "Context service unavailable"}
    assert 'private-connection-detail' not in r.text + caplog.text
    id = str(uuid4())
    assert client.delete('/context-spaces/' + id, headers=headers()).status_code == 405
    assert client.get('/context-spaces/' + id + '/access', headers=headers()).status_code == 404


def test_unbound_service_fails_closed_after_valid_authentication():
    auth, _ = build_auth()
    async def owner_for(_): return None
    with TestClient(create_app(security=SecurityBindings(authenticate=auth.authenticate,
                          policy=OwnerPolicyService(owner_for=owner_for)))) as client:
        assert client.get('/context-spaces', headers=headers()).status_code == 503


def test_mismatched_security_and_service_policy_cannot_be_composed():
    async def owner_for(_): return None
    first, second = (OwnerPolicyService(owner_for=owner_for) for _ in range(2))
    with pytest.raises(ValueError, match='same PolicyService'):
        create_app(services=ApplicationServices(context=ManagedContextService(repository=MemorySpaces(), policy=first),
                                                policy=first),
                   security=SecurityBindings(authenticate=None, policy=second))
