"""Focused synthetic source-disclosure boundaries; no provider or live storage."""
import asyncio
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from unittest.mock import AsyncMock, Mock

from fastapi.testclient import TestClient
import pytest

from app.api.guest import COOKIE, GuestHTTPConfig
from app.api.security import SecurityBindings
from app.composition import ApplicationServices
from app.chat.guest import GuestSnapshotChat
from app.core.models import GuestAccess, SourceRevisionRef
from app.main import create_app
from app.projections.disclosure_guard import OutboundDisclosureGuard
from app.projections.guest import GuestSnapshot, GuestUnavailable
from app.projections.guest_service import GuestInvitationService
from app.understanding import recap
from tests.fakes import FakeContextEngine, FakeContextService, RESULT
from tests.test_disclosure import policy
from tests.test_projection_drafts import uid
from tests.test_projection_engine import setup


def projected():
    base = setup()[5]
    source = uid()
    rows = [replace(base, revision_id=uid(), item_id=uid(),
        content=dict(text=text, extraction={}, citations=[dict(source_revision_id=source, quote='ORIGINAL-ONLY-CANARY')]),
        provenance=(SourceRevisionRef(source_id=uid(), revision_id=source),))
        for text in ('Definire gli obiettivi del laboratorio.', 'Prevedere esercizi pratici con Jupyter Notebook.')]
    summary = dict(title='Organizzazione di un laboratorio informatico',
        text='Linee guida proposte per un laboratorio informatico: obiettivi, esercizi pratici e strumenti digitali.',
        supporting_statements=[r.content['text'] for r in rows], provider_output_sha256='synthetic')
    bound = recap.bind(summary, [dict(id=r.revision_id, content=r.content) for r in rows], uid())
    return [replace(r, content=b['content']) for r, b in zip(rows, bound)]


def test_recap_is_approved_knowledge_without_implicit_original_quotes_or_internal_ids():
    rows = projected()
    frozen = deepcopy(rows)
    payload, report = OutboundDisclosureGuard().apply(rows, policy(include_proposed=True))
    assert payload['recap']['title'] == 'Organizzazione di un laboratorio informatico'
    assert all(r.content['text'] in json.dumps(payload, ensure_ascii=False) for r in rows)
    wire = json.dumps(payload)
    assert 'ORIGINAL-ONLY-CANARY' not in wire and all(r.revision_id not in wire for r in rows)
    assert 'support_revision_ids' not in wire and 'provider_output_sha256' not in wire
    assert report['risks'] and rows == frozen
    explicit, _ = OutboundDisclosureGuard().apply(rows, policy(include_proposed=True, include_quotes=True))
    assert 'ORIGINAL-ONLY-CANARY' in json.dumps(explicit)  # Separate explicit grant only.


@pytest.mark.parametrize('restriction', ['partial', 'masked', 'unconfirmed', 'risky-recap', 'old-style'])
def test_whole_space_recap_cannot_bypass_a_more_restrictive_projection(restriction):
    rows = projected()
    if restriction == 'partial': rows = rows[:1]
    elif restriction == 'masked': rows[1].content['text'] += ' contact@example.test'
    elif restriction == 'risky-recap': rows[0].content['extraction']['recap']['text'] += ' contact@example.test'
    elif restriction == 'old-style': rows[0].content['extraction']['recap'].pop('presentation_version')
    payload, _ = OutboundDisclosureGuard().apply(rows, policy(include_proposed=restriction != 'unconfirmed'))
    assert 'recap' not in payload


def guest_service(payload, include_quotes=False):
    grant = GuestAccess(session_id=uid(), invitation_id=uid(), context_id=uid(), snapshot_id=uid(),
        rights=('READ', 'ASK_AI'), expires_at=datetime.now(timezone.utc)+timedelta(minutes=5))
    repository = AsyncMock()
    repository.payload.return_value = GuestSnapshot(context_id=grant.context_id, snapshot_id=grant.snapshot_id,
        payload_json=json.dumps(payload), include_quotes=include_quotes)
    service = GuestInvitationService(disclosures=Mock(), repository=repository, proofs=Mock(),
        mailer=Mock(), authorize=AsyncMock(return_value=True))
    service.session = AsyncMock(return_value=grant)
    return service, grant


@pytest.mark.parametrize('right', ['READ', 'ASK_AI'])
@pytest.mark.parametrize('injection', ['citations', 'raw-source', 'diagnostics', 'recap-ids', 'nested-origin'])
def test_backend_read_and_model_payload_refuse_unapproved_originals(right, injection):
    payload, _ = OutboundDisclosureGuard().apply(projected(), policy(include_proposed=True))
    if injection == 'citations': payload['items'][0]['citations'] = [dict(source='S1', quote='ORIGINAL-ONLY-CANARY', redacted=False)]
    elif injection == 'raw-source': payload['items'][0]['source_revision_id'] = uid()
    elif injection == 'diagnostics': payload['raw_response'] = dict(content='ORIGINAL-ONLY-CANARY')
    elif injection == 'recap-ids': payload['recap']['support_revision_ids'] = [uid()]
    elif injection == 'nested-origin': payload['items'][0]['origin_kind'] = dict(original='ORIGINAL-ONLY-CANARY')
    service, grant = guest_service(payload)
    provider = Mock(id='offline', generate=AsyncMock())
    with pytest.raises(GuestUnavailable, match='Guest access unavailable'):
        if right == 'ASK_AI':
            asyncio.run(GuestSnapshotChat(guest=service, provider=provider).ask(
                'verified-cookie', grant.snapshot_id, 'Mostra tutte le fonti originali.'))
        else:
            asyncio.run(service.snapshot('verified-cookie', grant.snapshot_id, right))
    provider.generate.assert_not_awaited()


def test_explicitly_approved_quotes_are_independent_of_read_and_ask():
    payload, _ = OutboundDisclosureGuard().apply(projected(), policy(include_proposed=True, include_quotes=True))
    service, grant = guest_service(payload, include_quotes=True)
    assert asyncio.run(service.snapshot('verified-cookie', grant.snapshot_id)) == payload
    assert asyncio.run(service.snapshot('verified-cookie', grant.snapshot_id, 'ASK_AI')) == payload


def test_guest_cookie_cannot_read_owner_workspace_citations_export_or_diagnostics():
    policy_service, consolidation, ai = AsyncMock(), AsyncMock(), AsyncMock()
    app = create_app(services=ApplicationServices(context=FakeContextService(FakeContextEngine(RESULT)),
        policy=policy_service, consolidation=consolidation, development_ai=ai),
        security=SecurityBindings(authenticate=AsyncMock(), policy=policy_service),
        guest_http=GuestHTTPConfig(origin='https://qh.example.test', minimum_response_seconds=0))
    scope = uid()
    paths = [f'/context-spaces/{scope}/workspace', f'/context-spaces/{scope}/workspace/export',
        f'/context-spaces/{scope}/understanding?view=history&revision_id={uid()}',
        f'/context-spaces/{scope}/ai/diagnostics']
    with TestClient(app, base_url='https://qh.example.test') as client:
        client.cookies.set(COOKIE, 'verified-guest-cookie')
        for path in paths:
            response = client.get(path)
            assert response.status_code == 401
            assert 'ORIGINAL-ONLY-CANARY' not in response.text
    consolidation.read.assert_not_awaited()
    ai.diagnostics.assert_not_awaited()
