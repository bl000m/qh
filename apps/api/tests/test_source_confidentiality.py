"""Focused offline regressions for document exclusion and deterministic dialogue."""
import asyncio
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.chat.conversation import conversational_reply
from app.chat.snapshot_answer import projection_request
from app.projections.document_scope import document_scope, empty_projection, is_empty_projection, restrict_snapshot
from app.projections.disclosure import Candidate, Selection
from app.projections.disclosure_service import DisclosureService
from tests.test_disclosure import policy
from tests.test_unified_recap import projected_documents
from tests.test_consolidation import fixture, document
from tests.test_chat_service import request


def test_projection_filters_before_general_recap_and_never_reintroduces_excluded_pdf():
    rows=projected_documents()
    documents=tuple({c['source_revision_id'] for r in rows for c in r.content['citations']})
    scope=str(uuid4());owner=str(uuid4())
    from app.projections.drafts import RevisionKey
    candidates=tuple(Candidate(key=RevisionKey(item_id=r.item_id,revision_id=r.revision_id),state=r.validation_state) for r in rows)
    repo=Mock(select=AsyncMock(return_value=Selection(context_id=scope,stamp='s',candidates=candidates,name='RH',document_sources=documents)),
        prepare=AsyncMock(side_effect=lambda p:p))
    drafts=Mock(_allow=AsyncMock(),create=AsyncMock(return_value=SimpleNamespace(id=str(uuid4()),version=1)),
        resolve=AsyncMock(return_value=SimpleNamespace(revisions=rows)))
    service=DisclosureService(drafts=drafts,repository=repo)
    frozen=deepcopy(rows)
    preview=asyncio.run(service.prepare(owner,scope,policy()))
    assert is_empty_projection(preview.payload) and not preview.report['anchors']
    assert 'recap' not in preview.payload and rows==frozen
    # A mixed source item is excluded unless every document source is selected.
    mixed=SimpleNamespace(revision_id='mixed',provenance=[],content={'citations':[{'source_revision_id':d} for d in documents]})
    retained,_=document_scope([mixed],replace(policy(),semantic_documents=documents[:1],original_documents=documents[:1]),documents)
    assert not retained
    assert document_scope([mixed],replace(policy(),semantic_documents=documents,original_documents=documents),documents)[0]==(mixed,)
    independent=SimpleNamespace(revision_id='dialogue',provenance=[],content={'text':'Independent'})
    assert document_scope([independent],policy(),documents)[0]==(independent,)


def test_retained_snapshot_is_restricted_without_mutation_and_relations_close():
    original=dict(format='qh.disclosure/1',name='RH',recap={'title':'Unsafe','text':'Private'},items=[
        {'reference':'R1','text':'CV'}, {'reference':'R2','text':'Contract'},
        {'reference':'R3','text':'Mixed','relation':{'source':'R1','target':'R2'}}])
    frozen=deepcopy(original)
    safe=restrict_snapshot(original,{'R1','R3'})
    assert safe['items']==[original['items'][0]] and 'recap' not in safe
    assert 'Private' not in str(safe)
    assert is_empty_projection(restrict_snapshot(original,set())) and original==frozen


def test_only_explicitly_approved_scoped_quotes_reach_the_model():
    import json
    from app.projections.disclosure_guard import OutboundDisclosureGuard
    from app.projections.guest_payload import recipient_payload
    from app.core.models import SourceRevisionRef
    base=projected_documents()[0]
    documents=(str(uuid4()),str(uuid4()))
    rows=[replace(base,revision_id=str(uuid4()),item_id=str(uuid4()),
        provenance=(SourceRevisionRef(source_id=str(uuid4()),revision_id=source),),
        content=dict(text=text,citations=[dict(source_revision_id=source,quote=quote)]*2))
        for source,text,quote in zip(documents,('Parcours déclaré.','Conditions proposées.'),
            ('Freelance - janvier 2022 a aout 2023.','Clause Neptune : prime de 900 euros sur justificatifs.'))]
    frozen=deepcopy(rows)
    for include_quotes in (False,True):
        access=policy(include_proposed=True,include_quotes=include_quotes,
            semantic_documents=documents[:1],original_documents=documents[:1])
        selected,_=document_scope(rows,access,documents)
        payload,_=OutboundDisclosureGuard().apply(selected,access)
        recipient_payload(payload,include_quotes=include_quotes)
        packet=json.loads(projection_request(payload,'Quels détails ?').messages[1].content)
        item=packet['snapshot']['items'][0]
        assert item.get('evidence_quotes',[])==(['Freelance - janvier 2022 a aout 2023.'] if include_quotes else [])
        assert 'Neptune' not in str(packet) and 'source_revision_id' not in str(packet)
        assert 'citations' not in item and 'sources' not in item and rows==frozen
        revoked=restrict_snapshot(payload,set())
        assert json.loads(projection_request(revoked,'?').messages[1].content)['snapshot']['items']==[]


def test_actual_model_request_contains_no_client_history_or_empty_notice_knowledge():
    import json
    history=[{'role':'user','content':'EXCLUDED-CONTRACT-CANARY'}, {'role':'assistant','content':'Revoked salary: 999999'}]
    packet=json.loads(projection_request({'format':'qh.disclosure/1','items':[{'reference':'R1','text':'Allowed CV'}]},'CV?',history).messages[1].content)
    assert 'history' not in packet and 'EXCLUDED' not in str(packet) and '999999' not in str(packet)
    assert json.loads(projection_request(empty_projection('RH'),'?').messages[1].content)['snapshot']['items']==[]


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
