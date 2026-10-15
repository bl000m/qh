"""Pinned official Mistral chat API; explicit bounded experiment, zero retries.

No client is created at application startup. Credentials come only from the process
MISTRAL_API_KEY. Raw successful response/usage stay separate from QH validation.
List-price cost from observed tokens is not an independently verified invoice.
"""

from decimal import Decimal
import json
import os
from pathlib import Path
import fcntl

import httpx

from app.core.models import GenerationResult, Message, MessageRole

MODEL = "mistral-small-2603"
BASE = "https://api.mistral.ai/v1"
INPUT_USD_PER_M = Decimal("0.15")
OUTPUT_USD_PER_M = Decimal("0.60")


class MistralError(RuntimeError):
    """Redacted failure; never includes SDK messages, response bodies or secrets."""


def cost(prompt, completion):
    return (
        Decimal(prompt) * INPUT_USD_PER_M + Decimal(completion) * OUTPUT_USD_PER_M
    ) / 1_000_000


class ExperimentBudget:
    """Durable fail-closed ledger. Attempts (including metadata/errors) count.

    Create once, never reset by rerunning a command. A crash after reservation
    leaves it pending and blocks further calls until explicit review. Reservation
    includes a conservative input-token bound and the requested output maximum.
    """

    def __init__(self, path, *, create=False):
        self.path = Path(path)
        if create:
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as f:
                json.dump(dict(max_calls=8, max_usd="0.20", calls=[], blocked=False), f)
                f.flush()
                os.fsync(f.fileno())
        if not self.path.is_file() or self.path.stat().st_mode & 0o077:
            raise ValueError("Private existing experiment ledger required")

    def _change(self, operation):
        with self.path.open("r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            state = json.load(f)
            result = operation(state)
            f.seek(0)
            json.dump(state, f, indent=2)
            f.truncate()
            f.flush()
            os.fsync(f.fileno())
            return result

    def reserve(self, kind, maximum):
        def update(state):
            spent = sum(
                Decimal(c.get("observed_usd", c["reserved_usd"]))
                for c in state["calls"]
            )
            if (
                state["blocked"]
                or any(c["status"] == "pending" for c in state["calls"])
                or len(state["calls"]) >= min(state["max_calls"], 8)
                or spent + maximum > min(Decimal(state["max_usd"]), Decimal("0.20"))
            ):
                raise MistralError("Experiment call/budget gate closed")
            state["calls"].append(
                dict(kind=kind, reserved_usd=str(maximum), status="pending")
            )
            return len(state["calls"]) - 1

        return self._change(update)

    def settle(self, index, *, usage=None, error=None):
        def update(state):
            record = state["calls"][index]
            if record["status"] != "pending":
                raise MistralError("Ledger attempt already settled")
            if error:
                record.update(status="failed", error=error)
                state["blocked"] = True
            else:
                charge = (
                    cost(usage["prompt_tokens"], usage["completion_tokens"])
                    if usage
                    else Decimal(0)
                )
                record.update(status="completed", usage=usage, observed_usd=str(charge))
                if charge > Decimal(record["reserved_usd"]):
                    state["blocked"] = True
                    raise MistralError("Observed cost exceeded reservation")

        self._change(update)


class MistralProvider:
    def __init__(
        self, *, budget, max_input_tokens=16000, max_output_tokens=6000, transport=None
    ):
        self._key = os.environ.get("MISTRAL_API_KEY", "").strip()
        if not self._key:
            raise MistralError("MISTRAL_API_KEY is unavailable")
        if not 1 <= max_input_tokens <= 16000 or not 1 <= max_output_tokens <= 6000:
            raise ValueError("Experiment token caps exceeded")
        self.budget = budget
        self.max_input_tokens, self.max_output_tokens = (
            max_input_tokens,
            max_output_tokens,
        )
        self.transport = transport
        self.last_exchange = None

    async def _request(self, method, path, *, payload=None, maximum=Decimal(0)):
        self.last_exchange = None
        attempt = self.budget.reserve(path, maximum)
        try:
            async with httpx.AsyncClient(
                transport=self.transport or httpx.AsyncHTTPTransport(retries=0),
                timeout=httpx.Timeout(60, connect=10),
                follow_redirects=False,
                trust_env=False,
            ) as client:
                response = await client.request(
                    method,
                    BASE + path,
                    json=payload,
                    headers={
                        "Authorization": "Bearer " + self._key,
                        "Content-Type": "application/json",
                    },
                )
            if response.status_code != 200:
                raise MistralError("Mistral HTTP " + str(response.status_code))
            data = response.json()
            self.last_exchange = dict(request=payload, response=data, attempt=attempt)
            if method == "POST":
                usage = data.get("usage", {})
                if any(
                    type(usage.get(k)) is not int or usage[k] < 0
                    for k in ("prompt_tokens", "completion_tokens")
                ):
                    raise MistralError("Mistral usage missing or invalid")
                if (
                    usage["prompt_tokens"] > self.max_input_tokens
                    or usage["completion_tokens"] > self.max_output_tokens
                ):
                    raise MistralError("Mistral observed token limit exceeded")
                if data.get("model") != MODEL:
                    raise MistralError("Mistral response model differs from pinned ID")
                self.budget.settle(
                    attempt,
                    usage={k: usage[k] for k in ("prompt_tokens", "completion_tokens")},
                )
            else:
                self.budget.settle(attempt)
            return data
        except MistralError as exc:
            # No provider response/error body is included in the failure path.
            self.budget.settle(attempt, error=str(exc))
            raise MistralError(str(exc)) from None
        except Exception:
            self.budget.settle(attempt, error="Mistral transport/response failure")
            raise MistralError("Mistral transport/response failure") from None

    async def verify_model(self):
        data = await self._request("GET", "/models/" + MODEL)
        if data.get("id") != MODEL or not data.get("capabilities", {}).get(
            "completion_chat"
        ):
            raise MistralError("Pinned Mistral Small 4 unavailable for chat")
        return data

    async def generate(self, request):
        # UTF-8 bytes + 256/message is a conservative local bound, not a tokenizer.
        # Actual prompt usage is checked; no hidden-provider-token exactness claim.
        bound = sum(len(m.content.encode()) + 256 for m in request.messages)
        if not request.messages or bound > self.max_input_tokens:
            raise MistralError("Mistral input cap exceeded before HTTP")
        payload = dict(
            model=MODEL,
            messages=[
                dict(role=m.role.value, content=m.content) for m in request.messages
            ],
            response_format={"type": "json_object"},
            temperature=0,
            random_seed=42,
            max_tokens=self.max_output_tokens,
            stream=False,
            n=1,
            tool_choice="none",
        )
        data = await self._request(
            "POST",
            "/chat/completions",
            payload=payload,
            maximum=cost(self.max_input_tokens, self.max_output_tokens),
        )
        try:
            choice = data["choices"][0]
            if choice["finish_reason"] != "stop" or not isinstance(
                choice["message"]["content"], str
            ):
                raise ValueError("Incomplete completion")
            return GenerationResult(
                message=Message(
                    role=MessageRole.ASSISTANT, content=choice["message"]["content"]
                )
            )
        except (KeyError, IndexError, TypeError, ValueError):
            raise MistralError(
                "Mistral completion missing or truncated; no retry"
            ) from None
