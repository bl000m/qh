from dataclasses import dataclass

from app.core.models import ContextSearchHit, ItemRevisionRef, SourceRevisionRef


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectionRequest:
    hits: tuple[ContextSearchHit, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextProjection:
    """Formatting contract; not an immutable approved/persisted snapshot."""

    text: str
    item_revisions: tuple[ItemRevisionRef, ...]
    source_revisions: tuple[SourceRevisionRef, ...]
