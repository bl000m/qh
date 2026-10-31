"""Paid path exercised only with synthetic fixtures and HTTP MockTransport."""
import asyncio
from dataclasses import replace
from decimal import Decimal
import json
from unittest.mock import AsyncMock

import httpx
import pytest

from adapters.llm.guest_mistral import AUTHORIZATION,MistralSnapshotAnswers
from adapters.llm.guest_offline import OfflineSnapshotProvider
from adapters.llm.mistral import committed_cost,effective_ceiling
from adapters.llm.session_config import PrivateSessionFactory
from app.chat.guest import GuestSnapshotChat, question_payload
from app.core.models import GuestAccess,ProviderBudgetExceeded,ProviderFailure
from app.projections.guest import GuestDenied,GuestUnavailable
from tests.test_chat_sessions import setup as session_setup

PAYLOAD=dict(format='qh.disclosure/1',items=[dict(reference='R1',text='Nous voulons organiser un atelier.',
    validation_state='proposed',sources=['S1'])])
ANSWER=dict(answer='Le snapshot propose d’organiser un atelier.',reference_aliases=['R1'],insufficient_context=False,support_basis='canonical')


def setup(tmp_path,monkeypatch,answer=None,status=200,subject='alice',handler=None):
    def simulated(request):
        wire=json.loads(request.content)
        assert wire['model']=='mistral-small-2603' and 'max_tokens' not in wire
        packet=json.loads(wire['messages'][1]['content'])
        assert set(packet)<={'snapshot','question','conversation'}
        allowed={i['reference']:i for i in question_payload(PAYLOAD)['items']}
        assert all(allowed[i['reference']]==i for i in packet['snapshot']['items'])
        assert wire['tool_choice']=='none' and 'answer' in wire['response_format']['json_schema']['schema']['properties']
        if handler:handler(packet)
        return httpx.Response(status,json=dict(model='mistral-small-2603',usage=dict(prompt_tokens=100,completion_tokens=30),
            choices=[dict(finish_reason='stop',message=dict(content=json.dumps(answer or ANSWER)))]))
    s,_,_,_,calls,ledger,clock=session_setup(tmp_path,monkeypatch,handler=simulated)
    auth=s.factory.authorization_path;r=json.loads(auth.read_text())
    r.update(development_account=dict(environment='development',subject_id=subject,principal_id='a'*64),
        development_budget=dict(max_calls=None,max_usd='5.00',max_eur='10.00',eur_per_usd_upper_bound='2'),guest_snapshot_access=AUTHORIZATION)
    auth.write_text(json.dumps(r));state=json.loads(ledger.read_text());state.update(max_calls=None,max_usd='5.00');ledger.write_text(json.dumps(state))
    factory=PrivateSessionFactory(authorization_path=auth,ledger_path=ledger,transport=s.factory.transport)
    live=MistralSnapshotAnswers(factory)
    grant=GuestAccess(session_id='session',invitation_id='invite',context_id='space',snapshot_id='snapshot',rights=('READ','ASK_AI'),expires_at=__import__('datetime').datetime.fromtimestamp(clock[0]+60,__import__('datetime').timezone.utc),provider='mistral-small-2603',owner_id=subject)
    guest=AsyncMock();guest.session.return_value=grant;guest.snapshot.return_value=PAYLOAD
    return GuestSnapshotChat(guest=guest,provider=OfflineSnapshotProvider(),live=live),calls,ledger,grant


def test_real_path_mocked_21_requests_share_ledger_without_session_quota(tmp_path,monkeypatch):
    chat,calls,ledger,_=setup(tmp_path,monkeypatch)
    async def run():
        assert not calls
        for _ in range(21):
            result=await chat.ask('token','snapshot','Quel est l’objectif ?')
            assert result['model']=='mistral-small-2603' and not result['simulated']
            assert result['accounting']['cost_usd']=='0.000033'
        assert Decimal(result['budget']['remaining_usd'])==Decimal('5')-21*Decimal('0.000033')
    asyncio.run(run());assert len(calls)==21
    state=json.loads(ledger.read_text());assert len(state['calls'])==21 and all('session_id' not in r for r in state['calls'])


@pytest.mark.parametrize('mode',['missing-right','foreign-owner','wrong-provider','revoked-before','revoked-after','changed-after','bad-alias','budget','credit','http429'])
def test_guards_no_leak_no_retry_and_accounting(tmp_path,monkeypatch,mode):
    answer={**ANSWER}
    if mode=='bad-alias':answer['reference_aliases']=['OUTSIDE']
    chat,calls,ledger,grant=setup(tmp_path,monkeypatch,answer,status=429 if mode=='http429' else 200)
    if mode=='missing-right':chat.guest.snapshot.side_effect=GuestDenied('denied')
    if mode=='foreign-owner':chat.guest.session.return_value=replace(grant,owner_id='bob')
    if mode=='wrong-provider':chat.guest.session.return_value=replace(grant,provider='other-model')
    if mode=='revoked-before':chat.guest.snapshot.side_effect=[PAYLOAD,GuestDenied('denied')]
    if mode=='revoked-after':chat.guest.snapshot.side_effect=[PAYLOAD,PAYLOAD,GuestDenied('denied')]
    if mode=='changed-after':chat.guest.snapshot.side_effect=[PAYLOAD,PAYLOAD,dict(PAYLOAD,items=[])]
    state=json.loads(ledger.read_text())
    if mode=='budget':state['max_usd']='0.15'
    if mode=='credit':state.update(historical_external_usd='0.03',credit_guard=dict(max_committed_usd='0.18'))
    ledger.write_text(json.dumps(state))
    with pytest.raises((GuestDenied,GuestUnavailable,ProviderBudgetExceeded,ProviderFailure)):asyncio.run(chat.ask('token','snapshot','Question synthétique'))
    assert len(calls)==(1 if mode in ('revoked-after','changed-after','bad-alias','http429') else 0)
    if calls:
        final=json.loads(ledger.read_text());assert final['calls'][-1]['status']==('failed' if mode=='http429' else 'completed')
        assert not final['blocked']  # One rate-limited or rejected answer never suspends the AI.


def test_shared_knowledge_reaches_the_guest_without_masking_or_keyword_refusal(tmp_path,monkeypatch):
    payload=dict(format='qh.disclosure/1',items=[dict(reference='R1',text='Visite médicale le 01/09/2021, tél. 06 12 34 56 78.',
        validation_state='proposed',sources=['S1'])])
    monkeypatch.setitem(globals(),'PAYLOAD',payload)
    value=dict(answer='Visite médicale le 01/09/2021, tél. 06 12 34 56 78.',reference_aliases=['R1'],insufficient_context=False,support_basis='canonical')
    chat,calls,_,_=setup(tmp_path,monkeypatch,value)
    chat.guest.snapshot.return_value=payload
    result=asyncio.run(chat.ask('token','snapshot','Quand et comment joindre ?'))
    assert result['answer']==value['answer'] and len(calls)==1


def test_followups_reach_the_single_generation_as_untrusted_conversation(tmp_path,monkeypatch):
    seen=[]
    chat,calls,_,_=setup(tmp_path,monkeypatch,handler=seen.append)
    history=[dict(role='user',content='Quelles sont les deux dernières expériences ?'),dict(role='assistant',content='Une mission puis un CDI.')]
    asyncio.run(chat.ask('token','snapshot','Détaille la deuxième',history))
    assert len(calls)==1 and seen[0]['conversation']==history and seen[0]['question']=='Détaille la deuxième'


def test_pending_reservation_does_not_suspend_guest_answers(tmp_path,monkeypatch):
    chat,calls,ledger,_=setup(tmp_path,monkeypatch)
    state=json.loads(ledger.read_text());state['calls']=[dict(kind='/chat/completions',status='pending',reserved_usd='0.1572864')];ledger.write_text(json.dumps(state))
    asyncio.run(chat.ask('token','snapshot','Quel objectif ?'))
    assert len(calls)==1 and [c['status'] for c in json.loads(ledger.read_text())['calls']]==['pending','completed']


def test_history_and_credit_ceiling_are_not_double_counted_or_reset():
    state=dict(max_usd='5',historical_external_usd='0.03',credit_guard=dict(max_committed_usd='4.3'),
        calls=[dict(observed_usd='0.01',reserved_usd='0.15'),dict(reserved_usd='0.15')])
    assert committed_cost(state)==Decimal('0.19')
    assert effective_ceiling(state,Decimal('5'))==Decimal('4.3')


def test_dialogue_and_incomplete_warning_remain_independent(tmp_path,monkeypatch):
    value=dict(answer='Pouvez-vous préciser votre question ?',reference_aliases=[],support_basis='dialogue',insufficient_context=True)
    chat,_,_,_=setup(tmp_path,monkeypatch,value)
    result=asyncio.run(chat.ask('token','snapshot','Quel détail faudrait-il préciser ?'))
    assert result['insufficient_context'] and result['support_basis']=='dialogue'


def test_disabled_live_binding_keeps_readonly_status_without_fallback(tmp_path,monkeypatch):
    chat,calls,_,_=setup(tmp_path,monkeypatch);chat.live=None
    status=asyncio.run(chat.status('token'))
    assert not status['enabled'] and not status['simulated'] and status['model']=='mistral-small-2603'
    with pytest.raises(GuestDenied):asyncio.run(chat.ask('token','snapshot','Question'))
    assert not calls


def test_missing_workshop_steps_remain_explicit_in_snapshot_only_answer(tmp_path, monkeypatch):
    value = dict(answer='Les trente étapes ne sont pas présentes dans les informations autorisées.',
        reference_aliases=['R1'], support_basis='canonical', insufficient_context=True)
    chat, calls, _, _ = setup(tmp_path, monkeypatch, value)
    result = asyncio.run(chat.ask('token', 'snapshot', 'Donne les trente étapes complètes.'))
    assert result['insufficient_context'] and result['answer'] == value['answer'] and len(calls) == 1
