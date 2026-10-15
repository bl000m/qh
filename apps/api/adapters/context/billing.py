"""Per-request approval at the HTTP boundary; no key or payload in approval output."""

import asyncio
import hashlib
import json
import secrets
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass

import httpx


class ExternalCallDenied(RuntimeError):
    pass


@dataclass(frozen=True, kw_only=True)
class CallDescription:
    provider: str
    endpoint: str
    model: str
    purpose: str
    payload_sha256: str
    input_bytes: int
    max_output_tokens: int | None
    cost: str = "Not calculable: exact token usage and current model tariff unavailable"


Approval = Callable[[CallDescription], Awaitable[bool]]


async def deny_call(description: CallDescription) -> bool:
    return False


async def approve_in_terminal(description: CallDescription) -> bool:
    """Manual smoke only. Each prompt covers exactly one HTTP attempt."""
    token = secrets.token_hex(8)
    print(json.dumps(asdict(description), indent=2))
    answer = await asyncio.to_thread(input, f"Authorize this single request: type ALLOW {token}: ")
    return answer == f"ALLOW {token}"


class ApprovedTransport(httpx.AsyncBaseTransport):
    def __init__(self, *, model: str, embedding_model: str, approval: Approval = deny_call,
                 inner: httpx.AsyncBaseTransport | None = None):
        self.model = model
        self.embedding_model = embedding_model
        self.approval = approval
        self.inner = inner if inner is not None else httpx.AsyncHTTPTransport(retries=0)
        self.lock = asyncio.Lock()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        endpoint = str(request.url)
        allowed = {
            "https://api.mistral.ai/v1/chat/completions": (self.model, "Graphiti semantic extraction"),
            "https://api.mistral.ai/v1/embeddings": (self.embedding_model, "Graphiti semantic embedding"),
        }
        if request.method != "POST" or endpoint not in allowed:
            raise ExternalCallDenied("External endpoint is not configured")
        body = await request.aread()
        data = json.loads(body)
        model, purpose = allowed[endpoint]
        if data.get("model") != model or data.get("stream"):
            raise ExternalCallDenied("Unexpected model or streaming request")
        if endpoint.endswith("/embeddings"):
            inputs = data.get("input")
            if not (isinstance(inputs, str) or
                    isinstance(inputs, list) and len(inputs) == 1 and isinstance(inputs[0], str)):
                raise ExternalCallDenied("Embedding batches require separate single-input requests")
        description = CallDescription(provider="Mistral Cloud", endpoint=endpoint, model=model,
                                      purpose=purpose, payload_sha256=hashlib.sha256(body).hexdigest(),
                                      input_bytes=len(body), max_output_tokens=data.get("max_tokens"))
        async with self.lock:
            if not await self.approval(description):
                raise ExternalCallDenied("Single-request authorization required")
            # A permit is never cached, even when the request fails.
            try:
                response = await self.inner.handle_async_request(request)
            except Exception:
                raise RuntimeError("Provider request failed; no automatic retry") from None
            if response.status_code >= 300:
                await response.aclose()
                raise RuntimeError("Provider rejected request; no automatic retry")
            return response

    async def aclose(self) -> None:
        await self.inner.aclose()
