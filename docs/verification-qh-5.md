# QH-5 verification

Ticket: [QH-5](https://contextlab.atlassian.net/browse/QH-5), read in full through
Atlassian MCP. Approved identity decision was documented before OIDC implementation
in [the dedicated ADR](adr/0002-identity-and-authorization.md).
Execution: 2026-10-13/14, local Docker Desktop, Python/Node dependencies in containers.

Verdict: implementation and acceptance tests pass in **isolated databases**.
Application activation is pending explicit approval: database `qh` is still at
`0001_qh_schema`, with seven canonical tables and zero application rows. No
QH-5 migration or demo provisioning has been performed against it. A valid token
cannot resolve its identity there until deployment is authorized.

## Definition of Done evidence

| Criterion | Result | Actual evidence |
| --- | --- | --- |
| Real OIDC login/token and `/auth/me` | PASS, isolated | `make test-oidc`: actual Keycloak login form, Authorization Code + PKCE exchange, real JWKS and PostgreSQL mapping; Alice/Bob receive HTTP 200 and their QH IDs, including over TCP from a separate Uvicorn process using the production factory |
| Missing/false/expired/wrong issuer or audience rejected; spoofing ignored | PASS | Cryptographically signed negative tests and HTTP 401 assertions in `test_oidc_security.py`; real anonymous/false-token tests; headers/query cannot override the authenticated identity |
| Two distinct persistent QH identities; unique issuer/subject | PASS, isolated | Actual Alice/Bob subjects checked against realm; deterministic independent UUIDs; two provisioning runs retain two users/bindings; new app instance rereads the same identities; constraints and inactive/unmapped users tested |
| Owner isolation, both authorization gates and denial before disclosure | PASS | Core owner tests + fake/real OIDC HTTP tests on test-only routes; each user reads only their space; foreign/missing return identical 403; handler read counter stays unchanged on denial; missing general scope/role fails before identity/resource lookup |
| Additive migration upgrade/downgrade preserves QH-4 | PASS, isolated | `test_identity_migration.py` persists data in all seven canonical tables, compares every row through upgrade/reapply/downgrade, then re-upgrades and tests unique/FK/nonblank mapping constraints and provisioning conflicts |
| Reproducible setup, automatic/regression tests and boundaries, no secrets | PASS | Base/OIDC Compose checks; documented bootstrap executed; full regression and real OIDC tests below; Core AST/import guards; actual local passwords scanned against versionable files, `.env`/archive ignored |
| Startup and volume preservation | PASS | `make oidc-up`, Keycloak restart, stop/base `make up`, then optional restart all succeed; login/mapping still works after IdP restart; live topology checks verify persistent volumes, loopback ports and separate networks; no persistent volume deletion |
| QH-5 migration/provisioning on application database | NOT TESTED / awaiting approval | Read-only check confirms `qh` remains `0001_qh_schema`, seven application tables all count 0; prepared commands are `make migrate` and `make seed-oidc-demo` |

No failed check remains after corrections. Initial integration failure was a
realm import without the subject/role mappers: tokens lacked `sub`, and the
backend correctly refused them. The committed import and idempotent local scope
reconciliation fix it; real login was rerun successfully. An initial lock
generation used a nonstandard manifest filename; it was corrected to
`pyproject.toml`, then the hash-locked image built successfully.

## Executed checks

| Command/check | Result |
| --- | --- |
| Docker pytest owner + architecture before first commit | 42 passed |
| Targeted OIDC, owner, architecture, composition, identity migration | 74 passed before backend commit |
| `make verify-running` with Keycloak stopped | 126 backend + 2 MCP + 5 live smoke = 133 passed; frontend Vite production build and TypeScript/shared typechecks passed |
| `make test-oidc` with Keycloak running, also after restart | 1 real integration test passed; final run includes actual TCP API server against isolated PostgreSQL |
| `make oidc-up`; `make up` with IdP stopped | Builds and health waits passed; base stack remains independent of optional profile |
| `python3 scripts/check_compose.py` and `--oidc` | PASS: five base services, optional IdP profile, loopback ports, internal DB network, persistent volumes |
| `python3 scripts/verify_infra.py`, IdP stopped and running | PASS: five/six healthy services; backend queries both DBs; frontend/MCP denied TCP access to both DB IPs |
| Host HTTP probes | Frontend 200, backend/MCP health 200, anonymous `/auth/me` 401, test-private path 404; live OpenAPI contains only `/health`, `/auth/me`, with Bearer security |
| Read-only application DB inspection | `0001_qh_schema`; seven canonical tables, each 0 rows; no `user_identities` table |
| Local secret scan + ignores + `git diff --check` | PASS; no actual local password in versionable files |

The backend emits the existing Starlette/AnyIO `BlockingPortal` deprecation
warning. Tests still pass. No browser UI end-to-end test is claimed: frontend
login UI is outside QH-5, and real OIDC login is exercised through HTTP/PKCE.

## Changes and commits

| Hash | Message | Scope / checks |
| --- | --- | --- |
| `e164981` | `feat(QH-5): enforce owner read authorization in Core` | Owner policy + independent tests only; 42 owner/boundary tests |
| `f7bce09` | `docs(QH-5): record approved OIDC and authorization boundaries` | Required ADR and diagram before implementation; diff/ignore checks; preserved demo archive excluded |
| `98d0b69` | `feat(QH-5): verify OIDC identities and enforce layered access` | OIDC verifier, explicit HTTP bindings/runtime factory, read-only PostgreSQL security adapter, additive mapping/provisioning and tests, hash lock; 74 targeted tests, real OIDC and successful Docker build |
| `01155c3` | `build(QH-5): add optional persistent Keycloak development profile` | Realm, profile, Make/bootstrap/configuration/test helpers and actual login test; startup/restart, config, full regression, real OIDC and secret checks |

Final documentation/verification commit adds this report, setup instructions,
architecture/schema/README updates and the real TCP integration probe. Its hash
is reported in the delivery message; use `git log -5 --oneline` to reproduce the
complete local history. No push or Jira write was performed.

Key files: `apps/api/adapters/oidc.py`, `adapters/postgres/security.py`,
`adapters/postgres/demo_identities.py`, migration `0002_oidc_identities.py`,
`app/api/auth.py`, `app/api/security.py`, `app/bootstrap.py`, Core owner policy,
their tests, `infra/keycloak/qh-realm.json`, Compose/Makefile/env example,
`scripts/{init_oidc_env,configure_keycloak,verify_oidc}.py`, and
`tests/oidc/test_keycloak.py`. See [repeatable commands](qh-5-authentication.md).

## Residual work

- Obtain application deployment approval, inspect revision/data again, apply
  only the additive migration, then provision the two approved demo identities.
  Verify `/auth/me` against the default application DB after that authorization.
- QH-5 retains uniquely named `qh5_test_*` databases for inspection, including
  failed-attempt databases; none is silently deleted. They contain only isolated
  test data. Future removal requires explicit authorization.
- Existing local POC uses the development DB role, no separate least-privilege
  runtime/migration roles. Production IdP/HTTPS/operations hardening is outside
  this ticket; remote delegated MCP OAuth remains QH-23/QH-24.
- No Graphiti, context CRUD, projection/sharing engine or React login page added.
