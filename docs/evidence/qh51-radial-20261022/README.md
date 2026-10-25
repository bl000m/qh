# QH51 — radial map and ordinary AI evidence

22 October2026. Implementation4fc2a81 +f947216, PR23 open/unmerged. All screenshots
here use synthetic isolated data. Real VPS response/screenshots remain private
because they contain the real Space identity; secret-free aggregate receipts are
included. No provider call occurs on opening this folder.

[Side-by-side comparison and overlay](comparison.html)

| Same Space,1600×956 | Actual Playwright screenshot |
| --- | --- |
| Empty | [desktop-empty.png](desktop-empty.png) |
| First literal item, still unclassified | [desktop-first-item.png](desktop-first-item.png) |
| Explicit QH46 primary assignment | [desktop-classified.png](desktop-classified.png) |
| Explicit confirmation/current view | [desktop-confirmed.png](desktop-confirmed.png) |

These four images come from one real OIDC/API/PostgreSQL/Neo4j lifecycle. The same
map/orb/six nodes/chat/composer boxes compare exactly across all steps; JSON files
record their measurements. Original draft and DOM nodes survive review. The first
item stays unclassified until human assignment. The displayed8 calls/USD0.20 is
an **isolated simulated ledger**, never a reset of the actual account's balance.

| Reference/responsive check | Capture |
| --- | --- |
|1600×956, exact desktop target resolution | [desktop-reference.png](desktop-reference.png) |
|390×1160, exact mobile target resolution | [mobile-390-target.png](mobile-390-target.png) |
|390px full page, complete functional chat | [mobile-390-full.png](mobile-390-full.png) |
|320px | [mobile-320.png](mobile-320.png) |
|1200px, radial map above chat | [intermediate-1200.png](intermediate-1200.png) |
|Fullscreen | [uum-fullscreen.png](uum-fullscreen.png) |
|Fullscreen with actual text doubled | [uum-fullscreen-text200.png](uum-fullscreen-text200.png) |
|Desktop zoom200% | [uum-desktop-zoom200.png](uum-desktop-zoom200.png) |

Additional uum-320/375/768/1672 images show normal/doubled text. Geometry checks
cover every card pair, orb intersections, bounds, horizontal overflow and whole
word ranges. All six nodes are activated by mouse and Enter/Space, with view and
fullscreen navigation. Mobile state text remains in accessible names with a
visual dot; decorative chevrons are hidden to reserve label width.

Executed:19 visual/geometry/menu cases (including assignment/Escape focus restoration and compact mobile ancestor navigation) plus5 changed transport/composer regressions.
The22-case run had21 PASS and a first desktop load timeout while a concurrent test
stack exhausted host memory; that single case passed serially (desktop-reference).
The native six-case run passed1600/1200/768/375/320 same-Space lifecycle and ordinary
AI in two new Spaces. Later desktop/chat-response geometry was rechecked after
removing legacy content-dependent conversation sizing. Confirmation waits at
most30 seconds for actual canonical projection, still asserting the correct state.

All required targetPNG/SVG and original QH-design2 references were read before
changes. No target was rewritten or passed off as a screenshot. Original bitmap
orb and real controls/statuses remain. Mobile chat is taller than the illustrative
mock to retain readable functional controls. No fictional conversation is added.
Owner visual acceptance remains pending; tests/CI do not assert it.

[smoke-accounting.json](smoke-accounting.json):1 real chat POST,515/38 tokens,
USD0.00010005, all4 historical entries preserved;3 calls/USD0.19750265 remain.
[official-pricing.json](official-pricing.json): pinned official page/hash and
USD0.15/0.60 per million, public fetch with no key/context.
[preservation-result.json](preservation-result.json): all15 SQL fingerprints,
.env/realm and infrastructure identities/images/mounts unchanged after the smoke.

No real UUM extraction was paid in this task; simulated canonical validation does
not establish real-model semantic quality. See [full report](../../qh-51-development-ai-runtime.md).
[sha256.json](sha256.json) seals captured images/geometry and aggregate receipts.
