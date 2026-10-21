"""Owner policy and graph-verified retrieval precede review access and publication."""
from typing import Protocol
from uuid import UUID

from app.core.models import ContextBrowse, ContextRequest, ContextSpaceNotFound
from app.policy.models import PolicyAction, PolicyRequest


class ReviewConflict(ValueError):
    """Changed input, operation key conflict or obsolete review target."""


class ReviewRepository(Protocol):
    async def pending(self, subject, scope, limit, after): ...
    async def status(self, subject, scope, revision): ...
    async def apply(self, subject, scope, revision, operation): ...


class ReviewService:
    def __init__(self, *, context, policy, repository: ReviewRepository):
        self.context, self.policy, self.repository = context, policy, repository

    async def _allow(self, subject, scope, action):
        result = await self.policy.evaluate(PolicyRequest(subject_id=subject, action=action, context_ids=(scope,)))
        if not result.allowed:
            raise ContextSpaceNotFound('Context space not found')

    async def _revision(self, subject, scope, revision):
        result = await self.context.browse(ContextRequest(subject_id=subject,
            query=ContextBrowse(context_id=scope, view='history', revision_id=revision, limit=1)))
        if len(result.revisions) != 1:
            raise ContextSpaceNotFound('Revision not found')
        return result.revisions[0]

    async def pending(self, subject, scope, limit, after):
        await self._allow(subject, scope, PolicyAction.READ_CONTEXT)
        ids = await self.repository.pending(subject, scope, limit+1, after)
        # Even an empty inbox must establish graph availability/freshness.
        await self.context.browse(ContextRequest(subject_id=subject,
            query=ContextBrowse(context_id=scope, view='history', limit=1)))
        rows = tuple([await self._revision(subject, scope, id) for id in ids[:limit]])
        await self._allow(subject, scope, PolicyAction.READ_CONTEXT)
        return {'items': rows, 'next_after_revision_id': ids[limit-1] if len(ids)>limit else None}

    async def status(self, subject, scope, revision):
        await self._allow(subject, scope, PolicyAction.READ_CONTEXT)
        await self._revision(subject, scope, revision)
        result = await self.repository.status(subject, scope, revision)
        await self._allow(subject, scope, PolicyAction.READ_CONTEXT)
        return result

    async def apply(self, subject, scope, revision, operation):
        action = operation['action']
        if action not in ('confirm', 'reject', 'correct', 'review_assignments'):
            raise ValueError('Invalid review action')
        UUID(operation['operation_id'])
        for field in ('expected_latest_revision_id', 'expected_current_revision_id'):
            if operation[field] is not None:
                UUID(operation[field])
        text = operation.get('text')
        if action == 'correct':
            if not isinstance(text, str) or not text.strip() or len(text)>16000 or '\0' in text:
                raise ValueError('Nonempty bounded correction required')
        elif text is not None:
            raise ValueError('Only correction accepts text')
        decisions = operation.get('assignment_decisions')
        if action == 'review_assignments':
            if not isinstance(decisions, list) or not decisions:
                raise ValueError('Explicit assignment decisions required')
        elif decisions is not None:
            raise ValueError('Assignment decisions require their review action')
        policy_action = PolicyAction.PROPOSE_UPDATE if action in ('correct', 'review_assignments') else PolicyAction.CONFIRM_UPDATE
        await self._allow(subject, scope, policy_action)
        target = await self._revision(subject, scope, revision)
        if action == 'review_assignments':
            from app.understanding.descriptors import review_assignments
            if target.type_version != 2 or target.type_id not in ('qh.generic.item', 'qh.generic.entity', 'qh.generic.relation'):
                raise ValueError('Qualified semantic profile required')
            review_assignments(target.content.get('descriptors'), decisions, len(target.content.get('citations', [])))
            for decision in decisions:
                if decision.get('reuse_value') is not None:
                    matches = []
                    for view in ('current', 'proposed'):
                        page = await self.context.browse(ContextRequest(subject_id=subject, query=ContextBrowse(
                            context_id=scope, view=view, limit=1, descriptor=decision['reuse_value'],
                            descriptor_dimension='thematic', include_tentative=True, latest_pending=view=='proposed')))
                        matches.extend(page.revisions)
                    if not matches:
                        raise ReviewConflict('Theme name is no longer available in this Space')
        await self._allow(subject, scope, policy_action)
        return await self.repository.apply(subject, scope, revision, operation)
