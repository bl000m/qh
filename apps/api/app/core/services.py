from typing import Protocol, runtime_checkable

from app.core.models import ContextRequest, ContextResult


@runtime_checkable
class ContextService(Protocol):
    """Inbound contract for future authorized context retrieval.

    Implementations coordinate the policy boundary and ContextEngine. They must
    return scoped QH search hits rather than infrastructure entities. Defines only the
    contract; it does not implement authorization, retrieval or ingestion.
    """

    async def retrieve(self, request: ContextRequest) -> ContextResult: ...
