# QH-30 / QH-7b — canonical delta and first native increment

Reference: [QH-30](https://contextlab.atlassian.net/browse/QH-30), read in full
through Atlassian MCP on 2026-10-15, including subsequent updates to QH-30,
QH-8 and QH-10. QH-4 and QH-7 were read previously. The owner has already
realigned QH-30/QH-8/QH-10 and their native-engine dependencies on Jira. [ADR 0003](adr/0003-native-context-engine.md)
records the architecture direction. The owner approved the canonical principles
and implementation/testing on a disposable PostgreSQL server only. Applying the
migration to persistent QH remains unauthorized. This is not a Jira update.

## Baseline and preserved work

New branch `feat/QH-30-native-context-engine`, worktree `/home/ubuntu/qh-worktrees/qh-30` (moved from `/tmp/qh-30`), from main
`b1769b6`. Graphiti branch remains at `77de43c`, Draft PR #1 is untouched and never
merged; no prototype source/dependencies cherry-picked. SurrealDB worktree
`/tmp/qh-surrealdb` and its uncommitted files remain intact. The interrupted spike
is not a completed experiment and supplies no architecture/performance conclusion.
No QH database, volume or existing container is migrated, reset or replaced.

## Actual delta against QH-4

| Requirement | QH-4 baseline | QH-30 delta / remaining work |
| --- | --- | --- |
| Stable scope/ownership | users, context_spaces; child ownership derives from the space; OIDC mapping added by QH-5 | No new owner/auth tables or PolicyService |
| Original evidence | sources/source_revisions: UUID, revision number, original text, origin JSONB, created_at; unique/composite FK and immutable rows | Source locator/acquisition metadata may use existing origin JSONB; no engine episode mapping needed |
| Typed understanding | understanding_items identity; immutable understanding_item_revisions with 11 categories, including entity/relationship | Migration 0003 replaces the closed CHECK with a registered binding and shape guard |
| Revision/validation | predecessor same item; proposed/confirmed/rejected plus actor/time checks; nullable current pointer accepts confirmed same-item revision only | Reuse; AI proposal cannot overwrite current; no global Context Space revision |
| Provenance | item_revision_provenance, exact source revision and same-space FKs; immutable publication, advisory-lock assembly-before-revision | Reuse, including for entity/relation revisions; optional precise citation validation against source content remains application logic initially |
| Semantic entities | entity-category revisions can already hold structured content | No detail table: registered entity shape plus immutable publication suffices |
| Semantic relations | relationship-category content JSONB can encode a relation, but SQL cannot enforce JSON endpoint membership/type/scope | Implemented universal item endpoints with stable IDs/revision anchors; temporal metadata is common to all revision bindings |
| Projection/sync | No outbox, projector generation/version/progress tables | Fixture slice needs none; persistent processing needs an additive durable intent/progress design, reviewed before migration |
| Rebuild without paid calls | Original content/revisions already independent of engine | Canonical entity/relation content plus retained versioned embedding artifacts/cache missing; do not call LLM during rebuild |

Evidence: `apps/api/adapters/postgres/migrations/versions/0001_qh_schema.py` and
`0002_oidc_identities.py`, [schema notes](postgres-schema.md). No live inventory
or migration rerun was needed to discover these code/schema gaps.

## Canonical model — approved principles, isolated SQL implementation

The review superseded the earlier two-level category/type recommendation from
`bb967e3`. Principles and isolated implementation were subsequently approved by
the owner. Migration `0003_native_semantics` now implements **three** additive
tables on top of unchanged QH-4/QH-5 migrations. Only dedicated disposable tests
have applied it; no persistent QH database/public contract is migrated.

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
confirmed-current pointers. Implemented additive design, replacing the earlier
category-compatible/four-table proposal:

1. `semantic_type_versions(type_id, version, structural_kind, property_schema,
   relation_rules, validator_version)`:
   composite PK; nonempty namespaced ID, positive version, supported structural
   shape and JSON object schema. Published records cannot be updated/deleted/
   truncated; shape cannot change across versions of the same type. Unknown
   type/version fails FK validation. Schemas are retained permanently while used.
2. `item_revision_types(item_revision_id, context_space_id, type_id, type_version,
   fact_from, fact_to, valid_from, valid_to)`:
   PK on revision; same-space FK to the existing revision, plus FK to the registry.
   This is the **sole active semantic discriminator**, for old and new revisions.
   A deferred publication guard requires exactly one binding for every revision
   at commit and structural details appropriate to its type. It also checks that
   an item identity does not switch between item/entity/relation shapes. Serialize
   publication on the item identity as well as the revision to prevent races.
   The nullable timestamptz columns hold universal fact/validity time for every
   revision, not just relations; semantics and constraints are specified below.
3. `relation_revision_details(item_revision_id, context_space_id,
   source_item_id, source_revision_id, target_item_id, target_revision_id,
   predicate)`: same-space parent revision FK, relation-shape guard and two
   deferred composite FKs directly to
   `understanding_item_revisions(id, item_id, context_space_id)`, backed by UNIQUE
   on that triple. Stable IDs and anchors required; nonempty predicate. Any item
   shape is a possible endpoint, including another relation. Endpoint/predicate
   columns are authoritative for new writes, not conflicting copies in JSON.

**No entity_revision_details table:** type/version already fixes entity shape;
publication guards prevent an item switching shape, and universal endpoint FKs
prove ID/revision/space agreement. A marker adds no remaining integrity guarantee.
Entity descriptions remain ordinary immutable item revisions. Three tables suffice.

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
item revision and relation records; freeze new detail/type rows with parent publication,
using QH-4's deferred-FK + advisory-lock assembly-before-revision pattern. Index
new FK lookup paths for endpoint/history queries; no ontology/name uniqueness or
cross-space links, even between spaces with the same owner. Self-links need no
blanket prohibition. No copied owner or validation state on detail tables.

SQL FKs/guards prove type membership, shape, identity, scope and immutable assembly.
This increment also validates payloads at deferred SQL publication against the
pinned schema, without installing extensions or new dependencies. `qh-schema-1`
is an explicitly **limited schema profile**, not full JSON Schema: type (object,
string, integer, number, boolean, null, array), properties, required,
additionalProperties (boolean), enum (exact equality), items and minLength.
Unsupported keywords/references are rejected, never silently ignored or fetched.
Historical version-1 schemas deliberately accept any QH-4 content object; they
must not be presented as strict semantic validation of old interpretations.
Future validator implementations need distinct versioned behavior and must retain
old behavior; do not replace the meaning of qh-schema-1 in place.

Relation rules are immutable `relation_rules` on the relation type/version, not a
new ontology table or Domain Pack runtime. `allowlist` holds exact predicate,
source type/version and target type/version entries. Validation reads **anchored**
revision bindings, not current entity descriptions/latest schemas. A future rule
change requires a new type version; old relations keep their original binding.
The historical qh.relationship/v1 explicitly uses `any_registered`: any nonempty
predicate/registered endpoint types, with universal FK/scope checks still enforced.
Malformed/unknown rule fields are rejected. No inferred confirmation is possible.

Grounding/source locators remain resolver/application work: neither schema nor
SQL proves entailment. Unknown semantic time remains null, separately from source
acquisition/publication. Confidence, source reliability and human validation are
independent. No production canonical writer is activated in this increment.

### Universal endpoints: stable identity plus immutable anchor

| Endpoint option | History | Item evolution / reconciliation |
| --- | --- | --- |
| Exact revision only (previous proposal) | Preserves exact interpretation | Stable ID is derivable, but operational identity is implicit; current-entity graph joins become less direct |
| Stable item ID only | Identifies the referent | Loses the exact description used when the relation was asserted unless another historical selection rule is added |
| Stable item ID + exact item revision anchor | Explicit identity and exact original interpretation, FK checks agreement | Recommended: descriptions evolve independently; anchors remain historical evidence, not a demand to republish relations |

The extra stable ID is controlled redundancy for direct identity joins, checked by
the composite FK, not a second independently editable fact. Existing item IDs are
also the entity identities when the item is entity-shaped. For example, relation R1 points to item E and anchors E1;
adding description E2 leaves R1 unchanged. Historical views use E1; an explicitly
selected current view may show E2 while retaining R1/E1 and their validation states.
Never present an anchor as an automatically current/confirmed description.

Changing who a relation refers to requires a new relation revision, not changing
its anchor in place. Future dedup/reconciliation can record a scoped, explained
resolution/equivalence decision while retaining old entity IDs and anchors; do not
rewrite every old relation or automatically merge proposals. Storage/selection of
such decisions is future reviewed work, not an implemented alias/merge framework.
This model enables reconciliation; it does not claim to solve it already.

### Universal temporal columns: no additional table

Put temporal assertions in the already required one-to-one `item_revision_types`
row, frozen with the revision. Its role is now registered type binding **and common
revision metadata**; no new temporal table or duplicate JSON time fields are needed.

- `fact_from`, `fact_to`: nullable timestamptz occurrence bounds. A known instant
  uses equal bounds; a known interval uses ordered bounds. An unknown bound is null.
  Do not turn a date-only statement into an invented midnight instant: its exact
  granularity/calendar/timezone evidence remains in schema-validated content; use
  timestamp bounds only when the source supports their interpretation.
- `valid_from`, `valid_to`: nullable timestamptz applicability boundaries, independent
  of occurrence. When both known, use a nonempty half-open interval `[from,to)`.
  Null means unknown/unspecified, not automatically infinite or valid at query time.
  An explicitly open-ended assertion needs explicit schema-validated evidence;
  absence of an end alone does not establish permanence. Do not copy fact bounds
  into validity bounds or derive either from acquisition time.
- Acquisition remains `source_revisions.origin.acquired_at` with original precision/
  offset; `source_revisions.created_at` and item revision `created_at` are technical
  persistence metadata. They are not event dates, applicability or a guaranteed
  database commit timestamp. No new acquisition column/table or automatic default
  for semantic time is introduced.

Examples: a dated event can have occurrence with unknown validity; an observation
can have observation time; a state can have applicability; an undated preference
has all four columns null. Supported temporal changes create new immutable
revisions. Exact source revision provenance and locator checks justify the temporal
assertions; a SQL ordering check alone cannot prove grounding.

Retrieval can filter occurrence and applicability separately and explicitly include,
exclude or label unknowns; `NULL` must not be blindly coalesced to +/-infinity.
Historical reconstruction selects canonical revisions/anchors and then their temporal
assertions. Technical 'known by' selection uses retained source/publication evidence
with its stated precision; this is not a newly promised full bitemporal database.
The subsequent SQL-backed projection must retain these four values for every type
and check them against canonical metadata during hydration; the existing graph
fixture still uses its older internal temporal metadata. Semantic time never changes proposal/validation state.

Concise SQL contract below excerpts implemented constraints; the full migration
is 0003_native_semantics, and this snippet is **not independently executable**;
existing parent publication/shape/immutability guards remain required:

```sql
-- In item_revision_types (all four nullable, no acquisition-time default):
fact_from timestamptz,
fact_to   timestamptz,
valid_from timestamptz,
valid_to   timestamptz,
CHECK (fact_from IS NULL OR fact_to IS NULL OR fact_from <= fact_to),
CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_from < valid_to)

-- On understanding_item_revisions, for anchored endpoints:
UNIQUE (id, item_id, context_space_id)

-- In relation_revision_details (all endpoint columns NOT NULL):
FOREIGN KEY (source_revision_id, source_item_id, context_space_id)
  REFERENCES understanding_item_revisions (id, item_id, context_space_id)
  ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
FOREIGN KEY (target_revision_id, target_item_id, context_space_id)
  REFERENCES understanding_item_revisions (id, item_id, context_space_id)
  ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
```

Deferred endpoint checks permit one atomic batch of interrelated proposals without
insertion-order requirements; final FK and publication checks must hold at commit.
The existing item/space FK on the anchored revision establishes stable item existence
and scope, so another endpoint FK/identity table is unnecessary. Versioned semantic
validation still checks allowed endpoint types; SQL universally enforces exact
ID/revision agreement and same-space membership.

### Implemented QH-4-compatible migration and remaining application gate

Migration code: `apps/api/adapters/postgres/migrations/versions/0003_native_semantics.py`.
It creates the three tables and validators, seeds eleven compatibility type versions,
locks canonical publication, backfills bindings and recognized complete legacy
relation details, then installs assembly/shape/schema/rule guards and removes the
old CHECK while making category nullable. Existing revision payloads, metadata,
provenance, current pointers and QH-5 identities are not rewritten.

Recognized legacy relation content is `content.relation` with all five fields:
source_item_id/source_revision_id/target_item_id/target_revision_id/predicate.
Composite FKs validate the anchors. Incomplete relations, mixed structural shapes
on one old item, or an explicit legacy `content.temporal` object abort the entire
migration for review rather than fabricate mapping. Legacy raw JSON is preserved;
other source-specific temporal text is not interpreted or indexed automatically.
All backfilled temporal columns are null; never copied from acquisition/created_at.
Before persistent application, inspect actual legacy payload shapes and approve
any needed explicit mapping. Tests exercise success and full DDL/data rollback.

New metadata/provenance/detail rows must precede parent revision publication in
one transaction. Deferred guards require one binding, source provenance and exactly
the detail appropriate to relation shape, and validate pinned content/rules. Item
row locks and revision/type advisory locks serialize concurrent publication.
**READ COMMITTED** is required for type registration and new revision publication;
other isolation levels fail closed rather than risk stale-snapshot shape checks.

The migration is forward-only: downgrade refuses before altering data because new
types cannot be losslessly represented by the old CHECK. QH-4/5 writers supplying
non-null category are intentionally rejected after upgrade; deploy the registered
writer/projector path before resuming persistent ingestion. Public DTO changes,
real canonical repository, outbox/cache and application deployment are not included.
The historical QH-5 test is pinned to migration 0002 (not movable head), and its
helper admits only the explicitly named disposable server for this run.

**Persistent QH application is still gated.** No persistent database/volume is
changed by tests. Runtime tests use a dedicated PostgreSQL 16.8 tmpfs container,
with no published port, isolated network and separate credentials.

### Consequences for Neo4j, revisions and retrieval

Project stable Understanding Item IDs as referents, immutable item/relation revision IDs as
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
persistence work, not silently covered by approval of these three semantic tables.
The existing three-domain fixtures and 67-test results are retained as prior slice
evidence; the new tests below now exercise SQL plus generalized fixture endpoint projection,
without claiming an integrated PostgreSQL-to-Neo4j production pipeline.

## Fixture increment and current approval boundary

The completed fixture increment implements a narrow internal native Neo4j projector/retriever with a synthetic
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
Public QH contracts and historical migrations are unchanged. The canonical model
is approved and migration 0003 is tested in isolation. Persistent application
requires explicit authorization after this checkpoint.

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
shape enforces available item endpoints and matching stable IDs in the same space. Neo4j uses generic
SUBJECT/OBJECT edges and predicate/type/version data, with canonical fingerprints.

PASS: targeted native tests plus architecture/public-contract regressions, 68 tests
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
production composition is claimed. SQL migration 0003 is separately verified below.
QH-30 remains in progress; the next gate is persistent migration application.

PASS: `prepare`, dedicated test-container restart, `check` and
`rebuild-after-loss` executed with the universal fixture generation. The retained
QH stack, Graphiti branch/PR and SurrealDB worktree were not replaced.

Acceptance boundary: architecture/update and fixture projection/retrieval are PASS;
production PostgreSQL writes, outbox/cache, LLM extraction and hybrid semantic
retrieval are NOT TESTED/not implemented in this increment. This does not satisfy
the full QH-30 end-to-end Definition of Done.

## Isolated SQL verification checkpoint

Tests: `apps/api/tests/test_native_semantics_sql.py`, reusing QH-4 database/revision
helpers. Runs skip unless QH30_SQL_TEST=1, then refuse any host other than
`qh30-sql-test`; regular CI cannot silently substitute production PostgreSQL.
Container PostgreSQL 16.8-alpine3.21 uses tmpfs, no persistent volume/published port.
Existing Neo4j tests use only `qh30-native-neo4j-test` and its synthetic volume.
Credentials remain in mode-600 local env files; no QH/provider credentials loaded.

| Criterion | Evidence / result |
| --- | --- |
| Three tables, no redundant entity marker | PASS: empty upgrade and table inventory |
| Existing eleven categories, QH-4 through QH-5/head | PASS: immutable row snapshots unchanged; eleven pinned bindings; confirmed-current/provenance retained |
| New type/version without migration | PASS: registry inserts, strict payload rejection and preserved original schemas |
| Universal endpoints and stable/revision agreement | PASS: item→item, item→entity, relation→item; missing/mismatched/foreign anchors fail, including spaces with the same owner |
| Immutable revisions, provenance and new metadata | PASS: update/delete/truncate and late assembly rejected |
| Versioned semantic rules | PASS: v2 changes do not reinterpret v1; allowlist checks exact anchored versions |
| Explicit/unknown temporal values | PASS: all structural kinds, ordering, nulls and temporal filtering |
| Atomicity/concurrency | PASS: complete rollback, conflicting item/type publishers and late binding race checks |
| Old schema incompatibilities | PASS: incomplete relation, explicit unmapped temporal object and mixed historical shapes abort atomically |
| QH-4/QH-5 regressions | PASS: original migration tests on dedicated server; migrations 0001/0002 unchanged |
| Persistent QH database | PASS: read-only before/after dump hash and container/mount comparison unchanged |
| Production ingestion, outbox/cache/hybrid retrieval | NOT TESTED/not implemented in this increment |

Reproduction, from apps/api in the locked backend image mounted at /workspace:
`python -m pytest -q -p no:cacheprovider tests/test_native_semantics_sql.py
 tests/test_migrations.py tests/test_identity_migration.py tests/test_native_context.py
 tests/test_architecture.py tests/test_contracts.py`.
Set POSTGRES_HOST=qh30-sql-test, POSTGRES_DB=qh30_admin, QH30_SQL_TEST=1 and the
dedicated local env credentials; set QH30_TEST_NEO4J_URI to the dedicated graph.
No production-compose startup/migration, paid call or Graphiti dependency is used.

The fixture graph now covers decision→entity, observation→decision and
relation→preference with explicit matching stable IDs. Existing internal fixture
category fields are compatibility export metadata, not a second canonical type
classification. A real registered-type SQL reader/composition and common temporal
projection still belong to the subsequent persistent pipeline increment.

Executed totals for this checkpoint: **74** dedicated SQL model tests (72-test suite
plus the two QH-4-through-head/temporal retrieval checks), **33** historical migration
regressions, and **68** native graph/architecture/contract tests. All passed.
The QH-5 test originally stopped on its production-only hostname preflight; the
helper now explicitly admits the dedicated test server and the historical test
pins 0002 rather than head. The real test then passed; no production fallback was
used. Earlier SQL parser/NULL-handling and statistics-observation failures were
corrected and the affected real tests rerun successfully.

No new runtime dependencies or manifest/lock changes. QH Core/public signatures,
Compose QH, migrations 0001/0002 and the persistent QH data/volumes are unchanged.
