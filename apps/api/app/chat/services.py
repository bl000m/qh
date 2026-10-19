from typing import Protocol, runtime_checkable

from app.chat.models import ChatRequest, ChatResponse
from app.core.ports import LLMProvider


@runtime_checkable
class ChatService(Protocol):
    """Inbound contract for a future QH conversation response.

    Implementations coordinate policy, authorized context retrieval, projections
    and LLMProvider through explicit injection. They own orchestration, not SDK
    calls or graph queries. No orchestration or conversation storage is supplied.
    """

    async def respond(self, request: ChatRequest) -> ChatResponse: ...


class ProviderSessionBinding(Protocol):
    """A per-grant adapter and the existing durable accounting view."""
    provider: LLMProvider

    def summary(self) -> dict: ...


class ProviderSessionFactory(Protocol):
    """Explicit outbound configuration; key presence alone never supplies a grant."""
    model: str
    expires_at: float
    max_calls: int
    max_usd: str

    def allowed(self, subject_id: str, context_id: str) -> bool: ...
    async def verified(self, subject_id: str, context_id: str) -> bool: ...
    async def available(self, subject_id: str, context_id: str) -> bool: ...
    def remaining(self) -> dict: ...
    def accepts_snapshot(self, subject_id: str, context_id: str, digest: str) -> bool: ...
    def bind(self, session_id: str, *, max_calls: int, max_usd: str) -> ProviderSessionBinding: ...
