from dataclasses import dataclass

from app.core.models import ContextId, ContextQuery, Message, SubjectId


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatRequest:
    subject_id: SubjectId
    messages: tuple[Message, ...]
    context_query: ContextQuery | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatResponse:
    message: Message
    context_ids: tuple[ContextId, ...] = ()
