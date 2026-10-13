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
    ContextId, ContextQuery, ContextRequest, ContextResult, ContextSearchHit,
    ItemRevisionRef, SourceRevisionRef, RetrievalHitId, UnderstandingItemId,
    UnderstandingRevisionId, SourceId, SourceRevisionId,
    GenerationRequest, GenerationResult, Message, MessageRole, SubjectId,
)
from app.core.ports import ContextEngine, LLMProvider
from app.core.services import ContextService
from app.policy.models import PolicyAction, PolicyDecision, PolicyRequest
from app.policy.services import PolicyService
from app.projections.models import ContextProjection, ProjectionRequest
from app.projections.services import ProjectionService
from tests.fakes import (
    GENERATION, MESSAGE, HIT, RESULT, SPACE, ITEM_REVISION, SOURCE_REVISION,
    AlternateContextEngine, AlternateLLMProvider,
    FakeChatService, FakeContextEngine, FakeContextService,
    FakeLLMProvider, FakePolicyService, FakeProjectionService,
)

@pytest.mark.parametrize("engine", [FakeContextEngine(RESULT), AlternateContextEngine()])
def test_context_engine_is_replaceable(engine: ContextEngine) -> None:
    query = ContextQuery(text="test", context_ids=(SPACE,))
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
        projection = ContextProjection(text="test projection", item_revisions=(ITEM_REVISION,),
                                       source_revisions=(SOURCE_REVISION,))
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
        query = ContextQuery(text="test", context_ids=(SPACE,))
        assert await bindings.context.retrieve(ContextRequest(subject_id=subject, query=query)) is RESULT
        assert engine.queries == [query]
        assert await bindings.policy.evaluate(PolicyRequest(
            subject_id=subject, action=PolicyAction.READ_CONTEXT, context_ids=(SPACE,),
        )) is decision
        assert await bindings.projections.project(ProjectionRequest(hits=(HIT,))) is projection
        messages = (Message(role=MessageRole.USER, content="hello"),)
        response = await bindings.chat.respond(ChatRequest(subject_id=subject, messages=messages))
        assert isinstance(response, ChatResponse)
        assert response.message is MESSAGE
        assert provider.requests == [GenerationRequest(messages=messages)]

    asyncio.run(exercise())


def test_domain_values_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        HIT.excerpt = "changed"  # type: ignore[misc]
    assert HIT.excerpt == "test content"


def test_identity_roles_and_revision_provenance_are_distinct() -> None:
    assert get_type_hints(ContextSearchHit)["id"] is RetrievalHitId
    assert get_type_hints(ContextSearchHit)["context_id"] is ContextId
    assert get_type_hints(ItemRevisionRef)["item_id"] is UnderstandingItemId
    assert get_type_hints(ItemRevisionRef)["revision_id"] is UnderstandingRevisionId
    assert get_type_hints(SourceRevisionRef)["source_id"] is SourceId
    assert get_type_hints(SourceRevisionRef)["revision_id"] is SourceRevisionId
    assert HIT.item_revision == ITEM_REVISION and HIT.context_id == SPACE
    assert HIT.provenance == (SOURCE_REVISION,)
    projection = ContextProjection(text=HIT.excerpt, item_revisions=(ITEM_REVISION,),
                                   source_revisions=HIT.provenance)
    assert projection.item_revisions[0].revision_id == ITEM_REVISION.revision_id
    assert projection.source_revisions[0].revision_id == SOURCE_REVISION.revision_id


def test_queries_cannot_implicitly_search_all_spaces() -> None:
    with pytest.raises(TypeError):
        ContextQuery(text="unscoped")  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="space scope"):
        ContextQuery(text="empty scope", context_ids=())


def test_source_backed_hit_does_not_require_a_persisted_understanding_item() -> None:
    hit = ContextSearchHit(id=RetrievalHitId("source-hit"), context_id=SPACE,
                           excerpt="original source", provenance=(SOURCE_REVISION,))
    assert hit.item_revision is None
    assert hit.provenance[0].revision_id == SOURCE_REVISION.revision_id


def test_incomplete_adapters_do_not_satisfy_runtime_port_shapes() -> None:
    assert not isinstance(object(), ContextEngine)
    assert not isinstance(object(), LLMProvider)
