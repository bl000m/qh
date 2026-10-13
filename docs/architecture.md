# QH architecture

The repository contains the working QH-1 scaffold, the five-service Compose
environment from QH-3 and the QH-2 domain/application contracts. Concrete
services and application features remain deferred. See
[ADR 0001](adr/0001-modular-architecture.md).

## Containers

| Service | Runtime | Responsibility | Network / host access |
| --- | --- | --- | --- |
| frontend | Node 22.14.0; React, TypeScript, Vite | Serve frontend in development | app; loopback 5173 |
| backend | Python 3.12.9; FastAPI | HTTP inbound adapter; `/health` scaffold | app + data; loopback 8000 |
| mcp | Python 3.12.9; official MCP SDK 1.12.4 | Independent Streamable HTTP transport; `/mcp`, `/health`, `scaffold_ping` | app; loopback 3001 |
| neo4j | Neo4j Community 5.26.5 | Future graph persistence | internal data only; no host ports |
| postgres | PostgreSQL 16.8 | Future relational persistence | internal data only; no host ports |

Compose service names are internal DNS names. The browser uses host loopback
URLs, not Docker service names. No application feature currently uses a database.
Backend startup waits for PostgreSQL readiness and an authenticated Neo4j probe. MCP is
independent of backend startup and has no DB credentials or data network access.

## Module boundaries

- `apps/web` imports public wire contracts only; no backend implementation imports.
- `apps/api/app/core` owns immutable Python domain values, ContextEngine and
  LLMProvider outbound Protocols and the ContextService inbound contract.
- `app/policy`, `app/projections` and `app/chat` own their request/result values
  and PolicyService, ProjectionService and ChatService Protocols. Responsibilities
  and method signatures are documented in ADR 0001; no business logic is present.
- `app/composition.py` holds the explicitly supplied ApplicationServices bindings.
  `app/main.py:create_app(services=...)` composes the HTTP transport. Services are
  optional only for the health-only scaffold; no production fakes are installed.
- `app/api` owns FastAPI routes. The only current business-independent route
  remains `/health`.
- API, MCP and outbound adapters depend on Core interfaces. Core must never
  import FastAPI, Graphiti, MCP, adapters or provider SDKs. Composition roots
  assemble implementations through dependency injection.
- `apps/api/adapters/context` reserves ContextEngine implementations, including
  the future Graphiti adapter. `apps/api/adapters/llm` reserves LLMProvider
  implementations. Graphiti will be a backend Python library, never a sixth
  container. Neither integration nor any production adapter is implemented yet.
- `services/mcp-server` owns its Python dependencies and transport. Future QH
  operations use a documented boundary; do not import backend source files.
  `scaffold_ping` is solely a transport test, with no context or LLM behavior.
- `packages/shared` is reserved for public schemas and TypeScript wire types;
  Python domain interfaces are not duplicated here.
- `infra/docker` owns networking, persistence and development orchestration.

## Development and persistence

Application source bind mounts enable Vite and Uvicorn hot reload. Python uses
watchfiles polling and Vite polling for Docker on macOS. Dependencies remain
inside images, installed with `npm ci` or hash-locked `uv pip install`. Manifest
and lock changes require an image rebuild; source changes do not.

PostgreSQL and Neo4j data/log volumes survive `make down`. The `data` network
is internal and databases publish no ports. Only backend joins both app and
data networks. Frontend and MCP cannot connect directly to databases.
Credentials come from the root ignored `.env`, are not copied into builds, and
are never embedded in committed defaults. Changing passwords in `.env` does
not rotate credentials on initialized database volumes; use the database
administration workflow rather than deleting data.

Build, health and protocol results are recorded in `docs/verification-qh-1.md`.
QH-3's runtime isolation and database restart/persistence evidence are in
`docs/verification-qh-3.md`. `make verify-infra` checks five healthy services,
network and volume attachments, authenticated DB queries from backend and
denied TCP connections from frontend/MCP directly to both database IPs.
`make verify-persistence` additionally writes UUID-scoped markers, restarts only
existing DB containers, verifies the markers and removes only that probe's data.
Neither check deletes or replaces containers, images or volumes. Host Python
stdlib orchestrates Docker; database and TCP probes run in the containers.
These checks implement infrastructure verification, not application behavior.
This remains a local POC.

QH-2's AST tests enforce inward imports across all inner modules, and an isolated
Python subprocess imports their contracts without site packages. Contract tests
exercise fake adapters and explicit bindings. For an existing stack use
`make verify-running` to avoid replacing containers. QH-2 results and commit
history are recorded in `docs/verification-qh-2.md`; the approved baseline is
recorded in `docs/initial-commit-review.md`.
