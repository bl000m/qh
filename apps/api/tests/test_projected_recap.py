"""Offline recap disclosure: reuse only existing, completely verifiable semantics."""
from copy import deepcopy

import pytest

from app.projections.disclosure_guard import OutboundDisclosureGuard
from tests.test_context_sovereignty import projected
from tests.test_disclosure import policy


def test_complete_recap_and_missing_recap_have_distinct_owner_status():
    rows=projected()
    payload,report=OutboundDisclosureGuard().apply(rows,policy())
    assert payload['recap']=={k:rows[0].content['extraction']['recap'][k] for k in ('title','text')}
    assert report['recap_status']=='available'
    rows[0].content['extraction'].pop('recap')
    payload,report=OutboundDisclosureGuard().apply(rows,policy())
    assert 'recap' not in payload and report['recap_status']=='unavailable'


def test_excluded_support_stays_excluded_and_masked_summary_stays_closed():
    rows=projected()
    rows[1].content['text']='Diagnostic médical privé.'
    payload,report=OutboundDisclosureGuard().apply(rows,policy())
    assert report['recap_status']=='available'
    assert payload['items'] and 'Diagnostic' not in str(payload) and rows[1].revision_id not in str(payload)
    rows=projected()
    rows[0].content['extraction']['recap']['text']='Contacter private@example.test.'
    rows[0].content['text']='Contacter private@example.test.'
    payload,_=OutboundDisclosureGuard().apply(rows,policy())
    assert 'recap' not in payload and 'private@example.test' not in str(payload)


@pytest.mark.parametrize('originals',[0,1,2])
def test_owner_preview_approval_and_guest_share_the_same_canonical_recap_and_knowledge(originals):
    """Offline end-to-end: memorized CV-like PDFs → owner read → preview → approval → guest HTTP."""
    import asyncio
    import json
    from dataclasses import replace
    from datetime import datetime, timezone
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, Mock

    from fastapi.testclient import TestClient

    from app.api.guest import COOKIE
    from app.chat.guest import question_payload
    from app.projections.disclosure import ApprovedSnapshot, Candidate, Selection, TEXT_REVIEW
    from app.projections.disclosure_service import DisclosureService
    from app.projections.drafts import RevisionKey
    from app.projections.guest import GuestSnapshot
    from app.understanding import recap
    from tests.test_projection_drafts import uid
    from tests.test_sharing_simplified import setup
    from tests.test_unified_recap import SUMMARY, generate_documents, projected_documents

    generated=generate_documents()
    rows=projected_documents(generated)
    owner_view=recap.from_version(generated.rows,dict(id=generated.version,revision_ids=[r['id'] for r in generated.rows]))
    documents=tuple(s['id'] for s in generated.originals)
    owner,scope=uid(),uid()
    keys=tuple(Candidate(key=RevisionKey(item_id=r.item_id,revision_id=r.revision_id),state=r.validation_state,endpoints=()) for r in rows)
    repository=Mock(select=AsyncMock(return_value=Selection(context_id=scope,stamp='stable',candidates=keys,name='RH',document_sources=documents)),
        prepare=AsyncMock(side_effect=lambda value:value),preview=AsyncMock(),approve=AsyncMock())
    drafts=Mock(_allow=AsyncMock(),create=AsyncMock(return_value=SimpleNamespace(id=uid(),version=1)),
        resolve=AsyncMock(return_value=SimpleNamespace(revisions=rows)))
    service=DisclosureService(drafts=drafts,repository=repository)
    preview=asyncio.run(service.prepare(owner,scope,policy(knowledge_scope='context',original_documents=documents[:originals])))
    assert preview.payload['recap']=={k:owner_view[k] for k in ('title','text')}==SUMMARY
    assert [i['text'] for i in preview.payload['items']]==[r.content['text'] for r in rows]
    assert 'document_recaps' not in preview.payload and preview.report['recap_status']=='available'
    repository.preview.return_value=preview
    repository.approve.side_effect=lambda value,exceptions:ApprovedSnapshot(id=uid(),context_id=scope,owner_id=owner,
        preview_id=value.id,fingerprint=value.fingerprint,payload_json=value.payload_json,policy=value.policy,
        approved_at=datetime.now(timezone.utc),exceptions=exceptions)
    snapshot=asyncio.run(service.approve(owner,scope,preview.id,preview.fingerprint,exceptions=(TEXT_REVIEW,)))
    assert snapshot.payload==preview.payload and snapshot.policy.original_documents==documents[:originals]
    app,_,_,_,_,provider,_,_=setup()
    guest=app.state.services.guest
    grant=replace(guest.repository.authenticate.return_value,context_id=scope,snapshot_id=snapshot.id,rights=('READ','ASK_AI'))
    guest.repository.authenticate.return_value=grant
    app.state.services.policy._guest_for.return_value=grant
    guest.repository.payload.return_value=GuestSnapshot(context_id=scope,snapshot_id=snapshot.id,payload_json=snapshot.payload_json,include_quotes=False)
    with TestClient(app,base_url='https://qh.example.test') as client:
        client.cookies.set(COOKIE,'synthetic-verified-cookie')
        response=client.get('/guest/session')
        assert response.status_code==200 and response.json()['recap']==SUMMARY
    # Interrogable knowledge is identical for 0, 1 or 2 downloadable PDFs and excludes original quotes.
    packet=json.dumps(question_payload(snapshot.payload),ensure_ascii=False)
    assert all(r.content['text'] in packet for r in rows) and '06 12 34 56 78' not in packet and 'secret' not in packet
    provider.generate.assert_not_awaited()
