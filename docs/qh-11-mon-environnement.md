# QH-11 — Mon environnement

2026-10-17. First browser Space-management UI, reusing the existing React 18,
strict TypeScript and Vite scaffold. Jira [QH-11](https://contextlab.atlassian.net/browse/QH-11)
requires creating/opening a Space without a terminal, correct QH identity and
owner isolation, with no duplicated scaffold. The owner's expanded request adds
real browser PKCE proof, UI states, accessible/mobile navigation and green CI.

QH-10's PR #11 merged first as `24c9f4f8c065bb78b7d62da46b33a2078ccecc6e`;
its Jira closure is verified. QH-11 starts from that updated main in the sole
checkout `/home/ubuntu/qh`, branch `feat/QH-11-mon-environnement`.
QH-11 was subsequently owner-reviewed and merged as
`a5a635fb3200c77a3c1cf2b9e47dcdbb4116da73`; Jira is DONE. The results below
retain the pre-merge technical checkpoint; subsequent QH-12 work was separately authorized.

## Functional path and boundaries

Keycloak login → `/auth/me` → Mon environnement → Mes Context Spaces →
Créer un Context Space → metadata detail → return to list. All application data
comes from the actual QH-9 API. A recently created Space remains visible during
that session even if UUID ordering places it after the first page. Other pages
use the API's bounded cursor. Names are rendered as React text, never HTML.

The browser sends only `{name}` on creation, never owner/status/identity fields.
`GET /auth/me` supplies the internal QH identity; signed-token verification,
identity mapping and PolicyService in FastAPI remain authoritative. Missing and
foreign Spaces share the same message; raw API/IdP errors are not rendered/logged.
No frontend owner filter substitutes for backend access checks.

UI states cover sign-in, pending identity/list/detail, empty list, retryable errors,
invalid name, creation success/failure, inaccessible/missing Space and expired
session. Browser back/forward and deep links use the existing SPA without a new
routing framework. The detail exposes only name, identity, status and creation/
modification metadata. No Understanding retrieval, sources, revisions, chat,
sharing, guest links, MCP, delete or new lifecycle. Deletion remains unavailable.

## Approved browser session choice

The owner explicitly approved the minimal SPA session on 2026-10-17:

- Public `qh-web`, Authorization Code with PKCE S256 and nonce via pinned
  `oidc-client-ts` 3.5.0; no client secret, static token or password grant.
- Tokens exist only in adapter memory. Tab-scoped sessionStorage stores pending
  state/verifier, removed on callback and cleared as stale after five minutes at
  login/callback processing. No token in localStorage or sessionStorage.
- No automatic renewal. Expiry/HTTP 401 discards private views; reload requires
  login again. Keycloak's separate SSO session may satisfy a new login.
- Logout clears local QH memory immediately, then invokes the discovered OIDC
  end-session endpoint. It does not add a post-logout URI to the approved realm.
  The user may remain on the IdP logout screen and return to QH manually. If the
  IdP is unavailable, local logout still succeeds; remote SSO logout may not.
- Callback codes/state/errors are removed from the URL before rendering. The
  return destination is restricted to local Space paths; unrequested, stale or
  altered state and wrong PKCE fail closed. StrictMode redeems a callback once.

This is a POC session, not a new BFF, persistence model, MFA or SaaS hardening claim.
The [identity ADR](adr/0002-identity-and-authorization.md), Product Contract and
[architecture](architecture.md#qh-11-browser-client-merged-not-deployed) remain
in force. Browser authentication grants no sharing or confirmation permission.

## Configuration and running

The default public issuer is the existing `http://localhost:8080/realms/qh`,
client `qh-web`, redirect `http://localhost:5173/oidc/callback`. The Vite gateway
forwards fixed same-origin `/api` paths to `http://backend:8000`; it is development
transport, with all authorization performed by FastAPI. It does not introduce a
public backend contract or a second production service. An explicitly configured
`VITE_OIDC_ISSUER` is public build/dev-server configuration, never a secret.
`QH_WEB_API_TARGET` is trusted server-only configuration for an isolated backend.
A static production build would require a reviewed same-origin reverse proxy;
no deployment configuration is provided or activated here.

The live VPS still uses immutable c723d32 images/schema 0005, including the older
frontend scaffold and an API without Space-management routes. Opening it does
not demonstrate QH-11. Never run development `make up` against that environment.
Demo A activation remains QH-12 and requires separate authorization.

## Reproducible real browser proof

Use Docker, no host Node/Chrome installation or production `.env`:

```sh
docker build -f apps/api/Dockerfile.dev -t qh11-api:test .
docker build -f apps/web/Dockerfile.browser -t qh11-browser:test .
python3 scripts/test_qh11_browser.py \
  --backend-image qh11-api:test --browser-image qh11-browser:test \
  --output /tmp/qh11-browser-evidence-new
# Add --sudo-docker only if Docker access requires sudo.
```

The output directory must be new/empty. The harness creates a labelled network,
new tmpfs PostgreSQL 16.8 and disposable Keycloak 26.4.7 with generated credentials
in a private mode-600 temporary file. It imports the unchanged realm, applies
existing 0001–0005 to its empty test DB and reuses the existing identity fixture.
The real production bootstrap runs without native retrieval, which metadata CRUD
does not require. Chromium and Vite share the test IdP network namespace, so the
approved localhost URLs work with **zero published ports**. No live QH network,
volume, credentials or endpoint is used. Only resources created by this invocation
are stopped/removed normally; the ownership label is checked before teardown.

Build, typecheck (including tests), browser tests and existing real OIDC regression
must all succeed before `verified.json` is written. No automatic retries, trace,
HAR, video, token/session export or login screenshot is enabled. Screenshots cover
only synthetic post-login Alice/Bob views. Real browser acceptance is distinct
from HTTP-only regression and test-only response/fault simulation.

## Verification and Definition of Done

Executed results below refer to local Docker checks. Consult the task PR for
the latest-head hosted CI results; local success does not imply a hosted result.
The CI adds one test-only `browser` job; existing quality, oidc and strict native
jobs remain intact. A green UI test does not establish backend authorization by
itself; the Alice/Bob proof uses real Keycloak and real FastAPI/PostgreSQL.

| Criterion | Evidence required |
| --- | --- |
| Create/open/return without terminal, correct identity | Chromium Alice creates Projet QH, opens metadata, returns and sees it; actual `/auth/me` ID |
| Foreign-owner isolation and direct URL | Bob's independent browser session cannot list/open Alice's Space; uniform backend denial |
| Existing scaffold/contracts | React/Vite/strict TS retained; QH-9 API only; no application API/Core/schema changes |
| Authentication/session security | Real PKCE, forged state, wrong verifier, natural expiration, 401, logout and token-free browser storage |
| UI robustness | Loading/empty/errors/create validation, cursor pages, keyboard, mobile, history navigation, text escaping |
| Regression/CI | Build/typecheck, frontend checks, existing real OIDC/Core/SQL checks and latest-head hosted jobs |
| Scope preservation | Frozen evidence/ledger and live runtime preserved; no provider call, persistent migration or deployment |
| Task DONE | Pending owner review, authorized merge and subsequent Jira closure; green tests alone are insufficient |

Known POC limits: Chromium is the automated browser; no Safari/Firefox execution
or formal WCAG audit is claimed. Session memory does not survive reload, expiry
requires login, logout return is manual, and no refresh/session persistence is
implemented. UI rename is not necessary for this ticket and is not added; PATCH
remains available through the existing API. No additional development ticket starts.

## Executed evidence — 2026-10-17

Implementation unit `1b65a94`; browser/harness unit `2a342a8`. Subsequent report
changes do not alter app/test configuration. The browser image built from this
checkout used immutable ID
`sha256:cfb8548e68d0564f02c1526aed1695d64b1b1d89625a5f6366ba538caafed429`.
See the [machine-readable result](evidence/qh11-browser-20261017/verified.json)
for the observed identities; that artifact is authoritative if a tag changes.

| Criterion / check | Classification and observed result |
| --- | --- |
| Alice create Projet QH → detail → back | Implemented and tested — PASS, real Chromium login, exact internal QH ID, real POST/list/detail APIs |
| Bob foreign Space and direct URL | Implemented and tested — PASS, separate browser/SSO session; uniform 404-backed message and no Alice Space listed |
| Names/metadata and existing scaffold | Implemented and tested — PASS, TypeScript build, existing QH-9 wire contracts and React text rendering |
| PKCE/state/expiry/logout | Implemented and tested — PASS, actual S256 login; unrequested/altered state, wrong verifier, real-token client-clock expiry, 401, reload and logout cases |
| UI states/navigation | Implemented and tested — PASS, 14 frontend checks in 28.3 s, including keyboard/mobile/back/forward/loading and bounded-page simulation; zero skips |
| Existing real OIDC/Core/SQL regression | Implemented and tested — PASS, 1 selected isolated test in 10.78 s, 1 intentionally deselected live verifier; real Keycloak + PostgreSQL identity/owner/CRUD/reopen and TCP checks |
| Backend unit/API regressions | Implemented and tested — PASS, 96 tests in 5.88 s, network disabled, signed token/owner/API checks; no real database claim from this command |
| Lint/structure | Implemented and tested — PASS, Ruff on harness, actionlint, Git whitespace and staged secret guard |
| VPS, realm and frozen artifacts | PASS, before/after private container/image/mount/start/config comparisons; zero diff in backend/Core/shared contracts, realm and sealed QH-8/QH-33 evidence |
| Hosted latest-head CI | Required before technical readiness; recorded on the task PR after publication |
| Safari/Firefox, formal accessibility audit | NOT TESTED; Chromium/mobile viewport and keyboard checks only |
| Understanding/UI delete/rename/deployment | Out of scope; no implementation or activation claimed |
| Review, merge and Jira DONE | Pending owner review/authorization; Jira remains En cours, task is not DONE |

The existing Starlette/AnyIO deprecation warning is unchanged. Overlapping counts
are not summed. The initial 4 contract-only checks and intermediate 13-check run
are superseded by the 14-check final run, not added to its count.

Local commands actually executed (VPS project untouched):

```sh
python3 scripts/test_qh11_browser.py --sudo-docker \
  --backend-image qh10-retrieval:e47a295fe5b9528571779d838286a55318846e51 \
  --browser-image qh11-browser:final-candidate --output /tmp/qh11-browser-run3
sudo -n docker run --rm --network none --entrypoint python \
  qh10-retrieval:e47a295fe5b9528571779d838286a55318846e51 -m pytest -q \
  tests/test_oidc_security.py tests/test_owner_policy.py tests/test_api_composition.py \
  tests/test_context_spaces_api.py tests/test_context_query_api.py
```

The reused backend image is valid here because QH-11 changes no backend executable,
fixture, dependency, schema or contract. The hosted browser job builds the backend
again from the PR commit and runs the same harness; it does not substitute a mock
API. The harness reuses QH-5's test-owned identity provisioner and isolated test.

Documentation references: [oidc-client-ts UserManager](https://authts.github.io/oidc-client-ts/classes/UserManager.html),
[Playwright assertions](https://playwright.dev/docs/test-assertions).
