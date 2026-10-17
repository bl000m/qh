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


class ContextRetrievalUnavailable(RuntimeError):
    """Retrieval cannot establish canonical, authorized, fresh results."""


@dataclass(frozen=True, slots=True, kw_only=True)
class CanonicalSource:
    source_id: SourceId
    source_revision_id: SourceRevisionId
    revision_no: int
    origin: dict[str, object]


@dataclass(frozen=True, slots=True, kw_only=True)
class RevisionRelation:
    predicate: str
    source_item_id: UnderstandingItemId
    source_revision_id: UnderstandingRevisionId
    target_item_id: UnderstandingItemId
    target_revision_id: UnderstandingRevisionId


@dataclass(frozen=True, slots=True, kw_only=True)
class RevisionTime:
    fact_from: str | None
    fact_to: str | None
    valid_from: str | None
    valid_to: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class CanonicalRevision:
    context_space_id: ContextId
    item_id: UnderstandingItemId
    revision_id: UnderstandingRevisionId
    revision_no: int
    structural_kind: str
    type_id: str
    type_version: int
    content: dict[str, object]
    origin_kind: str
    validation_state: str
    validated_by: SubjectId | None
    validated_at: str | None
    current_revision_id: UnderstandingRevisionId | None
    is_current_confirmed: bool
    based_on_revision_id: UnderstandingRevisionId | None
    created_at: str
    temporal: RevisionTime
    relation: RevisionRelation | None
    provenance: tuple[CanonicalSource, ...]


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
    view: str | None = None
    descriptors: tuple[str, ...] = ()
    include_tentative: bool = False
    after_revision_id: UnderstandingRevisionId | None = None

    def __post_init__(self) -> None:
        if not self.context_ids:
            raise ValueError("ContextQuery requires an explicit nonempty space scope")
        if self.view is not None:
            if self.view not in ("current", "proposed", "history"):
                raise ValueError("Explicit supported revision view required")
            if not 1 <= len(self.context_ids) <= 20 or not 1 <= self.limit <= 101:
                raise ValueError("Bounded scope and limit required")
            if self.text.strip() and self.descriptors:
                raise ValueError("Choose text or descriptors")
            if len(self.text) > 4096 or len(self.descriptors) > 100 or any(
                not isinstance(v, str) or not v for v in self.descriptors
            ):
                raise ValueError("Bounded text or nonempty descriptor values required")
            if self.include_tentative and not self.descriptors:
                raise ValueError("Tentative inclusion requires descriptors")


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextResult:
    hits: tuple[ContextSearchHit, ...]
    revisions: tuple[CanonicalRevision, ...] = ()
    next_after_revision_id: UnderstandingRevisionId | None = None


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
