from dataclasses import dataclass
from typing import Literal

from app.core.models import CanonicalRevision, ContextId, ContextQuery, Message, SubjectId


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatRequest:
    subject_id: SubjectId
    messages: tuple[Message, ...]
    context_query: ContextQuery | None = None
    context_id: ContextId | None = None
    include_proposed: bool = False
    consolidated_revision_ids: tuple[str, ...] | None = None
    extended_dialogue: bool = False  # Trusted development composition, never a client flag.


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatResponse:
    message: Message
    context_ids: tuple[ContextId, ...] = ()
    model: str = "unbound"
    references: tuple[CanonicalRevision, ...] = ()
    provided_revisions: tuple[CanonicalRevision, ...] = ()
    support_basis: Literal['general', 'dialogue', 'canonical', 'mixed', 'insufficient'] = 'insufficient'
    insufficient_context: bool = True  # Completeness warning, independent of support_basis.
    partial_coverage: bool = False
    input_bound: int = 0
    context_bytes: int = 0
    generation_seconds: float | None = None
