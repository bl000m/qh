# QH-1 verification — 2026-10-13

**Definition of Done: PASS.** The React/Vite frontend, FastAPI backend and official
Python MCP scaffold built and started locally without errors after the two
configuration fixes recorded below. The complete `make verify` command exited 0.

## Jira scope

Tickets were read through Atlassian MCP before verification:

- [QH-1](https://contextlab.atlassian.net/browse/QH-1): initialize frontend,
  backend, MCP, infrastructure, tests, README and .gitignore. Exact Done criterion:
  **local startup of the three modules without errors**. Jira status read: À faire.
- [QH-2](https://contextlab.atlassian.net/browse/QH-2): design Core and adapter
  ports, ContextEngine and LLMProvider domain interfaces, plus an ADR. Depends
  on T01. Jira status read: **En cours (In Progress)**, already the state requested
  by the user if QH-1 passed.

No Jira write was necessary to start QH-2, since it is already In Progress.
QH-1's Jira status was not changed. No QH-2 interfaces or application features
were implemented during this verification.

## Executed checks

All application dependency installation, builds and automated tests ran inside
Docker. Runtime: Docker Desktop 4.95.0, Engine 29.8.2, Compose 5.6.0, Apple Silicon.
Application images use Node 22.14.0 / Python 3.12.9; database images use
PostgreSQL 16.8 and Neo4j Community 5.26.5.

| Check | Verdict | Command and actual result |
| --- | --- | --- |
| Compose configuration | PASS | `make config`: `config --quiet`, exit 0 |
| Application image builds | PASS | `make up`: all three images built; npm ci and hash-locked Python installs completed |
| Startup of the three application modules | PASS | `make up`: frontend, backend and mcp healthy |
| Full five-service startup | PASS | `docker compose ... ps`: all five services running and healthy |
| FastAPI health test | PASS | `make test`: backend pytest, **1 passed** |
| Live MCP health and real SDK client/tool exchange | PASS | `make test`: MCP pytest, **2 passed**; initialize, list_tools, scaffold_ping returned `qh: smoke` |
| Frontend TypeScript and production build | PASS | `make smoke`: tsc passed; Vite built 31 modules and produced HTML, CSS and JavaScript assets |
| Workspace TypeScript checks | PASS | `make smoke`: web and shared package checks completed successfully |
| Live service and DB smoke tests | PASS | `make smoke`: **5 passed**: Vite HTML/transformed React entry, backend health, MCP health, authenticated PostgreSQL SELECT 1 and Neo4j RETURN 1 |
| Host localhost frontend | PASS | HTTP GET `http://127.0.0.1:5173/`: 200, root element and React entry present |
| Host localhost backend | PASS | HTTP GET `http://127.0.0.1:8000/health`: 200, status ok / service qh-api |
| Host localhost MCP | PASS | HTTP GET `http://127.0.0.1:3001/health`: 200, status ok / service qh-mcp-server |
| Resolved Compose topology | PASS | `python3 scripts/check_compose.py`: five services, healthchecks, persistent DB volumes, loopback app ports, unpublished DB ports and internal data network |
| Effective DB network configuration | PASS | `docker network inspect qh_data`: Internal=true; both DB container PortBindings={} and networks=qh_data only |
| Persistence across down/up | NOT TESTED | Volumes are configured, but no write/restart/read persistence probe was executed |
| Browser rendering / UI interaction | NOT TESTED | HTTP serving, transformed React entry and production build were verified; no browser automation was run |

**Automated test total: 8 passed, 0 failed on the final run.** The FastAPI test
emitted one dependency deprecation warning about AnyIO's BlockingPortal alias;
it did not affect startup or test success.

After verification, Compose `down` exited 0 and `ps -a` showed no remaining QH
containers. Application images and database volumes were preserved.

## Fixes required by real execution

1. Neo4j initially exited with `Unrecognized setting ... PASSWORD`. The container
   interprets NEO4J_* environment variables as configuration. Renamed its
   healthcheck credential variable to `QH_NEO4J_PASSWORD`; kept root .env and
   backend configuration keys intact. Healthcheck uses the new container name.
   File: `infra/docker/docker-compose.yml`.
2. The frontend internal smoke request initially returned HTTP 403 with Vite's
   explicit hostname rejection. Added `allowedHosts: ['frontend']` to permit
   the Compose DNS hostname. Type checking, build and live smoke test then passed.
   File: `apps/web/vite.config.ts`. Reference:
   [Vite server.allowedHosts](https://vite.dev/config/server-options#server-allowedhosts).

The first run failed before backend startup; the second reached tests but had
one failed frontend HTTP smoke check. Those failures were corrected before the
final passing run; earlier blocked/unexecuted results do not count as passes.
No credential values were printed and no database volume was deleted.

## Repeat verification

From repository root with the local ignored `.env` present:

```bash
make verify
make ps
python3 scripts/check_compose.py
```

The wrapper executes these stages in order:

```bash
make config
make up
make test
make smoke
```

Optional host health checks and network inspection:

```bash
curl --fail http://127.0.0.1:5173/
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:3001/health
docker network inspect qh_data --format '{{.Internal}}'
docker inspect qh-postgres-1 qh-neo4j-1 --format '{{.Name}} {{json .HostConfig.PortBindings}}'
```

Stop and remove the verification containers with `make down`; persistent
volumes and built images are retained. Restart the environment with `make up`.
See README for equivalent commands without Make.

## Remaining scope

There is no demonstrated QH-1 startup blocker. QH-2 can proceed with its domain
boundaries, ports and ADR and is already In Progress in Jira. QH-3's five-service
startup and effective network configuration have now been checked; persistence
across restart and deliberate source hot reload probes remain untested.

The earlier missing Docker application/daemon blocker has been resolved. The
repository's earlier static checks and skill frontmatter verification were
separate from the container execution recorded here. The optional official
skill validator was previously blocked by missing PyYAML on the host; it was
not rerun or used as evidence for QH-1 startup. At the time of this QH-1 report,
the directory had no .git metadata and no commit was created. The subsequent
QH-2 preflight initialized Git; the user committed the approved baseline as
`e91a01b`. See
`initial-commit-review.md` and `verification-qh-2.md`.
