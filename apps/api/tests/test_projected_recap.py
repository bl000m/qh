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


@pytest.mark.parametrize('restriction',['excluded','masked'])
def test_existing_synopsis_reused_only_when_exact_whole_disclosed_statement(restriction):
    rows=projected()
    summary=rows[0].content['extraction']['recap']
    summary.update(title='Laboratorio proposto',text='Laboratorio proposto: Giulia vorrebbe partecipare, ma non ha ancora deciso.')
    rows[0].content['text']=summary['text']
    rows[1].content['text']='Diagnostic médical privé.' if restriction=='excluded' else 'Contacter private@example.test.'
    frozen=deepcopy(rows)
    payload,report=OutboundDisclosureGuard().apply(rows,policy())
    assert payload['recap']==dict(title=summary['title'],text=summary['text'])
    assert report['recap_status']=='available' and report['exclusions' if restriction=='excluded' else 'masks']
    assert 'private@example.test' not in str(payload) and 'Diagnostic' not in str(payload)
    assert rows==frozen
    # A matching fragment is insufficient: dropping the rest could remove attribution.
    rows[0].content['text']+=' Questa è soltanto un’ipotesi discussa, non una decisione.'
    payload,report=OutboundDisclosureGuard().apply(rows,policy())
    assert 'recap' not in payload and report['recap_status']=='restricted'


def test_partial_basis_and_masked_summary_stay_closed_without_invented_fallback():
    rows=projected()
    rows[1].content['text']='Diagnostic médical privé.'
    payload,report=OutboundDisclosureGuard().apply(rows,policy())
    assert 'recap' not in payload and report['recap_status']=='restricted'
    assert payload['items'] and 'Diagnostic' not in str(payload)
    rows=projected()
    rows[0].content['extraction']['recap']['text']='Contacter private@example.test.'
    rows[0].content['text']='Contacter private@example.test.'
    payload,_=OutboundDisclosureGuard().apply(rows,policy())
    assert 'recap' not in payload and 'private@example.test' not in str(payload)


def test_exact_preview_is_approved_then_returned_by_guest_session_without_inference():
    import asyncio
    from dataclasses import replace
    from datetime import datetime, timezone
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, Mock

    from fastapi.testclient import TestClient

    from app.api.guest import COOKIE
    from app.projections.disclosure import ApprovedSnapshot, Candidate, Selection, TEXT_REVIEW
    from app.projections.disclosure_service import DisclosureService
    from app.projections.drafts import RevisionKey
    from app.projections.guest import GuestSnapshot
    from tests.test_projection_drafts import uid
    from tests.test_sharing_simplified import setup

    rows=projected();owner,scope=uid(),uid()
    keys=tuple(Candidate(key=RevisionKey(item_id=r.item_id,revision_id=r.revision_id),state=r.validation_state,endpoints=()) for r in rows)
    repository=Mock(select=AsyncMock(return_value=Selection(context_id=scope,stamp='stable',candidates=keys,name='Atelier')),
        prepare=AsyncMock(side_effect=lambda value:value),preview=AsyncMock(),approve=AsyncMock())
    drafts=Mock(_allow=AsyncMock(),create=AsyncMock(return_value=SimpleNamespace(id=uid(),version=1)),
        resolve=AsyncMock(return_value=SimpleNamespace(revisions=rows)))
    service=DisclosureService(drafts=drafts,repository=repository)
    preview=asyncio.run(service.prepare(owner,scope,policy()))
    repository.preview.return_value=preview
    repository.approve.side_effect=lambda value,exceptions:ApprovedSnapshot(id=uid(),context_id=scope,owner_id=owner,
        preview_id=value.id,fingerprint=value.fingerprint,payload_json=value.payload_json,policy=value.policy,
        approved_at=datetime.now(timezone.utc),exceptions=exceptions)
    snapshot=asyncio.run(service.approve(owner,scope,preview.id,preview.fingerprint,exceptions=(TEXT_REVIEW,)))
    assert snapshot.payload==preview.payload
    app,_,_,_,_,provider,_,_=setup()
    guest=app.state.services.guest
    grant=replace(guest.repository.authenticate.return_value,context_id=scope,snapshot_id=snapshot.id,rights=('READ',))
    guest.repository.authenticate.return_value=grant
    app.state.services.policy._guest_for.return_value=grant
    guest.repository.payload.return_value=GuestSnapshot(context_id=scope,snapshot_id=snapshot.id,payload_json=snapshot.payload_json,include_quotes=False)
    with TestClient(app,base_url='https://qh.example.test') as client:
        client.cookies.set(COOKIE,'synthetic-verified-cookie')
        response=client.get('/guest/session')
        assert response.status_code==200
        assert response.json()['recap']==preview.payload['recap']
    provider.generate.assert_not_awaited()
