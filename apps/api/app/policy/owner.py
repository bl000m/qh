"""Owner-only read policy for the local demo; no transport or SQL dependencies."""

from typing import Awaitable, Callable

from app.core.models import ContextId, SubjectId
from app.policy.models import PolicyAction, PolicyDecision, PolicyRequest


class OwnerPolicyService:
    def __init__(self, *, owner_for: Callable[[ContextId], Awaitable[SubjectId | None]]) -> None:
        self._owner_for = owner_for

    async def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        if not request.subject_id or not request.context_ids or request.action != PolicyAction.READ_CONTEXT:
            return PolicyDecision(allowed=False, reason="Owner access required")
        for context_id in request.context_ids:
            owner = await self._owner_for(context_id)
            if owner is None or owner != request.subject_id:
                return PolicyDecision(allowed=False, reason="Owner access required")
        return PolicyDecision(allowed=True)
