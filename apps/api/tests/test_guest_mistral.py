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
from app.core.models import GuestAccess,ProviderBudgetExceeded
from app.projections.guest import GuestDenied,GuestUnavailable
from tests.test_chat_sessions import setup as session_setup

PAYLOAD=dict(format='qh.disclosure/1',items=[dict(reference='R1',text='Nous voulons organiser un atelier.',
    validation_state='proposed',sources=['S1'])])
ANSWER=dict(answer='Le snapshot propose d’organiser un atelier.',reference_aliases=['R1'],insufficient_context=False,support_basis='canonical')


def selection_reply(value,payload):
    refs={ref for subject in value.get('subjects',[]) for ref in subject['reference_aliases']} or set(value['reference_aliases'])
    groups=([subject['reference_aliases'] for subject in value['subjects']] if value.get('subjects') else
        value.get('referents', [list(value['reference_aliases'])] if refs else []))
    rows={i['reference']:dict(subject_type='Synthetic type',matches_subject=i['reference'] in refs,
        matches_conditions=True) for i in payload['items']}
    if refs-set(rows) or any(len(set(group))!=len(group) or not set(group)<=refs for group in groups):
        rows['OUTSIDE']=dict(subject_type='forged',matches_subject=True,matches_conditions=True)
    return dict(requested_subject='Synthetic requested subject',assessments=rows)



def composition_reply(value,packet):
    subjects=value.get('subjects',[])
    sections={key:next((subject['text'] for subject in subjects if set(subject['reference_aliases'])==set(refs)),value['answer'])
        for key,refs in packet['subjects'].items()}
    if value.get('_missing_section'):sections={}
    return dict(sections=sections,insufficient_context=value['insufficient_context'])


def wire_reply(value,packet,wire):
    if 'assessments' in wire['response_format']['json_schema']['schema']['properties']:
        return selection_reply(value,packet['snapshot'])
    return composition_reply(value,packet)


def setup(tmp_path,monkeypatch,answer=None,status=200,subject='alice',handler=None):
    def simulated(request):
        wire=json.loads(request.content)
        assert wire['model']=='mistral-small-2603' and 'max_tokens' not in wire
        packet=json.loads(wire['messages'][1]['content'])
        assert set(packet)<={'snapshot','question','conversation_references','subjects','language','coverage'}
        allowed={i['reference']:i for i in question_payload(PAYLOAD)['items']}
        assert all(allowed[i['reference']]==i for i in packet['snapshot']['items'])
        assert 'history' not in packet
        assert all(ref in {i['reference'] for i in PAYLOAD['items']} for turn in packet.get('conversation_references',[]) for group in turn for ref in group)
        assert wire['tool_choice']=='none'
        if handler:handler()
        return httpx.Response(status,json=dict(model='mistral-small-2603',usage=dict(prompt_tokens=100,completion_tokens=30),
            choices=[dict(finish_reason='stop',message=dict(content=json.dumps(wire_reply(answer or ANSWER,packet,wire))))]))
    s,_,_,_,calls,ledger,clock=session_setup(tmp_path,monkeypatch,handler=simulated)
    auth=s.factory.authorization_path;r=json.loads(auth.read_text())
    r.update(development_account=dict(environment='development',subject_id=subject,principal_id='a'*64),
        development_budget=dict(max_calls=None,max_usd='5.00',max_eur='10.00',eur_per_usd_upper_bound='2'),guest_snapshot_access=AUTHORIZATION)
    auth.write_text(json.dumps(r));state=json.loads(ledger.read_text());state.update(max_calls=None,max_usd='5.00');ledger.write_text(json.dumps(state))
    factory=PrivateSessionFactory(authorization_path=auth,ledger_path=ledger,transport=s.factory.transport,pricing=s.factory.pricing)
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
            assert result['accounting']['cost_usd']=='0.000066'
        assert Decimal(result['budget']['remaining_usd'])==Decimal('5')-42*Decimal('0.000033')
    asyncio.run(run());assert len(calls)==42
    state=json.loads(ledger.read_text());assert len(state['calls'])==42 and all('session_id' not in r for r in state['calls'])


@pytest.mark.parametrize('mode',['missing-right','foreign-owner','wrong-provider','revoked-before','revoked-after','changed-after','bad-alias','missing-section','hazard','budget','credit','pending','http429'])
def test_guards_no_leak_no_retry_and_accounting(tmp_path,monkeypatch,mode):
    answer={**ANSWER}
    if mode=='bad-alias':answer['reference_aliases']=['OUTSIDE']
    if mode=='missing-section':answer['_missing_section']=True
    if mode=='hazard':answer['answer']='Un diagnostic de cancer est disponible.'
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
    if mode=='pending':state['calls']=[dict(status='pending',reserved_usd='0.1572864')]
    ledger.write_text(json.dumps(state))
    with pytest.raises((GuestDenied,GuestUnavailable,ProviderBudgetExceeded)):asyncio.run(chat.ask('token','snapshot','Question synthétique'))
    assert len(calls)==(2 if mode in ('missing-section','hazard') else 1 if mode in ('revoked-after','changed-after','bad-alias','http429') else 0)
    if calls:
        final=json.loads(ledger.read_text());assert final['calls'][-1]['status']==('failed' if mode=='http429' else 'completed')
        assert final['blocked']==(mode=='http429')


def test_history_and_credit_ceiling_are_not_double_counted_or_reset():
    state=dict(max_usd='5',historical_external_usd='0.03',credit_guard=dict(max_committed_usd='4.3'),
        calls=[dict(observed_usd='0.01',reserved_usd='0.15'),dict(reserved_usd='0.15')])
    assert committed_cost(state)==Decimal('0.19')
    assert effective_ceiling(state,Decimal('5'))==Decimal('4.3')


def test_budget_exhausted_after_selection_prevents_composition_without_retry(tmp_path,monkeypatch):
    chat,calls,ledger,grant=setup(tmp_path,monkeypatch)
    state=json.loads(ledger.read_text());state['max_usd']='0.15730';ledger.write_text(json.dumps(state))
    with pytest.raises(ProviderBudgetExceeded):asyncio.run(chat.ask('token',grant.snapshot_id,'Quel objectif ?'))
    final=json.loads(ledger.read_text())
    assert len(calls)==1 and final['calls'][-1]['status']=='completed' and not final['blocked']
    assert final['max_usd']=='0.15730' and final['calls'][-1]['observed_usd']=='0.000033'


def test_missing_requested_candidate_cannot_be_hidden_by_composition(tmp_path,monkeypatch):
    payload=dict(format='qh.disclosure/1',items=[dict(reference='R1',text='Décision adoptée en 2024.')])
    monkeypatch.setitem(globals(),'PAYLOAD',payload)
    value=dict(answer='One supported decision in 2024.',reference_aliases=['R1'],support_basis='canonical',insufficient_context=False)
    chat,calls,_,grant=setup(tmp_path,monkeypatch,value)
    result=asyncio.run(chat.ask('token',grant.snapshot_id,'The last two decisions?'))
    assert len(calls)==2 and result['insufficient_context'] and result['support_basis']=='canonical'
    assert result['reference_aliases']==['R1']


def test_large_enumeration_clears_previous_reference_list_without_truncation(tmp_path,monkeypatch):
    payload=dict(format='qh.disclosure/1',items=[dict(reference=f'R{i}',text=f'Event {i}.') for i in range(1,10)])
    monkeypatch.setitem(globals(),'PAYLOAD',payload)
    value=dict(answer='unused',reference_aliases=[i['reference'] for i in payload['items']],insufficient_context=False,support_basis='canonical',
        subjects=[dict(text=i['text'],reference_aliases=[i['reference']]) for i in payload['items']])
    chat,calls,_,grant=setup(tmp_path,monkeypatch,value)
    chat.references.append(grant.session_id,grant.snapshot_id,payload,[['R1'],['R2']])
    result=asyncio.run(chat.ask('token',grant.snapshot_id,'List all events.'))
    assert '9. Event 9.' in result['answer'] and len(result['reference_aliases'])==9
    assert not chat.references.entries
    result=asyncio.run(chat.ask('token',grant.snapshot_id,'The second'))
    assert not result['reference_aliases'] and len(calls)==2


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
    assert result['insufficient_context'] and result['answer'] == value['answer'] and len(calls) == 2
