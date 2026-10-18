"""Offline QH-45 grants through the real adapter/ledger, HTTP MockTransport only."""
import asyncio
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import httpx
import pytest

from adapters.llm.mistral import ExperimentBudget
from adapters.llm.session_config import PrivateSessionFactory, configured_session_factory
from app.chat.sessions import ProviderSessions, ChatIdentity, SessionClosed
from app.chat.context import ChatContextUnavailable, ChatInputInvalid, ChatProviderUnavailable
from app.core.models import ContextSpaceNotFound, Message, MessageRole
from tests.test_chat_service import case, request
from tests.test_chat_context import revision


def setup(tmp_path, monkeypatch, handler=None, rows=None, **limits):
    monkeypatch.setenv('MISTRAL_API_KEY', 'synthetic-qh45-offline-key')
    now = datetime.now(timezone.utc)
    receipt = dict(purpose='QH-45 interactive chat', owner_authorized=True,
        model='mistral-small-2603', expires_at=(now+timedelta(hours=1)).isoformat(),
        pricing_verified_at=now.isoformat(), eur_per_usd_upper_bound='2',
        input_usd_per_million='0.15', output_usd_per_million='0.60',
        grants=[dict(subject_id='alice', context_id='space')], **limits)
    auth = tmp_path/'auth.json'; auth.write_text(json.dumps(receipt)); auth.chmod(0o600)
    ledger = tmp_path/'ledger.json'; ExperimentBudget(ledger, create=True)
    data = json.loads(ledger.read_text()); data['purpose'] = receipt['purpose']; ledger.write_text(json.dumps(data))
    calls = []
    def simulated(r):
        calls.append(json.loads(r.content))
        if handler:
            return handler(r)
        return httpx.Response(200, json=dict(model='mistral-small-2603',
            usage=dict(prompt_tokens=100, completion_tokens=20), choices=[dict(finish_reason='stop',
            message=dict(content=json.dumps(dict(answer='Controllo generativo simulato.', reference_aliases=['R1'], insufficient_context=False))))]))
    factory = PrivateSessionFactory(authorization_path=auth, ledger_path=ledger,
                                   transport=httpx.MockTransport(simulated))
    chat, context, _, owner = case(rows)
    clock = [now.timestamp()]
    sessions = ProviderSessions(chat=chat, factory=factory, clock=lambda: clock[0])
    identity = ChatIdentity('alice', clock[0]+120, 'verified-token-hash')
    return sessions, identity, context, owner, calls, ledger, clock


async def active(s, identity, req=None):
    p = await s.preview(identity, req or request())
    return await s.consent(identity, request(), p['session_id'], snapshot_sha256=p['snapshot_sha256'], consent=True)


def test_default_disabled_even_with_key(monkeypatch):
    monkeypatch.delenv('QH_CHAT_SESSIONS_ENABLED', raising=False)
    monkeypatch.setenv('MISTRAL_API_KEY', 'synthetic-unused-key')
    assert configured_session_factory() is None


def test_explicit_preview_separate_consent_multiturn_exact_references_and_ledger(tmp_path, monkeypatch):
    s, who, _, _, calls, ledger, _ = setup(tmp_path, monkeypatch)
    async def run():
        p = await s.preview(who, request())
        assert p['expires_at'] == who.expires_at and p['state'] == 'preview'
        assert p['provider_messages'][-1]['content'] == request().messages[-1].content
        assert not calls and not json.loads(ledger.read_text())['calls']
        with pytest.raises(SessionClosed): await s.respond(who, request(), p['session_id'])
        for consent, digest in [(False,p['snapshot_sha256']),(True,'wrong')]:
            with pytest.raises(ChatInputInvalid):
                await s.consent(who, request(), p['session_id'], snapshot_sha256=digest, consent=consent)
        await s.consent(who, request(), p['session_id'], snapshot_sha256=p['snapshot_sha256'], consent=True)
        assert not calls
        result = await s.respond(who, request(), p['session_id'])
        assert result.model == 'mistral-small-2603' and result.references == (revision(),)
        follow = request(messages=(*request().messages, result.message, Message(role=MessageRole.USER,content='E poi?')))
        await s.respond(who, follow, p['session_id'])
        assert len(calls)==2 and len(calls[-1]['messages'])==5
        status = await s.status(who, request(), p['session_id'])
        assert status['accounting']['calls']==2
    asyncio.run(run())
    assert 'synthetic-qh45-offline-key' not in ledger.read_text()
    assert all(c['session_id'] for c in json.loads(ledger.read_text())['calls'])


@pytest.mark.parametrize('when',['preview','consent','generate','after'])
def test_policy_and_graph_changes_fail_closed(tmp_path, monkeypatch, when):
    s, who, context, owner, calls, _, _ = setup(tmp_path, monkeypatch)
    async def run():
        if when=='preview':
            owner[0]='bob'
            with pytest.raises(ContextSpaceNotFound): await s.preview(who, request())
            assert not context.calls
            return
        p=await s.preview(who,request())
        if when=='consent':
            context.values[0].content['text']='changed in place'
            with pytest.raises(ChatContextUnavailable): await s.consent(who,request(),p['session_id'],snapshot_sha256=p['snapshot_sha256'],consent=True)
            return
        await s.consent(who,request(),p['session_id'],snapshot_sha256=p['snapshot_sha256'],consent=True)
        if when=='generate':
            context.values[0].content['text']='changed'
        else:
            original=s.chat.respond
            async def changed(*a,**kw):
                result=await original(*a,**kw);owner[0]='bob';return result
            s.chat.respond=changed
        with pytest.raises(ChatProviderUnavailable): await s.respond(who,request(),p['session_id'])
    asyncio.run(run());assert len(calls)==(1 if when=='after' else 0)


def test_subject_space_token_and_proposal_choices_cannot_reuse_grant(tmp_path, monkeypatch):
    s,who,_,_,calls,_,_=setup(tmp_path,monkeypatch)
    async def run():
        p=await active(s,who)
        with pytest.raises(ContextSpaceNotFound):await s.status(replace(who,subject_id='bob'),request(subject_id='bob'),p['session_id'])
        with pytest.raises(ContextSpaceNotFound):await s.status(who,request(context_id='foreign'),p['session_id'])
        with pytest.raises(SessionClosed):await s.respond(who,request(include_proposed=True),p['session_id'])
        with pytest.raises(SessionClosed):await s.status(replace(who,credential_id='new-login-token'),request(),p['session_id'])
    asyncio.run(run());assert not calls


def test_proposed_opt_in_and_no_canonical_writes(tmp_path,monkeypatch):
    row=revision(validation_state='proposed',is_current_confirmed=False)
    s,who,context,_,calls,_,_=setup(tmp_path,monkeypatch,rows=[row])
    async def run():
        with pytest.raises(ChatInputInvalid):await s.preview(who,request())
        p=await active(s,who,request(include_proposed=True))
        result=await s.respond(who,request(include_proposed=True),p['session_id'])
        assert result.provided_revisions==(row,) and not result.references[0].is_current_confirmed
        assert json.loads(calls[0]['messages'][1]['content'])['revisions'][0]['validation_state']=='proposed'
    asyncio.run(run());assert context.values==[row]


@pytest.mark.parametrize('mode',['expiry','revoke','restart'])
def test_expiry_revoke_restart_never_resume(tmp_path,monkeypatch,mode):
    s,who,_,_,calls,_,clock=setup(tmp_path,monkeypatch)
    async def run():
        p=await active(s,who)
        if mode=='expiry':clock[0]=who.expires_at
        elif mode=='revoke':await s.revoke(who,request(),p['session_id'])
        else:s.grants.clear()
        with pytest.raises((SessionClosed,ContextSpaceNotFound)):await s.respond(who,request(),p['session_id'])
    asyncio.run(run());assert not calls


def test_inflight_revocation_and_concurrent_request_discard_response(tmp_path,monkeypatch):
    s,who,_,_,calls,ledger,_=setup(tmp_path,monkeypatch)
    async def run():
        p=await active(s,who);grant=s.grants[p['session_id']]
        original=grant.binding.provider.generate
        entered=asyncio.Event();release=asyncio.Event()
        async def paused(req):
            entered.set();await release.wait();return await original(req)
        grant.binding.provider.generate=paused
        pending=asyncio.create_task(s.respond(who,request(),p['session_id']))
        await entered.wait()
        with pytest.raises(SessionClosed):await s.respond(who,request(),p['session_id'])
        await s.revoke(who,request(),p['session_id']);release.set()
        with pytest.raises(ChatProviderUnavailable):await pending
        assert grant.state=='revoked'
    asyncio.run(run());assert len(calls)==1 and len(json.loads(ledger.read_text())['calls'])==1


@pytest.mark.parametrize('failure',['429','401','timeout','json','aliases'])
def test_provider_failure_stops_session_without_retry(tmp_path,monkeypatch,failure):
    def handler(r):
        if failure in ['429','401']:return httpx.Response(int(failure),json={'message':'private-provider-error'})
        if failure=='timeout':raise httpx.ReadTimeout('private',request=r)
        content='bad-json' if failure=='json' else json.dumps(dict(answer='x',reference_aliases=['foreign'],insufficient_context=False))
        return httpx.Response(200,json=dict(model='mistral-small-2603',usage=dict(prompt_tokens=100,completion_tokens=20),choices=[dict(finish_reason='stop',message=dict(content=content))]))
    s,who,_,_,calls,ledger,_=setup(tmp_path,monkeypatch,handler)
    async def run():
        p=await active(s,who)
        with pytest.raises(ChatProviderUnavailable):await s.respond(who,request(),p['session_id'])
        with pytest.raises(SessionClosed):await s.respond(who,request(),p['session_id'])
    asyncio.run(run());assert len(calls)==1 and len(json.loads(ledger.read_text())['calls'])==1


def test_session_and_aggregate_limits_survive_new_grants(tmp_path,monkeypatch):
    s,who,_,_,calls,ledger,_=setup(tmp_path,monkeypatch)
    async def run():
        p=await active(s,who)
        for _ in range(3):await s.respond(who,request(),p['session_id'])
        with pytest.raises(ChatProviderUnavailable):await s.respond(who,request(),p['session_id'])
        for _ in range(2):
            p=await active(s,who)
            for _ in range(min(3,8-len(calls))):await s.respond(who,request(),p['session_id'])
        assert len(calls)==8
        p=await active(s,who)
        with pytest.raises(ChatProviderUnavailable):await s.respond(who,request(),p['session_id'])
    asyncio.run(run());assert len(json.loads(ledger.read_text())['calls'])==8


def test_small_session_budget_reserves_before_disclosure(tmp_path,monkeypatch):
    s,who,_,_,calls,ledger,_=setup(tmp_path,monkeypatch,max_session_usd='0.0001')
    async def run():
        p=await active(s,who)
        with pytest.raises(ChatProviderUnavailable):await s.respond(who,request(),p['session_id'])
    asyncio.run(run());assert not calls and not json.loads(ledger.read_text())['calls']


def test_pending_reservation_survives_reopen_and_blocks_other_session(tmp_path,monkeypatch):
    from decimal import Decimal
    from adapters.llm.session_config import SessionBudget
    from adapters.llm.mistral import MistralError
    s,_,_,_,calls,ledger,_=setup(tmp_path,monkeypatch)
    original=SessionBudget(s.factory.ledger,'crashed-session',3,'0.01')
    original.reserve('test-pending',Decimal('0.0024'))
    reopened=SessionBudget(ExperimentBudget(ledger),'new-session',3,'0.01')
    with pytest.raises(MistralError):reopened.reserve('test-next',Decimal('0.0024'))
    assert not calls and len(json.loads(ledger.read_text())['calls'])==1


def test_cross_session_reservations_are_atomic_under_concurrency(tmp_path,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from decimal import Decimal
    from adapters.llm.session_config import SessionBudget
    from adapters.llm.mistral import MistralError
    s,_,_,_,calls,ledger,_=setup(tmp_path,monkeypatch)
    def reserve(index):
        try:
            return SessionBudget(s.factory.ledger,str(index),3,'0.01').reserve('parallel',Decimal('0.0024'))
        except MistralError:return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(reserve,[1,2]))
    assert sum(x is not None for x in outcomes)==1
    assert len(json.loads(ledger.read_text())['calls'])==1 and not calls


def test_duration_is_capped_at_five_minutes_not_renewed_by_status(tmp_path,monkeypatch):
    s,who,_,_,_,_,clock=setup(tmp_path,monkeypatch)
    who=replace(who,expires_at=clock[0]+1000)
    async def run():
        p=await active(s,who);assert p['expires_at']==clock[0]+300
        clock[0]+=100
        assert (await s.status(who,request(),p['session_id']))['expires_at']==p['expires_at']
    asyncio.run(run())


def test_unknown_context_changes_outside_sent_budget_still_require_consent(tmp_path,monkeypatch):
    huge=revision(revision_id='other',content={'text':'x'*10000})
    s,who,context,_,calls,_,_=setup(tmp_path,monkeypatch,rows=[revision(),huge])
    async def run():
        p=await active(s,who);assert p['partial_coverage'] and len(p['provided_revisions'])==1
        context.values[1].content['text']='y'*10000
        with pytest.raises(ChatProviderUnavailable):await s.respond(who,request(),p['session_id'])
    asyncio.run(run());assert not calls


@pytest.mark.parametrize('amount',['-1','NaN','Infinity'])
def test_malformed_durable_costs_fail_before_http(tmp_path,monkeypatch,amount):
    s,who,_,_,calls,ledger,_=setup(tmp_path,monkeypatch)
    state=json.loads(ledger.read_text());state['calls']=[dict(kind='old',status='completed',reserved_usd=amount)]
    ledger.write_text(json.dumps(state))
    async def run():
        p=await active(s,who)
        with pytest.raises(ChatProviderUnavailable):await s.respond(who,request(),p['session_id'])
    asyncio.run(run());assert not calls


def test_graph_unavailability_and_changed_system_prompt_require_new_consent(tmp_path,monkeypatch):
    from app.core.models import ContextRetrievalUnavailable
    s,who,context,_,calls,_,_=setup(tmp_path,monkeypatch)
    async def run():
        p=await active(s,who)
        async def unavailable(request):raise ContextRetrievalUnavailable('private-graph-detail')
        context.browse=unavailable
        with pytest.raises(ChatProviderUnavailable):await s.respond(who,request(),p['session_id'])
    asyncio.run(run());assert not calls


def test_changed_system_prompt_cannot_reuse_exact_payload_consent(tmp_path,monkeypatch):
    import app.chat.context as formatting
    s,who,_,_,calls,_,_=setup(tmp_path,monkeypatch)
    async def run():
        p=await active(s,who)
        monkeypatch.setattr(formatting,'SYSTEM',formatting.SYSTEM+'Changed instructions')
        with pytest.raises(ChatProviderUnavailable):await s.respond(who,request(),p['session_id'])
    asyncio.run(run());assert not calls
