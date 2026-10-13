# Identity and authorization

Status: approved by the project owner for QH-5 (2026-10-13).

This decision complements, without replacing, the canonical persistence ADR
`0002-canonical-understanding-persistence.md` and the modular architecture ADR.

## Decision

Keycloak is the initial local development Identity Provider. OpenID Connect is
the integration contract, so another conforming provider can replace it without
changing QH Core. Provider SDKs, tokens and JWT/JWKS validation belong in adapters.

QH keeps its own stable identity (`users.id`). A persistent, unique external
`issuer + subject` pair maps to that identity; neither an email, username nor an
IdP subject alone identifies a QH owner. The mapping is an additive migration,
which must not be applied to the application database without authorization.

Keycloak authenticates users and manages identity, general OAuth roles and
scopes. The inbound security adapter verifies the token and applicable general
permissions. QH PolicyService remains authoritative for access to Context
Spaces, projections and shareable content. Access requires **both applicable
levels to permit it**; an OAuth scope never grants universal context access.
Authorization must precede reading or returning private content. Unknown and
foreign spaces yield the same denial to avoid disclosing their existence.

QH-5 implements OIDC authentication, `GET /auth/me` (only non-sensitive internal
identity), and reusable owner read policy. Private HTTP routes for exercising
that policy exist only in tests, never in the production router. Projection and
sharing policies remain in their feature tickets. Delegated remote MCP OAuth,
grants and consent remain in QH-23/QH-24; OIDC login does not implement them.

## Consequences

Keep the five base Docker services. Keycloak is an optional local development
profile, with persistent IdP data and no access to QH database credentials.
`start-dev` and demo provisioning are confined to local development. No parallel
proprietary authentication scheme is retained in the active application.

Compose dependencies explicitly at the application boundary. Core accepts only
QH domain identities and ports; it never imports FastAPI, Keycloak or JWT code.
Test provider validation, identity mapping and Core owner policy independently,
then exercise real Keycloak login and HTTP enforcement together in an isolated
database. Never use a test run to migrate or seed the application database.
