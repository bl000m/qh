"""Synthetic fixture assertions; never configure production extraction expectations."""

import re
from dataclasses import dataclass

from adapters.context.quality import ExtractionQualityError, SourceEvidence


@dataclass(frozen=True)
class SmokeFixture:
    text: str
    expected_entities: frozenset[str]
    undated: bool = True
    expected_facts: frozenset[str] = frozenset()

    def validate(self, evidence: SourceEvidence, phase: str, answer: dict):
        if evidence.text != self.text:
            raise ExtractionQualityError("Fixture/source mismatch")
        if phase == "extract_nodes.extract_text":
            actual = {entity["name"] for entity in answer["extracted_entities"]}
            if actual != self.expected_entities:
                raise ExtractionQualityError("Synthetic fixture entity coverage mismatch")
        if phase == "extract_edges.edge" and self.expected_facts:
            facts = {edge["fact"].strip().rstrip(".") for edge in answer["edges"]}
            if not facts or not facts <= self.expected_facts:
                raise ExtractionQualityError("Synthetic fixture fact grounding mismatch")
        if self.undated:
            rows = answer.get("edges", []) + answer.get("summaries", []) + answer.get("timestamps", [])
            if "valid_at" in answer or "invalid_at" in answer:
                rows += [answer]
            for row in rows:
                if row.get("valid_at") is not None or row.get("invalid_at") is not None:
                    raise ExtractionQualityError("Undated fixture has unsupported semantic time")
                text = row.get("fact", "") + " " + row.get("summary", "")
                # This oracle applies only to these explicitly undated synthetic
                # fixtures, never arbitrary production sources or technical metadata.
                if re.search(r"\d|\b(?:january|february|march|april|may|june|july|august|september|october|november|december|yesterday|today|tomorrow)\b", text, re.I):
                    raise ExtractionQualityError("Unsupported temporal/numeric claim in fixture")
