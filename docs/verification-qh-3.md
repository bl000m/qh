# QH-3 verification — 2026-10-13

Ticket: [QH-3 — Preparare Compose dei cinque servizi](https://contextlab.atlassian.net/browse/QH-3).
Read through Atlassian MCP before implementation; status read: À faire.
Dependency T01/QH-1 is covered by the verified, committed scaffold.

**Definition of Done: PASS.** Exact criterion: “docker compose avvia i 5 servizi
e DB sono raggiungibili solo dalla rete interna.” No Jira write was made.

The Compose configuration was already implemented in the QH-1 baseline
`e91a01b`: five services, pinned images, internal database network, healthchecks,
named volumes and no published DB ports. This ticket adds repeatable runtime
isolation/persistence checks and completion evidence; no additional services or
application business logic were introduced.

## Acceptance checklist and actual results

| Requirement | Result | Execution evidence |
| --- | --- | --- |
| Valid Compose configuration with exactly five services | PASS | `make verify-infra`: config --quiet and check_compose.py exited 0 |
| Compose starts/waits for frontend, backend, MCP, PostgreSQL, Neo4j Community | PASS | up --no-recreate --no-build -d --wait exited 0; all five inspected running/healthy |
| Internal database network | PASS | Actual qh_data Internal=true; PostgreSQL/Neo4j attached only to data; backend joins app and data |
| No published database ports | PASS | Both DB HostConfig.PortBindings empty; application bindings limited to 127.0.0.1 |
| Backend can authenticate/query both databases | PASS | Two containerized tests: PostgreSQL SELECT 1 and Neo4j RETURN 1 |
| Frontend/MCP cannot connect directly to databases | PASS | Four negative TCP probes to actual DB IPs: frontend and MCP each denied PostgreSQL 5432 and Neo4j 7687 |
| Persistent named volumes | PASS | Runtime mount checks: qh_postgres_data, qh_neo4j_data and qh_neo4j_logs |
| PostgreSQL and Neo4j data survive restart | PASS | UUID markers written, both DB containers restarted, markers read back; all five container IDs and DB mounts unchanged |
| Remove only disposable probe data | PASS | UUID-scoped SQL table/schema and tagged Neo4j node removed; absence checked; no CASCADE or DETACH deletion |
| QH-1/QH-2 regression suite | PASS | make verify-running exited 0: 46 backend + 2 MCP + 5 live smoke = 53 passed, zero failed |
| Frontend build and workspace types | PASS | Vite production build: 31 modules; web/shared TypeScript checks passed |
| Startup with newly recreated containers / persistence after volume remount | NOT TESTED | Existing containers preserved; restart tests prove persistence across process/container restart, not recreation |

The last row is beyond the ticket's Done requirement and is explicitly separated
from the tested startup/wait of the existing stack. The rebuilt QH-2 backend
image was not substituted into the existing container. No images, containers or
volumes were deleted, replaced or pruned. Application dependencies and probes
ran in containers; host Python used only its standard library to orchestrate
Docker. Credentials and resolved environment payloads were not printed.

## Repeat the executed checks

With Docker running, existing images/containers and the ignored root `.env`:

```bash
make verify-infra
make verify-persistence
make verify-running
make ps
```

`verify-infra` starts/waits without build or recreation, validates static and
actual topology, then runs positive backend queries and negative TCP probes.
`verify-persistence` requires a healthy running stack and additionally restarts
only PostgreSQL and Neo4j. Connections are briefly interrupted. It uses a fresh
UUID for each run and cleans only that run's marker data in a finally block.
The executed probe token was `bcfb8c22dd4c4727b98de1c8f795c62e`; cleanup passed.
README documents targeted cleanup recovery if a future run cannot reach a DB.
`verify-running` runs the existing full regression without rebuilding/replacing.

For a new environment, use `make build` then `make verify-infra`. To stop/start
the existing environment while retaining containers and volumes:

```bash
docker compose --env-file .env -f infra/docker/docker-compose.yml stop
docker compose --env-file .env -f infra/docker/docker-compose.yml up --no-recreate --no-build -d --wait --wait-timeout 240
```

## Local commit units

| Commit / message | Purpose and checks before commit |
| --- | --- |
| a791149 — test(QH-3): verify runtime service and database isolation | Runtime metadata checks, two positive DB tests, four denied TCP probes; make verify-infra passed; scoped diff/exclusion review |
| test(QH-3): verify database persistence and document delivery | Disposable write/restart/read/cleanup test; make verify-persistence and full make verify-running passed; scoped diff/exclusion review |

This report belongs to the second unit; its hash is available in Git history
and the final delivery rather than embedded in its own commit:

```bash
git log --oneline --grep='QH-3'
```

Changed files: `scripts/verify_infra.py`, `tests/infra/persistence_probe.py`,
`Makefile`, `README.md`, `docs/architecture.md` and this report. Compose itself
needed no change: live checks confirmed its existing settings were correct.

## Remaining limitations

No QH-3 Done blocker remains. Fresh container recreation, volume remount,
dedicated hot reload probes and browser UI automation were not run. The existing
Starlette/AnyIO deprecation warning remains (one warning, no failed tests).
Graphiti, concrete adapters and application features remain deferred to their
tickets. Jira status changes and remote pushes require separate authorization.
