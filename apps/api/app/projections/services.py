from typing import Protocol, runtime_checkable

from app.projections.models import ContextProjection, ProjectionRequest


@runtime_checkable
class ProjectionService(Protocol):
    """Project already-authorized hits into text with exact revision references.

    The caller is responsible for authorized input. Implementations must not
    retrieve graph data, invoke an LLM or import transport serializers here.
    Formatting and redaction behavior belong to subsequent implementation work.
    """

    async def project(self, request: ProjectionRequest) -> ContextProjection: ...
