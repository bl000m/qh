import asyncio

import pytest

from app.core.models import ContextId, SubjectId
from app.policy.models import PolicyAction, PolicyRequest
from app.policy.owner import OwnerPolicyService
from app.policy.services import PolicyService

OWNER = SubjectId("owner")
OTHER = SubjectId("other")
OWN = ContextId("own-space")
FOREIGN = ContextId("foreign-space")


@pytest.mark.parametrize("subject,contexts,action,allowed,lookups", [
    (OWNER, (OWN,), PolicyAction.READ_CONTEXT, True, [OWN]),
    (OTHER, (OWN,), PolicyAction.READ_CONTEXT, False, [OWN]),
    (OWNER, (FOREIGN,), PolicyAction.READ_CONTEXT, False, [FOREIGN]),
    (OWNER, (ContextId("missing"),), PolicyAction.READ_CONTEXT, False, [ContextId("missing")]),
    (OWNER, (OWN, FOREIGN), PolicyAction.READ_CONTEXT, False, [OWN, FOREIGN]),
    (SubjectId(""), (OWN,), PolicyAction.READ_CONTEXT, False, []),
    (OWNER, (), PolicyAction.READ_CONTEXT, False, []),
    (OWNER, (OWN,), PolicyAction.PROJECT_CONTEXT, False, []),
    (OWNER, (OWN,), PolicyAction.CHAT, False, []),
])
def test_owner_read_policy(subject, contexts, action, allowed, lookups) -> None:
    calls = []

    async def owner_for(context_id):
        calls.append(context_id)
        return {OWN: OWNER, FOREIGN: OTHER}.get(context_id)

    policy = OwnerPolicyService(owner_for=owner_for)
    assert isinstance(policy, PolicyService)
    decision = asyncio.run(policy.evaluate(PolicyRequest(subject_id=subject, action=action, context_ids=contexts)))
    assert decision.allowed is allowed
    assert calls == lookups


def test_ownership_lookup_failure_never_becomes_permission() -> None:
    async def unavailable(_context):
        raise RuntimeError("lookup unavailable")

    with pytest.raises(RuntimeError):
        asyncio.run(OwnerPolicyService(owner_for=unavailable).evaluate(
            PolicyRequest(subject_id=OWNER, action=PolicyAction.READ_CONTEXT, context_ids=(OWN,))))
