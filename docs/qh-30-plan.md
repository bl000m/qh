# QH-30 / QH-7b — canonical delta and first native increment

Reference: [QH-30](https://contextlab.atlassian.net/browse/QH-30), read in full
through Atlassian MCP on 2026-10-15, including subsequent updates to QH-30,
QH-8 and QH-10. QH-4 and QH-7 were read previously. The owner has already
realigned QH-30/QH-8/QH-10 and their native-engine dependencies on Jira. [ADR 0003](adr/0003-native-context-engine.md)
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
| Semantic relations | relationship-category content JSONB can encode a relation, but SQL cannot enforce JSON endpoint membership/type/scope | Proposed typed relation extension with stable entity IDs, exact revision anchors, same-space FKs and nullable supported event bounds |
| Projection/sync | No outbox, projector generation/version/progress tables | Fixture slice needs none; persistent processing needs an additive durable intent/progress design, reviewed before migration |
| Rebuild without paid calls | Original content/revisions already independent of engine | Canonical entity/relation content plus retained versioned embedding artifacts/cache missing; do not call LLM during rebuild |

Evidence: `apps/api/adapters/postgres/migrations/versions/0001_qh_schema.py` and
`0002_oidc_identities.py`, [schema notes](postgres-schema.md). No live inventory
or migration rerun was needed to discover these code/schema gaps.

## Final canonical recommendation — proposed, not applied

Review of 2026-10-15 supersedes the earlier two-level category/type recommendation
and revision-only endpoints from commit `bb967e3`. The architecture direction is
confirmed; the model below still awaits owner approval. No executable code,
migration, public contract or fixture is changed by this review.

### The eleven QH-4 categories and concrete alternatives

Exact source: `0001_qh_schema.py`, `CATEGORIES` and `ck_item_category`.

| Existing category | What it describes |
| --- | --- |
| objective | Semantic/functional classification: desired outcome |
| current_state | Semantic/functional classification: described state |
| decision | Semantic/functional classification: decision |
| hypothesis | Epistemic classification: tentative interpretation |
| open_question | Semantic/functional classification: unresolved question |
| constraint | Semantic/functional classification: limiting condition |
| preference | Semantic/functional classification: stated preference |
| concept | Semantic classification: conceptual content; not a distinct SQL structure today |
| entity | Structural shape: identifiable referent with descriptions/revisions |
| relationship | Structural shape: assertion with typed, scoped endpoints |
| uncertainty | Epistemic/semantic content; distinct from confidence or validation metadata |

All eleven are just category strings in today's SQL; entity/relationship are not
yet structurally enforced. A concept can later have an entity-shaped type if it
needs referential identity, but the migration must not guess this from its name.
The grouping above is analysis, not a reclassification of historical records.

| Alternative | Integrity and evolution | Cost / recommendation |
| --- | --- | --- |
| Keep eleven-category CHECK + type/version registry | FK and exact schema possible, but every new type must fit an old category | Adds two classifications and compatibility mapping; forces observations/events/intentions into arbitrary buckets. Reject as the long-term model |
| Single versioned type registry, without eleven-category CHECK | Controlled type/version FK; structural shape drives entity/endpoint constraints; new semantic types are registry data | Recommended: one semantic authority, no per-domain schema migration |
| Free type strings + JSONB | New types easy, but unknown versions and invalid references can escape validation | Reject: insufficient integrity |

**Recommendation:** one namespaced `type_id` + positive immutable `version`, with
an immutable `property_schema` and a small structural discriminator
`item | entity | relation`. This discriminator selects storage constraints only;
it is not a domain taxonomy or a second semantic category. Decision, observation,
event, intention and future types can all use item shape without being reduced
to current_state. Adding a new storage shape may require a migration; adding a
semantic category/domain does not. Type registration is controlled publication,
not permission for an LLM to invent types or grant access. Domain Pack runtime
and schema-management UI remain out of scope.

### Tables and necessary PostgreSQL constraints

Reuse QH-4 item identities, immutable revisions, validation, provenance and
confirmed-current pointers. Recommended additive design, replacing the earlier
category-compatible registry proposal:

1. `semantic_type_versions(type_id, version, structural_kind, property_schema)`:
   composite PK; nonempty namespaced ID, positive version, supported structural
   shape and JSON object schema. Published records cannot be updated/deleted/
   truncated; shape cannot change across versions of the same type. Unknown
   type/version fails FK validation. Schemas are retained permanently while used.
2. `item_revision_types(item_revision_id, context_space_id, type_id, type_version)`:
   PK on revision; same-space FK to the existing revision, plus FK to the registry.
   This is the **sole active semantic discriminator**, for old and new revisions.
   A deferred publication guard requires exactly one binding for every revision
   at commit and structural details appropriate to its type. It also checks that
   an item identity does not switch between item/entity/relation shapes. Serialize
   publication on the item identity as well as the revision to prevent races.
3. `entity_revision_details(item_revision_id, item_id, context_space_id)`:
   immutable entity marker with PK on revision; composite FK to the matching
   canonical revision/item/space, backed by an added UNIQUE on that triple.
   Its type binding must resolve to entity shape. UNIQUE on this same triple
   supports exact endpoint-anchor FKs. Labels/aliases/properties remain in content;
   there is no second entity identity hierarchy or separate entity-owner table.
4. `relation_revision_details(item_revision_id, context_space_id,
   source_entity_item_id, source_entity_revision_id,
   target_entity_item_id, target_entity_revision_id,
   predicate, valid_from, valid_to)`: same-space parent revision FK, relation-shape
   guard and two composite FKs to entity_revision_details (anchor revision, stable
   item ID, space). Predicate nonempty; event bounds nullable with ordered bounds
   when both known. Anchors and identities are required. Columns are authoritative;
   do not duplicate conflicting endpoints/predicate/time in content JSONB.

No `category` compatibility FK or mandatory mapping to the old eleven survives.
The binding table avoids adding/backfilling discriminator columns on immutable
revision rows. Its one-to-one join is deliberate migration compatibility overhead,
not a second classification. New revisions must use a null legacy category (enforced by the publication guard) after the
column becomes nullable; old category values remain frozen historical metadata.
The old CHECK is removed only together with replacement bindings/publication guards.
Removing the physical legacy column can be a later, separately approved cleanup.

Keep existing positive/unique revision numbers, same-item predecessor,
confirmed-current guard, origin/actor/state checks, JSONB object checks and exact
same-space source provenance. Add RESTRICT deletion for referenced registry,
entity and relation records; freeze new detail/type rows with parent publication,
using QH-4's deferred-FK + advisory-lock assembly-before-revision pattern. Index
new FK lookup paths for endpoint/history queries; no ontology/name uniqueness or
cross-space links, even between spaces with the same owner. Self-links need no
blanket prohibition. No copied owner or validation state on detail tables.

SQL FKs/guards prove type membership, shape, identity, scope and immutable assembly;
**they do not validate arbitrary JSON Schema or prove textual entailment**. The
canonical publication path must validate the exact versioned property schema,
including schema dialect/support, before publication; reject unknown schema
versions/unsupported keywords rather than silently ignore them. All write paths,
including imports, must use this validation path with restricted DB write access.
A full database JSON Schema extension is not required by this proposal. Validate
source locators/grounded dates in the resolver; retain null for unknown event time,
independently of technical acquisition/publication time. Model confidence, source
reliability and human validation remain separate; inferred content is not confirmed.

### Entity endpoints: stable identity plus immutable anchor

| Endpoint option | History | Entity evolution / reconciliation |
| --- | --- | --- |
| Exact revision only (previous proposal) | Preserves exact interpretation | Stable ID is derivable, but operational identity is implicit; current-entity graph joins become less direct |
| Stable item ID only | Identifies the referent | Loses the exact description used when the relation was asserted unless another historical selection rule is added |
| Stable item ID + exact entity revision anchor | Explicit identity and exact original interpretation, FK checks agreement | Recommended: descriptions evolve independently; anchors remain historical evidence, not a demand to republish relations |

The extra stable ID is controlled redundancy for direct identity joins, checked by
the composite FK, not a second independently editable fact. Existing item IDs are
the entity identities. For example, relation R1 points to entity E and anchors E1;
adding description E2 leaves R1 unchanged. Historical views use E1; an explicitly
selected current view may show E2 while retaining R1/E1 and their validation states.
Never present an anchor as an automatically current/confirmed description.

Changing who a relation refers to requires a new relation revision, not changing
its anchor in place. Future dedup/reconciliation can record a scoped, explained
resolution/equivalence decision while retaining old entity IDs and anchors; do not
rewrite every old relation or automatically merge proposals. Storage/selection of
such decisions is future reviewed work, not an implemented alias/merge framework.
This model enables reconciliation; it does not claim to solve it already.

### QH-4-compatible migration sequence — for approval, not execution

1. Before implementation, inventory category counts/IDs and payload shapes on the
   target database under authorized read access. This review inspected code/tests,
   not live canonical data. Preserve migrations 0001/0002 and immutable triggers.
2. In a new forward migration, create registry/bindings/detail tables, constraints
   and required unique indexes. Seed eleven version-1 compatibility schemas/types
   (`qh.objective`, etc.), retaining original meaning. Preserve concept as item
   shape unless explicit evidence/model review requires a new revision. Legacy
   schemas must honestly accept historical payloads; stricter future schema versions
   apply to new revisions rather than falsely certifying old content.
3. With writers quiesced and the change atomic, bind existing revisions by their
   original category without updating their content/category/state/timestamps.
   Controlled migration-only insertion of bindings onto published revisions must
   be explicit and limited to this transaction; normal publication stays frozen.
   Inspect any existing entity/relation payloads: do not fabricate endpoints,
   anchors or times. If incompatible/incomplete, abort and request a remediation
   decision; never skip them or claim a complete structural backfill.
4. Verify one binding per revision, exact scope/anchors and unchanged old row
   hashes/counts/provenance/current pointers. Install final publication/immutability
   guards, make legacy category nullable and drop only ck_item_category. New writes
   use bindings and null category; no dual-write or automatic category coercion.
   Deploy writer/projector changes together before resuming writes. No public DTO
   is changed here; any legacy public category dependency requires separate approval.
5. Before any application, test old-fixture upgrade, invalid type/version/properties,
   wrong shape, mismatched ID/anchor, foreign scope, missing details, concurrency,
   immutability, failed-transaction rollback and rebuild. These proposed-migration
   checks are **NOT TESTED**. A downgrade after genuinely new types exist is not
   losslessly representable by the old CHECK: refuse destructive rollback; use a
   reviewed forward repair or restore procedure. Never disable immutable guards
   globally or rewrite approved snapshots.

### Consequences for Neo4j, revisions and retrieval

Project stable entity IDs as referents, immutable entity/relation revision IDs as
assertions, and both endpoint anchors explicitly. Generic labels/edges and
properties carry type_id/version/predicate; no per-domain graph/database. A change
in description reprojects that entity's selected view and affected derived search
documents, without creating new canonical relation revisions. If a denormalized
relation embedding includes an entity label, invalidate only the dependent derived
artifact; historical canonical content and its embeddings are not silently rewritten.

Rebuild takes an explicit canonical revision set plus retained schemas/embedding
artifacts and selection configuration, preserves original anchors/provenance, and
makes no LLM call. Stable-ID equivalence never authorizes cross-space traversal.
Retrieval still authorizes first, then bulk-hydrates exact canonical references;
type filtering/ranking uses registry metadata, not the deprecated eleven-category
CHECK. Query state/current selection remains explicit and unconfirmed proposals
never acquire confirmation through traversal. New semantic types may need new
registered validation/extraction instructions, not schema migrations or a second
interpretation pass. No hybrid-search performance claim follows from this review.

Outbox/progress and versioned embedding cache remain separate proposed operational
persistence work, not silently covered by approval of these four semantic tables.
The existing three-domain fixtures and 67-test results are retained as prior slice
evidence; they have not exercised this proposed SQL model or stable-ID projection.

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
Public QH contracts and migrations are unchanged. Schema/model approval
is requested for the single-registry model, four additive tables, stable endpoint
IDs with immutable anchors, and the legacy-category transition described above;
actual migration application needs explicit authorization afterwards.

## Jira alignment — observed updates and remaining proposals, not posted

| Ticket | Proposed revised scope / acceptance | Proposed dependencies |
| --- | --- | --- |
| QH-7 | Preserve Graphiti as historical technical prototype/PR #1; record supersession by QH-30 and unfinished live grounding result. Do not label its original real-smoke DoD passed or merge its code. Keep valuable regression evidence. Status/resolution requires owner decision. | Keep historical QH-2/QH-3 links; replace downstream active implementation dependency with QH-30 after approval |
| QH-30 (QH-7b), owner-updated | Native engine direction/ADR + approved canonical delta + first fixture-backed projection/retrieval; subsequent persistence/extraction/hardening tracked explicitly, without claiming already delivered. | Proposed prerequisites QH-2, QH-3, QH-4; reuse QH-5/QH-29 identity/policy. No hard dependency on completing the Graphiti smoke or SurrealDB spike |
| QH-8, owner-updated | Import at least three synthetic source revisions; produce/persist decision, hypothesis, open_question as QH proposals with exact provenance/state; native projection/retrieval and PostgreSQL reread after restart. Replace Graphiti episode/smoke requirements with native engine/rebuild checks. No UI validation, sharing or generic ontology. | Keep QH-4; replace QH-7 blocker with QH-30's canonical-model/native-persistence milestone; keep existing QH-8 -> QH-10 link |
| QH-9 | Scope unchanged; review its current dependency on QH-7 so native ContextService uses QH-30, while preserving QH-4/QH-5/QH-29 gates | Proposed replacement only after owner approval; no edits made |

Avoid a cycle: QH-30 supplies the engine building blocks; QH-8 demonstrates the
three-item product flow. QH-30 may use fixtures without depending on completion of
QH-8. Re-estimate both tickets after schema review; original 1.5 h estimates refer
to the superseded Graphiti scope. No Jira links, descriptions, states or comments
were written by this work.

## Executed native fixture increment

Implementation: `apps/api/adapters/context/native.py` (`checked_rows`,
`NativeContextEngine.replace/search`, `AuthorizedNativeContextService.retrieve`).
Fixtures and version-keyed test validators: `apps/api/tests/test_native_context.py`
and `tests/fixtures/qh30_canonical_snapshot.json`. Validators are injected internal
composition, not a production Domain Pack registry or full JSON Schema engine.
The adapter has no domain names or closed semantic-type list. Coarse relationship
shape enforces available entity endpoints in the same space. Neo4j uses generic
SUBJECT/OBJECT edges and predicate/type/version data, with canonical fingerprints.

PASS: targeted native tests plus architecture/public-contract regressions, 67 tests
on 2026-10-15; Ruff checks passed. Real queries execute against the dedicated
`qh30-native-neo4j-test` container/network/volume, never the QH or spike databases.
Coverage includes three domain cases, extra observation type, explicit/null event
time, proposed state, exact provenance, owner denial before read, graph tampering,
missing evidence, foreign/missing endpoints, idempotence, atomic rollback and rebuild.

Reproduction (backend image with locked test dependencies, fixture-only database):
`python -m pytest -q -p no:cacheprovider tests/test_native_context.py
 tests/test_architecture.py tests/test_contracts.py`, from `apps/api`, with `PYTHONPATH=.`
and dedicated `QH30_TEST_NEO4J_URI`/password environment. The restart probe is
`scripts/verify_qh30_native.py --phase prepare|check|rebuild-after-loss`; it refuses
other database addresses and removes only its own tagged synthetic projection.

Limits: canonical reads are a scoped bulk fixture callback, not a PostgreSQL
repository; search is scoped substring retrieval, not vector/hybrid semantic
ranking. Graph traversal is demonstrated for relation endpoints and evidence,
not a completed product query API. No extraction/resolution, persistent outbox,
production composition or SQL schema changes are claimed. QH-30 remains in progress.
The next structural gate is approval of the proposed canonical delta above.

PASS: `prepare`, dedicated test-container restart, `check` and
`rebuild-after-loss` executed with the universal fixture generation. The retained
QH stack, Graphiti branch/PR and SurrealDB worktree were not replaced.

Acceptance boundary: architecture/update and fixture projection/retrieval are PASS;
production PostgreSQL writes, outbox/cache, LLM extraction and hybrid semantic
retrieval are NOT TESTED/not implemented in this increment. This does not satisfy
the full QH-30 end-to-end Definition of Done.

## Final model-review evidence (documentation only)

Re-read QH-30 via Atlassian MCP and inspected `CATEGORIES`, FK/immutability/publication
code in migration 0001, ADR 0002 and the existing native tests. `git diff --check`
and targeted reference/category consistency checks passed for this revision.
No executable code changed; the previously executed 67 tests were not repeated.
No migration SQL or public contract was generated/applied. Model approval is the
next gate; this proposal does not authorize migration execution.
