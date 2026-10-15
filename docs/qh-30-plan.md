# QH-30 / QH-7b — canonical delta and first native increment

## Current checkpoint — read this before historical milestones

| State | Result |
| --- | --- |
| Approved | PostgreSQL canonical; native rebuildable Neo4j; versioned universal semantic model |
| Completed in isolation | 0003 three canonical tables; real repository; multidomain SQL→Neo4j integration; 0004 two operational tables and incremental worker |
| Verified | 101 distinct tests in the outbox checkpoint, Ruff; earlier milestone evidence retained below |
| Persistent QH | Last read-only inventory: 0002, zero canonical/identity rows; no 0003/0004 application or native runtime activation |
| Remaining | Reviewed cutover/runtime composition, explicit activation approval, integrated CI coverage; extraction, embeddings/cache and advanced retrieval remain future work |

Historical sections below preserve what was true at each milestone. Earlier deferrals
of the outbox are superseded by the final **Incremental outbox and backend worker**
section. Historical test counts are not additive totals or evidence of deployment.
`make migrate` runs `upgrade head` and grants no authorization. Any future cutover
must recheck the inventory and explicitly target **0004_projection_outbox** from
the reviewed native commit/image; do not apply it now.

CI proposal before merge (not configured): add a required integration job with
runner-local disposable PostgreSQL and Neo4j, no published database ports, dedicated
credentials/network and the test servers' enforced names. Run the SQL model,
canonical pipeline and outbox suites with their explicit opt-in variables; fail
if integration tests skip. Stop/remove only job-owned resources at completion.
Existing green quality/OIDC gates do not establish these suites executed. No new
persistent service, paid API or workflow execution is authorized by this proposal.


Reference: [QH-30](https://contextlab.atlassian.net/browse/QH-30), read in full
through Atlassian MCP on 2026-10-15, including subsequent updates to QH-30,
QH-8 and QH-10. QH-4 and QH-7 were read previously. The owner has already
realigned QH-30/QH-8/QH-10 and their native-engine dependencies on Jira. [ADR 0003](adr/0003-native-context-engine.md)
records the architecture direction. The owner approved the canonical principles
and implementation/testing on a disposable PostgreSQL server only. Applying the
migrations 0003/0004 to persistent QH remains unauthorized. This is not a Jira update.

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
| Projection/sync | No outbox, projector generation/version/progress tables | Migration 0004 adds transactional outbox + per-scope state; backend-local incremental worker verified in isolation |
| Rebuild without paid calls | Original content/revisions already independent of engine | Canonical entity/relation content plus retained versioned embedding artifacts/cache missing; do not call LLM during rebuild |

Evidence: `apps/api/adapters/postgres/migrations/versions/0001_qh_schema.py` and
`0002_oidc_identities.py`, [schema notes](postgres-schema.md). No live inventory
or migration rerun was needed to discover these code/schema gaps.

## Canonical model — approved principles, isolated SQL implementation

The alternatives below retain the model review history. Implemented constraints
are described in the subsequent table/constraint sections; outbox status is in
the final incremental checkpoint.

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

In the QH-4 baseline, all eleven are just category strings; entity/relationship are not
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
SQL-backed projection now retains all four values and checks them against canonical
metadata during hydration; the retained fixture-only path uses its compatibility metadata. Semantic time never changes proposal/validation state.

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
writer/projector path before resuming persistent ingestion. The internal canonical
repository is now implemented/tested below; public DTO changes, outbox/cache and
application deployment remain excluded.
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

At this historical semantic-model checkpoint, outbox/progress and embedding cache
were separate proposals. Outbox/progress are now implemented by 0004 below;
versioned embedding cache remains future work.
The existing three-domain fixtures and 67-test results are retained as prior slice
evidence; the new tests below now exercise SQL plus generalized fixture endpoint projection,
with the next section demonstrating actual SQL-to-graph integration in isolation,
without claiming production deployment.

## Historical fixture increment and its approval boundary

The completed fixture increment implements a narrow internal native Neo4j projector/retriever with a synthetic
canonical fixture shaped as existing QH-4 item revisions and provenance. The
fixture represents the canonical input; it is explicitly **not** new PostgreSQL
storage. No unresolved entity extension is persisted or presented as approved.
Project revision IDs/state/provenance into Neo4j and retrieve existing QH hits
through an authorized wrapper using PolicyService. Test duplicate apply, stale
input, missing/foreign provenance, deletion/rebuild of only the fixture generation,
restart of only a disposable test DB and isolation. No production startup binding.

Do not build extraction/resolution/LLM/embedding adapters in this milestone. Full
text/vector/traversal fusion, durable outbox/cache, advanced entity
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

## Historical executed native fixture increment

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

## Historical isolated SQL verification checkpoint (0003)

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
classification. A real registered-type SQL reader and common temporal projection are implemented
in the isolated pipeline increment below; production composition remains gated.

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

## PostgreSQL → Neo4j full-snapshot increment (historical isolated milestone)

This milestone used only 0003; its O(n) ordinary path is superseded by the
incremental 0004 implementation below. Full reconciliation remains explicit recovery.
`adapters/postgres/canonical.py` implements
`CanonicalRepository.register_types/save/read_snapshot/projection_lock`. Existing
Core `ContextQuery`, `ContextResult`, item/source revision references and
PolicyService remain unchanged. The adapter uses internal SQL-shaped records, not
a new public ingestion DTO/port. No API/startup/worker binding is activated.

- `save` assembles typed metadata, relations and exact provenance before immutable
  publication, in one transaction. Stable IDs and revision numbers are explicit;
  exact replay is a no-op and mismatched replay fails. SQL pinned schemas/rules
  remain authoritative. No implicit confirmation or current-pointer change.
- Registration is explicit trusted provisioning, never auto-registration from an
  extraction. Writes require an already authorized internal operation; owner/scope
  SQL checks are defense in depth, not a newly defined public ingest permission.
  Public write authorization remains a later contract gate.
- `read_snapshot` uses an authorized, consistent, read-only SQL snapshot; optional
  exact revision IDs, bulk provenance/source metadata, type/version, temporal
  fields and universal relation anchors. It selects all historical revisions by
  default, explicitly **not** 'latest confirmed'. User-facing lifecycle selection
  is unchanged/pending; proposal references remain proposals.
- `NativeContextEngine` now supports these SQL records alongside retained fixtures.
  Registered types do not map back to the old eleven categories. Generic graph
  revision nodes carry stable IDs, type/version, common temporal properties and
  provenance; SUBJECT/OBJECT edges retain exact immutable anchors. Core hits are
  hydrated from SQL. Structured content without a text field uses its JSON
  representation, without a new interpretation step.

### Minimum synchronization and recovery

`context/native.py:reconcile` serializes projectors per slice with a PostgreSQL
session advisory lock. It captures the full authorized canonical revision set,
computes per-scope manifests, publishes one Neo4j generation transactionally and
rechecks canonical state. No SQL transaction is held open during Neo4j I/O.
Replaying identical state repairs missing projection records without duplicates;
a changed set gets a new generation. Canonical writes occurring during projection
cause an explicit 'advanced/pending' result and require the next reconciliation.

SQL-backed retrieval enables `verify_readiness=True`: authorize first, load the
scoped canonical set, compare its manifest to the graph generation, and verify
projected ID completeness, retrieval metadata, temporal fields and provenance.
This check also runs for otherwise empty text results. A stale or partially lost
graph fails instead of reporting a fresh canonical absence. Graph substring
matching still executes in Neo4j; SQL remains hydration/authority. No vector/hybrid
ranking is implemented. Lost source/reference metadata fails validation too.

A crash between SQL commit and Neo4j publication loses no work: the canonical set
itself is the recovery source. A lost acknowledgement after graph commit is safely
replayed; a failed graph transaction retains the old generation and canonical data.
A restarted application recreates adapters, reconciles authorized scopes and can
rebuild the entire projection without Graphiti, embeddings or LLM calls. Tests
simulate both failures and graph deletion using only uniquely tagged test records.
No automatic background recovery scheduler is claimed; reconciliation is explicit.

Cost/limit: full SQL and graph scans per reconciliation and freshness-checked read
are intentionally O(n) for this small milestone. This proves correctness, not an
incremental/high-throughput architecture. Per-scope generation selection is fixed
by the caller; reconcile the complete scope set owned by that slice.

The former incremental-outbox proposal is now implemented in migration 0004 and
validated below; it is no longer deferred or an ordinary full-snapshot dependency.
No broker/new service/container is introduced.

### Writer compatibility inventory and prepared adaptation

Search limited to executable writers under adapters/app/scripts and migration
entry points; historical QH-4/QH-5 fixtures remain on their own schema revisions.

| Existing writer / entry point | 0003 impact / action |
| --- | --- |
| Application Understanding Item/source SQL writers | None existed before this increment; no production category writer to convert. New CanonicalRepository writes registered bindings and null legacy category |
| `demo_identities.provision_demo` | INSERTs touch users/user_identities only, compatible and idempotent. CLI preflight previously required exactly 0002; `require_identity_schema` now explicitly accepts 0002, 0003 or 0004, rejecting unrecognized revisions. Existing local database restriction is preserved |
| Historical QH-4/QH-5 migration test helpers | Deliberately use historical category writes against pinned old migrations; do not rewrite history or make them write invalid payloads against head |
| `Makefile:migrate` | Calls upgrade head, so do not use it for this rollout. Historical 0003-only instruction superseded: eventual cutover must explicitly target 0004_projection_outbox from the reviewed native worktree/image, after authorization |
| Graphiti branch/runtime | Preserved; never silently replace its checkout/mount or treat its Neo4j graph as canonical SQL backfill |

The adapted identity writer is tested against 0003 and the existing QH-5 regression
is tested against 0002. No public source/UI validation workflow is introduced.

### QH-31 boundary

Read QH-31 and the new QH-30 comment through Atlassian MCP. Source content is a
representation, not an assertion that original file bytes live inline. Existing
origin JSONB can retain opaque synthetic external-reference metadata; tests save
an empty text representation with such metadata and retain exact provenance.
No original is fetched, copied or granted a download permission through context
access. Neo4j carries revision references, not binaries. Source Vault storage,
formats/lifecycle/policies and public contracts remain entirely QH-31 work.

### Repeatable demonstration and results

`tests/test_canonical_graph_pipeline.py` reuses the existing multidomain JSON
fixtures as input, then writes/reads real SQL. Its engine reader is the repository,
not the fixture callback. Both databases must be the explicitly named dedicated
servers. Existing fixture-only tests remain intact.

Command in the locked backend image, source mounted read-only at /workspace:
`python -m pytest -q -x --tb=short -p no:cacheprovider
 tests/test_canonical_graph_pipeline.py tests/test_native_context.py
 tests/test_architecture.py tests/test_contracts.py tests/test_identity_migration.py`.
Use only the dedicated SQL/Neo4j env files and qh30-native-test network described
above; no production credentials, providers or new dependencies are required.

PASS: 83 tests in the integrated/regression run, plus one targeted iterator/type
replay regression after input normalization: **84 distinct tests** for this
increment. Ruff passed. Previous unchanged 0003 migration tests were reused,
not repeated. Demonstration outcomes:

| Check | Observed result |
| --- | --- |
| Multidomain persistence/provenance/time | Three domain cases in A, all proposed; known event time distinct from acquisition, other times null |
| Two owners/spaces | A retrieves three Cedar hits; B retrieves three Birch hits and zero Cedar hits; cross-owner/mixed scope denied before retrieval, direct SQL scope guard also denies |
| Revision update | New revision of same item, old payload unchanged, current pointer untouched; pending graph blocks even an empty result; reconcile returns new revision |
| Idempotence / atomic writes | Repeated source/revision/type registration exact replay succeeds, conflicting replay/schema and partial-batch failure roll back |
| Failure/restart/rebuild | Failed graph transaction, lost acknowledgement, recreated readers, partial/full graph loss recover from canonical SQL |
| Race/read correctness | Canonical changes during publication detected; two projectors serialized; missing nodes, forged temporal data and SQL failure fail closed with cause retained |
| Persistent QH | PASS: retained baseline schema/data dump hash, container ID and mounts unchanged; no persistent migration or volume change |

### Persistent application plan — superseded by the inventory below

The earlier backup/clone procedure was conditional on actual content. The read-only
inventory in this increment found an empty QH database, so no elaborate data backup/
restore rehearsal is required for the recommended empty-schema activation. Migration
execution and runtime activation still require explicit authorization.

## Incremental outbox and backend worker — implemented in isolation

Migration `0004_projection_outbox` follows unchanged 0003. It adds **two operational
tables**, not canonical semantic objects:

- `projection_outbox`: stable intent ID, scope/item/exact revision, kind
  revision/current, per-scope sequence, pending/processing/ready/failed, attempts,
  availability, token/lease deadline, completion and redacted error code/class.
  Identity fields are immutable; retry/ack metadata is mutable. Canonical FKs and
  unique revision-intent/per-scope-version keys prevent duplicate canonical intent.
- `context_projection_state`: scope PK, recovery epoch, desired/applied versions
  and last success. This small row is required for commit-order sequencing,
  contiguous acknowledgements, constant-size readiness checks and worker fencing.
  It is operational/reconstructible state, not a Context Space domain revision.

AFTER INSERT revision triggers and explicit current-pointer-change triggers enqueue
in the **same SQL transaction** as publication. All SQL writers are covered, not
only CanonicalRepository. Deferred schema/endpoint validation failure rolls back
the intent and desired version too. Sequence allocation locks the scope state row:
commit order is serialized per scope, and rollback does not leave scope-version
gaps. Global outbox identity gaps are harmless and are never used as a watermark.
Existing 0003 revisions are queued once during migration; new spaces get state
rows automatically. This one-time backfill is not a normal-query/rebuild scan.

### Incremental execution and retry semantics

`adapters/context/incremental.py` contains IncrementalProjector, ProjectionWorker
and IncrementalContextEngine. It runs inside the backend Python process via
`ProjectionWorker.run(stop_event)` or bounded `run_once`, not a new microservice.
The actual polling loop is tested. No automatic production startup is enabled
while persistent 0003/0004 application remains prohibited.

Claim: short SQL transaction, per-scope row lock with SKIP LOCKED, claim only
applied+1, expiring token lease and attempt count. Workers can progress across
independent scopes; concurrent workers cannot claim the same unexpired head.
A restarted worker reclaims expired leases. Finish requires both the original
epoch and current token. SQL outages leave the lease recoverable; polling resumes.
Failures retry with bounded exponential delay (2–60 seconds), without paid APIs.

Projection: `read_affected_snapshot` follows only the changed immutable revision
and its transitive relation anchors by indexed IDs. One head lookup uses the
item/revision-number index. The Neo4j transaction MERGEs only these assertions,
provenance and relation edges, updates the affected item head monotonically, then
advances its scope marker. A predecessor gap is rejected for later delivery;
old/duplicate deliveries do not change newer marker/head data. Lost acknowledgement
is replayed without duplicate graph nodes. Namespaces separate independent canonical
databases sharing the test graph. Current-pointer selection is copied explicitly;
a deliberate canonical selection of an older confirmed revision is not an automatic
projection regression. Historical assertions remain immutable.

Errors: failed state, exception **class** only (no SDK message/SQL/source/credential),
attempts, timestamps and queue lag are available through owner-scoped sync_status.
The live worker retains the actual cause for internal diagnosis. Unavailable Neo4j
never rolls back or erases the committed canonical revision/intention.

### Ordinary retrieval versus explicit recovery

The existing PolicyService authorizes first. IncrementalContextEngine then reads
per-scope SQL counters and Neo4j epoch/version markers, runs the existing scoped
text candidate query, hydrates only candidate IDs in SQL, and rechecks counters
before returning. Pending/failed/missing-marker or changed-during-read state fails
explicitly, **including empty results**. No ordinary scope snapshot, checksum scan
or reconciliation is performed. Synchronization checks scale with requested scope
count; candidate hydration is bounded by query limits. Basic substring matching
is still the existing Neo4j search, not a new indexed/vector performance claim.

Full `reconcile` remains available for the historical snapshot adapter. For the
incremental projection use `ProjectionWorker.rebuild(scope)`: explicit maintenance
locks the scope's state (briefly pausing scope commits), creates a new epoch and
whole graph generation, fences old workers, reconstructs heads/anchors/provenance,
and acknowledges the captured canonical set. Old generations remain retained.
This exceptional maintenance path holds a SQL row lock across graph publication;
ordinary worker processing does not. Loss of the rebuild acknowledgement fails
marker/epoch checks closed and requires explicit retry. No LLM is needed.
Manual graph corruption/partial deletion outside transactional worker writes needs
explicit audit/rebuild; normal queries do not certify the entire graph with O(n)
checks. Positive hits remain canonically revalidated. Outbox/state are not a second
semantic truth and are not necessary to re-interpret sources during recovery.

### Executed tests and observed behavior

`tests/test_projection_outbox.py` reuses the real SQL/Neo4j pipeline fixture, then
upgrades that disposable database from 0003 to 0004. All graph namespaces are tied
to the unique test database; no persistent QH server is a test fallback.

PASS: 13 outbox tests, then 86 tests (two added lease/identity tests plus the 84
existing graph/pipeline/Core/identity regressions), plus the concurrent rollback
and new-empty-space cases: **101 distinct tests**. Ruff passed. Unchanged 0003 schema evidence was reused.

| Requirement | Actual evidence |
| --- | --- |
| Atomic outbox | Exact canonical replay adds no event; deferred validation and multi-record failure roll back intent/counter |
| Affected-only update | One item update loads/projects exactly one revision; instrumentation rejects read_snapshot without exact IDs on ordinary worker and query paths |
| Durable failure/restart | Failed state and lag recorded; real local Bolt connection refusal retried; expired worker lease recovered; polling survives temporary SQL exception |
| Ack loss/duplicates/order | Graph commits then synthetic SQL ack loss; retry projects zero rows; future delivery rejected until predecessor, older delivery cannot regress head/marker |
| Lease/epoch fencing | Old token may complete graph I/O but cannot ack a replacement lease; rebuild fences old workers |
| Commit order | Two concurrent SQL publishers, one rollback: next committed intent gets exactly next scope version despite a global event-ID gap |
| Empty-schema activation | Newly created space gets state automatically, fresh empty query needs no snapshot scan, first committed revision creates/projections its intent |
| Fresh reads/isolation | Pending state blocks both hits/empty results; owner/mixed scopes denied; two owners independently retrieve Cedar/Birch |
| Rebuild | Explicit new generation reconstructs current canonical data and item heads, retaining prior generations and exact evidence |
| Writers | Identity provisioning preflight supports 0004 and stays idempotent; existing historical migration tests stay pinned |

Reproduction inside the locked backend image with the existing dedicated SQL/Neo4j
env files and qh30-native-test network:
`python -m pytest -q -x --tb=short -p no:cacheprovider tests/test_projection_outbox.py`.
The integrated regression command from the previous checkpoint remains valid.
No Core/public DTO, production Compose or migrations 0001/0002/0003 changed.

### Persistent PostgreSQL inventory and simplest activation recommendation

Read-only transaction against **qh-postgres-1**, not a fixture: Alembic
**0002_oidc_identities**. Public schema has only the nine expected tables
(including alembic_version). Aggregates, without reading/displaying text or identities:

| Data | Rows |
| --- | ---: |
| users / user_identities | 0 / 0 |
| context_spaces | 0 |
| sources / source_revisions | 0 / 0 |
| understanding_items / understanding_item_revisions | 0 / 0 |
| item_revision_provenance | 0 |

There are **no canonical data, accounts or development records to preserve in this
PostgreSQL database**. The retained read-only dump hash, container ID and mounts
are unchanged. This says nothing about the separate historical Neo4j Graphiti
prototype; its graph, branch, PR and volumes must remain untouched.

Recommendation after explicit authorization: advance the **empty existing schema**
with the pinned migrations 0003 → 0004, which is simpler and less destructive than
recreating a database/container/volume. This is an empty-schema initialization,
not a historical-data conversion. A clean logical database recreation is possible
only with separate explicit authorization but adds no benefit for these counts.
Do not build an elaborate data-backup/restore procedure for zero rows.

Activation steps, **not executed**:
1. Reconfirm this read-only inventory immediately before activation and stop
   canonical writers. Pin reviewed commit/image and 0004 target, not upgrade head.
   If any data have appeared, stop and choose the earlier backup/verified-clone
   migration path based on their actual shape; do not classify them as disposable.
2. Authorize and apply 0003/0004 to the empty QH schema without deleting volumes.
   Verify three canonical + two operational tables, triggers/constraints, and
   unchanged empty canonical counts. Keep Graphiti runtime/data/worktrees separate.
3. Explicitly compose the registered repository, incremental engine/PolicyService
   and backend worker with correct QH configuration. Bootstrap identities/spaces
   only through separately authorized existing workflows. Verify scoped synthetic
   write → pending → worker → ready → retrieval, then resume writers.
4. On initialization failure, transactional DDL rollback preserves the prior schema;
   diagnose/retry before activation. After new canonical data exist, do not discard
   them or attempt destructive downgrade: stop writes and use reviewed repair/
   backup-and-restore based on actual content. Migrations remain forward-only.

Persistent 0003/0004 execution, destructive recreation, push/merge, Jira writes and
paid APIs remain unauthorized and were not performed. QH-30 remains in progress.
