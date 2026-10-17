"""Policy ordering and scope checks without a database or transport."""

import asyncio
from datetime import datetime, timezone

import pytest

from app.context.service import ManagedContextService
from app.core.models import ContextId, ContextSpace, ContextSpaceNotFound, SubjectId
from app.core.services import ContextService
from app.policy.models import PolicyAction, PolicyDecision, PolicyRequest
from app.policy.owner import OwnerPolicyService

ALICE, BOB = SubjectId("alice"), SubjectId("bob")
A = ContextId("space-a")
SPACE = ContextSpace(id=A, owner_id=ALICE, name="A", status="active",
                     created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))


@pytest.mark.parametrize("action,subject,contexts,allowed", [
    (PolicyAction.CREATE_CONTEXT, ALICE, (), True),
    (PolicyAction.LIST_CONTEXTS, BOB, (), True),
    (PolicyAction.CREATE_CONTEXT, ALICE, (A,), False),
    (PolicyAction.LIST_CONTEXTS, SubjectId(""), (), False),
    (PolicyAction.UPDATE_CONTEXT, ALICE, (A,), True),
    (PolicyAction.UPDATE_CONTEXT, BOB, (A,), False),
    (PolicyAction.UPDATE_CONTEXT, ALICE, (), False),
])
def test_existing_policy_authorizes_only_own_management_scope(action, subject, contexts, allowed):
    async def owner_for(id):
        return ALICE if id == A else None
    decision = asyncio.run(OwnerPolicyService(owner_for=owner_for).evaluate(
        PolicyRequest(subject_id=subject, action=action, context_ids=contexts)))
    assert decision.allowed is allowed


def test_service_checks_policy_before_each_repository_access_and_pages():
    events = []
    class Policy:
        async def evaluate(self, request):
            events.append(request.action)
            return PolicyDecision(allowed=True)
    class Repository:
        async def create(self, **kwargs):
            events.append("create"); return SPACE
        async def list_ids(self, **kwargs):
            events.append("list_ids"); assert kwargs == dict(subject_id=ALICE, limit=2, after_id=None)
            return (A, ContextId("next"))
        async def read(self, **kwargs):
            events.append("read"); return SPACE
        async def rename(self, **kwargs):
            events.append("rename"); return SPACE
    async def exercise():
        service = ManagedContextService(repository=Repository(), policy=Policy())
        assert isinstance(service, ContextService)
        assert await service.create_space(subject_id=ALICE, name="A") == SPACE
        page = await service.list_spaces(subject_id=ALICE, limit=1)
        assert page.items == (SPACE,) and page.next_after_id == A
        assert await service.rename_space(subject_id=ALICE, context_id=A, name="Renamed") == SPACE
    asyncio.run(exercise())
    assert events == [PolicyAction.CREATE_CONTEXT, "create", PolicyAction.LIST_CONTEXTS,
                      "list_ids", PolicyAction.READ_CONTEXT, "read", PolicyAction.UPDATE_CONTEXT, "rename"]


@pytest.mark.parametrize("operation", ["create_space", "list_spaces", "get_space", "rename_space"])
def test_denial_prevents_any_repository_call(operation):
    class Deny:
        async def evaluate(self, request):
            return PolicyDecision(allowed=False)
    async def exercise():
        service = ManagedContextService(repository=object(), policy=Deny())
        args = {"subject_id": BOB}
        if operation in ("create_space", "rename_space"):args["name"] = "Name"
        if operation in ("get_space", "rename_space"):args["context_id"] = A
        with pytest.raises((PermissionError, ContextSpaceNotFound)):
            await getattr(service, operation)(**args)
    asyncio.run(exercise())


@pytest.mark.parametrize("name", ["", "  \n", "x" * 257, "x\x00y", 123])
def test_invalid_names_never_reach_repository(name):
    class Allow:
        async def evaluate(self, request): return PolicyDecision(allowed=True)
    with pytest.raises(ValueError):
        asyncio.run(ManagedContextService(repository=object(), policy=Allow()).create_space(
            subject_id=ALICE, name=name))
