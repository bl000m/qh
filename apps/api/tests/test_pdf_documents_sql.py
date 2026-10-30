"""One disposable SQL/Neo4j path: atomic original, UUM provenance, guest denial/revocation."""
import asyncio
from dataclasses import replace
from datetime import timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from alembic import command
import psycopg
import pytest
from fastapi.testclient import TestClient

from adapters.pdf import extract_pdf
from adapters.guest_security import SecureGuestProofs
from adapters.postgres.guest import PostgresGuestRepository
from adapters.postgres.security import PostgresSecurityReader
from app.api.guest import GuestHTTPConfig, COOKIE
from app.api.security import SecurityBindings
from app.composition import ApplicationServices
from app.main import create_app
from app.policy.owner import OwnerPolicyService
from app.policy.services import guest_authorizer
from app.projections.guest import GuestDenied
from app.projections.guest_service import GuestInvitationService
from app.understanding.documents import DocumentInvalid
from app.understanding.enrichment import EnrichmentConflict
from tests.test_pdf_documents import pdf_bytes
from tests.test_consolidation_pipeline import prepare as consolidation
from tests.test_disclosure_pipeline import disclosure as disclosure, prepare, approve
from tests.test_projection_drafts_sql import drafts as drafts
from tests.test_generic_semantics import generic as generic
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only
from tests.test_canonical_graph_pipeline import drain

pytestmark=pytest.mark.parametrize('generic',['0005_retire_legacy_category'],indirect=True)


def run(value):return asyncio.run(value)


def test_original_atomic_source_provenance_owner_and_specific_guest_access(disclosure,empty_database):
    p=disclosure;service,who,repository,provider=consolidation(p,empty_database)
    command.upgrade(empty_database,'0011_source_documents')
    service.pdf_parser=extract_pdf
    operation=str(uuid4());data=pdf_bytes();scope=p['scope'];owner=who.subject_id
    saved=run(service.import_pdf(owner,scope,operation,'source.pdf',data))
    original=saved['intake'][0]['source_revision_id']
    assert saved['pending_count']==1
    assert bytes(run(repository(owner).document(scope,original))['original'])==data
    provider.generate.assert_not_awaited()
    assert run(service.import_pdf(owner,scope,operation,'source.pdf',data))==saved
    with pytest.raises(EnrichmentConflict):run(service.import_pdf(owner,scope,operation,'source.pdf',pdf_bytes(('Changed.',))))
    with pytest.raises(EnrichmentConflict):run(service.import_pdf(owner,scope,operation,'renamed.pdf',data))
    with pytest.raises(DocumentInvalid):run(service.import_pdf(owner,scope,str(uuid4()),'bad.pdf',b'%PDF-broken'))
    with patch.object(type(repository(owner)),'_append_on',side_effect=ValueError('injected rollback')):
        with pytest.raises(ValueError):run(service.import_pdf(owner,scope,str(uuid4()),'rollback.pdf',data))
    with p['repo'].connect() as c:
        assert c.execute('SELECT count(*) n FROM source_documents').fetchone()['n']==1
        with pytest.raises(psycopg.errors.CheckViolation),c.transaction():
            c.execute('UPDATE source_documents SET filename=\'changed.pdf\'')
    drain(p['worker'])
    memorized=run(service.consolidate(who,scope));drain(p['worker'])
    state=run(service.read(owner,scope))
    row=next(r for r in state['understanding'] if any(c['source_revision_id']==original for c in r['content'].get('citations',[])))
    citation=next(c for c in row['content']['citations'] if c['source_revision_id']==original)
    source=run(repository(owner).original(scope,original))
    assert source['content'][citation['start']:citation['end']]==citation['quote']=='Le responsable est Alice.'
    assert citation['turn_id'].endswith(':page:1') and row['validation_state']=='proposed'
    assert memorized['current']['revision_ids']
    async def authenticate(token):return owner if token=='owner' else str(uuid4())
    bindings=SecurityBindings(authenticate=authenticate,policy=service.policy)
    app=create_app(services=ApplicationServices(context=service.context,policy=service.policy,consolidation=service),security=bindings)
    with TestClient(app) as client:
        path=f'/context-spaces/{scope}/workspace/documents/{original}'
        assert client.get(path,headers={'Authorization':'Bearer owner'}).content==data
        assert client.get(path,headers={'Authorization':'Bearer other'}).status_code==404
        assert client.get(path.replace(scope,p['sibling']),headers={'Authorization':'Bearer owner'}).status_code==404
    # Fresh real SQL sessions and central PolicyService; OTP delivery is an offline double.
    now=[p['disclosure'].clock()]
    guest_repo=PostgresGuestRepository(url=p['repo'].url,clock=lambda:now[0])
    policy=OwnerPolicyService(owner_for=PostgresSecurityReader(url=p['repo'].url).owner_for,
        guest_for=guest_repo.guest_for,clock=lambda:now[0])
    mail=type('Mail',(),{})();mail.send=AsyncMock()
    guest=GuestInvitationService(disclosures=p['disclosure'],repository=guest_repo,
        proofs=SecureGuestProofs(b'pdf-test-only-key-32-characters!!!'),mailer=mail,
        authorize=guest_authorizer(policy),clock=lambda:now[0])
    def session(originals):
        snapshot=approve(p,prepare(p,include_proposed=True,original_documents=originals))
        invite=run(guest.create(owner,scope,snapshot.id))
        receipt=run(guest.request_code(invite.token,snapshot.policy.recipient_email,str(uuid4())))
        code=mail.send.call_args.args[1]
        return run(guest.verify(invite.token,receipt['challenge_id'],code,str(uuid4()))),invite,snapshot
    denied,_,_=session(())
    assert run(guest.documents(denied.token))==[]
    with pytest.raises(GuestDenied):run(guest.documents(denied.token,original))
    allowed,invite,snapshot=session((original,))
    listed=run(guest.documents(allowed.token))
    assert len(listed)==1 and listed[0]['source_revision_id']==original and listed[0]['filename']=='source.pdf'
    assert listed[0]['display_name']=='source.pdf' and listed[0]['size_bytes']==len(data)
    assert bytes(run(guest.documents(allowed.token,original))['original'])==data
    assert original not in str(snapshot.payload) and 'source.pdf' not in str(snapshot.payload)
    with pytest.raises(GuestDenied):run(guest.documents(allowed.token,str(uuid4())))
    services=ApplicationServices(context=service.context,policy=policy,consolidation=service,guest=guest)
    app=create_app(services=services,security=SecurityBindings(authenticate=authenticate,policy=policy),guest_http=GuestHTTPConfig(origin='https://qh.example.test',minimum_response_seconds=0))
    with TestClient(app,base_url='https://qh.example.test') as client:
        assert client.get('/guest/documents/'+original).status_code==401
        client.cookies.set(COOKIE,allowed.token)
        response=client.get('/guest/documents/'+original)
        assert response.status_code==200 and response.content==data
        assert response.headers['cache-control']=='private, no-store'
        run(guest.revoke(owner,scope,invite.id))
        assert client.get('/guest/documents/'+original).status_code==401
    expiring,_,_=session((original,));now[0]+=timedelta(hours=2)
    with pytest.raises(GuestDenied):run(guest.documents(expiring.token,original))
