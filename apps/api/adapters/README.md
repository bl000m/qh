# Backend adapters

`context/` reserves the location for implementations of
`app.core.ports.ContextEngine`, including the native Neo4j projection/retrieval increment under QH-30.
`llm/` reserves implementations of `app.core.ports.LLMProvider`.
`postgres/` owns environment-based connection settings and Alembic migrations.
It is infrastructure outside Core, with no ORM domain models or repositories.
Run migrations explicitly; API startup never changes the database schema.

`context/native.py` supplies the fixture-backed QH-30 Neo4j slice; `llm/` remains
reserved. Implementations accept clients/readers through explicit constructors and
translate SDK requests/results into QH domain values. SDK objects and exceptions
must not leak into port signatures. Never import these modules from Core.

The native QH Context Engine stays inside the backend; Graphiti is an archived
prototype on its separate branch/PR. See ADR 0003; no new engine container. No Graphiti/provider dependency, dummy production adapter,
policy rule or application behavior is installed by QH-2. FastAPI's inbound
adapter lives in `app/api`; the independent MCP service owns its transport.
