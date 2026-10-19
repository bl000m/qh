"""Authenticated navigation metadata, without any canonical content mutation."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

from app.api.context_spaces import allowed_query, call
from app.api.security import authenticated_subject
from app.core.models import SubjectId
from app.environment.service import OrganizationConflict

router = APIRouter(prefix='/environment', tags=['environment'])


class Domain(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: UUID
    name: StrictStr = Field(min_length=1, max_length=100)


class Organization(BaseModel):
    model_config = ConfigDict(extra='forbid')
    version: StrictInt = Field(ge=0)
    domains: list[Domain] = Field(max_length=50)
    memberships: dict[str, list[str]] = Field(max_length=1000)


def bound(request, response):
    allowed_query(request, set())
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
async def replace(document: Organization, request: Request, response: Response,
                  subject: SubjectId = Depends(authenticated_subject)):
    service = bound(request, response)
    try:
        return await call(service.replace(subject, document.model_dump(mode='json')))
    except OrganizationConflict:
        raise HTTPException(409, 'Organization changed; reload before editing') from None
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(422, 'Invalid organization') from None
