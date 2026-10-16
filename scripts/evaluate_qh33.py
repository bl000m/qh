"""Offline QH-33 judgment accounting/review packets, never semantic inference.

Default mode uses Python stdlib only. --probe-engine calls the existing extractor
on synthetic in-memory repositories; no provider, database or HTTP is involved.
"""

import argparse
import ast
import asyncio
from collections import Counter
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "apps/api/tests/fixtures/qh33/benchmark.json"
DIMENSIONS = (
    "coverage",
    "semantic",
    "attribution",
    "negation",
    "temporality",
    "uncertainty",
    "provenance",
)
RATINGS = {"pass", "partial", "fail", "n/a"}
KINDS = {"source_proposition", "extra_claim", "output_annotation", "control"}


def encoded(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON field")
            result[key] = value
        return result

    return json.loads(
        path.read_text(),
        object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")),
    )


def asset(spec, root):
    if set(spec) == {"inline", "sha256"}:
        value = spec["inline"]
        actual = digest(value)
    elif set(spec) == {"path", "sha256"}:
        path = (root / spec["path"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Asset outside repository")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        value = read_json(path)
    else:
        raise ValueError("Exact asset identity required")
    if actual != spec["sha256"]:
        raise ValueError("Benchmark asset fingerprint mismatch")
    return value


def pointer(value, path):
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValueError("JSON pointer required")
    for part in path[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def load_benchmark(path=BENCHMARK, root=ROOT):
    b = read_json(path)
    if (
        b["version"] != 1
        or b["reference_status"]
        != "assistant_proposal_pending_independent_human_review"
    ):
        raise ValueError("Explicit provisional benchmark required")
    cases = {}
    for case in b["cases"]:
        if case["id"] in cases:
            raise ValueError("Duplicate benchmark case")
        cases[case["id"]] = {
            "source": asset(case["source"], root),
            "output": asset(case["output"], root),
            "kind": case.get("kind", "frozen_mistral"),
        }
    ids = set()
    for u in b["units"]:
        if u["id"] in ids or u["kind"] not in KINDS:
            raise ValueError("Unique typed review units required")
        ids.add(u["id"])
        case = cases[u["case"]]
        e = u["source_evidence"]
        if (
            type(e["start"]) is not int
            or type(e["end"]) is not int
            or not 0 <= e["start"] < e["end"] <= len(case["source"]["content"])
        ):
            raise ValueError("Invalid source evidence bounds")
        if case["source"]["content"][e["start"] : e["end"]] != e["quote"] or not any(
            t["turn_id"] == e["turn_id"]
            and t["start"] <= e["start"] < e["end"] <= t["end"]
            for t in case["source"]["origin"]["turns"]
        ):
            raise ValueError("Review unit source locator mismatch")
        ratings = u["draft_ratings"]
        if set(ratings) != set(DIMENSIONS) or any(
            v not in RATINGS for v in ratings.values()
        ):
            raise ValueError("Explicit dimension ratings required")
        if ratings["coverage"] in {"pass", "partial"} and not u["anchors"]:
            raise ValueError("Coverage cannot count source/evidence-only retention")
        if not u["anchors"] and (
            u["kind"] != "source_proposition"
            or ratings["semantic"] != "n/a"
            or ratings["provenance"] != "n/a"
        ):
            raise ValueError("Absent output cannot be scored as a supported claim")
        for a in u["anchors"]:
            if "evidence" in a["pointer"].split("/"):
                raise ValueError("Evidence is not an extracted claim")
            if digest(pointer(case["output"], a["pointer"])) != a["value_sha256"]:
                raise ValueError("Review claim fingerprint mismatch")
    return b, cases


def summarize(units, ratings_by_id):
    groups = {}
    for kind in sorted(KINDS):
        group = [u for u in units if u["kind"] == kind]
        groups[kind] = {"units": len(group), "dimensions": {}}
        for dim in DIMENSIONS:
            counts = Counter(
                ratings_by_id.get(u["id"], {}).get(dim, "pending") for u in group
            )
            denominator = sum(counts[s] for s in ("pass", "partial", "fail"))
            groups[kind]["dimensions"][dim] = {
                **{s: counts[s] for s in ("pass", "partial", "fail", "n/a", "pending")},
                "assessed_denominator": denominator,
                "pass_fraction": counts["pass"] / denominator if denominator else None,
            }
    return groups


def locators(cases):
    counts = Counter()
    for case in cases.values():
        if case["kind"] != "frozen_mistral":
            continue
        source = case["source"]
        for item in case["output"]["items"]:
            counts["candidates"] += 1
            refs = item.get("evidence", [])
            if not refs:
                counts["candidates_missing_evidence"] += 1
            for e in refs:
                counts["supplied_citations"] += 1
                if (
                    e["source_revision_id"] == source["id"]
                    and source["content"][e["start"] : e["end"]] == e["quote"]
                ):
                    counts["exact_spans"] += 1
    return dict(counts)


def review_template(b):
    return {
        "benchmark_sha256": digest(b),
        "reviewer": None,
        "reviewed_at": None,
        "independent_of_assistant_author": None,
        "reference_completeness_checked": False,
        "candidate_payloads_checked": False,
        "units": [
            {
                "id": u["id"],
                "decision": "pending",
                "ratings": {d: None for d in DIMENSIONS},
                "notes": "",
            }
            for u in b["units"]
        ],
    }


def human_review(b, review):
    if review["benchmark_sha256"] != digest(b):
        raise ValueError("Stale review fingerprint")
    rows = {}
    expected = {u["id"]: u for u in b["units"]}
    for row in review["units"]:
        if row["id"] in rows or row["id"] not in expected:
            raise ValueError("Unknown/duplicate review unit")
        if (
            row["decision"] not in {"pending", "accept", "changes_requested"}
            or set(row["ratings"]) != set(DIMENSIONS)
            or any(v is not None and v not in RATINGS for v in row["ratings"].values())
        ):
            raise ValueError("Invalid review judgment")
        if row["decision"] == "accept":
            if any(v is None for v in row["ratings"].values()):
                raise ValueError("Accepted row requires complete dimension judgments")
            draft = expected[row["id"]]["draft_ratings"]
            if any(
                (draft[d] == "n/a") != (row["ratings"][d] == "n/a") for d in DIMENSIONS
            ):
                raise ValueError(
                    "Changed applicability requires a new benchmark revision"
                )
            rows[row["id"]] = row["ratings"]
        else:
            rows[row["id"]] = {}
    if set(rows) != set(expected):
        raise ValueError("Review must retain every unit")
    complete = all(row["decision"] == "accept" for row in review["units"])
    attested = (
        isinstance(review["reviewer"], str)
        and bool(review["reviewer"].strip())
        and isinstance(review["reviewed_at"], str)
        and bool(review["reviewed_at"].strip())
        and review["independent_of_assistant_author"] is True
        and review["reference_completeness_checked"] is True
        and review["candidate_payloads_checked"] is True
    )
    if attested:
        try:
            date = datetime.fromisoformat(review["reviewed_at"])
            if date.tzinfo is None:
                raise ValueError("Offset required")
        except ValueError as exc:
            raise ValueError("Explicit review timestamp required") from exc
    return {
        "status": "reviewer_declared_complete"
        if complete and attested
        else "pending_or_changes_requested",
        "identity_verified_by_tool": False,
        "metrics": summarize(b["units"], rows) if complete and attested else None,
        "accepted_units": sum(bool(v) for v in rows.values()),
        "required_units": len(expected),
    }


def evaluate(b, cases, review=None):
    return {
        "benchmark_sha256": digest(b),
        "reference_status": b["reference_status"],
        "method": "Arithmetic over explicit assistant draft judgments; no semantic classifier or model-quality claim",
        "provisional_assistant_metrics": summarize(
            b["units"], {u["id"]: u["draft_ratings"] for u in b["units"]}
        ),
        "original_locator_metrics": locators(cases),
        "human_review": human_review(b, review or review_template(b)),
        "new_inference_requests": 0,
        "limits": b["limits"],
    }


def packet(b, cases):
    text = [
        "# QH-33 independent review packet",
        "",
        "Draft reference, not human validation. First read source-only.md without consulting draft ratings; derive missing/extra propositions yourself. Then compare this proposal and review-template.json. Evidence-only text is not a claim. Full output payloads appear below, including fields not individually scored. No precision/recall against human truth exists yet.",
        "",
        "Approve/amend reference scope (including historical uncertainty) before rating outputs. pass = represented/supported; partial = incomplete/inconsistent; fail = absent/unsupported/wrong; n/a = not applicable. Keep coverage, meaning, agency, negation, event linkage, uncertainty and contextual support separate. Exact locator accuracy is mechanical and separate. Extra-claim inventory is targeted, not exhaustive. Use changes_requested for amended/split/extra reference units; create a new benchmark revision rather than scoring against silently changed expectations.",
        "",
    ]
    for case_id, case in cases.items():
        text += [
            "## " + case_id,
            "",
            "Source:",
            "",
            "```text",
            case["source"]["content"],
            "```",
            "",
            "Original/authored output:",
            "",
            "```json",
            json.dumps(case["output"], ensure_ascii=False, indent=2),
            "```",
            "",
        ]
        for u in b["units"]:
            if u["case"] == case_id:
                text += [
                    "- **" + u["id"] + "** (" + u["kind"] + "): " + u["meaning"],
                    "  Source turn: `"
                    + u["source_evidence"]["turn_id"]
                    + "`; claim pointers: "
                    + ", ".join(
                        a["pointer"]
                        for a in u["anchors"]
                        or [{"pointer": "none — omission proposed"}]
                    )
                    + ". Human decision/ratings: **pending**.",
                ]
        text.append("")
    return "\n".join(text) + "\n"


def probe_engine(b, cases, label):
    sys.path.insert(0, str(ROOT / "apps/api"))
    from app.understanding import extractor as module

    class Memory:
        subject_id = "11111111-1111-4111-8111-111111111111"

        def __init__(self, source):
            self.source, self.revisions = source, []

        def read_sources(self, scopes, refs):
            if scopes != (self.source["context_space_id"],) or refs != (
                self.source["id"],
            ):
                raise ValueError("Synthetic scope mismatch")
            return [deepcopy(self.source)]

        def save(self, *, revisions):
            self.revisions = deepcopy(revisions)

    class Policy:
        async def evaluate(self, request):
            return SimpleNamespace(allowed=True)

    class NoProvider:
        async def generate(self, request):
            raise AssertionError("Provider must never be invoked")

    def attempt(source, output, resolve=False):
        repo = Memory(source)
        engine = module.UnderstandingExtractor(
            repository=repo, policy=Policy(), provider=NoProvider()
        )
        cp = dict(
            version=1,
            context_space_id=source["context_space_id"],
            source_revision_id=source["id"],
            input_sha256=engine.source_hash(source),
            extraction_key="qh33.original",
            output=deepcopy(output),
        )
        try:
            if resolve:
                cp, _ = asyncio.run(
                    engine.resolve_citations(
                        subject_id=repo.subject_id,
                        checkpoint=cp,
                        extraction_key="qh33.derived",
                    )
                )
            asyncio.run(engine.publish(subject_id=repo.subject_id, checkpoint=cp))
            return {
                "accepted": True,
                "revisions": len(repo.revisions),
                "all_proposed": all(
                    r["validation_state"] == "proposed" for r in repo.revisions
                ),
            }
        except ValueError:
            if repo.revisions:
                raise AssertionError("Partial batch publication")
            return {"accepted": False, "revisions": 0, "source_retained": True}

    results = {
        name: {
            "original": attempt(c["source"], c["output"]),
            "resolved": attempt(c["source"], c["output"], True),
        }
        for name, c in cases.items()
    }
    temporal = []
    for test in read_json(ROOT / "apps/api/tests/fixtures/qh33/temporal-probes.json"):
        text = "Recorded timestamp: " + test["source"] + "."
        source = {
            "id": str(uuid5(NAMESPACE_URL, test["id"])),
            "source_id": str(uuid5(NAMESPACE_URL, "source" + test["id"])),
            "context_space_id": Memory.subject_id,
            "revision_no": 1,
            "content": text,
            "origin": {"turns": [{"turn_id": "literal", "start": 0, "end": len(text)}]},
        }
        evidence = [
            {
                "source_revision_id": source["id"],
                "start": 0,
                "end": len(text),
                "quote": text,
            }
        ]
        output = {
            "items": [
                {
                    "local_id": "sibling",
                    "shape": "item",
                    "text": "Synthetic valid sibling",
                    "evidence": evidence,
                },
                {
                    "local_id": "time",
                    "shape": "item",
                    "text": "Reported event marker",
                    "evidence": evidence,
                    "temporal": {"fact_from": test["bound"]},
                },
            ]
        }
        temporal.append(
            {
                "id": test["id"],
                "expected_accept": test["valid"],
                **attempt(source, output),
            }
        )
    return {
        "label": label,
        "benchmark_sha256": digest(b),
        "temporal_probes_sha256": hashlib.sha256(
            (ROOT / "apps/api/tests/fixtures/qh33/temporal-probes.json").read_bytes()
        ).hexdigest(),
        "extractor_sha256": hashlib.sha256(
            Path(module.__file__).read_bytes()
        ).hexdigest(),
        "publication": "in-memory; not SQL integration evidence",
        "provider_calls": 0,
        "cases": results,
        "temporal_literal_probes": temporal,
    }


def future_protocol(cases):
    tree = ast.parse((ROOT / "apps/api/app/understanding/extractor.py").read_text())
    baseline = next(
        ast.literal_eval(n.value)
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "INSTRUCTIONS" for t in n.targets)
    )
    suffix = (
        ROOT / "docs/evidence/qh33-semantic-20261016/prompt-candidate.txt"
    ).read_text()
    requests = []
    for case_id in ["evolving", "multilingual", "control.actual_discount_fr.good"]:
        source = cases[case_id]["source"]
        fingerprint = digest(
            {
                k: source[k]
                for k in (
                    "id",
                    "source_id",
                    "context_space_id",
                    "revision_no",
                    "content",
                    "origin",
                )
            }
        )
        user = encoded(
            dict(
                source_revision_id=source["id"],
                input_sha256=fingerprint,
                text=source["content"],
                turns=source["origin"]["turns"],
            )
        ).decode()
        for version, instruction in [
            ("baseline", baseline),
            ("candidate", baseline + "\n" + suffix),
        ]:
            messages = [
                {"role": "system", "content": instruction},
                {"role": "user", "content": user},
            ]
            bound = sum(len(m["content"].encode()) + 256 for m in messages)
            if bound > 16000:
                raise ValueError("Prepared request exceeds existing input cap")
            payload = dict(
                model="mistral-small-2603",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0,
                random_seed=42,
                max_tokens=6000,
                stream=False,
                n=1,
                tool_choice="none",
            )
            requests.append(
                dict(
                    case=case_id,
                    prompt=version,
                    conservative_input_bound=bound,
                    payload=payload,
                    payload_sha256=digest(payload),
                )
            )
    return dict(
        status="NOT AUTHORIZED / NOT EXECUTED",
        provider="Mistral",
        endpoint="POST https://api.mistral.ai/v1/chat/completions",
        max_total_requests=8,
        max_generations=6,
        max_metadata_requests=1,
        max_input_tokens=16000,
        max_output_tokens=6000,
        max_usd="0.05",
        conservative_generation_reservation_usd="0.036",
        pricing_basis="Frozen 2026-10-16 experiment rates: USD 0.15/M input and 0.60/M output, uncached. Estimate only; verify current prices/model/workspace before requesting authorization.",
        original_ledger="Unchanged original experiment, 7/8. Never resume/reset it for this proposal. A distinct future experiment/ledger requires explicit scoped authorization; aggregate history must remain linked.",
        gates=[
            "Independent human reference and rubric approval first",
            "Explicit provider/data/request/token/budget authorization",
            "Single sequential request, no retry/fallback/parallel calls",
            "Stop on error/429/truncation/model/cost mismatch",
            "Same sources/model/seed/format, only system-prompt suffix differs",
            "No labels/reference/rating fields in outgoing payload",
            "Record observed usage/latency separately from calculated charges",
            "Three diagnostic pairs only; four original cases and controls remain offline benchmark, no population/generalization claim",
        ],
        requests=requests,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--probe-engine", action="store_true")
    parser.add_argument("--prepare-protocol", action="store_true")
    parser.add_argument("--label", default="current")
    args = parser.parse_args()
    b, cases = load_benchmark()
    result = evaluate(b, cases, read_json(args.review) if args.review else None)
    args.out.mkdir(parents=True, exist_ok=False)

    def write(name, value):
        (args.out / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        )

    write("metrics.json", result)
    write("review-template.json", review_template(b))
    (args.out / "review-packet.md").write_text(packet(b, cases))
    seen = set()
    blind = [
        "# QH-33 source-only review",
        "",
        "Read sources first; list your own propositions/actors/negations/times/uncertainties before looking at the assistant draft. Do not treat assistant labels as human truth.",
        "",
    ]
    for name, c in cases.items():
        key = digest(c["source"])
        if key not in seen:
            blind += [
                "## " + name,
                "",
                "```text",
                c["source"]["content"],
                "```",
                "",
                "Your proposition inventory / missing information / notes: __________________",
                "",
            ]
            seen.add(key)
    (args.out / "source-only.md").write_text("\n".join(blind) + "\n")
    if args.probe_engine:
        write("engine-probes.json", probe_engine(b, cases, args.label))
    if args.prepare_protocol:
        write("future-protocol.json", future_protocol(cases))
    print(
        json.dumps(
            {
                "units": len(b["units"]),
                "output": str(args.out),
                "human_validation": "pending unless explicitly supplied/reviewer-declared; never inferred",
                "provider_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
