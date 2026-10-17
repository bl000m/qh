# QH-11 browser proof — 2026-10-17

Executed Chromium against real disposable Keycloak 26.4.7, production FastAPI
bootstrap and new tmpfs PostgreSQL 16.8. No published ports, QH live credentials,
production network or volume. Real login, create/open/back and Bob deep-link denial
pass; screenshots show synthetic post-login state only. No login/password/token,
trace, HAR or session export is retained. Test-only fault simulations cover errors
and pagination separately from real REST acceptance.

[Verified execution](verified.json), [Alice dashboard](alice-dashboard.png),
[Bob after denied deep link](bob-denied-dashboard.png).

Reproduce with [the harness and commands](../../qh-11-mon-environnement.md#reproducible-real-browser-proof).
Results demonstrate this bounded POC flow, not a production security certification
or an independent human usability/accessibility audit. The existing OIDC test
selects one isolated case and deselects its live-application case deliberately.
Frozen QH-8/QH-33 captures, review references and ledgers are unchanged.
