"""Projection application engine. Authorization is injected from PolicyService."""
from datetime import datetime, timezone
from typing import Awaitable, Callable

from app.projections.drafts import (
    DraftRepository, DraftSpec, ProjectionDraft, ProjectionNotFound,
    ProjectionUnavailable, identifier,
)


class ProjectionDraftService:
    def __init__(self, *, repository: DraftRepository,
                 authorize: Callable[[str, str], Awaitable[bool]], resolver=None,
                 clock: Callable[[], datetime] | None = None):
        self.repository, self.authorize, self.resolver = repository, authorize, resolver
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    async def _allow(self, subject, scope):
        identifier(subject)
        identifier(scope)
        try:
            allowed = await self.authorize(subject, scope)
        except Exception:
            raise ProjectionUnavailable('Projection unavailable') from None
        if allowed is not True:
            raise ProjectionNotFound('Projection not found')

    async def _checked(self, subject, scope, draft):
        await self._allow(subject, scope)
        if not isinstance(draft, ProjectionDraft) or draft.owner_id != subject or draft.context_id != scope:
            raise ProjectionUnavailable('Projection unavailable')
        return draft

    async def create(self, subject, scope, spec):
        await self._allow(subject, scope)
        if not isinstance(spec, DraftSpec):
            raise ValueError('Explicit draft specification required')
        return await self._checked(subject, scope, await self.repository.create(subject, scope, spec))

    async def read(self, subject, scope, draft_id):
        await self._allow(subject, scope)
        identifier(draft_id)
        draft = await self._checked(subject, scope, await self.repository.read(subject, scope, draft_id))
        if draft.id != draft_id:
            raise ProjectionUnavailable('Projection unavailable')
        return draft

    async def replace(self, subject, scope, draft_id, version, spec):
        await self._allow(subject, scope)
        identifier(draft_id)
        if type(version) is not int or version < 1 or not isinstance(spec, DraftSpec):
            raise ValueError('Explicit draft and expected version required')
        return await self._checked(subject, scope,
            await self.repository.replace(subject, scope, draft_id, version, spec))
