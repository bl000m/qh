# QH-43 — approved original logo, compact bubble and login preview

2026-10-18 (Europe/Rome). [Decisions](../../qh-43-branding-checkpoint.md),
[PR #15](https://github.com/bl000m/qh/pull/15), OPEN / DRAFT. The logo comparison is
closed. This checkpoint shows the selected original identity, not new alternatives.
No merge, Jira write, paid inference, persistent data write or VPS IdP activation.

## Actual screenshots

The client captures use **isolated synthetic fixture data**, not the private VPS
owner dashboard. Keycloak captures are the actual inherited login form of the
**disposable test realm** with QH theme selected only there. They are not mock forms
or evidence of theme activation on the VPS. Locale is inherited from that test
realm (English in these login captures); the French QH client language is unchanged.
No locale/realm configuration was changed on the VPS.

| Screen | Desktop | Mobile | Logo / artwork |
| --- | --- | --- | --- |
| Welcome | [Desktop](screenshots/welcome-desktop.png) | [Mobile](screenshots/welcome-mobile.png) | Selected mark in header, compact original bubble by welcome text |
| Mon environnement | [Desktop](screenshots/environment-desktop.png) | [Mobile](screenshots/environment-mobile.png) | Same header mark, compact decorative bubble, real owned-Space cards |
| Context Space | [Desktop](screenshots/space-desktop.png) | [Mobile](screenshots/space-mobile.png) | Same header mark; no decorative hero ahead of question, consent and explorer |
| Keycloak preview — isolated only | [Desktop](screenshots/keycloak-desktop.png) | [Mobile](screenshots/keycloak-mobile.png) | Selected original mark, small bubble, inherited credential form |

The logo does not replace Space identity or epistemic state. Opening a Space
still sends no chat request and grants no proposal/provider consent. Existing mock
label, both canonical proposal warnings, source/context distinction and full
canonical browsing/history remain intact. No portrait/future mockup control appears.

## Technical assets and limits

[Asset manifest](asset-manifest.json) records source SHA, exact PDF page/crop,
resampling, byte sizes and derivative hashes. Selected frontend assets:

- [Logo](../../../apps/web/src/brand/qh-logo.png): 876×768, one faithfully rendered
  original mark; CSS resizes it, without rotations, tracing or a recreated SVG.
- [Bubble](../../../apps/web/src/brand/qh-bubble.png): original artwork downsampled
  proportionally to 400×300 with alpha; decorative only.
- [Favicon preview](../../../apps/web/src/brand/qh-icon.png): 64×64 whole-mark fit,
  no invented glyph. The theme ICO embeds the same PNG.

The supplied approval image is the visual reference; no local binary attachment
was available. The same original construction is cropped from the owner's supplied
presentation. It is not claimed byte-identical to the chat attachment. The original
light background remains; no heuristic color-keying or creative reconstruction.
No standalone vector master is fabricated or required to reopen the closed choice.

Theme logo/bubble files equal the frontend files byte-for-byte. Original decks,
mockups, portraits and the historical logo board stay private. Owner permission is
recorded for this QH preview/integration; no general artwork licence or final UX
approval is invented. [Theme source and activation boundary](../../../infra/keycloak/themes/qh/README.md).

## Verification and reproduction

| Executed check | Result / limits |
| --- | --- |
| Frontend lint, exact-image build/typecheck | PASS |
| Full isolated Chromium/contracts with QH theme | **48 passed, zero skips**, 3.6m |
| Existing real OIDC regression | **1 passed, 1 deselected**, 13.79s |
| Real graph outage | **3 passed**, 6.0s; includes overlapping contracts |
| SQL restore / graph rebuild / restored-ID browse | Canonical tables unchanged; **1 browser passed**, 18.7s |
| Corrected ready-state screenshot check | **1 targeted browser passed**, 18.8s; same app/assets, explicit owned-list readiness wait |
| Targeted harness's retained security/recovery gates | OIDC 1 PASS/1 deselected; outage 3 PASS; restore/reopen 1 PASS; counts overlap |
| Actual VPS Alice/Bob | Three retained Spaces × six proposed records in mock; six Bob 404s; zero key warnings; no new identity/seed |
| Selected mark/favicon/bubble | Actual image dimensions/load, whole-mark icon, scope of decorative placement and 320px/200% text PASS |
| Keycloak | Real inherited form, selected assets, responsive/200%-text and PKCE completion PASS in isolation; VPS activation NOT EXECUTED |
| Preservation | Fourteen tables, six container identities/configurations/start times, private .env, readonly realm, closed ledgers and seven original files unchanged |

The complete run used `qh43-browser:branding`; the targeted ready-state recheck used
`qh43-browser:branding-final`. Their **client executable and graphic asset bytes are
identical**, verified in results.json. The latter only waits for real owned-list
readiness before capturing images. Hosted CI uses the final tests with no filter.
Expected Starlette/AnyIO deprecation and blank-test-graph warnings are unchanged;
no test assertion or security gate was disabled to pass.

Executed receipts and source/image identities are in [results](results.json).
Use the existing harness, dedicated disposable credentials and a new output path:

```bash
python3 scripts/test_qh11_browser.py --sudo-docker \
  --backend-image qh43-api:checkpoint --browser-image qh43-browser:branding-final \
  --understanding --qh-login-theme --output /tmp/qh43-branding-fresh
python3 docs/evidence/qh43-branding-checkpoint-20261018/audit.py --check-current-assets
```

The explicit theme flag copies the public realm fixture, changes only `loginTheme`
in that disposable copy and mounts theme sources read-only on the disposable IdP.
The committed/root VPS import is unchanged. CI's full browser job uses the flag;
the separate OIDC job also retains unthemed checks. The optional `--browser-grep`
uses quoted native Playwright filtering for targeted artifact checks, is recorded
in the receipt, and does **not** suppress OIDC/outage/restore gates. CI uses no filter.

The initial new environment screenshot captured its asynchronous loading state.
The capture test now waits for the actual owned fixture link, without sleeps or
fabricated cards. Final environment/Space captures use that targeted recheck;
full branding regressions remain separate. Counts overlap and are never summed.

Live VPS verification uses retained synthetic Alice Spaces, canonical reads and
mock chat only: six proposed records each, exact sources and six Bob 404s. Private
ready-state live dashboard images remain under `.local-archive/qh43-branding-20261018/`.
No live credentials/private owner content enter this archive. Protected inventories
compare fourteen QH tables, six container IDs/configurations/start times, `.env`,
readonly realm, both closed ledgers and seven original reference hashes.

## Remaining owner gates

| Criterion | Classification / boundary |
| --- | --- |
| Selected identity and original compact artwork | Implemented; technical asset adaptation only, comparison closed |
| Environment, primary chat, full explorer, consent/provenance/warnings | Implemented; existing application contracts retained |
| Keyboard/mobile/enlarged text, real OIDC/Alice–Bob | Executed evidence and limits in results; no universal accessibility certification |
| Keycloak presentation | Source-only inherited theme and real isolated preview; **NOT activated on VPS** |
| Final UX/preview approval | Pending owner review of this checkpoint |
| Merge and Jira closure | Not authorized; PR stays draft, Jira unchanged |

No new Context Engine, public API, canonical persistence, Domain/sharing feature,
provider activation, model inference, forced auth/session change or automatic
confirmation. The next action is owner review of these screenshots; theme activation
requires distinct authorization. No other ticket is started.
