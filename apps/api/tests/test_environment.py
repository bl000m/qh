"""Immediate disposable SQL/API isolation and optimistic organization checks."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor

from alembic import command
from fastapi.testclient import TestClient
import pytest

from app.environment.service import defaults, validate
from tests.test_context_spaces_sql import application
from tests.test_context_spaces_api import ALICE, BOB, headers
from tests.test_migrations import connect, empty_database as empty_database
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only
from tests.test_oidc_security import SETTINGS


@pytest.fixture
def organization_db(empty_database, monkeypatch):
    command.upgrade(empty_database, '0006_owner_organization')
    monkeypatch.setenv('QH_NATIVE_CONTEXT_ENABLED', 'false')
    with connect() as c:
        for id, sub in [(ALICE, 'external-alice'), (BOB, 'external-bob')]:
            c.execute('INSERT INTO users(id,display_name) VALUES (%s,%s)', (id, sub))
            c.execute('INSERT INTO user_identities(issuer,subject,user_id) VALUES (%s,%s,%s)', (SETTINGS.issuer, sub, id))


def test_virtual_defaults_and_strict_document_validation():
    original = defaults()
    assert len(original['domains']) == 7 and original['memberships'] == {}
    for changes in ({'version': True}, {'owner_id': BOB}, {'domains': [original['domains'][0]]*2}, {'memberships': {ALICE: ['foreign']}}):
        with pytest.raises((ValueError, TypeError)):
            validate(dict(original, **changes))
    original['domains'].clear()
    assert len(defaults()['domains']) == 7


def test_owner_persistence_multi_membership_reopen_and_no_canonical_writes(organization_db):
    with TestClient(application()) as client:
        assert client.get('/environment').status_code == 401
        before = client.get('/environment', headers=headers()).json()
        assert before == defaults()
        with connect() as c: assert c.execute('SELECT count(*) FROM owner_organization').fetchone() == (0,)
        space = client.post('/context-spaces', headers=headers(), json={'name': 'Owned'}).json()['id']
        change = deepcopy(before)
        change['domains'][0]['name'] = 'Travail personnel'
        change['memberships'][space] = [d['id'] for d in change['domains'][:2]]
        saved = client.put('/environment', headers=headers(), json=change)
        assert saved.status_code == 200 and saved.json()['version'] == 1
        assert client.put('/environment', headers=headers(), json=change).status_code == 409
        assert client.get('/environment', headers=headers('external-bob')).json() == defaults()
        assert client.put('/environment', headers=headers('external-bob'), json=change).status_code == 403
        assert client.put('/environment?owner_id='+BOB, headers=headers(), json=change).status_code == 422
        assert client.put('/environment', headers=headers(), json=dict(change, owner_id=BOB)).status_code == 422
    with TestClient(application()) as reopened:
        assert reopened.get('/environment', headers=headers()).json() == saved.json()
    with connect() as c:
        assert c.execute('SELECT count(*) FROM understanding_items').fetchone() == (0,)
        assert c.execute('SELECT count(*) FROM sources').fetchone() == (0,)
        assert c.execute('SELECT count(*) FROM context_spaces').fetchone() == (1,)


def test_conflicting_owner_edits_and_revocation_fence(organization_db):
    def save(_):
        with TestClient(application()) as client:
            return client.put('/environment', headers=headers(), json=defaults()).status_code
    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(save, range(2))) == [200, 409]
    with TestClient(application()) as client:
        space = client.post('/context-spaces', headers=headers(), json={'name': 'Owned'}).json()['id']
        doc = client.get('/environment', headers=headers()).json()
        doc['memberships'][space] = [doc['domains'][0]['id']]
        assert client.put('/environment', headers=headers(), json=doc).status_code == 200
        with connect() as c:
            c.execute('UPDATE context_spaces SET owner_id=%s WHERE id=%s', (BOB, space))
        assert client.get('/environment', headers=headers()).status_code == 403
        # Stale app policy cannot bypass SQL ownership.
        async def stale(_): return ALICE
        app = application(); app.state.services.policy._owner_for = stale
        with TestClient(app) as stale_client:
            doc['version'] += 1
            assert stale_client.put('/environment', headers=headers(), json=doc).status_code == 403
