# QH

Local sovereign context platform scaffold: React + TypeScript + Vite frontend,
Python + FastAPI backend, independent Python MCP adapter, Neo4j Community and
PostgreSQL. Graphiti will be a replaceable Python adapter inside the backend.
QH-2 defines domain/application contracts and explicit service bindings;
concrete adapters and application features belong to later tickets. See
[ADR 0001](docs/adr/0001-modular-architecture.md).

See [architecture](docs/architecture.md), [permanent instructions](AGENTS.md) and
[verification evidence](docs/verification-qh-1.md).

## Prerequisites

Docker with a running engine and Docker Compose v2.20 or newer (Docker Desktop
on macOS is suitable). The host does not need Node, npm, Python application
packages or a global runtime installation. Commands below run from repository
root. `make` is a convenience wrapper; equivalent Compose commands are shown.

## Local configuration

Generate ignored credentials with the host's existing Python 3 (standard library
only; no packages installed):

```bash
python3 scripts/init_env.py
```

Alternatively, copy `.env.example` to `.env` and set `POSTGRES_PASSWORD` and
`NEO4J_PASSWORD` locally. Use a Neo4j password of at least 8 characters. Empty
credentials cause Compose validation to fail. Never commit `.env`. The helper
uses random credentials, creates the file with mode 0600 and preserves an
existing file. Credentials are not printed.

## Start and stop

```bash
make config
make up
make ps
make logs
make down
```

`make up` builds all application images and waits up to 240 seconds for all five
services to become healthy. Stop following logs with Ctrl-C. `make down` removes
containers and networks, preserving database volumes. Do not add `--volumes`
unless you explicitly intend to destroy local database data.

Equivalent commands without Make:

```bash
docker compose --env-file .env -f infra/docker/docker-compose.yml config --quiet
docker compose --env-file .env -f infra/docker/docker-compose.yml up --build -d --wait --wait-timeout 240
docker compose --env-file .env -f infra/docker/docker-compose.yml down
```

Local endpoints:

- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/health
- MCP health: http://localhost:3001/health
- MCP Streamable HTTP endpoint: http://localhost:3001/mcp

Ports can be overridden in `.env`; they always bind to 127.0.0.1. Database ports
are never published. Browser use of backend/MCP features is not implemented in
this scaffold. `/mcp` requires a protocol client; an ordinary browser GET is not
a protocol test.

Source edits reload automatically through bind mounts and polling. Dependencies
live inside images, not host directories. After manifest or lock changes, run
`make up` again to rebuild. The standalone npm service shortcuts delegate to
Compose; prefer Make to avoid requiring npm on the host.

## Verification

```bash
make verify
```

This runs Compose validation, build/startup, domain/adapter contract and import
boundary tests, FastAPI health test, MCP health and
an actual SDK client exchange (`initialize`, `list_tools`, `scaffold_ping`),
frontend TypeScript checks/build, live Vite HTTP smoke checks, and authenticated
PostgreSQL/Neo4j connections from the backend container.

On an already running development stack, use `make verify-running` to run the
same configuration, unit and smoke checks without rebuilding or replacing
containers. New source/test files are picked up through the existing bind mounts.
This target requires all five services to be running. It does not prove a fresh
image build or startup; those checks are reported separately.

Individual commands, after `make up`:

```bash
make test
make smoke
docker compose --env-file .env -f infra/docker/docker-compose.yml exec -T backend python -m pytest -q
docker compose --env-file .env -f infra/docker/docker-compose.yml exec -T mcp python -m pytest -q
docker compose --env-file .env -f infra/docker/docker-compose.yml exec -T frontend npm run build:web
docker compose --env-file .env -f infra/docker/docker-compose.yml exec -T backend python -m pytest -q /workspace/tests/smoke
```

Optional static isolation check, using only the host's Python standard library:

```bash
python3 scripts/check_compose.py
```

This resolves Compose and checks service count, database volume/network settings,
healthchecks and port bindings without printing credentials. It does not test
running containers or effective network connectivity.

`tests/smoke` uses internal service DNS and actual DB credentials without logging
them. MCP tests need the running MCP server and use the official client over
HTTP, not a direct call to the Python tool function. The frontend smoke checks
that Vite serves HTML and transforms the React entry point; it does not claim
browser rendering or end-to-end UI coverage.

To verify effective database isolation after startup:

```bash
docker network inspect qh_data --format '{{.Internal}}'
docker inspect qh-postgres-1 qh-neo4j-1 --format '{{.Name}} {{json .HostConfig.PortBindings}} {{json .NetworkSettings.Networks}}'
```

Expect internal network `true`, no DB host port bindings and only `qh_data` for
both databases. Do not print full Compose config or container environments into
shared logs, since they include local credentials. Persistence validation can
be performed by creating disposable probe data from the backend, running
`make down` / `make up`, checking the same data and cleaning up the probes.
This check is separate from the non-mutating connection smoke tests.

## Infrastructure verification (QH-3)

```bash
make verify-infra
```

This validates Compose, starts/waits for the five services without rebuilding
or replacing existing containers, then verifies actual health/network/volume
settings. Authenticated backend queries prove both DBs are reachable; separate
TCP probes from frontend and MCP to the DB IPs must fail. Database ports remain
unpublished. The host's existing Python 3 orchestrates Docker CLI using only the
standard library; Node/Python network probes and DB tests run in containers.
Images must already be built (`make build` for initial setup). No cleanup occurs.

## Dependency locks

The frontend uses root `package-lock.json` and `npm ci`. Each Python service
uses a fully resolved `requirements.lock`, with exact versions and hashes,
installed using uv 0.8.4 with `--require-hashes --no-deps`. Development/test
dependencies are included because these are development images. Database drivers
in the backend dev dependencies are used only by infrastructure smoke checks.

After intentionally changing dependency manifests, regenerate locks in containers:

```bash
make lock-node
make lock-python
make verify
```

Lock generation needs registry access, but installs no application packages on
macOS. Base images use explicit runtime versions; validation of actual image
builds is reported in the verification document, not inferred from these pins.

## Jira workflow

Use the repository skill `.agents/skills/jira-ticket-workflow/SKILL.md`. Read the
ticket first, keep changes scoped, and report PASS / FAIL / NOT TESTED against
its Definition of Done. Jira is not automatically updated.
