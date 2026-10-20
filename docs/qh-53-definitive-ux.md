# QH-53 — Approved product maquettes

[QH-53](https://contextlab.atlassian.net/browse/QH-53) implements the owner's
2026-10-20 UX mandate in `/home/ubuntu/qh`, on `feat/QH-53-approved-ux`, from
main `797b274`. The owner explicitly authorized this increment while PR #19
remains open at `18bac2c`; that PR and its migration `0007` are untouched.
QH-52's activation is already verified; its personal Mac acceptance remains separate.

## Product and component contracts

All 15 supplied PNGs were inspected by content. The [reference catalogue](evidence/qh53-20261020/reference-catalog.json)
records dimensions, content and hashes. Six current 1672 × 941 references cover
empty Discussion, Éléments, Modèle, Conseils, context settings and global settings.
Earlier home/domain/brand/login references preserve the existing brand. Historical
projection/sharing concepts do not authorize implementing those features.

The only tab order is **Discussion → Éléments → Modèle → Conseils → Paramètres**.
Header, breadcrumb and original QH orb are shared. Model cards use the scale of
other tabs. Conversation, unsent text and provider consent remain mounted across
tabs; existing cleanup on changing Space, logout or invalid authorization remains.

React owns presentation. Existing QhApi, PolicyService, native graph retrieval,
QH-39 persistence and QH-46 review contracts remain in place. No backend, migration,
public API, provider budget/allowlist or identity/session contract changes.

- **Discussion:** original orb, two empty-state actions and composer in document
  flow. Ajouter un élément opens canonical literal intake for arbitrary text;
  Explorer focuses an editable question. Unavailable models get a brief explanation.
- **Consent:** sending without a valid grant opens exact-content authorization in
  an accessible modal. Internal preview performs no inference. Proposed inclusion
  is affirmative and separate from external-disclosure consent. Authorization does
  not send the pending question: another explicit Send is required. Snapshot/context
  changes still invalidate grants; revoke, expiry and accounting remain accessible.
- **Memory:** Mémoriser cette conversation appears only with selectable messages.
  The existing QH-39 dialog preserves exactly the selected segment, its source and
  unconfirmed proposals. Saving neither confirms truth nor preserves all history.
- **Éléments:** Sources, Compréhension and Détails du contexte retain browsing,
  provenance, history and explicit review. No question is needed to browse.
- **Modèle:** actual model, remaining dollars and requests from capabilities. After
  a response, status and capabilities are reread. No fictional model selector;
  the mock control requires both test mode and the explicit offline-test flag.
- **Conseils:** three editable question starters, with no automatic send or invented
  recommendation. Selecting one returns to Discussion and focuses the draft.
- **Settings:** existing rename, description and domain endpoints, with CAS and
  explicit conflict errors. Global settings contain Profil, Mes domaines,
  Préférences and Compte QH. Current French/light presentation is read-only;
  personal identifiers are secondary. Domain editing retains collection and
  unclassified-Space navigation.

The Product Contract presentation amendment documents these boundaries. No
Projection Editor, QH-51 runtime extraction or Block 3 functionality is introduced.

## Visual review

[Browser captures and visual review](evidence/qh53-20261020/README.md) provide the
synthetic screenshots and their hashes. Private side-by-side pairs preserve each
original reference on the left and actual Chromium UI on the right at native width.
Review corrected header spacing, CTA and card dimensions, the three settings cards,
global settings scale, small-screen overflow and composer placement.

Supported-feature differences are deliberate: the original QH orb is retained;
unsupported Delete, profile-name editing, notifications, language/theme switches
and model selection are absent. Modèle uses actual authorized isolated Projet
pilote data; the new budget Space remains unavailable rather than gaining a test
allowlist exception. Conseils describes question preparation rather than claiming
an automated synthesis. Mandatory tab order supersedes inconsistent reference tabs.

No separate supplied final image depicts a started conversation. Its capture is
checked against the explicit textual criterion: ordered messages and a memory
rectangle before the composer, only after selectable messages exist. Simulated
provider output establishes UI/protocol behavior, not live model semantic quality.

## Executed verification

Only targeted checks ran during development. The isolated browser runner uses
private networks, temporary PostgreSQL/Neo4j/Keycloak and packaged frontend/API
images; it never reads root `.env`, publishes ports or sends paid provider calls.
Evidence is retained under `.local-archive/qh53-ux-20261020/`.

- `foundation-targeted.log`: TypeScript and six layout/session checks PASS,
  including tab keys/draft retention, 320 px with 200% text, renewal/logout/8 h limits.
- `ui-regressions.log`: 25 of 29 targeted checks passed initially. Three presentation
  assertions/fixture dependencies and one unclassified-navigation regression were
  corrected. Canonical proposal warnings were also corrected to distinguish cited
  proposals from uncited proposals in a mixed snapshot.
- `corrected-regressions.log`: both canonical-warning checks and the maquette
  workflow PASS; the remaining unclassified-navigation failure was corrected in
  the actual domain editor before the final navigation run.
- `navigation-final.log`: both updated identity/Space and hierarchical domain
  workflows PASS. `product-final.log`: all four normal-product QH-53/QH-52 browser
  cases PASS, plus one real isolated Keycloak rotation/replay/revocation protocol
  check. TypeScript and packaged build PASS; exact captures are in the evidence README.
- The final hosted `QH quality` campaign is linked on the PR at its exact HEAD.
  It supplies the complete quality, native PostgreSQL–Neo4j, OIDC and browser gates.
  Local focused runs are not described as complete CI.

Ordinary failures corrected within scope: rename-modal opening raced rendering;
zoom exposed intrinsic flex overflow; mixed support produced an overbroad proposal
warning; global settings duplicated a heading; an existing navigation link had been
lost; model budget needed refreshing after a response. Relevant regressions cover
the corrected behavior. No architectural or persistent configuration workaround.

## Acceptance and closure

| Criterion | Classification / verdict | Evidence and limit |
| --- | --- | --- |
| Shared header, original orb, five tabs in mandatory order | Implemented and tested / PASS | Browser captures; roving arrow/Home/End focus checks |
| Empty Discussion and two working CTA | Implemented and tested / PASS | New empty Space; real intake; model unavailability; focusable composer |
| Started discussion and conditional memory rectangle | Implemented and tested / PASS | Simulated HTTP response; memory selection and sources; no whole-history claim |
| Sources, understanding, metadata and existing review | Implemented and tested / PASS | Native authorized retrieval; proposed/current/history; confirm/reject/correct regressions |
| Real model and budget, compact cards | Implemented and tested / PASS | Capabilities-backed values; budget reread after simulated generation |
| Three usable advice actions | Implemented and tested / PASS | Editable draft, return/focus, no automatic send |
| Context name, description and domains | Implemented and tested / PASS | Rename, direct description save, reload/reopen, CAS conflict and assignment |
| Four global sections, only supported controls | Implemented and tested / PASS | Actual domain edit/persistence, account details/logout; no fake switches |
| Necessary disclosure, proposed opt-in, revoke/accounting | Implemented and tested / PASS | Exact preview, distinct consent/send, selected revisions, invalidation, no retries/fallback |
| Desktop/mobile, 200%, keyboard, no composer overlap | Implemented and tested / PASS | Chromium 1672 × 941, 390 × 844, 320 px, CSS zoom 2 and short viewport; focus/scroll/drawer checks |
| Alice/Bob isolation and persistent canonical proposals | Implemented and tested / PASS | Real isolated identities and PostgreSQL; reopen and foreign-ID denials |
| No live inference, schema/config/allowlist/budget change | Implemented and tested / PASS | Hermetic runner; protected hashes/container identity checks; schema remains 0006 |
| Physical Mac/native password manager and OS keyboard | Implemented but unverified / NOT TESTED | Chromium viewport simulation does not prove physical-device acceptance |
| Live Mistral quality or new Space enablement | Out of scope / NOT TESTED | No paid call or allowlist extension authorized |
| Reviewed merge and Jira closure | Out of scope / NOT TESTED | Deliver READY FOR REVIEW; no automatic merge or Jira status transition |

Read-only preservation checks retain `.env`, readonly realm import, authorization
receipt, durable ledger, original container IDs/images/config/mounts and non-app
start times. At the early checkpoint 14 canonical tables matched the sealed QH-52
baseline; only owner opening activity differed. A later read-only checkpoint found
one additional live source/source revision and proposed item/revision, plus their
provenance/outbox and derived projection changes. Those were preserved, not
reverted or relabelled as unchanged. All automated write tests use disposable data.

PR #19 remains open/conflicting only in its existing documentation files. QH-46
status is unchanged. The next action on this task is owner visual/workflow review;
merge and Jira closure remain separate, explicitly controlled steps.
