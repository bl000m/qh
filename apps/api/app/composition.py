"""Typed application bindings supplied explicitly by the composition root."""

from dataclasses import dataclass

from app.environment.service import EnvironmentService

from app.chat.services import ChatService
from app.chat.sessions import ProviderSessions
from app.core.services import ContextService
from app.policy.services import PolicyService
from app.projections.services import ProjectionService


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
    environment: EnvironmentService | None = None
