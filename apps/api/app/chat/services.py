from typing import Protocol, runtime_checkable

from app.chat.models import ChatRequest, ChatResponse


@runtime_checkable
class ChatService(Protocol):
    """Inbound contract for a future QH conversation response.

    Implementations coordinate policy, authorized context retrieval, projections
    and LLMProvider through explicit injection. They own orchestration, not SDK
    calls or graph queries. No orchestration or conversation storage is supplied.
    """

    async def respond(self, request: ChatRequest) -> ChatResponse: ...
