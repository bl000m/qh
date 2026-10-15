"""Request-scoped extraction integrity, independent of QH human validation."""

from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable


class ExtractionQualityError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceEvidence:
    text: str
    reference_time: datetime  # Technical episode metadata, not a semantic assertion.


Observer = Callable[[SourceEvidence, str, dict], None]


@dataclass
class ExtractionSession:
    evidence: SourceEvidence
    observer: Observer | None = None
    entities: set[str] = field(default_factory=set)
    failure: str | None = None

    def check(self):
        if self.failure:
            raise ExtractionQualityError(self.failure)

    def reject(self, reason):
        self.failure = reason
        self.check()

    def validate(self, phase: str, answer: dict):
        self.check()
        try:
            if phase == "extract_nodes.extract_text":
                self.entities = {item["name"] for item in answer["extracted_entities"] if item["name"].strip()}
            if phase == "extract_edges.edge":
                for edge in answer["edges"]:
                    if not {edge["source_entity_name"], edge["target_entity_name"]} <= self.entities:
                        self.reject("Edge references unavailable extracted entities")
            for item in answer.get("extracted_entities", []) + answer.get("edges", []):
                if any(index != 0 for index in item.get("episode_indices", [0])):
                    self.reject("Source episode reference outside the ingestion scope")
            # Validate typed semantic timestamps without guessing whether arbitrary
            # source language (relative dates, aliases, paraphrases) supports them.
            dated = answer.get("edges", []) + answer.get("timestamps", [])
            if "valid_at" in answer or "invalid_at" in answer:
                dated = dated + [answer]
            for item in dated:
                for key in ("valid_at", "invalid_at"):
                    value = item.get(key)
                    if value is not None:
                        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                        if parsed.tzinfo is None or parsed.utcoffset() is None:
                            self.reject("Semantic timestamp must include a timezone")
            if self.observer:
                self.observer(self.evidence, phase, answer)
        except Exception as exc:
            if self.failure is None:
                self.failure = "Extraction validation failed: " + type(exc).__name__
            raise ExtractionQualityError(self.failure) from None


active_extraction: ContextVar[ExtractionSession | None] = ContextVar("qh_extraction", default=None)
