"""Owner-only resource policy; no transport or SQL dependencies."""

from typing import Awaitable, Callable

from app.core.models import ContextId, SubjectId
from app.policy.models import PolicyAction, PolicyDecision, PolicyRequest


class OwnerPolicyService:
    def __init__(self, *, owner_for: Callable[[ContextId], Awaitable[SubjectId | None]]) -> None:
        self._owner_for = owner_for

    async def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        if not request.subject_id:
            return PolicyDecision(allowed=False, reason="Owner access required")
        if request.action in (PolicyAction.CREATE_CONTEXT, PolicyAction.LIST_CONTEXTS, PolicyAction.ORGANIZE_ENVIRONMENT):
            # The trusted authenticated subject selects only their own namespace.
            # No target owner or foreign scope can be supplied with these actions.
            return PolicyDecision(allowed=not request.context_ids, reason=None if not request.context_ids else "Owner access required")
        # QH-13 owner-approved: CHAT is a separate single-Space operation.
        if request.action == PolicyAction.CHAT and len(request.context_ids) != 1:
            return PolicyDecision(allowed=False, reason="Owner access required")
        if not request.context_ids or request.action not in (PolicyAction.READ_CONTEXT, PolicyAction.UPDATE_CONTEXT, PolicyAction.CHAT):
            return PolicyDecision(allowed=False, reason="Owner access required")
        for context_id in request.context_ids:
            owner = await self._owner_for(context_id)
            if owner is None or owner != request.subject_id:
                return PolicyDecision(allowed=False, reason="Owner access required")
        return PolicyDecision(allowed=True)
