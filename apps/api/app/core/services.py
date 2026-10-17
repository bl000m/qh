from typing import Protocol, runtime_checkable

from app.core.models import (ContextId, ContextRequest, ContextResult, ContextSpace,
                             ContextSpacePage, SubjectId)


@runtime_checkable
class ContextService(Protocol):
    """Inbound Space management and separately scoped understanding retrieval.

    Implementations authorize metadata operations through the application policy.
    Retrieval separately coordinates policy/ContextEngine and returns scoped QH
    hits rather than infrastructure entities. QH-9 implements metadata management,
    not understanding retrieval.
    """

    async def retrieve(self, request: ContextRequest) -> ContextResult: ...

    async def create_space(self, *, subject_id: SubjectId, name: str) -> ContextSpace: ...

    async def list_spaces(self, *, subject_id: SubjectId, limit: int = 20,
                          after_id: ContextId | None = None) -> ContextSpacePage: ...

    async def get_space(self, *, subject_id: SubjectId, context_id: ContextId) -> ContextSpace: ...

    async def rename_space(self, *, subject_id: SubjectId, context_id: ContextId,
                           name: str) -> ContextSpace: ...
