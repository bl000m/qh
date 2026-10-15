# QH-30 / QH-7b — canonical delta and first native increment

## Current checkpoint — read this before historical milestones

Post-cutover semantic review: [proposal, prioritized debt inventory and QH-8 plan](qh-semantic-consolidation.md).
A separate branch/worktree based on preserved `42a20c7` tests generic structural
profiles and prepares 0005. No persistent change/deployment is authorized. The
specialized-default QH-8 proposal at the end is historical; demonstration meanings
need not each be registered SQL types. Deployed code remains pinned to fd50b1b.

| State | Result |
| --- | --- |
| Approved | PostgreSQL canonical; native rebuildable Neo4j; versioned universal semantic model |
| Completed in isolation | 0003 three canonical tables; real repository; multidomain SQL→Neo4j integration; 0004 two operational tables and incremental worker |
| Verified | Latest runtime/strict CI checkpoint: 178 tests passed, Ruff/actionlint; previous 101-test outbox milestone retained below |
| Persistent QH | Cutover authorized and completed: 0004, native backend/worker active at fd50b1b; two retained synthetic proposed decisions/spaces and two ready outbox intents |
| Remaining | Owner review after successful cutover; merge and historical retirement still unauthorized. Extraction, embeddings/cache and advanced retrieval remain future work |

The final **Persistent cutover execution and read-only historical inventory** section
records the current deployment. Earlier authorization/deployment gates below describe
their historical milestone and were superseded only by the owner-authorized cutover.

Historical sections below preserve what was true at each milestone. Earlier deferrals
of the outbox are superseded by the final **Incremental outbox and backend worker**
section. Historical test counts are not additive totals or evidence of deployment.
`make migrate` runs `upgrade head` and grants no authorization. Any future cutover
must recheck the inventory and explicitly target **0004_projection_outbox** from
the reviewed native commit/image; do not apply it now.

Historical CI proposal, now implemented by the `native-integration` job below
(hosted execution/required-check configuration still pending): a required job with
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

## Runtime composition and cutover preparation (isolated milestone)

`app.bootstrap:create_runtime_app` now composes the native runtime through the
FastAPI lifespan when `QH_NATIVE_CONTEXT_ENABLED=true`. Default is false. It
requires an explicit `QH_NATIVE_GRAPH_NAMESPACE`, schema exactly 0004 and Neo4j
connectivity; startup never migrates. `app.state.native_context.context_for(subject)`
binds the existing authorized service to an owner-scoped repository. No new public
HTTP/MCP ingestion or retrieval contract is introduced (QH-9 remains separate).

`adapters/context/runtime.py:NativeRuntime` owns one backend-local polling thread.
It discovers due queue/scope metadata, then uses owner-bound workers/repositories;
new scopes and owners do not need a backend restart. Errors log only exception
classes, with durable per-scope attempts/lag/failure in `sync_status`. SQL/graph
outages are retried through the existing leases/backoff; shutdown signals and joins
the thread before closing the driver. Runtime SQL calls have five-second statement/
lock limits; graph connection/acquisition and transaction retries are bounded.
A 30-second shutdown timeout fails explicitly rather than pretending the worker
stopped. Unacknowledged work remains recoverable from its lease after restart.

### Verification and CI

The new `native-integration` job in `.github/workflows/quality.yml` builds the locked
backend and uses `infra/docker/qh30-integration.yml`: separate internal network,
PostgreSQL/Neo4j tmpfs data, no database ports or persistent volumes. The strict
`scripts/run_qh30_integration.py` refuses missing/wrong dedicated configuration and
fails on skipped tests or empty collection. It covers SQL semantics, outbox,
canonical pipeline, application lifespan, graph and Core/identity regressions.
GitHub execution and making this check required in branch protection remain pending
remote authorization; adding a workflow does not itself configure branch protection.

Runtime tests use the actual application factory/lifespan, not a fixture reader:
source/revision save → SQL/outbox → automatically running worker → graph candidates
→ PolicyService → exact SQL hydration. They cover both owners/spaces, revision and
source provenance, pending reads, error diagnostics, shutdown/restart recovery,
old-schema startup rejection and disabled-runtime compatibility. The post-cutover
CLI probe below is also executed against the test application worker; the probe
never starts its own worker. No LLM/embedding calls occur.

PASS: final strict CI-project execution: **178 passed, zero skipped**, in 163.48s,
using the freshly built image and separate tmpfs PostgreSQL/Neo4j. The post-cutover
CLI smoke was exercised by the runtime test with the application worker. Targeted
commit-error/runtime regression run: 4 passed. Ruff, actionlint 1.7.7, Compose config
(base, pinned override and integration project), local links and diff checks passed.
Negative checks passed: missing dedicated configuration fails; unavailable PostgreSQL
fails; an intentionally skipped test makes the strict runner fail. No hosted CI or
real Keycloak protocol rerun was performed. The sole warning is the existing
Starlette TestClient/AnyIO deprecation; it did not affect test outcomes.

Reproduce from the native worktree with an ignored mode-600 test env file defining
QH30_SQL_PASSWORD/QH30_GRAPH_PASSWORD (fresh synthetic credentials):
`docker compose --env-file <test-env> -p qh30-ci -f infra/docker/qh30-integration.yml build integration`,
then the same Compose prefix with `run --rm integration`, and finally `down` for
**that disposable project only**. Never use the production Compose for this suite.
No database volumes are declared in this integration project.

An initial strict run on the existing dedicated servers passed 178 tests. Fresh
CI execution exposed a psycopg 3.2.9 behavior: its connection context manager does
not close the connection when commit fails (including deferred SQL publication
validation). This can retain sessions until garbage collection and block test DB
cleanup. CanonicalRepository now closes in a finally block, preserving the original
error. The regression keeps strong connection references and asserts closure after
a real deferred commit failure. No force cleanup, session termination or destructive
retry was introduced. The strict runner also dumps thread stacks after 60 seconds
of an unexpectedly slow test; the hosted job has a 20-minute overall timeout.

### Persistent inventory and writer compatibility

Read-only inventory reconfirmed on 2026-10-15: `qh-postgres-1` at
`0002_oidc_identities`, zero rows in users, user_identities, context_spaces, sources,
source_revisions, understanding_items, understanding_item_revisions and
item_revision_provenance. This is not permission to initialize or discard data.

The **currently deployed backend is not the native runtime**: its mounts still
point at `/home/ubuntu/qh`, and in-container read-only checks found neither the
native runtime module nor migration 0004. Do not migrate underneath this deployment.
Deploy the reviewed native worktree/image and settings as part of an authorized
cutover. The native repository writes null legacy category plus registered bindings;
identity provisioning accepts 0002/0003/0004. Historical category-writing test helpers
remain pinned to historical schemas. The OIDC test helper/live read-only probe now
accept known compatible revisions 0002/0003/0004 instead of requiring exactly 0002,
so the existing OIDC CI job can migrate its disposable application DB to head.
Real Keycloak protocol execution is not repeated by the native integration job.
No new public source/item writer is installed.
The development image already includes the locked Neo4j driver; no dependency or
lock change is required for this image. A future production-only packaging profile
must retain that driver explicitly.

### Exact activation sequence — prepared, NOT executed

Use the reviewed native worktree and a pinned image, keeping the original ignored
VPS env file outside Git. `infra/docker/qh30-runtime.yml` requires an explicit image
tag; the base Compose passes native runtime flags but defaults to disabled.
Commands below are a proposal requiring authorization, **not an instruction to run now**.

1. Recheck schema/counts read-only. Stop if any canonical/identity rows appeared;
   review preservation/backup for actual data instead of assuming disposable data.
   Quiesce all writers and stop only the existing backend when authorized. Preserve
   its image ID/configuration and all Graphiti files, graph data, branch and PR.
2. Build/pin the verified native image without changing database containers. Use
   the native worktree Compose plus `qh30-runtime.yml`, project `qh`, and the existing
   local credential env file. Set `QH_NATIVE_BACKEND_IMAGE` to that pinned image and
   `QH_NATIVE_CONTEXT_ENABLED=false`. Resolve configuration quietly and verify mount
   sources point to the native worktree; never print resolved credential settings.
3. Run a one-off native backend container with `--rm --no-deps` and explicit command:
   `alembic -c adapters/postgres/alembic.ini upgrade 0004_projection_outbox`.
   This advances 0002 → 0003 → 0004 without recreating PostgreSQL/Neo4j or their
   volumes. Do not use `make migrate`/`upgrade head`. Check exact Alembic revision,
   three canonical plus two operational additions, triggers and unchanged empty
   canonical counts. Any migration error must stop activation.
4. Enable `QH_NATIVE_CONTEXT_ENABLED=true` and a deployment-specific namespace
   `QH_NATIVE_GRAPH_NAMESPACE=qh-native` (distinct from historical Graphiti labels).
   With the same reviewed image/env/Compose files, run `up -d --no-deps --no-build
   backend` only. This replaces the backend, not databases or other services.
   Check health and redacted `native_worker_started` diagnostics. Startup rejects
   the wrong schema instead of running a migration. Native indexes/labels may now
   be created in Neo4j; historical Graphiti records are retained.
5. With separate authorization to retain synthetic smoke records, execute in the
   running backend: `python /workspace/scripts/smoke_qh30_runtime.py --write-synthetic`.
   It creates two synthetic user metadata records (no OIDC/login mappings), one
   synthetic space/source/proposed decision, waits for the **application worker**,
   validates exact item/source provenance and rejects the foreign subject.
   It retains immutable evidence and prints its synthetic scope ID; no cleanup,
   confirmation, provider call or migration occurs. A timeout/failure stops acceptance.
6. Observe ready counters/queue lag, backend health and worker recovery after an
   authorized backend restart. Only then resume canonical writers. No public QH
   context endpoint or LLM extractor is implied by this internal-runtime acceptance.

If initialization fails before writes, leave writers paused and diagnose; do not
attempt a forward-only downgrade or delete volumes. Native runtime can be disabled
while retaining schema/data for reviewed forward repair. Once smoke or other data
exist, they are immutable data to preserve, not a reason to reset the database.
The zero-row inventory avoids an elaborate historical-data backup procedure; a
new nonempty inventory changes that assumption and requires a reviewed backup path.

Required authorizations still outstanding: persistent 0003/0004 application; backend
replacement/native graph activation; retained synthetic smoke/bootstrap writes and
backend restart; remote push/CI execution and branch-protection changes. No such
operations, Jira writes, merge or paid APIs were performed by this milestone.

## Definitive VPS cutover runbook — corrected invocation, execution recorded below

Publication/PR/hosted CI and the controlled cutover were subsequently authorized
for runtime commit `fd50b1ba67061ea95285a2ffce122939524ab93f`. Execution results are
recorded below. These retained commands are not authorization to repeat migrations,
backend replacement or synthetic writes after acceptance.
The post-cutover historical-resource inventory was performed read-only after
successful native acceptance; no archival/removal is authorized.

### Pin and validate the accepted revision (safe preparation)

Use Bash and Docker access on the VPS. The authorized runtime revision has successful
quality, oidc and native-integration checks. Bind-mounted runtime files must remain
identical to that revision. The later documentation-only correction/record does not
change the image or authorize any application code change.

```bash
cd /home/ubuntu/qh-worktrees/qh-30
set -euo pipefail
test "$(git branch --show-current)" = feat/QH-30-native-context-engine
test -z "$(git status --porcelain)"
QH30_DEPLOY_COMMIT=fd50b1ba67061ea95285a2ffce122939524ab93f
export QH_NATIVE_BACKEND_IMAGE="qh-native-backend:${QH30_DEPLOY_COMMIT}"
export QH_NATIVE_CONTEXT_ENABLED=false
export QH_NATIVE_GRAPH_NAMESPACE=qh-native
QH30_ENV=/home/ubuntu/qh/.env
test -f "$QH30_ENV"
QH30_COMPOSE=(docker compose
  --env-file "$QH30_ENV" -p qh
  -f /home/ubuntu/qh-worktrees/qh-30/infra/docker/docker-compose.yml
  -f /home/ubuntu/qh-worktrees/qh-30/infra/docker/qh30-runtime.yml)
"${QH30_COMPOSE[@]}" config --quiet
python3 scripts/check_secrets.py
docker build -f apps/api/Dockerfile.dev \
  --label "org.opencontainers.image.revision=${QH30_DEPLOY_COMMIT}" \
  -t "$QH_NATIVE_BACKEND_IMAGE" .
QH30_IMAGE_ID=$(docker image inspect "$QH_NATIVE_BACKEND_IMAGE" --format '{{.Id}}')
test "$(docker image inspect "$QH_NATIVE_BACKEND_IMAGE" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = "$QH30_DEPLOY_COMMIT"
printf 'Accepted commit: %s\nImage: %s\nImage ID: %s\n' "$QH30_DEPLOY_COMMIT" "$QH_NATIVE_BACKEND_IMAGE" "$QH30_IMAGE_ID"
```

Do not copy/view API keys. Compose passes only declared database/OIDC/native
settings; no Mistral settings or provider SDK work is activated. The current
Dockerfile includes locked development dependencies, including the Neo4j driver.

### Read-only gate immediately before authorization/execution

```bash
docker exec qh-postgres-1 sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "BEGIN READ ONLY; SELECT version_num FROM alembic_version; SELECT '\''users'\'',count(*) FROM users UNION ALL SELECT '\''user_identities'\'',count(*) FROM user_identities UNION ALL SELECT '\''context_spaces'\'',count(*) FROM context_spaces UNION ALL SELECT '\''sources'\'',count(*) FROM sources UNION ALL SELECT '\''source_revisions'\'',count(*) FROM source_revisions UNION ALL SELECT '\''understanding_items'\'',count(*) FROM understanding_items UNION ALL SELECT '\''understanding_item_revisions'\'',count(*) FROM understanding_item_revisions UNION ALL SELECT '\''item_revision_provenance'\'',count(*) FROM item_revision_provenance; COMMIT;"'
docker inspect qh-backend-1 --format '{{.Id}} {{.Image}} {{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}'
docker inspect qh-postgres-1 qh-neo4j-1 --format '{{.Name}} {{.Id}} {{range .Mounts}}{{.Type}}:{{.Name}}:{{.Destination}} {{end}}'
```

Expected: 0002 and eight zero counts. Stop if different; do not classify new rows
as disposable. Record old backend image/mounts and DB container/volume identities
in a restrictive local operational note, not a full environment/container dump.
No historical-resource inventory or backup/export of Neo4j is needed at this gate.

### Authorized maintenance window ONLY

The following commands are **not executed by publication/CI authorization**.
Ensure all external/manual canonical writers are quiescent. Both DB services,
frontend/MCP/Keycloak and all volumes remain running/unchanged.

```bash
test -z "$(git diff --name-only "$QH30_DEPLOY_COMMIT" -- . ':(exclude)docs/qh-30-plan.md')"
test -z "$(git status --porcelain)"
test "$(docker image inspect "$QH_NATIVE_BACKEND_IMAGE" --format '{{.Id}}')" = "$QH30_IMAGE_ID"
"${QH30_COMPOSE[@]}" stop backend
"${QH30_COMPOSE[@]}" run --rm --no-deps backend \
  alembic -c adapters/postgres/alembic.ini upgrade 0003_native_semantics
"${QH30_COMPOSE[@]}" run --rm --no-deps backend \
  alembic -c adapters/postgres/alembic.ini upgrade 0004_projection_outbox
"${QH30_COMPOSE[@]}" run --rm --no-deps backend \
  alembic -c adapters/postgres/alembic.ini current
```

Each explicit migration is transactional; because these are separate invocations,
a failed 0004 can leave **0003 committed**. Keep the backend stopped, diagnose and
retry/repair forward; do not assume both migrations rolled back or run downgrade.
Verify 0004, the three canonical/two operational tables and unchanged zero counts
before enabling the runtime. A count/constraint mismatch stops the procedure.

```bash
docker exec qh-postgres-1 sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "BEGIN READ ONLY; SELECT version_num FROM alembic_version; SELECT table_name FROM information_schema.tables WHERE table_schema='\''public'\'' AND table_name IN ('\''semantic_type_versions'\'','\''item_revision_types'\'','\''relation_revision_details'\'','\''projection_outbox'\'','\''context_projection_state'\'') ORDER BY table_name; SELECT count(*) FROM understanding_item_revisions; SELECT count(*) FROM sources; SELECT count(*) FROM projection_outbox; COMMIT;"'
export QH_NATIVE_CONTEXT_ENABLED=true
"${QH30_COMPOSE[@]}" up -d --no-deps --no-build --wait --wait-timeout 120 backend
test "$(docker inspect qh-backend-1 --format '{{.Image}}')" = "$QH30_IMAGE_ID"
docker inspect qh-backend-1 --format '{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}'
"${QH30_COMPOSE[@]}" exec -T backend python -c 'from pathlib import Path; assert Path("adapters/context/runtime.py").is_file(); import urllib.request; assert urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5).status == 200; print("PASS: native files and backend health")'
"${QH30_COMPOSE[@]}" logs --no-color --tail 60 backend
```

All five source mounts must point into `/home/ubuntu/qh-worktrees/qh-30`, including
scripts/tests. They must no longer point at `/home/ubuntu/qh`. DB container IDs and
volume names must match the pre-cutover values. The process must finish native
startup (schema/connectivity/index initialization and worker thread creation);
health alone is not projection proof. Routine Uvicorn logging may suppress the
worker's INFO line; the smoke proves actual processing. Restrict log inspection to
this backend and never print raw environments. Native label/index additions are
expected only after this authorized activation, retaining historical Graphiti data.

### Authorized synthetic acceptance and restart/recovery

```bash
"${QH30_COMPOSE[@]}" exec -T backend python /workspace/scripts/smoke_qh30_runtime.py --write-synthetic
"${QH30_COMPOSE[@]}" restart --timeout 40 backend
"${QH30_COMPOSE[@]}" exec -T backend python -c 'import time,urllib.request; time.sleep(2); assert urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5).status == 200; print("PASS: restarted backend health")'
"${QH30_COMPOSE[@]}" exec -T backend python /workspace/scripts/smoke_qh30_runtime.py --write-synthetic
```

Each smoke retains two synthetic users without login mappings, one space/source
and one proposed decision. It waits for the application worker, validates exact
SQL-backed provenance and denies the foreign subject. Record both printed scope
IDs. No real user/source text, LLM or embedding request is involved. The second
smoke proves the restarted process handles newly committed work. Deliberate crash,
ack-loss and DB-outage injection stay in disposable CI tests; do not stop the
shared persistent Neo4j merely to reproduce them.

If health is not ready immediately after restart, poll it for up to 120 seconds
before acceptance; do not rerun the write probe until health succeeds. Both smoke
results and DB identity checks must pass before writer resumption. Projection
failure leaves durable pending/failed work and preserves canonical data.

### Failure handling and deferred historical inventory

- Before migration: leave/restart the old backend only if PostgreSQL is still
  exactly 0002 and its original image/configuration are verified unchanged.
- At 0003 or 0004: keep writers stopped. Never restart the Graphiti/category writer
  against the upgraded schema. Use the pinned native image for reviewed forward
  repair. Preserve original backend image/configuration, but it is not a safe
  schema rollback mechanism.
- Native activation/smoke failure: stop only the backend or set native opt-in false
  and recreate only that backend if needed for identity/health diagnosis. Do not
  claim context availability in disabled mode. Preserve smoke IDs, outbox state,
  redacted causes and all canonical records. Do not delete history, force ready,
  change epochs manually or downgrade. Rebuild is an explicit reviewed maintenance
  operation if markers are inconsistent; ordinary provider-free retries cover
  transient delivery failures.
- Never use `down`, `--volumes`, database recreation or volume pruning on project
  `qh` during this procedure. If real data appear, select a reviewed preservation/
  backup/restore path before proceeding; this zero-row runbook is no longer enough.
- Only **after owner-authorized activation and successful acceptance**, inventory
  historical Graphiti/SurrealDB resources read-only and propose a separate staged
  retirement plan with use/shared-resource/disk/risk evidence. No historical
  resource is removed by this cutover. Preserve Graphiti branch, Draft PR #1 and
  architectural evidence regardless of future infrastructure retirement.


## Persistent cutover execution and read-only historical inventory

Owner-authorized on 2026-10-15, including the explicit correction to omit
`--project-directory`. Runtime code/image remain **fd50b1ba67061ea95285a2ffce122939524ab93f**.
This subsequent edit changes only this documentation file. The corrected Compose
invocation uses absolute `-f` paths and `-p qh`; its default project directory is
`infra/docker`, so relative build/bind paths resolve to the native worktree.
The rejected invocation resolved build context to `/home/ubuntu` and backend mounts
to `/home/ubuntu/apps/...`; it was stopped before mutation and never deployed.

### Observed acceptance results

| Check | Actual result |
| --- | --- |
| Last preflight | PASS: 0002, eight empty application tables; exact five native mounts; matching DB settings; existing volumes/networks |
| PostgreSQL targets | PASS: explicit 0003 then 0004; 14 tables, 71 validated constraints, 24 enabled triggers, 11 compatibility type versions |
| Native backend | PASS: only `qh-backend-1` replaced; container `813b466e674d73bc363bc8d253db432cab30b3f4d837d53e323d33ec0842c30e` |
| Image | `qh-native-backend:fd50b1ba67061ea95285a2ffce122939524ab93f`, ID `sha256:0d30a854117eefebb14f83ec2ffcf892f7d9c383a6d9c66576d66d9067547e45`; revision label matches |
| First smoke | PASS: source → SQL/outbox → actual application worker → authorized graph retrieval → exact canonical provenance; foreign user denied |
| Controlled restart | PASS: same new backend container/image/mounts, new process start time; pre-restart data still retrievable and new post-restart intent processed |
| Cross-space checks | PASS: each owner gets exactly its own hit; foreign and mixed scopes denied; both scopes ready 1/1, attempts 1, no persisted error |
| Temporal/validation | Unknown fact/validity bounds remain null; interpretations remain proposed; no automatic confirmation |
| Graph namespace | `qh-native`; 10 nodes: two each QH30Item/Revision/Slice/Source/Sync; zero relationships to Graphiti nodes |
| Graphiti integrity | PASS: 3 Entity + 3 Episodic, four incident relationships, identical IDs/labels/properties/relationship fingerprint before and after activation/restart |
| Shared services | PASS: PostgreSQL, Neo4j, frontend, MCP, Keycloak container IDs/images/mounts retained; qh_app/qh_data network IDs and DB volume names unchanged |
| CI / publication | Draft PR #2, runtime head fd50b1b; hosted run 38727480617 passed quality/oidc/native-integration, 178 native tests with zero skips; no merge |

The three native settings (enabled=true, namespace=qh-native, commit-tagged image)
are retained in the existing ignored `/home/ubuntu/qh/.env`, mode 0600. Provider
settings were preserved and not printed. Only use native Compose paths for backend
operations; `/home/ubuntu/qh` remains the historical checkout, not the backend source.
No LLM, embedding or paid-provider request occurred during activation.

Retained synthetic records (all exact IDs and canonical metadata are in private
local evidence outside Git at `/home/ubuntu/qh-cutover-evidence`):

| Probe | Context Space | Item revision | Source revision |
| --- | --- | --- | --- |
| Before restart | 0b6d7e9f-8fff-4f05-8878-b8e49aeb32df | 2aa3bf8a-b531-4b51-8293-509d5aa6d7aa | 31f60c61-1dd2-4a24-97ab-8c29c1b0fdec |
| After restart | 36143133-3dde-43d7-a2a1-c7886a8e87a1 | 24bd95a7-74e2-4c77-a7df-ba0aaed0ba1d | 65790291-9b1c-4de8-8f22-b4ab8ed33646 |

There are four synthetic user metadata rows, zero OIDC mappings, two spaces/sources/
source revisions/items/item revisions/provenance rows, and two ready outbox rows.
Neither smoke record nor historical data was deleted. Restart acceptance proves
retained reads and fresh post-restart processing; deliberate ack-loss/crash/outage
injection remains disposable CI evidence, not a persistent failure experiment.

Nonblocking diagnostic observation: Neo4j emitted UnknownPropertyKeyWarning for
`scope_manifests_json`. The reused reader asks for the optional full-reconciliation
manifest, while incremental readiness uses epoch/version counters and does not
require that property. Both retrieval/scope gates passed. No property, runtime code
or historical fact was modified to suppress the warning; any cleanup is later work.

Historical graph integrity SHA-256:
`f604509c02424ecd613ae965e873ec4ba880461b37c122c3757a14c1ff032f32`.
This covers exact six nodes and four incident relationships, not just counts.

### Read-only inventory and retirement proposal — nothing removed

Measurements are a live snapshot, rounded decimal MB unless stated otherwise.
Volumes use allocated bytes from `du -sB1`; Docker image sizes include shared layers.
They are not additive guaranteed reclaim totals. Full IDs, mount owners, network
members and private artifact paths are retained in local inventory evidence.

| Resource | Purpose / current use | Shared? | Proposal and risk / potential benefit |
| --- | --- | --- | --- |
| qh-postgres-1, qh_postgres_data (~98 MB) | Canonical QH at 0004, retained smoke and governance foundation | Active QH | Preserve; deleting loses canonical data |
| qh-neo4j-1, qh_neo4j_data (~543 MB), qh_neo4j_logs | Native graph and historical six Graphiti nodes coexist in the same instance/database | Active QH + history | Preserve container/volumes. Any future historical-node cleanup requires exact export/IDs and separate approval; no database/volume deletion |
| qh_app, qh_data; frontend/MCP/Keycloak and qh_keycloak_data | Current application network, UI/MCP scaffolds and identity service | Active QH | Preserve; removal interrupts live services |
| qh-backend:latest and qh-backend:qh7 | Old Graphiti backend images; zero container references after replacement | Not runtime; layers/cache shared | Candidates after acceptance/archive approval. ~544 MB virtual each but only ~0.53 MB unique per image in Docker df; joint reclaim depends on shared layers/cache. They cannot safely roll back the upgraded SQL schema |
| qh-surreal-spike-surreal-1 / postgres-1 / neo4j-1 | Still-running isolated unfinished spike; no native QH dependency | Dedicated containers/data/network; base PG/Neo images shared | Archive uncommitted experiment/results before separately authorizing stop/removal. ~606 MiB observed RAM across the three; Neo4j writable layer ~170 MB. Its neo4j/system databases are online; no nodes were returned in its user graph inventory |
| qh-surreal-spike_surreal-data, pg-data, neo-data and their /logs volumes | Dedicated spike persistence; network qh-surreal-spike_default has only those three containers | No production sharing | ~667 MB allocated in total at measurement. Eligible only after archive decision; deletion loses experiment state. Container-specified anonymous logs are mapped in evidence |
| surrealdb/surrealdb:v3.3.0 | Used only by spike SurrealDB container | Exclusive image | ~481 MB image, candidate only after that container is retired. Keep postgres:16.8-alpine3.21 and neo4j:5.26.5-community images: QH and tests still use them |
| qh30-sql-test, qh30-native-neo4j-test, qh30-native-test network | Native regression infrastructure, distinct from Graphiti/SurrealDB and production | Shared by ongoing QH-30 tests | Not obsolete history. Can later be stopped/recreated with explicit authorization; current total RAM ~801 MiB, test graph volume ~548 MB plus logs; PG is tmpfs |
| /home/ubuntu/qh (Graphiti branch 77de43c) | Historical Git branch plus common Git object store, VPS .env, active frontend/MCP/Keycloak mounts | Strongly shared | Preserve whole checkout now (~4.8 MB measured including common Git objects); removing breaks worktrees/configuration/live mounts. Branch/PR #1/evidence must remain permanently available |
| /tmp/qh-surrealdb | Spike worktree b1769b6 with untracked spike/ | Experiment only; common Git shared | ~1.0 MB. Archive uncommitted work before any future move/removal; do not classify as a completed benchmark |
| /tmp/qh7-* and qh7_* | 36 checkpoints, response/cache/log/helper artifacts, including qh7-graphiti and uuid-before-fix | Historical reproduction evidence | ~2.2 MB combined. Preserve useful evidence; classify/redact content before any archive/pruning. Naming-only inventory does not certify every artifact contains no sensitive data |
| qh30-runtime-ci-local-integration image and /tmp/qh30* | Native CI image and ongoing test/cutover helpers/credentials | Native development, not historical Graphiti | ~430 MB image almost entirely shared with current native image; no useful independent 430 MB reclaim claim. Preserve required credentials securely; later select only redundant generated artifacts |
| Docker build cache | ~1.533 GB aggregate cache across historical and native builds | Mixed/shared | Not all attributable to Graphiti; no global prune. Select build records only in a separately reviewed cleanup |

Progressive proposal (all steps require separate approval): first archive necessary
spike/untracked material and provider-free checkpoints, retain branch/PR #1 and
canonical evidence; then stop only the dedicated spike containers and observe QH;
then remove only proven exclusive spike data/images/network after archive validation;
finally consider unused old backend images and individually identified temporary/cache
artifacts. Keep shared services/volumes/base images/common Git checkout intact.
No retirement operation, branch/worktree deletion, Jira write, merge or paid API
was performed. Persistent cutover acceptance and this inventory stop here for owner review.

## Historical post-cutover consolidation and first QH-8 proposal (planning only)

The owner authorized publication of documentation-only `eeadeef` on QH-30.
Draft PR #2 now targets that commit. Hosted [run 38736085229](https://github.com/bl000m/qh/actions/runs/38736085229)
passed quality, oidc and native-integration; the native job executed 178 tests
with zero skips (99.31s), and both selected live OIDC tests passed. Runtime files and the deployed image remain
`fd50b1ba67061ea95285a2ffce122939524ab93f`. The cutover result, synthetic IDs and
technical evidence above are retained. Extraction, embeddings/cache and advanced
semantic/vector search remain unimplemented. No further persistent DB writes,
service stop, archival export or retirement operation is authorized by this plan.

### SurrealDB archive and stop plan — prepared, not executed

Fresh read-only checks found no active QH dependency: the six QH services use
qh_app/qh_data; the three spike services use only qh-surreal-spike_default. Their
volumes are disjoint, no QH bind mount points into the spike worktree, and native
code/configuration and effective QH endpoint settings contain no spike references.
No established TCP connection was observed on the spike's loopback ports 18080
and 17474 at inspection. This is a snapshot, not proof that another host client
will never use them; recheck and quiesce experimental writers before an authorized stop.
PostgreSQL and Neo4j base images remain shared with production/native tests and
must not be removed as part of spike retirement.

| Future step | Activity and acceptance gate |
| --- | --- |
| 1. Preserve experiment | Record container/image IDs, volume owners, version pins, namespace/database names and uncommitted spike/ files in /tmp/qh-surrealdb. Check local free space for archives and disposable restore copies; copy code/schema/seed/results plus a manifest/checksums into a protected local archive outside Git. Keep credentials separate and restricted; do not copy an unfiltered environment into logs/repository or send archives externally |
| 2. Logical exports | Once separately authorized, stop experimental writers, export each actual Surreal namespace/database and make a custom-format pg_dump of the dedicated spike PostgreSQL database. Inspect the installed export flags; the running v3.3.0 CLI supports namespace/database-scoped SurrealQL export. Exports may contain authentication metadata and require private handling. Do not run exports now |
| 3. Cold Neo4j archive | The installed Neo4j dump command cannot dump a database mounted by a running server. In an approved maintenance window, stop only qh-surreal-spike-neo4j-1 gracefully, then archive its dedicated data/log volumes cold (or run the pinned admin dump offline). Never use live tar as a claim of a consistent graph backup; never point the admin tool at qh_neo4j_data |
| 4. Validate restore | Check archive hashes and restore exports/cold copies into fresh disposable resources with the same version pins and no QH network/volume attachment. Compare schema/record counts/identifiers. A failed validation blocks deletion and preserves the original spike volumes |
| 5. Stop, retain | After archive acceptance and fresh dependency checks, gracefully stop exactly qh-surreal-spike-surreal-1, qh-surreal-spike-postgres-1 and qh-surreal-spike-neo4j-1; retain containers, volumes, network, images and worktree. Recheck native backend/DB health, existing scoped reads and outbox state read-only; no extra production smoke writes |
| 6. Later retirement | Only with separate deletion authorization remove proven exclusive spike resources. Preserve Graphiti branch/PR #1, common Git checkout, QH data/networks/base images, and required architectural/experimental evidence |

Initial archival/export and stopping are themselves pending approval, not merely
volume deletion. No stop/export/restore has been performed. Potential resource
benefit after a future stop: approximately 606 MiB RAM across three spike services.
Future deletion could release approximately 667 MB allocated spike volumes and the
481 MB exclusive SurrealDB image, plus container writable layers; image/cache
sharing prevents treating these as an exact additive disk total.
Dependency-check evidence remains private/local at
`/home/ubuntu/qh-cutover-evidence/surreal-dependencies-postcutover.json`.

### QH-8: one conversational source, three identified excerpts, one complete flow

Read [QH-8](https://contextlab.atlassian.net/browse/QH-8) in full through Atlassian
MCP on 2026-10-15. It has no comments. Ticket dependencies are QH-4 and QH-30;
QH-8 blocks QH-10. No Jira field/status/link was changed. The original 1.5 h is
explicitly marked for recalibration; this proposal does not promise that estimate.

Recommend one synthetic conversation represented by one immutable source revision,
with three explicit excerpt/turn IDs and original character intervals recorded in
origin metadata. These are three imported episodes/excerpts in the same Context
Space, not three revisions of different content pretending to be source history.
No episode table or Source Vault implementation is needed. Exact source revision
and locators are retained; inline text is a representation and does not preclude
future original-byte storage outside PostgreSQL in QH-31.

Use the excerpts to cover professional, health and family contexts in one space.
For example, an explicit pilot decision, an observation plus a tentative explanation
(no diagnosis), and an unresolved household question. Expected fixture outputs are
at least decision, hypothesis and open_question; add one observation to exercise a
new registered type without a new schema migration. Expectations belong in tests,
not domain names or fixture-specific correction rules in the production extractor.
The Jira word category maps to registered type_id/version; do not restore the old
category CHECK or a closed project-domain enum.

| Unit | Minimum implementation / reused dependency |
| --- | --- |
| 1. Controlled import + fixtures | Manual internal development command, explicit authorized owner/space, stable source/revision IDs, original transcript and three deterministic excerpt locators. Reuse CanonicalRepository source save; fixture B tests denial and cross-space isolation |
| 2. Replaceable extractor | Small application extractor using existing LLMProvider.generate with SDK-free messages; provider adapter configured for structured JSON output, with provider-specific schema/HTTP decoding confined to adapters/llm. Fake/replay provider first. No new Core port or public HTTP/MCP contract is needed for this increment |
| 3. Validate and publish | Validate pinned type/schema versions, payload shape, excerpt IDs and literal citations against the exact stored source revision. Unknown references, malformed output and unsupported dates fail without auto-repair. Register explicit trusted type versions if stricter content schemas are needed; retain old versions and the limited qh-schema-1 profile. Use nullable temporal fields and proposed state; do not move confirmed-current pointers |
| 4. Native persistence/retrieval | Persist all accepted item revisions and exact provenance in one CanonicalRepository transaction; 0004 triggers enqueue intents atomically. Existing application worker projects them. Wait for ready, use authorized ContextEngine retrieval, then bulk-hydrate selected canonical revisions to show type/version, structured content, proposed state and exact source evidence |
| 5. Persistence and failure proof | Real isolated PostgreSQL/Neo4j tests, actual application lifecycle, replay/idempotence and rejected output rollback. After restart, read canonical understanding without another LLM call. Demonstrate direct canonical reads with graph unavailable; normal graph retrieval must report unavailable/pending rather than invent a fresh result |
| 6. Bounded real demonstration | Only after offline success and separate approval: one planned logical extraction for the three excerpts/four small proposals, preferably one HTTP request, zero embedding calls, no automatic retry/parallelism. Present the exact provider/model/endpoint/prompt/output cap, request count and cost estimate before seeking experiment authorization |

The source is committed before LLM work; no DB transaction stays open during the
request. Failed extraction preserves its source and publishes no successful batch
of understanding/outbox intents. Stable IDs and a private synthetic checkpoint
(input hash, exact source revision, pinned schemas, sanitized response and ID mapping)
allow offline replay and exact repository replays without another paid request.
This is an explicit bounded demonstration, not a new persistent LLM job scheduler.
Citations matching text establish a locator, not automatic proof that a model's
interpretation is true; semantic assertions are checked against controlled fixtures
and remain proposals. Acquisition timestamps never supply missing fact dates.

Authorization boundary: existing PolicyService READ_CONTEXT precedes protected reads
and retrieval; it does not grant a public ingest/write action or permission to
send content to an LLM. The first command is an explicitly authorized internal
operation, using the same owner/scope SQL guards as QH-30. Writes and external
provider disclosure must be covered by the owner's separate authorization. Public
write/disclosure actions and routes would require contract/policy approval and are
not silently added here. CI/startup must never call the real provider.

The existing ContextResult carries hits/revision/provenance references, not the
complete structured item DTO. The internal demonstrator bulk-hydrates those IDs
with the canonical repository and displays the typed canonical rows and source
locators. That proves persisted understanding rather than only text chunks without
changing public response contracts. Natural-language reasoning/QH-10 and a public
CRUD/import UI/QH-9 are not prerequisites for this internal proof.

### Proposed QH-8 acceptance (not yet implemented or executed)

- Three identifiable conversational excerpts in one authorized space, retaining
  original source revision, turn IDs and exact source intervals.
- At least decision, hypothesis and open_question persisted as separate typed QH
  item revisions, plus an observation fixture for extensibility/multidomain coverage.
- Every proposal cites an existing same-space source revision with locators checked
  against original text; unknown time stays null, no automatic confirmation or
  mutation of approved history. No invented missing entities/relations are needed.
- Authorized retrieval returns the expected item IDs and exact evidence; canonical
  hydration exposes type/version, content and proposed state. Cross-owner and mixed
  scopes fail before disclosure. No claim of vector/hybrid search: current native
  candidate matching remains substring-based.
- Restart preserves canonical items and evidence; a fake provider that fails on
  unexpected invocation proves no re-extraction on read/rebuild/replay. Duplicate
  publication does not create extra revisions/intents; malformed output does not
  produce a partially successful item batch. Graph outage does not erase SQL data.
- Source-driven fixtures cover project, health and personal/family contexts without
  clinical/personality confirmation; changing the fake provider keeps QH output
  and persistence behavior independent of SDK/provider formats.
- Docker tests and dependency/public-contract guards pass; real API smoke remains
  separate, blocked pending a scoped cost authorization. No current persistent QH
  writes, new migrations, Domain Packs, advanced resolution, human approval UI,
  sharing or embedding/vector implementation is included in this planning task.

Git/runtime safety for implementation: QH-30 remains unmerged. After approval, use
a separate QH-8 branch/worktree based on the reviewed native code (or main after
an independently authorized merge). Do not implement in the live QH-30 worktree:
its application directories are bind-mounted into the running VPS backend. Keep
QH-8 code/tests/providers isolated until a separately approved deployment.

This is a proposed first QH-8 increment, not a completed extraction capability or
permission to execute the experiment. QH-4/QH-30 infrastructure is technically
available; owner acceptance/merge/ticket completion remain separate decisions.
