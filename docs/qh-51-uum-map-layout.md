# QH-51 — Blocking UUM map readability correction

22 October2026. Owner-authorized frontend-only correction to the existing PR23,
branch `feat/QH-51-semantic-understanding`, sole checkout `/home/ubuntu/qh`.
The baseline is6d8f2f2. The UUM contract, API and persistence are unchanged.

## Diagnosis established in the browser

The production ContextMap and CSS were rendered in Chromium before editing.
At320px the middle cards intersected the orb; text was clipped and icons hidden.
At desktop the empty-Space sidebar gave the map about537px:36.5%-wide absolute
cards,54px icons and arrows left only a few characters per line. Content exceeded
fixed row spacing. `height:auto` on the map could not incorporate absolutely
positioned cards. `overflow-wrap:anywhere` then split full French words.

The200% regression exposed two additional inherited constraints: `.orb-art
.qh-bubble` was145% wide in the Space and the empty-Space parent kept two columns
on tablet. These were part of the same observed containment/readability failure.

## Final behavior

`ContextMap.tsx` places the original Orb first in DOM flow, followed by the six
original dimension buttons. CSS Grid reserves actual rows for their content:

- below30rem of map content width: orb above one full-width card column;
- from30rem: orb above two columns;
- from60rem: a reserved central orb column, with three card rows on each side.

Named container queries use actual map width and respond to root font enlargement.
At narrow widths, each card gives its label a full row beneath its icon/arrow;
labels/status wrap at word boundaries, without ellipsis or line clamp. Heights
follow content, so longer status text cannot cover adjacent cards.
The original image asset is unchanged; its rendered extent is bounded by the
reserved center. Tablet empty-Space composition now collapses as the populated
composition already did. Mobile keeps chat before the map.

Propositions / Compréhension courante are wrapping native toggle buttons with
`aria-pressed`, grouped under État de compréhension. This replaces a native select
whose single-line field could clip its long label at200%. Fullscreen, recenter,
add, explore, unclassified and dimension navigation keep their callbacks.
Full-screen content has vertical scrolling available; no horizontal hiding masks
overflow. Original fixed SVG paths were removed because they no longer represent
adaptive geometry; no fake connection is drawn. Six colors/icons are retained.

## Executed acceptance criteria

| Criterion | Classification | Result and limits |
| --- | --- | --- |
| Wide three-row layout, intermediate two columns, narrow full-width flow | Implemented and tested | PASS; actual container widths and a narrow desktop-hosted container |
| Original boule, six colors/icons and full French labels | Implemented and tested | PASS; loaded original image, visible icons, exact text and word rectangles |
| No card/card or card/orb intersection; cards inside map; no horizontal overflow | Implemented and tested | PASS across14 recorded geometries |
| 320/375/768/desktop-with-chat/fullscreen screenshots | Implemented and tested | PASS; real Chromium screenshots linked below |
| Text200%, including fullscreen, plus zoom200% reflow | Implemented and tested | PASS; genuine computed-font doubling and separate CSS zoom simulation |
| All six nodes mouse/keyboard reachable and activated | Implemented and tested | PASS; actual callback counters, Tab/Enter/Space; six actual-VPS member dialogs also opened by Enter |
| Both views, empty/loading/unavailable/populated status, recenter/fullscreen exit | Implemented and tested | PASS; empty state remains derived from API, not fabricated from layout |
| Composer/draft/source dialog regressions | Implemented and tested | PASS in retained targeted layout tests |
| Model/API/profiles/schema/auth/economic files unchanged | Verified | PASS; no implementation change;17 registered profiles/identity schema among14 byte-identical tables;39 protected file hashes and16 frozen backup hashes match |
| Every SQL row byte-identical during live development | Not fully satisfied | FAIL for owner_organization fingerprint only: two ordinary Space-open activity POSTs recorded while an existing client was connected during hot reload. Other14 tables exact; one owner-created Space and zero items preserved. No blind metadata restore |
| Physical Mac visual acceptance | Owner review pending | NOT TESTED by Codex; actual VPS Chromium smoke completed, owner decides acceptance |

[Comparative screenshots and geometry](evidence/qh51-uum-layout-20261022/README.md).
12 new layout tests plus retained checks: final targeted execution19 PASS,29.4s.
TypeScript source/tests PASS; production build PASS (70 modules).
Earlier diagnosis320/desktop:2 FAIL, reproduced intentionally. First correction:
5 PASS/5 FAIL; fixed inherited image overflow, tablet parent width and controls.
The final targeted result replaces these failures without erasing their evidence.

Actual-VPS smoke used real Alice OIDC and the already owner-created empty Space;
320/375/768/1672 and fullscreen geometries PASS, six real member dialogs reachable
by keyboard and empty, login/logout PASS. All QH non-GET requests from the smoke
were intercepted, including automatic opening activity. No Space/item was created,
no review was submitted and no provider was contacted. The private smoke retains
actual screenshots/results under `.local-archive/qh51-uum-layout-20261022/`.

A pre/post fingerprint check separately found two successful `/environment/spaces/
[ID]/open` POSTs at08:30:11/08:35:34UTC during source hot reload by a connected
client. The owner organization row remains version1, usage open_count5. Logs show
only those mutating requests; the changed table is consistent with the pre-existing
opening counter behavior, not a classification or a content edit. The before
checkpoint stores row hashes, not a full metadata copy, so unchanged organization
fields cannot independently be proven byte-for-byte. This exception is explicit;
no restoration of owner activity is attempted. P3 suggested follow-up: ensure
hot reload does not duplicate opening activity. No Jira issue/status is written.

## Publication and readiness

This correction remains in PR23; no merge is authorized. No PR19 change, migration,
profile registration, Keycloak/configuration/budget/ledger write or paid inference.
The runtime serves these frontend sources through its existing hot-reload binds;
no restart or container/image replacement was needed. The UI correction is ready
for review; the organization-activity exception and owner visual acceptance remain
explicit limits. QH-51 is not declared DONE.

All targeted tests precede one final candidate publication. That push launches the
existing required CI once; its actual results are recorded separately rather than
claiming the prior6d8f2f2 CI validates this new change.
