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
the owner authorized a VPS POC hot-reload transition on 2026-10-17:
frontend/backend use the QH-12 checkout with source binds; MCP retains c723d32
image-only operation. See [active POC procedure](docs/qh-development-stack.md).
The sole development checkout is /home/ubuntu/qh;
use one active task branch there under the Single Checkout Development Policy
below. Runtime management uses guarded `make dev-*` commands and private .env;
/home/ubuntu/qh-runtime/current remains the preserved image-only rollback bundle.
Keep the readonly root Keycloak realm import file unchanged. Future planning does
not authorize further persistent writes/deployment/retirement.
Read [post-cutover consolidation](docs/qh-semantic-consolidation.md) for the
approved three generic profiles, open descriptor contract, authorized structured selection and
applied 0005 and executed deployment evidence. Controlled registration is explicit; never infer new
SQL types or human validation from descriptors. Semantic meanings
are open-ended content, not mandatory registry types or the eleven QH-4 categories.
Optional specialized schemas/rules remain supported; never rewrite applied
migrations or immutable historical bindings to force a new vocabulary.

## Browse-first product decision

Read [ADR 0005](docs/adr/0005-browse-first-context-understanding.md) and the Product
Contract's browse-first amendment before changing understanding UX or retrieval.
Browsing is primary; search complements it. Preserve deterministic-preview versus
validated/generative synthesis distinctions, open data-derived groups, epistemic
states and progressive disclosure. No global counts from partial pages, semantic
inference from descriptors, or SQL-only graph bypass. Search QH-10's selector
contract remains distinct. The ADR and QH-12 report distinguish implemented/tested
capabilities from future work; never infer acceptance from the approved direction.

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
  PR, branch and checkout path (`/home/ubuntu/qh`); inspect local/remote Git state
  and prior evidence. If Jira is unavailable, report the blocker; never invent requirements.
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

A task is not DONE because tests pass. It is DONE when every Jira acceptance criterion has been verified, the PR has been reviewed and merged, and Jira has been updated accordingly. Never start the next task automatically.

| Workflow state | Meaning |
| --- | --- |
| IN PROGRESS | Implementation is in progress; required technical criteria remain unverified or unmet |
| READY FOR REVIEW | Technical acceptance criteria are verified and the PR is published, but it is not merged |
| DONE | Every Jira acceptance criterion is verified, the PR is reviewed and merged, and Jira is updated accordingly |

A merged PR with Jira closure still pending is not DONE; report that outstanding
closure explicitly. Jira writes still require explicit authorization. Do not infer
permission to transition Jira from this definition. For non-ticket maintenance,
report Jira as not assigned and the missing/owner-approved closure mapping rather
than inventing a key, claiming a Jira update or declaring DONE automatically.

Before reporting technical readiness, map every acceptance/Done criterion to
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
- Correct the current PR in its existing branch and checkout; do not create another
  branch or PR for an ordinary correction. Reuse existing implementations and
  evidence rather than duplicating work under another ticket or PR.
- Never merge automatically. After an explicitly authorized merge, verify the PR's
  actual merge and preservation of its work, safely synchronize `main` in the
  single checkout and report Jira closure separately. Legacy worktree retirement
  follows the transition safeguards below; a closed-but-unmerged PR never
  authorizes removal. Do not start another task automatically after closure.

### Required concise outcome report

At the end of every task, always report:

- Jira ticket (or explicitly not assigned), objective and verifiable Definition of Done.
- Code/files actually changed and relevant local commits, hashes and purpose.
- Checks executed, observed results and what they demonstrate, including limits.
- Each Done criterion satisfied/missing using the classifications above.
- Problems corrected autonomously, with cause and verified resolution (or none).
- Residual issues and proposed solutions, with priority and suggested Jira follow-up.
- Associated PR, branch, checkout path, HEAD and Git status; publication,
  review/closure and remote/local synchronization state.
- The next recommended action on the current task. Do not automatically propose
  starting the next ticket while the current one remains open.

## Versioning and verification

Read [main consolidation](docs/main-consolidation.md) and the later
[hot-reload decision](docs/qh-development-stack.md) before merge, checkout or
runtime-source changes. Frontend/backend now depend on this tree: stop only these
apps with `sudo -n make dev-stop` before any branch switch, verify they are stopped
and no other source-dependent process is active, then restart via `dev-up` only
after reviewing the selected branch's compatibility. The root readonly IdP bind remains.
The primary checkout may
be on the single authorized task branch; older instructions that require it to
remain on main are historical and superseded by this policy. Preserve the readonly
bind and private .env.
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
- Routine task-branch publication follows the Single Checkout Development Policy below.
  Other remote pushes, all force pushes and destructive resets require explicit
  approval. The Jira authorization rules above also apply.
- At ticket completion, list each commit's hash, message, purpose and checks.
- Prefer Medium reasoning when sufficient; increase for architecture, security
  or complex problems. Use targeted checks per unit and full verification at
  integration or when changes/failures justify it, not after every small edit.

## Single Checkout Development Policy

### One development directory and one active task

- All new development takes place directly in `/home/ubuntu/qh`, switching Git
  branches in that same directory. Keep one active local development branch,
  one Jira ticket and one development PR in the ordinary workflow. Do not create
  additional development worktrees or alternate working copies for new tasks.
- Read this checkout's `AGENTS.md`, relevant skills, ticket/comments and task
  instructions first. Confirm the previous task is DONE before starting the next,
  unless the user explicitly authorizes an exception. Existing #5/#7 worktrees
  are paused transition exceptions, not permission for parallel development.
- Before each task, verify no unsaved editor changes, tracked modifications,
  staged changes or untracked files at risk. Preserve ignored files and secrets;
  a clean ordinary Git status alone does not establish switch safety. Commit
  authorized work first; never silently stash, discard or overwrite local work.
- Inspect processes, open files, source/config bind mounts and runtime path
  dependencies before switching. Stop on incompatible activity, another active
  coding session or uncertain ownership; preserve the current branch and report
  the specific blocker. Never switch while a build/test/reload process depends
  on the current tree. Do not kill services or sessions implicitly.
- Fetch `origin/main`, safely select `main` and synchronize it by fast-forward
  only. Verify local `main` equals fetched `origin/main`; stop on divergence.
  Then create the task branch from that baseline or select the existing task
  branch after checking its base, local commits and associated PR. Never force
  a branch switch, reset/rebase published history or bypass an attached-worktree
  refusal. Do not create a new branch for a correction to the current PR.
- Code changes must be visible immediately in `/home/ubuntu/qh`. Always report
  that path, the active branch, HEAD and Git status. After a reviewed, authorized
  merge, return safely to updated `main`; closure never starts the next task.
- `scripts/start_task_worktree.py` is disabled, including its old plan/create
  modes. It must not create directories, branches or worktrees. Use the reviewed
  manual single-checkout preflight in [the workflow guide](docs/worktree-lifecycle.md).

### Runtime and publication boundary

- The owner-approved VPS POC runs frontend/backend from this checkout with hot
  reload. MCP remains image-only; `/home/ubuntu/qh-runtime/current` is the retained
  rollback bundle, not the active app configuration. Changes in app source become
  live before merge. Stop apps before branch switches; inspect actual mounts/processes.
- Preserve private `.env`, the frozen runtime bundle and readonly root
  `infra/keycloak/qh-realm.json`. Before a switch, verify the target branch keeps
  the same realm path and bytes and does not overwrite private/ignored files.
  Unexpected mounts or protected-file differences block switching until resolved.
- Use only guarded `make dev-up|dev-status|dev-logs|dev-restart|dev-stop` for this
  POC (with Docker permission). Never run `make up`, `make migrate`, `make verify`,
  `make oidc-up` or generic Compose lifecycle commands against the persistent stack.
  A branch switch grants no migration, seed, data-write or dependency replacement
  permission. Runtime rollback is a separately reviewed app-only operation.
- Publish verified, review-ready commits to the current task PR unless the user
  prohibits it. This authorizes ordinary publication of that task branch only,
  not force pushes, other task branches, tags/releases, Jira writes, merge or
  deployment. Explicit task restrictions take precedence.
- Preserve reports, tests and experiment evidence in Git or a documented durable
  destination. Keep secrets only in protected ignored configuration/private
  archives; never publish them. Frozen captures, references and ledgers remain
  immutable; relocation does not create new counters or paid-call authorization.

### Legacy worktree transition and safe retirement

- Preserve the PR #5 and #7 worktrees, commits, ignored files and evidence until
  their integration or an explicitly authorized, verified safe migration. Do not
  move their active branches forcibly. Preserve historical PR #1 and its refs.
- The PR #6 branch may be released from its clean legacy worktree by an ordinary
  detached checkout at the retained commit, then selected in `/home/ubuntu/qh`,
  after runtime/process/file preflight. Keep the detached directory as a snapshot;
  it is not a second active development directory. No cleanup is implied.
- A future migration of a legacy task requires clean/saved state, no conflicting
  session/process/mount, verified durable evidence/private-file copies and retained
  commit refs. Detach only without force, then select the existing branch in the
  primary checkout; verify identical commit/tree and original directory contents.
  If any check fails, retain the worktree and report; never bypass Git protection.
- Retirement after merge is separate: verify actual reviewed merge on GitHub,
  updated-main reachability and preservation of every branch-only commit (including
  squash/rebase mapping if applicable). Check tracked, untracked and ignored files,
  durable evidence, active sessions/processes/open files and all path dependencies.
  Then use ordinary `git worktree remove` without force; if refused, retain it.
- Preview `git worktree prune --dry-run`; prune only verified stale registrations.
  Delete a local branch only when safe with `git branch -d`; retain it on refusal.
  No remote branch deletion is implied. Never remove the primary checkout, runtime,
  database volumes, private configuration or evidence archives. No `rm -rf`,
  `git reset --hard`, `git clean -fdx` or forced cleanup/switch is permitted.

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
