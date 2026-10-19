"""Authenticated navigation metadata, without any canonical content mutation."""
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

from app.api.context_spaces import allowed_query, call, SpaceName, SpaceView, SpacePage
from app.api.security import authenticated_subject
from app.core.models import SubjectId
from app.environment.service import OrganizationConflict

router = APIRouter(prefix='/environment', tags=['environment'])


class Domain(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: UUID
    name: StrictStr = Field(min_length=1, max_length=100)


class OrganizationInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    version: StrictInt = Field(ge=0)
    domains: list[Domain] = Field(max_length=50)
    memberships: dict[str, list[str]] = Field(max_length=1000)
    primary_domains: dict[str, str] = Field(max_length=1000)


class Opening(BaseModel):
    model_config = ConfigDict(extra='forbid')
    last_opened_at: datetime
    open_count: StrictInt = Field(ge=1)


class Organization(OrganizationInput):
    usage: dict[str, Opening]


class OpenEvent(BaseModel):
    model_config = ConfigDict(extra='forbid')
    event_id: UUID


class OrganizedSpace(SpaceName):
    primary_domain_id: UUID


def bound(request, response, query=frozenset()):
    allowed_query(request, query)
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['Vary'] = 'Authorization'
    services = request.app.state.services
    if services is None or services.environment is None:
        raise HTTPException(503, 'Organization unavailable')
    return services.environment


@router.get('', response_model=Organization)
async def read(request: Request, response: Response, subject: SubjectId = Depends(authenticated_subject)):
    return await call(bound(request, response).read(subject))


@router.put('', response_model=Organization)
async def replace(document: OrganizationInput, request: Request, response: Response,
                  subject: SubjectId = Depends(authenticated_subject)):
    service = bound(request, response)
    try:
        return await call(service.replace(subject, document.model_dump(mode='json')))
    except OrganizationConflict:
        raise HTTPException(409, 'Organization changed; reload before editing') from None
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(422, 'Invalid organization') from None


@router.post('/spaces', response_model=SpaceView, status_code=201)
async def create_space(payload: OrganizedSpace, request: Request, response: Response,
                       subject: SubjectId = Depends(authenticated_subject)):
    service = bound(request,response)
    try:
        result = await call(service.create_space(subject,payload.name,str(payload.primary_domain_id)))
    except OrganizationConflict:
        raise HTTPException(409,'Unknown primary domain; reload organization') from None
    response.headers['Location']='/context-spaces/'+result.id
    return result


@router.post('/spaces/{context_id}/open', response_model=Opening)
async def opened(context_id: UUID, event: OpenEvent, request: Request, response: Response,
                 subject: SubjectId = Depends(authenticated_subject)):
    return await call(bound(request,response).opened(subject,str(context_id),str(event.event_id)))


@router.get('/spaces', response_model=SpacePage)
async def resume(request: Request, response: Response, sort: Literal['recent','used']='recent',
                 domain: str | None=None, limit: Annotated[int, Query(ge=1,le=100)]=20,
                 after_id: UUID | None=None, subject: SubjectId = Depends(authenticated_subject)):
    service=bound(request,response,{'sort','domain','limit','after_id'})
    try:
        return await call(service.resume(subject,sort,domain,limit,str(after_id) if after_id else None))
    except ValueError:
        raise HTTPException(422,'Invalid resume page') from None
