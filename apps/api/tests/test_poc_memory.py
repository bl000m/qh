"""POC output defaults/global-only budget/full-conversation extraction, zero network."""
import asyncio
from decimal import Decimal
import json
from uuid import uuid4

import httpx
import pytest

from adapters.llm.mistral import MODEL_CONTEXT_TOKENS,cost
from adapters.llm.session_config import PrivateSessionFactory
from app.core.models import ProviderBudgetExceeded,Message,MessageRole
from app.understanding.enrichment import EnrichmentUnavailable
from tests.test_development_ai import setup,answer
from tests.test_chat_service import request


def poc(ai,ledger):
    path=ai.factory.authorization_path;r=json.loads(path.read_text())
    r['development_budget']=dict(max_calls=None,max_usd='5.00',max_eur='10.00',eur_per_usd_upper_bound='2');path.write_text(json.dumps(r))
    state=json.loads(ledger.read_text());state.update(max_calls=None,max_usd='5.00');ledger.write_text(json.dumps(state))
    old=ai.factory;ai.factory=PrivateSessionFactory(authorization_path=path,ledger_path=ledger,transport=old.transport)


def test_no_token_parameter_or_call_session_ceiling_and_history_retained(tmp_path,monkeypatch):
    ai,who,_,_,calls,ledger,_,_=setup(tmp_path,monkeypatch,answer);poc(ai,ledger)
    state=json.loads(ledger.read_text());old=[dict(status='completed',reserved_usd='.001',observed_usd='.0001',kind='/chat/completions') for _ in range(110)];state['calls']=old;ledger.write_text(json.dumps(state))
    messages=tuple(Message(role=MessageRole.USER if i%2==0 else MessageRole.ASSISTANT,content='Texte explicite '+str(i)+' '+('x'*4200)) for i in range(11))
    from app.api.development_ai import FullChatInput
    FullChatInput.model_validate(dict(messages=[dict(role=m.role.value,content=m.content) for m in messages]))
    result=asyncio.run(ai.respond(who,request(messages=messages)))
    assert result and len(calls)==1 and 'max_tokens' not in calls[0]
    assert len(calls[0]['messages'])==13  # Full user/assistant dialogue + existing context/system.
    assert json.loads(ledger.read_text())['calls'][:110]==old
    caps=asyncio.run(ai.capabilities(who,request()));assert caps['remaining_calls'] is None and caps['max_calls'] is None


@pytest.mark.parametrize('finish',['stop','length'])
def test_complete_output_beyond_1000_maps_to_proposed_uum_or_truncation_saves_nothing(tmp_path,monkeypatch,finish):
    quote='Je veux garder une heure pour mon projet.'
    value=dict(format='qh.atomic-understanding/1',items=[dict(text='Objectif '+str(i),primary_dimension='objectives_intentions',assignment_certainty='asserted',evidence=[dict(quote=quote)]) for i in range(16)])
    def response(req):
        assert 'max_tokens' not in json.loads(req.content)
        content=json.dumps(value) if finish=='stop' else json.dumps(value)[:-10]
        return httpx.Response(200,json=dict(model='mistral-small-2603',usage=dict(prompt_tokens=1368,completion_tokens=4000 if finish=='stop' else 1000),choices=[dict(finish_reason=finish,message=dict(content=content))]))
    ai,who,_,_,calls,ledger,_,repo=setup(tmp_path,monkeypatch,response);poc(ai,ledger)
    scope=str(uuid4())
    from app.policy.owner import OwnerPolicyService
    async def owned(s):return 'alice' if s==scope else None
    ai.chat.policy=OwnerPolicyService(owner_for=owned)
    turns=[dict(id=str(uuid4()),role='user' if i%2==0 else 'assistant',content=quote if i==0 else 'Autre passage '+str(i)+' '+('x'*2000),captured_at='2026-10-23T10:00:00Z') for i in range(12)]
    payload=dict(conversation_id=str(uuid4()),operation_id=str(uuid4()),persist_consent=True,extraction_mode='semantic',turns=turns)
    from app.api.development_ai import FullEnrichmentInput
    payload=FullEnrichmentInput.model_validate(payload).model_dump(mode='json')
    if finish=='length':
        with pytest.raises(EnrichmentUnavailable):asyncio.run(ai.enrich(who,scope,payload))
        assert not repo.saved and repo.calls==0
    else:
        result=asyncio.run(ai.enrich(who,scope,payload));assert len(result['revision_ids'])==16
        source,rows=next(iter(repo.saved.values()))[2:]
        assert len(source['origin']['turns'])==12 and repo.calls==1
        assert all(r['validation_state']=='proposed' and r['content']['primary_dimension']['value']=='objectives_intentions' for r in rows)
        replay=asyncio.run(ai.enrich(who,scope,payload));assert replay['replayed'] and repo.calls==1
    assert len(calls)==1 and json.loads(ledger.read_text())['calls'][-1]['status']=='completed'


def test_full_window_reservation_blocks_before_http_not_prepaid_credit(tmp_path,monkeypatch):
    ai,who,_,_,calls,ledger,_,_=setup(tmp_path,monkeypatch,answer);poc(ai,ledger)
    state=json.loads(ledger.read_text());state['max_usd']=str(cost(0,MODEL_CONTEXT_TOKENS)-Decimal('.00000001'));ledger.write_text(json.dumps(state))
    with pytest.raises(ProviderBudgetExceeded):asyncio.run(ai.respond(who,request()))
    assert not calls and not json.loads(ledger.read_text())['calls']


def test_pending_reservation_holds_budget_without_suspending_the_ai(tmp_path,monkeypatch):
    ai,who,_,_,calls,ledger,_,_=setup(tmp_path,monkeypatch,answer);poc(ai,ledger)
    state=json.loads(ledger.read_text());state['max_usd']='.16';state['calls']=[dict(status='pending',reserved_usd=str(cost(0,MODEL_CONTEXT_TOKENS)),kind='/chat/completions')];ledger.write_text(json.dumps(state))
    caps=asyncio.run(ai.capabilities(who,request()))
    assert not caps['enabled'] and not caps['accounting_blocked'] and caps['unavailable_reason']=='budget' and not calls


def test_poc_capabilities_http_serializes_global_limits_without_provider_call(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from unittest.mock import AsyncMock
    from app.api.security import SecurityBindings
    from app.composition import ApplicationServices
    from app.main import create_app
    from app.api.chat_sessions import CapabilityOutput
    from pydantic import ValidationError

    ai, who, _, _, calls, ledger, _, _ = setup(tmp_path, monkeypatch, answer)
    poc(ai, ledger)
    ai.chat._authorize = AsyncMock()
    async def authenticate(token):
        return who.subject_id
    async def identity(token):
        return who
    app = create_app(services=ApplicationServices(
        context=ai.chat.context, policy=ai.chat.policy, chat=ai.chat,
        chat_sessions=object(), development_ai=ai), security=SecurityBindings(
        authenticate=authenticate, authenticate_session=identity,
        authenticate_with_expiry=AsyncMock(), policy=ai.chat.policy))
    before = ledger.read_bytes()
    with TestClient(app) as client:
        response = client.get('/context-spaces/'+str(uuid4())+'/chat-sessions',
            headers={'Authorization': 'Bearer synthetic'})
        assert response.status_code == 200
        value = response.json()
        assert value['automatic'] and value['enabled']
        assert value['max_seconds'] is value['max_calls'] is value['remaining_calls'] is None
        assert response.headers['cache-control'] == 'private, no-store'
        assert client.get('/context-spaces/'+str(uuid4())+'/chat-sessions').status_code == 401
    assert not calls and ledger.read_bytes() == before
    for change in ({'automatic': False}, {'max_calls': 3}, {'max_seconds': 1800}):
        with pytest.raises(ValidationError):
            CapabilityOutput.model_validate({**value, **change})


def test_accounting_block_is_reported_without_changing_history_or_spending(tmp_path,monkeypatch):
    ai,who,_,_,calls,ledger,_,_=setup(tmp_path,monkeypatch,answer);poc(ai,ledger)
    state=json.loads(ledger.read_text())
    state['blocked']=True
    state['calls']=[dict(status='failed',reserved_usd=str(cost(0,MODEL_CONTEXT_TOKENS)),error='Mistral HTTP 400')]
    ledger.write_text(json.dumps(state));before=ledger.read_bytes()
    caps=asyncio.run(ai.capabilities(who,request()))
    assert caps['accounting_blocked'] and not caps['enabled'] and not caps['plafond_reached']
    assert Decimal(caps['remaining_usd'])>1
    from app.api.chat_sessions import CapabilityOutput
    assert CapabilityOutput.model_validate(caps).accounting_blocked
    assert ledger.read_bytes()==before and not calls
