"""Owner-explicit chat persistence, independent of answering or confirmation."""
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr

from app.api.context_spaces import allowed_query, call
from app.api.security import authenticated_subject
from app.core.models import SubjectId
from app.understanding.enrichment import EnrichmentConflict, EnrichmentUnavailable

router = APIRouter(prefix='/context-spaces/{context_id}', tags=['understanding'])


class SelectedTurn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: UUID
    role: Literal['user', 'assistant']
    content: Annotated[StrictStr, Field(min_length=1, max_length=4096)]
    captured_at: Annotated[StrictStr, Field(min_length=1, max_length=64)]


class EnrichmentInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    conversation_id: UUID
    operation_id: UUID
    turns: list[SelectedTurn] = Field(min_length=1, max_length=8)
    persist_consent: StrictBool


class EnrichmentReceipt(BaseModel):
    context_id: UUID
    source_revision_id: UUID
    revision_ids: list[UUID]
    replayed: bool
    provider_mode: Literal['offline-literal/1']


@router.post('/enrichments', response_model=EnrichmentReceipt)
async def enrich(context_id: UUID, payload: EnrichmentInput, request: Request,
                 response: Response, subject: SubjectId = Depends(authenticated_subject)):
    allowed_query(request, set())
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['Vary'] = 'Authorization'
    services = request.app.state.services
    if services is None or services.enrichment is None:
        raise HTTPException(503, 'Enrichment unavailable')
    try:
        return await call(services.enrichment.enrich(subject, str(context_id), payload.model_dump(mode='json')))
    except EnrichmentConflict:
        raise HTTPException(409, 'Conflicting submission; no automatic retry') from None
    except EnrichmentUnavailable:
        raise HTTPException(503, 'Extraction unavailable; no automatic retry') from None
    except ValueError:
        raise HTTPException(422, 'Invalid segment or extraction; nothing published') from None
