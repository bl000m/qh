"""Test-only adapters; production composition never installs these fakes."""

from dataclasses import dataclass

from app.chat.models import ChatRequest, ChatResponse
from app.core.models import (
    ContextId, ContextQuery, ContextRecord, ContextRequest, ContextResult,
    GenerationRequest, GenerationResult, Message, MessageRole,
)
from app.core.ports import ContextEngine, LLMProvider
from app.policy.models import PolicyDecision, PolicyRequest
from app.projections.models import ContextProjection, ProjectionRequest

RECORD = ContextRecord(id=ContextId("test-context"), content="test content")
RESULT = ContextResult(contexts=(RECORD,))
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
