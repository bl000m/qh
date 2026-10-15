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
future feature worktrees may be temporary. Runtime management uses the frozen
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
- Remote pushes (including force pushes) and destructive resets require explicit
  approval. The Jira authorization rules above also apply.
- At ticket completion, list each commit's hash, message, purpose and checks.
- Prefer Medium reasoning when sufficient; increase for architecture, security
  or complex problems. Use targeted checks per unit and full verification at
  integration or when changes/failures justify it, not after every small edit.

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
