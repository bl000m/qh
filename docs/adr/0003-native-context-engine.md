# ADR 0003 — Native QH Context Engine and rebuildable Context Graph

Date: 2026-10-15
Status: architecture direction authorized by the owner through
[QH-30 / QH-7b](https://contextlab.atlassian.net/browse/QH-30).
The owner has approved a single versioned type registry and stable identities with
immutable revision references, universal endpoints and temporal metadata. The owner
authorized incremental implementation/testing on a dedicated disposable database.
Migration 0003 is implemented with three tables; **persistent QH application and
public contract changes remain unauthorized**.

## Context and supersession

QH-30 replaces Graphiti as a runtime interpretation/retrieval dependency with a
native, modular QH Context Engine. PostgreSQL remains the sole canonical authority;
Neo4j becomes the explicitly operational, rebuildable Context Graph. This is not
the SurrealDB spike, and does not adopt its experimental schema or conclusions.

ADR 0001 dependency direction, existing Core ports, the QH-4 revision/validation
model and the identity/PolicyService decisions of ADR 0002 remain in force.
Superseded: ADR 0001's concrete choice of a future Graphiti library, references to
Graphiti owning extraction/semantic objects, and QH-8's need for an engine episode
mapping. Refined: QH-4's PostgreSQL authority explicitly includes semantic entities
and relations; it does not imply copying the complete operational graph to SQL.
QH-4's historical no-native-engine limit governed QH-4, not this new ticket.
No existing migration is rewritten.

Preserve `feat/QH-7-graphiti-context-engine` at `77de43c` and its Draft PR #1;
this branch starts at main `b1769b6`, with no cherry-pick of the prototype. The
compatibility map is inspectable with `git show 77de43c:docs/qh-7-graphiti.md`
(section “Compatibilità e punti di sostituzione”). Preserve the separate
`spike/qh-surrealdb` worktree; it supplies no production dependency here.

## Authority, ownership and data partition

| Data | PostgreSQL canonical | Neo4j operational projection |
| --- | --- | --- |
| Identity, Context Space ownership, policy/approval facts | QH users, OIDC mapping, space ownership and approved governance facts; PolicyService decides access | Context Space IDs for query filtering; no independent owner/authorization authority |
| Sources and source revisions | Original immutable content, origin and exact revision identity | Source/revision identifiers and useful locators; no full source-copy requirement |
| Understanding Items and revisions | Stable item ID, revision ID/number, registered type/version, structured content, origin, validation/actor/time, predecessor, confirmed-current pointer | Relevant revision text/properties, registered type/version/state and canonical references for retrieval |
| Semantic entities and relations | Stable identities, immutable assertion/revision data, endpoint identity, grounded event times and provenance; schema tested only in isolation | Revision/identity nodes, typed edges, traversal shortcuts and selected denormalizations; never independent edits |
| Embeddings | Reusable, versioned derived artifact/cache keyed by canonical revision/content hash + provider/model/version/dimension/configuration | Vector and index configuration necessary for retrieval; can be repopulated from the cache |
| Projection/sync metadata | Durable work intent, canonical version being projected and progress/error records (proposed additive schema) | Projector version/generation and applied canonical version, useful indexes |

An embedding is not an authoritative semantic assertion. Cache persistence location
and SQL shape require review, but retained artifacts are necessary for a rebuild
with **zero LLM/embedding API calls**. If vectors were not retained, rebuild the
text/graph portion and mark vectors unavailable; never silently call a provider.
Change of embedding model invalidates that cache/index configuration, not sources
or canonical understanding. No arbitrary canonical graph copies or second editable
truth. Owner IDs on child records derive from their space, not independent copies.

## Universal semantics, extensions and independent governance

Owner decision recorded in the updated QH-30, QH-8 and QH-10 tickets on
2026-10-15: QH is domain-neutral. Professional, health, family and personal
contexts use the same persistence and engine boundaries; a Context Space can mix
these domains. `decision`, `hypothesis` and `open_question` are initial types,
not a closed ontology.

The universal nucleus carries stable item/entity identities, immutable revisions,
relations with explicit endpoints, exact evidence, supported event time distinct
from acquisition time, uncertainty and validation. Model confidence, source
reliability and human validation are separate dimensions. An AI inference remains
a proposal; a symptom is not a diagnosis and a declared preference is not an
inferred personality trait. Governance/PolicyService remains independent of type:
a domain label never grants access or approval.

Semantic type identifiers and immutable schema versions describe extensible
properties; neither Core enums nor database-per-domain schemas define the ontology.
Unknown type/version or invalid properties must fail validation, without coercing
into a known type or silently selecting the latest schema. Retain older schemas
for historical revisions. Stable scope/provenance/endpoint constraints remain
relational constraints, not optional JSON conventions. The concrete additive SQL
mapping is implemented/tested in isolation as recorded in the QH-30 plan;
persistent application remains a separate approval gate.

Neo4j uses generic revision/entity/relation structures and type/predicate values as
data; adding a vocabulary must not require dynamic Cypher labels, a new database
or a second interpretation. Graph projections retain schema version and canonical
references, then hydrate through the authorized canonical repository.

Future **Domain Packs** may compose namespaced vocabularies, versioned schemas,
extraction instructions and specialized rules. They are optional extensions, not
exclusive Context Space kinds, authorization systems or new services. No pack
runtime, domain-specific Core module or domain workflow is implemented here.
Conflicting pack schemas must not reinterpret an existing immutable type version.

## Canonical model approved; isolated implementation (2026-10-15)

This review supersedes the initial proposal of eleven fixed broad categories plus
semantic subtypes, and revision-only relation endpoints. It does **not** amend the
historical QH-4 migration. The owner subsequently approved the model and isolated
migration tests; persistent application remains gated. See the concrete alternatives,
constraints and migration gates in [QH-30 plan](../qh-30-plan.md).

Recommend a single immutable type/version registry and one binding per item revision;
replace the eleven-category CHECK rather than force new types into old buckets.
A small item/entity/relation structural shape selects integrity constraints and is
independent of domain/semantic classification. Historical category values remain
unchanged as deprecated metadata; new revisions use only the registered type binding.
No free-form unknown types, automatic latest schema or duplicated classification.

Recommend relation endpoints as stable Understanding Item IDs **and** required
immutable item revision anchors. Composite same-space FKs target QH-4
understanding_item_revisions directly and prove ID/revision/scope agreement.
Endpoints can be decisions, constraints, observations, entities, events, states,
preferences, intentions or other registered types; they are not universally
entity-to-entity. Versioned semantic rules constrain allowed pairs/predicates on
the canonical write path, independently of universal SQL referential integrity.
Anchors preserve the interpretation at assertion time; later descriptions need no
canonical relation rewrite. A different referent requires a new relation revision.
Deduplication must preserve old IDs/anchors and explicit scope, not silently merge
history. Generic Neo4j projections preserve identity and assertion separately.

The three implemented tables are semantic_type_versions, item_revision_types
and relation_revision_details. No entity_revision_details marker is needed: the
registered structural shape and publication guard already distinguish entity
revisions, and endpoint FKs directly enforce item/revision/scope agreement. Publication retains immutable
assembly, exact provenance, actor/state and confirmed-current checks. Property
schemas are validated by deferred SQL publication using the explicit limited
qh-schema-1 profile (not full JSON Schema); unsupported keywords/references fail.
SQL also checks structural integrity, never textual entailment. Immutable relation
rules are pinned to the relation type/version, with exact predicate and anchored
endpoint type/version allowlists, or explicit historical any_registered behavior. Legacy compatibility
schemas/bindings must not rewrite old content, and incomplete legacy relations block
migration until reviewed. Real SQL regressions now verify these constraints and the legacy backfill; the
fixture graph is also verified with universal endpoints and stable-ID agreement.
No production PostgreSQL-to-Neo4j repository/outbox is activated.

## One logical interpretation, separate transactions

1. Authenticate and apply the existing general permission gate plus PolicyService
   to the requested operation/scope **before** reading protected content or sending
   it to any provider. For unsupported actions the current policy still denies;
   this ADR does not implement new policy actions or public ingestion routes.
2. Save/revision the source using QH-4 identity/provenance rules. Capture original
   content, source locator and technical acquisition time. A failed interpretation
   does not erase that source or imply understanding was created.
3. The Understanding Extractor interprets the authorized revision into typed QH
   proposals. One logical interpretation job may require explicitly bounded calls;
   it does not mean one HTTP call or allow Neo4j to reinterpret it. No DB transaction
   stays open during LLM work. Provider access remains default-deny unless a single
   call or scoped experiment is explicitly authorized with count and budget.
4. Knowledge Resolver validates schema, evidence, endpoints and scope, resolves
   stable entities conservatively, records ambiguity/conflict instead of guessing,
   and constructs canonical proposals. A match/dedup/contradiction decision must
   be explainable; it must not silently merge identities or confirm an AI claim.
5. Canonical Repository commits the affected records/revisions/provenance and a
   durable projection intent atomically in PostgreSQL. Preserve QH-4 provenance
   assembly-before-publication and immutable revisions. An optimistic expected
   revision/content fingerprint prevents publishing against silently changed input.
   Interpretation failures never become a fully successful ingestion.
6. Context Graph Projector reads committed canonical data in batches and projects
   incremental changes into Neo4j, with explicit version/generation keys and
   idempotent operations. No extraction or provider call in this stage.
7. Semantic Retriever authorizes scope before candidate generation, searches
   selected text/vector indexes and traversal paths, then bulk-hydrates/revalidates
   canonical revisions, state, provenance and permitted disclosure. Return existing
   QH values; a new public state/ranking DTO requires separate approval.

## Revision, provenance and time semantics

The same QH item can have proposed/rejected/confirmed immutable revisions. A new
proposal does not move the confirmed-current pointer. Semantic type and validation are
independent; confirming a hypothesis does not certify it as a true fact. Historical
evidence refers to exact revisions. The revised proposal above records stable
item identities plus exact historical endpoint anchors; ordinary item description
updates do not require new relation revisions. A change of referent or validation
creates a new revision, not an in-place mutation of an old assertion.

Evidence resolves to source revision IDs in the same Context Space. Locators/spans
are checked against original text when available; provenance and interpretation
remain distinct. A relation cannot cite missing/out-of-scope entities. Do not
repair a failed extraction by inserting a missing entity or fabricated fact.

Keep technical acquisition/processing times distinct from event/validity times.
Unknown event time stays null. Explicit or genuinely relative source time can be
resolved with documented evidence; present tense alone is not proof of event
start at ingestion. Never strip a supported semantic date to make a test pass.

Universal temporal assertions live in the already mandatory `item_revision_types`
row: nullable timestamptz `fact_from/fact_to` for occurrence and `valid_from/valid_to`
for applicability, on **all** item revisions. Relations no longer own special time
columns. Occurrence allows equal bounds for an instant; known validity bounds form
a nonempty half-open interval. Null is unknown/unspecified, never an automatic
unbounded validity assertion. Date-only precision must not become an invented
midnight instant; preserve source granularity in validated content. Acquisition
remains source origin metadata, and created_at remains technical persistence time.
No semantic defaults derive from either, and no new temporal table is needed.

Temporal changes require new revisions and source-backed grounding. Neo4j carries
these common fields for scoped temporal retrieval; historical reconstruction uses
selected canonical revisions and exact endpoint anchors. Query handling of unknown
times must be explicit. This does not promise full bitemporal storage or treat
created_at as an exact database commit time. The SQL checks and migration handling
are specified once in the QH-30 plan.

Which proposal revisions are retrieved is an explicit query/application policy,
not “all are current” or “everything is confirmed”. The initial fixture slice
uses an explicit set of revision IDs with validation retained internally. It does
not define an unapproved public latest/proposal selection contract.

## Synchronization, recovery and read correctness

There is no distributed ACID transaction across PostgreSQL and Neo4j. PostgreSQL
commit is authoritative; a failed projection leaves durable pending/failed work,
not a rolled-back canonical decision or a misleading ready result. Use a
transactional outbox when persistent incremental processing begins, with a backend
worker in the same service initially. No new broker/container is required.

Delivery is at-least-once. Work identifies canonical scope/revision and projector
version. The worker re-reads authoritative state; old deliveries cannot regress an
already applied version. MERGE keyed by QH revision/identity and transactional graph
updates prevents duplicates/partial projection. Record pending/projecting/ready/
failed or equivalent states, lag, attempts and a redacted cause. Count-only health
checks do not establish consistency. Operational local DB retry policy is separate
from paid-provider retry authorization.

If Neo4j commits but acknowledgement fails, replay is safe. PostgreSQL intent and
cache survive graph loss. For rebuild: select an explicit canonical snapshot/set,
load a new graph generation in bounded batches, include cached embeddings, validate
counts/IDs/provenance/checksums, then atomically switch the active generation. Keep
old generation until checks pass; a crash cannot expose a half-built replacement.
No global Context Space domain revision/event-sourcing system is introduced.

Search can lag canonical writes. Before disclosure, remove stale/foreign/deleted
candidates and verify references against PostgreSQL/current policy in bulk.
Revalidation prevents stale positives, but cannot recover newly committed facts
missing from a lagging index: report projection readiness/lag and fail/defer a
read-after-write guarantee until the required projection is ready. Never disguise
an empty/stale graph result as a fresh canonical absence. Exact public readiness
representation is pending contract review; the first internal slice raises a local
error on graph/canonical disagreement. A graph outage must not damage canonical data.

## Modules and existing contracts

| Responsibility | Boundary / next implementation |
| --- | --- |
| Understanding Extractor / Knowledge Resolver | QH application logic and SDK-free internal data, depending inward on existing Core; provider-specific decoding/HTTP belongs in outbound adapters |
| Canonical Repository | PostgreSQL adapter reusing QH-4 schema; application orchestrates commits; new repository/schema shape requires review before deployment |
| Context Graph Projector | Outbound Neo4j implementation in `apps/api/adapters/context`; internal project/rebuild functions, not a new Core ingest port |
| Semantic Retriever | Existing `ContextEngine.search(ContextQuery) -> ContextResult`; an authorized application boundary uses existing `PolicyService`; no SDK objects in Core |
| Composition | Explicit backend assembly, initially manual/test only; no production route, startup migration or worker activation in this milestone |

`ContextService`, `LLMProvider`, `ContextEngine`, OIDC and PolicyService signatures
are unchanged. Existing LLMProvider does not expose a structured extraction schema
contract; do not overload it or add public methods before review. Future internal
typed extraction interfaces can be proposed without changing Core now. MCP remains
an authenticated backend adapter, never a direct database client.

## Lessons retained from QH-7

Retain requirements/tests for native structured-output validation, cautious entity
resolution, complete endpoints, grounded dates, contradictions, exact source
revision provenance, scope enforcement, cause-preserving diagnostics, safe offline
replay and bounded cost authorization. Native Mistral structured output is an
adapter choice, not a Core type. Historical 3B/8B responses are regression evidence,
not trusted canonical fixtures or authorization to repeat paid calls.

Do not bring over Graphiti UUID episode precreation, `group_id`, prompt phase names,
retry subclass overrides, recipe copies, private OpenAI strict converter or SDK
transport monkey-patches. Stable QH IDs replace engine-derived episode mappings.
Entity resolution and contradiction handling were requirements/partially diagnosed
in the prototype, not capabilities already implemented by QH-30.

## Trade-offs and alternatives

PostgreSQL ACID integrity/immutable provenance gives one repairable source of truth;
Neo4j gives traversal and independent text/vector read indexes. Costs: duplicated
retrieval properties/vectors, write amplification, async lag, hydration and recovery
logic. Bulk upserts/hydration avoids N+1; rebuild needs temporary disk/RAM for two
generations. Indexing/warm-cache latency and vector dimensions must be measured on
comparable workloads; no performance claim follows from this ADR.

Keep Graphiti: less custom initial engine code, but prototype-private hooks and
runtime extraction coupling remain. Use SQL only: simpler operational consistency,
but no demonstrated equivalent rich traversal/read performance. SurrealDB: separate
unfinished spike, not an approved replacement or evidence of equivalent governance.
The owner chooses PostgreSQL + native Neo4j now; no migration to another database.

## Milestones and approval boundary

1. This ADR plus [QH-4 delta and Jira realignment proposal](../qh-30-plan.md).
2. A first fixture-backed native projection/retrieval slice: real Neo4j tests for
   idempotence, reconstruction, restart, scope/provenance; no canonical migrations,
   no extraction and no live vectors. A fixture is not deployed PostgreSQL persistence.
3. Canonical model is approved and migration 0003 tested only in isolation. Next:
   explicit persistent-application approval, transactional persistence/
   outbox/cache and recovery; then native extraction/resolution and advanced hybrid
   retrieval. QH-8 retains the three persistent typed Understanding Items demo.

Stop before applying migration 0003 to the **persistent QH database** or changing
public contracts. Only the disposable QH-30 test database is authorized. The detailed SQL model,
embedding artifact storage, outbox implementation and lifecycle selection remain
subsequent review points. Registration/publication currently requires READ COMMITTED;
other transaction isolation modes fail closed. This migration is forward-only and downgrade is refused; use a reviewed restore
or forward repair because the old CHECK cannot represent arbitrary new types. This ADR does not mark QH-30 or QH-8 Done.
