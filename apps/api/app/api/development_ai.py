"""An explicit Send/Propose is the owner's authorization in development mode."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.chat import ChatInput, ChatOutput, DialogueMessage
from app.api.enrichment import SelectedTurn
from pydantic import Field, StrictStr
from typing import Annotated

from app.api.chat_sessions import chat_request
from app.api.context_spaces import allowed_query, call
from app.api.enrichment import EnrichmentInput, EnrichmentReceipt
from app.api.security import authenticated_chat_identity
from app.chat.context import ChatProviderUnavailable
from app.core.models import ProviderBudgetExceeded
from app.chat.context import ChatContextUnavailable, ChatInputInvalid
from app.understanding.enrichment import EnrichmentConflict, EnrichmentUnavailable

class FullDialogueMessage(DialogueMessage):
    content: Annotated[StrictStr, Field(min_length=1)]

class FullChatInput(ChatInput):
    messages: list[FullDialogueMessage] = Field(min_length=1)

class FullTurn(SelectedTurn):
    content: Annotated[StrictStr, Field(min_length=1)]

class FullEnrichmentInput(EnrichmentInput):
    turns: list[FullTurn] = Field(min_length=1)


router = APIRouter(prefix='/context-spaces/{context_id}/ai', tags=['development AI'])
PLAFOND = 'Plafond IA atteint. Aucune nouvelle requête ne sera facturée.'


def service(request, response):
    allowed_query(request, set())
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['Vary'] = 'Authorization'
    services = request.app.state.services
    if services is None or services.development_ai is None:
        raise HTTPException(503, 'Development AI unavailable')
    return services.development_ai


async def execute(operation):
    from app.understanding.documents import DocumentInvalid
    try:
        return await call(operation)
    except ProviderBudgetExceeded:
        raise HTTPException(402, PLAFOND) from None
    except EnrichmentConflict:
        raise HTTPException(409, 'Conflicting operation; no automatic retry') from None
    except (ChatProviderUnavailable, ChatContextUnavailable, EnrichmentUnavailable):
        raise HTTPException(503, 'AI unavailable; no automatic retry') from None
    except DocumentInvalid as exc:
        raise HTTPException(422,str(exc)) from None
    except (ChatInputInvalid, ValueError):
        raise HTTPException(422, 'Invalid AI input or output') from None
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, 'AI unavailable; no automatic retry') from None


@router.post('/messages', response_model=ChatOutput)
async def messages(context_id: UUID, payload: FullChatInput, request: Request, response: Response,
                   identity=Depends(authenticated_chat_identity)):
    result = await execute(service(request, response).respond(identity,
        chat_request(identity.subject_id, context_id, payload)))
    return ChatOutput(context_id=context_id, answer=result.message.content, model=result.model,
        references=result.references, provided_revisions=result.provided_revisions,
        support_basis=result.support_basis, insufficient_context=result.insufficient_context, partial_coverage=result.partial_coverage,
        input_bound=result.input_bound, context_bytes=result.context_bytes, generation_seconds=result.generation_seconds)


@router.post('/proposals', response_model=EnrichmentReceipt)
async def proposals(context_id: UUID, payload: FullEnrichmentInput, request: Request, response: Response,
                    identity=Depends(authenticated_chat_identity)):
    return await execute(service(request, response).enrich(identity, str(context_id), payload.model_dump(mode='json')))


@router.get('/diagnostics')
async def diagnostics(context_id: UUID, request: Request, response: Response,
                      identity=Depends(authenticated_chat_identity)):
    return await execute(service(request, response).diagnostics(identity,
        chat_request(identity.subject_id, context_id)))


@router.delete('/diagnostics/{diagnostic_id}')
async def delete_diagnostic(context_id: UUID, diagnostic_id: UUID, request: Request, response: Response,
                            identity=Depends(authenticated_chat_identity)):
    return await execute(service(request, response).diagnostics(identity,
        chat_request(identity.subject_id, context_id), delete_id=str(diagnostic_id)))
