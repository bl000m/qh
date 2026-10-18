# QH-43 — immersive heroes, Space capsules and primary chat

2026-10-18. [Decisions, implementation and limits](../../qh-43-hero-checkpoint.md).
Existing [PR #15](https://github.com/bl000m/qh/pull/15); no merge/Jira DONE or
new product capability. The owner requested this correction after the previous
final-review checkpoint; earlier captures/ledgers remain immutable.

## Actual desktop/mobile captures

| Surface | Desktop | Mobile |
| --- | --- | --- |
| Full-width welcome, large central original bubble | [Welcome](screenshots/welcome-desktop.png) | [Welcome](screenshots/welcome-mobile.png) |
| Mon environnement, central hero | [Environment](screenshots/environment-desktop.png) | [Environment](screenshots/environment-mobile.png) |
| Owned-Space capsules, centered short captions | [Space list](screenshots/spaces-desktop.png) | [Space list](screenshots/spaces-mobile.png) |
| Primary chat and folded explorer | [Space](screenshots/space-desktop.png) | [Space](screenshots/space-mobile.png) |

Captures are real Chromium rendering of isolated synthetic fixtures, not the
private VPS dashboard or composited mockups. The environment/list capture test retains exact API records for only the three
actual synthetic demo Spaces in its fixture response, excluding other acceptance/
security controls. That restriction is test-only, not a production filter or a
complete/global inventory. The full suite exercises the other controls separately. The same seven original private
references and selected public mark/bubble/icon bytes remain unchanged.

Welcome uses the useful shell width (1120px at 1280px viewport), a central 480px
image box, centered heading and login action; mobile caps the box at 340px and
available width. Environment artwork is 400px desktop/300px mobile. PNG boxes keep
the original 4:3 ratio, including original transparent margins; the visible sphere
is smaller than the image box. No crop, new master or creative variant is produced.

Each Space has a rounded capsule with a proportionate original bubble, centered
title above and full accessible link name. Above ten **grapheme clusters**, visual
captions use the first ten plus `…`; full names remain in tooltip, metadata and
detail, and navigation/React keys retain exact UUIDs. Two identical short captions
remain distinct objects. No Domain, category or semantic state is inferred from
artwork. The larger chat panel/composer dominates in-Space; technical metadata
moves below chat/explorer. Consent/warnings remain visible and unchanged.

## Human availability messages

Proposed-only support without opt-in explicitly explains that elements **exist**,
are unconfirmed and require checking the named proposal-inclusion control. This
is visible before a question and alongside an insufficient answer. The checkbox
stays unchecked; no generated answer is fabricated or semantically rewritten.

No current/proposed hit alone is not called empty. Only then, one authorized
`history` row is checked through the existing graph-verified browse endpoint.
History-only gets a preserved-history explanation; no retained understanding
revisions gets an empty-understanding state. This says nothing about source-only
records. On a history lookup error chat is unavailable, never falsely empty.
History is never added to the chat payload. Other insufficient answers explain
limited supplied support without asserting information is absent everywhere.

## Verification, integrity and reproduction

The [execution receipt](results.json) records exact image/source identities and
observed counts.

| Executed check | Observed result |
| --- | --- |
| Complete isolated Chromium/contracts | 51 passed, zero skips, 3.6m |
| Existing real OIDC/owner regression | 1 passed, 1 deselected, 13.16 s |
| Real graph outage | 4 passed, 8.0 s |
| SQL restore/native rebuild | All canonical tables equal |
| Restored-ID browser | 1 passed, 15.8 s |
| Final three-Space capture recheck | 1 passed, 19.9 s |
| Capture harness retained security/recovery gates | OIDC 1 PASS/1 deselected; outage 4 PASS; restore browser 1 PASS |
| Build/TypeScript, Ruff, selected asset/original archive integrity | PASS |
| Fresh VPS read-only preservation and six healthy containers | PASS |

The complete 51-case run uses `qh43-browser:hero`; a targeted
capture recheck uses `qh43-browser:hero-review`. Their client executable/asset
bytes are identical; only the latter's test narrows the screenshot fixture list.
Hosted CI uses the final test tree with no filter. Tests cover long/short Unicode captions, collision-safe links,
keyboard, primary composer, opt-in/explanations, historical/empty/error states,
canonical warnings, explorer/history/provenance, Alice/Bob and real OIDC.
No paid provider is used. Counts from different phases overlap; do not sum them.

The existing Docker-only harness uses dedicated generated credentials and
isolated test SQL/Neo4j/Keycloak. Its theme preview is inherited French login in
the disposable realm; the VPS theme/realm stays unchanged. It also verifies real
graph outage, SQL dump/restore, native rebuild and restored-ID browsing.

```bash
python3 scripts/test_qh11_browser.py --sudo-docker \
  --backend-image qh43-api:checkpoint --browser-image qh43-browser:hero \
  --understanding --qh-login-theme --output /tmp/qh43-hero-fresh
python3 docs/evidence/qh43-hero-20261018/audit.py
```

All selected image hashes match the original asset manifest. Before/after read-only
checks cover fourteen QH tables, six runtime container identities/configurations/
start times, private .env, readonly realm import, both closed Mistral ledgers and
seven original references. Full owner/database inventories and live dashboard
captures remain private. Existing hot reload/ports are retained; no persistent
write, inference, deployment, configuration replacement, realm change or restart.

Hosted CI must be checked on the latest PR HEAD, with all four jobs green. Technical
readiness does not imply owner UX acceptance, merge or Jira DONE. No other ticket
is started. Previous final-review runtime hash assertions refer to their prior
checkpoint; the historical sealed artifacts stay unchanged after this explicitly
authorized source correction.
