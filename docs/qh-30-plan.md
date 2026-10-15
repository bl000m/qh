# QH-30 / QH-7b — canonical delta and first native increment

Reference: [QH-30](https://contextlab.atlassian.net/browse/QH-30), read in full
through Atlassian MCP on 2026-10-15; no comments or linked issues. QH-4, QH-7 and
QH-8 descriptions/dependencies were read too. [ADR 0003](adr/0003-native-context-engine.md)
records the architecture direction. Everything labelled proposed below needs
canonical-model review before migrations. This is not a Jira update.

## Baseline and preserved work

New branch `feat/QH-30-native-context-engine`, worktree `/tmp/qh-30`, from main
`b1769b6`. Graphiti branch remains at `77de43c`, Draft PR #1 is untouched and never
merged; no prototype source/dependencies cherry-picked. SurrealDB worktree
`/tmp/qh-surrealdb` and its uncommitted files remain intact. The interrupted spike
is not a completed experiment and supplies no architecture/performance conclusion.
No QH database, volume or existing container is migrated, reset or replaced.

## Actual delta against QH-4

| Requirement | Already implemented | Actual gap / proposed change |
| --- | --- | --- |
| Stable scope/ownership | users, context_spaces; child ownership derives from the space; OIDC mapping added by QH-5 | No new owner/auth tables or PolicyService |
| Original evidence | sources/source_revisions: UUID, revision number, original text, origin JSONB, created_at; unique/composite FK and immutable rows | Source locator/acquisition metadata may use existing origin JSONB; no engine episode mapping needed |
| Typed understanding | understanding_items identity; immutable understanding_item_revisions with 11 categories, including entity/relationship | Existing categories alone do not enforce typed entity endpoints in SQL |
| Revision/validation | predecessor same item; proposed/confirmed/rejected plus actor/time checks; nullable current pointer accepts confirmed same-item revision only | Reuse; AI proposal cannot overwrite current; no global Context Space revision |
| Provenance | item_revision_provenance, exact source revision and same-space FKs; immutable publication, advisory-lock assembly-before-revision | Reuse, including for entity/relation revisions; optional precise citation validation against source content remains application logic initially |
| Semantic entities | entity-category revisions can already hold structured content | Proposed typed extension marking a revision as an entity; no separate owner, identity or validation copy |
| Semantic relations | relationship-category content JSONB can encode a relation, but SQL cannot enforce JSON endpoint membership/type/scope | Proposed typed relation extension with entity-revision FKs, predicate and nullable supported event bounds |
| Projection/sync | No outbox, projector generation/version/progress tables | Fixture slice needs none; persistent processing needs an additive durable intent/progress design, reviewed before migration |
| Rebuild without paid calls | Original content/revisions already independent of engine | Canonical entity/relation content plus retained versioned embedding artifacts/cache missing; do not call LLM during rebuild |

Evidence: `apps/api/adapters/postgres/migrations/versions/0001_qh_schema.py` and
`0002_oidc_identities.py`, [schema notes](postgres-schema.md). No live inventory
or migration rerun was needed to discover these code/schema gaps.

## Minimum canonical schema proposal — not implemented

Recommendation: extend existing entity/relationship **item revisions**, rather
than add another parallel entity/relationship identity + revision system. Reuse
all QH-4 origin, validation, provenance and current-pointer semantics.

1. `entity_revision_details(item_revision_id, context_space_id)`: typed marker with
   PK on revision ID, same-space FK to understanding_item_revisions, and unique
   pair for endpoint references. Category must be entity. Labels/aliases/structured
   attributes stay in the existing versioned content JSONB, not a second copy.
2. `relation_revision_details(item_revision_id, context_space_id,
   source_entity_revision_id, target_entity_revision_id, predicate,
   valid_from, valid_to)`: PK/FK to a relationship-category revision, endpoints
   reference entity_revision_details with the same space; nonempty predicate,
   nullable timestamptz event bounds and sensible ordering when both are present.
   These typed columns are authoritative for endpoint/predicate/time; do not also
   keep conflicting structured copies in content JSONB. Content can hold prose,
   uncertainty or qualifiers. No ontology or fuzzy-name uniqueness in SQL.

Recommended endpoint choice **for review**: exact immutable entity revision IDs.
Stable entity item IDs can be obtained through those revisions, so historical
endpoint meaning does not drift when names/resolution change. Alternative: stable
entity item IDs only (less coupling, but historical label/resolution must be
resolved separately). Do not silently choose the latter or rewrite old relations.
Both proposed and confirmed entity revisions may be referenced with explicit state;
referencing a proposal does not confirm it. No cross-space relation, even if both
spaces have the same owner. Self-relations are not prohibited without a domain rule.

New detail rows must be frozen alongside their parent revision, not appended after
publication. Follow QH-4's deferred FK + transaction-scoped advisory-lock assembly
pattern: provenance and detail rows first, immutable revision publication last,
with endpoint existence/type/scope checked by constraints/triggers. Extend the
publication guard only after review; a normal immediate FK or an after-the-fact
application-only check would not preserve the existing publication invariant.
Deletion/update/truncate must not silently mutate old assertions.

This is a two-table semantic delta, not two complete entity stores. Alternative
with zero tables: store endpoints/predicate in JSONB and rely on application
checks. It is suitable for fixtures but **not recommended** as the canonical
production model because endpoint/type/scope integrity is not guaranteed by QH-4
SQL today. A separate entity identity/revision hierarchy duplicates existing QH
concepts and is not justified for this increment.

Temporal evidence must be attributable to a cited source revision/locator; unknown
bounds remain null. Existing created_at is technical publication metadata, not the
fact date. Preserve original acquisition time in source origin when distinct.
Precise locator/spans need application validation; no schema column is silently
claimed to prove textual entailment.

Outbox/progress and embedding cache are additional **operational persistence**
needs, not included in the two semantic tables: propose a transactional job/intent
row referencing canonical revisions with state/attempt/cause/version, and retained
embedding artifacts keyed by revision/content hash and model/config/dimension.
They must be reviewed before persistent projector deployment. No generic event
sourcing, broker, worker container, graph ID mapping or public repository port.

## First increment and approval boundary

Implement a narrow internal native Neo4j projector/retriever with a synthetic
canonical fixture shaped as existing QH-4 item revisions and provenance. The
fixture represents the canonical input; it is explicitly **not** new PostgreSQL
storage. No unresolved entity extension is persisted or presented as approved.
Project revision IDs/state/provenance into Neo4j and retrieve existing QH hits
through an authorized wrapper using PolicyService. Test duplicate apply, stale
input, missing/foreign provenance, deletion/rebuild of only the fixture generation,
restart of only a disposable test DB and isolation. No production startup binding.

Do not build extraction/resolution/LLM/embedding adapters in this milestone. Full
text/vector/traversal fusion, real canonical writer/outbox/cache, advanced entity
matching/contradictions and readiness DTOs remain subsequent QH-30 increments.
Public QH contracts and migrations are unchanged. The only schema/model approval
requested at this milestone is the two typed extension tables and endpoint choice;
actual migration application needs explicit authorization afterwards.

## Proposed Jira realignment — text/dependencies only, not posted

| Ticket | Proposed revised scope / acceptance | Proposed dependencies |
| --- | --- | --- |
| QH-7 | Preserve Graphiti as historical technical prototype/PR #1; record supersession by QH-30 and unfinished live grounding result. Do not label its original real-smoke DoD passed or merge its code. Keep valuable regression evidence. Status/resolution requires owner decision. | Keep historical QH-2/QH-3 links; replace downstream active implementation dependency with QH-30 after approval |
| QH-30 (QH-7b) | Native engine direction/ADR + approved canonical delta + first fixture-backed projection/retrieval; subsequent persistence/extraction/hardening tracked explicitly, without claiming already delivered. | Proposed prerequisites QH-2, QH-3, QH-4; reuse QH-5/QH-29 identity/policy. No hard dependency on completing the Graphiti smoke or SurrealDB spike |
| QH-8 | Import at least three synthetic source revisions; produce/persist decision, hypothesis, open_question as QH proposals with exact provenance/state; native projection/retrieval and PostgreSQL reread after restart. Replace Graphiti episode/smoke requirements with native engine/rebuild checks. No UI validation, sharing or generic ontology. | Keep QH-4; replace QH-7 blocker with QH-30's canonical-model/native-persistence milestone; keep existing QH-8 -> QH-10 link |
| QH-9 | Scope unchanged; review its current dependency on QH-7 so native ContextService uses QH-30, while preserving QH-4/QH-5/QH-29 gates | Proposed replacement only after owner approval; no edits made |

Avoid a cycle: QH-30 supplies the engine building blocks; QH-8 demonstrates the
three-item product flow. QH-30 may use fixtures without depending on completion of
QH-8. Re-estimate both tickets after schema review; original 1.5 h estimates refer
to the superseded Graphiti scope. No Jira links, descriptions, states or comments
were written by this work.
