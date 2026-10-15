# QH — semantic foundation after cutover

2026-10-15. Three generic profiles, open descriptors and authorized structured
selection approved by the owner. Deployment prepared in isolation; **not a deployed
model change**. Baseline `42a20c7`, preserved on QH-30 and inherited by
`refactor/QH-30-semantic-foundation` in a separate worktree. The live backend still
uses `fd50b1ba67061ea95285a2ffce122939524ab93f`, schema 0004 and the QH-30 mounts.
No persistent writes, container changes, historical-resource cleanup or remote
publication belong to this increment. Cutover evidence remains in
[QH-30](qh-30-plan.md#persistent-cutover-execution-and-read-only-historical-inventory).

## Recommendation and its limits

Use three generic registered profiles for **new** understanding, retaining the
versioned registry for optional justified extensions. The controlled default profiles are
`qh.generic.item/1`, `qh.generic.entity/1`, `qh.generic.relation/1`. The owner approved
the three-profile architecture, open descriptor contract and structured authorized
selection. Persistent provisioning/deployment still require separate authorization. This is three initial write profiles,
not a registry limited to exactly three records. `qh.entity/1` already exists:
reusing that immutable ID/version with a stricter schema conflicts and is rejected.

`item`, `entity`, `relation` select storage constraints. They do not describe all
meaning. A decision and a hypothesis can share item shape; a concept may need
entity identity; a relation can connect any shapes, including another relation.
An item identity cannot change shape across revisions. No domain discriminator,
mandatory semantic category, second enum or automatic type registration is needed.

Content profile: an object with nonempty `text`, optional `descriptors`, optional
`properties` object, and extensible additional properties. New meanings need no
registry row. Generic relation rules use `any_registered`; predicate and endpoints
remain authoritative relation columns, not copied JSON. Arbitrary extension-property
details are not automatically validated by this deliberately small envelope.

### Approved descriptor contract (implemented and tested in isolation)

```json
{
  "text": "The pilot could reduce waiting.",
  "descriptors": [
    {"value": "hypothesis", "certainty": "asserted"},
    {"value": "expected_effect", "certainty": "tentative"}
  ],
  "properties": {"explanation": "Tentative interpretation of the cited conversation"}
}
```

- `value` is any nonempty string, with exact, case-sensitive Unicode comparison.
  No closed vocabulary, domain enum, aliases, stemming or automatic normalization.
  Meaningful spelling is the caller/extractor's responsibility; whitespace is not
  trimmed silently. A new string such as `reversible_pause` requires no registration.
- An element may carry multiple assignments. Each object requires `value` and
  `certainty`; the latter is `asserted` or `tentative`. This enum describes certainty
  **of assigning that descriptor**, not truth, source reliability or human validation.
  A hypothesis descriptor can be asserted while its content remains hypothetical
  and its revision remains proposed. Duplicate assignments do not duplicate hits.
- Missing `descriptors` or `[]` means unclassified: no positive descriptor match,
  no category inferred from text. A missing certainty is rejected, not defaulted.
  Tentative assignments are excluded by default; explicit `include_tentative=True`
  includes them, preserving the assignment in hydrated canonical content.
- Provenance, temporal assertions, revision identity, validation/actor and ownership
  remain canonical metadata. A descriptor grants no access or confirmation.
- `semantic_profiles.py:CONTENT_SCHEMA` uses only qh-schema-1 keywords: object,
  array, string, properties, required, items, enum, minLength and additionalProperties.
  Assignment objects reject additional fields. Null/string-only assignments, empty
  values, unknown certainty or missing fields fail deferred SQL publication atomically.
  No uniqueItems/pattern/$ref or unsupported JSON Schema promises are made.

Decision, hypothesis, open_question and reversible_pause are fixture meanings,
all stored as `qh.generic.item/1`. Identical text with different assignments is
selected differently without text search. The earlier unpublished string-array
candidate is superseded by this explicit uncertainty contract. If any database
already published a different definition under these IDs/versions, provisioning
fails closed: retain it and review a distinct version; never replace its schema.

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

The VPS fd50 image still offers substring search only. This branch adds an
**internal** authorized selector, without changing ContextQuery, Core ports or
public REST/MCP DTOs:

```python
await runtime.context_for(owner).select_descriptors(
    subject_id=owner, context_ids=(space,), values=("decision", "intention"),
    include_tentative=False, limit=20, after_revision_id=None,
)
```

PolicyService authorizes before access. The repository applies an exact **any-of**
JSON predicate across the requested owned scopes, ordered by revision UUID with
keyset pagination (`after_revision_id` is the last returned revision ID). It
selects canonical IDs without a text candidate prerequisite. The engine checks
readiness, looks up those exact IDs in the existing Neo4j namespace, bulk-hydrates
and validates canonical metadata/evidence/fingerprints, then rechecks readiness.
Missing selected graph assertions, pending/error state or a concurrent commit fail
closed, including empty selections. Multiple matching descriptors yield one hit.
A page has 1–100 results; descriptor input has 1–100 nonempty string values. Hydrate
returned IDs through the repository to inspect content and assignment certainty.

This selects **declared annotation membership**, not inferred natural-language
meaning. It covers all historical revisions, not just selected/confirmed heads;
validation remains visible and is not implicitly filtered/promoted. Unclassified
or differently spelled equivalent assertions do not match. The SQL JSON predicate
can scan scoped rows; there is no indexed or advanced semantic performance claim.
No GIN/vector infrastructure, ontology or new public query contract is introduced.

## Prioritized debt inventory — closure matrix

Inspection covers tracked native code, instructions, manifests, scripts/workflows,
fixtures and documentation. Historical checkouts/resources are read only. Paths
below are relative to this worktree unless absolute.

The nineteen entries below are the existing audit, in the same order. This is a
closure check against its findings, not a new audit. `46eda1f` completes the
remaining standalone-reconciler removal; previous verified commits are retained.
“Prepared / authorization pending” means no further safe code deletion is outstanding.

| ID / priority | Existing element | Closure / commit | Reason or remaining boundary |
| --- | --- | --- | --- |
| A01 P0 | README, AGENTS, architecture, SQL notes, adapter notes | **Resolved** — `40832b6`, `8fd06bd`; documentation commit following `46eda1f` | Active environment is 0004/fd50 with native worker; separate 0005 branch is not deployed. No edits through live QH-30 mounts |
| A02 P0 | Product Contract, ADR 0003 | **Resolved** — `40832b6`, `8fd06bd`; documentation commit following `46eda1f` | Generic profiles, open descriptors and authorized selection approved; deployment is separate. Dated amendment preserves earlier decisions |
| A03 P1 | `context/native.py` legacy decoder / injected validator | **Resolved** — `f85b31c` | One registered PostgreSQL-shaped representation; no production category/content decoder or fixture validator |
| A04 P1 | Canonical fixtures, compatibility mapping, duplicate time/endpoints, fixture probe | **Resolved** — `f85b31c`, `46eda1f` | Fixtures use actual bindings/time/details. Obsolete fixture-only `scripts/verify_qh30_native.py` removed; real runtime smoke/restart/rebuild tests replace it. Specialized fixtures still test optional extensions |
| A05 P1 | Null legacy category and obsolete `qh30_publish` check | **Prepared; persistent authorization pending** — `5c8cd44` | 0005 removes only the null column/check. Non-null history aborts atomically; no canonical rewrite. VPS remains at 0004 |
| A06 P1 | Repository/writer, runtime and identity compatibility | **Resolved** — `f85b31c`, `5c8cd44`, `16d350e` | No category write/export; explicit 0004/0005 support and compatible smoke/OIDC helper. No dynamic-head acceptance or hidden fallback |
| A07 P1 | Migrations 0001–0004 and historical SQL/security tests | **Intentionally retained** — unchanged applied history | Required to reproduce upgrades, eleven historical seeds, rollback, immutable publication, shape, isolation and authorization. Not abandoned runtime code |
| A08 P1 | Historical registry definitions and referenced bindings | **Intentionally retained** — `16d350e` provisions separate generic IDs | Existing qh.decision/1 revisions remain readable and immutable. No default eleven-category vocabulary, registry deletion or rebinding |
| A09 P1 | `NativeContextEngine.replace`, full-generation publisher | **Intentionally retained** — recovery verified in `46eda1f` | Called by actual `ProjectionWorker.rebuild`; deleting it breaks reconstruction. Ordinary delivery remains affected-only |
| A10 P2 | Standalone `reconcile`, `verify_readiness`, `projection_lock`, old snapshot pipeline | **Resolved** — `46eda1f` | Removed separate API, advisory lock, O(n) read checks and unused scope-manifest writes. Unique lost-ack/failure/corruption/concurrency regressions now exercise incremental rebuild and worker |
| A11 P2 | Neo4j `category`/`semantic_type`/`schema_version`/`properties_json` aliases | **Intentionally retained** — `16d350e`, `46eda1f` remove unused manifest access | Active fingerprint inputs: category means structural shape, not the old eleven meanings. Removing aliases changes graph compatibility and needs a reviewed epoch/rebuild transition; no duplicate decoder remains |
| A12 P2 | Known 0002/0003 identity preflight | **Intentionally retained** — historical tests pinned | Needed by QH-5 and pre-0004 identity workflows; unrelated to semantic categorization |
| A13 P2 | Manifests, locks, Dockerfile dependencies | **Intentionally retained after verification** — no unnecessary dependency removal | Native branch has no Graphiti/Surreal/provider SDK dependency. Neo4j driver is used and installed by the current dev-extra image. A hypothetical lean-image packaging change is not audit debt |
| A14 P2 | Chat/projections/LLM/MCP/shared scaffolding | **Intentionally retained** — approved module contracts | Reserved for planned tickets, not abandoned adapters. No provider extraction implementation or obsolete service to remove |
| A15 P2 | Strict native integration CI, quality/OIDC checks | **Intentionally retained / extended** — `5c8cd44`, `16d350e`, `a1eba04`, `46eda1f` | Real disposable SQL/Neo4j and skip-failure guard remain; hosted execution requires publication authorization. Independent OIDC checks remain useful |
| A16 P2 | Runtime Compose, current mounts/networks | **Intentionally retained** — unchanged | Live fd50 backend and shared PostgreSQL/Neo4j/network/volumes, frontend/MCP/IdP remain operational. New worktree is not mounted |
| A17 P3 | Graphiti checkout, PR #1, images, six historical nodes | **Intentionally retained; resource retirement authorization pending** — existing cutover inventory | No native adapter dependency. Root checkout still supplies live shared mounts, Git and .env; preserve history/PR/nodes. Exclusive old images only eligible after separate approval |
| A18 P3 | SurrealDB three containers, network/volumes and spike checkout | **Archival/stop prepared; authorization pending** — existing post-cutover inventory/plan | No active QH dependency; no native manifest reference. Preserve until separately authorized archive/restore rehearsal and stop. No fresh resource audit or shutdown; [existing archive/stop plan](qh-30-plan.md#surrealdb-archive-and-stop-plan--prepared-not-executed) |
| A19 P3 | Dated reports, ADRs and old verification commands/scripts | **Intentionally retained; obsolete executable probe removed** — `40832b6`, `8fd06bd`, `46eda1f` | Keep historical evidence and migration/security reproducibility. Removed operational fixture probe survives in Git; dated commands below are historical evidence, not current instructions |

There is no further safe deletion outstanding in this inventory. Residual actions
are persistent 0005/provisioning/deployment, a graph-format transition only if the
aliases are deliberately retired, publication/hosted CI and separately authorized
historical-resource archival/stop/removal. None is executed here. The prior deferral
of A10 is superseded by this closure; its original test results remain below.

No application dependency or service removal is justified merely by a Graphiti or
SurrealDB keyword in a historical report. No QH or historical resource was stopped,
deleted or pruned; execution used disposable test containers and test-owned data only.

## Audit closure verification

Code unit **46eda1f2788cddf6169f03471f702b6fa631ab2e**, local only: removes the
standalone snapshot reconciler, its full-scope query scans, repository advisory
projection lock, unused scope-manifest publication and fixture-only probe. One
bounded test drain helper replaces duplicates; the SQL/graph pipeline now uses
actual 0004 outbox delivery. Rebuild retains the shared atomic generation publisher.
No applied migration, canonical model/public port, runtime Compose or dependency
lock changed in this closure. No new compatibility layer was introduced.

The relocated regressions verify rollback after failed graph publication, SQL ack
loss after graph commit, concurrent rebuild serialization on scope state, partial
graph loss, tampered positive hits, changes during delivery, empty pending results,
exact replay, two-owner isolation and canonical SQL error causes. Older historical
full-snapshot test results below remain dated evidence, not a supported alternate
operational path. The independent pre-0004 startup rejection test remains explicit.

| Check | Result |
| --- | --- |
| Targeted changed paths | PASS **97 tests**, 273.85 s: canonical pipeline, outbox, native projection, generic semantics and runtime |
| Full strict integration entry point | PASS **261 tests, zero skips**, 323.00 s, via `scripts/run_qh30_integration.py` against dedicated PostgreSQL/Neo4j; includes migration/model, generic semantics, outbox/rebuild, runtime, Core contracts, OIDC crypto and owner-policy regressions |
| Exact candidate image, no source mounts | PASS **6 tests**, 87.85 s: runtime on 0004/0005, retained-ID smoke/restart, separate Uvicorn process recovery on 0005 and empty install/provisioning |
| Static/security | PASS Ruff, actionlint, Git whitespace and staged private-file/credential guard; 42 local Markdown links/anchors. Mermaid diagrams unchanged |
| Hosted CI / persistent activation | NOT EXECUTED — no push, deployment or persistent migration authorized |

Test counts above are separate runs, not additive totals.

The new candidate is `qh-semantic-candidate:46eda1f2788cddf6169f03471f702b6fa631ab2e`,
Docker-inspected image ID `sha256:74313b1c89d0440aa206d1aa7f80080e83edcce1ad84e2d7dd1cb019c6c2c4aa`,
OCI revision `46eda1f2788cddf6169f03471f702b6fa631ab2e`. Built from that exact
Git archive, without ignored files. It supersedes the earlier a1eba04 candidate;
the runbook below now pins this image. No image was deployed. Reproduce packaged
checks with the same command as the previous packaging record below, substituting
this full image tag. Use the existing strict-suite command for complete local CI.

The only observed test warning is the pre-existing Starlette/AnyIO deprecation;
no dependency change is justified by this warning in the present closure.
All nineteen audit entries are resolved, deliberately retained for the stated
functional/history reason, or prepared behind the listed authorization boundary.
QH-8 implementation is not started by closing this audit.

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
not provision profiles or restrict optional specialized types. Controlled provisioning
is an explicit, idempotent command separate from schema migration and application startup:
`python /workspace/scripts/provision_qh_semantics.py --register-generic-profiles`.
It requires known 0004/0005, atomically registers the three pinned definitions (or
accepts identical replay), and refuses conflicts. No model output triggers registration.
Exactly three registry rows on an already migrated database would require deleting
history; that is neither necessary nor authorized.

Before any future deployment: authorize 0005/provisioning separately; review
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
   `shape` is item/entity/relation only; descriptors use the optional open assignment
   objects defined above, including assignment certainty.
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
   Retrieve with the authorized descriptor selector (no text prerequisite), hydrate
   canonical references and display proposed state, assignment certainty and exact
   evidence. Also retain ordinary native text retrieval as a separate check. Do not promise natural-
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

Dependencies: native 0004 infra is already deployed and the three-profile direction
and the descriptor contract are approved. Authorize controlled provisioning
in the target environment before QH-8 uses it. 0005 is independently
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

## Previous isolated checkpoint (preserved evidence)

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

Historical reproduction only (the executable probe is removed by audit closure):
the fixture probe used the same graph env/network/mount plus
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

At that earlier checkpoint, pending acceptance included generic profile names/schema
and QH-8 extraction/query semantics; the later approval and completion below supersede
that planning gate, while persistent application remains prohibited. Still pending: authorize any future push/hosted run independently;
review and authorize a new image plus persistent 0005 separately. Generic QH-8
proof can start on existing 0004 after profile/work authorization, without forcing
that cleanup migration. Surreal shutdown/archival, PR merge, Jira updates and paid
provider experiments remain separately gated.


## Deployment 0004 → 0005 — prepared, NOT authorized/executed

The existing VPS image is **fd50b1ba67061ea95285a2ffce122939524ab93f**, with five
backend source mounts under `/home/ubuntu/qh-worktrees/qh-30`. Do not edit that
checkout or rely on a changed image tag while old source remains mounted. This
branch's schema/profile/query behavior is not deployed. Use a newly reviewed code
commit and its matching image plus source mounts together.

Preparation after explicit publication/image acceptance, before the maintenance
window (commands below are a runbook, not execution authorization):

```bash
set -euo pipefail
cd /home/ubuntu/qh-worktrees/qh-semantic-foundation
QH_SEM_DEPLOY_COMMIT=46eda1f2788cddf6169f03471f702b6fa631ab2e
export QH_NATIVE_BACKEND_IMAGE="qh-semantic-candidate:${QH_SEM_DEPLOY_COMMIT}"
export QH_NATIVE_GRAPH_NAMESPACE=qh-native
export QH_NATIVE_CONTEXT_ENABLED=true
# Require a clean tree and no executable/config drift after the reviewed code unit.
test -z "$(git status --porcelain)"
git diff --exit-code "$QH_SEM_DEPLOY_COMMIT" -- apps/api scripts tests infra .github \
  ":(exclude)**/*.md"
QH_SEM_COMPOSE=(sudo -n docker compose --env-file /home/ubuntu/qh/.env -p qh
  -f /home/ubuntu/qh-worktrees/qh-semantic-foundation/infra/docker/docker-compose.yml
  -f /home/ubuntu/qh-worktrees/qh-semantic-foundation/infra/docker/qh30-runtime.yml)
"${QH_SEM_COMPOSE[@]}" config --quiet
QH_SEM_IMAGE_ID=sha256:74313b1c89d0440aa206d1aa7f80080e83edcce1ad84e2d7dd1cb019c6c2c4aa
test "$(sudo -n docker image inspect "$QH_NATIVE_BACKEND_IMAGE" --format '{{.Id}}')" = "$QH_SEM_IMAGE_ID"
test "$(sudo -n docker image inspect "$QH_NATIVE_BACKEND_IMAGE" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = "$QH_SEM_DEPLOY_COMMIT"
```

The candidate was built from `git archive 46eda1f2788cddf6169f03471f702b6fa631ab2e`
piped to Docker build, with the revision label above; ignored files/credentials
never entered its build context. Reuse that exact tested image. If it is missing
or differs, stop and rebuild/retest/review a new image identity before activation;
do not silently substitute an equivalent-looking tag.

**No `--project-directory`.** Privately inspect resolved config (do not print all
credentials): five backend mounts must point into the new checkout; project `qh`,
namespace `qh-native`, networks `qh_app`/`qh_data` and existing DB/log/IdP volumes
must be identical to the live inventory. Snapshot other container IDs/mounts and
canonical/source/provenance/binding/current-pointer, registry and outbox/state
hashes/counts. Without `--profile oidc`, Compose omits the optional IdP service/volume
from its rendered model; the running Keycloak remains untouched by backend-only
commands and must be checked via its unchanged container inventory. Recheck 0004 and zero **non-null categories**, not an empty database:
there are already two retained smoke revisions. Stop on unexpected data/definitions
or config. Preserve the private cutover evidence and exact historical smoke IDs.

Maintenance sequence, only after explicit migration/deployment authorization:

1. Freeze all external/manual canonical writers. Stop **only the backend**, including
   its worker, and verify it is stopped. Do not run fd50 CLI writers on 0005. No
   public ingestion route exists yet, but manual processes must still be quiescent.
2. With writers stopped, make a restricted logical backup of actual 0004 content
   (`pg_dump -Fc` from qh-postgres-1, mode 600). Validate its archive listing; retain
   existing IDs and immutable records. Do not recreate any database/container/volume.
3. Recheck version, null-category precondition and before hashes; run explicit 0005
   using the **new** image/mounts via the one-off Alembic command below. No worker
   runs in this command. 0001–0004 are unchanged and are not reapplied manually.
4. Verify version 0005, column absence and qh30_publish without NEW.category;
   compare canonical, binding, evidence, outbox and per-scope state hashes exactly.
   Compare constraints/triggers (only the obsolete check inside the publication
   function changes), check all remain enabled/validated. No Neo4j epoch reset,
   rebuild, namespace change, historical registry deletion or outbox re-enqueue.
5. Run explicit generic-profile provisioning; verify three exact new definitions
   plus retained historical records. Persist only the three native configuration
   keys in the existing ignored mode-600 .env, especially the new image tag, with
   an atomic scoped update preserving all other credentials/settings. Avoid future
   generic Compose invocations accidentally selecting fd50 from the old .env.
6. Start only the new backend; verify image ID/commit, five mounts, worker startup,
   scope counters and old smoke retrieval. Other services/volumes remain untouched.

```bash
"${QH_SEM_COMPOSE[@]}" stop --timeout 40 backend
test "$(sudo -n docker inspect qh-backend-1 --format '{{.State.Running}}')" = false
"${QH_SEM_COMPOSE[@]}" run --rm --no-deps backend \
  alembic -c adapters/postgres/alembic.ini upgrade 0005_retire_legacy_category
"${QH_SEM_COMPOSE[@]}" run --rm --no-deps backend \
  alembic -c adapters/postgres/alembic.ini current
# Perform schema/data/outbox comparison before provisioning (which adds three types).
"${QH_SEM_COMPOSE[@]}" run --rm --no-deps backend \
  python /workspace/scripts/provision_qh_semantics.py --register-generic-profiles
# Persist the reviewed native configuration before enabling routine service management.
"${QH_SEM_COMPOSE[@]}" up -d --no-deps --no-build --wait --wait-timeout 120 backend
test "$(sudo -n docker inspect qh-backend-1 --format '{{.Image}}')" = "$QH_SEM_IMAGE_ID"
```

Post-deployment acceptance: use the new smoke CLI below. It creates only synthetic
structured data (no extraction/provider call): four meanings on generic item/1,
including a new descriptor, exact source revision evidence, proposed state, atomically
queued intents, actual backend worker processing, text and descriptor retrieval,
canonical hydration and foreign-subject denial. Its final JSON preserves scope,
owner, revision IDs and source revision IDs. Save that output privately; **retain
all data**. Then restart only backend and verify the same scope read-only using
its retained scope/owner values; require identical IDs and evidence without replay
or a second synthetic import. Also read the two historical fd50 smoke scopes with
their retained owners; those historical bindings remain readable.

```bash
"${QH_SEM_COMPOSE[@]}" exec -T backend \
  python /workspace/scripts/smoke_qh30_runtime.py --write-synthetic
# Set these from the saved synthetic JSON, without discarding that evidence.
QH_SEM_SMOKE_SCOPE=RETAINED_SCOPE_UUID
QH_SEM_SMOKE_OWNER=RETAINED_OWNER_UUID
"${QH_SEM_COMPOSE[@]}" restart --timeout 40 backend
# Wait for /health and actual native startup, then:
"${QH_SEM_COMPOSE[@]}" exec -T backend \
  python /workspace/scripts/smoke_qh30_runtime.py \
  --verify-scope "$QH_SEM_SMOKE_SCOPE" --owner-id "$QH_SEM_SMOKE_OWNER"
```

If 0005 fails: its transactional DDL must leave 0004/function/column intact; verify
before considering any resumption and keep the maintenance window until diagnosed.
If 0005 commits and provisioning/startup/smoke later fails: **keep writers stopped;
never restart fd50 against 0005**. Inspect redacted error classes, schema/version,
new image/mounts and durable intents. Retry identical provisioning or restart the
same compatible new image only after fixing the cause; leases/retries recover pending
work. Preserve all committed data and graph generations. A different repair/image
requires review. Do not downgrade, delete synthetic rows, clear the queue, change
epochs blindly or restore a backup over newer content. No destructive fallback is
part of this runbook. After transition, use only the reviewed new-worktree Compose invocation; root
`make up` or old worktree commands can select stale images/mounts and are not an
approved management path. Health alone is insufficient; failed/pending state, missing
IDs/evidence or image/mount drift blocks acceptance and reopening writers.

## Previous completion evidence — descriptor/runtime/CI preparation

Release/test unit: **a1eba04510bc6796d4799a71d267a981edf1a32e**, local only.
Implementation unit `16d350e` supplies controlled profiles/selection and 0005/OIDC
coverage; `a1eba04` adds actual separate-process restart recovery. The documentation
unit follows it and changes no runtime code. Generic profiles and the descriptor
selector are prepared, not active on QH. 0005 itself required no further SQL change:
its old-field removal and retained guards were verified by the cases below.

| Required verification | Executed evidence / result |
| --- | --- |
| Existing synthetic 0004 → 0005 | PASS `test_cleanup_preserves_historical_bindings_and_replay`: two preexisting proposed qh.decision/1 revisions/sources/spaces; unchanged canonical export, exact outbox/state JSON, constraint/trigger counts and Neo4j markers; old hits readable without rebuild. Strengthened case rerun on both schema variants: 2 passed |
| Non-null historical category | PASS `test_cleanup_refuses_nonnull_history_without_partial_ddl`: migration aborts, version remains 0004, column/value and original NEW.category function remain; no partial DDL |
| Empty install and controlled registration | PASS `test_empty_install_0005_then_controlled_profiles`: 0001→0005 on a fresh database, no category column, CLI adds exactly three profiles, no outbox events. CLI missing opt-in fails; exact replay works; conflicting immutable schemas fail |
| New generic data, metadata and isolation | PASS generic fixtures parameterized on 0004 and 0005: new writes, exact evidence, null/explicit occurrence, malformed payload/evidence/validation/validity rejected, same-owner cross-space anchors denied, immutable endpoints, shape changes rejected |
| Publication guards after cleanup | PASS targeted READ COMMITTED and shape-change regressions, both schemas: 4 passed. Item locks and deferred SQL guards remain installed; no historical migration edited |
| Outbox → Neo4j → authorized retrieval | PASS generic pipeline and descriptor selection on both schemas; ordinary text path retained. Pending and changed-during-read state fail even for empty descriptor results; missing graph revisions fail; policy denies before candidate access |
| Meaning without text | PASS identical neutral text carries decision/hypothesis/open_question/new-meaning descriptors; selection distinguishes exact assignments, supports multiple labels, excludes tentative/absent assignments by default, explicit tentative inclusion and UUID pagination work |
| Runtime restart/pending recovery | PASS `test_application_runtime_end_to_end_restart_and_error_recovery` on both schemas: failed projection remains durable, new application instance retries, new smoke writes generic profiles, a further runtime restart verifies the same scope/owner/item/source IDs read-only. Runtime module rerun after smoke enhancement: 4 passed. Additional actual Uvicorn process restart on 0005: first PID exits, a revision is committed while stopped, new PID drains its pending intent and retrieves the same ID/evidence; passed standalone and again in the final packaged image |
| OIDC/CI compatibility | PASS strict cryptographic OIDC/owner regressions; SQL identity lookup and authorized selection on 0004/0005; existing real Keycloak tests both pass against temporary schema 0005 (PKCE + HTTP application test, 2 passed). OIDC application snapshot preflight explicitly accepts 0005; historical 0002 migration test remains pinned |
| Strict CI entry point | PASS **256 passed, zero skips**, 241.40 s, including added OIDC/owner suites. Four later shape/isolation cases and strengthened migration/smoke tests were run separately as above; counts are not described as a single larger full-suite run. The additional process-restart test also passed separately and in the final packaged run. The strict entry point now collects those additions too |
| Packaging | PASS final candidate image from exact release commit, no bind mounts: **6 tests passed**, 83.47 s (runtime 0004/0005, retained-ID smoke after restart, separate Uvicorn processes recovering pending 0005 work, empty install/provisioning) |
| Lint/security | PASS Ruff, actionlint, Git whitespace and staged private-file/credential guard; 48 active-document links/anchors resolve. Hosted GitHub Actions not executed; no push authorized |

The real OIDC checks used temporary Keycloak 26.4.7, tmpfs PostgreSQL and a temporary
backend on the test network, with no published ports. They exercised the existing
`tests/oidc/test_keycloak.py` workflow cases (both tests executed, no skips), including
the helper's application-version preflight on 0005. Only these newly created test
services were shut down afterward; no QH or historical container was stopped.
Credentials stayed in mode-600 `/tmp/qh-foundation-oidc.env`, outside Git/logs.

No persistent migration, profile provisioning, backend replacement, push or hosted
workflow was performed in this task. The original 42a20c7, Draft PRs and historical
resources remain preserved. The owner subsequently approved the descriptor contract
(value/certainty, exact any-of selection over historical revisions) and three profiles.
Remaining gates are publication, 0005/provisioning and deployment authorization. Public latest/confirmed-only
selection, synonyms/ranking and write/provider-disclosure policy remain future
contract decisions; the first QH-8 proof uses expressly authorized internal work.
No real provider integration, embeddings or advanced semantic search is implemented.


Previous verified candidate image (superseded by the audit-closure image above, **never deployed**):
`qh-semantic-candidate:a1eba04510bc6796d4799a71d267a981edf1a32e`, image ID
`sha256:80feadad7d40ad34ef3cce259407380286ab0aba3d213d50fb1bba1c960b3445`, OCI
revision label `a1eba04510bc6796d4799a71d267a981edf1a32e`. Reproduction of packaging
checks, using dedicated test credentials and no source mount:

```bash
sudo -n docker run --rm --network qh30-native-test \
  --env-file /tmp/qh30-postgres-test.env --env-file /tmp/qh30-native-test.env \
  --entrypoint python qh-semantic-candidate:a1eba04510bc6796d4799a71d267a981edf1a32e \
  -u -m pytest -q -x --tb=short -p no:cacheprovider \
  tests/test_native_runtime.py \
  tests/test_generic_semantics.py::test_empty_install_0005_then_controlled_profiles
```

The three-profile direction is ready for QH-8 planning. Before its first persistent
use, authorize the provisioning/deployment window separately; the descriptor contract
is approved. QH-8 implementation begins with fake/replay and verified exact
citations; the current structured smoke is not an implemented extractor. A future
provider can replace the fake without changing profile IDs/content/state/provenance.
Only explicit human validation can create a confirmed revision through an authorized
workflow; neither descriptor certainty nor a successful extraction implies approval.


Preparation preflight also passed in read-only mode: the corrected Compose invocation
(no project-directory override) resolves the candidate image, five existing source
paths under the separate worktree, project qh, app/data networks, qh-native namespace
and shared DB volumes. Optional OIDC is not targeted. Final VPS check remains schema
0004, two item/source revisions, zero non-ready intents, healthy fd50 backend and
no mount from this worktree. 0001–0005 migration files, Core and runtime Compose
configuration were unchanged by this completion increment; 0005 stays prepared only.
