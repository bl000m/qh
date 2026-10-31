"""Mistral adapter mocks only. No real HTTP/key is used by pytest or CI."""

import asyncio
from decimal import Decimal
import json
from pathlib import Path

import httpx
import pytest

from adapters.llm.mistral import (
    ExperimentBudget,
    MistralProvider,
    MistralError,
    MODEL,
    cost,
)
from app.core.models import GenerationRequest, Message, MessageRole
from app.core.ports import LLMProvider

REQUEST = GenerationRequest(
    messages=(
        Message(role=MessageRole.USER, content="Return JSON for a synthetic source."),
    )
)


def budget(tmp_path):
    return ExperimentBudget(tmp_path / "ledger.json", create=True)


def response(**changes):
    data = dict(
        model=MODEL,
        usage=dict(prompt_tokens=80, completion_tokens=20),
        choices=[dict(finish_reason="stop", message=dict(content='{"items":[]}'))],
    )
    return {**data, **changes}


def test_official_json_mode_no_retry_usage_and_raw_separation(tmp_path, monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "synthetic-test-value")
    seen = []

    def handler(req):
        seen.append(req)
        assert str(req.url) == "https://api.mistral.ai/v1/chat/completions"
        payload = json.loads(req.content)
        assert payload["model"] == MODEL and payload["response_format"] == {
            "type": "json_object"
        }
        assert (
            payload["max_tokens"] == 6000
            and payload["n"] == 1
            and payload["stream"] is False
        )
        assert req.headers["Authorization"] == "Bearer synthetic-test-value"
        return httpx.Response(200, json=response())

    ledger = budget(tmp_path)
    provider = MistralProvider(budget=ledger, transport=httpx.MockTransport(handler))
    assert isinstance(provider, LLMProvider)
    result = asyncio.run(provider.generate(REQUEST))
    assert result.message.content == '{"items":[]}' and len(seen) == 1
    assert provider.last_exchange["response"] == response()
    state = json.loads(ledger.path.read_text())
    assert state["calls"][0]["observed_usd"] == str(cost(80, 20))
    assert "synthetic-test-value" not in ledger.path.read_text()


@pytest.mark.parametrize(
    "failure,kind,blocks",
    [
        ("400", "request", False),
        ("401", "auth", True),
        ("429", "rate_limit", False),
        ("500", "provider", False),
        ("redirect", "provider", False),
        ("timeout", "transport", False),
        ("bad_json", "provider", False),
        ("bad_usage", "accounting", True),
        ("wrong_model", "accounting", True),
        ("over_tokens", "accounting", True),
    ],
)
def test_failures_are_classified_counted_redacted_and_only_anomalies_block(
    tmp_path, monkeypatch, failure, kind, blocks
):
    monkeypatch.setenv("MISTRAL_API_KEY", "synthetic-private-token")
    seen = []

    def handler(req):
        seen.append(req)
        if failure == "timeout":
            raise httpx.ReadTimeout("synthetic-private-token")
        if failure in ("400", "401", "429", "500", "redirect"):
            return httpx.Response(
                {"redirect": 302}.get(failure, int(failure) if failure.isdigit() else 500),
                text="synthetic-private-token",
            )
        if failure == "bad_json":
            return httpx.Response(200, text="not JSON")
        if failure == "bad_usage":
            return httpx.Response(200, json=response(usage={}))
        if failure == "wrong_model":
            return httpx.Response(200, json=response(model="another-model"))
        return httpx.Response(
            200, json=response(usage=dict(prompt_tokens=16001, completion_tokens=20))
        )

    ledger = budget(tmp_path)
    provider = MistralProvider(budget=ledger, transport=httpx.MockTransport(handler))
    with pytest.raises(MistralError) as exc:
        asyncio.run(provider.generate(REQUEST))
    state = json.loads(ledger.path.read_text())
    # One HTTP attempt, no retry; the failed reservation stays counted.
    assert exc.value.kind == kind and "synthetic-private-token" not in str(exc.value)
    assert len(seen) == 1 and state["calls"][0]["status"] == "failed"
    assert "observed_usd" not in state["calls"][0] and state["blocked"] is blocks
    with pytest.raises(MistralError):
        asyncio.run(provider.generate(REQUEST))
    # An isolated request/transport/provider incident never blocks the next call.
    assert len(seen) == (1 if blocks else 2)


def test_caps_and_missing_key_fail_before_http(tmp_path, monkeypatch):
    ledger = budget(tmp_path)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    with pytest.raises(MistralError, match="unavailable"):
        MistralProvider(budget=ledger)
    monkeypatch.setenv("MISTRAL_API_KEY", "synthetic")
    provider = MistralProvider(budget=ledger, max_input_tokens=1)
    with pytest.raises(MistralError, match="input cap"):
        asyncio.run(provider.generate(REQUEST))
    assert not json.loads(ledger.path.read_text())["calls"]


def test_persistent_call_budget_crash_and_spend_gates(tmp_path):
    ledger = budget(tmp_path)
    for i in range(8):
        assert ledger.reserve("metadata", Decimal(0)) == i
        ledger.settle(i)
    with pytest.raises(MistralError):
        ledger.reserve("ninth", Decimal(0))
    reopened = ExperimentBudget(ledger.path)
    with pytest.raises(MistralError):
        reopened.reserve("ninth", Decimal(0))
    with pytest.raises(FileExistsError):
        ExperimentBudget(ledger.path, create=True)
    other = ExperimentBudget(tmp_path / "pending.json", create=True)
    with pytest.raises(MistralError):
        other.reserve("large", Decimal("0.21"))
    other.reserve("pending", Decimal("0.01"))
    # A crash-left pending reservation stays counted but does not close the gate.
    with pytest.raises(MistralError):
        ExperimentBudget(other.path).reserve("over-ceiling", Decimal("0.20"))
    assert ExperimentBudget(other.path).reserve("after-crash", Decimal("0.19")) == 1


def test_metadata_probe_uses_one_of_eight_requests(tmp_path, monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "synthetic")
    provider = MistralProvider(
        budget=budget(tmp_path),
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200, json=dict(id=MODEL, capabilities=dict(completion_chat=True))
            )
        ),
    )
    assert asyncio.run(provider.verify_model())["id"] == MODEL
    assert len(json.loads(provider.budget.path.read_text())["calls"]) == 1


def test_reference_is_separate_literal_and_dataset_is_new():
    folder = Path(__file__).parent / "fixtures"
    cases = json.loads((folder / "mistral_unseen_conversations.json").read_text())
    reference = json.loads((folder / "mistral_evaluation_reference.json").read_text())
    old = json.loads((folder / "qh8_conversations.json").read_text())
    old_texts = {t["text"] for c in old for t in c["conversation"]["turns"]}
    assert len(cases) == 4 and len(reference["cases"]) == 4
    for case, ref in zip(cases, reference["cases"]):
        assert case["name"] == ref["name"] and len(case["conversation"]["turns"]) >= 3
        assert "expected" not in case and "forbidden_inferences" not in case
        turns = {t["id"]: t["text"] for t in case["conversation"]["turns"]}
        assert not old_texts.intersection(turns.values())
        for item in ref["expected"]:
            for evidence in item["evidence"]:
                assert evidence["quote"] in turns[evidence["turn_id"]]


def test_error_diagnostics_keep_only_bounded_codes_and_numeric_retry_after(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("MISTRAL_API_KEY", "synthetic-private-token")
    provider = MistralProvider(
        budget=budget(tmp_path),
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                429,
                json={
                    "code": "1300",
                    "type": "rate_limited",
                    "message": "synthetic-private-token",
                },
                headers={"Retry-After": "2", "X-Secret": "synthetic-private-token"},
            )
        ),
    )
    with pytest.raises(MistralError):
        asyncio.run(provider.generate(REQUEST))
    assert provider.last_failure["http_status"] == 429
    assert provider.last_failure["code"] == "1300"
    assert provider.last_failure["type"] == "rate_limited"
    assert provider.last_failure["retry_after_seconds"] == 2
    assert provider.last_failure["headers"] == {"retry-after": "2"}
    assert provider.last_failure["message"] == "[REDACTED]"
    assert provider.last_failure["latency_seconds"] >= 0
    assert "synthetic-private-token" not in json.dumps(provider.last_failure)


def test_only_review_worthy_failures_need_an_explicit_reconciliation(tmp_path):
    ledger = budget(tmp_path)
    limited = ledger.reserve("chat", Decimal("0.006"))
    ledger.settle(limited, error="Mistral HTTP 429")
    assert not json.loads(ledger.path.read_text())["blocked"]
    with pytest.raises(MistralError):
        ledger.reconcile_reviewed_429(reason="Nothing is blocked")
    anomaly = ledger.reserve("chat", Decimal("0.006"))
    ledger.settle(anomaly, error="Mistral usage missing or invalid", block=True)
    state = json.loads(ledger.path.read_text())
    assert state["blocked"] and [c["reserved_usd"] for c in state["calls"]] == ["0.006", "0.006"]
    with pytest.raises(MistralError):
        ledger.reserve("blocked", Decimal(0))

@pytest.mark.parametrize('capture_private_errors', [False, True])
def test_error_body_capture_is_explicit_and_never_retries(tmp_path, monkeypatch, capture_private_errors):
    monkeypatch.setenv('MISTRAL_API_KEY', 'synthetic-test-value')
    seen = []
    def error(req):
        seen.append(req)
        return httpx.Response(429, json={'message': 'synthetic-private-response'})
    ledger = budget(tmp_path)
    provider = MistralProvider(budget=ledger, transport=httpx.MockTransport(error),
        capture_private_errors=capture_private_errors)
    with pytest.raises(MistralError):
        asyncio.run(provider.generate(REQUEST))
    assert len(seen) == 1
    assert (provider.last_exchange is not None) is capture_private_errors
    if capture_private_errors:
        assert provider.last_exchange['http_status'] == 429
    assert not json.loads(ledger.path.read_text())['blocked']
