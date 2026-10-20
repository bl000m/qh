"""Typed application bindings supplied explicitly by the composition root."""

from dataclasses import dataclass
from typing import Protocol

from app.core.models import ContextSpace, ContextSpacePage, SubjectId


from app.chat.services import ChatService
from app.chat.sessions import ProviderSessions
from app.core.services import ContextService
from app.policy.services import PolicyService
from app.projections.services import ProjectionService


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
