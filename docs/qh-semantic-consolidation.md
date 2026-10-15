# QH — semantic foundation after cutover

2026-10-15. Architecture proposal and isolated implementation; **not a deployed
model change**. Baseline `42a20c7`, preserved on QH-30 and inherited by
`refactor/QH-30-semantic-foundation` in a separate worktree. The live backend still
uses `fd50b1ba67061ea95285a2ffce122939524ab93f`, schema 0004 and the QH-30 mounts.
No persistent writes, container changes, historical-resource cleanup or remote
publication belong to this increment. Cutover evidence remains in
[QH-30](qh-30-plan.md#persistent-cutover-execution-and-read-only-historical-inventory).

## Recommendation and its limits

Use three generic registered profiles for **new** understanding, retaining the
versioned registry for optional justified extensions. The experimental names are
`qh.generic.item/1`, `qh.generic.entity/1`, `qh.generic.relation/1`; publication of
these as defaults needs owner acceptance. This is three initial write profiles,
not a registry limited to exactly three records. `qh.entity/1` already exists:
reusing that immutable ID/version with a stricter schema conflicts and is rejected.

`item`, `entity`, `relation` select storage constraints. They do not describe all
meaning. A decision and a hypothesis can share item shape; a concept may need
entity identity; a relation can connect any shapes, including another relation.
An item identity cannot change shape across revisions. No domain discriminator,
mandatory semantic category, second enum or automatic type registration is needed.

Candidate content profile, exercised in isolated tests: an object with nonempty
`text`; optional `descriptors` (array of nonempty free strings), optional
`properties` (object), and extensible additional properties. Descriptors are
retrieval annotations as data, not an ontology or an authority for access/state.
An item with no descriptors remains valid. New meanings need no new registry row.
Generic relation rules use `any_registered`; the predicate and exact endpoints
remain authoritative columns in `relation_revision_details`, not copied JSON.
This deliberately small schema does not validate arbitrary extension properties.

| Guarantee / capability | Three generic profiles | Specialized type/version |
| --- | --- | --- |
| Stable IDs, same-space source evidence, exact endpoint anchors | Same SQL FKs and immutable publication guards | Same |
| Shape stability, revisions, validation actor/time, confirmed-current pointer | Same, independent of content descriptors | Same |
| Occurrence/applicability, unknown bounds, ownership and outbox atomicity | Same universal binding/state columns and policy | Same |
| Payload checking | Generic envelope; arbitrary extension details remain unvalidated | Pinned schema can require fields, value types and supported enums |
| Relation meaning | Nonempty predicate and registered anchored endpoints | Pinned allowlist can restrict exact predicate and endpoint type/versions |
| Decision versus hypothesis selection | Explicit optional descriptors/text; no universal inference guarantee | Type filter has exact declared membership, still no proof of truth |
| New meaning | Add content without registry provisioning | Register only if a new validation obligation warrants it |

**Integrity is not entirely equivalent.** Three generic profiles preserve universal
integrity, but lose the ability to distinguish different item meanings through
endpoint type allowlists or specialized payload schemas. Today's eleven historical
v1 schemas accept arbitrary content objects and `qh.relationship/1` uses
`any_registered`, so they do not currently supply those stricter semantic guarantees.
Later specialized schemas/rules in regression tests do, and must remain supported.
No SQL schema validates textual entailment or converts an inference into confirmation.

Concrete cases:

- Pilot decision, tentative explanation and open question: all generic items,
  different text/properties and optional descriptors, same exact source revision.
- Reported tiredness, household preference, and a previously unknown “reversible
  pause”: same profile; no clinical/personality assertion or new registered type.
- A team's description evolves E1→E2: an existing `selected_by` relation retains
  E's stable ID and its immutable E1 anchor. A relation-to-item/relation remains legal.
- A structured measurement needing a numeric amount and an explicit allowed unit
  justifies an optional versioned schema. A contractual relation permitted only
  between two specialized registered endpoint types justifies a versioned allowlist.
  Generic item→entity alone cannot enforce that rule. Use supported `qh-schema-1`
  keywords only; units/schema integrity does not establish medical correctness.

## Selective retrieval without mandatory categories

The deployed engine does scoped substring candidate search, SQL hydration and
freshness rechecks. It has no descriptor query port, vector ranking or semantic
classifier. This increment demonstrates exact descriptor selection **after canonical
hydration of a bounded candidate set**, plus text retrieval of a novel meaning.
That does not establish complete recall across an entire Context Space: a candidate
limit or an unlabeled equivalent assertion can omit relevant understanding.

For the first QH-8 demonstration, use controlled conversation/query text and
optional descriptors in validated output; hydrate exact returned revision IDs,
then select an explicitly requested descriptor. Explain this limit in the demo.
For exhaustive descriptor selection, a later authorized internal query can apply
an exact JSON predicate in owner-authorized SQL with explicit pagination, or project
descriptors into a derived index with canonical revalidation. Natural-language
“all decisions” needs agreed annotation/query semantics, synonyms and measured
recall; three storage shapes cannot supply those semantics. Do not hide a closed
category list inside a required JSON key. No public query DTO changes are made here.

## Prioritized debt inventory

Inspection covers tracked native code, instructions, manifests, scripts/workflows,
fixtures and documentation. Historical checkouts/resources are read only. Paths
below are relative to this worktree unless absolute.

| Priority / disposition | Concrete paths | Finding and action |
| --- | --- | --- |
| P0 simplify — done locally | `AGENTS.md`, `README.md`, `docs/architecture.md`, `docs/postgres-schema.md`, `apps/api/adapters/README.md` | Present-tense “0002/empty/not authorized” contradicted successful cutover. Distinguish deployed 0004/fd50 from this unpushed candidate; prohibit edits through live mounts |
| P0 simplify — done locally | `docs/product/QH_PRODUCT_CONTRACT.md`, `docs/adr/0003-native-context-engine.md` | Examples could imply mandatory semantic classes; clarify transverse dimensions and optional specialization. Dated status/amendment preserves earlier decisions |
| P1 eliminate — done locally | `apps/api/adapters/context/native.py` | Second legacy category/content decoder and injected fixture validator existed in runtime. Use registered repository-shaped input only; fixture validation remains test-owned |
| P1 simplify — done locally | `apps/api/tests/fixtures/qh30_canonical_snapshot.json`, `test_native_context.py`, `test_canonical_graph_pipeline.py`, `scripts/verify_qh30_native.py` | Category/type compatibility mapping and duplicate embedded endpoints/event timestamps. Fixtures now use canonical binding, temporal columns and relation detail; specialized examples remain extension regressions |
| P1 eliminate — prepared only | `understanding_item_revisions.category`, `qh30_publish()`; new `0005_retire_legacy_category.py` | Null historical metadata is unused. Prepared forward-only migration removes only the null column and its publication check; preserve all other guards and locks. Non-null history blocks atomically |
| P1 simplify — done locally | `adapters/postgres/canonical.py`, `context/runtime.py`, `postgres/demo_identities.py`, `scripts/smoke_qh30_runtime.py` | Repository no longer writes/exports category; explicit schema compatibility includes 0004 and prepared 0005. No dynamic head acceptance; deployed image remains unchanged |
| P1 keep / historical | migrations `0001`–`0004`; `test_migrations.py`, `test_identity_migration.py`, `test_native_semantics_sql.py` | Applied immutable migration history, backfill/rollback/concurrency/shape/authorization regressions. Eleven seeds stay in 0003 for reproducibility; no retroactive edit or fixture rewrite of historical SQL tests |
| P1 keep historical references | `semantic_type_versions` eleven seeded records, existing `item_revision_types` | Smoke rows reference `qh.decision/1`. Never rewrite bindings or delete registry records, even unused immutable ones. Stop treating them as recommended default vocabulary; keep readable schemas/rules permanently |
| P1 keep functional | `context/native.py:NativeContextEngine.replace`, `incremental.py:ProjectionWorker.rebuild` | Full-generation publisher is used by actual incremental rebuild; deleting it breaks recovery. Keep bounded normal outbox path and explicit maintenance distinct |
| P2 keep narrowly / historical API | `native.py:reconcile`, `verify_readiness`, `CanonicalRepository.projection_lock`, full-snapshot pipeline tests | Standalone historical reconciler is not bound by runtime; retains lost-ack/corruption/readiness/concurrency regression evidence. May remove this separate interface later after relocating its unique tests to incremental rebuild; do not remove the shared publisher |
| P2 simplify later | Neo4j `category`, `semantic_type`, `schema_version`, `properties_json` graph fields | SQL-backed category value already means shape. Keep graph property aliases now: removing fingerprint inputs needs a projector/epoch rebuild transition, not an unannounced in-place deployment |
| P2 keep functional | `demo_identities.py` known 0002/0003 preflight; `tests/oidc_database.py` | Required to reproduce QH-5/old-schema identity tests; no closed semantic classification. Keep until those supported workflows explicitly retire |
| P2 keep functional | `pyproject.toml`, `requirements.lock`, `Dockerfile.dev` | No Graphiti, Surreal, Mistral/OpenAI SDK dependencies in native branch. Neo4j driver is under dev extra but current image installs that extra and runtime imports it; don't remove it. Moving it to runtime deps is packaging work if a lean image is introduced |
| P2 keep scaffold | `app/chat`, `app/projections`, `adapters/llm`, `services/mcp-server`, `packages/shared` | Approved boundaries, not abandoned adapters. No extraction/provider implementation to remove; MCP only offers scaffold transport |
| P2 keep / improve later | `.github/workflows/quality.yml`, `scripts/run_qh30_integration.py`, `qh30-integration.yml` | Disposable strict integration is useful; extended here with generic/migration regressions. Keep quality and real OIDC coverage distinct. Hosted run of this branch not authorized |
| P2 keep functional | `infra/docker/qh30-runtime.yml`, base Compose mounts/networks | Current image pin and backend-only override. New worktree is not mounted. Shared QH PostgreSQL/Neo4j/volumes/network, frontend/MCP/IdP must remain intact |
| P3 archive later | `/home/ubuntu/qh` Graphiti checkout/PR #1; old backend images, six historical Neo4j nodes | Not native dependencies; checkout still supplies other live mounts, shared Git and `.env`. Keep branch/PR/evidence; image cleanup needs separate approval. No native branch Graphiti adapter to delete |
| P3 archive/stop later | `/tmp/qh-surrealdb/spike`, three `qh-surreal-spike-*` containers and dedicated network/volumes | Isolated interrupted experiment, absent from native manifests/locks. Existing archival/dependency plan remains valid; don't stop/delete. Shared image layers are not additive reclaimable space |
| P3 historical evidence | `docs/verification-*`, QH-4 ADR/model review, older QH-30 sections and scripts | Preserve dated outcomes/commands; label supersession instead of changing old experiments into current evidence. No mass deletion of migration/security tests |

No application dependency or service removal is justified merely by a Graphiti or
SurrealDB keyword in a historical report. No resource was stopped, deleted or pruned.

## Prepared migration and deployment boundary

`0005_retire_legacy_category` follows immutable 0004. It takes a table lock, refuses
any non-null category, replaces only `qh30_publish` to remove that obsolete check,
and drops the column without CASCADE. READ COMMITTED and item publication locks
remain; deferred schema/shape/evidence/rules, immutability, endpoints, confirmed-current
and outbox triggers remain unchanged. No data/registry/binding/provenance update,
trigger disabling or extra archival table is used. Existing 0004 rows with null
metadata and all historical registered bindings remain readable/replayable.

If a non-null category exists, **stop**: retain column/data and design an explicit
preservation mapping with owner approval. Do not use a trigger bypass, rename the
field out of sight, or erase historical registry definitions. The migration does
not insert experimental generic types or restrict optional specialized types.
Exactly three registry rows on an already migrated database would require deleting
history; that is neither necessary nor authorized.

Before any future deployment: approve defaults/schema and 0005 separately; review
an immutable new image and its new worktree mounts, inventory actual 0004 content,
pause writers, take the appropriate backup for the data then present, run explicit
`alembic upgrade 0005_retire_legacy_category`, inspect guards/state/evidence, deploy
the new compatible backend, and smoke generic plus old-binding reads/replay/restart.
Never start fd50 against 0005: its writer references category and runtime preflight
requires 0004. Keep it on the current 0004 until this separate transition is approved.
A failure stops writes for diagnosis/forward repair; no destructive downgrade/restore.
`make migrate` now resolves to this candidate head and remains unauthorized on QH.

## First QH-8 increment: proposed extraction contract

This supersedes the specialized-default proposal retained at the end of
[QH-30 planning](qh-30-plan.md). Read QH-8, QH-10 and QH-30 via Atlassian MCP on
2026-10-15; their current wording still associates meanings with registered types.
The owner's newer instruction changes that proposed acceptance, not Jira itself.

1. Import one synthetic conversation with three identifiable excerpts/turns in a
   single Context Space. Persist original representation, stable revision IDs and
   origin locators before extraction. Three domains may coexist in the same space.
2. Use a provider-neutral internal extractor returning one JSON envelope:
   `items: [{local_id, shape, text, descriptors?, properties?, evidence, relation?, temporal?}]`.
   `shape` is item/entity/relation only; descriptors are optional free strings.
   Evidence entries contain exact source revision, zero-based half-open Unicode
   code-point offsets and literal quote. Relations name local endpoints plus a
   nonempty predicate; the resolver assigns stable IDs and exact revision anchors.
   Temporal assertions carry source support/precision; unsupported bounds stay null.
3. The application maps shapes to trusted, explicitly provisioned generic profiles;
   the LLM cannot register a type or supply owner, authorization, validation actor,
   current pointer or confirmation. Validate output envelope, known source/scope,
   unique local refs, exact quote/span equality and endpoint completeness. Persist
   citation locators as validated content and exact source FK provenance, requiring
   agreement. Reject unsupported fields/claims that conflict with canonical metadata.
   Matching text proves a locator, not entailment; controlled semantic assertions
   remain proposed and can be checked against the demo's human expectations.
4. Commit the accepted proposal batch atomically via CanonicalRepository/outbox;
   the existing runtime worker and authorized engine perform projection/retrieval.
   No SQL transaction spans provider work. Invalid output preserves the source and
   publishes no partial item batch. Local checkpoints permit idempotent offline replay.
5. Demonstrate decision, hypothesis and open-question **meanings**, all with generic
   item binding; include a fourth novel meaning without another type registration.
   Retrieve by controlled text, hydrate canonical references, optionally select
   descriptor data and display proposed state/evidence. Do not promise natural-
   language classification, exhaustive semantic recall or new public REST/MCP DTOs.
6. Implement fake/replay provider first using the existing SDK-free LLMProvider
   boundary with application validation and provider decoding in adapters. No
   public port change is implicit. One later real structured-output experiment
   requires provider/model/endpoint, request/output caps, estimated cost and explicit
   disclosure/call authorization; no embeddings, automatic retry or CI paid calls.

Acceptance: three excerpts; three intended meanings plus novel meaning persisted
with generic profiles and exact evidence; two interchangeable fake providers;
malformed output/missing/foreign evidence or endpoints fails atomically; AI items
remain proposed with no current-pointer movement; owner/mixed-scope denial precedes
disclosure; readiness/pending behaves explicitly; actual backend restart and graph
rebuild recover without extractor invocation; direct authorized SQL reads remain
possible during graph outage. Limited qh-schema-1 profile is not full JSON Schema.

Dependencies: native 0004 infra is already deployed; generic profile decision and
trusted provisioning must be approved before QH-8 uses them. 0005 is independently
gated **not a technical prerequisite**: generic profiles work on 0004. Public write/
provider-disclosure policy is still unresolved; first demo must be explicitly
owner-authorized internal work, not READ_CONTEXT being promoted to write/send.
QH-9/QH-10 are later public flows; QH-31 original-byte storage, Domain Packs,
advanced reconciliation, semantic/vector search and human approval UI remain outside.

Jira-ready changes, **not posted**: QH-30 record actual cutover/hosted 178-test
checkpoint and remaining capabilities, plus proposed cleanup/defaults; QH-8 replace
mandatory database categories/types with demonstration meanings and generic profiles,
retain three excerpts/proposals/evidence/restart/multidomain acceptance and reestimate;
QH-10 distinguish meaning/optional descriptors from registry types and specify future
selection/recall/public DTO contract without weakening scope/state guards; QH-9
review public write/disclosure policy separately. QH-31 and historical QH-7 remain
unchanged; preserve linked decision/evidence history. No status changes are inferred.

## Verification record

PASS: strict integration entry point **194 tests, zero skips**, 200.85 s, using
real dedicated PostgreSQL/Neo4j. This includes 15 new generic/migration cases and
runtime restart/retry tests parameterized on 0004 and prepared 0005. After refining
the foreign-anchor regression to isolate endpoint failure from provenance failure,
its two schema variants passed again (2 passed, 13 deselected). Test counts are not
summed. Earlier targeted generic/runtime run: 19 passed.

PASS: fixture probe `prepare`, `check`, `rebuild-after-loss`; no database container
restart in this additional probe. PASS: Ruff, Git whitespace and staged private-
file/credential guards; 50 local Markdown links/anchors resolved. Mermaid diagrams
were unchanged. No hosted CI execution or new image build/deployment was performed.
A pre-existing Starlette/AnyIO deprecation warning remains non-blocking.

Reproduce from this worktree (dedicated credentials stay in ignored local files):

```bash
sudo -n docker run --rm --network qh30-native-test \
  --env-file /tmp/qh30-postgres-test.env --env-file /tmp/qh30-native-test.env \
  --mount type=bind,src=/home/ubuntu/qh-worktrees/qh-semantic-foundation,dst=/workspace,readonly \
  -w /workspace/apps/api --entrypoint python qh30-runtime-ci-local-integration:latest \
  -u /workspace/scripts/run_qh30_integration.py
```

The fixture probe uses the same graph env/network/mount plus
`PYTHONPATH=/workspace/apps/api`, running `scripts/verify_qh30_native.py --phase`
with each of the three phases above. Its new registered-row probe namespace does
not reuse the old category-fixture generation. Required CI configuration still
fails explicitly for missing credentials/opt-ins or skipped/empty collection.

Local implementation commits:

- `f85b31c` — registered-row projector/repository exports, fixture/loader cleanup
  and fixture restart probe; verified by the full strict suite and three probe phases.
- `5c8cd44` — guarded 0005, 0004/0005 runtime compatibility and generic-profile
  regressions wired into strict CI; verified by the strict suite, targeted refined
  anchor regression, Ruff and staged credential guard.
- Documentation unit — this proposal, functional contract, dated ADR amendment,
  onboarding and agent instructions; validated links and staged credential guard.

Final read-only VPS checks: schema still **0004_projection_outbox**, two item
revisions, two source revisions, zero non-ready outbox intents; backend healthy
on the same fd50 image, with no mount from this isolated worktree. The original
QH-30 checkout is clean and still preserves local `42a20c7`. All changes occur only
in this separate checkout or test-created disposable databases/graph namespaces.
Historical 178-test hosted evidence is for fd50/eeadeef, not this branch.

Pending acceptance: choose the generic default profile names/schema and QH-8
extraction/query semantics; authorize any future push/hosted run independently;
review and authorize a new image plus persistent 0005 separately. Generic QH-8
proof can start on existing 0004 after profile/work authorization, without forcing
that cleanup migration. Surreal shutdown/archival, PR merge, Jira updates and paid
provider experiments remain separately gated.
