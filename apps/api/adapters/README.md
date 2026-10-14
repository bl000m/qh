# Backend adapters

`context/` implements `app.core.ports.ContextEngine` with the replaceable Graphiti
adapter from QH-7. See [its configuration and approval workflow](../../../docs/qh-7-graphiti.md).
`llm/` reserves implementations of `app.core.ports.LLMProvider`.
`postgres/` owns environment-based connection settings and Alembic migrations.
It is infrastructure outside Core, with no ORM domain models or repositories.
Run migrations explicitly; API startup never changes the database schema.

Context implementations accept configuration/clients through explicit constructors and
translate SDK requests/results into QH domain values. SDK objects and exceptions
must not leak into port signatures. Never import these modules from Core.

Graphiti is a Python library in this backend, not a separate container or
TypeScript package. Its factory is explicit and disabled at production startup;
all provider requests require individual approval. QH-2 itself installed no
provider adapter or application behavior. FastAPI's inbound
adapter lives in `app/api`; the independent MCP service owns its transport.
