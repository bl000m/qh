# Backend adapters

`context/` reserves the location for implementations of
`app.core.ports.ContextEngine`, including the future Graphiti adapter.
`llm/` reserves implementations of `app.core.ports.LLMProvider`.
`postgres/` owns environment-based connection settings and Alembic migrations.
It is infrastructure outside Core, with no ORM domain models or repositories.
Run migrations explicitly; API startup never changes the database schema.

Both namespaces are deliberately empty of concrete adapters. Their future
implementations accept configuration/clients through explicit constructors and
translate SDK requests/results into QH domain values. SDK objects and exceptions
must not leak into port signatures. Never import these modules from Core.

Graphiti will be a Python library in this backend, not a separate container or
TypeScript package. No Graphiti/provider dependency, dummy production adapter,
policy rule or application behavior is installed by QH-2. FastAPI's inbound
adapter lives in `app/api`; the independent MCP service owns its transport.
