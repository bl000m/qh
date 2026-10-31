"""Synthetic minimal reproductions of rejected answers; one generation, no retry."""
import asyncio
import json

import pytest

from app.chat.snapshot_answer import SnapshotAnswerError, decode_snapshot_answer, projection_request
from app.core.models import Message, MessageRole
from app.projections.guest import GuestUnavailable
from tests.test_guest_mistral import setup, PAYLOAD


@pytest.mark.parametrize('answer,code',[
    (dict(answer='Contenuto disponibile.',reference_aliases=['R1'],support_basis='dialogue',insufficient_context=False),'guest.invalid_snapshot_support'),
    (dict(answer='Contenuto disponibile [R1].',reference_aliases=['R1'],support_basis='canonical',insufficient_context=False),'guest.internal_structure_in_answer'),
    (dict(answer='Contenuto.',reference_aliases=['R1'],support_basis='canonical',insufficient_context=False,subjects=[]),'guest.invalid_answer_fields'),
])
def test_rejected_answers_keep_precise_private_codes_without_retry(tmp_path,monkeypatch,answer,code):
    with pytest.raises(SnapshotAnswerError) as error:
        decode_snapshot_answer(Message(role=MessageRole.ASSISTANT,content=json.dumps(answer)),PAYLOAD)
    assert error.value.code==code
    chat,calls,_,grant=setup(tmp_path,monkeypatch,answer)
    with pytest.raises(GuestUnavailable):asyncio.run(chat.ask('token',grant.snapshot_id,'Pourquoi ?'))
    diagnostics=[json.loads(p.read_text()) for p in chat.live.factory.diagnostics.path.glob('*.json')]
    rejected=[d for d in diagnostics if d['outcome']=='rejected']
    assert len(calls)==1 and len(rejected)==1 and rejected[0]['checks'][-1]['reason']==code


@pytest.mark.parametrize('basis,refs,text',[
    ('canonical',['R1'],'È previsto un atelier.'),
    ('dialogue',[],'Vuoi conoscere gli obiettivi o il programma?'),
    ('canonical',['R1'],'Competenze: AWS S3, R2 di Cloudflare, 2019-2023.'),
])
def test_contract_accepts_valid_knowledge_or_clarification(basis,refs,text):
    request=projection_request(PAYLOAD,'Quali dati?',history=[dict(role='user',content='Il progetto?'),dict(role='assistant',content='Quale aspetto?')])
    assert request.output_schema['properties']['answer']['description']
    assert set(request.output_schema['properties'])=={'answer','reference_aliases','insufficient_context','support_basis'}
    value=decode_snapshot_answer(Message(role=MessageRole.ASSISTANT,content=json.dumps(dict(
        answer=text,reference_aliases=refs,support_basis=basis,insufficient_context=False))),PAYLOAD)
    assert value['answer']==text


def test_prompt_is_generic_without_domain_rules():
    prompt=projection_request(PAYLOAD,'?').messages[0].content.casefold()
    assert not any(word in prompt for word in ('cv','expérience professionnelle','recette','budget','atelier','employeur'))
