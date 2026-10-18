# QH-43 — actual VPS branded French login

2026-10-18 (Europe/Rome). [Operation, boundaries and rollback](../../qh-43-keycloak-activation.md).
These are **actual VPS** captures and tests, distinct from the previous disposable
realm preview. No merge/Jira DONE, QH-42 auth redesign or QH-45 implementation.

## Before versus active QH login

| Actual VPS form | Desktop | Mobile |
| --- | --- | --- |
| Original standard theme, English browser | [Before](screenshots/before-desktop.png) | [Before](screenshots/before-mobile.png) |
| Active QH theme, French despite English browser | [QH login](screenshots/login-desktop.png) | [QH login](screenshots/login-mobile.png) |

Both captures precede credential entry; no owner dashboard, admin console, personal
identity, password/token or full URL appears. Header/mark, decorative original
bubble and white/black/red presentation replace the standard dark/blue login.
French heading/password/Connexion and existing credential feedback are inherited
from Keycloak 26.4.7, not implemented in React or copied password templates.
The browser still redirects to the same Keycloak URL; this is not same-origin/BFF.

## Actual runtime delta

Seven already reviewed static files were installed at `/opt/keycloak/themes/qh`
in the **existing** `qh-keycloak-1`. The server discovered them dynamically.
**Zero restart, zero recreation, zero new mounts/volumes/services.** Image, container
ID/start time, command, environment, networks and ports remain unchanged for all
six services. Theme files equal the frozen/source hashes. The installed writable-
layer copy survives restart but requires reinstall before any future separately
authorized container recreation; frozen sources/checksums are retained privately.

Only four qh realm settings change: `loginTheme=qh`, internationalization enabled,
supported `fr/en`, default `fr`. Standard `ui_locales=fr` is now requested by QH;
realm default alone could be overridden by browser English. Issuer/client ID,
redirects/scopes, authentication flows, identity mappings, credentials, token memory,
300-second access-token lifetime and SSO/session settings are unchanged. The readonly
root import is unchanged. No master realm configuration endpoint is written.

Narrow backup/rollback settings and private administration use the existing hosted
admin Authorization Code flow, not password grant/ROPC. No credential endpoint is
called or exported. An initial broader backup proposal was rejected before execution
and replaced by the four-field backup and non-secret equality checks.

## Rollback and diagnostic honesty

The old theme was restored and observed on the actual VPS before reapplying QH.
The backup/checksum and narrow helper remain privately available. No QH data, user,
credential, realm or volume restore/deletion is part of rollback.

Initial operator checks correctly stopped on representation details: supported
locales are a set, and null theme/default-locale fields do not clear the selected
values on update. The helper now compares the exact locale set and restores unset
strings with explicit empty values, without weakening other-field equality. The
protected configuration digest stayed equal throughout. A new live test initially
used an obsolete error-element ID; the actual wrong-password feedback was already
rendered correctly in French. Its assertions now locate the visible French message.
Each failed acceptance attempt automatically restored the old presentation. These
preliminary failures are retained privately, not presented as successful runs.

## Verifiable current acceptance

| Actual VPS check | Observed outcome |
| --- | --- |
| Fresh English-browser desktop/mobile → French QH login → Mon environnement | PASS |
| Wrong password, readable French message, subsequent successful login | PASS |
| Exact S256 verifier/state/ID-token nonce binding and tokens only in memory | PASS |
| Tampered state, nonce and verifier | PASS: no private API access; wrong verifier rejected by actual Keycloak |
| Alice's retained synthetic Spaces | PASS: three Spaces, six proposed revisions each |
| Bob cross-owner access | PASS: six 404 denials; no Alice entries in Bob's list |
| Logout and fresh server credential prompt | PASS |
| Real client/server signed-token expiration | PASS after 305 elapsed seconds, HTTP 401; no clock acceleration |
| Anonymous access | PASS, HTTP 401 |
| Previous-theme live rollback and final reapplication | PASS |
| Runtime/data/configuration preservation | PASS, zero restarts/recreations |

The [sanitized result receipt](results.json) contains actual live check outcomes,
source/static hashes, preserved-config checks and runtime identity equality. The
manual verifier is [guarded and read-only for QH](../../../tests/browser/verify_qh43_live_login.cjs);
it requires explicit opt-in and private generated/configured demo credentials.
It never runs against the VPS automatically in CI. CI retains isolated test data;
its new nonce regression and French-request assertion reuse the existing harness.

The live tests cover fresh desktop/mobile QH → Keycloak → Mon environnement,
wrong password then successful login, logout and fresh server login, real Code+PKCE
and nonce binding, state/nonce/verifier rejection before private API access,
Alice's three retained Spaces/six proposed revisions each, six Bob denials,
anonymous denial and memory-only tokens. Natural access-token expiration is awaited
on the real wall clock, then the same actual signed token must return HTTP 401;
no browser clock acceleration or shortened realm/session settings.

All fourteen QH tables, three demo Spaces, six container configurations, private
.env, readonly import, both closed Mistral ledgers and seven original artwork files
are preserved. Detailed inventories/failure captures/admin configuration stay private.
No provider call, Understanding write, confirmation, migration or app restart.

Full hosted CI and final PR HEAD are verified separately on PR #15; green checks
do not approve the UX or authorize merge/Jira closure. The next step remains the
owner's real Mac review. QH-45, QH-39 and QH-42 implementation are not started.
