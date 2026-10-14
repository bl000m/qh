# QH-5 authorized local deployment

Date: 2026-10-14 (Europe/Paris). The project owner explicitly authorized
`make migrate` and `make seed-oidc-demo` after reviewing the isolated QH-5
verification and its deployment limits. No remote push or Jira write authorized.

## Preconditions — PASS

- Clean Git baseline at `891a753`; updated QH-5 reread through Atlassian MCP.
- Docker context `desktop-linux` uses the local Unix socket, not a remote daemon.
- Backend destination is the Compose service `postgres:5432`, database `qh`.
- `make migration-current` returned `0001_qh_schema`.
- Read-only SQL verified exactly seven canonical tables plus Alembic metadata;
  every application table contained zero rows. Prepared head was exactly
  `0002_oidc_identities`, descending from the existing QH-4 revision.
- Captured the six container IDs and volume attachments before execution,
  without credentials in the snapshot or logs.

## Authorized operations — PASS

```sh
make migrate
make migration-current
make seed-oidc-demo
make seed-oidc-demo
```

Migration succeeded; Alembic now reports `0002_oidc_identities (head)`.
Provisioning succeeded twice; subsequent read-only checks confirmed two users
and two distinct issuer/subject mappings, with no duplicates. No Context Spaces
or content were created by provisioning.

| Application table | Rows after deployment |
| --- | --- |
| users | 2 |
| user_identities | 2 |
| context_spaces | 0 |
| sources | 0 |
| source_revisions | 0 |
| understanding_items | 0 |
| understanding_item_revisions | 0 |
| item_revision_provenance | 0 |

The additive mapping table has the composite issuer/subject primary key and
user FK from the reviewed migration. No application downgrade was executed.

## Runtime checks — PASS

`make test-oidc-application` passed one deployed integration test (one isolated
test deselected). It performs **no database writes**: it verifies stored mappings,
logs Alice and Bob into actual Keycloak using Authorization Code + PKCE, and
calls `http://backend:8000/auth/me` on the already running backend connected to
`qh`. Both return HTTP 200 with only their associated internal QH user ID.
Client-supplied identity headers/query values cannot override it. Missing
credentials, a spoofing header alone and a false token return HTTP 401 with the
Bearer challenge. Live OpenAPI contains only `/health` and `/auth/me`; a private
test route returns 404.

`python3 scripts/verify_infra.py` passed: six healthy services, preserved named
volumes, internal database network, loopback application ports, authenticated
backend queries against both databases, and denied DB TCP connections from
frontend/MCP. The normalized JSON snapshot comparison confirmed all six
container IDs and all volume attachments match the pre-deployment snapshot.
Its initial comparison mixed tuples with JSON lists; correcting that local
representation and rerunning passed. No container or volume was replaced.

Docker smoke tests `/workspace/tests/smoke`: **5 passed** (frontend, API, MCP and
authenticated PostgreSQL/Neo4j connections). `make test-oidc` also passed one
isolated OIDC/owner integration test (one deployed test deselected) after deployment.
Full pre-deployment regression (126 backend,
2 MCP, 5 smoke, frontend build/typecheck) is recorded in
[QH-5 verification](verification-qh-5.md); a full suite was not rerun for this
migration-only deployment and targeted test addition.

The existing Starlette/AnyIO deprecation warning remains non-failing. No
application data, databases, images or persistent volumes were deleted. Previously
retained isolated test databases remain untouched; the isolated regression creates
its own uniquely named database.

## Repeatable verification

```sh
make migration-current
make test-oidc-application   # read-only deployed identity check
make test-oidc              # separate isolated OIDC + owner integration
python3 scripts/verify_infra.py
```

Setup instructions and schema/architecture/README were updated to reflect the
approved deployment. A local granular QH-5 commit records the new test mode and
these evidences; its hash/message are reported in the delivery. No Jira status
was changed. QH-6 and subsequent tickets were not started.
