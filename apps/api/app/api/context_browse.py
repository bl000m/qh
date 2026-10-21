"""QH-12 canonical browse. QH-10 selector requirements remain unchanged."""
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from app.api.context_query import RevisionPage, View
from app.api.context_spaces import allowed_query, call, service
from app.api.security import authenticated_subject
from app.core.models import ContextBrowse, ContextRequest, SubjectId

router = APIRouter(prefix='/context-spaces', tags=['context-spaces'])


@router.get('/{context_id}/understanding', response_model=RevisionPage)
async def browse_context(context_id: UUID, request: Request, response: Response, view: View,
                         limit: Annotated[int, Query(ge=1, le=100)] = 20,
                         after_revision_id: UUID | None = None,
                         descriptor: Annotated[str | None, Query(min_length=1)] = None,
                         descriptor_dimension: Literal['thematic', 'semantic_role'] | None = None,
                         latest_pending: bool = False, include_tentative: bool = False,
                         kind: Literal['item', 'entity', 'relation'] | None = None,
                         unclassified: bool = False, item_id: UUID | None = None,
                         revision_id: UUID | None = None, related_item_id: UUID | None = None,
                         subject: SubjectId = Depends(authenticated_subject)):
    allowed_query(request, {'view', 'limit', 'after_revision_id', 'descriptor', 'include_tentative',
                            'kind', 'unclassified', 'item_id', 'revision_id', 'related_item_id', 'descriptor_dimension', 'latest_pending'})
    try:
        query = ContextBrowse(context_id=str(context_id), view=view, limit=limit,
            after_revision_id=str(after_revision_id) if after_revision_id else None,
            descriptor=descriptor, descriptor_dimension=descriptor_dimension, latest_pending=latest_pending, include_tentative=include_tentative, kind=kind,
            unclassified=unclassified, item_id=str(item_id) if item_id else None,
            revision_id=str(revision_id) if revision_id else None,
            related_item_id=str(related_item_id) if related_item_id else None)
    except ValueError:
        raise HTTPException(422, 'Invalid navigation filters') from None
    result = await call(service(request).browse(ContextRequest(subject_id=subject, query=query)))
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['Vary'] = 'Authorization'
    return RevisionPage(view=view, items=result.revisions, next_after_revision_id=result.next_after_revision_id)
