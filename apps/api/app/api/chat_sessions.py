"""Scoped QH-45 disclosure ingress; never accepts an owner, key, model or price."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, StrictBool, StrictStr

from app.api.chat import ChatInput, ChatOutput
from app.api.context_spaces import allowed_query, call
from app.api.security import authenticated_subject, authenticated_chat_identity
from app.chat.context import ChatInputInvalid, ChatContextUnavailable, ChatProviderUnavailable
from app.chat.models import ChatRequest
from app.chat.sessions import SessionClosed
from app.core.models import Message, MessageRole

router = APIRouter(prefix='/context-spaces', tags=['chat sessions'])


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


@router.get('/{context_id}/chat-sessions')
async def capabilities(context_id: UUID, request: Request, response: Response,
                       subject=Depends(authenticated_subject)):
    return await execute(service(request, response).capabilities(chat_request(subject, context_id)))


@router.post('/{context_id}/chat-sessions/preview')
async def preview(context_id: UUID, payload: ChatInput, request: Request, response: Response,
                  identity=Depends(authenticated_chat_identity)):
    return await execute(service(request, response).preview(identity, chat_request(identity.subject_id, context_id, payload)))


@router.post('/{context_id}/chat-sessions/{session_id}/consent')
async def consent(context_id: UUID, session_id: UUID, payload: ConsentInput,
                  request: Request, response: Response, identity=Depends(authenticated_chat_identity)):
    return await execute(service(request, response).consent(identity, chat_request(identity.subject_id, context_id),
        str(session_id), snapshot_sha256=payload.snapshot_sha256, consent=payload.disclosure_consent))


@router.get('/{context_id}/chat-sessions/{session_id}')
async def status(context_id: UUID, session_id: UUID, request: Request, response: Response,
                 identity=Depends(authenticated_chat_identity)):
    return await execute(service(request, response).status(identity, chat_request(identity.subject_id, context_id), str(session_id)))


@router.delete('/{context_id}/chat-sessions/{session_id}')
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
        insufficient_context=result.insufficient_context, partial_coverage=result.partial_coverage,
        input_bound=result.input_bound, context_bytes=result.context_bytes,
        generation_seconds=result.generation_seconds)
