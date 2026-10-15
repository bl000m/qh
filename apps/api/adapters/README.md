# Backend adapters

`context/` implements
`app.core.ports.ContextEngine`, including the native Neo4j projection/retrieval increment under QH-30.
`llm/` reserves implementations of `app.core.ports.LLMProvider`.
`postgres/` owns environment-based connection settings and Alembic migrations.
It is infrastructure outside Core, with no ORM domain models. Its internal
`canonical.py` repository owns explicit ACID registered-revision writes and scoped
bulk snapshot reads. It is not a public ingestion contract.
Run migrations explicitly; API startup never changes the database schema.

`context/native.py` supplies QH-30 Neo4j projection/retrieval with registered PostgreSQL-shaped rows;
test fixtures use that same representation, without a production category decoder. `reconcile` performs explicit full reconciliation;
SQL-backed composition enables readiness/completeness checks before retrieval.
`context/incremental.py` supplies the backend-local outbox worker, monotonic graph
projector and ordinary bounded-hydration retrieval; 0004 owns operational SQL state.
The full-generation publisher remains required by incremental rebuild; the standalone
full reconciler retains historical recovery regressions. `context/runtime.py` binds
the actual worker and authorized engine in the backend lifespan (VPS schema 0004,
fd50b1b). There is no public context route; `llm/` remains reserved.
The separate cleanup branch accepts 0004/prepared 0005, without startup migrations. Implementations accept clients/readers through explicit constructors and
translate SDK requests/results into QH domain values. SDK objects and exceptions
must not leak into port signatures. Never import these modules from Core.

The native QH Context Engine stays inside the backend; Graphiti is an archived
prototype on its separate branch/PR. See ADR 0003; no new engine container. No Graphiti/provider dependency, dummy production adapter,
policy rule or application behavior is installed by QH-2. FastAPI's inbound
adapter lives in `app/api`; the independent MCP service owns its transport.
