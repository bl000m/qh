"""Projection application engine. Authorization is injected from PolicyService."""
from datetime import datetime, timezone
from typing import Awaitable, Callable

from app.projections.drafts import (
    DraftRepository, DraftResolver, DraftSpec, ProjectedRevision, ProjectionConflict,
    ProjectionDraft, ProjectionNotFound, ProjectionUnavailable, ResolvedDraft, RevisionKey, identifier,
)


class ProjectionDraftService:
    def __init__(self, *, repository: DraftRepository,
                 authorize: Callable[[str, str], Awaitable[bool]], resolver: DraftResolver | None = None,
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
        result = await self._checked(subject, scope, await self.repository.create(subject, scope, spec))
        if result.version != 1 or result.spec != spec:
            raise ProjectionUnavailable('Projection unavailable')
        return result

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
        result = await self._checked(subject, scope,
            await self.repository.replace(subject, scope, draft_id, version, spec))
        if result.id != draft_id or result.version != version + 1 or result.spec != spec:
            raise ProjectionUnavailable('Projection unavailable')
        return result

    def _resolvable(self, draft, version):
        if type(version) is not int or version < 1:
            raise ValueError('Explicit expected version required')
        if draft.version != version:
            raise ProjectionConflict('Projection changed')
        if not draft.spec.effective or (draft.spec.expires_at is not None and draft.spec.expires_at <= self.clock()):
            raise ProjectionNotFound('Projection not found')

    async def resolve(self, subject, scope, draft_id, version, requested=None):
        draft = await self.read(subject, scope, draft_id)
        self._resolvable(draft, version)
        keys = draft.spec.effective
        if requested is not None:
            if (not isinstance(requested, tuple) or not requested or len(requested) > 100
                    or any(not isinstance(key, RevisionKey) for key in requested)
                    or len(set(requested)) != len(requested)
                    or not set(requested) <= set(keys)):
                raise ProjectionNotFound('Projection not found')
            keys = tuple(sorted(requested))
        if self.resolver is None:
            raise ProjectionUnavailable('Projection unavailable')
        try:
            revisions = await self.resolver.resolve(subject, scope, keys)
        except (ProjectionNotFound, ProjectionUnavailable):
            raise
        except Exception:
            raise ProjectionUnavailable('Projection unavailable') from None
        if (not isinstance(revisions, tuple) or len(revisions) != len(keys)
                or any(not isinstance(r, ProjectedRevision) or r.context_id != scope for r in revisions)
                or {RevisionKey(item_id=r.item_id, revision_id=r.revision_id) for r in revisions} != set(keys)):
            raise ProjectionUnavailable('Projection unavailable')
        for revision in revisions:
            if revision.relation is not None:
                for side in ('source', 'target'):
                    endpoint = RevisionKey(item_id=getattr(revision.relation,side+'_item_id'),
                        revision_id=getattr(revision.relation,side+'_revision_id'))
                    if endpoint not in keys:
                        raise ProjectionUnavailable('Projection unavailable')
        # No transaction spans graph work. Pin the edit version and expiry again,
        # and repeat the shared owner policy before any result leaves this service.
        current = await self.read(subject, scope, draft_id)
        self._resolvable(current, version)
        if current != draft:
            raise ProjectionConflict('Projection changed')
        return ResolvedDraft(draft_id=draft.id,context_id=scope,version=draft.version,
            recipient_kind=draft.spec.recipient_kind,recipient=draft.spec.recipient,
            purpose=draft.spec.purpose,expires_at=draft.spec.expires_at,
            revisions=tuple(sorted(revisions,key=lambda r:(r.item_id,r.revision_id))))
