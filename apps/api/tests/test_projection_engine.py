"""Deterministic fail-closed resolution; adapter spies never call a provider."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.models import RevisionTime
from app.projections.drafts import ProjectedRevision, ProjectionConflict, ProjectionNotFound, ProjectionUnavailable
from app.projections.engine import ProjectionDraftService
from tests.test_projection_drafts import key, run, spec, uid


def setup():
    from app.projections.drafts import ProjectionDraft
    alice,scope,draft_id=uid(),uid(),uid();a,b=key(),key();now=datetime.now(timezone.utc)
    draft=ProjectionDraft(id=draft_id,context_id=scope,owner_id=alice,version=1,
        spec=spec(included=(a,b),excluded=(b,)),created_at=now,updated_at=now)
    row=ProjectedRevision(context_id=scope,item_id=a.item_id,revision_id=a.revision_id,
        revision_no=1,structural_kind='item',type_id='qh.generic.item',type_version=1,
        content={'text':'Allowed pilot'},origin_kind='ai',validation_state='proposed',
        temporal=RevisionTime(fact_from=None,fact_to=None,valid_from=None,valid_to=None),relation=None,provenance=())
    repository=Mock(read=AsyncMock(return_value=draft))
    resolver=Mock(resolve=AsyncMock(return_value=(row,)))
    service=ProjectionDraftService(repository=repository,authorize=AsyncMock(return_value=True),resolver=resolver,clock=lambda:now)
    return alice,scope,draft,a,b,row,service


def test_exact_revision_result_and_no_provider_dependency():
    alice,scope,draft,a,b,row,service=setup()
    result=run(service.resolve(alice,scope,draft.id,1))
    assert result.revisions==(row,) and result.version==1
    service.resolver.resolve.assert_awaited_once_with(alice,scope,(a,))
    assert not hasattr(service,'provider')


@pytest.mark.parametrize('reason',['empty','expired','version','direct-excluded','direct-unknown','duplicate','policy'])
def test_negative_cases_deny_before_content_resolution(reason):
    alice,scope,draft,a,b,row,service=setup();version=1;requested=None
    if reason=='empty':service.repository.read.return_value=replace(draft,spec=spec())
    elif reason=='expired':service.repository.read.return_value=replace(draft,spec=replace(draft.spec,expires_at=service.clock()))
    elif reason=='version':version=2
    elif reason=='direct-excluded':requested=(b,)
    elif reason=='direct-unknown':requested=(key(),)
    elif reason=='duplicate':requested=(a,a)
    elif reason=='policy':service.authorize.return_value=False
    with pytest.raises((ProjectionNotFound,ProjectionConflict)):
        run(service.resolve(alice,scope,draft.id,version,requested))
    service.resolver.resolve.assert_not_awaited()


@pytest.mark.parametrize('failure',['extra','missing','foreign','changed','revoked','expired-inflight','error'])
def test_fail_closed_after_adapter_or_concurrent_change(failure):
    alice,scope,draft,a,b,row,service=setup()
    if failure=='extra':service.resolver.resolve.return_value=(row,replace(row,item_id=b.item_id,revision_id=b.revision_id))
    elif failure=='missing':service.resolver.resolve.return_value=()
    elif failure=='foreign':service.resolver.resolve.return_value=(replace(row,context_id=uid()),)
    elif failure=='changed':service.repository.read.side_effect=[draft,replace(draft,version=2)]
    elif failure=='revoked':service.authorize.side_effect=[True,True,False]
    elif failure=='expired-inflight':
        end=service.clock()+timedelta(seconds=1)
        service.repository.read.return_value=replace(draft,spec=replace(draft.spec,expires_at=end))
        service.clock=Mock(side_effect=[end-timedelta(seconds=1),end])
    elif failure=='error':service.resolver.resolve.side_effect=RuntimeError('PRIVATE CANARY')
    with pytest.raises((ProjectionNotFound,ProjectionConflict,ProjectionUnavailable)) as caught:
        run(service.resolve(alice,scope,draft.id,1))
    assert 'PRIVATE CANARY' not in str(caught.value)
