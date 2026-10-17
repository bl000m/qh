"""Signed OIDC / real REST and shared policy; no SQL/graph needed for boundary tests."""

from dataclasses import replace

import pytest

from app.core.models import ContextResult, ContextRetrievalUnavailable
from tests.test_context_spaces_api import api as api, headers

PATH = '/context-spaces/query'


@pytest.fixture
def query_api(api):
    client, repo = api
    a = client.post('/context-spaces', headers=headers(), json={'name':'A'}).json()['id']
    b = client.post('/context-spaces', headers=headers('external-bob'), json={'name':'B'}).json()['id']
    calls = []
    class Backend:
        async def retrieve(self, request):
            calls.append(request)
            return ContextResult(hits=())
    client.app.state.services.context.retrieval_for = lambda subject: Backend()
    return client, repo, a, b, calls


def payload(scope, **kwargs):
    return dict(context_ids=[scope], view='proposed', text='pilot', **kwargs)


def test_explicit_views_and_open_descriptors_reach_existing_context_service(query_api):
    client, _, a, _, calls = query_api
    for view in ('current', 'proposed', 'history'):
        r = client.post(PATH, headers=headers(), json={**payload(a), 'view':view})
        assert r.status_code == 200 and r.json() == {'view':view,'items':[], 'next_after_revision_id':None}
        assert calls[-1].query.view == view
    r = client.post(PATH, headers=headers(), json=dict(context_ids=[a,a], view='history',
        descriptors=['NewMeaning Ω','decision'], include_tentative=True, limit=100))
    assert r.status_code == 200
    q = calls[-1].query
    assert q.descriptors == ('NewMeaning Ω','decision') and q.context_ids == (a,)
    assert q.include_tentative and q.limit == 100


@pytest.mark.parametrize('change', [dict(view=None),dict(view='latest'),dict(context_ids=[]),
    dict(context_ids=['bad']),dict(text=' '),dict(text='x'*4097),dict(descriptors=['decision']),
    dict(text=None,descriptors=[]),dict(text=None,descriptors=['']),dict(text=None,descriptors=[4]),
    dict(text=None),dict(limit=0),dict(limit=101),dict(limit=True),dict(include_tentative=True),
    dict(include_tentative='true'),dict(after_revision_id='bad'),dict(source_revision_id='external'),
    dict(revision_id='external'),dict(owner_id='spoof'),dict(fact_at='2026-10-17')])
def test_invalid_queries_never_invoke_retrieval(query_api, change):
    client, _, a, _, calls = query_api
    assert client.post(PATH, headers=headers(), json={**payload(a),**change}).status_code == 422
    assert not calls


def test_missing_view_is_rejected_and_scope_denied_as_a_whole(query_api):
    client, _, a, b, calls = query_api
    body=payload(a);del body['view']
    assert client.post(PATH, headers=headers(), json=body).status_code == 422
    for scopes, auth in (([b], headers()),([a,b], headers()),([a],headers('external-bob'))):
        r=client.post(PATH, headers=auth, json={**payload(a),'context_ids':scopes})
        assert r.status_code == 404 and r.json() == {'detail':'Context space not found'}
    assert not calls


@pytest.mark.parametrize('auth', [{}, {'X-User-ID':'alice'}, {'Authorization':'Bearer invalid'},headers(exp=1)])
def test_anonymous_invalid_and_expired_tokens_do_not_retrieve(query_api, auth):
    client, _, a, _, calls = query_api
    assert client.post(PATH, headers=auth, json=payload(a)).status_code == 401
    assert not calls


def test_query_spoofing_service_failure_and_policy_revocation_fail_closed(query_api):
    client, repo, a, _, calls = query_api
    assert client.post(PATH+'?owner_id=alice', headers=headers(), json=payload(a)).status_code == 422
    assert not calls
    service=client.app.state.services.context
    service.retrieval_for=None
    assert client.post(PATH, headers=headers(), json=payload(a)).status_code == 503
    class Revoker:
        async def retrieve(self, request):
            repo.rows[a]=replace(repo.rows[a],owner_id='revoked')
            return ContextResult(hits=())
    service.retrieval_for=lambda subject:Revoker()
    assert client.post(PATH, headers=headers(), json=payload(a)).status_code == 404


def test_unavailable_backend_details_are_not_disclosed(query_api, caplog):
    client, _, a, _, _ = query_api
    class Unavailable:
        async def retrieve(self, request):
            raise ContextRetrievalUnavailable('synthetic-private-driver-message')
    client.app.state.services.context.retrieval_for=lambda subject:Unavailable()
    r=client.post(PATH, headers=headers(), json=payload(a))
    assert r.status_code==503 and 'synthetic-private' not in r.text+caplog.text
