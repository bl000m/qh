# QH-51 — UUM map: responsive layout correction

Owner-reported blocking visual regression on6d8f2f2; frontend-only correction,
22 October2026. PR23 stays open. No provider, schema, profile, identity, budget or
ledger changes. [Acceptance and executed checks](../../qh-51-uum-map-layout.md).

These are actual Chromium/Playwright screenshots of the production React Chat,
ContextMap, Orb asset and stylesheet. Only the API boundary is simulated with an
empty Space in `apps/web/tests/fixtures/uum-layout.html`. No VPS identity, private
content, token or canonical data is published. Separate actual-VPS smoke evidence
is retained privately and identified in the report.

| Scenario | Screenshot | Observed geometry |
| --- | --- | --- |
| Original320px defect | [Before320](before-320.png) | Card/orb overlap, clipped labels, hidden icons: FAIL |
| Original desktop defect | [Before desktop](before-desktop.png) | Internal word splitting, intersecting rows: FAIL |
| 320px | [Corrected320](uum-320.png) | PASS; full-width flow cards, orb above |
| 375px | [Corrected375](uum-375.png) | PASS |
| 768px | [Corrected768](uum-768.png) | PASS; tablet empty-Space columns collapse correctly |
| Desktop1672px, map beside chat | [Full composition](uum-desktop-with-chat.png), [map](uum-1672.png) | PASS; two card columns, orb above |
| Fullscreen1672px | [Fullscreen](uum-fullscreen.png) | PASS; three rows, left/right around central orb |
| Text200%,320px | [320 enlarged](uum-320-text200.png) | PASS; actual label/status/control font doubling |
| Text200%,375px | [375 enlarged](uum-375-text200.png) | PASS |
| Text200%,768px | [768 enlarged](uum-768-text200.png) | PASS |
| Text200%,desktop | [Desktop enlarged](uum-1672-text200.png) | PASS |
| Text200%,fullscreen | [Fullscreen enlarged](uum-fullscreen-text200.png) | PASS; reflows to orb above two columns |
| Zoom200%,desktop | [Zoom reflow](uum-desktop-zoom200.png) | PASS; CSS zoom simulation in addition to text-only enlargement |

[Recorded bounding boxes and text checks](geometry.json):14 snapshots across12 new
tests (the loading/unavailable/populated case records three snapshots). Every
snapshot has an empty `errors` array. Checks include card/card and card/orb
intersections, containment, horizontal overflow, unclipped labels/status, one
rectangle per unbroken word, visible icons/chevrons, and exact six French labels.
Normal/200% cases activate every node by mouse, Enter and Space; counters verify
actual repeated callback invocation and Tab checks preserve DOM order.

Final targeted command (network-none container, production src/tests readonly):
`npm run test --workspace apps/web -- uum-layout.spec.ts layout.spec.ts presentation.spec.ts`.
**19 PASS**,29.4s, zero retries:12 new layout cases and7 retained checks matched by
the filename patterns, including the composer/source dialog and tab/draft behavior.
TypeScript frontend/tests and production Vite build PASS. The first diagnosis run
and intermediate5 PASS/5 FAIL are retained; they were corrected, not relabelled PASS.
