# QH-4 — Authorized local migration and deployment

Verdict: **PASS**. The user explicitly authorized applying Alembic to the local
development QH database and starting services with current images. This extends
the earlier [implementation verification](verification-qh-4.md); no domain/schema
change, QH-5 implementation, remote push or Jira write occurred.

## Preflight and migration

- Docker context desktop-linux, Unix socket, Docker Desktop engine. Compose
  project qh; backend target postgres:5432/qh matches its local PostgreSQL container
  and environment configuration. The database network is internal and unpublished.
- TCP server address matched the PostgreSQL container IP. A first preflight
  stopped on inet-to-text formatting (/32 suffix); normalizing with host() fixed
  that comparison before any migration. No data/revision/environment risk appeared.
- Read-only inspection before upgrade: Alembic base, zero application tables and
  zero application rows. make migration-current also returned no revision.
- make migrate exited 0. make migration-current returned 0001_qh_schema (head).
- Read-only inspection after upgrade and deployment: exactly seven foundation
  tables plus alembic_version; all seven application tables contain zero rows.

Present tables: users, context_spaces, sources, source_revisions,
understanding_items, understanding_item_revisions, item_revision_provenance.

## Images, storage and runtime

make up built all three application images and waited successfully for all five
services. Compose recreated only the backend to deploy its updated image;
frontend/MCP already used current images. PostgreSQL/Neo4j container IDs and all
database volume mounts match the preflight snapshot. No database, volume or
application data was deleted, and no Docker cleanup/pruning was performed.

| Application | Running image ID |
| --- | --- |
| backend | sha256:383929f3daba02b95f4f5deaac28ff6dd94f9685fddd3520a6f8c0cdc7fb8e68 |
| frontend | sha256:ec014824e95e3ccf46bc89eb7167ff45ccab782bca0c5064651d6e70246fa4ee |
| mcp | sha256:6d8a74855466c31f550c56a92313f52a1a1ea5b7a586b4e2728de65428c565a8 |

All five services are running/healthy. Host loopback checks returned HTTP 200
for frontend /, backend /health and MCP /health. The MCP SDK client initialized,
listed tools and invoked scaffold_ping successfully. Runtime infrastructure
checks confirmed named volumes, internal DB networking, unpublished DB ports,
authenticated backend queries and four denied frontend/MCP database connections.

## Isolated committed persistence smoke

Created database qh4_smoke_35d0e08804ec4c84adefbdda96ca63b3 from template0 and
applied the same migration only inside that isolated database. Committed one row
per foundation table: owner, space, original source/revision, item/revision and
provenance, including the confirmed-current reference. fsync and synchronous_commit
were both on. Closed the writer, opened a new connection and verified content,
relationships, current revision and Alembic head.

**PASS: seven committed test rows survived connection closure and were read back.**
The isolated database is retained for inspection because the user prohibited
database/data deletion. No DROP DATABASE, DELETE or destructive cleanup was run.
The QH application database was rechecked afterwards: zero rows in all seven
tables. This proves committed write/read; this intervention did not restart
PostgreSQL to repeat a process-restart persistence test.

## Executed regression checks

```bash
make migration-current
make migrate
make migration-current
make up
docker compose --env-file .env -f infra/docker/docker-compose.yml exec -T backend python -m pytest -q --ignore=tests/test_migrations.py
docker compose --env-file .env -f infra/docker/docker-compose.yml exec -T mcp python -m pytest -q
make smoke
python3 scripts/verify_infra.py
```

Results: **53 backend + 2 MCP + 5 live smoke = 60 passed**. Frontend production
build and web/shared TypeScript checks also passed. The 32 migration tests were
not rerun: their teardown drops isolated databases, contrary to this intervention's
no-database-deletion constraint. Their earlier passing results remain documented
in the implementation report. One existing Starlette/AnyIO warning remains.

Preflight, image/volume comparison, loopback HTTP and isolated persistence were
orchestrated with host Python standard-library helpers saved in /tmp; DB operations
and tests ran inside the backend container. No host packages were installed and
no credential values were printed. The stack remains running with QH at head.

This delivery is recorded in a separate local documentation commit; inspect its
hash with git log --oneline --grep='docs(QH-4): record authorized local deployment'.
