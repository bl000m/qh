"""Owner-only resource policy; no transport or SQL dependencies."""

from typing import Awaitable, Callable
from datetime import datetime, timezone

from app.core.models import ContextId, GuestAccess, SubjectId
from app.policy.models import PolicyAction, PolicyDecision, PolicyRequest


class OwnerPolicyService:
    def __init__(self, *, owner_for: Callable[[ContextId], Awaitable[SubjectId | None]],
                 guest_for: Callable[[str], Awaitable[GuestAccess | None]] | None = None, clock=None) -> None:
        self._owner_for = owner_for
        self._guest_for = guest_for
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    async def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        if request.action in (PolicyAction.READ_SNAPSHOT, PolicyAction.ASK_SNAPSHOT):
            return await self._snapshot(request)
        # Guest sessions can never be repurposed into owner/Space actions.
        if request.guest_session_id is not None or request.snapshot_id is not None:
            return PolicyDecision(allowed=False, reason='Snapshot access required')
        if not request.subject_id:
            return PolicyDecision(allowed=False, reason="Owner access required")
        if request.action in (PolicyAction.CREATE_CONTEXT, PolicyAction.LIST_CONTEXTS, PolicyAction.ORGANIZE_ENVIRONMENT):
            # The trusted authenticated subject selects only their own namespace.
            # No target owner or foreign scope can be supplied with these actions.
            return PolicyDecision(allowed=not request.context_ids, reason=None if not request.context_ids else "Owner access required")
        # QH-13 owner-approved: CHAT is a separate single-Space operation.
        if request.action in (PolicyAction.CHAT, PolicyAction.PROJECT_CONTEXT) and len(request.context_ids) != 1:
            return PolicyDecision(allowed=False, reason="Owner access required")
        if not request.context_ids or request.action not in (PolicyAction.READ_CONTEXT, PolicyAction.UPDATE_CONTEXT, PolicyAction.CHAT, PolicyAction.PROPOSE_UPDATE, PolicyAction.CONFIRM_UPDATE, PolicyAction.PROJECT_CONTEXT):
            return PolicyDecision(allowed=False, reason="Owner access required")
        for context_id in request.context_ids:
            owner = await self._owner_for(context_id)
            if owner is None or owner != request.subject_id:
                return PolicyDecision(allowed=False, reason="Owner access required")
        return PolicyDecision(allowed=True)

    async def _snapshot(self, request):
        deny = PolicyDecision(allowed=False, reason='Snapshot access required')
        if (request.subject_id is not None or not request.guest_session_id or not request.snapshot_id
                or len(request.context_ids) != 1 or self._guest_for is None):
            return deny
        grant = await self._guest_for(request.guest_session_id)
        right = 'READ' if request.action == PolicyAction.READ_SNAPSHOT else 'ASK_AI'
        if (not isinstance(grant, GuestAccess) or grant.session_id != request.guest_session_id
                or grant.context_id != request.context_ids[0] or grant.snapshot_id != request.snapshot_id
                or grant.expires_at <= self.clock() or right not in grant.rights):
            return deny
        return PolicyDecision(allowed=True)
