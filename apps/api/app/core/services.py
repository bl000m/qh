from typing import Protocol, runtime_checkable

from app.core.models import ContextRequest, ContextResult


@runtime_checkable
class ContextService(Protocol):
    """Inbound contract for future authorized context retrieval.

    Implementations coordinate the policy boundary and ContextEngine. They must
    return QH records rather than infrastructure entities. QH-2 defines only the
    contract; it does not implement authorization, retrieval or ingestion.
    """

    async def retrieve(self, request: ContextRequest) -> ContextResult: ...
