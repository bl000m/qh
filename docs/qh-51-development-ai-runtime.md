# QH51 — ordinary development AI and stable radial map,22 October2026

Implementation commits:4fc2a81 (ordinary AI/backend/contracts) andf947216 (radial UI/direct send/browser coverage),392b24a (menus/access contracts) andebdc1fe (compact mobile ancestor navigation).

Current task extends PR23 on feat/QH-51-semantic-understanding in the single
/home/ubuntu/qh checkout. The owner explicitly superseded per-session/snapshot UI
consent and economic gates for the development account. PR23 stays unmerged;
PR19, schema0006, profilesv3 and the post-reset data are preserved. No Jira write.

## Actual result and limits

Ordinary AI is active on the existing VPS app containers. The private receipt adds
only the exact existing owner's verified OIDC account for all its owned Spaces;
old grants remain historical. Envoyer directly calls the backend; there is no
activation, provider checkbox, preview approval or conversation grant. A separate
explicit Proposer avec Mistral action uses the same Understanding Engine and
produces proposed revisions. Human review and proposed inclusion stay independent.
See [the binding contract](qh-51-essai-ia.md).

One standalone real browser smoke used the actual Alice OIDC login and the real
backend/Mistral path. The existing owned Space had **zero confirmed-current
revisions**; no proposal or canonical content was sent. Opening-activity writes
were intercepted in that probe and all other application writes were blocked.
No live test Space or canonical revision was created. No further paid call was made.

Synthetic question:

> Pour un voyage fictif, suggère une seule question pour préciser mon objectif,
> sans inventer de fait personnel.

Unmodified Mistral response:

> Quel type d'expérience ou d'ambiance souhaitez-vous vivre lors de ce voyage fictif ?

HTTP200; exact model mistral-small-2603;0 supplied revisions/0 fabricated references;
1 provider POST;0 legacy consent requests; no popup. Usage515 input/38 output tokens,
accounted list-price cost **USD0.00010005**. This proves actual chat/model access at
execution time, not future quota or the semantic quality of UUM extraction. Real
UUM inference was not spent from the one-call authorization: its source/quote/
publication/review path was exercised with a simulated provider in isolated SQL/Neo4j.

The original QH45 ledger now has5 of8 calls; spentUSD0.00249735, remaining
**3 calls/USD0.19750265**, ceilingUSD0.20 unchanged. All four historical rows and
non-call fields compare equal. No QH51 experiment budget is reused. Absolute
expiry remains18 November2026,05:30 Europe/Rome (04:30UTC). No session3-call budget
applies to this development mode, and neither login, Space nor restart refills it.

## Layout evidence and visual review boundary

All three mandatory new target files were inspected before layout changes, along
with the original QH-design2 PNG references. Original orb bitmap, icons and six
colors remain. ContextMap uses intrinsic Grid and container width, with measured
SVG connectors to actual node/orb boxes. There are three rows around the central
orb when wide, a full-width map above chat at intermediate widths and readable
mobile columns/list. The graphic does not depend on the number/state of items.
Chat uses one Space key; review refreshes data without remounting the conversation.

[Evidence index](evidence/qh51-radial-20261022/README.md) contains actual Playwright
captures and geometry, including the **same Space** empty/first manual item/
explicit primary assignment/confirmation and view changes. Literal input stays
unclassified until human assignment; no keyword classification was introduced.

Compared with the target, the implemented app retains actual view/fullscreen/
keyboard/source controls, truthful node statuses and real provider availability;
it never adds the mock's fictional conversation. Mobile chat is taller to retain
readable suggestions, disclosure information and composer. The original raster
orb replaces the target's illustrative vector. These are explicit functional/
accessibility differences. Visual owner acceptance remains separate from passing
geometry, tests or CI; no claim of owner visual approval is made here.

## Executed checks

| Criterion | Classification / verdict | Evidence and limit |
| --- | --- | --- |
| Real authenticated Send without provider popup | Implemented and tested — PASS | One real browser smoke, exact model/response/usage, zero consent endpoints; existing empty-confirmed Space to preserve live data |
| New owned Spaces and switching without renewed consent | Implemented and tested — PASS in isolation | Real OIDC/API/SQL/Neo4j browser scenario creates two Spaces, sends and extracts, zero preview/activation/consent endpoints; repeated calls simulated |
| Global budget, identity and ownership | Implemented and tested — PASS |15 development unit cases,4 sequential residual calls, OIDC renewal/new login, Bob/foreign identity, empty context, missing key, private receipt revocation, pending/concurrent reservation, no reset |
| Insufficient ceiling before paid HTTP | Implemented and tested — PASS | HTTP402 with exact French message; call transport counter unchanged; simulated low USD/call ceiling and concurrent pending case |
| Exact UUM evidence, proposed-only, replay | Implemented and tested — PASS in isolation | Same Engine/QH32/QH46 and native SQL/graph tests; simulated invalid quote fails batch, replay makes no extra provider call |
| Genuine semantic quality on real Mistral | Not tested | One authorized paid call used for actual chat; no claim that schema conformance proves meaning quality |
| Responsive map, labels, collisions, keyboard, fullscreen,200% | Implemented and tested — PASS |19 targeted visual/geometry/menu cases; same-Space native lifecycle at1600/1200/768/375/320; source/box evidence in index |
| Canonical/identity/config preservation | Implemented and tested — PASS | All15 application SQL table fingerprints equal before/after real probe, .env/readonly realm bytes equal; all container IDs/images/mounts and infrastructure start times equal |
| PR merge and Jira closure | Out of scope | PR23 remains open; no merge/Jira mutation authorized |

Additional backend regression run:82 passed across UUM pipeline, ordinary AI,
legacy session HTTP and OIDC security. Later targeted ordinary/session API run:
30 passed (including exact route/method allowlists). Ruff and TypeScript lint passed. Final complete CI is run once on the
published candidate; its exact conclusion belongs to PR23 checks, not an inferred
PASS from local checks. No full local CI or paid inference during CI.

## Operations and rollback

Frontend/backend were deliberately stopped with guarded dev-stop while the auth
and layout changes were prepared, then restarted with guarded dev-up only. Images,
ports, mounts, schema, OIDC TTLs and Keycloak configuration did not change. No
migration0007, reset, seed, dependency replacement or infrastructure restart.

Private preparation, original/candidate receipt, verified account/hash, inventory,
actual response/screenshot, preservation fingerprints and rollback are retained in
.local-archive/qh51-map-target-20261022 (restricted permissions). They are not
published because they include real identity/context identifiers. The development
receipt was validated with network disabled before atomic installation.

To revoke/rollback availability, stop only apps with guarded dev-stop, atomically
restore the original private receipt, then guarded dev-up. Never restore the
ledger after a new call: all completed, failed and pending entries must remain.
Changing/removing the receipt invalidates in-flight/subsequent authorization.
No secret/identity/realm/image rollback is needed for this receipt-only change.

Autonomous corrections: replaced overlapping absolute cards; removed empty/
populated primary-layout branches and review-triggered Chat remount; closed the
mobile map menu after navigation and the domain menu after assignment with focus restored; removed legacy content-dependent conversation
sizing so the composer stays in the same flex region before/after a response.
The latest owner correction also removed the initially proposed activation/
consent system before operational activation. No such gate remains in ordinary
use. Historical consent contracts and their regression tests remain separate.

The compact mobile Space name opens the retained ancestor links; domain assignment
is available through Paramètres on narrow layouts. Header menus close and restore
focus after assignment or Escape. Model verification is shown as loading, not false
unavailability.

The GitHub integration previously returned HTTP403 for PR title/body updates.
No alternate write channel was attempted. [Exact manual metadata text](reviews/qh51-pr23-current-description.md)
is prepared; the existing historical PR title does not describe the final UUM scope.

Next action on this task: owner Mac/visual review of PR23 and the actual runtime.
No automatic merge or next-ticket work follows.
