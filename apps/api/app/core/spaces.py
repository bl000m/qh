"""Scoped metadata persistence port; no driver, transport or graph dependencies."""

from typing import Protocol

from app.core.models import ContextId, ContextSpace, SubjectId


class ContextSpaceRepository(Protocol):
    async def create(self, *, subject_id: SubjectId, name: str) -> ContextSpace: ...

    async def list_ids(self, *, subject_id: SubjectId, limit: int,
                       after_id: ContextId | None) -> tuple[ContextId, ...]: ...

    async def read(self, *, subject_id: SubjectId, context_id: ContextId) -> ContextSpace | None: ...

    async def rename(self, *, subject_id: SubjectId, context_id: ContextId,
                     name: str) -> ContextSpace | None: ...
