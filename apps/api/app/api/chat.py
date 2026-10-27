"""One authorized Space per chat request; no conversation or canonical writes."""
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr

from app.api.context_spaces import allowed_query, call
from app.api.security import authenticated_subject
from app.chat.context import ChatInputInvalid, ChatContextUnavailable, ChatProviderUnavailable
from app.chat.models import ChatRequest
from app.core.models import CanonicalRevision, Message, MessageRole, SubjectId

router = APIRouter(prefix='/context-spaces', tags=['chat'])


class DialogueMessage(BaseModel):
    model_config = ConfigDict(extra='forbid')
    role: Literal['user', 'assistant']
    content: Annotated[StrictStr, Field(min_length=1, max_length=4096)]


class ChatInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    messages: list[DialogueMessage] = Field(min_length=1, max_length=7)
    include_proposed: StrictBool = False


class ChatOutput(BaseModel):
    context_id: UUID
    answer: str
    model: str
    references: tuple[CanonicalRevision, ...]
    provided_revisions: tuple[CanonicalRevision, ...]
    support_basis: Literal['general', 'dialogue', 'canonical', 'mixed', 'insufficient']
    insufficient_context: bool
    partial_coverage: bool
    input_bound: int
    context_bytes: int
    generation_seconds: float | None


@router.post('/{context_id}/chat', response_model=ChatOutput)
async def chat(context_id: UUID, payload: ChatInput, request: Request, response: Response,
               subject: SubjectId = Depends(authenticated_subject)):
    allowed_query(request, set())
    bindings = request.app.state.services
    if bindings is None or bindings.chat is None or not request.app.state.offline_chat:
        raise HTTPException(503, 'Chat unavailable')
    try:
        result = await call(bindings.chat.respond(ChatRequest(subject_id=subject,
            context_id=str(context_id), include_proposed=payload.include_proposed,
            messages=tuple(Message(role=MessageRole(m.role), content=m.content) for m in payload.messages))))
    except ChatInputInvalid:
        raise HTTPException(422, 'Invalid dialogue or input budget exceeded') from None
    except (ChatContextUnavailable, ChatProviderUnavailable):
        raise HTTPException(503, 'Chat unavailable; no automatic retry') from None
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['Vary'] = 'Authorization'
    return ChatOutput(context_id=context_id, answer=result.message.content, model=result.model,
        references=result.references, provided_revisions=result.provided_revisions,
        support_basis=result.support_basis, insufficient_context=result.insufficient_context, partial_coverage=result.partial_coverage,
        input_bound=result.input_bound, context_bytes=result.context_bytes,
        generation_seconds=result.generation_seconds)
