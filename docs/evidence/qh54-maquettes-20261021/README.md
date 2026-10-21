# QH-54 — Latest four Space maquettes

Actual Chromium captures use disposable PostgreSQL/Neo4j/Keycloak, generated
credentials and the normal product UI. No live demo test write or paid inference.
The original QH-54 understanding workspace/evidence remains retained separately.

| View | Desktop | Mobile |
| --- | --- | --- |
| Empty Space, actual two-card intake/discussion | [Empty](empty-desktop.png) | [Empty](empty-mobile.png) |
| Six actual personal declarations, containment map/chat | [Populated](populated-desktop.png) | [Populated](populated-mobile.png) |
| OIDC expiry, current unsent message + element | [Timeout](timeout-desktop.png) | [Timeout](timeout-mobile.png) |
| Authorized Mistral selection, real synthetic budget | [Models](models-desktop.png) | [Models](models-mobile.png) |

Also captured: [excluded budget Space](models-unavailable.png) and
[populated reflow at half desktop width](populated-zoom200.png). No screenshot
inserts a fictional answer, fabricated category or active unsupported control.

[Reference hashes](reference-catalog.json) identify the four current 1672×941
images. All historical PNGs and all24 PDF pages were also read before editing.
Four native-width side-by-side pairs (3344×981) remain in the protected archive;
[comparison hashes](comparisons.json) link each exact reference and capture.
Original incoming reference files are preserved, not republished or edited.

[Capture manifest](captures.json) records dimensions, SHA-256, exact test image IDs
and a source hash verified against both packaged frontend/browser images. Backend
code, dependencies and migrations are unchanged; its verified image is reused.
[Targeted results](targeted-results.txt) preserve executed public test outcomes.
The initial mixed development run had two corrected test failures; later successful
runs establish their corrected behavior. They are not silently counted as passing.

- Nine focused draft/origin/group/320px-layout/keyboard checks pass.
- Eighteen targeted navigation/chat/disclosure/revocation/owner-review checks pass.
- Seven scenarios passed in the initial mixed product run: persistence, correction,
  isolation, separate consent, temporary recovery and native descriptions.
- The corrected three-case run passes both maquette cases and real rotating OIDC,
  revoked refresh, fresh credentials when SSO is revoked, clear and logout.
- The delivered two-case run passes all four compositions, different-Space node
  labels, exact node-detail navigation, real model limits, mobile copy width,
  same-owner SSO recovery, clipboard equality and no automatic save/send.
- Every product run executes the dedicated real Keycloak rotation/revoke/logout
  protocol check. HTTP provider simulation is confined to isolated fixtures.

The current complete CI campaign belongs to the published PR22 HEAD, not the old
8191171 run. Its result and exact link are reported in the PR after completion.
No new full campaign is started merely to record that conclusion in documentation.

See [criterion-by-criterion report](../../qh-54-maquette-alignment.md) for exact
scope, differences, corrections, preservation and remaining owner review. No pixel
identity, human visual acceptance, paid-provider availability or semantic-quality
claim is made. PR22 remains unmerged; Jira status is unchanged.

## Reproduce the delivered focused cases

```sh
sudo -n docker build -f apps/web/Dockerfile.browser -t qh54-browser:review .
sudo -n docker build -f apps/web/Dockerfile.dev -t qh54-web:review .
python3 scripts/test_qh11_browser.py --sudo-docker \
  --backend-image qh53-api:review --browser-image qh54-browser:review \
  --frontend-image qh54-web:review --understanding --chat-sessions --product-mode \
  --browser-grep 'QH-54 maquettes' --focused-browser-only \
  --output /tmp/new-empty-qh54-maquette-evidence
```

This command creates separate temporary infrastructure and never reads root `.env`.
Full operational diagnostics, source receipts and preservation snapshots remain
private; only synthetic screenshots, public artifact hashes and test outcomes are
published. Concurrent runtime Space/organization changes are retained, not reset.

[Sanitized preservation verdict](preservation.json) contains comparison booleans
and schema identity only; no raw ledger, allowlist, credentials or canonical rows.
