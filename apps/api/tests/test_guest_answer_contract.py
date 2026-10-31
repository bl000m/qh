"""Synthetic minimal reproductions of the actual HTTP-200 rejection patterns."""
import asyncio
import json

import pytest

from app.chat.snapshot_answer import SnapshotAnswerError, decode_snapshot_answer, projection_request
from app.core.models import Message, MessageRole
from tests.test_guest_mistral import setup, PAYLOAD


@pytest.mark.parametrize('answer,code',[
    (dict(answer='Contenuto disponibile.',reference_aliases=['R1'],support_basis='dialogue',insufficient_context=False),'guest.invalid_snapshot_support'),
    (dict(answer='Contenuto disponibile [R1].',reference_aliases=['R1'],support_basis='canonical',insufficient_context=False),'guest.internal_structure_in_answer'),
])
def test_real_failure_patterns_stay_rejected_with_precise_private_codes(tmp_path,monkeypatch,answer,code):
    with pytest.raises(SnapshotAnswerError) as error:
        decode_snapshot_answer(Message(role=MessageRole.ASSISTANT,content=json.dumps(answer)),PAYLOAD)
    assert error.value.code==code
    if code=='guest.invalid_snapshot_support':return  # Composer citations are now assigned by the server.
    chat,calls,_,grant=setup(tmp_path,monkeypatch,answer)
    if code=='guest.internal_structure_in_answer':
        result=asyncio.run(chat.ask('token',grant.snapshot_id,'Pourquoi cette confusion ?'))
        assert result['support_basis']=='dialogue' and result['reference_aliases']==[]
        assert 'R1' not in result['answer']
    diagnostics=[json.loads(p.read_text()) for p in chat.live.factory.diagnostics.path.glob('*.json')]
    rejected=[d for d in diagnostics if d['outcome']=='rejected']
    assert len(calls)==2 and len(rejected)==1
    assert rejected[0]['checks'][-1]['reason']==code


@pytest.mark.parametrize('basis,refs,text',[
    ('canonical',['R1'],'È previsto un atelier.'),
    ('dialogue',[],'Vuoi conoscere gli obiettivi o il programma?'),
])
def test_contract_explains_and_accepts_valid_knowledge_or_clarification(basis,refs,text):
    request=projection_request(PAYLOAD,'Quali dati?',history=[dict(role='user',content='Il progetto?'),dict(role='assistant',content='Quale aspetto?')])
    assert request.output_schema['properties']['answer']['description']
    assert 'Nonempty requires canonical or mixed' in request.output_schema['properties']['reference_aliases']['description']
    value=decode_snapshot_answer(Message(role=MessageRole.ASSISTANT,content=json.dumps(dict(
        answer=text,reference_aliases=refs,support_basis=basis,insufficient_context=False))),PAYLOAD)
    assert value['answer']==text


def test_structured_subjects_are_the_single_authorized_citation_authority():
    payload=dict(format='qh.disclosure/1',items=[dict(reference=f'R{i}',text=f'Authorized fact {i}') for i in range(1,21)])
    refs=[item['reference'] for item in payload['items']]
    value=dict(answer='Unused draft.',reference_aliases=['R1'],support_basis='canonical',insufficient_context=False,
        subjects=[dict(text='A complete authorized overview.',reference_aliases=refs)])
    result=decode_snapshot_answer(Message(role=MessageRole.ASSISTANT,content=json.dumps(value)),payload)
    assert result['reference_aliases']==refs and result['referents']==[refs]
    assert result['answer']=='1. A complete authorized overview.'
    value['subjects'][0]['reference_aliases']=['OUTSIDE']
    with pytest.raises(SnapshotAnswerError,match='guest.invalid_subject_support'):
        decode_snapshot_answer(Message(role=MessageRole.ASSISTANT,content=json.dumps(value)),payload)
