# QH-52 — Demo B readiness stabilization

Owner request, 2026-10-20. Dedicated branch from main `0336566`; PR #19 and its
`18bac2c` source branch are retained unchanged. No dependency on unapplied schema
0007. Related Jira: QH-42, QH-49, QH-50, QH-51. One stabilization PR and one final
full CI campaign. No merge, paid inference or existing demo-Space test writes.

## Structural contracts — owner approved 2026-10-20

The owner explicitly approved A, B and C for implementation and isolated tests.
Persistent activation gates below remain in force.

### A. Browser work session, development profile only

Keep the SPA and Code+PKCE, existing issuer/client/redirects/scopes and short
access-token lifetime. Use the existing oidc-client-ts 3.5.0 refresh flow, with
access/ID/refresh tokens only in its memory store. No offline access, BFF or
JavaScript authentication cookie. Start renewal 60 seconds before access expiry;
serialize renewal and recheck on focus/visibility/wake and before protected API
requests. Never replay a failed data/provider POST automatically.

Verify rotated refresh-token handling against isolated Keycloak with
`revokeRefreshToken=true`, `refreshTokenMaxReuse=0`; never reuse an earlier refresh
token. Prepare the exact realm-setting patch only if the active development realm
does not already rotate. No live realm write is authorized by this proposal.
Do not increase access or SSO TTLs. The existing SSO idle/absolute bounds still
terminate the work session; background refresh while the browser runs can maintain
SSO idle validity. Browser suspension beyond those bounds correctly needs a new
authentication. A local eight-hour absolute work-session ceiling prevents indefinite
automatic extension even if an IdP permits more.

Successful renewal keeps the current React tree and unsent text in memory. On
failure, preserve the open route and offer reconnection through the existing
Keycloak SSO. Safe domain AND Space paths may survive the OIDC transaction;
no conversation text/token enters storage. A reload discards unsaved text. Before
an explicit full-page reconnection, warn and offer user-initiated copying of unsent
text; never silently persist it. Explicit logout cancels renewal/inflight work,
revokes refresh credentials where supported and starts native OIDC logout; no
silent sign-in after an explicit logout. Backend owner/issuer+subject policy stays.

Alternative: top-level SSO reconnection every 300 seconds preserves the old token
contract but interrupts editing and cannot retain memory across redirects. A BFF
adds a server session responsibility and remains QH-42 design work. Recommended:
bounded memory-only refresh, with isolated expiry/logout/revocation/wake tests.

### B. Organization descriptions without a database migration

Extend only the existing owner_organization JSON contract at schema 0006: optional
domain `description` and `space_descriptions` keyed by explicitly owned Space ID,
each plain text up to 500 characters. Existing documents mean empty descriptions;
preserve omitted fields from old clients rather than silently erasing metadata.
Reuse version conflict handling, organization policy and SQL owner checks. Reuse
QH-9 PATCH for Space names. No original source/Understanding/schema/type migration,
automatic classification or demo-data update. The owner approved the metadata API extension and tests
as a public-contract refinement; actual new
metadata writes are initiated explicitly by the owner through the UI.

Alternative: add canonical Space columns and a migration; this unnecessarily moves
organizational descriptions into canonical lifecycle and risks collision with
unmerged 0007. Recommended: existing owner-only organization metadata.

### C. Disclosure consent stable across access-token renewal

Keep administrative enablement, exact-content disclosure and epistemic review
separate. Add a default-off development grant mode, prepared and tested in isolation.
Bind a consented grant to the verified QH identity AND verified OIDC issuer/session
(`sid`, hashed internally), exact Space/model/purpose/proposed choice and canonical
snapshot/selection. No token value or raw session identifier is exposed or logged.
Missing/unverified session identity fails closed; the legacy token-bound mode stays
available. Renewing an access token for the same verified session does not itself
renew disclosure. Grant lifetime is at most 30 minutes, bounded by administrative
availability and the browser work session; expiry requires explicit reauthorization.

The single consent covers the displayed exact snapshot and bounded ongoing
user-authored dialogue for this purpose. Newly saved revisions, broader selection,
another Space/model/purpose, logout/account switch or revocation invalidate it.
Show provider/model and remaining budget without asking users to administer limits
per question. The administrative receipt/allowlist/prices, central CHAT policy,
provenance checks, atomic durable accounting and no retry/fallback remain mandatory
on every send. No new allowlist, request cap or price/budget availability is granted.

Retain the existing aggregate 8 POST / USD 0.20 and per-session 3 POST / USD 0.01;
account a renewed/reconsented grant against the same work-session budget rather
than resetting counters. Historical ledgers remain immutable. Prepare the versioned
accounting/grant contract with fake providers; do not migrate the active ledger,
enable the new mode, extend the original 30-day availability or send a real POST.
Explicit logout/revoke blocks new sends; already transmitted data cannot be recalled.

Alternative: keep five-minute token-bound grants; this is secure but cannot meet
the requested continuity after token renewal. An unrestricted environment-wide
grant would silently widen disclosure and is rejected. Recommended: bounded
session-bound exact-snapshot consent, default-off until separately activated.

### Approval boundary

Approval of A/B/C authorizes implementation and isolated tests of these precise
contracts, plus documentation/ADR amendments. It does not authorize persistent
realm/provider settings, ledger migration, schema application, paid calls, new
allowlists or a Keycloak image replacement. Any necessary VPS operation must be
presented as an exact tested artifact/config diff with backup/rollback before its
separate activation gate. Ordinary CSS, existing-endpoint bootstrap, name editing
and product-provider presentation corrections continue independently.

## Evidence and sources

The current SPA explicitly sets automaticSilentRenew=false and clears its User at
access expiry; provider grants expire within 300 seconds and compare credential
hashes. The root readonly realm import specifies no custom token/session lifetimes;
actual observed access lifetime is about 300 seconds. Do not infer active rotation
or SSO settings from omitted import fields.

Primary references consulted for the proposal:

- [oidc-client-ts 3.5.0 UserManager implementation](https://github.com/authts/oidc-client-ts/blob/v3.5.0/src/UserManager.ts)
- [UserManager settings](https://authts.github.io/oidc-client-ts/interfaces/UserManagerSettings.html)
- [Keycloak 26.4.7 session/token administration](https://www.keycloak.org/docs/26.4.7/server_admin/)

The theme field macros default autocomplete to off but accept values supplied by
the inherited native login form. That is not evidence that rendered username or
password fields disable completion. Inspect the actual isolated login DOM before
changing or building a replacement image. Native Mac password-manager prompts
remain browser/OS-controlled; compatible markup alone cannot prove their display.


## Prepared persistent activation gate (not executed)

The exact non-secret Keycloak delta is
[infra/keycloak/qh52-development-session.json](../infra/keycloak/qh52-development-session.json):
rotation with zero refresh-token reuse, and an additive qh-web-only AUTH_TIME
session-note mapper. The existing qh:api audience/roles/subject, public client,
Code+PKCE, redirect/origin and TTLs stay fixed. The mapper uses the server session
note, never a user-editable attribute. The readonly root import remains untouched.
Its reference is Keycloak26.4.7's built-in
[auth_time mapper](https://github.com/keycloak/keycloak/blob/26.4.7/services/src/main/java/org/keycloak/protocol/oidc/OIDCLoginProtocolFactory.java).
No protocol mapper or realm setting has been written to the VPS.

For a later activation request, first retain a protected realm/client/settings
readback and backup/rollback under the established Keycloak procedure. Compare the
actual delta (apply only missing mapper/settings), preserve sealed image ID, root
import and data volume, and test rollback on the isolated copy. Enable only the
frontend VITE_QH_DEVELOPMENT_SESSION=1 environment and backend
QH_CHAT_SESSION_BINDING=oidc after explicit approval of their concrete container
config diff and brief frontend/backend restart. The guarded hot-reload overlay prepares both environment keys with deny-by-default values; no dev-up/restart has been run with that changed configuration. Neither flag is enabled here.
Terminate the old browser work session and sign in anew; retain historical ledger
rows and cumulative totals. Do not map old grant UUIDs to invented session IDs or
reset costs. Existing receipt/snapshot/allowlist/price/budget and availability expiry
still apply. No paid smoke or canonical/demo write is part of this activation.

Password-manager evidence: the native form actually served at localhost:8080 has
username/name=username/autocomplete=username, password/name=password/type=password/
autocomplete=current-password and a native same-origin POST form. No React password
field or password storage exists. Remember Me concerns the IdP session, not browser
password saving; it is absent from the inspected form. On the Mac retain the same
SSH-tunnel host and port for both saved credentials and login: localhost and
127.0.0.1 are distinct origins. Chrome/Safari profile, private-browsing and password
manager settings still determine whether a save/update prompt appears. That native
Mac prompt is NOT TESTED here; markup compatibility is directly verified.

A read-only administration inspection of the actual VPS on2026-10-20 confirmed:
access300s, SSO idle1800s, SSO absolute36000s, refresh rotationfalse, maxReuse0,
RememberMefalse; qh-web remains public Code+PKCE with qh:api and no password grant.
The client has no auth_time mapper. The necessary activation delta is therefore
rotationfalse→true plus that client mapper, frontend flag0→1 and backend binding
credential→oidc. MaxReuse0 and all TTLs stay as observed. A resolved Compose dry
comparison verified that enabling the prepared flags changes exactly those two
frontend/backend environment entries and no other service configuration. Keycloak
imageID remains sha256:21451375143c0d31397f1d23cbb38aca9a872e220bd74c94d89f815635b43954.
Guarded dev-status still reports all six QH services healthy; no restart/activation
was performed after preparing the new environment keys.

## Acceptance evidence (technical readiness, review still required)

Dedicated Jira: [QH-52](https://contextlab.atlassian.net/browse/QH-52). Related QH-42,
QH-49, QH-50 and QH-51; no QH-46 state change. Checkout /home/ubuntu/qh on
fix/QH-52-demo-readiness from0336566. PR19 stays OPEN at18bac2c. No merge is part
of this task. Private execution artifacts: .local-archive/qh52-20261020/.

| Criterion | Classification and verdict | Executed evidence and limits |
| --- | --- | --- |
| Dedicated scope/dependencies and approved structural decisions | Implemented and tested — PASS | QH-52 created/linked; owner A/B/C approval recorded in comment10034 and this document |
| Memory-only bounded renewal, route continuity, work/disclosure budgets and fail-closed checks | Implemented and tested — PASS for isolated contracts | backend-contracts.log:79 tests; session-http.log:10 tests; focused-web-final.log:6 tests including failed rotation, different account, logout race, expiry and8h clock; actual Keycloak rotating/old-token/revoke/logout protocol test passes; product-browser-8 passes real SPA renewal, unchanged grant/draft, revoked-refresh expiry with in-memory draft retention, explicit logout erasure |
| Native password-manager-compatible form | Implemented and tested — PASS for markup | Actual VPS DOM readback native-login-fields.json plus real Chromium/Keycloak login; native Mac Chrome/Safari password-manager prompts NOT TESTED |
| Composer/empty notice, desktop1448×1086, mobile390×844, zoom200%, reduced keyboard viewport, expanded disclosure | Implemented and tested — PASS | Product browser runs and screenshots, bounds/overflow assertions; real device OS keyboard NOT TESTED (450px viewport simulated) |
| Owner-only name/descriptions, persistence and compatibility | Implemented and tested — PASS | test_environment.py isolated PostgreSQL at0006: reopening, old-client omission preservation, CAS, Alice/Bob, ownership revocation, no sources/understanding writes; product name/domain edits and reopen |
| No mock in normal product path | Implemented and tested — PASS | Product-mode browser without fixture flag; unavailable provider disables Send, explicit direct mock POST returns503; legacy replay fixtures opt in |
| Administrative availability vs exact disclosure vs human confirmation | Implemented and tested — PASS within prepared contract | Separate receipt/policy/budget, snapshot consent, and canonical review remain; fake-provider tests retain3/USD0.01 work cap and aggregate8/USD0.20 across token renewal/reconsent/restart |
| Empty-Space first information without Mistral | Implemented and tested — PASS | Real UI→OIDC→API→isolated PostgreSQL/Neo4j, exact literal source/proposed revision/provenance, reload and Bob denial. No semantic extraction or human confirmation inferred |
| Existing configuration/evidence and active PR preserved | Implemented and tested — PASS | preservation.json: all947 original ignored files, .env/import, original image/mount identities and infrastructure start times equal; guarded dev-status six healthy; PR19 unchanged |
| Full final CI campaign and new review PR | Implemented but unverified — NOT TESTED at this checkpoint | PR20 initial integration pass found a partially replaced OIDC test binding; all verifier facets were aligned and rechecked. The final campaign verdict is recorded on PR20 and in the final Jira comment |
| Persistent VPS renewal/grant activation | Out of scope for this approval — NOT TESTED | Prepared exact delta above; no realm/ledger/receipt/schema/provider activation or real paid POST |

Regression corrections were kept within scope: explicit mock opt-in in historical
fixtures, capability HTTP union for the approved1800s mode, native logout navigation
synchronization in the browser test, and title/actions grouping on mobile. Simulated
Mistral HTTP demonstrates orchestration/accounting, not live model comprehension,
latency, cost or provider reliability. Semantic extraction remains QH-51.


Final targeted product result before publication: product-browser-7 first scenario
PASS (native form, Space/domain edits, all viewport bounds, literal bootstrap,
reopen, mock denial and Bob isolation); product-browser-8 renewal/revocation scenario
PASS with actual Keycloak and simulated provider HTTP. The extra browser-clock step
crosses SDK expires_in-derived expiry; server time and TTLs are never changed.
[Retained synthetic screenshots](evidence/qh52-20261020/README.md).


Final integration corrections: test compositions now replace identity, expiry and
verified-session authentication together, retaining actual signature/claims and SQL
owner checks. Logout dispatches grant revocation with its current in-memory access
credential before clearing it; it cannot wait on or initiate a renewal. The focused
logout/current-token and in-flight/account/rotation checks pass (3 tests/typecheck).
No timeout, policy, ledger or provenance check was weakened.


Final browser compatibility/layout correction: Space-route restoration stays behind
the approved development profile; the unactivated legacy profile retains its prior
home landing (domain deep links remain supported). Both profile-boundary unit checks
and the original protected-login/reload acceptance pass. On mobile, the edit action
is compact and first-information opens directly from the empty-Space guide; the
manual authoring control for populated Spaces follows the primary composer.
The original composer position assertion (<650px) passes unchanged. product-final
then passes both product scenarios plus the actual rotating Keycloak protocol test;
the retained screenshots now match that final source. Zoom evidence uses CSS zoom
and the existing200% text-reflow regression, not a native Mac browser zoom gesture.

The earlier84e2593 hosted pass verified785 native integration tests without skips,
quality and OIDC. Its browser failures identified legacy-landing incompatibility
and mobile control height; these were corrected and targeted before publication.
The final review verdict requires all checks on the final PR head, not reuse of a
failed or merely partial workflow result.


## Later QH-54 draft exception — owner approval 2026-10-21

The owner approved only unsent message/manual-element recovery in sessionStorage
for explicit reconnection, max30minutes and the exact verified QH owner/owned Space.
Stored text is removed after restoration, logout, account change or explicit clear;
no tokens/history, automatic submission or canonical writes. This supersedes the
earlier memory-only draft restriction for that narrow path. OIDC refresh/rotation,
TTL, disclosure, work-session and administrative budget contracts remain unchanged.
[Implementation and isolated verification](qh-54-maquette-alignment.md).


## Superseding development AI decision — 2026-10-22

The owner explicitly replaces prior development UI snapshot/session consents and
Alice/Projet pilote eligibility with ordinary AI use by the exact verified owner
OIDC account in all its owned Spaces, present/future. **Envoyer** authorizes one
chat processing request; **Proposer avec Mistral** authorizes one selected-source
UUM extraction. There is no preliminary activation, provider checkbox, mandatory
snapshot preview/confirmation or per-Space/conversation grant. No inference on
opening a page. The active model and transmitted data scope are visible. Only
confirmed-current Space elements and the explicitly submitted dialogue are sent
by default; proposed inclusion is a separate user choice. Chat never confirms or
persists facts; UUM creates proposed revisions reviewed through QH46.

This exception retains verified OIDC/CHAT/owner policy, graph freshness, exact
source validation, immutable revisions and isolated ownership. Only development,
one configured OIDC principal, Mistral AI/mistral-small-2603. Preserve the original
QH45 ledger and aggregate8 requests/USD0.20, old entries and absolute expiry; no
QH51 allocation transfer or reset. Historical3 requests/USD0.01 session limits do
not apply in this mode. Reserve the bounded maximum cost atomically before HTTP;
concurrent requests cannot overspend. No retry/fallback. Insufficient global
reservation returns « Plafond IA atteint. Aucune nouvelle requête ne sera facturée. »
before sending. Previous decisions above remain historical and continue outside
this precisely scoped development mode. See [implementation contract](qh-51-essai-ia.md).
