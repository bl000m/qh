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

At the initial implementation checkpoint, work was IN PROGRESS. No merge or Jira
closure is authorized; the final PR checks and owner review determine readiness.

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

The corrected browser campaign executed 64 checks successfully before the existing
OIDC verifier rejected the newly approved routes. Its exact path/method allowlist
is now extended to the five organization/review paths, with negative tests for an
unknown endpoint and an extra method. This changes no issuer, token, permission or
realm behavior. Local domain creation/multi-membership/order/editing and the chat
scroll/source/reflow scenarios have passed separately; omitted full gates in these
focused runs remain explicitly NOT TESTED until the required CI jobs complete.

## Later owner refinement: minimal hierarchy and native login

The existing branch and every prior commit were preserved, including the local OIDC
allowlist correction `984645f`. The later owner request replaces home-domain filtering
with dedicated stable-ID views, without another schema/backend change. Home contains
two compact shelves, actual recent/used order and discreet settings/all-Spaces links.
Domain views contain only associated Spaces and preselect their primary domain on
creation. Settings retain editable domains, all/unclassified collections and the
honest future-profile disclosure. Technical metadata is still available in secondary
collection/Space views, not exposed on the home cards.

Nested Space routes carry actual origin, verified against the owner's memberships.
Direct/resume opening never substitutes the primary domain for origin. Browser history,
renaming, removed/private domains and explicit domain reauthentication are regression
cases; ordinary login/plain Space reload retain the Mon environnement landing contract.
No canonical data is written for routing. Existing opening tracking remains owner scoped.

The login reference is the original private `QH-design 2/Interface de connexion QH minimaliste.png`.
The versioned theme uses the original logo/bubble, a compact rounded card, pill fields,
Continuer/Continue and true Keycloak FR/EN locale links. The ordinary login title is
removed; other native-flow headings remain. Two pinned 26.4.7 template overrides preserve
native authentication, session, error, recovery/registration and passkey branches.
No password is persisted to preserve drafts during language navigation. Browser flag
rendering follows the platform emoji font. Recovery/registration are shown only if the
realm already supports them; no illustrative registration promise is added.

The newer theme is **not activated on the VPS**: source and isolated evidence are distinct
from its existing QH-43 login. QH-49 remains open for durable image/mount delivery and
recreation/rollback checks before future activation; no new writable-layer installation
or persistent container/realm change was performed. See the [theme maintenance record](../infra/keycloak/themes/qh/README.md#qh-50-source-refinement--2026-10-19).

The first isolated hierarchy run passed. A second run exposed a real navigation race:
leaving settings immediately after saving a removed domain could fetch its old metadata
before the PUT finished. The client now awaits in-flight organization writes before
metadata/Space-list reads, with a delayed-write regression; it does not retry failed
writes or weaken server version checks. The theme's decorative submit arrow initially
entered its accessible name; an image background keeps the accessible button name exact.
Focused login FR/EN, invalid-password clearing, native show/hide, 200% reflow and logout
passed after correction. Final required CI still verifies the published exact HEAD.

Read-only preservation rechecked every original SQL table against the post-0006 inventory,
identities, demo Spaces, graph/outbox state and triggers. Container IDs/images/mounts/env,
private configuration, original art and historical ledgers match the pre-initiative record.
Only application StartedAt differs from that older record because frontend/backend were
already restarted at 05:14 UTC for the authorized branch transition, before this refinement;
all infrastructure StartedAt values match. The QH-45 ledger hash is unchanged, three calls.
The sealed QH-33 v1/v2 audit reproduces 74 IDs, with human review pending/null as before.


## Refinement reproduction

Focused source/build contracts: Docker `npm run typecheck`, `npm run build:web`,
then `playwright test tests/environment.spec.ts tests/contracts.spec.ts`: **8 PASS**,
including origin URL rejection and delayed organization-save ordering. The native
business/backend is unchanged by this refinement; earlier real SQL/graph evidence
is retained. Required CI is still run by the repository's unmodified PR workflow.

Private screenshots and machine output use the existing isolated harness:

```bash
python3 scripts/test_qh11_browser.py --sudo-docker \
  --backend-image qh50-api:review --browser-image qh50-browser:review \
  --frontend-image qh50-web:review --understanding --qh-login-theme --chat-sessions \
  --browser-grep 'source-only QH login theme|UX V2 hierarchical' \
  --focused-browser-only --output .local-archive/qh50-browser-hierarchy-theme-final
```

This focused command deliberately omits separate OIDC/outage/restore stages and
reports them NOT TESTED in that run; it never substitutes for the required full
GitHub Actions campaign. Login tests switch real Keycloak language links, submit
an invalid password, check clearing and native visibility, complete real PKCE login,
then logout. Hierarchy checks cover owner-only custom domains, multi-membership,
primary-domain preservation, explicit origins, recent/used sorting, deleted domains,
keyboard, desktop/mobile and direct-domain refresh through reauthentication.

The ordinary QH-43 dashboard branding regression was updated only where the later
owner decision replaced the large home hero with compact original-bubble shelves.
The original asset dimensions/ratio, Space isolation and warning/consent checks remain.
Screenshots remain private; the approved reference mockup is not published in Git.


Final refinement run: **2 browser tests PASS, 43.5 s**, using the exact packaged
frontend/backend without source mounts; the original theme is mounted read-only only
inside the test-owned Keycloak. All ten requested hierarchy/login desktop/mobile
captures are under `.local-archive/qh50-browser-hierarchy-theme-final/`. No live QH
access, published test ports or paid calls. Earlier targeted API-error/branding checks
also passed; counts are not summed across overlapping runs. The separate full suite
is required by the published PR workflow, whose current-head checks are authoritative.

| Done criterion | Classification / evidence and remaining gate |
| --- | --- |
| Three authorized increments, one branch/PR | Implemented/tested; distinct chat, organization, review and refinement commits, PR #17 |
| Real opening order, primary/multiple domains, stable hierarchy | Implemented/tested; 8 focused contracts, final browser hierarchy including Alice/Bob and removal |
| Chat/manual scroll, accessible answer-specific sources, guided review | Implemented/tested; retained focused browser/native evidence and required full PR regressions |
| Canonical states, citations, immutable review, policy/concurrency | Implemented/tested; 71 focused review/policy/composition checks, native CI guard |
| New login visual and real FR/EN interaction | Implemented/tested in isolation; final browser login/error/visibility/logout/reflow checks |
| VPS preservation and zero new inference | PASS read-only inventory/ledger/config audit; no new schema/runtime change in refinement |
| Required full current-head CI | Required publication gate; consult the final PR check results, not an earlier successful job |
| Durable new theme activation | Out of QH-50 scope; QH-49 and explicit runtime authorization; existing VPS login preserved |
| Owner review, merge and Jira closure | Pending, not authorized automatically; technical readiness is not DONE |

Residual limitations: no advanced semantic matching/ranking or persistent chat;
300-second OIDC sessions remain unchanged (QH-42). Historical creation stays compatible
and unclassified; restrictive profiles may reject review metadata atomically. Language
switching need not retain unsubmitted fields and never stores a password. The login
layout is responsive rather than the mockup's fixed poster dimensions; unsupported
registration is deliberately absent. Existing live theme persistence debt remains
QH-49; this PR neither hides it nor adds another ephemeral installation.

## Later three-maquette implementation

The owner's three newly approved maquettes supersede the preceding visual layouts.
See [the visual comparison and confirmation record](qh-50-maquette-fidelity.md) for
verified image mapping, functional assignment, typed-name deletion gate, mobile support
navigation, actual comparisons, intentional differences and execution results. Earlier
CI/captures remain historical evidence; current-head PR checks determine final readiness.
