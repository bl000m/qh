# QH-43 — second UX iteration, 2026-10-18

Owner checkpoint on PR #15, **OPEN / DRAFT**, not full ticket readiness or DONE.
[Decisions and private logo gate](../../qh-43-visual-proposal.md).
Earlier [checkpoint artifacts](../qh43-ux-checkpoint-20261018/README.md) are unchanged.

## Comparable screenshots

These are real Chromium captures of the **same retained synthetic Projet pilote**,
initial empty dialogue, unchecked proposal choice, closed explorer (and the new
help disclosure where present), 1280 × 900
or 390 × 844 viewport. Full-page images can exceed viewport height. No branded
reference, owner dashboard, private account panel or generated answer is substituted.
Before: executable client at `28e8200`; after: source identified in `results.json`.

| View | Before | After |
| --- | --- | --- |
| Desktop | [Initial Space](screenshots/before-desktop.png) | [Initial Space](screenshots/after-desktop.png) |
| Mobile | [Initial Space](screenshots/before-mobile.png) | [Initial Space](screenshots/after-mobile.png) |
| Actual mock conversation | First checkpoint remains archived | [Desktop](screenshots/conversation-desktop.png), [mobile](screenshots/conversation-mobile.png) |
| Keyboard-only skip link | No permanent overlay intended | [Focused desktop state](screenshots/skip-focused-desktop.png) — deliberately visible on focus |

The textarea top moves from **741.59 to 571.92 CSS px desktop**, and **897.86 to
518.47 CSS px mobile**, measured after context availability loads, at scroll zero.
This is a layout comparison, not a model-quality, semantic-ranking or accessibility
certification score. Consent and applicable epistemic warnings remain visible.

## Execution and limits

Final source/test image: executable commit `6857ea2`, browser image
`sha256:f0563ff570cd711573bc9a74cfd3e468e78824ab1d19b2dc0c63aec0d0d1ee9d`.
All five changed executable/test files match its copied source byte-for-byte.

| Check | Executed result |
| --- | --- |
| TypeScript/lint/build | PASS: running frontend lint; exact final browser image build/typecheck |
| Isolated browser/contracts | **45 passed, zero skips**, 3.5m |
| Existing real OIDC regression | **1 passed, 1 deselected**, 13.18s |
| Real graph outage | **3 passed**, 7.4s (two overlap contract cases) |
| SQL restore / graph rebuild / reopen | All SQL tables identical; **1 browser passed**, 16.9s on restored IDs |
| Live retained Alice/Bob | Three Spaces × six proposed records; exact canonical evidence; six Bob 404s; zero React key warnings |
| Live keyboard / contrast / text reflow | Skip/main/composer focus PASS; textarea 19.57:1, placeholder 5.35:1; 320px/200% text, zero offscreen elements |
| Preservation | Fourteen tables, six container IDs/configurations/start times, `.env`, realm, closed ledgers and seven asset hashes unchanged |
| Final branding / theme | NOT IMPLEMENTED / NOT TESTED / NOT ACTIVATED; owner asset/rights gate |

A preceding run also passed 45 cases before the final wording/placeholder-contrast
refinement; it is not added to these totals. Existing Starlette/AnyIO deprecation
and expected blank-test-graph property warnings are unchanged and non-blocking.

Exact final commands, test-image IDs, observed results and preservation checks are
recorded in [results](results.json). Reproduce using the existing isolated harness:

```bash
python3 scripts/test_qh11_browser.py --sudo-docker \
  --backend-image qh43-api:checkpoint --browser-image qh43-browser:iteration2-final \
  --understanding --output /tmp/qh43-iteration2-fresh-evidence
python3 docs/evidence/qh43-ux-iteration2-20261018/audit.py
```

Use a fresh empty output directory and the recorded exact test image identities;
these are disposable test images, not deployed production artifacts. The harness
uses isolated PostgreSQL, Neo4j, real Keycloak and Chromium, no persistent QH volumes
or credentials. Build/typecheck, browser/contracts, OIDC, graph outage, restore and
reopen checks are distinct; overlapping counts must not be summed.

The browser regressions check explicit opt-in, canonical proposal warnings with
misleading provider prose, extractive mock labels, source/anchor/history access,
three-Space dialogue reset/late responses and Alice/Bob denial. New checks cover
secondary help, first-screen composer, actual pending-question rendering without a
fake answer, first keyboard stop/main-focus transfer, non-overlaid composer and
computed textarea/placeholder contrast (at least 4.5:1). Reflow is checked at 320px
and 200% text, including expanded exploration. These do not certify every assistive
technology, browser zoom combination or final branded palette.

Live checks use only retained synthetic Alice Spaces, canonical reads and mock
POSTs. All six elements per Space remain proposed; six Bob denials, no canonical
writes, zero paid calls. Read-only before/after inventories cover all fourteen QH
tables, six container identities/configurations/start times, private configuration,
realm, both closed ledgers and seven original asset hashes. No frontend/backend
restart or container/image replacement; existing HMR and ports are retained.

## Private asset review and remaining acceptance

The seven supplied files are confirmed by the owner; no ZIP is required. The
private board is `.local-archive/branding/logo-review-20261018/logo-board.html`
(and `logo-board.png`). L1–L8 are labelled source-region crops, with SHA-256, page,
coordinates and derivative hashes; no redraw/rotation or reconstructed master.
All 24 PDF pages have a private contact sheet. **No board, crop, full PDF/mockup
or original branding asset is published in this archive or the application.**

Owner logo selection and public logo/bubble rights remain pending. A standalone
master SVG and official variants/tokens/licences were not supplied. Approved visual
direction is compact original bubble, black/white, red and discreet iridescence;
application styling here remains neutral. Keycloak source/theme is NOT IMPLEMENTED,
NOT TESTED and NOT ACTIVATED. Final branding, final UX approval, reviewed merge and
explicit Jira closure remain unmet QH-43 criteria. Jira has not been changed.

Only frontend presentation/tests and decision/evidence documentation change. No
backend, Core, API, auth/session/policy, provider, database/schema, infrastructure,
Domain/sharing/ingestion capability, Mistral activation or ledger change.

## Current acceptance mapping

| QH-43 criterion | Classification / execution verdict | Remaining boundary |
| --- | --- | --- |
| Environment landing, reload, owned overview, Alice/Bob | Implemented and tested — PASS, existing browser/OIDC regressions and live three-Space checks | Owner final UX acceptance |
| Primary chat, explicit proposal choice, temporary reset, honest mock | Implemented and tested — PASS, mobile composer/pending question, canonical warnings and three-Space regressions | No semantic-comprehension claim |
| Expandable full understanding, exact evidence/history/anchors | Implemented and tested — PASS, keyboard exploration and canonical regressions | Final branded visual review |
| Keyboard, mobile, enlarged text, readable contrast | Implemented and tested for the stated checks — PASS | Not comprehensive accessibility certification; final assets/palette unverified |
| Original approved graphics with rights | Partially prepared: private traceable review board; no public asset implementation | Logo selection, authoritative master or explicit raster choice, public usage rights |
| Keycloak presentation | Not implemented / NOT TESTED / NOT ACTIVATED; existing OIDC preserved and tested | Source preparation after asset approval; activation separately authorized |
| Frontend/lint/build/browser/OIDC/CI | Executed results in results.json; latest hosted run must match PR HEAD | Green tests alone do not close QH-43 |
| Owner final review, merge and Jira closure | Not completed; PR remains OPEN / DRAFT, Jira unchanged | Explicit owner approval/authorization; no automatic merge or DONE |
