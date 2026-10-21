"""Explicit immutable owner review. No model-confirmation or canonical bulk write."""
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StrictStr, StrictInt

from app.api.context_spaces import allowed_query, call
from app.api.security import authenticated_subject
from app.api.context_query import RevisionPage
from app.core.models import SubjectId
from app.review.service import ReviewConflict

router = APIRouter(prefix='/context-spaces/{context_id}', tags=['review'])


class AssignmentDecision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    index: Annotated[StrictInt, Field(ge=0, le=99)]
    state: Literal['accepted', 'rejected']
    reuse_value: StrictStr | None = Field(default=None, min_length=1, max_length=256)


class ReviewOperation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    operation_id: UUID
    action: Literal['confirm', 'reject', 'correct', 'review_assignments']
    expected_latest_revision_id: UUID
    expected_current_revision_id: UUID | None
    text: StrictStr | None = Field(default=None, min_length=1, max_length=16000)
    assignment_decisions: list[AssignmentDecision] | None = Field(default=None, min_length=1, max_length=100)


class ReviewStatus(BaseModel):
    revision_id: UUID
    latest_revision_id: UUID
    current_revision_id: UUID | None
    pending: bool
    successor_revision_id: UUID | None


class ReviewReceipt(BaseModel):
    revision_id: UUID
    action: Literal['confirm','reject','correct','review_assignments']
    replayed: bool


def bound(request, response, query=frozenset()):
    allowed_query(request, query)
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['Vary'] = 'Authorization'
    services = request.app.state.services
    if services is None or services.review is None:
        raise HTTPException(503, 'Review unavailable')
    return services.review


@router.get('/review', response_model=RevisionPage)
async def inbox(context_id: UUID, request: Request, response: Response,
                limit: Annotated[int, Query(ge=1, le=50)] = 20, after_revision_id: UUID | None = None,
                subject: SubjectId = Depends(authenticated_subject)):
    service = bound(request, response, {'limit','after_revision_id'})
    page = await call(service.pending(subject, str(context_id), limit, str(after_revision_id) if after_revision_id else None))
    return dict(page, view='proposed')


@router.get('/understanding/{revision_id}/review', response_model=ReviewStatus)
async def status(context_id: UUID, revision_id: UUID, request: Request, response: Response,
                 subject: SubjectId = Depends(authenticated_subject)):
    return await call(bound(request, response).status(subject, str(context_id), str(revision_id)))


@router.post('/understanding/{revision_id}/review', response_model=ReviewReceipt)
async def review(context_id: UUID, revision_id: UUID, operation: ReviewOperation,
                 request: Request, response: Response, subject: SubjectId = Depends(authenticated_subject)):
    service = bound(request, response)
    try:
        return await call(service.apply(subject, str(context_id), str(revision_id), operation.model_dump(mode='json', exclude_none=True) | {'text': operation.text, 'expected_current_revision_id': str(operation.expected_current_revision_id) if operation.expected_current_revision_id else None}))
    except ReviewConflict:
        raise HTTPException(409, 'Review conflict or profile constraint; reload before acting') from None
    except ValueError:
        raise HTTPException(422, 'Invalid review operation') from None
