# AGENTS

QH is a modular, sovereign context platform. Read `docs/architecture.md` before
changing module boundaries.

## QH Product Invariants

QH is a sovereign context environment: people build, preserve, query, govern and
selectively share persistent understanding through Context Spaces, independently
of AI providers/models. Its differentiators are owner control, persistent identity
and lifecycle, structured understanding, provenance distinct from interpretation,
portability and selective sharing. Substantial decisions remain human-controlled;
backend authorization precedes disclosure to AI providers. V0.1 approved projections
are immutable snapshots.

Before decisions about Context Space, understanding, provenance, projection,
ownership, authorization or sharing, read the relevant sections of
[QH Product Contract](docs/product/QH_PRODUCT_CONTRACT.md), the mandatory functional
reference. Never infer the functional model solely from table names, existing code
or an incomplete Jira ticket. PostgreSQL is canonical for QH sources, persisted
understanding, revisions and governance; Neo4j is replaceable derived operational state. ADR 0003 supersedes
the Graphiti runtime choice while preserving ADR 0002 product/identity invariants.
QH-30 and semantic foundation are consolidated in main. Persistent schema is 0005;
backend/frontend/MCP run images from c723d32c5d0825f9232ece560e7e666e69dceb27
without source bind mounts. The permanent checkout is /home/ubuntu/qh on main;
development worktrees follow the Git Worktree Lifecycle Policy below. Runtime management uses the frozen
/home/ubuntu/qh-runtime/current bundle and private .env, not development make up.
Keep the readonly root Keycloak realm import file unchanged. Future planning does
not authorize further persistent writes/deployment/retirement.
Read [post-cutover consolidation](docs/qh-semantic-consolidation.md) for the
approved three generic profiles, open descriptor contract, authorized structured selection and
applied 0005 and executed deployment evidence. Controlled registration is explicit; never infer new
SQL types or human validation from descriptors. Semantic meanings
are open-ended content, not mandatory registry types or the eleven QH-4 categories.
Optional specialized schemas/rules remain supported; never rewrite applied
migrations or immutable historical bindings to force a new vocabulary.

## Autonomy and STOP AND ASK

Structural decisions require user approval: domain meaning, canonical data,
authorization rules, architectural responsibilities, public contracts and product
invariants. Apply STOP AND ASK if they are not already defined by the Product
Contract or approved ADRs. Do not reopen approved decisions unless a concrete
contradiction, new risk or technical constraint makes them impractical; explain
that specific issue rather than restarting a general architecture review.

Make implementation decisions autonomously within approved contracts: internal
module layout, index names, migration details, tests, local refactoring and other
reversible technical choices. Do not request approval for every SQL field/file/test.

For unresolved structural choices, stop the affected implementation when:

- A ticket omits a necessary domain choice or contradicts the Product Contract.
- The Product Contract does not resolve an ambiguity.
- Architectural alternatives have different structural consequences.
- A choice changes the canonical model or persistence responsibilities.
- A decision may compromise privacy, authorization or data sovereignty.
- Implementation requires a significant deviation from an approved ADR.
- A change makes Graphiti, an LLM provider or another adapter hard to replace.
- A decision introduces a service or changes public contracts.

Identify the missing decision; present feasible alternatives, consequences,
benefits/risks and a reasoned recommendation. Wait for explicit user approval
before implementing the affected part. Continue only independent, already-defined
work without anticipating the blocked decision. Ordinary reversible technical
choices consistent with approved decisions do not require interruption.

## Paid external calls

Paid or potentially metered external calls require prior explicit authorization.
Describe provider, endpoint, models, purpose and estimated cost before requesting
authorization. Authorization may cover one call or a precisely scoped experiment
with a maximum request count and estimated budget. Within an authorized experiment,
proceed without per-call confirmations while enforcing all limits; stop on errors,
unexpected behavior or risk of exceeding them. Retries and parallelism require
coverage by that authorization. No paid calls during startup, automatic tests or CI.
Keep provider secrets exclusively in ignored local configuration, never logs or chat.

## Architecture and dependency direction

- `apps/web`: React + TypeScript + Vite. TypeScript is strict and extends the
  root configuration. The browser communicates with public API contracts.
- `apps/api`: Python + FastAPI. FastAPI is an inbound adapter, not QH Core.
- `services/mcp-server`: independent Python adapter using the official `mcp`
  SDK. It must not import backend implementation files or access databases.
- `apps/api/app/core` is Python, independent of FastAPI, Graphiti, MCP and LLM SDKs.
  Inbound adapters and outbound adapter implementations depend on Core ports;
  Core never imports them. Assemble dependencies at the application boundary.
- `app/policy`, `app/projections` and `app/chat` own their application contracts;
  `app/composition.py` holds explicit service bindings. Keep their types and
  dependencies consistent with `docs/adr/0001-modular-architecture.md`.
- QH-30 / ADR 0003 replaces the archived Graphiti prototype with a native QH
  Context Engine. PostgreSQL is canonical; Neo4j is a rebuildable operational
  graph. Preserve the Graphiti branch/PR; do not copy its runtime/private hooks.
  Keep the engine in the backend with no new production service by default.
- `packages/shared`: public wire schemas/types, not Python domain interfaces.
- `infra/docker`: five base Compose services: frontend, backend, mcp, neo4j
  and postgres; optional local Keycloak profile under the approved
  `docs/adr/0002-identity-and-authorization.md`. Keep infrastructure separate.
- Document new module responsibilities and adapter contracts. Do not implement
  business logic before module boundaries and contracts are established.

## Ticket workflow

- Read the Jira ticket, acceptance criteria and dependencies through Atlassian
  MCP before implementation. If unavailable, report the blocker; do not invent
  ticket requirements.
- Inspect the repository and scope changes to the requested ticket. Use
  `.agents/skills/jira-ticket-workflow/SKILL.md` for ticket-based work.
- Identify the delta against previous verified results before implementation.
  Reuse them; repeat completed work only for changed behavior, regressions or
  insufficient evidence. Scale preflight to the change's actual risk.
- Verify the Definition of Done with actual execution evidence. Report each
  criterion as PASS, FAIL or NOT TESTED, with commands and observed results.
- Never claim tests passed if they were not executed. Distinguish static review
  from build, runtime, protocol and persistence checks.
- Never automatically change Jira status. Any Jira write requires explicit
  user authorization; status changes require user approval.

## Task Execution & Definition of Done Policy

This policy is mandatory for development and maintenance tasks. Explicit user
instructions and already granted, precisely scoped authorizations take precedence;
record any exception instead of treating it as permission for later work.

### One active ticket at a time

- Before implementation, read the Jira ticket, objective, acceptance criteria,
  dependencies and relevant comments through Atlassian MCP. Identify the associated
  PR, branch and absolute worktree path; inspect local/remote Git state and prior
  evidence. If Jira is unavailable, report the blocker; never invent requirements.
- If there is no verifiable Definition of Done, propose one before implementing:
  observable outcomes, checks/evidence, exclusions and unresolved decisions. Obtain
  approval for missing structural decisions under STOP AND ASK. For explicitly
  requested non-ticket maintenance, report Jira as not assigned and use the user's
  approved objective and verifiable criteria; do not create a ticket automatically.
- Do not start a new development task or open another development PR until the
  active task has been reviewed and closed, unless the user explicitly authorizes
  an exception. Green CI, a local completion report or a published PR does not
  constitute review or closure. A reviewed cancellation/closure must be explicit;
  do not infer permission to discard its work or merge it.
- Historical archived PRs are a documented exception, not active development.
  Record their archival reason, retained refs/evidence and superseding decision.
  Graphiti Draft PR #1 is retained under
  [ADR 0003](docs/adr/0003-native-context-engine.md), including local `77de43c`;
  its still-open GitHub state is not a dependency on reviving that prototype.
  Never silently archive a current PR to bypass the one-task rule.

### Autonomous corrections within the approved scope

- For an in-scope bug or technical failure, identify the cause, communicate the
  smallest safe solution, implement it autonomously and add appropriate regression
  tests. Run the relevant checks and verify the actual outcome. Do not stop at an
  error report or repeatedly rerun tests when a safe in-scope correction is possible.
- Obtain prior explicit approval for substantial architectural changes, persistent
  schema/database changes, public contracts, authorization/security changes,
  deployment, paid external API calls or functional scope expansion, unless that
  exact action is already authorized. Preserve the existing STOP AND ASK, paid-call
  limits and persistent-data protections; a technical failure grants no new scope.
- Do not implement unrelated problems silently. Report each residual/out-of-scope
  issue with priority, impact, a minimal proposed solution and a suggested existing
  Jira ticket or proposed ticket title. Do not invent keys or write to Jira.

### Mandatory criterion-by-criterion Definition of Done

Before declaring implementation complete, map every acceptance/Done criterion to
an observable result and evidence (command, test, artifact or functional check).
Classify each criterion explicitly:

| Classification | Required interpretation |
| --- | --- |
| Implemented and tested | Relevant executed checks demonstrate the claimed outcome; cite evidence and limits |
| Implemented but unverified | Work exists, but the required check was not run or does not establish the outcome |
| Not implemented | Required behavior is missing, or a known failure leaves the criterion unmet |
| Out of scope | Excluded by the approved task boundary; explain why, never relabel a required criterion silently |

Keep execution verdicts PASS / FAIL / NOT TESTED alongside these classifications.
A failed required check remains unmet until corrected and verified. Distinguish
static review, build, unit, integration, runtime, protocol and persistence evidence.
Green tests do not automatically establish task completion, functional correctness,
semantic quality or human acceptance. Report missing criteria and blockers plainly;
implementation completion, PR review/merge and Jira closure are separate states.

### One PR, one objective

- Prefer new branches from verified, updated `main`, after the active task closes.
  Avoid stacked PRs or dependence on unintegrated branches without explicit user
  authorization. Record any authorized dependency and its review/integration order.
- Correct the current PR in its existing branch/worktree; do not create another
  branch or PR for an ordinary correction. Reuse existing implementations and
  evidence rather than duplicating work under another ticket or PR.
- Never merge automatically. After an explicitly authorized merge, verify the PR's
  actual merge and preservation of its work, safely synchronize the permanent
  `main` checkout, then apply every check in Git Worktree Lifecycle Policy before
  removal. A closed-but-unmerged PR never authorizes worktree cleanup.

### Required concise outcome report

At the end of every task, always report:

- Jira ticket (or explicitly not assigned), objective and verifiable Definition of Done.
- Code/files actually changed and relevant local commits, hashes and purpose.
- Checks executed, observed results and what they demonstrate, including limits.
- Each Done criterion satisfied/missing using the classifications above.
- Problems corrected autonomously, with cause and verified resolution (or none).
- Residual issues and proposed solutions, with priority and suggested Jira follow-up.
- Associated PR, branch, absolute worktree, HEAD and Git status; publication,
  review/closure and remote/local synchronization state.
- The next recommended action on the current task. Do not automatically propose
  starting the next ticket while the current one remains open.

## Versioning and verification

Read [main consolidation](docs/main-consolidation.md) before merge, checkout or
runtime-source changes. Source mounts have been removed from all app services;
root retains only the readonly IdP configuration bind. Preserve it and private .env.
Authorization may explicitly cover a whole consolidation sequence; do not request
it again for already authorized steps. Preserve published native ancestry.

Follow [versioning and logical milestones](docs/versioning.md), maintain
[CHANGELOG](CHANGELOG.md) and the [deployment register](docs/deployments.md).
Separate product versions, migration targets, semantic versions and image identities.
Tags, GitHub Releases and Jira milestone/version writes require explicit approval.

- Before ticket work, verify Git and the baseline. If either is missing, propose
  the baseline contents and obtain user approval before the first commit.
- Split a ticket into coherent independent units when useful (often 2–4, never
  a fixed quota). Commit verified units incrementally instead of waiting for
  the end of the ticket.
- Authorization to implement a ticket permits local commits. Use conventional
  messages with its Jira key; each commit must have one clear purpose.
- Before each commit, run relevant checks and review git status, working/staged
  diffs and exclusions. Stage explicit files/hunks; keep unrelated or user-owned
  changes out unless approved. Never include secrets or local data.
- Routine task-branch publication follows the Git Worktree Lifecycle Policy below.
  Other remote pushes, all force pushes and destructive resets require explicit
  approval. The Jira authorization rules above also apply.
- At ticket completion, list each commit's hash, message, purpose and checks.
- Prefer Medium reasoning when sufficient; increase for architecture, security
  or complex problems. Use targeted checks per unit and full verification at
  integration or when changes/failures justify it, not after every small edit.

## Git Worktree Lifecycle Policy

### Bootstrap and creation

- Keep the primary repository at `/home/ubuntu/qh`, normally on `main`. Before
  creating a task branch or worktree, read that checkout's `AGENTS.md`, relevant
  skills and task instructions, then inspect `git worktree list --porcelain` and
  Git status. Do not rely only on instructions copied into an older feature branch.
- Every new development task requiring an isolated branch must use a dedicated
  worktree, directly under `/home/ubuntu/` as a sibling of the primary repository.
  Never create worktrees in `/tmp`, inside the primary repository or in another
  temporary directory. Do not develop new functionality directly on `main`.
- Use clear ticket/branch names: `feat/QH-8-mistral-evaluation` maps to
  `/home/ubuntu/qh8-mistral-evaluation`; `feat/QH-9-context-graph` maps to
  `/home/ubuntu/qh9-context-graph`. Non-ticket maintenance may use a descriptive
  name such as `/home/ubuntu/qh-worktree-lifecycle-policy`.
- Use `git worktree add`. Inspect existing registrations first; never recreate a
  branch already associated with a worktree. Reuse that task worktree only when
  authorized and idle; leave other active Codex sessions' worktrees untouched.
- Once integrated on `main`, use `scripts/start_task_worktree.py` from the primary
  checkout for task bootstrap. First run its read-only plan, read the printed
  primary-checkout instructions and resolve their requirements, then create using
  the returned policy SHA-256. The script re-reads committed `main` instructions
  before creation, rejects stale policy, occupied destinations and attached
  branches, and creates only a direct sibling through `git worktree add`.
- Always report the absolute worktree path, associated branch, HEAD and Git status.
  A moved checkout retains its branch's committed instructions; bootstrap must
  still consult the primary checkout to pick up policy updates after integration.

### Development and publication

- Keep each task isolated; run its tests and commits in the corresponding worktree.
  Preserve unrelated changes, local/untracked/ignored files and other sessions.
- Publish verified, review-ready task commits to the task PR unless the user gives
  contrary instructions. This policy authorizes routine publication of that task
  branch, not unrelated branches, force pushes, tags/releases, Jira writes, merges
  or deployment. Relocation or cleanup alone never triggers a push or publication
  of another task's pending commits. Explicit task restrictions take precedence.
- Keep important reports, test results, experimental outputs and evidence in the
  repository or a documented persistent destination. Never leave their only copies
  in `/tmp`. Secrets belong only in protected ignored configuration/private archives,
  never published artifacts. Preserve frozen evidence and historical path strings.
- Before relocation, check destination absence, active processes/sessions, open
  files, container mounts and absolute-path dependencies. Use `git worktree move`,
  preserving branch, commits and all local/untracked/ignored contents. Compare
  file hashes, relevant metadata and Git state before/after. Update operational
  configuration/scripts that use the old path; do not rewrite historical evidence.
  If another session is active or a dependency is unresolved, retain the worktree
  and explain the blocker. Never infer permission to replace runtime services.

### Mandatory cleanup after merge

A worktree is a temporary development space and must be removed after its PR is
merged, once every safety check below succeeds. An open PR or unrecoverable local
changes always prevent removal. A failed or uncertain check means retain and report.

1. Verify on GitHub that the associated PR is actually merged, not merely closed.
2. Fetch the main branch and verify the relevant work is reachable from updated
   `origin/main`. For merge commits, check commit ancestry. For squash/rebase merges,
   original SHAs may differ: verify the PR's resulting commit(s) are reachable and
   review the mapped patch/tree changes and any branch-only commits. Do not equate
   a merged flag or a patch-equivalence hint alone with proof all work is preserved.
3. Inspect uncommitted changes, untracked files **and ignored files**. Preserve
   anything important and stop if local changes cannot be recovered. A clean
   ordinary `git status` alone is insufficient.
4. Confirm reports, tests, outputs and other important artifacts have verified
   persistent copies. Preserve private configuration and evidence archives.
5. Recheck active Codex sessions/processes, open files, container mounts and other
   path dependencies immediately before removal. Never modify/remove a worktree
   used by another active session; retain it if activity cannot be resolved safely.
6. Remove using `git worktree remove <absolute-path>`, **without `--force`**. If Git
   refuses, keep the worktree and report why; do not bypass the protection.
7. Inspect `git worktree prune --dry-run`, then run `git worktree prune` only for
   verified stale registrations. Do not prune metadata for active/offline worktrees.
8. Delete the local branch only if appropriate and safe with `git branch -d`.
   If ordinary deletion refuses (including squash/rebase history), retain the ref;
   never force deletion. No remote branch deletion is implied.
9. Report the removed/retained worktrees, absolute paths, branches, HEADs, checks
   and outcomes. Classify runtime/deployment directories and evidence archives
   separately; a `qh-` prefix does not identify a worktree.

Never use `rm -rf`, `git reset --hard`, `git clean -fdx`, force flags or equivalent
destructive cleanup to bypass these checks. Never remove runtime environments,
database resources/volumes, sensitive configuration or evidence archives. This
policy does not authorize any persistent QH data changes, deployment or auto-merge.

## Docker-first development

- Prefer Docker Compose for running services, installing dependencies and tests.
  The host only needs Docker with Compose v2; Python 3 is optional for generating
  a local `.env`. Use the root Makefile and README commands.
- Do not install runtimes or packages globally on macOS without authorization.
  If Docker is unavailable, identify the executable/daemon/permission blocker
  and mark affected checks NOT TESTED. Do not replace container tests with
  claims based on source inspection.
- Install Node dependencies with `npm ci` in the frontend image. Install Python
  dependencies from hash-locked `requirements.lock` files in their images.
  Commit manifests and regenerated lockfiles together; rebuild after changes.
- Use bind mounts for source hot reload; do not mount host dependency directories.
- Keep database ports unpublished and database containers on the internal data
  network. Application ports bind to loopback for this local POC.
- Keep credentials in ignored `.env` files and configuration keys in
  `.env.example`. Never commit secrets or include them in image build contexts.
- Do not delete database volumes or reset local data without explicit approval.
- `make migrate` runs Alembic `upgrade head`; its existence is not authorization
  to migrate persistent QH. Use an explicitly reviewed target for an authorized
  cutover. CI success does not prove dedicated PostgreSQL–Neo4j tests executed;
  consult the QH-30 evidence and test environment gates.
- Respect task-specific restrictions on container replacement. Use
  `make verify-running` for an existing stack when container recreation is not
  authorized.
