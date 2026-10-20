"""Owner-managed draft values and persistence port; no sharing approval."""
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.core.models import ContextRetrievalUnavailable, ContextSpaceNotFound, RevisionRelation, RevisionTime, SourceRevisionRef


class ProjectionNotFound(ContextSpaceNotFound):
    """Uniform absent, foreign or outside-scope resource."""


class ProjectionConflict(RuntimeError):
    """Draft version changed; explicit owner reload required."""


class ProjectionUnavailable(ContextRetrievalUnavailable):
    """Cannot establish a safe canonical projection."""


def identifier(value):
    if not isinstance(value, str) or str(UUID(value)) != value:
        raise ValueError('Canonical UUID required')
    return value


@dataclass(frozen=True, slots=True, kw_only=True, order=True)
class RevisionKey:
    item_id: str
    revision_id: str

    def __post_init__(self):
        identifier(self.item_id)
        identifier(self.revision_id)


@dataclass(frozen=True, slots=True, kw_only=True)
class DraftSpec:
    recipient_kind: str
    recipient: str
    purpose: str
    included: tuple[RevisionKey, ...] = ()
    excluded: tuple[RevisionKey, ...] = ()
    expires_at: datetime | None = None

    def __post_init__(self):
        if self.recipient_kind not in ('subject', 'category'):
            raise ValueError('Explicit recipient kind required')
        for text, maximum in ((self.recipient, 256), (self.purpose, 1024)):
            if not isinstance(text, str) or not text.strip() or len(text) > maximum or '\x00' in text:
                raise ValueError('Bounded recipient and purpose required')
        for refs in (self.included, self.excluded):
            if (not isinstance(refs, tuple) or len(refs) > 100
                    or any(not isinstance(ref, RevisionKey) for ref in refs)
                    or len(set(refs)) != len(refs)):
                raise ValueError('Bounded unique exact revision pairs required')
        pairs = self.included + self.excluded
        if len({p.revision_id for p in pairs}) != len({(p.item_id, p.revision_id) for p in pairs}):
            raise ValueError('Revision must identify one item')
        if self.expires_at is not None and (
                not isinstance(self.expires_at, datetime) or self.expires_at.utcoffset() is None):
            raise ValueError('Timezone-aware expiry required')

    @property
    def effective(self):
        return tuple(sorted(set(self.included) - set(self.excluded)))


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectionDraft:
    id: str
    context_id: str
    owner_id: str
    version: int
    spec: DraftSpec
    created_at: datetime
    updated_at: datetime
    state: str = 'draft'

    def __post_init__(self):
        for value in (self.id, self.context_id, self.owner_id):
            identifier(value)
        if type(self.version) is not int or self.version < 1 or self.state != 'draft':
            raise ValueError('Versioned draft required')


class DraftRepository(Protocol):
    async def create(self, subject: str, scope: str, spec: DraftSpec) -> ProjectionDraft: ...
    async def read(self, subject: str, scope: str, draft_id: str) -> ProjectionDraft: ...
    async def replace(self, subject: str, scope: str, draft_id: str,
                      version: int, spec: DraftSpec) -> ProjectionDraft: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectedRevision:
    """Selected content with exact evidence refs; no unselected pointers/origins."""
    context_id: str
    item_id: str
    revision_id: str
    revision_no: int
    structural_kind: str
    type_id: str
    type_version: int
    content: dict[str, object]
    origin_kind: str
    validation_state: str
    temporal: RevisionTime
    relation: RevisionRelation | None
    provenance: tuple[SourceRevisionRef, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolvedDraft:
    draft_id: str
    context_id: str
    version: int
    recipient_kind: str
    recipient: str
    purpose: str
    expires_at: datetime | None
    revisions: tuple[ProjectedRevision, ...]


class DraftResolver(Protocol):
    async def resolve(self, subject: str, scope: str,
                      keys: tuple[RevisionKey, ...]) -> tuple[ProjectedRevision, ...]: ...
