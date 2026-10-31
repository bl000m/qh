"""Whole-understanding sharing independent of PDFs; legacy snapshots stay restricted."""
import asyncio
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.chat.conversation import conversational_reply
from app.chat.snapshot_answer import projection_request
from app.projections.document_scope import empty_projection, is_empty_projection, restrict_snapshot
from app.projections.disclosure import Candidate, Selection
from app.projections.disclosure_service import DisclosureService
from tests.test_disclosure import policy
from tests.test_unified_recap import projected_documents
from tests.test_consolidation import fixture, document
from tests.test_chat_service import request


def preview_service(rows,documents):
    scope=str(uuid4())
    from app.projections.drafts import RevisionKey
    candidates=tuple(Candidate(key=RevisionKey(item_id=r.item_id,revision_id=r.revision_id),state=r.validation_state) for r in rows)
    repo=Mock(select=AsyncMock(return_value=Selection(context_id=scope,stamp='s',candidates=candidates,name='RH',document_sources=documents)),
        prepare=AsyncMock(side_effect=lambda p:p))
    drafts=Mock(_allow=AsyncMock(),create=AsyncMock(return_value=SimpleNamespace(id=str(uuid4()),version=1)),
        resolve=AsyncMock(return_value=SimpleNamespace(revisions=rows)))
    return DisclosureService(drafts=drafts,repository=repo),scope


def test_pdf_grants_never_change_the_shared_understanding_or_recap():
    rows=projected_documents()
    documents=tuple(sorted({c['source_revision_id'] for r in rows for c in r.content['citations']}))
    service,scope=preview_service(rows,documents)
    frozen=deepcopy(rows)
    previews=[asyncio.run(service.prepare(str(uuid4()),scope,policy(knowledge_scope='context',original_documents=chosen)))
        for chosen in ((),documents[:1],documents)]
    knowledge=[{k:v for k,v in p.payload.items()} for p in previews]
    assert knowledge[0]==knowledge[1]==knowledge[2] and rows==frozen
    assert [i['text'] for i in knowledge[0]['items']]==[r.content['text'] for r in rows]
    assert knowledge[0]['recap']['title'] and not previews[0].report['exclusions']


@pytest.mark.parametrize('legacy',[{},{'include_quotes':True}])
def test_new_previews_require_whole_context_without_original_quotes(legacy):
    rows=projected_documents()
    service,scope=preview_service(rows,())
    with pytest.raises(ValueError):
        asyncio.run(service.prepare(str(uuid4()),scope,policy(**({'knowledge_scope':'context'} if legacy else {}),**legacy)))


def test_retained_snapshot_is_restricted_without_mutation_and_relations_close():
    original=dict(format='qh.disclosure/1',name='RH',recap={'title':'Unsafe','text':'Private'},items=[
        {'reference':'R1','text':'CV'}, {'reference':'R2','text':'Contract'},
        {'reference':'R3','text':'Mixed','relation':{'source':'R1','target':'R2'}}])
    frozen=deepcopy(original)
    safe=restrict_snapshot(original,{'R1','R3'})
    assert safe['items']==[original['items'][0]] and 'recap' not in safe
    assert 'Private' not in str(safe)
    assert is_empty_projection(restrict_snapshot(original,set())) and original==frozen


def test_retained_quote_snapshot_keeps_its_approved_quotes_and_new_items_have_none():
    import json
    from app.projections.guest_payload import recipient_payload
    legacy=dict(format='qh.disclosure/1',name='RH',items=[dict(reference='R1',text='Parcours déclaré.',validation_state='proposed',
        sources=['S1'],citations=[dict(source='S1',quote='Freelance - janvier 2022 a aout 2023.',redacted=False)])])
    recipient_payload(legacy,include_quotes=True)
    packet=json.loads(projection_request(legacy,'Quels détails ?').messages[1].content)
    assert packet['snapshot']['items'][0]['evidence_quotes']==['Freelance - janvier 2022 a aout 2023.']
    from app.projections.disclosure_guard import OutboundDisclosureGuard
    payload,_=OutboundDisclosureGuard().apply(projected_documents(),policy(knowledge_scope='context'))
    assert all('citations' not in item for item in payload['items'])
    assert 'quote' not in json.dumps(payload) and 'source_revision_id' not in json.dumps(payload)
    assert json.loads(projection_request(restrict_snapshot(legacy,set()),'?').messages[1].content)['snapshot']['items']==[]


def test_client_history_is_conversation_context_never_snapshot_knowledge():
    import json
    history=[{'role':'user','content':'Quelles sont les expériences ?'}, {'role':'assistant','content':'Deux missions.'}]
    packet=json.loads(projection_request({'format':'qh.disclosure/1','items':[{'reference':'R1','text':'Allowed CV'}]},'Et la deuxième ?',history).messages[1].content)
    assert packet['conversation']==history and packet['snapshot']['items']==[{'reference':'R1','text':'Allowed CV'}]
    assert 'conversation' not in json.loads(projection_request(empty_projection('RH'),'?').messages[1].content)


def test_empty_projection_skips_even_live_provider_and_rechecks_access():
    from app.chat.guest import GuestSnapshotChat
    live=Mock(answer_payload=AsyncMock())
    service=GuestSnapshotChat(guest=Mock(),provider=SimpleNamespace(id='offline'),live=live)
    recheck=AsyncMock()
    value=asyncio.run(service.answer_payload('owner','space','mistral-small-2603',empty_projection('RH'),'? ',recheck))
    assert value['insufficient_context'] and value['reference_aliases']==[]
    live.answer_payload.assert_not_awaited();recheck.assert_awaited_once()


def test_exact_conversational_messages_check_documents_and_bypass_ai():
    assert conversational_reply('Grazie!')=='Prego!'
    assert 'Vedo' in conversational_reply('Ho allegato contratto e CV',[{'filename':'contratto.pdf'},{'filename':'cv.pdf'}])
    assert 'Non riesco' in conversational_reply('Ho allegato contratto e CV',[{'filename':'cv.pdf'}])
    assert conversational_reply('Ok, analizza il contratto') is None
    assert conversational_reply('Ho allegato contratto e CV?') is None
    assert conversational_reply('Quanto guadagno?') is None
    service,who,scope,repo,ai,_=fixture();question=document('Ho allegato contratto e CV')
    repo.read.return_value={'intake':[question]};repo.documents=AsyncMock(return_value=[{'filename':'contratto.pdf'},{'filename':'CV.pdf'}])
    repo.claim_chat=AsyncMock(return_value={'intake':[question]});repo.finish_chat=AsyncMock()
    assert asyncio.run(service.respond(who,scope,request(),question['id'],str(uuid4())))=={'state':'completed'}
    assert len(repo.finish_chat.call_args.args[3]['text'])<160
    ai.respond.assert_not_called();repo.documents.assert_awaited_once()


def test_owner_preview_notice_also_skips_provider():
    from app.chat.development import DevelopmentAI
    service=DevelopmentAI(chat=Mock(),enrichment=Mock(),factory=Mock(),clock=Mock())
    service._authorize=AsyncMock();service._provider=Mock();recheck=AsyncMock()
    result=asyncio.run(service.answer_projection(SimpleNamespace(subject_id='owner'),'space',empty_projection('RH'),'? ',recheck))
    assert result['insufficient_context'] and result['simulated'] is False
    recheck.assert_awaited_once();service._provider.assert_not_called()
