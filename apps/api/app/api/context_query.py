"""Scoped canonical retrieval; no generation, ingestion or confirmation."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, model_validator

from app.api.context_spaces import allowed_query, call, service
from app.api.security import authenticated_subject
from app.core.models import CanonicalRevision, ContextQuery, ContextRequest, SubjectId

router = APIRouter(prefix="/context-spaces", tags=["context-spaces"])
View = Literal['current', 'proposed', 'history']


class RetrievalQuery(BaseModel):
    model_config = ConfigDict(extra='forbid')
    context_ids: list[UUID] = Field(min_length=1, max_length=20)
    view: View
    text: Annotated[StrictStr, Field(max_length=4096)] | None = None
    descriptors: list[Annotated[StrictStr, Field(min_length=1)]] | None = Field(default=None, min_length=1, max_length=100)
    include_tentative: StrictBool = False
    limit: Annotated[StrictInt, Field(ge=1, le=100)] = 20
    after_revision_id: UUID | None = None

    @model_validator(mode='after')
    def explicit_selection(self):
        if (self.text is None) == (self.descriptors is None):
            raise ValueError('Choose exactly one of text or descriptors')
        if self.text is not None and (not self.text.strip() or self.include_tentative):
            raise ValueError('Nonempty text required; tentative inclusion is descriptor-only')
        self.context_ids = list(dict.fromkeys(self.context_ids))
        return self


class RevisionPage(BaseModel):
    view: View
    items: tuple[CanonicalRevision, ...]
    next_after_revision_id: UUID | None


@router.post('/query', response_model=RevisionPage)
async def query_context(payload: RetrievalQuery, request: Request,
                        subject: SubjectId = Depends(authenticated_subject)):
    allowed_query(request, set())
    query = ContextQuery(
        context_ids=tuple(str(id) for id in payload.context_ids), view=payload.view,
        text=payload.text if payload.text is not None else '',
        descriptors=tuple(payload.descriptors or ()), include_tentative=payload.include_tentative,
        limit=payload.limit,
        after_revision_id=str(payload.after_revision_id) if payload.after_revision_id else None,
    )
    result = await call(service(request).retrieve(ContextRequest(subject_id=subject, query=query)))
    return RevisionPage(view=payload.view, items=result.revisions,
                        next_after_revision_id=result.next_after_revision_id)
