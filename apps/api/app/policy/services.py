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


def guest_authorizer(policy: PolicyService):
    """Only a token-authenticated application may supply the transient session ID."""
    from app.policy.models import PolicyAction
    async def allowed(grant, right):
        action = {'READ': PolicyAction.READ_SNAPSHOT, 'ASK_AI': PolicyAction.ASK_SNAPSHOT}.get(right)
        if action is None:
            return False
        return (await policy.evaluate(PolicyRequest(subject_id=None, action=action,
            context_ids=(grant.context_id,), snapshot_id=grant.snapshot_id, guest_session_id=grant.session_id))).allowed
    return allowed
