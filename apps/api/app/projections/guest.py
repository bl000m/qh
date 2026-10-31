"""Verified mailbox invitation/session contracts; no guest account or write grant."""
from dataclasses import dataclass, field
from datetime import datetime
import json
from typing import Protocol

from app.core.models import GuestAccess


class GuestDenied(PermissionError):
    """Uniform invalid, expired, used, revoked or mismatched invitation/session."""


class GuestUnavailable(RuntimeError):
    """Sanitized infrastructure failure; no address, proof or payload in errors."""


class GuestRateLimited(RuntimeError):
    """Public peer-level throttling, independent of invitation existence."""


class MailUnavailable(RuntimeError):
    """Sandbox delivery failed; never retry automatically."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Invitation:
    id: str
    snapshot_id: str
    expires_at: datetime
    token: str = field(repr=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class CodeDelivery:
    challenge_id: str
    recipient: str = field(repr=False)
    expires_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class GuestSession:
    access: GuestAccess
    token: str = field(repr=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class GuestSnapshot:
    context_id: str
    snapshot_id: str
    payload_json: str = field(repr=False)
    include_quotes: bool = False

    @property
    def payload(self):
        return json.loads(self.payload_json)


class GuestProofs(Protocol):
    def token(self) -> str: ...
    def code(self) -> str: ...
    def token_hash(self, token: str, kind: str) -> str: ...
    def code_hash(self, token_hash: str, challenge_id: str, code: str) -> str: ...
    def peer_hash(self, peer: str, phase: str) -> str: ...


class SandboxMail(Protocol):
    async def send(self, delivery: CodeDelivery, code: str) -> None: ...


class GuestRepository(Protocol):
    async def create(self, subject: str, scope: str, snapshot_id: str, token_hash: str) -> dict: ...
    async def list(self, subject: str, scope: str) -> dict: ...
    async def revoke(self, subject: str, scope: str, invitation_id: str) -> None: ...
    async def limit(self, key_hash: str, maximum: int) -> bool: ...
    async def issue(self, token_hash: str, email: str, challenge_id: str, code_hash: str) -> CodeDelivery | None: ...
    async def delivered(self, challenge_id: str, sent: bool) -> None: ...
    async def verify(self, token_hash: str, challenge_id: str, code_hash: str, session_hash: str) -> GuestAccess | None: ...
    async def authenticate(self, session_hash: str) -> GuestAccess | None: ...
    async def guest_for(self, session_id: str) -> GuestAccess | None: ...
    async def payload(self, grant: GuestAccess, right: str) -> GuestSnapshot: ...
    async def logout(self, session_hash: str) -> None: ...
