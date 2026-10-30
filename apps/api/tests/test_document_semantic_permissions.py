"""Offline sharing service/Guard/snapshot checks; no SQL or paid provider."""
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
from tests.test_modular_recap import generate_documents, projected
from tests.test_projection_drafts import run


def fixture():
    bound, _, originals, _ = generate_documents()
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


@pytest.mark.parametrize('selected,expected',[((),[3]),((0,),[0,3]),((0,1,2),[0,1,2,3,4])])
def test_document_scope_requires_all_sources_then_applies_guard_and_preserves_canonical(selected,expected):
    service,rows,documents,scope=fixture();frozen=deepcopy(rows)
    access=policy(semantic_documents=tuple(documents[i] for i in selected),original_documents=tuple(documents[i] for i in selected))
    preview=run(service.prepare(str(uuid4()),scope,access))
    assert [i['text'] for i in preview.payload['items']]==[rows[i].content['text'] for i in expected]
    assert preview.payload['semantic_document_count']==len(selected)
    assert 'document_recaps' not in preview.payload and rows==frozen
    assert recipient_payload(preview.payload)==preview.payload
    assert any(e['reason']=='recognised_high_risk' for e in preview.report['exclusions'])==bool(selected)
    # This exact minimized packet is the only knowledge available to snapshot chat.
    packet=question_payload(preview.payload)
    if len(selected)<3:
        assert rows[1].content['text'] not in json.dumps(packet)
        assert rows[2].content['text'] not in json.dumps(packet)
        assert 'Mixed CV and contract.' not in json.dumps(packet)


@pytest.mark.parametrize('originals', [False, True])
def test_empty_notice_approval_does_not_release_document_introduction_or_call_ai(originals):
    service,rows,documents,scope=fixture()
    service.drafts.resolve.return_value=SimpleNamespace(revisions=tuple(rows[:3]))
    owner=str(uuid4());access=policy(original_documents=(documents[0],) if originals else ())
    preview=run(service.prepare(owner,scope,access))
    assert is_empty_projection(preview.payload) and 'recap' not in preview.payload
    assert not preview.report['anchors']
    assert preview.payload['items'][0]['sources']==[]
    service.repository.preview=AsyncMock(return_value=preview)
    snapshot=ApprovedSnapshot(id=str(uuid4()),context_id=scope,owner_id=owner,preview_id=preview.id,
        fingerprint=preview.fingerprint,payload_json=preview.payload_json,policy=access,
        approved_at=service.clock(),exceptions=tuple(preview.report['risks']))
    service.repository.approve=AsyncMock(return_value=snapshot)
    assert run(service.approve(owner,scope,preview.id,preview.fingerprint,exceptions=snapshot.exceptions))==snapshot
    assert recipient_payload(snapshot.payload)==snapshot.payload
    from adapters.llm.guest_offline import OfflineSnapshotProvider
    provider=OfflineSnapshotProvider()
    provider.generate=AsyncMock(wraps=provider.generate)
    chat=GuestSnapshotChat(guest=Mock(),provider=provider)
    answer=run(chat.answer_payload(owner,scope,'offline',snapshot.payload,'Que prévoit le contrat ?',
        AsyncMock(return_value=snapshot.payload)))
    assert answer['insufficient_context'] and rows[1].content['text'] not in answer['answer']
    assert question_payload(snapshot.payload)['items']==[]
    provider.generate.assert_not_awaited()
    semantic=run(service.prepare(owner,scope,policy(semantic_documents=(documents[0],))))
    assert is_empty_projection(semantic.payload) and semantic.policy.original_documents==()
    assert semantic.policy.semantic_documents==(documents[0],)


@pytest.mark.parametrize('failure', ['masked-support','sensitive-introduction','excluded-support'])
def test_introduction_is_not_disclosable_merely_because_it_is_general(failure):
    service,rows,documents,scope=fixture()
    if failure=='masked-support':
        rows[0].content['text']+=' private@example.test'
    elif failure=='sensitive-introduction':
        for row in rows:
            for component in row.content.get('extraction',{}).get('recap_components',[]):
                if component['kind']=='general':component['text']='Diagnostic médical privé.'
    else:
        service.drafts.resolve.return_value=SimpleNamespace(revisions=tuple(rows[1:]))
    for selected in ((),documents):
        preview=run(service.prepare(str(uuid4()),scope,policy(semantic_documents=selected,original_documents=selected)))
        assert 'recap' not in preview.payload


def test_exact_policy_roundtrip_foreign_documents_and_later_uploads():
    service,rows,documents,scope=fixture();access=policy(semantic_documents=documents,original_documents=documents)
    assert AccessPolicy.from_wire(access.wire())==access
    old=policy().wire();assert 'semantic_documents' not in old
    assert AccessPolicy.from_wire(old).wire()==old
    with pytest.raises(ProjectionNotFound):
        run(service.prepare(str(uuid4()),scope,policy(semantic_documents=(str(uuid4()),))))
    service.drafts.create.assert_not_awaited()
    first=run(service.prepare(str(uuid4()),scope,access));frozen=deepcopy(first.payload)
    later=str(uuid4())
    service.repository.select.return_value=replace(service.repository.select.return_value,document_sources=documents+(later,))
    new=replace(rows[0],revision_id=str(uuid4()),item_id=str(uuid4()),content=dict(text='Later private PDF.'),
        provenance=(SourceRevisionRef(source_id=str(uuid4()),revision_id=later),))
    service.drafts.resolve.return_value=SimpleNamespace(revisions=tuple(rows)+(new,))
    subsequent=run(service.prepare(str(uuid4()),scope,access))
    assert 'Later private PDF.' not in json.dumps(subsequent.payload)
    assert first.payload==frozen and first.policy.semantic_documents==documents


def test_single_safe_document_synopsis_survives_scope_without_random_excerpts():
    service,rows,documents,scope=fixture()
    access=policy(semantic_documents=(documents[0],),original_documents=(documents[0],))
    frozen=deepcopy(rows)
    preview=run(service.prepare(str(uuid4()),scope,access))
    component=next(c for row in rows for c in row.content.get('extraction',{}).get('recap_components',[])
        if c['kind']=='document' and c['source_revision_id']==documents[0])
    assert preview.payload['recap']=={key:component[key] for key in ('title','text')}
    assert rows==frozen and 'document_recaps' not in preview.payload
    assert rows[1].content['text'] not in json.dumps(question_payload(preview.payload))
