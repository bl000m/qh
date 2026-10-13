from dataclasses import dataclass

from app.core.models import ContextId, ContextRecord


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectionRequest:
    contexts: tuple[ContextRecord, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextProjection:
    text: str
    context_ids: tuple[ContextId, ...]
