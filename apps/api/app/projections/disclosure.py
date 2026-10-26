"""Governed disclosure values/ports; safe representations never hydrate originals."""
from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
import re
from typing import Protocol

from app.projections.drafts import RevisionKey, identifier


GUARD_VERSION = 'qh.disclosure/1'
TEXT_REVIEW = 'unassessed_free_text'
LIVE_PROVIDER = 'mistral-small-2603'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True, slots=True, kw_only=True)
class AccessPolicy:
    recipient_email: str
    purpose: str
    rights: tuple[str, ...]
    expires_at: datetime
    include_proposed: bool = False
    include_quotes: bool = False
    provider: str | None = None
    excluded: tuple[RevisionKey, ...] = ()

    def __post_init__(self):
        email = self.recipient_email
        if (not isinstance(email, str) or len(email) > 254 or not email.isascii()
                or re.fullmatch(r'[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+', email) is None):
            raise ValueError('Specific recipient email required')
        if not isinstance(self.purpose, str) or not 1 <= len(self.purpose.strip()) <= 1024 or '\x00' in self.purpose:
            raise ValueError('Bounded purpose required')
        if (not isinstance(self.rights, tuple) or not self.rights
                or len(set(self.rights)) != len(self.rights) or not set(self.rights) <= {'READ', 'ASK_AI'}):
            raise ValueError('Explicit READ/ASK_AI rights required')
        if not isinstance(self.expires_at, datetime) or self.expires_at.utcoffset() is None:
            raise ValueError('Explicit timezone-aware expiry required')
        if type(self.include_proposed) is not bool or type(self.include_quotes) is not bool:
            raise ValueError('Explicit inclusion choices required')
        if (self.provider not in (None, 'offline',LIVE_PROVIDER) or ('ASK_AI' in self.rights) != (self.provider is not None)):
            raise ValueError('ASK_AI requires an explicitly authorized QH-controlled provider')
        if (not isinstance(self.excluded, tuple) or len(self.excluded) > 100
                or any(not isinstance(k, RevisionKey) for k in self.excluded)
                or len(set(self.excluded)) != len(self.excluded)):
            raise ValueError('Bounded exact restrictions required')
        object.__setattr__(self, 'rights', tuple(sorted(self.rights)))
        object.__setattr__(self, 'excluded', tuple(sorted(self.excluded)))

    def wire(self):
        return {**asdict(self), 'expires_at': self.expires_at.isoformat()}

    @classmethod
    def from_wire(cls, value):
        data = dict(value)
        data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        data['rights'] = tuple(data['rights'])
        data['excluded'] = tuple(RevisionKey(**k) for k in data['excluded'])
        return cls(**data)


@dataclass(frozen=True, slots=True, kw_only=True)
class Candidate:
    key: RevisionKey
    state: str
    endpoints: tuple[RevisionKey, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class Selection:
    context_id: str
    stamp: str
    candidates: tuple[Candidate, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class DisclosurePreview:
    id: str
    context_id: str
    owner_id: str
    draft_id: str | None
    policy: AccessPolicy
    selection_stamp: str
    # Canonical JSON strings make nested payloads immutable at this boundary.
    payload_json: str
    report_json: str
    fingerprint: str
    created_at: datetime

    @property
    def payload(self):
        return json.loads(self.payload_json)

    @property
    def report(self):
        return json.loads(self.report_json)


@dataclass(frozen=True, slots=True, kw_only=True)
class ApprovedSnapshot:
    id: str
    context_id: str
    owner_id: str
    preview_id: str
    fingerprint: str
    payload_json: str
    policy: AccessPolicy
    approved_at: datetime
    exceptions: tuple[str, ...]

    @property
    def payload(self):
        return json.loads(self.payload_json)


class DisclosureDecisionRequired(ValueError):
    """Preview contains named residual risks requiring an explicit owner decision."""


class DisclosureRepository(Protocol):
    async def select(self, subject: str, scope: str) -> Selection: ...
    async def prepare(self, preview: DisclosurePreview) -> DisclosurePreview: ...
    async def preview(self, subject: str, scope: str, preview_id: str) -> DisclosurePreview: ...
    async def approve(self, preview: DisclosurePreview, exceptions: tuple[str, ...]) -> ApprovedSnapshot: ...
    async def snapshot(self, subject: str, scope: str, snapshot_id: str) -> ApprovedSnapshot: ...


def preview_fingerprint(preview):
    return digest(dict(version=GUARD_VERSION, context_id=preview.context_id, owner_id=preview.owner_id,
        draft_id=preview.draft_id, policy=preview.policy.wire(), stamp=preview.selection_stamp,
        payload=preview.payload, report=preview.report))


def validate_preview(preview, subject, scope):
    for value in (preview.id, subject, scope):
        identifier(value)
    if (preview.owner_id != subject or preview.context_id != scope
            or preview_fingerprint(preview) != preview.fingerprint):
        raise ValueError('Invalid disclosure receipt')
