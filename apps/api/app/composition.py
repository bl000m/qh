"""Typed application bindings supplied explicitly by the composition root."""

from dataclasses import dataclass
from typing import Protocol

from app.core.models import ContextSpace, ContextSpacePage, SubjectId


from app.chat.services import ChatService
from app.chat.sessions import ProviderSessions
from app.core.services import ContextService
from app.policy.services import PolicyService
from app.projections.services import ProjectionService
from app.projections.disclosure_service import DisclosureService
from app.chat.guest import GuestSnapshotChat


class EnvironmentApplication(Protocol):
    """Inbound composition facet; implementations own organization policy/metadata."""
    async def read(self, subject: SubjectId) -> dict: ...
    async def replace(self, subject: SubjectId, document: dict) -> dict: ...
    async def opened(self, subject: SubjectId, scope: str, event_id: str) -> dict: ...
    async def create_space(self, subject: SubjectId, name: str, primary_domain_id: str) -> ContextSpace: ...
    async def resume(self, subject: SubjectId, sort: str, domain: str | None, limit: int, after: str | None) -> ContextSpacePage: ...


class ReviewApplication(Protocol):
    """Inbound review facet; no persistence or policy implementation in composition."""
    async def pending(self, subject: SubjectId, scope: str, limit: int, after: str | None) -> dict: ...
    async def status(self, subject: SubjectId, scope: str, revision: str) -> dict: ...
    async def apply(self, subject: SubjectId, scope: str, revision: str, operation: dict) -> dict: ...


class EnrichmentApplication(Protocol):
    """Explicit owner-selected conversation persistence through the Engine."""
    async def enrich(self, subject: SubjectId, scope: str, payload: dict) -> dict: ...
    async def capabilities(self, subject: SubjectId, scope: str) -> dict: ...


class DevelopmentAIApplication(Protocol):
    """Owner-approved development ingress; automatic access and global budget gates."""
    async def diagnostics(self, identity, request, delete_id=None) -> dict: ...
    async def capabilities(self, identity, request) -> dict: ...
    async def respond(self, identity, request): ...
    async def enrich(self, identity, scope: str, payload: dict) -> dict: ...


class GuestApplication(Protocol):
    """Snapshot invitations; transient guest proof, never a canonical QH account."""
    async def create(self, subject, scope: str, snapshot_id: str): ...
    async def list(self, subject, scope: str) -> dict: ...
    async def revoke(self, subject, scope: str, invitation_id: str) -> None: ...
    async def request_code(self, token: str, email: str, peer: str) -> dict: ...
    async def verify(self, token: str, challenge_id: str, code: str, peer: str): ...
    async def session(self, token: str): ...
    async def snapshot(self, token: str, snapshot_id: str, right: str = 'READ') -> dict: ...
    async def logout(self, token: str) -> None: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class ApplicationServices:
    """Explicit inbound services; unimplemented feature facets remain unbound.

    Service implementations receive their ContextEngine/LLMProvider and other
    dependencies through their own constructors. Transport factories receive
    this binding object instead of constructing or importing outbound adapters.
    """

    context: ContextService
    policy: PolicyService
    projections: ProjectionService | None = None
    chat: ChatService | None = None
    chat_sessions: ProviderSessions | None = None
    environment: EnvironmentApplication | None = None
    review: ReviewApplication | None = None
    enrichment: EnrichmentApplication | None = None
    development_ai: "DevelopmentAIApplication | None" = None
    guest: GuestApplication | None = None
    sharing: DisclosureService | None = None
    guest_chat: GuestSnapshotChat | None = None
