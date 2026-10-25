"""Scoped QH-45 disclosure ingress; never accepts an owner, key, model or price."""
from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr

from app.api.chat import ChatInput, ChatOutput
from app.api.context_spaces import allowed_query, call
from app.api.security import authenticated_subject, authenticated_chat_identity
from app.chat.context import ChatInputInvalid, ChatContextUnavailable, ChatProviderUnavailable
from app.chat.models import ChatRequest
from app.chat.sessions import SessionClosed
from app.core.models import CanonicalRevision, Message, MessageRole

router = APIRouter(prefix='/context-spaces', tags=['chat sessions'])


class CapabilityOutput(BaseModel):
    automatic: bool = False
    plafond_reached: bool = False
    enabled: bool
    model: Literal['mistral-small-2603'] | None
    max_seconds: Literal[300, 1800]
    max_calls: int = Field(ge=1, le=100)
    max_usd: str
    provider_expires_at: float | None
    remaining_calls: int = Field(ge=0, le=100)
    remaining_usd: str


class AccountingOutput(BaseModel):
    calls: int = Field(ge=0, le=8)
    committed_usd: str
    blocked: bool


class SessionOutput(BaseModel):
    session_id: UUID
    context_id: UUID
    model: Literal['mistral-small-2603']
    state: Literal['preview', 'active', 'closed', 'revoked']
    expires_at: float = Field(gt=0)
    include_proposed: bool
    snapshot_sha256: str
    max_calls: int = Field(ge=1, le=8)
    max_usd: str
    accounting: AccountingOutput
    provided_revisions: tuple[CanonicalRevision, ...]
    provider_messages: tuple[Message, ...]
    partial_coverage: bool
    input_bound: int = Field(ge=0, le=12000)
    context_bytes: int = Field(ge=0, le=8000)


class RevokedOutput(BaseModel):
    session_id: UUID
    state: Literal['revoked']


class ConsentInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    snapshot_sha256: StrictStr
    disclosure_consent: StrictBool


def service(request, response):
    allowed_query(request, set())
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['Vary'] = 'Authorization'
    bindings = request.app.state.services
    if bindings is None or bindings.chat_sessions is None:
        raise HTTPException(503, 'Provider sessions unavailable')
    return bindings.chat_sessions


def chat_request(subject, scope, payload=None):
    return ChatRequest(subject_id=subject, context_id=str(scope),
        include_proposed=payload.include_proposed if payload else False,
        messages=tuple(Message(role=MessageRole(m.role), content=m.content) for m in payload.messages) if payload else ())


async def execute(operation):
    try:
        return await call(operation)
    except ChatInputInvalid:
        raise HTTPException(422, 'Invalid session input or eligible context unavailable') from None
    except SessionClosed:
        raise HTTPException(409, 'Provider session closed or unavailable; new consent required') from None
    except (ChatContextUnavailable, ChatProviderUnavailable):
        raise HTTPException(503, 'Provider session stopped; no automatic retry') from None
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, 'Provider sessions unavailable') from None


@router.get('/{context_id}/chat-sessions', response_model=CapabilityOutput)
async def capabilities(context_id: UUID, request: Request, response: Response,
                       subject=Depends(authenticated_subject)):
    legacy = service(request, response)
    automatic = request.app.state.services.development_ai
    if automatic is not None:
        from app.api.security import bearer
        identity = await authenticated_chat_identity(request, await bearer(request))
        return await execute(automatic.capabilities(identity, chat_request(subject, context_id)))
    return await execute(legacy.capabilities(chat_request(subject, context_id)))


@router.post('/{context_id}/chat-sessions/preview', response_model=SessionOutput)
async def preview(context_id: UUID, payload: ChatInput, request: Request, response: Response,
                  identity=Depends(authenticated_chat_identity)):
    return await execute(service(request, response).preview(identity, chat_request(identity.subject_id, context_id, payload)))


@router.post('/{context_id}/chat-sessions/{session_id}/consent', response_model=SessionOutput)
async def consent(context_id: UUID, session_id: UUID, payload: ConsentInput,
                  request: Request, response: Response, identity=Depends(authenticated_chat_identity)):
    return await execute(service(request, response).consent(identity, chat_request(identity.subject_id, context_id),
        str(session_id), snapshot_sha256=payload.snapshot_sha256, consent=payload.disclosure_consent))


@router.get('/{context_id}/chat-sessions/{session_id}', response_model=SessionOutput)
async def status(context_id: UUID, session_id: UUID, request: Request, response: Response,
                 identity=Depends(authenticated_chat_identity)):
    return await execute(service(request, response).status(identity, chat_request(identity.subject_id, context_id), str(session_id)))


@router.delete('/{context_id}/chat-sessions/{session_id}', response_model=RevokedOutput)
async def revoke(context_id: UUID, session_id: UUID, request: Request, response: Response,
                 identity=Depends(authenticated_chat_identity)):
    return await execute(service(request, response).revoke(identity, chat_request(identity.subject_id, context_id), str(session_id)))


@router.post('/{context_id}/chat-sessions/{session_id}/messages', response_model=ChatOutput)
async def generate(context_id: UUID, session_id: UUID, payload: ChatInput,
                   request: Request, response: Response, identity=Depends(authenticated_chat_identity)):
    result = await execute(service(request, response).respond(identity,
        chat_request(identity.subject_id, context_id, payload), str(session_id)))
    return ChatOutput(context_id=context_id, answer=result.message.content, model=result.model,
        references=result.references, provided_revisions=result.provided_revisions,
        support_basis=result.support_basis, insufficient_context=result.insufficient_context, partial_coverage=result.partial_coverage,
        input_bound=result.input_bound, context_bytes=result.context_bytes,
        generation_seconds=result.generation_seconds)
