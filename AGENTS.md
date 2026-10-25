# AGENTS — MVP Fast Track

Build Demo B with the smallest useful change and verification proportional to risk.
These are the current operating rules; historical records do not create new work or
permissions. Explicit owner instructions and already granted scoped approvals prevail.

## Product and architecture

- Read the relevant sections of [Product Contract](docs/product/QH_PRODUCT_CONTRACT.md)
  before changing domain behavior; consult only the applicable approved ADRs.
- Read [architecture](docs/architecture.md) before changing module boundaries.
  Preserve Core / API / Adapters / UI; dependencies point inward through Core ports.
  Core stays independent of FastAPI, database drivers and provider SDKs.
- PostgreSQL is canonical; Neo4j is a rebuildable projection. Preserve graph checks,
  owner/Space isolation, fail-closed policy and authorization before disclosure.
- Reuse the single Understanding Engine and existing services. Provenance, declared
  information, interpretation, certainty and human confirmation remain independent.
  Proposals require human review; chat never automatically confirms knowledge.
- Canonical revisions and approved projection snapshots are immutable. Preserve
  exact source evidence, atomic publication, idempotence and retained history.
- Public wire contracts belong in `packages/shared`; MCP uses public contracts,
  never backend internals or direct database access.

## Current QH-51 contracts

- [ADR 0010](docs/adr/0010-universal-understanding-model.md): generic profiles v3,
  six universal map dimensions, optional single primary assignment or unclassified.
  Themes are optional metadata, never mandatory primary groups or organization domains.
  No v1/v2 backfill or compatibility adapters for the abandoned experimental dataset.
- Keep `qh.atomic-understanding/1`, its shared strict output schema and exact original
  evidence (including Markdown); preserve fiction, uncertainty and speaker attribution.
  No heuristic repair, automatic confirmation or assistant suggestion promoted to a
  user decision. All semantic output remains proposed through the one Engine/QH-32.
- Chat provenance (`support_basis`) and `insufficient_context` are independent;
  dialogue alone can support an answer in an empty Space. Canonical/mixed support
  still requires exact authorized citations; incomplete-information warnings remain.
- Mémoriser → Continuer sends the whole current conversation and atomically conserves
  Source/proposals/outbox; Voir les propositions opens individual QH-46 review.
  Zero proposals is source-only success, not successful semantic understanding;
  ambiguous errors never claim that no data was saved. Preserve replay identity.
- Ordinary AI is for the exact verified development OIDC account and its owned Spaces,
  `mistral-small-2603` only. No inference on load, extra consent/session grants or
  paid retry/fallback. Ordinary calls omit `max_tokens` and reserve technical worst-case
  cost before HTTP; proposed inclusion stays explicit. Keep the active budget below.
- Private diagnostics remain response-only, scoped and outside Git (0700/0600), with
  one-hour retention and controlled deletion; no prompt/secret/raw JSON in ordinary logs.
- The owner confirms the real Chat → UUM → Propositions test passed on 2026-10-25.
  Manual individual review and further UX polish are deferred, not new acceptance gates
  or permission to remove provenance, review or authorization safeguards.

## Safety and authorization

- Keep secrets in ignored private configuration. Never put secrets, prompts, raw
  provider JSON or sensitive content in ordinary logs, CI, Git or reports.
  Private diagnostics retain authenticated scope, approved retention and deletion.
- No persistent migration, seed/reset, infrastructure replacement or deployment
  without the applicable explicit authorization and backup/rollback safeguards.
- Preserve Keycloak identities, realm import, pinned images, volumes, private `.env`,
  canonical data, budgets, ledgers and frozen evidence unless precisely authorized.
- Use disposable infrastructure for tests; never run application tests against VPS data.
- Prefer Docker and locked dependencies; no global runtime/package installation
  without authorization. If Docker is unavailable, report affected checks as not run.
- Never bypass a tool or GitHub safety refusal. Identify its action/reason if blocked.

## Paid external calls

- Codex needs explicit task-scoped provider/model/payload/cost authorization before
  paid calls. A standing account budget alone does not authorize an agent experiment.
- No paid inference in startup, tests or CI; no paid retry/fallback without approval.
- Ordinary development Envoyer and Mémoriser → Continuer authorize their respective
  user requests under the approved account contract, without redundant provider UI.
  Preserve OIDC, CHAT/owner/current-Space checks, pinned model, source validation,
  atomic maximum-cost reservation and durable cumulative accounting before HTTP.
- As of 2026-10-25, EUR10 Mistral credit/owner envelope is distinct from the active
  runtime configuration: 100 attempts / USD2.50, including history. Never claim the
  larger runtime ceiling is active or change limits/reset ledgers implicitly.
  Check actual availability/configuration only when relevant to the operation.

## Autonomy and STOP AND ASK

Implement ordinary reversible technical choices and fix in-scope bugs autonomously.
Do not reopen approvals for routine helpers, indexes, commits or relevant checks.
Stop only the affected operation and ask for:

- unauthorized structural changes to domain, canonical schema, policy or public contracts;
- destructive changes/data-loss risk, unauthorized disclosure or a concrete security risk;
- unauthorized spending, Git conflicts or operations that could damage existing work.

Explain the specific missing decision or blocker; continue independent authorized work.
Do not create ADRs, tickets, audits, screenshots or manifests without a concrete need.

## Single Checkout Development Policy

- Work only in `/home/ubuntu/qh`, one task branch/PR at a time unless the owner
  explicitly authorizes an exception. Do not create alternate development worktrees.
- Before switching, inspect Git changes, untracked/ignored files, editor state and
  source-dependent processes/mounts. Preserve unsaved/user work; never auto-stash,
  discard, force-switch, reset published history or remove retained checkouts.
- Frontend/backend use this checkout through hot reload. Stop only these apps with
  `sudo -n make dev-stop` before switching and verify they are stopped. Preserve
  private paths and the exact readonly realm import; stop on uncertain ownership.
- Fetch `origin/main`, fast-forward local `main` only and verify equality. Start a
  new task branch there; ordinary corrections stay in their existing task branch.
- Before restarting, verify the selected source is compatible with the active data
  and configuration. For temporary maintenance, return to the compatible task ref
  before restoring apps. A Git switch grants no migration or data-write permission.
- Manage the persistent POC only with guarded `make dev-*` commands: up, status,
  logs, restart or stop. Never use generic Compose lifecycle, `make up`, `make verify`,
  `make migrate` or `make oidc-up` against it. MCP remains image-only.
- The retained runtime bundle and old checkouts are not cleanup targets. Consult
  [runtime operations](docs/qh-development-stack.md) only for relevant operations;
  [checkout history](docs/worktree-lifecycle.md) is historical reference.
- Review/stage explicit files, preserve exclusions and commit coherent verified units
  with conventional messages (Jira key when assigned). No artificial commit quota.
- Publish verified task-branch work unless prohibited. No force push, tags/releases,
  Jira writes or merge without the corresponding explicit authorization.

## Clean Code

- **DRY:** share actual repeated logic, queries, validation and transformations;
  do not abstract superficial similarities.
- **KISS:** choose the simplest readable, predictable solution.
- **YAGNI:** no future-only features, configuration layers or abstractions for the MVP.
- **SRP:** each function/module has one identifiable responsibility.
- Aim for functions around 30 lines when reasonable. Split multiple responsibilities,
  use explicit helper names and early returns, and reduce nesting. Do not add useless
  helpers or a mandatory line-count lint rule to satisfy a numeric target.
- Improve readability incrementally in code already being changed. No unrelated
  service/file rewrites, new frameworks or general refactoring campaigns.

## Risk-based verification

Choose A/B/C from the actual change; escalate when it affects stronger invariants.

- **A — local UI/low risk:** relevant TypeScript/build or lint; one focused functional
  check when useful. No SQL/Neo4j/OIDC/full browser stack without a related change.
- **B — application logic/API/UUM/adapters:** focused unit tests; one pertinent
  integration check when component interactions change; offline LLM replay.
- **C — security/data/policy/isolation/sharing:** tests of affected invariants and
  negative authorization/isolation cases; real SQL/Neo4j or OIDC when necessary;
  Full Verification before merge, run early when needed.
- Reuse passing evidence when relevant code/dependencies have not changed. Repeat
  only for changed behavior, a regression or insufficient evidence; never invent PASS.
- No general benchmarks, legacy v1/v2 campaigns for v3-only work, repeated diagnostics
  or absolute test-count cap that compromises essential verification.
- Keep development PRs draft for PR Fast. Ready PRs, manual workflow runs and pushes
  to main use Full Verification, retaining the quality/OIDC/native/browser checks.
  High-risk draft work requires an early manual Full run when those checks are needed.
- Require green Full evidence for the exact final candidate before merge; report
  branch-protection gaps instead of claiming an optional check is enforced.
  Do not manually duplicate a Full run already covering the same candidate.

## Task Execution & Definition of Done Policy

For ticket work, use [jira-ticket-workflow](.agents/skills/jira-ticket-workflow/SKILL.md).
Read the ticket and only relevant context, choose the minimal delta and risk level,
implement through existing services, run pertinent checks, review/commit and publish.
For explicitly requested maintenance without a ticket, use the owner's observable
criteria; report Jira as unassigned rather than creating one.

Acceptance criteria remain binding. Keep evidence proportional: commands/results
and material limitations, not a detailed report for every assertion. Distinguish
executed checks, reused evidence and checks not run. Do not relabel failures as PASS.
Technical readiness, review/merge, runtime activation and Jira closure are separate:
IN PROGRESS while required work is missing; READY FOR REVIEW after verified publication;
DONE only after acceptance, reviewed merge and authorized Jira closure when applicable.
Do not change Jira automatically or start the next task without a new mandate.

## Final report

Give a short outcome: files/commits and purpose, relevant executed/reused/not-run
checks, residual blockers and next manual action. Include PR, checkout/branch/HEAD
and Git/publication state. Follow the owner's length limit; avoid duplicate reports.
