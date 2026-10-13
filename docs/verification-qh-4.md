# QH-4 verification

This report records the implementation checks before deployment authorization.
The subsequent [authorized local deployment](verification-qh-4-local-deployment.md)
applies the migration to QH and deploys the rebuilt backend; historical NOT TESTED
entries below describe the earlier run, not the current local deployment.

Ticket: [QH-4](https://contextlab.atlassian.net/browse/QH-4).
Verdict: **PASS within the user-approved scope in ADR 0002.** The Jira action
list still names five preliminary tables; the owner's subsequent D1–D7 approval
authorizes the canonical foundation and deferring premature projection/sharing
tables. No Jira edit/status change or remote push was performed.

## Definition of Done and approved requirements

| Requirement | Result | Executed evidence |
| --- | --- | --- |
| Reproduce schema from empty database | PASS | CREATE DATABASE from template0, assert no public tables, Alembic upgrade head, inspect seven tables and revision 0001_qh_schema |
| Roll back one migration | PASS | downgrade -1 removes foundation tables/functions, preserves unrelated marker table/data, empties version row; upgrade again and repeated head upgrade pass |
| Canonical originals distinct from interpretations | PASS | Original text in source_revisions, structured JSONB understanding revisions and exact source revision references |
| Immutable revisions and provenance | PASS | UPDATE/DELETE/TRUNCATE rejected for all three immutable tables; later provenance extension rejected; second connection waits on publication then cannot append |
| Integrity and single-space cardinalities | PASS | Composite FK tests reject cross-space revisions/provenance even with the same owner; current/predecessor references cannot target another item |
| AI proposals do not replace approved current state | PASS | Proposed/rejected cannot become current; new confirmation creates separate revision and does not auto-promote; confirmed hypothesis remains a hypothesis |
| Minimal Core semantics corrected | PASS | Distinct typed IDs, search hits/revision provenance, mandatory explicit query scope, formatting projection references; fake adapters and API composition tests pass |
| Core remains framework independent | PASS | Import guard includes SQLAlchemy/Alembic/psycopg; isolated python -I -S imports contracts without site packages |
| Existing QH-1/2/3 verification | PASS | make verify-running: 85 backend + 2 MCP + 5 live smoke = 92 passed; frontend build/types and Compose config passed |
| Final backend image build | PASS | sha256:383929f3daba02b95f4f5deaac28ff6dd94f9685fddd3520a6f8c0cdc7fb8e68 |
| Preserve QH application database | PASS | Read-only catalog before/after: zero application tables, no alembic_version; zero residual qh4_test_* databases |
| Runtime DB isolation and health | PASS | Five healthy existing services, actual internal network/volume/port checks, two authenticated DB queries and four denied frontend/MCP TCP probes |
| Apply migration to QH application DB | NOT TESTED | Explicitly withheld by user; make migrate was not executed |
| Cold start of rebuilt image / semantic engine reconstruction | NOT TESTED | Existing containers preserved; Graphiti integration is outside QH-4 |

The query-scope contract is not a production authorization implementation. QH-5
and later services must authorize scope/results before any adapter/provider
disclosure. Typed IDs use Python NewType annotations, not runtime identity-class
checks. No production repository, validation workflow or engine is installed.

## Implemented scope and deferred work

Seven tables: users, context_spaces, sources, source_revisions,
understanding_items, understanding_item_revisions, item_revision_provenance.
See [schema details](postgres-schema.md) and [ADR 0002](adr/0002-canonical-understanding-persistence.md).
No copied owner_id fields in child entities, graph nodes/edges, embeddings,
global space revision, full event sourcing or proprietary comprehension engine.

- QH-8: ingestion, source locators and Graphiti episode mappings.
- QH-14: projections, recipient/purpose/scope/allowlist/expiry.
- QH-19: approved snapshot storage/version/approval audit and behavior.
- QH-20: shares targeting snapshots, token hashes, expiry and revocation.

Tables can be added with complete constraints in those tickets. Persisted source
and item revision IDs are already independent of Graphiti's internal formats;
actual engine reconstruction remains a future verification requirement.

## Commands actually executed

```bash
# Documentation unit: whitespace and relative-link checks, scoped staged review.
git diff --check

# Schema unit: 32 migration tests, then 32 configuration/boundary tests.
make test-migrations
docker compose --env-file .env -f infra/docker/docker-compose.yml exec -T backend python -m pytest -q tests/test_architecture.py tests/test_postgres_config.py

# Contract unit: 52 targeted checks, then one full integration pass.
docker compose --env-file .env -f infra/docker/docker-compose.yml exec -T backend python -m pytest -q tests/test_contracts.py tests/test_api_composition.py tests/test_health.py tests/test_architecture.py
make verify-running
docker compose --env-file .env -f infra/docker/docker-compose.yml build backend
python3 scripts/verify_infra.py
```

Final read-only PostgreSQL catalog query used BEGIN READ ONLY and counted
non-system tables and qh4_test_* databases; both returned 0. No application
migration, database restart, container recreation or image/volume/container
deletion occurred. Only explicitly test-created databases were dropped by test
teardown, with no FORCE. Existing services were left healthy/running.

## Incremental local commits

| Commit / message | Scope and checks before commit |
| --- | --- |
| 5325cea — build(QH-4): configure Alembic PostgreSQL migrations | Preserved pre-review configuration/dependency commit; 29 targeted tests and backend build |
| 78c2b0b — docs(QH-4): record approved canonical persistence decisions | Product Contract, approved ADR 0002, historical review and autonomy rules; 14 local links and diff checks |
| 355258d — feat(QH-4): persist canonical sources and immutable understanding revisions | Seven-table migration and isolated tests; 32 migration + 32 boundary/configuration checks |
| refactor(QH-4): distinguish space identities and scoped retrieval contracts | Minimal Core/fake/ADR changes; 52 targeted checks, final 92-test regression, build, runtime isolation and application DB preservation checks |

This report belongs to the final contract unit; its hash is available in Git
history and the delivery summary rather than embedded into its own commit:

```bash
git log --oneline --grep='QH-4'
```

## Remaining limitations

The existing Starlette/AnyIO deprecation warning remains (one warning, zero
failures). Static Python type checking is not added. Existing containers execute
new source through bind mounts; the rebuilt backend image is not deployed over
them. Database triggers protect ordinary SQL changes, not deliberate override
by a database administrator. Separate runtime/migration roles remain future work.
The official skill validator remains blocked by missing host PyYAML; no global
Mac packages were installed. Documentation references/whitespace were verified
separately and are not presented as a successful official skill validation.
