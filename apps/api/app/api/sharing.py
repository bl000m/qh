"""Owner policy/preview/approval HTTP facade, explicitly bound with guest transport."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter,Depends,Request
from pydantic import BaseModel,ConfigDict,Field,StrictBool,StrictStr

from app.api.guest import GuestRoute,bound,proof
from app.api.security import authenticated_subject, authenticated_chat_identity
from app.projections.disclosure import AccessPolicy,LIVE_PROVIDER
from app.projections.guest import GuestUnavailable
from app.projections.drafts import RevisionKey, ProjectionConflict
from app.chat.snapshot_answer import public_answer

router=APIRouter(route_class=GuestRoute,tags=['governed sharing'])


class ExclusionInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    item_id:UUID
    revision_id:UUID


class PolicyInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    recipient_email:StrictStr=Field(min_length=3,max_length=254)
    purpose:StrictStr=Field(min_length=1,max_length=1024)
    expires_at:datetime
    allow_update_proposals:StrictBool=False
    excluded:list[ExclusionInput]=Field(default_factory=list,max_length=100)


class ApprovalInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    fingerprint:StrictStr=Field(pattern='^[a-f0-9]{64}$')
    exceptions:list[Literal['unassessed_free_text']]=Field(default_factory=list,max_length=1)


class QuestionInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    question:StrictStr=Field(min_length=1,max_length=2000)


class GuestQuestionInput(QuestionInput):
    history:list[dict[str,StrictStr]]=Field(default_factory=list,max_length=12)


def owner_service(request):
    service=request.app.state.services.sharing
    if service is None:raise GuestUnavailable('Sharing unavailable')
    return service


def preview_view(preview):
    return dict(id=preview.id,fingerprint=preview.fingerprint,policy=preview.policy.wire(),
        payload=preview.payload,report=preview.report)


@router.post('/context-spaces/{scope}/sharing/previews',status_code=201)
async def prepare(scope:UUID,document:PolicyInput,request:Request,subject=Depends(authenticated_subject)):
    await owner_service(request).drafts._allow(subject,str(scope))
    chat=request.app.state.services.guest_chat
    if chat is None:raise GuestUnavailable('Sharing unavailable')
    provider=LIVE_PROVIDER if chat.live is not None else 'offline'
    if chat.live is not None and not chat.live.allowed(subject,str(scope)):
        raise GuestUnavailable('Sharing unavailable')
    policy=AccessPolicy(recipient_email=document.recipient_email,purpose=document.purpose,
        expires_at=document.expires_at,rights=('READ','ASK_AI'),provider=provider,
        allow_update_proposals=document.allow_update_proposals,
        include_proposed=True,include_quotes=False,
        excluded=tuple(RevisionKey(item_id=str(k.item_id),revision_id=str(k.revision_id)) for k in document.excluded))
    return preview_view(await owner_service(request).prepare(subject,str(scope),policy))


@router.post('/context-spaces/{scope}/sharing/previews/{preview_id}/approve')
async def approve(scope:UUID,preview_id:UUID,document:ApprovalInput,request:Request,subject=Depends(authenticated_subject)):
    snapshot=await owner_service(request).approve(subject,str(scope),str(preview_id),document.fingerprint,
        exceptions=tuple(document.exceptions))
    return dict(snapshot_id=snapshot.id,expires_at=snapshot.policy.expires_at)


@router.post('/context-spaces/{scope}/sharing/previews/{preview_id}/ask')
async def preview_question(scope:UUID,preview_id:UUID,document:QuestionInput,request:Request,
                           identity=Depends(authenticated_chat_identity)):
    sharing=owner_service(request)
    chat=request.app.state.services.guest_chat
    if chat is None:raise GuestUnavailable('Sharing unavailable')
    preview=await sharing.preview(identity.subject_id,str(scope),str(preview_id))
    async def recheck():
        current=await sharing.preview(identity.subject_id,str(scope),str(preview_id))
        sharing._fresh(current.policy,current.created_at)
        if current.fingerprint!=preview.fingerprint or (await sharing.repository.select(identity.subject_id,str(scope))).stamp!=current.selection_stamp:
            raise ProjectionConflict('Context changed; verify sharing again')
        if current.policy.provider==LIVE_PROVIDER:
            ai=request.app.state.services.development_ai
            if ai is None:raise GuestUnavailable('Verified owner AI unavailable')
            await ai.authorize_consolidation(identity,str(scope))
        return current.payload
    if preview.policy.provider==LIVE_PROVIDER:
        value=await request.app.state.services.development_ai.answer_projection(identity,str(scope),preview.payload,document.question,recheck)
    else:
        value=await chat.answer_payload(identity.subject_id,str(scope),preview.policy.provider,
            preview.payload,document.question,recheck)
    return public_answer(value)


@router.post('/guest/ask')
async def ask(document:GuestQuestionInput,request:Request):
    service=request.app.state.services.guest_chat
    if service is None:raise GuestUnavailable('Snapshot answer unavailable')
    token=proof(request)
    grant=await bound(request).session(token)
    return public_answer(await service.ask(token,grant.snapshot_id,document.question,history=document.history))


@router.get('/context-spaces/{scope}/sharing/providers')
async def providers(scope:UUID,request:Request,subject=Depends(authenticated_subject)):
    await owner_service(request).drafts._allow(subject,str(scope))
    service=request.app.state.services.guest_chat
    if service is None:raise GuestUnavailable('Provider unavailable')
    return await service.providers(subject,str(scope))


@router.get('/guest/provider')
async def guest_provider(request:Request):
    service=request.app.state.services.guest_chat
    if service is None:raise GuestUnavailable('Provider unavailable')
    status=await service.status(proof(request))
    return {k:status[k] for k in ('enabled','simulated')}
