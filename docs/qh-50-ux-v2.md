# QH-50 — UX V2 implementation record

2026-10-19. One owner-authorized initiative in three increments, one branch/PR
and one final complete campaign. QH-45 merged in `393a91daac9281d7f8918f5b6819f33d6ea91aba`
and Jira is DONE. No new inference is part of this work.

[ADR 0008](adr/0008-personal-organization-and-owner-review.md) records the explicitly
approved metadata and review contracts. QH-43 supplies the visual baseline;
QH-46 review is bounded by that approval; QH-47/48 advanced engines remain future.

## Verification plan

Increment 1: focused frontend contracts, typecheck/build and new browser assertions
for manual scroll, source-panel focus and compact session management.
Increment 2: immediate isolated SQL/API ownership, persistence and concurrency
checks for organization; no automatic demo memberships.
Increment 3: immediate isolated canonical review, replay, race, provenance,
current pointer and outbox tests. No persistent demo review writes.
At integration: one full native/SQL/graph/browser/OIDC/outage/restore campaign,
then repeat only failed or affected checks. Results will be recorded when executed.

Implementation is IN PROGRESS. No merge or Jira closure is authorized.

Increment 1 focused execution: Docker `npm run build:web` and `npm run typecheck`
PASS; two human-provenance/descriptor tests PASS. Browser interaction assertions
and the full campaign remain pending; these checks do not establish final readiness.

## Contract implementation and limits

`GET/PUT /environment` returns virtual defaults until the owner saves organization.
The sole new table is `owner_organization`; update version conflicts return 409.
Every membership is policy-checked and SQL-fenced. There are no demo associations
or automatic canonical Space creation. Transversal profile is an honest navigation
entry; a canonical personal profile/preference-sharing engine is not implemented.

`GET /context-spaces/{id}/review` is a bounded pending inbox. The existing proposed
and history selectors retain all retained revisions. Scoped revision review has
GET status and POST explicit operation, optimistic latest/current IDs and a UUID
operation key. Review receipts live in the new revision's `content.qh_review`;
confirmation/rejection preserve extraction origin, while correction is human and
proposed. Original citations/extraction remain historical lineage, not a claim
that an LLM produced the corrected text. All fields and source anchors remain
available under technical disclosure. A restrictive registered profile that
forbids receipt metadata rejects the whole operation; the application does not
weaken it or publish a partial review. A reviewed schema version would be needed
for such future profiles. All three demo profiles support the approved envelope.

Review resets the client chat and revokes its temporary grant: new canonical
understanding requires a new retrieval and any applicable disclosure consent.
The pinned QH-45 demo provider snapshot is never rewritten to accommodate changes.
Semantic contradiction, inferred supersession, false merge/split prevention and
advanced matching remain unimplemented QH-47 work, not implied by lineage labels.

Focused execution so far: 48 organization/API/architecture checks PASS; 71 review,
policy and composition checks PASS (includes 12 isolated SQL/graph review cases
across 0004/0005). Frontend build/typecheck and organization wire test PASS.
Counts overlap where suites share tests and are not a single full-run total.

## Resumption and owner clarification

Execution resumed without reset/clean/rebase: `91a48f2` (chat) and `1765495`
(organization) preserved; review changes were uncommitted. No test process or
migration was left running. VPS preflight still reported 0005, no organization
table and zero non-ready outbox rows. Earlier successful checks were reused.

The owner's later dashboard decision adds two horizontal shelves, primary domain
on new dashboard Spaces, explicit unclassified/all filters and genuine opening
activity. The same single metadata table stores server timestamp/count plus a
bounded event deduplication window. No conversation or content is recorded there.
`GET /environment/spaces` orders owned Spaces across bounded pages by real usage;
`POST /environment/spaces` creates with required primary domain atomically;
`POST /environment/spaces/{id}/open` records an authorized actual UI opening.
Legacy QH-9 API creation remains domain-neutral for compatibility. Existing demo
Spaces remain unclassified until their owner explicitly organizes them.

## Authorized VPS metadata migration

0006 was applied only after a protected full PostgreSQL dump was restored to a
new disposable test database and all original table row hashes matched. Restore
comparison normalizes PostgreSQL-generated internal FK trigger OID names; trigger
bodies remain equivalent. The migration adds the empty `owner_organization` table
and its FK triggers only. All original table hashes (except Alembic's version row),
identities, Spaces, projection state and pre-existing triggers remain unchanged.
Backup, restore inventory and exact before/after records are private mode-600 files
under `.local-archive/qh50-organization/`. No Understanding demo review or domain
assignment was performed. The first post-upgrade audit was corrected to account
for the expected new metadata FK triggers; no data discrepancy was concealed.

Local focused UI runs explicitly use `--focused-browser-only --browser-grep`.
This mode is refused in CI, reports omitted OIDC/outage/restore gates as NOT TESTED
and leaves default full CI acceptance unchanged. It supplies private screenshots
without adding external artifact uploads. A fixture preflight initially rejected
0006; both explicit provisioning helpers now recognize the additive metadata schema.
No provisioning command was run against the live VPS for this correction.

## Final integration gates

Focused browser work caught and corrected asynchronous checkbox rendering, StrictMode
modal cleanup, scroll-shelf accessible-label overflow, and a sticky composer that
could obscure mandatory controls at enlarged text sizes. The composer is persistent
only when its measured height fits; otherwise it stays in normal flow. The provider
selector is width-bounded. An isolated no-network 320px/200% layout regression passes.
Explicit opening activity reuses the authorized metadata read, without a duplicate
read or any conversation content. Pending inbox excludes obsolete older proposals.

Final acceptance is the single complete GitHub Actions campaign on this task PR:
quality, native integration (including organization/review), real OIDC, full browser,
real graph outage and disposable backup/restore. PR checks and its final report are
the authoritative execution evidence; until those jobs succeed, readiness is pending.
Private focused screenshots are under `.local-archive/qh50-browser-focused-*`.
No screenshot/raw evidence upload was added to CI; the default security gates remain.
QH-46/47/48 are not closed automatically; owner review and merge remain outstanding.

The first CI attempt identified two regressions: an unintended third positional
argument in the historical QH-8 harness migration call (mistakenly enabling SQL
output mode), and a changed frozen QH-33 architecture test. Both historical files
were restored byte-for-byte from the merged baseline. New boundaries are checked
in a separate test and composition uses typed inward-only application facets.
The focused simulated-429 test and 45 composition/boundary checks pass; the sealed
v1/v2 QH-33 audit passes without changing any stored fingerprint or attestation.

Recovery remains forward-only: do not drop owner metadata or stamp Alembic back
to 0005. A historic image-only rollback that rejects 0006 requires a reviewed
compatibility patch first. The current hot-reload runtime explicitly accepts the
additive version. Restoring the protected pre-upgrade backup is a separately
reviewed recovery operation, never an automatic way to discard later owner data.
