# QH-43 — controlled VPS QH login activation

2026-10-18 (Europe/Rome). The owner's later Jira decision and explicit execution
message authorize QH theme/static assets, four realm language/theme fields and,
only if necessary, a restart/recreation of Keycloak alone. Earlier source-only
checkpoints remain historical. No merge/Jira DONE, new auth system, BFF or QH-45.

## Reviewed operation and backup boundary

Existing Keycloak 26.4.7 container `qh-keycloak-1`, project `qh`, loopback 8080,
`start-dev --import-realm`, existing `qh_keycloak_data` volume and readonly root
realm file remain authoritative. Frontend/backend keep HMR; other services stay
running. A preflight confirms `/opt/keycloak/themes/qh` does not exist and the
existing themes directory is writable by the existing Keycloak user.

The narrow backup records only the actual old `loginTheme`,
`internationalizationEnabled`, `supportedLocales` and `defaultLocale`, with a
durable checksum and equality digests of other configuration. Old values are
null/false/[]/null. Private mode-600 records live under
`.local-archive/qh43-login-activation-20261018/` (directory mode 700).
No credential records, password exports, client secrets or full realm export are
backed up. An initial overly broad backup proposal was rejected by automatic
review; it was not executed. The narrower operation excludes credential endpoints.

Administration uses the existing Keycloak-hosted admin login through its own
Authorization Code flow, with bearer tokens only in process memory. The only
configuration PUT endpoint is `/admin/realms/qh`, and the payload contains exactly
the four fields above. No master realm setting, issuer, client, redirect, scope,
policy, user/password, identity mapping or session lifetime is changed.

## Exact installation and language change

1. Preserve the original source tree/theme manifest, QH SQL equality inventory,
   private configuration, ledgers and all six container identities/configurations.
2. Make a frozen, hashed private copy of the already verified `qh/login` theme.
   Install only it at `/opt/keycloak/themes/qh` in the existing container. Do not
   replace the base theme, add mounts, rebuild the image or edit Compose/.env.
3. Check the admin server theme list before selecting it. If dynamically recognized,
   no restart is necessary. Otherwise only a graceful restart of the same Keycloak
   is authorized, followed by health/discovery verification. Other changes stop work.
4. Apply only `loginTheme=qh`, `internationalizationEnabled=true`,
   `supportedLocales=[fr,en]`, `defaultLocale=fr`; compare all other configuration.
5. The client sends standard OIDC presentation hint `ui_locales=fr`. This is needed
   because browser English can override a realm default. It changes neither grant,
   PKCE/state/nonce, authority/client/redirect/scopes nor token/session storage.
   Users retain the realm's explicit language selector; fresh English-browser login
   must render French without pretending a locale setting alone proves rendering.
6. Verify live desktop/mobile and authentication, rehearse restoring the old four
   settings, then reapply the approved settings and run final acceptance.

The installed static files live in the existing container's writable layer: they
survive its ordinary restart, **not recreation**. Frozen source/hash receipts and
reinstallation instructions are retained durably. Any future authorized Keycloak
replacement must install these same files and verify readiness **before** serving
the realm selecting `qh`. Generic recreation is still prohibited; there is no new
source bind/path dependency during branch switches or automatic deployment hook.

## Rapid rollback

Use the retained private administrative helper with action `rollback`; it checks
the backup checksum and non-presentation configuration before PUT of only the old
four values. No volume, realm/user, credential or QH database is restored/deleted.
Keep the harmless static files installed; choosing the old theme stops using them.
A clean browser must show the former theme and existing identities must still work.
The helper's `apply` action reinstates only the four approved values after the
rehearsal. When the old theme/default locale was unset, use empty strings in the
PUT payload to clear them: a JSON null is treated as no update. Normalize empty
strings/null to the effective unset state for comparison. Compare supported locales
as an unordered set, not serialized array order; Keycloak's
[26.4.7 RealmRepresentation](https://www.keycloak.org/docs-api/26.4.7/javadocs/org/keycloak/representations/idm/RealmRepresentation.html)
exposes a set. Initial verification/rollback diagnostics revealed these two
representation details; no unrelated configuration was accepted or overwritten. If any real authentication/security regression occurs, rollback and stop
rather than changing security contracts. Protected helper/configuration and exact
execution commands are retained privately; no secrets belong in Git/logs.

## Acceptance and evidence

Actual live receipts and screenshots are recorded separately from the previous
isolated theme evidence. Require welcome → branded French Keycloak → authentic
Code+PKCE callback → Mon environnement on desktop/mobile; wrong password,
state/nonce/PKCE negative controls, token memory/expiry, logout and Alice/Bob scope
must pass. No test creates, confirms or changes QH understanding or calls Mistral.
Natural server/token expiry is distinguished from browser clock acceleration.

[Live execution evidence](evidence/qh43-keycloak-live-20261018/README.md) records
actual changes/restarts and rollback result; preparation alone is not activation.
## Executed acceptance against the owner's new Jira criteria

| Criterion | Classification / execution verdict |
| --- | --- |
| Fresh real VPS welcome → branded French login → Mon environnement, desktop/mobile | Implemented and tested — PASS |
| Selected original logo/bubble/palette, inherited French text and readable invalid-password feedback | Implemented and tested — PASS, including English-browser locale override |
| Code+PKCE/state/nonce, callback, memory-only tokens, logout and existing owner isolation | Implemented and tested — PASS; negative controls stay outside private API access |
| Real token expiry | Implemented and tested — PASS: existing 300-second lifetime, 305 real elapsed seconds, client view removed and original signed token rejected with HTTP 401; no clock acceleration |
| Backup, reversible previous theme, protected configuration/data/volumes | Implemented and tested — PASS: four-field backup, old live form restored, other configuration digest and fourteen QH tables equal; no restart/recreation |
| Live evidence distinct from isolated preview, exact runtime delta | Implemented and tested — PASS: separate live archive, all six container identities/start times unchanged |
| Owner final review, authorized merge and Jira closure | Not completed — pending owner decision; PR remains open, no Jira write |

The protected configuration digest stayed equal before/after and during rollback;
no authentication/security regression was found. Preliminary helper representation
and test-selector failures were corrected and are disclosed in the evidence.

Final owner review, merge and Jira closure remain separate gates. QH-42 retains
future BFF/same-origin decisions; QH-45 is not started.

## Final owner acceptance and centring — 2026-10-18

The owner accepts this baseline and authorizes merge/Jira closure after final
checks, with a final horizontal-centering correction. The existing container
receives only the corrected theme CSS: full-width header grid, no realm update,
restart or recreation. Mobile welcome/environment also remain centred. The
[new actual VPS receipt](evidence/qh43-centering-20261018/README.md) supplements,
and never rewrites, the sealed earlier screenshots/results. Run its lineage audit
for the later CSS revision; the original audit describes the original snapshot.
Backup/rollback remains available. Reproducible theme delivery before a future
container recreation is separately tracked; no recreation is performed now.
