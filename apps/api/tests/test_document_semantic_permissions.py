"""Whole-understanding sharing, independent of original PDF grants; no paid provider."""
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.chat.guest import GuestSnapshotChat, question_payload
from app.core.models import SourceRevisionRef
from app.projections.disclosure import AccessPolicy, ApprovedSnapshot, Candidate, Selection
from app.projections.disclosure_service import DisclosureService
from app.projections.document_scope import is_empty_projection
from app.projections.drafts import ProjectionNotFound, RevisionKey
from app.projections.guest_payload import recipient_payload
from tests.test_disclosure import policy
from tests.test_context_sovereignty import projected
from tests.test_projection_drafts import run
from tests.test_unified_recap import generate_documents

TEXTS=['Giulia Rossi décrit son expérience en développement dans son CV.',
    'Le contrat prévoit une activité de développement.',
    'Giulia souhaiterait devenir architecte, sans décision contractuelle.']


def general_recap(rows):
    return next(r.content['extraction']['recap'] for r in rows if r.content.get('extraction',{}).get('recap'))


def fixture():
    generated = generate_documents(pages=TEXTS, items=[(text,[text]) for text in TEXTS])
    bound, originals = generated.rows, generated.originals
    documents = tuple(s['id'] for s in originals)
    base = projected()[0]
    rows = [replace(base,revision_id=r['id'],item_id=r['item_id'],content=r['content'],
        provenance=tuple(SourceRevisionRef(source_id=str(uuid4()),revision_id=s) for s in r['provenance'])) for r in bound]
    rows.append(replace(base,revision_id=str(uuid4()),item_id=str(uuid4()),content=dict(text='Dialogue independent.'),provenance=()))
    rows.append(replace(base,revision_id=str(uuid4()),item_id=str(uuid4()),content=dict(text='Mixed CV and contract.'),
        provenance=tuple(SourceRevisionRef(source_id=str(uuid4()),revision_id=s) for s in documents[:2])))
    rows.append(replace(rows[0],revision_id=str(uuid4()),item_id=str(uuid4()),content=dict(text='Diagnostic médical privé.')))
    selection = Selection(context_id=base.context_id,stamp='offline-current',name='RH synthetic',document_sources=documents,
        candidates=tuple(Candidate(key=RevisionKey(item_id=r.item_id,revision_id=r.revision_id),state='proposed') for r in rows))
    drafts = Mock(_allow=AsyncMock(),create=AsyncMock(return_value=SimpleNamespace(id=str(uuid4()),version=1)),
        resolve=AsyncMock(return_value=SimpleNamespace(revisions=tuple(rows))))
    repository = Mock(select=AsyncMock(return_value=selection),prepare=AsyncMock(side_effect=lambda p:p))
    service = DisclosureService(drafts=drafts,repository=repository)
    return service, rows, documents, base.context_id


def context_preview(service,scope,originals=()):
    return run(service.prepare(str(uuid4()),scope,policy(knowledge_scope='context',original_documents=originals)))


def test_whole_understanding_is_shared_verbatim_independently_of_original_downloads():
    service,rows,documents,scope=fixture();frozen=deepcopy(rows)
    previews=[context_preview(service,scope,originals) for originals in ((),documents[1:2],documents)]
    assert all(p.payload==previews[0].payload for p in previews)
    # Every eligible canonical item, including sensitive wording, mixed and dialogue items.
    assert [i['text'] for i in previews[0].payload['items']]==[r.content['text'] for r in rows]
    assert not previews[0].report['exclusions'] and previews[0].report['masks']==[]
    assert previews[0].payload['recap']=={k:general_recap(rows)[k] for k in ('title','text')}
    assert previews[0].payload['semantic_document_count']==len(documents) and rows==frozen
    assert all('citations' not in item for item in previews[0].payload['items'])
    assert recipient_payload(previews[0].payload)==previews[0].payload
    assert [i['text'] for i in question_payload(previews[0].payload)['items']]==[r.content['text'] for r in rows]


def test_personal_data_dates_and_numbers_are_never_masked():
    service,rows,documents,scope=fixture()
    detail=' Né le 02/03/1981, tél. +33 6 12 34 56 78, private@example.test, Identifiant : 123456789, 2019/2021.'
    rows[0].content['text']+=detail
    preview=context_preview(service,scope)
    assert rows[0].content['text'] in [i['text'] for i in preview.payload['items']]
    assert '[MASQUÉ]' not in json.dumps(preview.payload,ensure_ascii=False) and preview.payload['recap']


@pytest.mark.parametrize('case',['sensitive-recap','missing-basis'])
def test_shared_recap_is_the_persisted_one_or_explicitly_unavailable(case):
    service,rows,documents,scope=fixture()
    if case=='sensitive-recap':
        general_recap(rows)['text']='Diagnostic médical privé.'
    else:
        service.drafts.resolve.return_value=SimpleNamespace(revisions=tuple(rows[1:]))
    preview=context_preview(service,scope,documents)
    if case=='sensitive-recap':
        assert preview.payload['recap']=={k:general_recap(rows)[k] for k in ('title','text')}
    else:
        # No valid canonical recap: say so, without blocking the detailed understanding.
        assert 'recap' not in preview.payload and preview.report['recap_status']=='unavailable'
        assert len(preview.payload['items'])==len(rows)-1


def test_legacy_policies_roundtrip_but_cannot_prepare_new_previews():
    service,rows,documents,scope=fixture();access=policy(semantic_documents=documents,original_documents=documents)
    assert AccessPolicy.from_wire(access.wire())==access
    old=policy().wire();assert 'semantic_documents' not in old
    assert AccessPolicy.from_wire(old).wire()==old
    for legacy in (access,policy(),policy(knowledge_scope='context',include_quotes=True)):
        with pytest.raises(ValueError):run(service.prepare(str(uuid4()),scope,legacy))
    with pytest.raises(ValueError):policy(knowledge_scope='context',semantic_documents=documents)
    with pytest.raises(ProjectionNotFound):
        run(service.prepare(str(uuid4()),scope,policy(knowledge_scope='context',original_documents=(str(uuid4()),))))
    service.drafts.create.assert_not_awaited()


def test_preview_is_frozen_while_later_uploads_enter_only_new_previews():
    service,rows,documents,scope=fixture()
    first=context_preview(service,scope);frozen=deepcopy(first.payload)
    later=str(uuid4())
    service.repository.select.return_value=replace(service.repository.select.return_value,document_sources=documents+(later,))
    new=replace(rows[0],revision_id=str(uuid4()),item_id=str(uuid4()),content=dict(text='Later PDF.'),
        provenance=(SourceRevisionRef(source_id=str(uuid4()),revision_id=later),))
    service.drafts.resolve.return_value=SimpleNamespace(revisions=tuple(rows)+(new,))
    subsequent=context_preview(service,scope)
    assert 'Later PDF.' in json.dumps(subsequent.payload) and first.payload==frozen


def test_empty_understanding_approval_never_calls_ai():
    service,rows,documents,scope=fixture()
    service.repository.select.return_value=replace(service.repository.select.return_value,candidates=())
    owner=str(uuid4());preview=run(service.prepare(owner,scope,policy(knowledge_scope='context')))
    assert is_empty_projection(preview.payload) and not preview.report['anchors']
    from adapters.llm.guest_offline import OfflineSnapshotProvider
    provider=OfflineSnapshotProvider();provider.generate=AsyncMock(wraps=provider.generate)
    chat=GuestSnapshotChat(guest=Mock(),provider=provider)
    answer=run(chat.answer_payload(owner,scope,'offline',preview.payload,'Que prévoit le contrat ?',AsyncMock(return_value=preview.payload)))
    assert answer['insufficient_context'] and question_payload(preview.payload)['items']==[]
    provider.generate.assert_not_awaited()
