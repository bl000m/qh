# QH architecture

This consolidation implements the QH-1 scaffold and the minimum Compose base
requested from QH-3. QH-2 domain ports, module design and its ADR are deferred.

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
- `apps/api/app` currently contains only the FastAPI health endpoint. Future
  Python QH Core will be independent of transport, persistence and LLM libraries.
- API, MCP and outbound adapters depend on Core interfaces. Core must never
  import FastAPI, Graphiti, MCP, adapters or provider SDKs. Composition roots
  assemble implementations through dependency injection.
- The future GraphitiAdapter belongs under `apps/api/adapters`. Graphiti will
  be a Python library within the backend, never a sixth container. Its domain
  port and implementation are intentionally not defined in this consolidation.
- `services/mcp-server` owns its Python dependencies and transport. Future QH
  operations use a documented boundary; do not import backend source files.
  `scaffold_ping` is solely a transport test, with no context or LLM behavior.
- `packages/shared` is reserved for public schemas and TypeScript wire types;
  the initial TypeScript domain/Graphiti placeholders have been removed.
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

Build, health, protocol and persistence validation results are recorded
separately in `docs/verification-qh-1.md`. This remains a local POC.
