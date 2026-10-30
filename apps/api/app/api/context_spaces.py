"""QH-9 wire contract: authenticated owner metadata, never understanding retrieval."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

from adapters.oidc import IdentityUnavailable
from app.api.security import authenticated_subject
from app.context.service import validate_name
from app.core.models import (ContextId, ContextSpaceNotFound, ContextStorageUnavailable,
                             ContextRetrievalUnavailable, SubjectId)

router = APIRouter(prefix="/context-spaces", tags=["context-spaces"])


class SpaceName(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: StrictStr = Field(min_length=1, max_length=256)

    @field_validator("name")
    @classmethod
    def valid_name(cls, value):
        return validate_name(value)


class SpaceView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    owner_id: UUID
    name: str
    status: str
    created_at: datetime
    updated_at: datetime


class SpacePage(BaseModel):
    items: list[SpaceView]
    next_after_id: UUID | None


def service(request: Request):
    bindings = request.app.state.services
    if bindings is None:
        raise HTTPException(503, "Context service unavailable")
    return bindings.context


def allowed_query(request, allowed):
    if set(request.query_params) - allowed or any(
        len(request.query_params.getlist(key)) != 1 for key in request.query_params
    ):
        raise HTTPException(422, "Unsupported query parameters")


async def call(operation):
    try:
        return await operation
    except ContextSpaceNotFound:
        raise HTTPException(404, "Context space not found") from None
    except PermissionError:
        raise HTTPException(403, "Access denied") from None
    except (ContextStorageUnavailable, ContextRetrievalUnavailable, IdentityUnavailable):
        raise HTTPException(503, "Context service unavailable") from None


@router.post("", status_code=201, response_model=SpaceView)
async def create_space(payload: SpaceName, request: Request, response: Response,
                       subject: SubjectId = Depends(authenticated_subject)):
    allowed_query(request, set())
    result = await call(service(request).create_space(subject_id=subject, name=payload.name))
    response.headers["Location"] = "/context-spaces/" + result.id
    return result


@router.get("", response_model=SpacePage)
async def list_spaces(request: Request,
                      limit: Annotated[int, Query(ge=1, le=100)] = 20,
                      after_id: UUID | None = None,
                      subject: SubjectId = Depends(authenticated_subject)):
    allowed_query(request, {"limit", "after_id"})
    return await call(service(request).list_spaces(
        subject_id=subject, limit=limit,
        after_id=ContextId(str(after_id)) if after_id is not None else None,
    ))


@router.get("/{context_id}", response_model=SpaceView)
async def get_space(context_id: UUID, request: Request,
                    subject: SubjectId = Depends(authenticated_subject)):
    allowed_query(request, set())
    return await call(service(request).get_space(subject_id=subject, context_id=ContextId(str(context_id))))


@router.patch("/{context_id}", response_model=SpaceView)
async def rename_space(context_id: UUID, payload: SpaceName, request: Request,
                       subject: SubjectId = Depends(authenticated_subject)):
    allowed_query(request, set())
    return await call(service(request).rename_space(
        subject_id=subject, context_id=ContextId(str(context_id)), name=payload.name,
    ))


@router.delete('/{context_id}',status_code=204)
async def delete_space(context_id:UUID,payload:SpaceName,request:Request,
                       subject:SubjectId=Depends(authenticated_subject)):
    from app.core.spaces import SpaceConfirmationMismatch
    allowed_query(request,set())
    deletion=request.app.state.services.space_deletion if request.app.state.services else None
    if deletion is None:
        raise HTTPException(503,'Space deletion activation required')
    try:
        await call(deletion.delete(subject,str(context_id),payload.name))
    except SpaceConfirmationMismatch:
        raise HTTPException(409,'Exact Space name confirmation required') from None
    return Response(status_code=204,headers={'Cache-Control':'private, no-store'})
