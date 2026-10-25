"""Offline transient guest policy, proof domains and opt-in transport boundaries."""
import asyncio
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from adapters.guest_security import SecureGuestProofs
from adapters.sandbox_mail import SandboxSMTPMailer
from app.api.guest import GuestHTTPConfig
from app.core.models import GuestAccess
from app.main import create_app
from app.policy.models import PolicyAction, PolicyRequest
from app.policy.owner import OwnerPolicyService
from tests.test_projection_drafts import uid


def run(operation):
    return asyncio.run(operation)


def test_proofs_have_distinct_domains_and_private_otp_key():
    a,b=SecureGuestProofs(b'a'*32),SecureGuestProofs(b'b'*32)
    token=a.token();challenge=uid();code=a.code()
    assert len(token)>=43 and len(code)==8 and code.isdecimal()
    assert a.token_hash(token,'invitation')!=a.token_hash(token,'session')
    assert a.code_hash('x'*64,challenge,code)!=b.code_hash('x'*64,challenge,code)
    assert a.code_hash('x'*64,challenge,code)!=a.code_hash('y'*64,challenge,code)
    assert a.code_hash('x'*64,challenge,code)!=a.code_hash('x'*64,uid(),code)
    with pytest.raises(ValueError):SecureGuestProofs(b'short')
    with pytest.raises(ValueError):SandboxSMTPMailer(host='smtp.external.example')


def test_unbound_runtime_has_no_guest_or_invitation_routes():
    app=create_app()
    paths=set(app.openapi()['paths'])
    assert not any('/guest/' in p or '/invitations' in p for p in paths)


@pytest.mark.parametrize('origin',['http://qh.example.test','https://qh.example.test/','https://qh.example.test/path',
    'https://user:password@qh.example.test','https://qh.example.test?x=1','*'])
def test_guest_transport_requires_exact_https_origin(origin):
    with pytest.raises(ValueError):GuestHTTPConfig(origin=origin)


@pytest.mark.parametrize('change',['owner_actor','space','snapshot','session','expired','no_read','absent'])
def test_central_policy_denies_mismatched_snapshot_guest_actor(change):
    now=datetime.now(timezone.utc)
    grant=GuestAccess(session_id=uid(),invitation_id=uid(),context_id=uid(),snapshot_id=uid(),
        rights=('READ',),expires_at=now+timedelta(minutes=30))
    request=PolicyRequest(subject_id=None,action=PolicyAction.READ_SNAPSHOT,context_ids=(grant.context_id,),
        snapshot_id=grant.snapshot_id,guest_session_id=grant.session_id)
    facts=grant
    if change=='owner_actor':request=replace(request,subject_id=uid())
    elif change=='space':request=replace(request,context_ids=(uid(),))
    elif change=='snapshot':request=replace(request,snapshot_id=uid())
    elif change=='session':facts=replace(grant,session_id=uid())
    elif change=='expired':facts=replace(grant,expires_at=now)
    elif change=='no_read':facts=replace(grant,rights=('ASK_AI',))
    elif change=='absent':facts=None
    policy=OwnerPolicyService(owner_for=AsyncMock(),guest_for=AsyncMock(return_value=facts),clock=lambda:now)
    assert not run(policy.evaluate(request)).allowed


def test_guest_read_never_grants_ask_or_space_write_or_owner_access():
    now=datetime.now(timezone.utc)
    grant=GuestAccess(session_id=uid(),invitation_id=uid(),context_id=uid(),snapshot_id=uid(),
        rights=('READ',),expires_at=now+timedelta(minutes=30))
    policy=OwnerPolicyService(owner_for=AsyncMock(return_value=uid()),guest_for=AsyncMock(return_value=grant))
    request=PolicyRequest(subject_id=None,action=PolicyAction.READ_SNAPSHOT,context_ids=(grant.context_id,),
        snapshot_id=grant.snapshot_id,guest_session_id=grant.session_id)
    assert run(policy.evaluate(request)).allowed
    for action in (PolicyAction.ASK_SNAPSHOT,PolicyAction.READ_CONTEXT,PolicyAction.CHAT,
                   PolicyAction.PROPOSE_UPDATE,PolicyAction.CONFIRM_UPDATE,PolicyAction.PROJECT_CONTEXT):
        assert not run(policy.evaluate(replace(request,action=action))).allowed
