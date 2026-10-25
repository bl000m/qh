"""Real private SMTP mailbox + isolated SQL/native/OIDC and secure cookie flow."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import logging
import os
import re
from unittest.mock import AsyncMock

from alembic import command
from fastapi.testclient import TestClient
import httpx
import psycopg
import pytest

from adapters.guest_security import SecureGuestProofs
from adapters.postgres.guest import PostgresGuestRepository
from adapters.postgres.security import PostgresSecurityReader
from adapters.sandbox_mail import SandboxSMTPMailer
from app.api.guest import COOKIE, GuestHTTPConfig
from app.api.security import SecurityBindings
from app.composition import ApplicationServices
from app.main import create_app
from app.policy.owner import OwnerPolicyService
from app.policy.services import guest_authorizer, projection_authorizer
from app.projections.guest import GuestDenied, GuestRateLimited, GuestSnapshot, GuestUnavailable, MailUnavailable
from app.projections.drafts import ProjectionNotFound
from app.projections.guest_service import GuestInvitationService
from tests.fakes import FakeContextEngine, FakeContextService, RESULT
from tests.test_disclosure_pipeline import disclosure as disclosure, prepare, approve
from tests.test_projection_drafts_sql import drafts as drafts
from tests.test_generic_semantics import generic as generic, revision
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only
from tests.test_oidc_security import build_auth, token
from tests.test_projection_drafts import run, uid
from tests.test_canonical_graph_pipeline import drain

# One current disposable baseline; no duplicate historical 0004/0005 campaigns.
pytestmark=pytest.mark.parametrize('generic',['0005_retire_legacy_category'],indirect=True)
ORIGIN='https://qh.example.test'


@pytest.fixture
def guest(disclosure,empty_database):
    if os.environ.get('QH20_TEST')!='1':pytest.skip('Explicit private SMTP sandbox required')
    assert os.environ.get('QH20_MAILBOX_URL')=='http://qh-guest-mailbox:8025'
    p=disclosure;command.upgrade(empty_database,'0009_guest_invitations')
    now=[datetime.now(timezone.utc)];clock=lambda:now[0]
    repository=PostgresGuestRepository(url=p['repo'].url,clock=clock)
    reader=PostgresSecurityReader(url=p['repo'].url)
    policy=OwnerPolicyService(owner_for=reader.owner_for,guest_for=repository.guest_for,clock=clock)
    p['disclosure'].drafts.authorize=projection_authorizer(policy)
    service=GuestInvitationService(disclosures=p['disclosure'],repository=repository,
        proofs=SecureGuestProofs(b'qh20-isolated-only-private-key-32-bytes'),mailer=SandboxSMTPMailer(),
        authorize=guest_authorizer(policy),clock=clock)
    with httpx.Client(base_url=os.environ['QH20_MAILBOX_URL'],timeout=5) as mailbox:
        response=mailbox.delete('/api/v1/messages');assert response.status_code in (200,204)
        p.update(guest=service,guest_repository=repository,policy=policy,clock=now,mailbox=mailbox)
        snapshot=approve(p,prepare(p,include_proposed=True))
        p['snapshot']=snapshot
        p['invitation']=run(service.create(p['repo'].subject_id,p['scope'],snapshot.id))
        yield p


def challenge(p,invitation=None,email='clement@example.test',peer='guest-test'):
    invitation=invitation or p['invitation']
    return run(p['guest'].request_code(invitation.token,email,peer))


def mailbox_code(p):
    messages=p['mailbox'].get('/api/v1/messages').json()['messages']
    if not messages:raise AssertionError('No SMTP message delivered to private mailbox')
    message=p['mailbox'].get('/api/v1/message/'+messages[0]['ID']).json()
    match=re.search(r'Code de vérification QH : (\d{8})',message.get('Text',''))
    if match is None:raise AssertionError('No usable code in the delivered SMTP message')
    return match.group(1),message


def verified(p,invitation=None,peer='guest-test'):
    invitation=invitation or p['invitation'];receipt=challenge(p,invitation,peer=peer)
    code,_=mailbox_code(p)
    result=run(p['guest'].verify(invitation.token,receipt['challenge_id'],code,peer))
    return result,receipt,code


def test_real_smtp_delivery_then_session_safe_snapshot_and_no_guest_user(guest):
    p=guest;before=p['repo'].read_snapshot((p['scope'],))
    with p['repo'].connect() as c:users=c.execute('SELECT count(*) AS n FROM users').fetchone()['n']
    session,receipt,code=verified(p)
    assert run(p['guest'].snapshot(session.token,p['snapshot'].id))==p['snapshot'].payload
    _,message=mailbox_code(p)
    assert message['To'][0]['Address']=='clement@example.test'
    with p['repo'].connect() as c:
        row=c.execute('SELECT code_hash,used_at,delivery_state FROM guest_challenges WHERE id=%s',
            (receipt['challenge_id'],)).fetchone()
        invite_hash=p['guest'].proofs.token_hash(p['invitation'].token,'invitation')
        assert row['code_hash']==p['guest'].proofs.code_hash(invite_hash,receipt['challenge_id'],code)
        assert row['used_at'] and row['delivery_state']=='sent'
        data=json.dumps(c.execute('SELECT row_to_json(g) AS row FROM guest_sessions g').fetchall(),default=str)
        if session.token in data or code in data or p['invitation'].token in data:
            raise AssertionError('A raw proof was persisted')
        assert c.execute('SELECT count(*) AS n FROM users').fetchone()['n']==users
    assert p['repo'].read_snapshot((p['scope'],))==before


def test_forwarded_link_wrong_email_and_unknown_link_have_generic_receipts_without_mail(guest):
    p=guest
    a=challenge(p,email='someone-else@example.test')
    wrong=replace(p['invitation'],token='not-an-invitation')
    b=challenge(p,wrong)
    assert a['message']==b['message'] and set(a)==set(b)=={'challenge_id','message'}
    assert p['mailbox'].get('/api/v1/messages').json()['total']==0
    for invitation,receipt in ((p['invitation'],a),(wrong,b)):
        with pytest.raises(GuestDenied):run(p['guest'].verify(invitation.token,receipt['challenge_id'],'00000000','guest-test'))


def test_wrong_codes_commit_attempts_and_correct_code_cannot_bypass_lockout(guest):
    p=guest;receipt=challenge(p);code,_=mailbox_code(p)
    wrong='0'*8 if code!='0'*8 else '1'*8
    for _ in range(5):
        with pytest.raises(GuestDenied):run(p['guest'].verify(p['invitation'].token,receipt['challenge_id'],wrong,'guest-test'))
    with pytest.raises(GuestDenied):run(p['guest'].verify(p['invitation'].token,receipt['challenge_id'],code,'guest-test'))
    with p['repo'].connect() as c:
        assert c.execute('SELECT attempts FROM guest_challenges WHERE id=%s',(receipt['challenge_id'],)).fetchone()['attempts']==5
        assert c.execute('SELECT failed_verifications FROM guest_invitations').fetchone()['failed_verifications']==5
        assert c.execute('SELECT count(*) AS n FROM guest_sessions').fetchone()['n']==0


def test_code_expiry_reuse_and_other_invitation_challenge_are_denied(guest):
    p=guest;receipt=challenge(p);code,_=mailbox_code(p)
    other=run(p['guest'].create(p['repo'].subject_id,p['scope'],p['snapshot'].id))
    with pytest.raises(GuestDenied):run(p['guest'].verify(other.token,receipt['challenge_id'],code,'guest-test'))
    p['clock'][0]+=timedelta(minutes=5)
    with pytest.raises(GuestDenied):run(p['guest'].verify(p['invitation'].token,receipt['challenge_id'],code,'guest-test'))
    session,new_receipt,new_code=verified(p)
    with pytest.raises(GuestDenied):run(p['guest'].verify(p['invitation'].token,new_receipt['challenge_id'],new_code,'guest-test'))
    assert run(p['guest'].session(session.token)).snapshot_id==p['snapshot'].id


def test_cooldown_resend_cap_and_old_challenge_invalidation(guest):
    p=guest;old=challenge(p);old_code,_=mailbox_code(p)
    challenge(p)
    assert p['mailbox'].get('/api/v1/messages').json()['total']==1
    p['clock'][0]+=timedelta(seconds=60);challenge(p)
    with pytest.raises(GuestDenied):run(p['guest'].verify(p['invitation'].token,old['challenge_id'],old_code,'guest-test'))
    p['clock'][0]+=timedelta(seconds=60);challenge(p)
    p['clock'][0]+=timedelta(seconds=60);challenge(p)
    assert p['mailbox'].get('/api/v1/messages').json()['total']==3


@pytest.mark.parametrize('reason',['logout','revoke','session-expiry','invitation-expiry','owner-disabled'])
def test_session_is_rechecked_on_every_request(guest,reason):
    p=guest;session,_,_=verified(p)
    assert run(p['guest'].snapshot(session.token,p['snapshot'].id))['items']
    if reason=='logout':run(p['guest'].logout(session.token))
    elif reason=='revoke':run(p['guest'].revoke(p['repo'].subject_id,p['scope'],p['invitation'].id))
    elif reason=='session-expiry':p['clock'][0]+=timedelta(minutes=30)
    elif reason=='invitation-expiry':p['clock'][0]+=timedelta(hours=2)
    else:
        with p['repo'].connect() as c:c.execute("UPDATE context_spaces SET status='inactive' WHERE id=%s",(p['scope'],))
    with pytest.raises(GuestDenied):run(p['guest'].snapshot(session.token,p['snapshot'].id))


def test_owner_isolation_snapshot_binding_rights_and_no_original_source_fetch(guest,monkeypatch):
    p=guest;session,_,_=verified(p)
    with pytest.raises(GuestDenied):run(p['guest'].snapshot(session.token,uid()))
    with pytest.raises(GuestDenied):run(p['guest'].snapshot(session.token,p['snapshot'].id,'ASK_AI'))
    for subject,scope in ((uid(),p['scope']),(p['repo'].subject_id,p['foreign'])):
        with pytest.raises(ProjectionNotFound):run(p['guest'].create(subject,scope,p['snapshot'].id))
        with pytest.raises(ProjectionNotFound):run(p['guest'].revoke(subject,scope,p['invitation'].id))
    def no_originals(*a,**kw):raise AssertionError('Guest must not hydrate canonical source')
    monkeypatch.setattr(type(p['repo']),'read_snapshot',no_originals)
    assert run(p['guest'].snapshot(session.token,p['snapshot'].id))==p['snapshot'].payload


def test_frozen_snapshot_does_not_expand_after_new_revision_and_graph_work(guest):
    p=guest;session,_,_=verified(p)
    p['repo'].save(revisions=[revision(p,'NEW PRIVATE OUTSIDE SNAPSHOT')]);drain(p['worker'])
    payload=run(p['guest'].snapshot(session.token,p['snapshot'].id))
    assert payload==p['snapshot'].payload and 'NEW PRIVATE' not in json.dumps(payload)


def test_simultaneous_valid_code_consumption_has_one_session(guest):
    p=guest;receipt=challenge(p);code,_=mailbox_code(p)
    def consume(_):
        try:return run(p['guest'].verify(p['invitation'].token,receipt['challenge_id'],code,'guest-test'))
        except GuestDenied:return None
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(consume,range(2)))
    assert sum(r is not None for r in results)==1
    with p['repo'].connect() as c:assert c.execute('SELECT count(*) AS n FROM guest_sessions').fetchone()['n']==1


def test_peer_rate_limit_durable_after_service_recreation(guest):
    p=guest
    for _ in range(10):challenge(p,email='unknown@example.test',peer='same-peer')
    with pytest.raises(GuestRateLimited):challenge(p,peer='same-peer')
    reopened=PostgresGuestRepository(url=p['repo'].url,clock=lambda:p['clock'][0])
    key=p['guest'].proofs.peer_hash('same-peer','request')
    assert run(reopened.limit(key,10)) is False
    p['clock'][0]+=timedelta(seconds=60)
    assert run(reopened.limit(key,10)) is True


def test_resend_does_not_reset_cumulative_failures(guest):
    p=guest
    for attempt in range(2):
        if attempt:p['clock'][0]+=timedelta(seconds=60)
        receipt=challenge(p);code,_=mailbox_code(p)
        wrong='0'*8 if code!='0'*8 else '1'*8
        for _ in range(5):
            with pytest.raises(GuestDenied):run(p['guest'].verify(p['invitation'].token,receipt['challenge_id'],wrong,'guest-test'))
    p['clock'][0]+=timedelta(seconds=60);challenge(p)
    assert p['mailbox'].get('/api/v1/messages').json()['total']==2
    with p['repo'].connect() as c:
        assert c.execute('SELECT failed_verifications FROM guest_invitations').fetchone()['failed_verifications']==10


def test_concurrent_code_requests_deliver_only_one_message(guest):
    p=guest
    with ThreadPoolExecutor(2) as pool:receipts=list(pool.map(lambda _:challenge(p),range(2)))
    assert all(set(r)=={'challenge_id','message'} for r in receipts)
    assert p['mailbox'].get('/api/v1/messages').json()['total']==1
    with p['repo'].connect() as c:
        assert c.execute('SELECT send_count FROM guest_invitations').fetchone()['send_count']==1
        assert c.execute('SELECT count(*) AS n FROM guest_challenges').fetchone()['n']==1


def test_verification_peer_limit_precedes_more_guesses(guest):
    p=guest
    for _ in range(30):
        with pytest.raises(GuestDenied):run(p['guest'].verify(p['invitation'].token,uid(),'00000000','same-peer'))
    with pytest.raises(GuestRateLimited):run(p['guest'].verify(p['invitation'].token,uid(),'00000000','same-peer'))


def test_ask_only_grant_does_not_imply_read_and_keeps_snapshot_scope(guest):
    p=guest
    snapshot=approve(p,prepare(p,include_proposed=True,rights=('ASK_AI',),provider='offline'))
    invite=run(p['guest'].create(p['repo'].subject_id,p['scope'],snapshot.id))
    session,_,_=verified(p,invite)
    with pytest.raises(GuestDenied):run(p['guest'].snapshot(session.token,snapshot.id))
    with pytest.raises(GuestDenied):run(p['guest'].snapshot(session.token,p['snapshot'].id,'ASK_AI'))
    assert run(p['guest'].snapshot(session.token,snapshot.id,'ASK_AI'))==snapshot.payload


@pytest.mark.parametrize('field',['context_id','snapshot_id'])
def test_guest_payload_port_cannot_return_another_scope(guest,monkeypatch,field):
    p=guest;session,_,_=verified(p)
    payload=GuestSnapshot(context_id=p['scope'],snapshot_id=p['snapshot'].id,payload_json=json.dumps(p['snapshot'].payload))
    monkeypatch.setattr(p['guest_repository'],'payload',AsyncMock(return_value=replace(payload,**{field:uid()})))
    with pytest.raises(GuestUnavailable):run(p['guest'].snapshot(session.token,p['snapshot'].id))


def test_failed_delivery_cannot_verify_and_does_not_retry(guest,monkeypatch):
    p=guest;calls=[]
    async def failure(delivery,code):calls.append(delivery.challenge_id);raise MailUnavailable('Sandbox mail unavailable')
    monkeypatch.setattr(p['guest'].mailer,'send',failure)
    receipt=challenge(p)
    assert calls==[receipt['challenge_id']]
    with p['repo'].connect() as c:
        row=c.execute('SELECT delivery_state FROM guest_challenges WHERE id=%s',(receipt['challenge_id'],)).fetchone()
        assert row['delivery_state']=='failed'
    with pytest.raises(GuestDenied):run(p['guest'].verify(p['invitation'].token,receipt['challenge_id'],'00000000','guest-test'))


def test_guest_binding_and_counters_cannot_be_rewritten_in_sql(guest):
    p=guest;session,_,_=verified(p)
    for sql in ('UPDATE guest_invitations SET send_count=0',
                'UPDATE guest_invitations SET snapshot_id=gen_random_uuid()',
                "UPDATE guest_sessions SET expires_at=expires_at+interval '1 hour'",
                'UPDATE guest_challenges SET used_at=NULL',
                'DELETE FROM guest_sessions'):
        with p['repo'].connect() as c,pytest.raises(psycopg.errors.CheckViolation):c.execute(sql)
    run(p['guest'].logout(session.token))
    with p['repo'].connect() as c,pytest.raises(psycopg.errors.CheckViolation):c.execute('UPDATE guest_sessions SET revoked_at=NULL')


def test_https_origin_secure_cookie_and_real_mailbox_http_flow(guest,caplog):
    p=guest;auth,_=build_auth(mapping={'external-alice':p['repo'].subject_id,'external-bob':uid()})
    caplog.set_level(logging.INFO)
    app=create_app(services=ApplicationServices(context=FakeContextService(FakeContextEngine(RESULT)),policy=p['policy'],guest=p['guest']),
        security=SecurityBindings(authenticate=auth.authenticate,policy=p['policy']),guest_http=GuestHTTPConfig(origin=ORIGIN,minimum_response_seconds=0))
    with TestClient(app,base_url=ORIGIN,headers={'Origin':ORIGIN}) as client:
        assert client.get('/guest/snapshots/'+p['snapshot'].id).status_code==401
        owner_path=f'/context-spaces/{p["scope"]}/snapshots/{p["snapshot"].id}/invitations'
        assert client.post(owner_path,json={}).status_code==401
        assert client.post(owner_path,json={},headers={'Authorization':'Bearer '+token(sub='external-bob')}).status_code==404
        owner={'Authorization':'Bearer '+token()}
        created=client.post(owner_path,json={},headers=owner)
        assert created.status_code==201
        invite=created.json();proof=invite['invitation_token']
        response=client.post('/guest/code',json={'invitation_token':proof,'email':'clement@example.test'})
        assert response.status_code==202 and set(response.json())=={'challenge_id','message'}
        code,_=mailbox_code(p)
        verified=client.post('/guest/verify',json={'invitation_token':proof,'challenge_id':response.json()['challenge_id'],'code':code})
        assert verified.status_code==200 and verified.json()['verification']=='mailbox_control'
        cookie=verified.headers['set-cookie'].lower()
        assert COOKIE.lower() in cookie and all(flag in cookie for flag in ('secure','httponly','samesite=strict','path=/'))
        assert 'token' not in json.dumps(verified.json()) and 'email' not in verified.json()
        assert client.get('/guest/snapshots/'+p['snapshot'].id).json()==p['snapshot'].payload
        assert client.get('/context-spaces/'+p['scope']).status_code==401
        csrf=client.post('/guest/logout',json={},headers={'Origin':'https://attacker.example.test'})
        assert csrf.status_code==403
        assert client.get('/guest/session').status_code==200
        bad=client.post('/guest/verify',json={'invitation_token':proof,'challenge_id':'bad','code':code})
        assert bad.status_code==400 and 'input' not in bad.json()
        revoke=f'/context-spaces/{p["scope"]}/invitations/{invite["id"]}/revoke'
        assert client.post(revoke,json={},headers=owner).status_code==204
        assert client.get('/guest/snapshots/'+p['snapshot'].id).status_code==401
        assert client.get('/guest/session').headers['cache-control']=='private, no-store'
        if proof in caplog.text or code in caplog.text or 'clement@example.test' in caplog.text:
            raise AssertionError('A guest proof or address leaked into application logs')


def test_http_denies_insecure_origin_oversized_and_extra_input_and_logout_revokes(guest):
    p=guest;auth,_=build_auth(mapping={'external-alice':p['repo'].subject_id})
    app=create_app(services=ApplicationServices(context=FakeContextService(FakeContextEngine(RESULT)),policy=p['policy'],guest=p['guest']),
        security=SecurityBindings(authenticate=auth.authenticate,policy=p['policy']),guest_http=GuestHTTPConfig(origin=ORIGIN,minimum_response_seconds=0))
    with TestClient(app,base_url='http://qh.example.test') as client:
        assert client.get('/guest/session').status_code==403
    with TestClient(app,base_url=ORIGIN,headers={'Origin':ORIGIN}) as client:
        assert client.post('/guest/code',json={'invitation_token':'x','email':'x','extra':'x'}).status_code==400
        assert client.post('/guest/code',content='x'*4097,headers={'Content-Type':'application/json'}).status_code==413
        response=client.post('/guest/code',json={'invitation_token':p['invitation'].token,'email':'clement@example.test'})
        code,_=mailbox_code(p)
        response=client.post('/guest/verify',json={'invitation_token':p['invitation'].token,
            'challenge_id':response.json()['challenge_id'],'code':code})
        assert response.status_code==200
        cookie=client.cookies.get(COOKIE)
        assert client.post('/guest/logout',json={}).status_code==204
        client.cookies.set(COOKIE,cookie,domain='qh.example.test',path='/')
        assert client.get('/guest/session').status_code==401
