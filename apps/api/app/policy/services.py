from typing import Protocol, runtime_checkable

from app.policy.models import PolicyDecision, PolicyRequest


@runtime_checkable
class PolicyService(Protocol):
    """Evaluate whether a subject may perform a QH action on selected contexts.

    Future implementations own policy decisions, not identity authentication
    or persistence. No allow-all/deny-all production implementation is provided.
    """

    async def evaluate(self, request: PolicyRequest) -> PolicyDecision: ...


def projection_authorizer(policy: PolicyService):
    """Dependency bridge: draft operations reuse this one resource-decision port."""
    from app.policy.models import PolicyAction

    async def allowed(subject, scope):
        return (await policy.evaluate(PolicyRequest(subject_id=subject,
            action=PolicyAction.PROJECT_CONTEXT, context_ids=(scope,)))).allowed
    return allowed
