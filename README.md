# QH

QH is a sovereign context platform: people preserve, query, govern and selectively
share persistent understanding through Context Spaces, independently of AI providers.
Stable identity, immutable revisions, explicit validation and traceable evidence keep
interpretations distinct from their sources and substantial decisions human-controlled.
A space can contain multiple domains without a separate schema for each.

## Implementation status

| Layer | State |
| --- | --- |
| Consolidated `main` | QH-30 and semantic foundation merged through PR #2/#3; 261 native hosted tests plus quality/OIDC passed |
| QH environment | Schema 0005; native backend/worker, frontend and MCP run versioned images from `c723d32` without application source mounts. Smoke, exact evidence, isolation, restart and pending-intent recovery passed |
| Semantic foundation | Three generic profiles provisioned; authorized exact descriptor selection active. Historical type bindings, canonical revisions and six Graphiti nodes preserved. [Deployment record](docs/deployments.md) |
| QH-8 feature branch | Offline conversation import/extractor/resolver, two interchangeable fake/replay providers, exact citations and generic proposed understanding. Isolated SQL/Neo4j verification; not deployed, no real LLM extraction |
| Mistral experiment branch | Four full synthetic Small 4 generations; 7/8 cumulative requests, 2,673 input / 5,922 output tokens, USD 0.00392283 cache-aware calculated usage charge. One of four QH batches accepted; 23/34 citation spans exact. Provisional reference, no independent validation. [Report](docs/qh8-mistral-evaluation.md) |
| Offline citation follow-up | One Understanding Engine/two governed inputs documented in ADR 0004; unique exact quote resolution on the four frozen captures raises contract-valid batches from 1/4 to 3/4. Missing evidence still rejects the full batch; semantic errors remain. [Follow-up](docs/qh8-citation-followup.md) |
| Future | Source Vault (QH-31), Domain Packs, verified real-provider extraction quality, embedding cache and advanced vector/hybrid retrieval; product context operations through MCP |

Graphiti is a preserved historical prototype, not a native-engine dependency.
The independent MCP server currently provides transport scaffolding, not a QH context
client. Deployed retrieval offers scoped substring search and an internal exact
descriptor selector: authorize → canonical IDs from SQL → Neo4j verification →
canonical hydration and freshness recheck. No public context DTO/API or semantic
ranking is implied. The sole development checkout is `/home/ubuntu/qh`, using one
task branch at a time. Deployed images and the frozen Compose bundle are independent of that branch.

## Architecture and data flow

The diagram describes the implemented QH-30 path, tested in isolation and activated
on the VPS at the pinned cutover commit. The worker
runs in the backend process; no broker or new microservice is required. Core stays
independent of FastAPI, database drivers and provider SDKs.

```mermaid
flowchart LR
    W[Internal authorized writer] --> R[Canonical repository]
    R --> T[PostgreSQL transaction: revisions and outbox intent]
    T --> PG[(PostgreSQL)]
    PG -->|claim committed intent| Worker[Backend incremental worker]
    Worker -->|affected assertions only| N[(Neo4j)]
    Worker -->|acknowledge or retain retry state| PG
    Q[Context request] --> P[PolicyService]
    P -->|allow before retrieval| E[Native retrieval]
    E -->|check sync state| PG
    E -->|scoped candidates| N
    N --> H[Hydrate exact candidates and recheck freshness]
    H --> PG
    H --> Result[Authorized result]
```

Canonical publication and projection intent commit atomically. Leases, per-space
sequences and epochs make retries idempotent and fence stale workers. Pending,
failed or mismatched projection state blocks retrieval, including empty results.
Queries do not require full reconciliation. Explicit rebuild/audit remains available;
normal readiness checks do not certify arbitrary manual graph corruption.

## PostgreSQL model through 0005

This simplified ERD describes deployed schema **0005**. It preserves all 0004
tables; 0005 removes only the unused null legacy category column/check. Composite foreign keys enforce matching space and stable-ID/revision
anchors. Revisions, provenance, type schemas and semantic rules are immutable;
unknown fact/validity times stay null and are separate from acquisition metadata.

```mermaid
erDiagram
    users ||--o{ user_identities : maps
    users ||--o{ context_spaces : owns
    context_spaces ||--o{ sources : contains
    sources ||--o{ source_revisions : versions
    context_spaces ||--o{ understanding_items : contains
    understanding_items ||--o{ understanding_item_revisions : versions
    understanding_item_revisions ||--|| item_revision_types : binds
    semantic_type_versions ||--o{ item_revision_types : validates
    understanding_item_revisions ||--o{ item_revision_provenance : cites
    source_revisions ||--o{ item_revision_provenance : supports
    understanding_item_revisions ||--o| relation_revision_details : describes
    understanding_item_revisions ||--o{ relation_revision_details : anchors_endpoints
    context_spaces ||--|| context_projection_state : tracks
    context_spaces ||--o{ projection_outbox : queues
    understanding_items ||--o{ projection_outbox : changes
```

0003 adds three canonical tables: `semantic_type_versions`, `item_revision_types`
(type binding and universal temporal bounds), `relation_revision_details` (universal
item endpoints). No entity marker table is needed. 0004 adds two reconstructible
operational tables: `projection_outbox` and `context_projection_state`. The outbox
also references exact revisions where applicable. See [SQL details](docs/postgres-schema.md).

## Neo4j operational graph

Actual labels and assertion edges in the native adapters:

```mermaid
flowchart LR
    I[QH30Item: stable ID and selected heads]
    R[QH30Revision: immutable assertion]
    A[QH30Revision: source anchor]
    B[QH30Revision: target anchor]
    S[QH30Source: exact source revision reference]
    R -->|EVIDENCED_BY| S
    R -->|SUBJECT| A
    R -->|OBJECT| B
    I -. head properties reference revision IDs .-> R
    Slice[QH30Slice] -. active_generation property .-> G[QH30Generation]
    Sync[QH30Sync: scope epoch and applied version]
```

Dotted lines explain properties, not additional Cypher relationship types.
Relation endpoints can reference any registered item shape. PostgreSQL remains the
semantic and authorization authority; Neo4j retains operational assertions, evidence
references and synchronization markers. Rebuild uses canonical data without LLM calls.
Original-byte storage and access policy belong to future QH-31, not this graph.

## Development and verification

Develop only in `/home/ubuntu/qh`, with one active task branch, Jira ticket and
PR at a time. Before each task, check clean/saved state and runtime/process safety,
fast-forward `main` from `origin/main`, then create or select the task branch.
Do not switch with unsaved changes or incompatible processes. Follow the
[single-checkout workflow and legacy transition](docs/worktree-lifecycle.md).
The old worktree bootstrap is disabled; existing PR #5/#7 directories remain
preserved transition exceptions. No branch switch authorizes runtime changes.

Tests passing is technical evidence. Report **IN PROGRESS**, **READY FOR REVIEW**
(verified technical criteria, published PR, unmerged), or **DONE** only when every
Jira acceptance criterion is verified, the PR reviewed/merged and Jira updated.
Never start the next task automatically; Jira writes and merge need authorization.

Use Docker Engine and Compose v2; dependencies install from committed lockfiles
inside images. Keep credentials in ignored local `.env`, never in Git or logs.
For a new local checkout, generate configuration with `python3 scripts/init_env.py`;
inspect the checkout/configuration before starting any separately authorized services.

- `make config`: validate Compose without printing credentials.
- `make up`: build/start the development stack; use only when container changes are authorized.
- `make verify-running`: verify an existing stack without rebuilding/replacing containers.
- `make verify`: build/start plus existing quality checks; not proof of dedicated QH-30 integration coverage.
- `make migrate`: **Alembic `upgrade head` against the configured database**. This command is not authorization to migrate persistent QH. A cutover must use the explicitly approved target/commit and configuration.

API startup does not migrate. Preserve database volumes; never add volume deletion
as routine cleanup. Do not point isolated tests at persistent QH. Dedicated QH-30
server names, opt-in variables, executed results, reproduction commands and the
strict integration CI job are in the [QH-30 checkpoint](docs/qh-30-plan.md).
The new `native-integration` job runs the strict disposable SQL/Neo4j suite and
fails on skips. Hosted run [38736085229](https://github.com/bl000m/qh/actions/runs/38736085229)
retains the earlier 178-test result. The consolidated main run
[38774841579](https://github.com/bl000m/qh/actions/runs/38774841579) passed all three
jobs and 261 native cases without skips. A green
quality/OIDC gate alone does not establish integrated coverage. Native runtime is
opt-in through `QH_NATIVE_CONTEXT_ENABLED`; the historical fd50 image requires 0004.
The consolidated runtime accepts 0004/0005; startup never migrates. The VPS is at 0005;
never restart its incompatible historical fd50 image. The
[deployment register](docs/deployments.md) records executed activation and recovery.
For VPS management use the frozen `/home/ubuntu/qh-runtime/current` Compose bundle
with its image pins and existing private .env, not default development `make up`.

## Modules and technical references

| Path / reference | Responsibility |
| --- | --- |
| `apps/api/app/core`, `app/policy` | SDK-free contracts and owner authorization |
| `apps/api/adapters/postgres` | Canonical repository and additive migrations |
| `apps/api/adapters/context` | Native graph projection, incremental worker and retrieval |
| `apps/web`, `services/mcp-server`, `packages/shared` | Web scaffold, independent MCP transport, public wire types |
| [Product Contract](docs/product/QH_PRODUCT_CONTRACT.md) | Mandatory functional invariants |
| [Main consolidation and image-only deployment](docs/main-consolidation.md) | Merge gates, checkout safety, tested Compose override and separately authorized activation |
| [CHANGELOG](CHANGELOG.md), [versioning and milestones](docs/versioning.md), [deployments](docs/deployments.md) | Unreleased changes, release discipline and executed/candidate artifact history |
| [Architecture](docs/architecture.md), [ADR 0003](docs/adr/0003-native-context-engine.md) | Boundaries, decision succession and native-engine approval gates |
| [AGENTS](AGENTS.md), [ticket skill](.agents/skills/jira-ticket-workflow/SKILL.md) | Development, authorization and evidence rules |
| [OIDC setup](docs/qh-5-authentication.md), [adapter notes](apps/api/adapters/README.md) | Detailed setup and internal integration boundaries |

Earlier `docs/verification-*` reports retain dated evidence, not current deployment
inventories. [Cutover evidence](docs/qh-30-plan.md#persistent-cutover-execution-and-read-only-historical-inventory)
records the active image, synthetic IDs and Graphiti integrity. Real-provider extraction,
embedding and advanced semantic retrieval remain future work; no further deployment is implicit.

## QH-8 offline demonstration

[QH-8 implementation and acceptance](docs/qh-semantic-consolidation.md#qh-8-offline-implementation-and-acceptance)
uses three synthetic three-turn conversations (project, health report, family) in
one space: conversation → interchangeable extractor → exact citation/endpoint
validation → generic proposed items → PostgreSQL/outbox → existing worker → Neo4j
→ authorized descriptor selection and canonical hydration. No external call occurs.

Run on **disposable infrastructure only**, from the feature checkout:

```bash
python3 - <<'PYENV'
import os, secrets
with os.fdopen(os.open('/tmp/qh8-test.env', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as f:
    for key in ('QH30_SQL_PASSWORD', 'QH30_GRAPH_PASSWORD'):
        f.write(key + '=' + secrets.token_hex(24) + '\n')
PYENV
docker compose --env-file /tmp/qh8-test.env -p qh8-ci \
  -f infra/docker/qh30-integration.yml build integration
docker compose --env-file /tmp/qh8-test.env -p qh8-ci \
  -f infra/docker/qh30-integration.yml run --rm integration
# Optional visible demo; this creates/deletes only its unique test databases.
docker compose --env-file /tmp/qh8-test.env -p qh8-ci \
  -f infra/docker/qh30-integration.yml run --rm --entrypoint python integration \
  -m pytest -q -s -p no:cacheprovider \
  tests/test_understanding_pipeline.py::test_three_domains_two_providers_atomic_outbox_and_structured_retrieval
# Remove only this disposable project, never the VPS qh project.
docker compose --env-file /tmp/qh8-test.env -p qh8-ci \
  -f infra/docker/qh30-integration.yml down
```

The demo prints synthetic scope/source/revision IDs and readiness. Tests verify
exact IDs/evidence across process restart and graph rebuild before their own
cleanup. The full strict entry point fails on unavailable infrastructure or skips.
A successful fake/replay demonstration does not establish real-model quality.

## QH-33 offline semantic evaluation

[QH-33 benchmark and review limits](docs/qh33-semantic-evaluation.md) separates
source-proposition coverage, semantic support, agency, negation, time, uncertainty
and provenance. All semantic labels are assistant proposals pending independent
human review. Frozen Mistral/QH-32 artifacts remain unchanged; new paired authored
controls are not model outputs. Tests and valid citations never establish truth.

```bash
# Stdlib-only: no key, HTTP, database, provider or canonical writes.
python3 scripts/evaluate_qh33.py --out /tmp/qh33-review --prepare-protocol
```

The output directory must be new. Source-first material, blank human-review grid
and separate draft metrics are reproducible; durable copies are committed under
`docs/evidence/qh33-semantic-20261016/`. Prepared requests are a proposal only;
no live execution mode is provided. The [current scope proposal](docs/qh33-closure-scope.it.md)
defers complete human validation to QH-38; QH-33's Jira description still needs
formal scope alignment before closure. Reviewed merge and Jira closure remain
pending. No subsequent task starts automatically.


QH-33 v2 applies owner-approved D1–D5 while keeping the original benchmark sealed.
Use the [74-unit personal-review matrix](docs/evidence/qh33-v2-20261016/review-matrix.it.md)
and [package instructions](docs/evidence/qh33-v2-20261016/README.md). Owner approval
of the rubric does not attest personal review; all human judgments remain pending.
Reproduce with `python3 scripts/evaluate_qh33_v2.py --out /tmp/qh33-v2-review`.
