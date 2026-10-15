"""Adapter-local error metadata; never logs payloads or exception messages."""

from contextvars import ContextVar
from dataclasses import asdict, dataclass
import json

from neo4j.exceptions import DriverError, Neo4jError
from pydantic import ValidationError

llm_phase: ContextVar[str] = ContextVar('qh_llm_phase', default='unknown')


@dataclass(frozen=True)
class FailureDiagnostic:
    category: str
    phase: str
    exception_types: tuple[str, ...]

    def as_dict(self):
        return asdict(self)


class StageError(RuntimeError):
    def __init__(self, category: str, phase: str):
        super().__init__('Semantic adapter stage failed')
        self.category = category
        self.phase = phase


def describe_failure(error: BaseException, phase: str, *, llm: bool = False) -> FailureDiagnostic:
    chain = []
    current = error
    while current is not None and id(current) not in {id(e) for e in chain}:
        chain.append(current)
        current = current.__cause__
    # Explicit classifications survive optional Graphiti stages swallowing errors.
    for item in chain:
        if isinstance(item, StageError):
            return FailureDiagnostic(item.category, item.phase, tuple(type(e).__name__ for e in chain))
    from adapters.context.quality import ExtractionQualityError
    category = 'graphiti_internal'
    if any(isinstance(e, ExtractionQualityError) for e in chain):
        category = 'qh_consistency'
        phase = next((getattr(e, 'phase', phase) for e in chain if isinstance(e, ExtractionQualityError)), phase)
    elif any(isinstance(e, (Neo4jError, DriverError)) for e in chain):
        category = 'neo4j_persistence'
    elif llm and any(isinstance(e, json.JSONDecodeError) for e in chain):
        category = 'llm_parsing'
    elif llm and any(isinstance(e, ValidationError) for e in chain):
        category = 'llm_schema'
    return FailureDiagnostic(category, phase, tuple(type(e).__name__ for e in chain))
