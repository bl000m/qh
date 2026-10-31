"""Current owner correction: ordinary AI sends, shared original budget, zero network."""
import asyncio
from dataclasses import replace
import json
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from adapters.llm.session_config import PrivateSessionFactory
from app.api.security import SecurityBindings
from app.chat.context import ChatProviderUnavailable
from app.core.models import ProviderFailure, ProviderBudgetExceeded
from app.chat.development import DevelopmentAI
from app.chat.implementation import ContextualChatService
from app.composition import ApplicationServices
from app.core.models import ContextSpaceNotFound
from app.main import create_app
from app.understanding.enrichment import EnrichmentUnavailable
from tests.test_chat_sessions import setup as session_setup
from tests.test_chat_service import request
from tests.test_enrichment import setup as enrichment_setup, payload


def setup(tmp_path, monkeypatch, handler=None):
    sessions, identity, context, owner, calls, ledger, clock = session_setup(tmp_path, monkeypatch, handler=handler, rows=[])
    auth = sessions.factory.authorization_path
    receipt = json.loads(auth.read_text())
    receipt['development_account'] = dict(environment='development', subject_id=identity.subject_id, principal_id='a'*64)
    auth.write_text(json.dumps(receipt))
    old = sessions.factory
    factory = PrivateSessionFactory(authorization_path=auth, ledger_path=ledger, transport=old.transport)
    identity = replace(identity, principal_id='a'*64, verified_session_id='verified-login', work_expires_at=clock[0]+8*3600)
    repo, _, _, enrich = enrichment_setup(); enrich.uum=True
    automatic = DevelopmentAI(chat=sessions.chat, enrichment=enrich, factory=factory, clock=lambda:clock[0])
    return automatic, identity, context, owner, calls, ledger, clock, repo


def answer(_):
    return httpx.Response(200, json=dict(model='mistral-small-2603', usage=dict(prompt_tokens=100, completion_tokens=30),
        choices=[dict(finish_reason='stop',message=dict(content=json.dumps(dict(answer='Précisez votre objectif.',reference_aliases=[],support_basis='insufficient', insufficient_context=True))))]))


def test_ordinary_send_empty_and_new_space_no_activation_or_session_budget(tmp_path,monkeypatch):
    ai,who,context,owner,calls,ledger,_,_=setup(tmp_path,monkeypatch,answer)
    original=dict(status='completed',kind='/chat/completions',reserved_usd='0.0024',observed_usd='0.0001')
    state=json.loads(ledger.read_text());state['calls']=[dict(original) for _ in range(4)];ledger.write_text(json.dumps(state))
    async def owned(scope): return 'alice' if scope in ('space','new-space') else None
    # Bind an actual owner policy for both owned synthetic Spaces, not a client grant.
    from app.policy.owner import OwnerPolicyService
    ai.chat.policy=OwnerPolicyService(owner_for=owned)
    async def run():
        before=ledger.read_bytes();caps=await ai.capabilities(who,request())
        assert caps['automatic'] and caps['enabled'] and caps['remaining_calls']==4
        assert before==ledger.read_bytes() and not calls
        for i in range(4):
            result=await ai.respond(who,request(context_id='space' if i%2 else 'new-space'))
            assert result.model=='mistral-small-2603' and result.insufficient_context and not result.references
        with pytest.raises(ProviderBudgetExceeded): await ai.respond(who,request())
        assert (await ai.capabilities(who,request()))['plafond_reached']
    asyncio.run(run());state=json.loads(ledger.read_text())
    assert len(calls)==4 and len(state['calls'])==8 and state['calls'][:4]==[original]*4
    assert all('session_id' not in row for row in state['calls'][4:])
    # New process/login cannot manufacture budget; original receipt and ledger reused.
    assert ai.factory.remaining()['remaining_calls']==0


@pytest.mark.parametrize('change',[dict(subject_id='bob'),dict(principal_id='b'*64),dict(verified_session_id=None),dict(expires_at=0),dict(work_expires_at=0)])
def test_verified_identity_only_no_other_account_disclosure(tmp_path,monkeypatch,change):
    ai,who,_,_,calls,ledger,_,_=setup(tmp_path,monkeypatch,answer)
    changed=replace(who,**change)
    if 'subject_id' in change or 'principal_id' in change:
        with pytest.raises(ContextSpaceNotFound):asyncio.run(ai.respond(changed,request(subject_id=changed.subject_id)))
    else:
        # The eligible owner's expired work session is reported as such, never as a missing Space.
        with pytest.raises(ProviderFailure) as failure:asyncio.run(ai.respond(changed,request()))
        assert failure.value.kind=='session'
        caps=asyncio.run(ai.capabilities(changed,request()))
        assert not caps['enabled'] and caps['unavailable_reason']=='session_expired'
    assert not calls and not json.loads(ledger.read_text())['calls']


def test_foreign_scope_and_receipt_revocation_before_and_during_request(tmp_path,monkeypatch):
    ai,who,_,owner,calls,ledger,_,_=setup(tmp_path,monkeypatch,answer)
    with pytest.raises(ContextSpaceNotFound):asyncio.run(ai.respond(who,request(context_id='foreign')))
    owner[0]='bob'
    with pytest.raises(ContextSpaceNotFound):asyncio.run(ai.respond(who,request()))
    owner[0]='alice'
    path=ai.factory.authorization_path;receipt=json.loads(path.read_text());receipt.pop('development_account');path.write_text(json.dumps(receipt))
    with pytest.raises(ContextSpaceNotFound):asyncio.run(ai.respond(who,request()))
    assert not calls and not json.loads(ledger.read_text())['calls']


def test_insufficient_global_usd_and_atomic_competing_requests_never_overspend(tmp_path,monkeypatch):
    ai,who,_,_,calls,ledger,_,_=setup(tmp_path,monkeypatch,answer)
    state=json.loads(ledger.read_text());state['max_usd']='0.0023';ledger.write_text(json.dumps(state))
    with pytest.raises(ProviderBudgetExceeded):asyncio.run(ai.respond(who,request()))
    assert not calls and not json.loads(ledger.read_text())['calls']
    state['max_usd']='0.20';ledger.write_text(json.dumps(state))
    # A pending reservation (in flight or left by a crash) counts at its maximum.
    index=ai.factory.ledger.reserve('/chat/completions',ai.factory.reservation_usd)
    with pytest.raises(ProviderBudgetExceeded):asyncio.run(ai.respond(who,request()))
    assert not calls and len(json.loads(ledger.read_text())['calls'])==1
    ai.factory.ledger.settle(index,error='synthetic stopped request')
    assert not json.loads(ledger.read_text())['blocked']


def test_chat_and_umm_share_same_ledger_exact_sources_proposed_and_replay(tmp_path,monkeypatch):
    def semantic(req):
        sent=json.loads(req.content);source=json.loads(sent['messages'][-1]['content']);quote=source['turns'][0]
        # Source turns have locators; quote comes from exact supplied original text.
        text='Je veux dormir sept heures.'
        value=dict(format='qh.atomic-understanding/1',items=[dict(text='Dormir sept heures',primary_dimension='objectives_intentions',assignment_certainty='asserted',evidence=[dict(quote=text)])])
        assert text in source['text'] and 'other-space-secret' not in str(source)
        return httpx.Response(200,json=dict(model='mistral-small-2603',usage=dict(prompt_tokens=100,completion_tokens=100),choices=[dict(finish_reason='stop',message=dict(content=json.dumps(value)))]))
    ai,who,_,_,calls,ledger,_,repo=setup(tmp_path,monkeypatch,semantic)
    scope=str(uuid4());data=dict(payload('Je veux dormir sept heures.'),extraction_mode='semantic')
    from app.policy.owner import OwnerPolicyService
    async def owned(s):return 'alice' if s in (scope,'space') else None
    ai.chat.policy=OwnerPolicyService(owner_for=owned)
    async def run():
        first=await ai.enrich(who,scope,data);second=await ai.enrich(who,scope,data)
        assert second==dict(first,replayed=True)
        source,rows=next(iter(repo.saved.values()))[2:]
        assert source['origin']['metadata']['provider_mode']=='uum-mistral/3'
        assert len(rows)==1 and rows[0]['validation_state']=='proposed'
        assert rows[0]['content']['primary_dimension']['value']=='objectives_intentions'
        assert rows[0]['content']['primary_dimension']['review_state']=='proposed'
        assert rows[0]['content']['citations'][0]['quote']==data['turns'][0]['content']
    asyncio.run(run());assert len(calls)==1 and len(json.loads(ledger.read_text())['calls'])==1 and repo.calls==1


def test_invalid_umm_output_no_silent_repair_or_publication(tmp_path,monkeypatch):
    def invalid(_):return httpx.Response(200,json=dict(model='mistral-small-2603',usage=dict(prompt_tokens=100,completion_tokens=30),choices=[dict(finish_reason='stop',message=dict(content='{"format":"qh.atomic-understanding/1","items":[{"text":"Invented","primary_dimension":null,"evidence":[{"quote":"Invented"}]}]}'))]))
    ai,who,_,_,calls,ledger,_,repo=setup(tmp_path,monkeypatch,invalid)
    ai.chat._authorize=AsyncMock()
    with pytest.raises(ValueError):asyncio.run(ai.enrich(who,str(uuid4()),dict(payload(),extraction_mode='semantic')))
    assert repo.calls==0 and len(calls)==1 and len(json.loads(ledger.read_text())['calls'])==1


@pytest.mark.parametrize('basis', ['insufficient', 'dialogue'])
def test_authenticated_http_send_and_plafond_message_without_grant_endpoints(tmp_path,monkeypatch,basis):
    def response(req):
        raw=answer(req).json()
        value=json.loads(raw['choices'][0]['message']['content']); value['support_basis']=basis
        raw['choices'][0]['message']['content']=json.dumps(value)
        return httpx.Response(200,json=raw)
    ai,who,context,_,calls,ledger,_,repo=setup(tmp_path,monkeypatch,response)
    scope=str(uuid4());ai.chat._authorize=AsyncMock()
    async def auth(token):
        if token!='synthetic':
            from adapters.oidc import InvalidCredentials
            raise InvalidCredentials('Invalid credentials')
        return who.subject_id
    async def full(token):await auth(token);return who
    app=create_app(services=ApplicationServices(context=ai.chat.context,policy=ai.chat.policy,chat=ai.chat,development_ai=ai),security=SecurityBindings(authenticate=auth,authenticate_with_expiry=AsyncMock(),authenticate_session=full,policy=ai.chat.policy))
    with TestClient(app) as client:
        data=dict(messages=[dict(role='user',content='Une question.')],include_proposed=False)
        assert client.post('/context-spaces/'+scope+'/ai/messages',json=data).status_code==401
        result=client.post('/context-spaces/'+scope+'/ai/messages',headers={'Authorization':'Bearer synthetic'},json=data)
        assert result.status_code==200 and len(calls)==1
        dto=result.json()
        assert dto['support_basis']==basis and dto['insufficient_context'] is True
        assert dto['references']==[] and dto['provided_revisions']==[]
        assert context.values==[] and repo.calls==0 and not repo.saved
        state=json.loads(ledger.read_text());state['max_calls']=1;ledger.write_text(json.dumps(state))
        result=client.post('/context-spaces/'+scope+'/ai/messages',headers={'Authorization':'Bearer synthetic'},json=data)
        assert result.status_code==402 and result.json()['detail']=='Plafond IA atteint. Aucune nouvelle requête ne sera facturée.' and len(calls)==1


def test_oidc_renewal_and_new_login_do_not_refill_global_accounting(tmp_path,monkeypatch):
    ai,who,_,_,calls,ledger,clock,_=setup(tmp_path,monkeypatch,answer)
    async def run():
        await ai.respond(who,request())
        for expected,identity in enumerate((replace(who,credential_id='renewed',expires_at=clock[0]+300),
                         replace(who,credential_id='new-login',verified_session_id='new-work-session')),start=1):
            assert (await ai.capabilities(identity,request()))['remaining_calls']==8-expected
            await ai.respond(identity,request())
    asyncio.run(run());assert len(calls)==3 and len(json.loads(ledger.read_text())['calls'])==3


def test_in_flight_reservation_counts_toward_the_ceiling_without_blocking(tmp_path,monkeypatch):
    ai,who,_,_,calls,ledger,_,_=setup(tmp_path,monkeypatch,answer)
    entered,release=None,None
    async def transport(req):
        entered.set();await release.wait();return answer(req)
    ai.factory.transport=httpx.MockTransport(transport)
    async def run():
        nonlocal entered,release
        entered,release=asyncio.Event(),asyncio.Event()
        first=asyncio.create_task(ai.respond(who,request()));await entered.wait()
        # In flight is not "suspended"; its reserved maximum still refuses an overspend.
        assert (await ai.capabilities(who,request()))['accounting_blocked'] is False
        with pytest.raises(ProviderBudgetExceeded):await ai.respond(who,request())
        release.set();await first
    asyncio.run(run());rows=json.loads(ledger.read_text())['calls'];assert len(rows)==1 and rows[0]['status']=='completed'


def test_bob_owned_space_and_missing_credentials_never_available(tmp_path,monkeypatch):
    ai,who,_,_,calls,ledger,_,_=setup(tmp_path,monkeypatch,answer)
    ai.chat._authorize=AsyncMock()
    bob=replace(who,subject_id='bob',principal_id='b'*64)
    assert not asyncio.run(ai.capabilities(bob,request(subject_id='bob')))['automatic']
    with pytest.raises(ContextSpaceNotFound):asyncio.run(ai.respond(bob,request(subject_id='bob')))
    monkeypatch.delenv('MISTRAL_API_KEY')
    assert not asyncio.run(ai.capabilities(who,request()))['enabled']
    assert not calls and not json.loads(ledger.read_text())['calls']


def test_exhaustion_message_precedes_any_provider_request(tmp_path,monkeypatch):
    ai,who,_,_,calls,ledger,_,_=setup(tmp_path,monkeypatch,answer)
    state=json.loads(ledger.read_text());state['max_usd']='0.0023';ledger.write_text(json.dumps(state))
    with pytest.raises(ProviderBudgetExceeded):asyncio.run(ai.respond(who,request()))
    assert not calls and not json.loads(ledger.read_text())['calls']
