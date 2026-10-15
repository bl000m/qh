"""Deterministic extractor validation and provider substitution; no DB/network."""

import asyncio
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from adapters.llm.offline import (
    FixtureUnderstandingProvider,
    ReplayLLMProvider,
    request_hash,
)
from app.core.models import GenerationResult, Message, MessageRole
from app.core.ports import LLMProvider
from app.policy.models import PolicyDecision
from app.understanding.extractor import UnderstandingExtractor, decode_output

CASES = json.loads(
    (Path(__file__).parent / "fixtures/qh8_conversations.json").read_text()
)


class MemoryRepository:
    def __init__(self):
        self.subject_id = str(uuid4())
        self.sources = {}
        self.revisions = []

    def save(self, *, sources=(), revisions=()):
        self.sources.update({s["id"]: deepcopy(s) for s in sources})
        self.revisions = deepcopy(revisions)

    def read_sources(self, scopes, refs):
        return [deepcopy(self.sources[r]) for r in refs]


def offline(case=None):
    case = deepcopy(case or CASES[0])
    repo = MemoryRepository()
    policy = Mock(evaluate=AsyncMock(return_value=PolicyDecision(allowed=True)))
    provider = FixtureUnderstandingProvider(case["items"])
    extractor = UnderstandingExtractor(
        repository=repo, policy=policy, provider=provider
    )
    owner, scope = repo.subject_id, str(uuid4())
    ref = asyncio.run(
        extractor.import_conversation(
            subject_id=owner, context_id=scope, conversation=case["conversation"]
        )
    )
    checkpoint = asyncio.run(
        extractor.extract(
            subject_id=owner,
            context_id=scope,
            source_revision_id=ref,
            extraction_key="run-1",
        )
    )
    return repo, policy, provider, extractor, owner, scope, ref, checkpoint


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["name"])
def test_two_provider_implementations_and_exact_unicode_citations(case):
    repo, policy, provider, extractor, owner, scope, ref, cp = offline(case)
    assert isinstance(provider, LLMProvider)
    replay = ReplayLLMProvider(
        expected_request_sha256=request_hash(provider.last_request),
        response_json=provider.last_result.message.content,
    )
    assert isinstance(replay, LLMProvider)
    second = UnderstandingExtractor(repository=repo, policy=policy, provider=replay)
    cp2 = asyncio.run(
        second.extract(
            subject_id=owner,
            context_id=scope,
            source_revision_id=ref,
            extraction_key="run-1",
        )
    )
    assert cp2 == cp
    ids = asyncio.run(second.publish(subject_id=owner, checkpoint=cp2))
    assert len(ids) == 6 and len(set(ids)) == 6
    assert {r["type_id"] for r in repo.revisions} == {
        "qh.generic." + shape for shape in ("item", "entity", "relation")
    }
    for r in repo.revisions:
        assert r["validation_state"] == "proposed" and r["origin_kind"] == "ai"
        for e in r["content"]["citations"]:
            assert repo.sources[ref]["content"][e["start"] : e["end"]] == e["quote"]
    # Offline publication invokes neither adapter again.
    assert asyncio.run(second.publish(subject_id=owner, checkpoint=cp2)) == ids
    assert provider.calls == replay.calls == 1
    changed = deepcopy(provider.last_request)
    with pytest.raises(ValueError, match="fingerprint"):
        asyncio.run(
            ReplayLLMProvider(
                expected_request_sha256="wrong", response_json="{}"
            ).generate(changed)
        )


BAD = [
    "missing",
    "duplicate",
    "shape",
    "empty_text",
    "state",
    "owner",
    "type",
    "category",
    "false_quote",
    "negative",
    "reversed",
    "boolean_offset",
    "byte_offset",
    "foreign_source",
    "missing_evidence",
    "turn_boundary",
    "missing_endpoint",
    "foreign_endpoint",
    "relation_on_item",
    "bad_certainty",
    "string_descriptor",
    "missing_certainty",
    "null_properties",
    "unbacked_time",
    "naive_time",
    "reversed_time",
    "validity_empty",
    "fingerprint",
    "version",
]


def corrupt(cp, mode):
    item = cp["output"]["items"][0]
    evidence = item["evidence"][0]
    if mode == "missing":
        del item["local_id"]
    elif mode == "duplicate":
        cp["output"]["items"][1]["local_id"] = item["local_id"]
    elif mode == "shape":
        item["shape"] = "decision"
    elif mode == "empty_text":
        item["text"] = ""
    elif mode in ("state", "owner", "type", "category"):
        item[mode] = "forbidden"
    elif mode == "false_quote":
        evidence["quote"] = "invented"
    elif mode == "negative":
        evidence["start"] = -1
    elif mode == "reversed":
        evidence["end"] = evidence["start"]
    elif mode == "boolean_offset":
        evidence["start"] = True
    elif mode == "byte_offset":
        evidence["end"] += 3
    elif mode == "foreign_source":
        evidence["source_revision_id"] = str(uuid4())
    elif mode == "missing_evidence":
        item["evidence"] = []
    elif mode == "turn_boundary":
        evidence.update(start=0, end=1, quote="A")
    elif mode == "missing_endpoint":
        del cp["output"]["items"][-1]["relation"]["target"]
    elif mode == "foreign_endpoint":
        cp["output"]["items"][-1]["relation"]["target"] = str(uuid4())
    elif mode == "relation_on_item":
        item["relation"] = {
            "source": "choice",
            "target": "participant",
            "predicate": "x",
        }
    elif mode == "bad_certainty":
        item["descriptors"][0]["certainty"] = "confirmed"
    elif mode == "string_descriptor":
        item["descriptors"] = ["decision"]
    elif mode == "missing_certainty":
        del item["descriptors"][0]["certainty"]
    elif mode == "null_properties":
        item["properties"] = None
    elif mode == "unbacked_time":
        item["temporal"] = {"fact_from": "2030-01-01T00:00:00Z"}
    elif mode == "naive_time":
        item["temporal"] = {"fact_from": "2026-10-01T12:00:00"}
    elif mode in ("reversed_time", "validity_empty"):
        # Existing literal timestamp is copied into evidence for the temporal item.
        item = cp["output"]["items"][3]
        item["temporal"] = (
            {"valid_from": "2026-10-01T12:00:00Z", "valid_to": "2026-10-01T12:00:00Z"}
            if mode == "validity_empty"
            else {
                "fact_from": "2026-10-01T12:00:00Z",
                "fact_to": "2026-09-01T12:00:00Z",
            }
        )
    elif mode == "fingerprint":
        cp["input_sha256"] = "changed"
    elif mode == "version":
        cp["version"] = True


@pytest.mark.parametrize("mode", BAD)
def test_invalid_checkpoint_never_reaches_publication(mode):
    repo, _, provider, extractor, owner, _, ref, cp = offline()
    corrupt(cp, mode)
    with pytest.raises((ValueError, PermissionError)):
        asyncio.run(extractor.publish(subject_id=owner, checkpoint=cp))
    assert not repo.revisions and ref in repo.sources and provider.calls == 1


@pytest.mark.parametrize(
    "raw", ['{"items":[],"items":[]}', '{"items":NaN}', "```json\n{}\n```", "[]", "{"]
)
def test_malformed_provider_response_never_publishes(raw):
    repo, _, provider, extractor, owner, scope, ref, _ = offline()
    provider.generate = AsyncMock(
        return_value=GenerationResult(
            message=Message(role=MessageRole.ASSISTANT, content=raw)
        )
    )
    with pytest.raises(ValueError):
        asyncio.run(
            extractor.extract(
                subject_id=owner,
                context_id=scope,
                source_revision_id=ref,
                extraction_key="bad",
            )
        )
    assert not repo.revisions and len(repo.sources) == 1


def test_denial_precedes_source_access_provider_and_write():
    repo, policy, provider, extractor, owner, scope, ref, cp = offline()
    repo.read_sources = Mock(side_effect=AssertionError("private read"))
    repo.save = Mock(side_effect=AssertionError("private write"))
    policy.evaluate = AsyncMock(return_value=PolicyDecision(allowed=False))
    for operation in (
        extractor.extract(
            subject_id=owner,
            context_id=scope,
            source_revision_id=ref,
            extraction_key="deny",
        ),
        extractor.publish(subject_id=owner, checkpoint=cp),
        extractor.import_conversation(
            subject_id=owner, context_id=scope, conversation=CASES[0]["conversation"]
        ),
    ):
        with pytest.raises(PermissionError):
            asyncio.run(operation)
    assert provider.calls == 1
    repo.read_sources.assert_not_called()
    repo.save.assert_not_called()
    with pytest.raises(PermissionError):
        asyncio.run(
            extractor.extract(
                subject_id=str(uuid4()),
                context_id=scope,
                source_revision_id=ref,
                extraction_key="deny",
            )
        )


def test_decoder_bounds_and_supported_literal_temporal_assertion():
    with pytest.raises(ValueError):
        decode_output(" " * 1_000_001)
    repo, _, _, extractor, owner, _, _, cp = offline()
    cp["output"]["items"][3]["temporal"] = {
        "fact_from": "2026-10-01T12:00:00Z",
        "fact_to": "2026-10-01T12:00:00Z",
    }
    asyncio.run(extractor.publish(subject_id=owner, checkpoint=cp))
    assert repo.revisions[3]["fact_from"] == "2026-10-01T12:00:00Z"
    assert "fact_from" not in repo.revisions[0]  # Acquisition is not semantic time.


def test_provider_failure_keeps_source_and_has_no_hidden_retry():
    repo, _, provider, extractor, owner, scope, ref, _ = offline()
    provider.generate = AsyncMock(side_effect=ConnectionError("synthetic failure"))
    with pytest.raises(ConnectionError):
        asyncio.run(
            extractor.extract(
                subject_id=owner,
                context_id=scope,
                source_revision_id=ref,
                extraction_key="failure",
            )
        )
    provider.generate.assert_awaited_once()
    assert ref in repo.sources and not repo.revisions


@pytest.mark.parametrize(
    "mode", ["few_turns", "duplicate_turn", "bad_revision", "bad_time", "unknown_field"]
)
def test_invalid_import_never_stores_source(mode):
    repo, _, _, extractor, owner, scope, _, _ = offline()
    conversation = deepcopy(CASES[0]["conversation"])
    if mode == "few_turns":
        conversation["turns"] = conversation["turns"][:2]
    elif mode == "duplicate_turn":
        conversation["turns"][1]["id"] = conversation["turns"][0]["id"]
    elif mode == "bad_revision":
        conversation["revision_no"] = True
    elif mode == "bad_time":
        conversation["acquired_at"] = "2026-10-15"
    else:
        conversation["owner"] = "forbidden"
    before = deepcopy(repo.sources)
    with pytest.raises(ValueError):
        asyncio.run(
            extractor.import_conversation(
                subject_id=owner, context_id=scope, conversation=conversation
            )
        )
    assert repo.sources == before


def test_temporal_ordering_with_two_actually_cited_bounds():
    case = deepcopy(CASES[0])
    original = case["conversation"]["turns"][2]["text"]
    text = original + " Previous timestamp 2026-09-01T12:00:00Z."
    case["conversation"]["turns"][2]["text"] = text
    for item in case["items"]:
        for e in item["evidence"]:
            if e["quote"] == original:
                e["quote"] = text
    repo, _, _, extractor, owner, _, _, cp = offline(case)
    cp["output"]["items"][3]["temporal"] = {
        "fact_from": "2026-10-01T12:00:00Z",
        "fact_to": "2026-09-01T12:00:00Z",
    }
    with pytest.raises(ValueError, match="time bounds"):
        asyncio.run(extractor.publish(subject_id=owner, checkpoint=cp))
    assert not repo.revisions
