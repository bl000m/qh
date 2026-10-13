"""Outbound ports. Adapters translate their SDK types to/from these QH values."""

from typing import Protocol, runtime_checkable

from app.core.models import ContextQuery, ContextResult, GenerationRequest, GenerationResult


@runtime_checkable
class ContextEngine(Protocol):
    """Retrieve context through a replaceable graph/search implementation.

    This port has no authorization, transport, graph-driver or Graphiti types.
    The ContextService boundary owns the future authorized retrieval use case.
    """

    async def search(self, query: ContextQuery) -> ContextResult: ...


@runtime_checkable
class LLMProvider(Protocol):
    """Generate a QH message through a replaceable provider adapter.

    SDK messages, credentials and model-specific configuration remain in the
    implementation. Provider errors must not become domain return values.
    """

    async def generate(self, request: GenerationRequest) -> GenerationResult: ...
