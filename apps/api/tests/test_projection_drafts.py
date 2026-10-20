"""QH-14 draft model and central policy; no network or provider."""
import asyncio
from dataclasses import replace
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.policy.models import PolicyAction
from app.policy.owner import OwnerPolicyService
from app.policy.services import projection_authorizer
from app.projections.drafts import DraftSpec, ProjectionDraft, ProjectionNotFound, ProjectionUnavailable, RevisionKey
from app.projections.engine import ProjectionDraftService


def uid():
    return str(uuid4())


def spec(**kwargs):
    return DraftSpec(**(dict(recipient_kind='subject',recipient='Clément',purpose='Pilot collaboration') | kwargs))


def key():
    return RevisionKey(item_id=uid(),revision_id=uid())


def run(value):
    return asyncio.run(value)


@pytest.mark.parametrize('changes', [
    {'recipient_kind':'everyone'}, {'recipient':''}, {'purpose':' '}, {'purpose':'x'*1025},
    {'included':[]}, {'included':tuple(key() for _ in range(101))}, {'included':('not-a-ref',)},
    {'expires_at':datetime(2026,10,20)},
])
def test_invalid_draft_contract(changes):
    with pytest.raises(ValueError):
        spec(**changes)


def test_exact_exclusions_win_and_never_infer_new_revisions():
    a,b=key(),key()
    assert spec(included=(a,b),excluded=(b,)).effective == (a,)
    assert spec().effective == ()
    with pytest.raises(ValueError):spec(included=(a,a))
    with pytest.raises(ValueError):RevisionKey(item_id=a.item_id,revision_id='not-an-id')
    with pytest.raises(ValueError):spec(included=(a,),excluded=(replace(a,item_id=uid()),))


def test_owner_denial_precedes_all_repository_access_and_no_recipient_grant():
    alice,bob,scope=uid(),uid(),uid()
    lookup=AsyncMock(return_value=alice)
    policy=OwnerPolicyService(owner_for=lookup)
    repository=Mock(create=AsyncMock(),read=AsyncMock(),replace=AsyncMock())
    service=ProjectionDraftService(repository=repository,authorize=projection_authorizer(policy))
    for operation in (service.create(bob,scope,spec()),service.read(bob,scope,uid()),
                      service.replace(bob,scope,uid(),1,spec())):
        with pytest.raises(ProjectionNotFound):run(operation)
    repository.create.assert_not_awaited()
    repository.read.assert_not_awaited()
    repository.replace.assert_not_awaited()


def test_policy_rechecked_before_disclosure_and_adapter_scope_checked():
    alice,scope=uid(),uid();now=datetime.now(timezone.utc)
    draft=ProjectionDraft(id=uid(),owner_id=alice,context_id=scope,version=1,spec=spec(),created_at=now,updated_at=now)
    repository=Mock(read=AsyncMock(return_value=draft))
    authorize=AsyncMock(side_effect=[True,False])
    service=ProjectionDraftService(repository=repository,authorize=authorize)
    with pytest.raises(ProjectionNotFound):run(service.read(alice,scope,draft.id))
    service=ProjectionDraftService(repository=repository,authorize=AsyncMock(return_value=True))
    repository.read.return_value=replace(draft,owner_id=uid())
    with pytest.raises(ProjectionUnavailable):run(service.read(alice,scope,draft.id))


def test_authorizer_uses_project_context_only():
    from app.policy.models import PolicyDecision
    policy=Mock(evaluate=AsyncMock(return_value=PolicyDecision(allowed=True)))
    assert run(projection_authorizer(policy)(uid(),uid())) is True
    assert policy.evaluate.call_args.args[0].action == PolicyAction.PROJECT_CONTEXT
