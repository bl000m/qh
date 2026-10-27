"""Authenticated Context Space intake, consolidation, portable export and chat."""
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator, model_validator

from app.api.security import authenticated_subject, authenticated_chat_identity
from app.api.development_ai import execute
from app.api.chat_sessions import chat_request
from app.api.context_spaces import allowed_query


class StrictDocument(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ExportEvidence(StrictDocument):
    source_revision_id: UUID
    quote: Annotated[StrictStr, Field(min_length=1, max_length=100000)]
    turn_id: StrictStr | None = None


class ExportItem(StrictDocument):
    id: UUID
    text: Annotated[StrictStr, Field(min_length=1, max_length=16000)]
    primary_dimension: Literal['situation_information','objectives_intentions','decisions_actions',
        'constraints_preferences','hypotheses_uncertainties','open_questions'] | None
    certainty: Literal['asserted','tentative'] | None
    validation_state: Literal['proposed','confirmed','rejected']
    evidence: list[ExportEvidence] = Field(min_length=1, max_length=100)


class ContextOrigin(StrictDocument):
    schema_version: Literal['qh.context-space/1']
    logical_id: UUID
    name: Annotated[StrictStr, Field(min_length=1, max_length=256)]
    version: Annotated[int, Field(strict=True, ge=1)]
    consolidated_at: Annotated[StrictStr, Field(min_length=1, max_length=64)]
    understanding: list[ExportItem] = Field(min_length=1, max_length=100)

    @field_validator('consolidated_at')
    @classmethod
    def timestamp(cls, value):
        if datetime.fromisoformat(value.replace('Z','+00:00')).tzinfo is None:
            raise ValueError('Timezone required')
        return value


class PortableContext(ContextOrigin):
    ancestry: list[ContextOrigin] = Field(default_factory=list, max_length=100)


class IntakeInput(StrictDocument):
    id: UUID
    kind: Literal['message','document','context']
    role: Literal['user','assistant'] = 'user'
    text: Annotated[StrictStr, Field(min_length=1, max_length=500000)] | None = None
    name: Annotated[StrictStr, Field(min_length=1, max_length=256)] | None = None
    context: PortableContext | None = None

    @model_validator(mode='after')
    def valid_content(self):
        if self.kind=='context':
            if self.context is None or self.text is not None or self.role!='user':
                raise ValueError('Portable context required')
        elif self.text is None or not self.text.strip() or '\0' in self.text or self.context is not None:
            raise ValueError('Original text required')
        if self.kind!='message' and self.role!='user':
            raise ValueError('Owner-submitted document or context required')
        if self.kind=='document' and (not self.name or not self.name.lower().endswith(('.txt','.md','.markdown'))):
            raise ValueError('Only textual TXT and Markdown extraction is supported')
        if len(self.model_dump_json().encode())>500000:
            raise ValueError('Intake exceeds supported byte limit')
        return self


router = APIRouter(prefix='/context-spaces/{context_id}/workspace', tags=['Context Space'])


def service(request, response):
    allowed_query(request, set())
    response.headers['Cache-Control']='private, no-store'
    response.headers['Vary']='Authorization'
    services = request.app.state.services
    if services is None or services.consolidation is None:
        raise HTTPException(503, 'Context Space consolidation unavailable')
    return services.consolidation


@router.get('')
async def read(context_id: UUID, request: Request, response: Response, subject=Depends(authenticated_subject)):
    return await execute(service(request,response).read(subject,str(context_id)))


@router.post('/intake')
async def intake(context_id: UUID, payload: IntakeInput, request: Request, response: Response,
                 subject=Depends(authenticated_subject)):
    return await execute(service(request,response).append(subject,str(context_id),payload.model_dump(mode='json')))


@router.post('/consolidate')
async def consolidate(context_id: UUID, request: Request, response: Response,
                      identity=Depends(authenticated_chat_identity)):
    return await execute(service(request,response).consolidate(identity,str(context_id)))


@router.get('/export', response_model=PortableContext)
async def export(context_id: UUID, request: Request, response: Response, subject=Depends(authenticated_subject)):
    application=service(request,response)
    state=await execute(application.read(subject,str(context_id)))
    if not state['current']:
        raise HTTPException(409,'No consolidated understanding')
    space=await execute(application.context.get_space(subject_id=subject,context_id=str(context_id)))
    items=[]
    for row in state['understanding']:
        content=row['content']
        primary=content.get('primary_dimension') or {}
        items.append(dict(id=row['revision_id'],text=content['text'],
            primary_dimension=primary.get('value'),certainty=primary.get('certainty'),
            validation_state=row['validation_state'],evidence=[dict(source_revision_id=e['source_revision_id'],
                quote=e['quote'],turn_id=e.get('turn_id')) for e in content['citations']]))
    ancestry={}
    for row in state['intake']:
        if row['kind']!='context' or row['id'] not in state['current']['intake_ids']:
            continue
        origin=row['context']
        for entry in [origin,*origin.get('ancestry',[])]:
            ancestry[(entry['logical_id'],entry['version'])]={k:v for k,v in entry.items() if k!='ancestry'}
    return PortableContext(ancestry=list(ancestry.values()),schema_version='qh.context-space/1',logical_id=context_id,name=space.name,
        version=state['current']['version'],consolidated_at=state['current']['created_at'],understanding=items)


class WorkspaceMessageInput(StrictDocument):
    question_id: UUID
    operation_id: UUID


class RegenerationInput(StrictDocument):
    operation_id: UUID


@router.post('/regenerate')
async def regenerate(context_id: UUID, payload: RegenerationInput, request: Request, response: Response,
                     identity=Depends(authenticated_chat_identity)):
    return await execute(service(request,response).consolidate(identity,str(context_id),str(payload.operation_id)))


@router.post('/messages')
async def messages(context_id: UUID, payload: WorkspaceMessageInput, request: Request, response: Response,
                   identity=Depends(authenticated_chat_identity)):
    from app.understanding.consolidation import WorkspaceChatFailed
    async def respond():
        try:
            return await service(request,response).respond(identity,str(context_id),
                chat_request(identity.subject_id,context_id),str(payload.question_id),str(payload.operation_id))
        except WorkspaceChatFailed:
            raise HTTPException(502, 'La réponse n’a pas pu être générée.') from None
    return await execute(respond())
