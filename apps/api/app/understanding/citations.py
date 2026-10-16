"""Exact source-backed quote location; no inference, normalization or publication.

The caller must first authorize/read the immutable source revision. Provider offsets
are untrusted hints and never resolve ambiguous text. Output is derived separately;
any missing/foreign/ambiguous evidence rejects the entire derivation.
"""

from copy import deepcopy
import hashlib

VERSION = "qh-citation-resolver/1"


class CitationResolutionError(ValueError):
    def __init__(self, issues):
        self.issues = tuple(issues)
        super().__init__("Citation resolution rejected the batch")


def resolve_output_citations(output, *, source):
    if (
        not isinstance(output, dict)
        or set(output) != {"items"}
        or not isinstance(output["items"], list)
        or not 1 <= len(output["items"]) <= 100
    ):
        raise ValueError("Bounded candidate envelope required")
    text = source.get("content")
    turns = source.get("origin", {}).get("turns")
    if (
        not isinstance(text, str)
        or len(text.encode()) > 1_000_000
        or not isinstance(source.get("id"), str)
        or not isinstance(turns, list)
        or not 1 <= len(turns) <= 100
    ):
        raise ValueError("Original source and bounded identified turns required")
    previous_end, seen = 0, set()
    for turn in turns:
        if (
            not isinstance(turn, dict)
            or not isinstance(turn.get("turn_id"), str)
            or not turn["turn_id"]
            or turn["turn_id"] in seen
            or type(turn.get("start")) is not int
            or type(turn.get("end")) is not int
            or not previous_end <= turn["start"] < turn["end"] <= len(text)
        ):
            raise ValueError("Distinct ordered original turn bounds required")
        previous_end = turn["end"]
        seen.add(turn["turn_id"])

    issues, resolved, cache = [], [], {}
    for index, item in enumerate(output["items"]):
        if not isinstance(item, dict):
            issues.append(dict(item_index=index, code="invalid_candidate"))
            continue
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not 1 <= len(evidence) <= 100:
            issues.append(dict(item_index=index, code="missing_or_invalid_evidence"))
            continue
        for evidence_index, ref in enumerate(evidence):
            issue = dict(item_index=index, evidence_index=evidence_index)
            if (
                not isinstance(ref, dict)
                or not {"source_revision_id", "quote"} <= ref.keys()
                or ref.keys() - {"source_revision_id", "quote", "start", "end"}
            ):
                issues.append({**issue, "code": "invalid_evidence_fields"})
                continue
            if ref["source_revision_id"] != source["id"]:
                issues.append({**issue, "code": "foreign_source_revision"})
                continue
            quote = ref["quote"]
            if (
                not isinstance(quote, str)
                or not quote
                or len(quote.encode()) > 1_000_000
            ):
                issues.append({**issue, "code": "missing_or_invalid_quote"})
                continue
            if quote not in cache:
                matches = []
                for turn in turns:
                    offset = turn["start"]
                    while len(matches) < 2:
                        start = text.find(quote, offset, turn["end"])
                        if start == -1:
                            break
                        matches.append((start, start + len(quote), turn["turn_id"]))
                        offset = (
                            start + 1
                        )  # Count overlapping occurrences as ambiguous.
                    if len(matches) == 2:
                        break
                cache[quote] = matches
            matches = cache[quote]
            if len(matches) != 1:
                issues.append(
                    {
                        **issue,
                        "code": "ambiguous_quote"
                        if matches
                        else "quote_not_in_original_turns",
                    }
                )
                continue
            start, end, turn_id = matches[0]
            resolved.append(
                dict(
                    item_index=index,
                    evidence_index=evidence_index,
                    source_revision_id=source["id"],
                    turn_id=turn_id,
                    original={k: ref[k] for k in ("start", "end") if k in ref},
                    derived=dict(start=start, end=end),
                    changed=type(ref.get("start")) is not int
                    or type(ref.get("end")) is not int
                    or ref.get("start") != start
                    or ref.get("end") != end,
                    quote_sha256=hashlib.sha256(quote.encode()).hexdigest(),
                )
            )
    if issues:
        raise CitationResolutionError(issues)
    derived = deepcopy(output)
    for record in resolved:
        derived["items"][record["item_index"]]["evidence"][
            record["evidence_index"]
        ].update(record["derived"])
    return derived, dict(version=VERSION, citations=resolved)
