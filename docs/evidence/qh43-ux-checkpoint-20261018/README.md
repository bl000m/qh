# QH-43 — first functional layout and asset-analysis checkpoint

2026-10-18. Executable source `20314d6197fed8d751af8802ec3a2d8bc74beadb`, PR #15.
[Proposal and limits](../../qh-43-visual-proposal.md). This archive contains
synthetic fixture screenshots and result summaries, **no original PDF/mockup/logo**.
The private branded composition is not an implemented product screenshot.

## Executed evidence

| Check | Actual result / boundary |
| --- | --- |
| TypeScript/lint/build | PASS: running frontend `npm run lint --workspace apps/web`; existing isolated harness runs `npm run build:web` and `npm run typecheck` before browser cases |
| Final isolated Chromium/contracts | **43 passed**, 3.1m; real SQL/Neo4j/Keycloak and mocked/extractive provider only |
| Existing real OIDC check | **1 passed**, 1 deselected, 12.74s; reuses `tests/oidc/test_keycloak.py` |
| Real isolated graph outage | **3 passed**, 6.2s; includes two overlapping chat contract cases |
| Restore/rebuild/reopen | SQL dump restore and graph rebuild preserve all canonical tables; **1 browser case passed**, 16.3s, on restored IDs |
| Real VPS Alice/Bob | Three retained demo Spaces, six proposed records each in mock context, exact sources/relations; six Bob 404s, no React key warning. No canonical writes or paid calls |
| Live enlarged text | 320px / 200% text reflow PASS, zero offscreen elements. This is text resizing, not certification of every browser zoom/assistive technology |
| Preservation | All fourteen QH tables, six container identities/configuration/start times, private `.env`, realm, ledgers and supplied asset hashes unchanged |
| Original files | Five PNG CRCs/boundaries PASS; PDF 24 pages readable; seven individual SHA-256 values retained. Named ZIP absent, archive-level check NOT TESTED |
| Final branding/theme | NOT IMPLEMENTED / NOT TESTED / NOT ACTIVATED, pending owner asset-selection approval |
| Hosted CI | Check latest PR #15 HEAD separately; local counts above are not attributed to a hosted run |

Counts overlap and are not summed. The first attempt had 41 PASS / 2 FAIL: a new
SSO test-helper assumption and actual enlarged-text overflow. Both were corrected;
the full final run and live reflow check passed. No assertion was weakened to pass.
Existing Starlette/AnyIO deprecation and expected isolated graph-probe warnings
remain distinct from failures.

## Screenshots

These show the **working neutral layout**, not approved branding, on synthetic
isolated fixture data:

- [Environment desktop](screenshots/qh43-environment-desktop.png)
- [Environment mobile](screenshots/qh43-environment-mobile.png)
- [Space desktop](screenshots/qh43-space-desktop.png)
- [Space mobile](screenshots/qh43-space-mobile.png)

Actual VPS screenshots remain private at
`.local-archive/qh43-implementation-20261018/live-*.png`: its dashboard also contains
owner Spaces outside the three demo fixtures, so it is not copied into this archive.
The private proposal is `visual-proposal.png` in the same directory, with its source
HTML under `.local-archive/branding/review-20261018/`.

[Results](results.json) include exact test-image identities and hashes proving its
copied frontend sources equal the executable commit. These are temporary test
images, not deployed/reviewed production artifacts. [Asset inventory](asset-inventory.json)
records precisely which private originals were inspected; [preservation](preservation.json)
is a summary of protected read-only inventories, not an independent external audit.

Reproduce with the existing isolated harness; no persistent QH credentials/volumes:

```bash
python3 scripts/test_qh11_browser.py --sudo-docker \
  --backend-image qh43-api:checkpoint --browser-image qh43-browser:checkpoint \
  --understanding --output /tmp/qh43-fresh-isolated-evidence
python3 docs/evidence/qh43-ux-checkpoint-20261018/audit.py
```

The first command requires those retained exact test images and a fresh empty output
path; use the committed Dockerfiles for a reviewed rebuild, not a silent tag substitute.
The offline audit checks artifact integrity/consistency without network or QH access;
it does not rerun the browser, verify private originals independently, or grant consent.
