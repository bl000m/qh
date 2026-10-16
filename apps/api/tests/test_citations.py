"""Original frozen captures and adversarial locators; no external inference."""

import asyncio
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from adapters.llm.offline import ReplayLLMProvider
from app.policy.models import PolicyDecision
from app.understanding.citations import (
    CitationResolutionError,
    resolve_output_citations,
)
from app.understanding.extractor import UnderstandingExtractor, decode_output
from tests.test_understanding import MemoryRepository

CAPTURES = Path(__file__).resolve().parents[3] / "docs/evidence/qh8-mistral-20261016"


def frozen(case):
    folder = CAPTURES / case
    capture = json.loads((folder / "raw.json").read_text())
    source = json.loads((folder / "source.json").read_text())
    repo = MemoryRepository()
    repo.sources[source["id"]] = source
    policy = Mock(evaluate=AsyncMock(return_value=PolicyDecision(allowed=True)))
    provider = ReplayLLMProvider(
        expected_request_sha256=capture["request_sha256"],
        response_json=capture["response"]["choices"][0]["message"]["content"],
    )
    extractor = UnderstandingExtractor(
        repository=repo, policy=policy, provider=provider
    )
    cp = dict(
        version=1,
        context_space_id=source["context_space_id"],
        source_revision_id=source["id"],
        input_sha256=extractor.source_hash(source),
        extraction_key="mistral-initial-v1",
        output=decode_output(provider.response_json),
    )
    return repo, policy, provider, extractor, cp


@pytest.mark.parametrize(
    "case,count,changed",
    [("work", 9, 5), ("evolving", 14, 6), ("personal", 5, 0), ("multilingual", 0, 0)],
)
def test_frozen_originals_then_explicit_derived_replay(case, count, changed):
    repo, _, provider, extractor, cp = frozen(case)
    original = deepcopy(cp)
    operation = extractor.extract(
        subject_id=repo.subject_id,
        context_id=cp["context_space_id"],
        source_revision_id=cp["source_revision_id"],
        extraction_key=cp["extraction_key"],
    )
    if case == "personal":
        assert asyncio.run(operation) == cp
    else:
        with pytest.raises(ValueError):
            asyncio.run(operation)
    assert provider.calls == 1  # Exact request fingerprint checked by replay adapter.
    resolve = extractor.resolve_citations(
        subject_id=repo.subject_id, checkpoint=cp, extraction_key="derived-v1"
    )
    if case == "multilingual":
        with pytest.raises(CitationResolutionError) as error:
            asyncio.run(resolve)
        assert [i["item_index"] for i in error.value.issues] == [6, 7, 8]
        assert not repo.revisions
    else:
        derived, audit = asyncio.run(resolve)
        assert sum(r["changed"] for r in audit["citations"]) == changed
        assert not repo.revisions  # Resolution never writes.
        without_offsets = deepcopy(derived["output"])
        for item, original_item in zip(
            without_offsets["items"], cp["output"]["items"], strict=True
        ):
            for ref, original_ref in zip(
                item["evidence"], original_item["evidence"], strict=True
            ):
                ref.update({k: original_ref[k] for k in ("start", "end")})
        assert without_offsets == cp["output"]
        ids = asyncio.run(
            extractor.publish(subject_id=repo.subject_id, checkpoint=derived)
        )
        assert len(ids) == count
        assert (
            asyncio.run(
                extractor.publish(subject_id=repo.subject_id, checkpoint=derived)
            )
            == ids
        )
        assert all(r["validation_state"] == "proposed" for r in repo.revisions)
        for row in repo.revisions:
            for e in row["content"]["citations"]:
                assert (
                    repo.sources[cp["source_revision_id"]]["content"][
                        e["start"] : e["end"]
                    ]
                    == e["quote"]
                )
    assert cp == original and provider.calls == 1


def example(text="é🙂 e\u0301", quote="🙂 e\u0301"):
    source = dict(
        id="original",
        content="N: " + text + "\n",
        origin={"turns": [dict(turn_id="t1", start=3, end=3 + len(text))]},
    )
    output = {
        "items": [
            dict(
                local_id="one",
                shape="item",
                text="unchanged assertion",
                properties={"hypothetical": True},
                evidence=[
                    dict(source_revision_id="original", quote=quote, start=-50, end=999)
                ],
            )
        ]
    }
    return source, output


def test_unicode_code_points_and_missing_offsets_without_normalization():
    source, output = example()
    original = deepcopy(output)
    del output["items"][0]["evidence"][0]["start"]
    del output["items"][0]["evidence"][0]["end"]
    derived, audit = resolve_output_citations(output, source=source)
    ref = derived["items"][0]["evidence"][0]
    assert ref["start"] == 4 and ref["end"] == 8
    assert source["content"][4:8] == "🙂 e\u0301"
    assert derived["items"][0]["properties"] == original["items"][0]["properties"]
    assert audit["citations"][0]["changed"]
    assert "start" not in output["items"][0]["evidence"][0]


@pytest.mark.parametrize(
    "text,quote",
    [
        ("aaaa", "aa"),
        ("oui oui", "oui"),
        ("e\u0301", "é"),
        ("text", "invented"),
        ("text", "N:"),
    ],
)
def test_ambiguous_absent_or_normalized_quote_fails_closed(text, quote):
    source, output = example(text, quote)
    before = deepcopy(output)
    with pytest.raises(CitationResolutionError):
        resolve_output_citations(output, source=source)
    assert output == before


def test_valid_provider_offsets_do_not_disambiguate_repeated_turns():
    source, output = example("same", "same")
    source["content"] += "M: same\n"
    source["origin"]["turns"].append(dict(turn_id="t2", start=11, end=15))
    output["items"][0]["evidence"][0].update(start=3, end=7)
    with pytest.raises(CitationResolutionError, match="rejected"):
        resolve_output_citations(output, source=source)


def test_cross_turn_quote_and_foreign_source_are_never_repaired():
    source, output = example("first", "first\nM: second")
    source["content"] += "M: second\n"
    source["origin"]["turns"].append(dict(turn_id="t2", start=12, end=18))
    with pytest.raises(CitationResolutionError):
        resolve_output_citations(output, source=source)
    output["items"][0]["evidence"][0].update(
        quote="first", source_revision_id="foreign"
    )
    with pytest.raises(CitationResolutionError) as error:
        resolve_output_citations(output, source=source)
    assert error.value.issues[0]["code"] == "foreign_source_revision"


def test_one_missing_citation_rejects_whole_derivation_and_changes_nothing():
    source, output = example()
    output["items"].append(dict(local_id="two", shape="relation", text="no evidence"))
    before = deepcopy(output)
    with pytest.raises(CitationResolutionError):
        resolve_output_citations(output, source=source)
    assert output == before


def test_resolution_denial_precedes_private_reads_and_never_calls_provider():
    repo, policy, provider, extractor, cp = frozen("work")
    policy.evaluate = AsyncMock(return_value=PolicyDecision(allowed=False))
    repo.read_sources = Mock(side_effect=AssertionError("private read"))
    repo.save = Mock(side_effect=AssertionError("write"))
    with pytest.raises(PermissionError):
        asyncio.run(
            extractor.resolve_citations(
                subject_id=repo.subject_id, checkpoint=cp, extraction_key="derived"
            )
        )
    assert provider.calls == 0
    repo.read_sources.assert_not_called()
    repo.save.assert_not_called()


@pytest.mark.parametrize("mode", ["fingerprint", "scope", "key", "endpoint"])
def test_derivation_does_not_bypass_fingerprint_scope_key_or_relation_validation(mode):
    repo, _, provider, extractor, cp = frozen("work")
    key = "derived"
    if mode == "fingerprint":
        cp["input_sha256"] = "tampered"
    elif mode == "scope":
        cp["context_space_id"] = "another-scope"
    elif mode == "key":
        key = cp["extraction_key"]
    else:
        cp["output"]["items"][-1]["relation"]["target"] = "missing"
    with pytest.raises(ValueError):
        asyncio.run(
            extractor.resolve_citations(
                subject_id=repo.subject_id, checkpoint=cp, extraction_key=key
            )
        )
    assert not repo.revisions and provider.calls == 0


@pytest.mark.parametrize("mode", ["absent", "null", "empty"])
def test_absent_or_empty_quote_is_not_manufactured(mode):
    source, output = example()
    ref = output["items"][0]["evidence"][0]
    if mode == "absent":
        del ref["quote"]
    else:
        ref["quote"] = None if mode == "null" else ""
    before = deepcopy(output)
    with pytest.raises(CitationResolutionError):
        resolve_output_citations(output, source=source)
    assert output == before


def test_boolean_offset_hint_is_recorded_as_a_changed_type():
    source, output = example()
    source["content"] = "ab"
    source["origin"]["turns"] = [dict(turn_id="one", start=0, end=2)]
    output["items"][0]["evidence"][0].update(quote="b", start=True, end=2)
    derived, audit = resolve_output_citations(output, source=source)
    assert audit["citations"][0]["changed"]
    assert audit["citations"][0]["original"]["start"] is True
    assert type(derived["items"][0]["evidence"][0]["start"]) is int
