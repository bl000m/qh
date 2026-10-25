"""Owner policy/preview/approval HTTP facade, explicitly bound with guest transport."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter,Depends,Request
from pydantic import BaseModel,ConfigDict,Field,StrictBool,StrictStr

from app.api.guest import GuestRoute,bound,proof
from app.api.security import authenticated_subject
from app.projections.disclosure import AccessPolicy
from app.projections.guest import GuestUnavailable

router=APIRouter(route_class=GuestRoute,tags=['governed sharing'])


class PolicyInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    recipient_email:StrictStr=Field(min_length=3,max_length=254)
    purpose:StrictStr=Field(min_length=1,max_length=1024)
    rights:list[Literal['READ','ASK_AI']]=Field(min_length=1,max_length=2)
    expires_at:datetime
    include_proposed:StrictBool=False
    include_quotes:StrictBool=False
    provider:Literal['offline']|None=None


class ApprovalInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    fingerprint:StrictStr=Field(pattern='^[a-f0-9]{64}$')
    exceptions:list[Literal['unassessed_free_text']]=Field(default_factory=list,max_length=1)


class QuestionInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    question:StrictStr=Field(min_length=1,max_length=2000)


def owner_service(request):
    service=request.app.state.services.sharing
    if service is None:raise GuestUnavailable('Sharing unavailable')
    return service


def preview_view(preview):
    return dict(id=preview.id,fingerprint=preview.fingerprint,policy=preview.policy.wire(),
        payload=preview.payload,report=preview.report)


@router.post('/context-spaces/{scope}/sharing/previews',status_code=201)
async def prepare(scope:UUID,document:PolicyInput,request:Request,subject=Depends(authenticated_subject)):
    policy=AccessPolicy(**{**document.model_dump(),'rights':tuple(document.rights)})
    return preview_view(await owner_service(request).prepare(subject,str(scope),policy))


@router.post('/context-spaces/{scope}/sharing/previews/{preview_id}/approve')
async def approve(scope:UUID,preview_id:UUID,document:ApprovalInput,request:Request,subject=Depends(authenticated_subject)):
    snapshot=await owner_service(request).approve(subject,str(scope),str(preview_id),document.fingerprint,
        exceptions=tuple(document.exceptions))
    return dict(snapshot_id=snapshot.id,expires_at=snapshot.policy.expires_at)


@router.post('/guest/snapshots/{snapshot_id}/ask')
async def ask(snapshot_id:UUID,document:QuestionInput,request:Request):
    service=request.app.state.services.guest_chat
    if service is None:raise GuestUnavailable('Snapshot answer unavailable')
    return await service.ask(proof(request),str(snapshot_id),document.question)
