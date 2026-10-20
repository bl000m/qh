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
