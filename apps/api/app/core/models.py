"""Immutable, provider-neutral values exchanged across QH boundaries.

These types define data shape only. Validation, authorization, persistence and
conversation behavior are deliberately deferred to later tickets.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import NewType

ContextId = NewType("ContextId", str)
SubjectId = NewType("SubjectId", str)
UnderstandingItemId = NewType("UnderstandingItemId", str)
UnderstandingRevisionId = NewType("UnderstandingRevisionId", str)
SourceId = NewType("SourceId", str)
SourceRevisionId = NewType("SourceRevisionId", str)
RetrievalHitId = NewType("RetrievalHitId", str)


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextSpace:
    id: ContextId
    owner_id: SubjectId
    name: str
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextSpacePage:
    items: tuple[ContextSpace, ...]
    next_after_id: ContextId | None = None


class ContextStorageUnavailable(RuntimeError):
    """Sanitized persistence failure, without driver/credential details."""


class ContextSpaceNotFound(LookupError):
    """Uniform missing or inaccessible Space result."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ItemRevisionRef:
    context_id: ContextId
    item_id: UnderstandingItemId
    revision_id: UnderstandingRevisionId


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceRevisionRef:
    source_id: SourceId
    revision_id: SourceRevisionId


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextSearchHit:
    """A retrieval result, not a Context Space or canonical understanding row."""

    id: RetrievalHitId
    context_id: ContextId
    excerpt: str
    provenance: tuple[SourceRevisionRef, ...]
    item_revision: ItemRevisionRef | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextQuery:
    text: str
    context_ids: tuple[ContextId, ...]
    limit: int = 20

    def __post_init__(self) -> None:
        if not self.context_ids:
            raise ValueError("ContextQuery requires an explicit nonempty space scope")


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextResult:
    hits: tuple[ContextSearchHit, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextRequest:
    subject_id: SubjectId
    query: ContextQuery


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True, slots=True, kw_only=True)
class Message:
    role: MessageRole
    content: str


@dataclass(frozen=True, slots=True, kw_only=True)
class GenerationRequest:
    messages: tuple[Message, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class GenerationResult:
    message: Message
