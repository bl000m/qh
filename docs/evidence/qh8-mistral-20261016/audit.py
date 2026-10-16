"""Recompute deterministic metrics offline; never imports a provider or edits outputs."""
import json
from decimal import Decimal
from pathlib import Path

root = Path(__file__).resolve().parent
rows = []
for case in ("work", "evolving", "personal", "multilingual"):
    folder = root / case
    capture = json.loads((folder / "raw.json").read_text())
    output = json.loads(capture["response"]["choices"][0]["message"]["content"])
    assert (folder / "output.json").read_text() == capture["response"]["choices"][0]["message"]["content"]
    assert json.loads((folder / "understanding-candidates.json").read_text()) == output["items"]
    source = json.loads((folder / "source.json").read_text())
    evidence = [e for i in output["items"] for e in i.get("evidence", [])]
    usage = capture["response"]["usage"]
    cached = usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)
    charge = (Decimal(usage["prompt_tokens"]) * Decimal("0.15") + Decimal(usage["completion_tokens"]) * Decimal("0.60")) / 1_000_000
    cache_charge = charge - Decimal(cached) * Decimal("0.135") / 1_000_000
    rows.append(dict(
        case=case, http_status=capture["http_status"],
        input_tokens=usage["prompt_tokens"], output_tokens=usage["completion_tokens"],
        calculated_uncached_upper_usd=str(charge), calculated_cache_aware_usd=str(cache_charge),
        cached_input_tokens=cached, invoiced_cost=None,
        latency_seconds=capture["latency_seconds"], candidates=len(output["items"]),
        citations=len(evidence),
        exact_spans=sum(source["content"][e["start"]:e["end"]] == e["quote"] for e in evidence),
        literal_quotes=sum(e["quote"] in source["content"] for e in evidence),
        source_ids_correct=sum(e["source_revision_id"] == source["id"] for e in evidence),
        items_missing_evidence=[i["local_id"] for i in output["items"] if not i.get("evidence")],
        temporal_items=sum(bool(i.get("temporal")) for i in output["items"]),
    ))
ledger = json.loads((root / "ledger-after.json").read_text())
before = json.loads((root / "ledger-before.json").read_text())
assert ledger["calls"][:len(before["calls"])] == before["calls"]
assert len(ledger["calls"]) == 7
metrics = dict(
    requests_this_resumption=4, cumulative_requests=len(ledger["calls"]), max_requests=8,
    max_usd="0.20", uncertain_prior_hold_usd="0.012",
    observed_input_tokens=sum(r["input_tokens"] for r in rows),
    observed_output_tokens=sum(r["output_tokens"] for r in rows),
    observed_cached_input_tokens=sum(r["cached_input_tokens"] for r in rows),
    calculated_uncached_upper_usd=str(sum(Decimal(r["calculated_uncached_upper_usd"]) for r in rows)),
    calculated_cache_aware_usd=str(sum(Decimal(r["calculated_cache_aware_usd"]) for r in rows)),
    cases=rows,
)
print(json.dumps(metrics, indent=2))
