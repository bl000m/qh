from typing import Protocol, runtime_checkable

from app.policy.models import PolicyDecision, PolicyRequest


@runtime_checkable
class PolicyService(Protocol):
    """Evaluate whether a subject may perform a QH action on selected contexts.

    Future implementations own policy decisions, not identity authentication
    or persistence. No allow-all/deny-all production implementation is provided.
    """

    async def evaluate(self, request: PolicyRequest) -> PolicyDecision: ...
