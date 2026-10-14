# QH-6 quality gate and CI delta

Date: 2026-10-14 (Europe/Paris).
Ticket: [QH-6](https://contextlab.atlassian.net/browse/QH-6), read in full through
Atlassian MCP. Scope: residual quality/CI work only. No product model, API,
Graphiti or OIDC implementation changed. The owner subsequently authorized a
push to test hosted Actions, followed by a local report commit. The push succeeded;
both hosted jobs were subsequently verified successful after CLI reauthentication.
No Jira write was performed. The report updates remain local.

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
| Versioned Actions workflow matches existing commands, no paid/external LLM service | PASS, local/hosted | actionlint 1.7.7, Docker gate, lint/build/typechecks and both OIDC checks pass locally and on GitHub; no provider key inputs |
| Hosted Actions execution/results | PASS | Push run [38550589615](https://github.com/bl000m/qh/actions/runs/38550589615), full SHA `e696b5409a81f0da25d6f26b0783cbc0c82440cf`; `quality` and `oidc` both completed successfully on fresh Ubuntu 24.04 hosted runners |
| Existing local commands and only missing integrations | PASS | One complete `make verify` after integration: 127 backend + 10 guard + 2 MCP + 5 smoke = 144 passed; all application image builds/health waits, Ruff, TypeScript/shared checks and Vite build passed |
| Existing complete OIDC check remains available | PASS, local/hosted | `make test-oidc-application`: 1 passed, 1 deselected; `make test-oidc`: 1 passed, 1 deselected, on both environments; existing Keycloak/API/isolated owner checks reused |
| Secret guard and Core boundaries preserved | PASS, local/hosted | Guard and AST/isolated import tests included in both gates; hosted logs reviewed with redaction visible and no private-key/GitHub-token/LLM-key pattern matches. This is the scoped minimum guard, not a complete secret/history audit |
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
| `6e3b363` — `docs(QH-6): record authorized push and hosted access blocker` | Initial report and README; successful push recorded while API access was unavailable; index, diff and links checks |

Final documentation commit updates README and this report with hosted evidence.
Its hash/message is reported in the delivery; `git log -4 --oneline` reproduces
all QH-6 commits. The two report commits were not pushed.
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

## Authorized push and hosted evidence

`git push origin main` succeeded: remote advanced from `9842027` to
`e696b5409a81f0da25d6f26b0783cbc0c82440cf`, publishing the two QH-6 implementation
commits. [Pushed commit](https://github.com/bl000m/qh/commit/e696b5409a81f0da25d6f26b0783cbc0c82440cf)
and [Actions on main](https://github.com/bl000m/qh/actions?query=branch%3Amain).

Initial observation was blocked by GitHub app visibility (404) and invalid CLI
credentials (401), not a pipeline failure. The owner reauthenticated the existing
`/opt/homebrew/bin/gh`; no new tool was installed and no token was printed or
copied into repository files. Subsequent run/job/log reads succeeded.

Actual [run 38550589615](https://github.com/bl000m/qh/actions/runs/38550589615):
event `push`, full head SHA above, conclusion `success`. It ran on 2026-10-14
from 12:35:05 to 12:39:29 Europe/Paris (approximately 4m24s).

| Hosted job | Result | Executed evidence |
| --- | --- | --- |
| [quality — 115807298142](https://github.com/bl000m/qh/actions/runs/38550589615/job/115807298142) | PASS | Checkout, ephemeral credentials, actionlint, existing `make verify`, stop and cleanup steps all succeed; 127 backend + 10 guard + 2 MCP + 5 smoke = 144 passed; both Ruff checks, Vite build and workspace TypeScript checks pass. Job duration approximately 1m55s |
| [oidc — 115808059336](https://github.com/bl000m/qh/actions/runs/38550589615/job/115808059336) | PASS | Existing Keycloak setup and migrations/provisioning on its fresh runner succeed; deployed OIDC test 1 passed/1 deselected, isolated OIDC test 1 passed/1 deselected; stop and cleanup succeed. Job duration approximately 2m23s |

Both hosted jobs use the Ubuntu 24.04 runner label. This
confirms the new unversioned/empty application preflight works in the complete
standard gate on a fresh hosted environment, not only the local snapshot test.

Logs were captured for review without dumping raw output into the conversation
or repository. Only test/build counts and review summaries were emitted. Redaction
markers (`***`) are visible; private-key, GitHub-token and LLM-key patterns have
no matches. Generated credentials are handled by the masking protocol, with no
raw environment/Compose/inspect dumps or uploaded credential artifacts observed.
As elsewhere, these checks do not constitute an exhaustive secret detector.
The existing Starlette/AnyIO warning appears in hosted tests and is non-failing.

Read commands: `gh run list --repo bl000m/qh --branch main --event push`,
`gh run view 38550589615 --repo bl000m/qh --json headSha,status,conclusion,url,event,createdAt,updatedAt,jobs`,
and `gh run view 38550589615 --repo bl000m/qh --log` (captured and reviewed).
Only the push trigger was executed; PR/manual triggers were statically validated.
Branch protection/settings and later application features remain outside scope.
The report update is committed locally; publishing it is not part of this push.
