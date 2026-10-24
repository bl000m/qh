"""All provider responses here are synthetic HTTP MockTransport, no paid calls."""
import asyncio
from dataclasses import replace
from decimal import Decimal
import json
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi.testclient import TestClient
import httpx
import pytest

from adapters.llm.chat_config import ChatConfigurationError
from adapters.llm.diagnostics import PrivateDiagnostics
from adapters.llm.session_config import PrivateSessionFactory
from app.api.security import SecurityBindings
from app.chat.context import ChatProviderUnavailable
from app.composition import ApplicationServices
from app.core.models import ContextSpaceNotFound, ProviderBudgetExceeded
from app.main import create_app
from tests.test_chat_service import request
from tests.test_development_ai import setup, answer
from tests.test_enrichment import payload


def expand(ai, ledger):
    path = ai.factory.authorization_path
    receipt = json.loads(path.read_text())
    receipt['development_budget'] = dict(max_calls=100, max_usd='2.50', max_eur='5.00', eur_per_usd_upper_bound='2')
    path.write_text(json.dumps(receipt))
    state = json.loads(ledger.read_text())
    state.update(max_calls=100, max_usd='2.50')
    ledger.write_text(json.dumps(state))
    old = ai.factory
    ai.factory = PrivateSessionFactory(authorization_path=path, ledger_path=ledger, transport=old.transport, pricing=old.pricing)


def test_expanded_envelope_preserves_history_shared_counts_and_caps_at_100(tmp_path, monkeypatch):
    ai, who, _, _, calls, ledger, _, _ = setup(tmp_path, monkeypatch, answer)
    old = dict(status='completed', kind='/chat/completions', reserved_usd='0.0024', observed_usd='0.00048345', usage=dict(prompt_tokens=1079, completion_tokens=536))
    state = json.loads(ledger.read_text()); state['calls'] = [dict(old) for _ in range(6)]; ledger.write_text(json.dumps(state))
    expand(ai, ledger)
    async def run():
        cap = await ai.capabilities(who, request())
        assert cap['remaining_calls'] == 94 and cap['max_calls'] == 100 and cap['max_usd'] == '2.50'
        assert Decimal(cap['remaining_usd']) == Decimal('2.50') - 6*Decimal('0.00048345')
        # Cross the obsolete eight-call and three-session limits without a refill.
        for _ in range(4):
            await ai.respond(who, request())
        assert ai.factory.remaining()['remaining_calls'] == 90
        state = json.loads(ledger.read_text()); state['calls'] += [dict(old) for _ in range(90)]; ledger.write_text(json.dumps(state))
        with pytest.raises(ProviderBudgetExceeded):
            await ai.respond(who, request())
    asyncio.run(run())
    assert len(calls) == 4 and json.loads(ledger.read_text())['calls'][:6] == [old]*6


def test_budget_amendment_required_and_insufficient_usd_zero_http(tmp_path, monkeypatch):
    ai, who, _, _, calls, ledger, _, _ = setup(tmp_path, monkeypatch, answer)
    state = json.loads(ledger.read_text()); state.update(max_calls=100, max_usd='2.50'); ledger.write_text(json.dumps(state))
    with pytest.raises(ChatConfigurationError):
        PrivateSessionFactory(authorization_path=ai.factory.authorization_path, ledger_path=ledger)
    expand(ai, ledger)
    state = json.loads(ledger.read_text()); state['max_usd'] = '0.00239999'; ledger.write_text(json.dumps(state))
    with pytest.raises(ProviderBudgetExceeded):
        asyncio.run(ai.respond(who, request()))
    assert not calls and not state['calls']


def test_completed_http_200_rejected_chat_full_response_captured_before_cleanup(tmp_path, monkeypatch, capsys):
    raw = dict(id='synthetic-response', model='mistral-small-2603', usage=dict(prompt_tokens=1079, completion_tokens=536),
        choices=[dict(finish_reason='stop', message=dict(content=json.dumps(dict(answer='Synthetic private dossier answer.', reference_aliases=[], support_basis='canonical', insufficient_context=False))))])
    ai, who, _, _, calls, ledger, _, _ = setup(tmp_path, monkeypatch, lambda _: httpx.Response(200, json=raw))
    with pytest.raises(ChatProviderUnavailable):
        asyncio.run(ai.respond(who, request()))
    result = asyncio.run(ai.diagnostics(who, request()))
    record, = result['items']
    assert record['raw_response'] == raw and record['outcome'] == 'rejected'
    assert record['attempt_index'] == 0 and record['accounting']['status'] == 'completed'
    assert record['accounting']['observed_usd'] == '0.00048345'
    assert record['checks'][-2]['rule'] == 'chat.support_basis_matches_transmitted_inputs'
    assert record['checks'][-2]['result'] == 'FAIL'
    assert all(c['result'] == 'PASS' for c in record['checks'][:-2])
    text = next(ai.factory.diagnostics.path.glob('*.json')).read_text()
    assert 'request' not in json.loads(text) and 'messages' not in json.loads(text)
    assert next(ai.factory.diagnostics.path.glob('*.json')).stat().st_mode & 0o077 == 0
    assert not capsys.readouterr().out and len(calls) == 1
    assert len(json.loads(ledger.read_text())['calls']) == 1


@pytest.mark.parametrize('status,finish', [(403, 'stop'), (200, 'length'), (200, 'stop')])
def test_transport_rejection_and_accepted_chat_are_distinct(tmp_path, monkeypatch, status, finish):
    def response(req):
        raw = json.loads(answer(req).content); raw['choices'][0]['finish_reason'] = finish
        return httpx.Response(status, json=raw)
    ai, who, _, _, _, _, _, _ = setup(tmp_path, monkeypatch, response)
    if status == 200 and finish == 'stop':
        asyncio.run(ai.respond(who, request()))
    else:
        with pytest.raises(ChatProviderUnavailable):
            asyncio.run(ai.respond(who, request()))
    row, = asyncio.run(ai.diagnostics(who, request()))['items']
    assert row['http_status'] == status and row['raw_response']['model'] == 'mistral-small-2603'
    assert row['outcome'] == ('accepted' if status == 200 and finish == 'stop' else 'rejected')


def test_diagnostics_exact_owner_scope_no_price_http_delete_does_not_touch_ledger(tmp_path, monkeypatch):
    ai, who, _, _, calls, ledger, _, _ = setup(tmp_path, monkeypatch, answer)
    asyncio.run(ai.respond(who, request()))
    before = ledger.read_bytes()
    ai.factory.pricing.verify = AsyncMock(side_effect=AssertionError('No price/provider HTTP for diagnostics'))
    with pytest.raises(ContextSpaceNotFound):
        asyncio.run(ai.diagnostics(replace(who, principal_id='b'*64), request()))
    with pytest.raises(ContextSpaceNotFound):
        asyncio.run(ai.diagnostics(who, request(context_id='foreign')))
    ai.chat._authorize = AsyncMock()
    assert not asyncio.run(ai.diagnostics(who, request(context_id='another-owned-space')))['items']
    row, = asyncio.run(ai.diagnostics(who, request()))['items']
    asyncio.run(ai.diagnostics(who, request(context_id='another-owned-space'), delete_id=row['id']))
    assert asyncio.run(ai.diagnostics(who, request()))['items']
    asyncio.run(ai.diagnostics(who, request(), delete_id=row['id']))
    assert not asyncio.run(ai.diagnostics(who, request()))['items']
    assert ledger.read_bytes() == before and len(calls) == 1


def test_retention_capacity_symlink_and_storage_failure_before_paid_http(tmp_path, monkeypatch):
    now = [100.0]
    store = PrivateDiagnostics(tmp_path/'private', clock=lambda: now[0])
    identity = store.begin(subject='alice', scope='space', kind='chat')
    now[0] += 3601; store.purge_expired()
    assert not (store.path/(identity+'.json')).exists()
    ai, who, _, _, calls, ledger, _, _ = setup(tmp_path, monkeypatch, answer)
    ai.factory.diagnostics.max_records = 0
    with pytest.raises(ChatProviderUnavailable):
        asyncio.run(ai.respond(who, request()))
    assert not calls and not json.loads(ledger.read_text())['calls']
    target = tmp_path/'symlink'; target.symlink_to(store.path)
    with pytest.raises(ValueError):
        PrivateDiagnostics(target)


def test_umm_exact_quote_failure_traced_no_publication(tmp_path, monkeypatch):
    raw = dict(model='mistral-small-2603', usage=dict(prompt_tokens=100, completion_tokens=30),
        choices=[dict(finish_reason='stop', message=dict(content=json.dumps(dict(format='qh.atomic-understanding/1', items=[dict(text='Invented', primary_dimension=None, evidence=[dict(quote='NOT IN SOURCE')])]))))])
    ai, who, _, _, _, _, _, repo = setup(tmp_path, monkeypatch, lambda _: httpx.Response(200, json=raw))
    ai.chat._authorize = AsyncMock()
    scope = str(uuid4())
    with pytest.raises(ValueError):
        asyncio.run(ai.enrich(who, scope, dict(payload(), extraction_mode='semantic')))
    row, = asyncio.run(ai.diagnostics(who, request(context_id=scope)))['items']
    assert row['raw_response'] == raw and row['outcome'] == 'rejected' and repo.calls == 0
    assert any('quote_not_in_original_turns' in (c['reason'] or '') for c in row['checks'])


def test_http_diagnostics_require_full_identity_private_no_store_and_delete(tmp_path, monkeypatch):
    ai, who, _, _, _, _, _, _ = setup(tmp_path, monkeypatch, answer)
    asyncio.run(ai.respond(who, request()))
    row, = asyncio.run(ai.diagnostics(who, request()))['items']
    scope = str(uuid4())
    ai.chat._authorize = AsyncMock()
    async def authenticate(_): return who.subject_id
    async def session(token): return who if token == 'alice' else replace(who, principal_id='b'*64)
    app = create_app(services=ApplicationServices(context=ai.chat.context, policy=ai.chat.policy, development_ai=ai),
        security=SecurityBindings(authenticate=authenticate, policy=ai.chat.policy, authenticate_session=session, authenticate_with_expiry=AsyncMock()))
    with TestClient(app) as client:
        path = '/context-spaces/'+scope+'/ai/diagnostics'
        assert client.get(path).status_code == 401
        assert client.get(path, headers={'Authorization':'Bearer bob'}).status_code == 404
        response = client.get(path, headers={'Authorization':'Bearer alice'})
        assert response.status_code == 200 and response.json()['items'] == []
        assert response.headers['cache-control'] == 'private, no-store'
        assert client.delete(path+'/'+row['id'], headers={'Authorization':'Bearer alice'}).status_code == 200
        assert asyncio.run(ai.diagnostics(who, request()))['items']  # foreign-scope delete is inert


def test_echoed_provider_credential_redacted_explicitly_and_request_never_retained(tmp_path, monkeypatch):
    from adapters.llm.diagnostics import DiagnosticCall
    from types import SimpleNamespace
    ai, who, _, _, _, _, _, _ = setup(tmp_path, monkeypatch, answer)
    diagnostic = DiagnosticCall(ai.factory.diagnostics, who.subject_id, 'space', 'chat')
    diagnostic.begin()
    raw = SimpleNamespace(_key='synthetic-secret', last_exchange=dict(response=dict(message='synthetic-secret'), http_status=200), last_attempt=None, last_failure=None)
    diagnostic.capture(raw)
    row, = ai.factory.diagnostics.records(subject=who.subject_id, scope='space')
    assert row['secret_redacted'] and row['raw_response'] == dict(message='[REDACTED]')
    assert 'synthetic-secret' not in next(ai.factory.diagnostics.path.glob('*.json')).read_text()


def test_changed_context_keeps_paid_response_private_and_records_post_check_failure(tmp_path, monkeypatch):
    from tests.test_chat_context import revision
    from app.chat.context import ChatContextUnavailable
    holder = []
    def response(req):
        holder[0].values = [revision()]
        return answer(req)
    ai, who, context, _, _, _, _, _ = setup(tmp_path, monkeypatch, response)
    holder.append(context)
    with pytest.raises(ChatContextUnavailable):
        asyncio.run(ai.respond(who, request()))
    row, = asyncio.run(ai.diagnostics(who, request()))['items']
    assert row['accounting']['status'] == 'completed' and row['outcome'] == 'rejected'
    assert any(c['rule'] == 'chat.post_generation_policy_graph_snapshot' and c['result'] == 'FAIL' for c in row['checks'])
