"""Exercise ports and inbound contracts using explicitly injected test fakes."""

import asyncio
from dataclasses import FrozenInstanceError
import inspect
from typing import get_type_hints

import pytest

from app.chat.models import ChatRequest, ChatResponse
from app.chat.services import ChatService
from app.composition import ApplicationServices
from app.core.models import (
    ContextQuery, ContextRequest, ContextResult,
    GenerationRequest, GenerationResult, Message, MessageRole, SubjectId,
)
from app.core.ports import ContextEngine, LLMProvider
from app.core.services import ContextService
from app.policy.models import PolicyAction, PolicyDecision, PolicyRequest
from app.policy.services import PolicyService
from app.projections.models import ContextProjection, ProjectionRequest
from app.projections.services import ProjectionService
from tests.fakes import (
    GENERATION, MESSAGE, RECORD, RESULT,
    AlternateContextEngine, AlternateLLMProvider,
    FakeChatService, FakeContextEngine, FakeContextService,
    FakeLLMProvider, FakePolicyService, FakeProjectionService,
)

@pytest.mark.parametrize("engine", [FakeContextEngine(RESULT), AlternateContextEngine()])
def test_context_engine_is_replaceable(engine: ContextEngine) -> None:
    query = ContextQuery(text="test")
    assert isinstance(engine, ContextEngine)
    result = asyncio.run(engine.search(query))
    assert isinstance(result, ContextResult)
    assert result == RESULT


@pytest.mark.parametrize("provider", [FakeLLMProvider(GENERATION), AlternateLLMProvider()])
def test_llm_provider_is_replaceable(provider: LLMProvider) -> None:
    request = GenerationRequest(messages=(Message(role=MessageRole.USER, content="hello"),))
    assert isinstance(provider, LLMProvider)
    result = asyncio.run(provider.generate(request))
    assert isinstance(result, GenerationResult)
    assert result == GENERATION


@pytest.mark.parametrize("port, method", [(ContextEngine, "search"), (LLMProvider, "generate")])
def test_outbound_signatures_use_only_qh_domain_values(port: type, method: str) -> None:
    hints = get_type_hints(getattr(port, method))
    assert hints
    assert all(hint.__module__ == "app.core.models" for hint in hints.values())


@pytest.mark.parametrize("contract, implementation, method", [
    (ContextEngine, FakeContextEngine, "search"),
    (LLMProvider, FakeLLMProvider, "generate"),
    (ContextService, FakeContextService, "retrieve"),
    (PolicyService, FakePolicyService, "evaluate"),
    (ProjectionService, FakeProjectionService, "project"),
    (ChatService, FakeChatService, "respond"),
])
def test_fake_signatures_match_contracts(
    contract: type, implementation: type, method: str,
) -> None:
    expected = getattr(contract, method)
    actual = getattr(implementation, method)
    assert inspect.iscoroutinefunction(expected) and inspect.iscoroutinefunction(actual)
    assert get_type_hints(actual) == get_type_hints(expected)
    expected_parameters = inspect.signature(expected).parameters
    actual_parameters = inspect.signature(actual).parameters
    assert tuple(actual_parameters) == tuple(expected_parameters)
    assert [p.kind for p in actual_parameters.values()] == [
        p.kind for p in expected_parameters.values()
    ]


def test_service_bindings_preserve_injected_adapters_and_domain_values() -> None:
    async def exercise() -> None:
        engine = FakeContextEngine(RESULT)
        provider = FakeLLMProvider(GENERATION)
        decision = PolicyDecision(allowed=False, reason="test decision")
        projection = ContextProjection(text="test projection", context_ids=(RECORD.id,))
        bindings = ApplicationServices(
            context=FakeContextService(engine),
            policy=FakePolicyService(decision),
            projections=FakeProjectionService(projection),
            chat=FakeChatService(provider),
        )
        assert isinstance(bindings.context, ContextService)
        assert isinstance(bindings.policy, PolicyService)
        assert isinstance(bindings.projections, ProjectionService)
        assert isinstance(bindings.chat, ChatService)
        subject = SubjectId("test-subject")
        query = ContextQuery(text="test")
        assert await bindings.context.retrieve(ContextRequest(subject_id=subject, query=query)) is RESULT
        assert engine.queries == [query]
        assert await bindings.policy.evaluate(PolicyRequest(
            subject_id=subject, action=PolicyAction.READ_CONTEXT, context_ids=(RECORD.id,),
        )) is decision
        assert await bindings.projections.project(ProjectionRequest(contexts=(RECORD,))) is projection
        messages = (Message(role=MessageRole.USER, content="hello"),)
        response = await bindings.chat.respond(ChatRequest(subject_id=subject, messages=messages))
        assert isinstance(response, ChatResponse)
        assert response.message is MESSAGE
        assert provider.requests == [GenerationRequest(messages=messages)]

    asyncio.run(exercise())


def test_domain_values_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        RECORD.content = "changed"  # type: ignore[misc]
    assert RECORD.content == "test content"


def test_incomplete_adapters_do_not_satisfy_runtime_port_shapes() -> None:
    assert not isinstance(object(), ContextEngine)
    assert not isinstance(object(), LLMProvider)
