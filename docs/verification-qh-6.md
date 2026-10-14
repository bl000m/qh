# QH-6 quality gate and CI delta

Date: 2026-10-14 (Europe/Paris).
Ticket: [QH-6](https://contextlab.atlassian.net/browse/QH-6), read in full through
Atlassian MCP. Scope: residual quality/CI work only. No product model, API,
Graphiti or OIDC implementation changed. The owner subsequently authorized a
push to test hosted Actions, followed by a local report commit. The push succeeded;
no Jira write was performed.

## Existing evidence reused

QH-1–QH-5 already provide Docker Compose, pinned runtime images, Node/hash-locked
Python installs, frontend strict TypeScript/Vite build, backend/MCP tests, Core
import guards, isolated Alembic tests, owner isolation and real OIDC checks.
The [QH-5 report](verification-qh-5.md) and
[approved local deployment](verification-qh-5-local-deployment.md) were consulted.
Origin already points at GitHub; it was neither created nor changed.
Product Contract/ADRs, STOP AND ASK, implementation autonomy and granular local
commits were already present in AGENTS/skill, so only the delta/preflight rule
was added. No full architecture or secret-history audit was repeated.

## Added delta

- `.github/workflows/quality.yml`: pull requests, main pushes and manual runs;
  Ubuntu 24.04, checkout v5.0.0 pinned by commit SHA, read-only contents permission,
  no persisted checkout credentials, bounded timeouts and cancelled stale runs.
- Standard job reuses `make verify`: secret/index guard, Compose/build/health,
  Python lint, existing backend/MCP tests, new guard tests, frontend build/types
  and existing smoke tests. No parallel test framework or paid service.
- OIDC is a separate job depending on a successful standard gate: Keycloak's
  startup/build cost cannot delay diagnosis of ordinary lint/test failures, and
  failing base checks avoid the IdP job entirely. It reuses `make oidc-up`,
  `make migrate`, `make seed-oidc-demo`, `make test-oidc-application` and
  `make test-oidc` on a fresh hosted runner. Those CI migration/seed commands
  never target the developer's database. No realm/auth/test was recreated.
- Credentials are generated per runner in ignored `.env`, masked using GitHub's
  masking protocol and never uploaded or dumped with full Compose/inspect/logs.
  Cleanup stops only that runner's services; no volume deletion/prune command.
- Ruff 0.14.0 adds minimum correctness rules (`F63`, `F7`, `F82`; syntax parsing
  is inherent), not broad style cleanup. Existing Python pins remain unchanged;
  only Ruff was added to each service's hash lock. Backend also scans existing
  root tests/scripts, shared through the existing container rather than a new
  service. Frontend keeps its existing `tsc` lint/typecheck and Vite build.
- `scripts/check_secrets.py` inspects Git **index content**, prohibits private,
  database/dependency/archive files, checks known local `.env` credential values,
  key/token patterns, blank/placeholder `.env.example` secrets and realm secrets.
  It reports paths/rule names, never matching values. It is a minimum index guard,
  not a complete entropy/history scanner. Ten tests exercise rejection/allowance
  and non-disclosure. `.dockerignore` additionally excludes Ruff cache.
- The existing isolated identity helper assumed an already migrated application
  DB. It now also recognizes a genuinely empty unversioned CI schema, rejects
  unexpected/unversioned nonempty schemas, and checks the application snapshot
  remains unchanged. A real empty PostgreSQL test validates its read-only snapshot.
  It does not bootstrap or migrate the application DB during tests.

## Definition of Done

| Criterion | Result | Evidence |
| --- | --- | --- |
| Versioned Actions workflow matches existing commands, no paid/external LLM service | PASS, static/local | `make lint-workflows` passes actionlint 1.7.7 in Docker; actual commands above and no provider key inputs |
| Hosted Actions execution/results | NOT TESTED — read access blocked | Authorized `git push origin main` succeeded at `e696b5409a81f0da25d6f26b0783cbc0c82440cf`. GitHub connector returns 404 for repository/runs; existing gh CLI returns HTTP 401 Bad credentials. No hosted success or failure is inferred from the push |
| Existing local commands and only missing integrations | PASS | One complete `make verify` after integration: 127 backend + 10 guard + 2 MCP + 5 smoke = 144 passed; all application image builds/health waits, Ruff, TypeScript/shared checks and Vite build passed |
| Existing complete OIDC check remains available | PASS, local | `make test-oidc-application`: 1 passed, 1 deselected; `make test-oidc`: 1 passed, 1 deselected; actual local Keycloak, current API, isolated owner checks reused |
| Secret guard and Core boundaries preserved | PASS, local/static | New guard's positive/negative cases, real index check, existing AST and isolated import tests included in backend suite; CI masking/config reviewed. Hosted CI log inspection remains NOT TESTED |
| Permanent workflow is proportionate and based on prior verified delta | PASS, review | Only short AGENTS/skill additions; all preexisting approval/autonomy/commit rules preserved |
| No development database/volume/data deleted | PASS | DB/IdP container IDs and mounts equal QH-5 snapshot; live topology/isolation check passes; application remains `0002_oidc_identities`, 2 users/bindings and 0 spaces; no application migration/seed in this ticket |

No application or test failure remains. The existing Starlette/AnyIO
`BlockingPortal` deprecation warning is unchanged and non-failing. The official
skill validator was attempted but could not run because host PyYAML is absent;
NOT TESTED for that formal validator. No global dependency was installed.
The narrow skill edit preserved its original frontmatter; links/diffs were reviewed.

## Checks and commits

Targeted checks preceded the gate commit: Docker image builds, both lint commands,
12 focused tests (10 secret guard + fresh PostgreSQL snapshot + additive identity
migration), index/diff checks and actionlint. One full integration run followed
the combined Make/dependency changes; no complete suites after individual edits.
Additional actual OIDC checks and network/volume probes were targeted.

| Commit | Purpose / checks |
| --- | --- |
| `6ab729f` — `docs(QH-6): require delta-based ticket preflight` | Brief AGENTS/skill rule; diff/reference review; formal validator unavailable as noted above |
| `e696b54` — `ci(QH-6): add reproducible Docker quality and OIDC gates` | Workflow and minimal missing gates; targeted tests/lint/actionlint/index checks; integration results recorded here |

Final documentation commit updates README and this report. Its hash/message is
reported in the delivery; `git log -3 --oneline` reproduces all QH-6 commits.
Local validation source references: [Actions syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax),
[checkout v5 release](https://github.com/actions/checkout/releases/tag/v5.0.0),
[actionlint Docker usage](https://github.com/rhysd/actionlint/blob/main/docs/usage.md),
[Ruff configuration](https://docs.astral.sh/ruff/configuration/).

Repeat: `make lint-workflows`, `make check-secrets`, `make verify` (or
`make verify-running` on a prepared stack), `make test-oidc-application` and
`make test-oidc`. Build changed Python images before linting an old stack.
QH-6's fresh test databases use `qh6_test_*` and are retained; prior isolated
databases remain untouched. Existing QH-4 tests still clean only their own
temporary databases, never development data/volumes.

## Authorized push and hosted access

`git push origin main` succeeded: remote advanced from `9842027` to
`e696b5409a81f0da25d6f26b0783cbc0c82440cf`, publishing the two QH-6 implementation
commits. [Pushed commit](https://github.com/bl000m/qh/commit/e696b5409a81f0da25d6f26b0783cbc0c82440cf)
and [Actions on main](https://github.com/bl000m/qh/actions?query=branch%3Amain).

Hosted observation is blocked, not a tested pipeline failure: the connected
GitHub app cannot read `bl000m/qh` (404 for repository and runs). The existing
`/opt/homebrew/bin/gh` executable was reused, with no installation, but
`gh run list --repo bl000m/qh --branch main --event push` returns HTTP 401
`Bad credentials`. No token was printed or copied into repository files.
The owner was asked to reauthenticate that CLI with an account that can access
the repository. A hosted run ID, job outcomes, test counts and log redaction
cannot yet be verified. They remain NOT TESTED; no success is claimed.

After authentication, inspect runs for the pushed full SHA and both `quality`
and `oidc` jobs, then replace these pending results with actual evidence. Hosted
runner architecture/network/registry/permissions and log redaction are not proven
by local execution or static actionlint. Branch protection/settings and later
application features remain outside this change. The report commit is local;
publishing it is not part of this verification push.
