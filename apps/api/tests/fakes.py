"""Test-only adapters; production composition never installs these fakes."""

from dataclasses import dataclass

from app.chat.models import ChatRequest, ChatResponse
from app.core.models import (
    ContextId, ContextQuery, ContextSearchHit, ContextRequest, ContextResult,
    GenerationRequest, GenerationResult, Message, MessageRole,
    ItemRevisionRef, SourceRevisionRef, RetrievalHitId, SourceId, SourceRevisionId,
    UnderstandingItemId, UnderstandingRevisionId,
    ContextSpace, ContextSpacePage, SubjectId,
)
from app.core.ports import ContextEngine, LLMProvider
from app.policy.models import PolicyDecision, PolicyRequest
from app.projections.models import ContextProjection, ProjectionRequest

SPACE = ContextId("test-space")
ITEM_REVISION = ItemRevisionRef(context_id=SPACE, item_id=UnderstandingItemId("test-item"),
                               revision_id=UnderstandingRevisionId("test-item-revision"))
SOURCE_REVISION = SourceRevisionRef(source_id=SourceId("test-source"),
                                   revision_id=SourceRevisionId("test-source-revision"))
HIT = ContextSearchHit(id=RetrievalHitId("test-hit"), context_id=SPACE,
                       excerpt="test content", provenance=(SOURCE_REVISION,), item_revision=ITEM_REVISION)
RESULT = ContextResult(hits=(HIT,))
MESSAGE = Message(role=MessageRole.ASSISTANT, content="test reply")
GENERATION = GenerationResult(message=MESSAGE)


class FakeContextEngine:
    def __init__(self, result: ContextResult) -> None:
        self.result = result
        self.queries: list[ContextQuery] = []

    async def search(self, query: ContextQuery) -> ContextResult:
        self.queries.append(query)
        return self.result


class AlternateContextEngine:
    """A separate implementation with no shared adapter base class."""

    async def search(self, query: ContextQuery) -> ContextResult:
        return RESULT


class FakeLLMProvider:
    def __init__(self, result: GenerationResult) -> None:
        self.result = result
        self.requests: list[GenerationRequest] = []

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        self.requests.append(request)
        return self.result


class AlternateLLMProvider:
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        return GENERATION


@dataclass
class FakeContextService:
    engine: ContextEngine

    async def browse(self, request: ContextRequest) -> ContextResult:
        raise NotImplementedError('Explicit browse test double required')

    async def create_space(self, *, subject_id: SubjectId, name: str) -> ContextSpace:
        raise NotImplementedError("Retrieval-only test double")

    async def list_spaces(self, *, subject_id: SubjectId, limit: int = 20,
                          after_id: ContextId | None = None) -> ContextSpacePage:
        raise NotImplementedError("Retrieval-only test double")

    async def get_space(self, *, subject_id: SubjectId, context_id: ContextId) -> ContextSpace:
        raise NotImplementedError("Retrieval-only test double")

    async def rename_space(self, *, subject_id: SubjectId, context_id: ContextId,
                           name: str) -> ContextSpace:
        raise NotImplementedError("Retrieval-only test double")

    async def retrieve(self, request: ContextRequest) -> ContextResult:
        # Delegation belongs to this test double, not a production use case.
        return await self.engine.search(request.query)


@dataclass
class FakePolicyService:
    decision: PolicyDecision

    async def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        return self.decision


@dataclass
class FakeProjectionService:
    projection: ContextProjection

    async def project(self, request: ProjectionRequest) -> ContextProjection:
        return self.projection


@dataclass
class FakeChatService:
    provider: LLMProvider

    async def respond(self, request: ChatRequest) -> ChatResponse:
        result = await self.provider.generate(GenerationRequest(messages=request.messages))
        return ChatResponse(message=result.message)
