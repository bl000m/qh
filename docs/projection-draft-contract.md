# Projection Draft engine — QH-14 / QH-15 / QH-16

Owner-approved Demo B block 2, 2026-10-20. One increment, one branch and PR.
This implements the Product Contract's selective perimeter, not approval or sharing.

## Responsibilities established before implementation

`app/projections` owns immutable draft values, bounded exact revision scope, draft
CRUD and deterministic resolution. The existing formatting `ProjectionService`
remains unchanged. An injected asynchronous authorization predicate delegates only
to the existing `PolicyService` PROJECT_CONTEXT decision; it is a dependency bridge,
not another authorization system. That central policy permits only one active owned
Space. Recipient/category and purpose are descriptive draft restrictions, never a
grant to the recipient. Owner derives from the Space and cannot be supplied by a client.

PostgreSQL owns draft persistence through a projections-owned repository port.
Migration `0007_projection_drafts` is additive, following 0006; it is prepared and
tested in isolated databases only. No startup migration or persistent VPS write.
Entries reference canonical item/revision pairs in their one Space, with explicit
include/exclude effects. Exclusion wins. An empty draft may be saved, but resolution
denies an empty effective scope. Draft version is a compare-and-swap edit version,
not an immutable Approved Snapshot. Concurrent or stale edits fail closed.

The outbound resolution adapter uses the native graph's exact-revision verification
and readiness gates over canonically selected IDs, never graph traversal or search.
Only effective included revisions may be hydrated. A bounded canonical export
loads those revisions and minimal provenance identities; it does not load original
source bodies, other revisions, current-head contents or relation endpoints.
Relations require their exact endpoints explicitly in effective scope; no automatic
scope closure. Original source access remains a separate future authorization.

Resolution returns selected revision content/state, exact identity, semantic binding,
temporal metadata, in-scope relation anchors and provenance references. It omits
unselected current/predecessor pointers, validator identities, original source bodies
and origin metadata. Existing selected-revision citation excerpts are part of that
explicit revision's content, not permission to expose the whole source. No provider
port or chat session is connected to this engine. Future consumers must use this
filtered result and still obtain their own snapshot/disclosure authorization.

Policy precedes draft/private reads and is rechecked before returning. SQL repeats
the owner predicate under locks; missing/foreign draft or revision yields a uniform
denial. Version/expiry are rechecked after graph verification. New canonical revisions
cannot widen an existing draft: exact historical IDs remain pinned. Sharing approval
and epistemic confirmation remain independent; proposed revisions stay proposed.

## Verification boundary

Targeted unit, SQL integrity/atomicity and native graph/API isolation checks during
development; one complete hosted CI campaign on the final block. Reuse OIDC and
owner fixtures. No paid calls, persistent demo writes, Editor, guest link, approved
snapshot, natural-language selection, reconciliation or MCP. Technical readiness,
human review/merge and Jira closure remain distinct.

## Internal consumer contract (future Projection Editor)

Instantiate `ProjectionDraftService(repository=PostgresDraftRepository(url=...),
authorize=projection_authorizer(policy), resolver=NativeDraftResolver(...))` at the
application boundary. The resolver receives an owner-bound CanonicalRepository
factory and the existing native projector; it creates no worker or graph namespace.
No production route, runtime activation or public wire schema is added in this block.
HTTP exposure and runtime acceptance of schema 0007 require the later Editor contract.
The existing hosted Keycloak/OIDC campaign stays explicitly on its deployed 0006
baseline, rather than following Alembic `head` into a not-yet-enabled runtime schema.
No existing OIDC assertions are removed. New projection fixtures upgrade through
0007 and reuse signed OIDC verification/identity adapters on that isolated schema.

| Operation | Inputs and result |
| --- | --- |
| `create(subject, scope, spec)` | Authenticated QH subject, one Space, DraftSpec → saved version-1 ProjectionDraft |
| `read(subject, scope, draft_id)` | Owned Space and draft UUID → exact draft metadata and selection |
| `replace(subject, scope, draft_id, version, spec)` | Whole replacement at expected version → next version, atomically; no silent merge/retry |
| `resolve(subject, scope, draft_id, version, requested=None)` | Expected version plus optional exact subset of effective RevisionKeys → ResolvedDraft |

`DraftSpec` has recipient_kind (`subject` or `category`), opaque recipient label,
purpose, tuple of included RevisionKeys, tuple of excluded RevisionKeys and optional
timezone-aware expiry. Each RevisionKey has canonical item_id/revision_id UUIDs.
Both lists are bounded to 100 unique pairs. Identity/owner/state/version come from
the service/repository, never the spec. Unknown semantic descriptors do not infer scope.
An expired draft remains editable/readable by its owner but cannot resolve.

Resolution is all-or-nothing and sorts by item UUID then revision UUID. Explicit
subsets cannot expand scope. Empty effective/requested scope, invalid pairs, missing
draft, foreign owner or relation without explicitly included exact endpoints fails
uniformly. A stale edit version conflicts. Pending/missing/tampered graph or changed
readiness fails unavailable; no SQL fallback. Owner, version and expiry are rechecked
after graph work. The service has no provider port; the result alone is not a future
guest or provider-disclosure grant.

`ProjectionNotFound` and `ProjectionUnavailable` inherit the existing Core missing/
unavailable errors and can use existing inbound error mapping. ProjectionConflict
requires a future 409 mapping. This block tests those mappings with private test-only
routes; it does not add public endpoints. Automatic review rejected an attempted
public API/runtime expansion as outside explicit authorization; that patch was not
applied, and the internal engine increment proceeds within the approved boundary.

## Criterion mapping and executed evidence

| Ticket / acceptance | Classification and executed evidence |
| --- | --- |
| QH-14 minimal canonical draft, exact revision scope, owner, recipient/purpose, expiry/version/default deny | Implemented and tested — PASS: model/policy tests; real SQL CRUD/reopen/CAS, invalid pair/space and FK/identity constraints; no approved snapshot/share table |
| QH-15 only included authorized revisions, exclusions before retrieval/disclosure | Implemented and tested — PASS: native exact graph verification, minimal source identities, spy proves only included revision hydrated; direct excluded/unknown IDs denied before content load; extra/foreign adapter output rejected |
| QH-16 isolation and negative policy cases | Implemented and tested — PASS: Alice/Bob signed OIDC, same missing/denied HTTP 404 through existing mapper on private test-only route; no fake-provider request on denial, allowed payload excludes private canaries |
| Revision changes after creation | Implemented and tested — PASS: new proposed/confirmed revision plus new current pointer and graph rebuild still return only pinned original revision; future revision ID denied |
| Graph expansion, pending/missing/tampered assertions | Implemented and tested — PASS: relation endpoints must be explicitly included before hydration; relations never widen plain-item scope; all unavailable graph cases fail closed |
| Inflight owner/draft/expiry/canonical change | Implemented and tested — PASS: no result after deactivation, CAS version edit, expiry or pending canonical publication |
| Additive migration preservation | Implemented and tested — PASS: original canonical snapshot and trigger definitions preserved after isolated 0006 → 0007 upgrade; no persistent VPS migration |
| Existing full CI, review and closure | Final hosted results recorded on the PR/Jira after publication. No merge of this block authorized; Jira status transitions are not inferred |

Executed locally in Docker, on a newly created internal-network test project with
tmpfs PostgreSQL/Neo4j, no ports or persistent volumes:

- QH-14: **71 PASS** unit/policy/boundary checks, then **6 PASS / 12.07 s** SQL
  CRUD/CAS/rollback cases. An initial harness-only missing POSTGRES_PORT was fixed;
  only the affected SQL cases were rerun.
- QH-15: **25 PASS / 30.16 s** engine/native checks; **57 PASS** affected model/
  architecture checks. Ruff PASS. Counts overlap, never sum them.
- QH-16 integration after the order-normalization correction: **122 PASS / 72.92 s**
  across `test_projection_drafts.py`, `test_projection_drafts_sql.py`,
  `test_projection_engine.py`, `test_projection_engine_pipeline.py`,
  `test_projection_isolation.py`, `test_owner_policy.py`, `test_architecture.py`,
  `test_identity_migration.py`, `test_ux_v2_architecture.py`.
- Additional final owner/foreign-space controls: **20 PASS / 9.41 s**, 17 unrelated
  cases deselected, using `-k 'owner_read_policy or valid_revision_in_other_space'`.
- Existing Ruff, actionlint, Git whitespace and sealed QH-33 v1/v2 audit PASS.
  No local frontend rebuild/full browser campaign: frontend/wire routes are unchanged;
  the final hosted workflow exercises the existing complete gates once.

The stricter write-result check exposed differing tuple order between input scope
and sorted SQL rows (six rejected positive cases). DraftSpec now normalizes both
lists as sorted sets of exact pairs; a regression proves order-independent equality.
No selection, policy, graph assertion, historical binding or sealed audit was relaxed.

Private preflight/test harness and protected inventories are retained under
`.local-archive/block2-20261020/`, never published. Reproduce isolated execution with
`infra/docker/qh30-integration.yml` in a dedicated project, generated test credentials
and the named pytest files; never use the persistent `qh` project for these tests.
