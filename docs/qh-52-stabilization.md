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
automatic classification or demo-data update. The metadata API extension and tests
need approval as a public-contract refinement before implementation; actual new
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
