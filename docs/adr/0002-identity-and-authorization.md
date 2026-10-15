# Identity and authorization

Update 2026-10-15: [ADR 0003](0003-native-context-engine.md) / QH-30 changes only the context
engine direction. The OIDC mapping, shared PolicyService and default-deny/resource
boundaries in this decision remain unchanged.

Status: approved by the project owner for QH-5 (2026-10-13).
QH-29 / QH-6b adds the approved shared authorization boundary (2026-10-14).

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

## Shared logical authorization point (QH-29)

The existing `PolicyService` port in `app/policy/services.py` is the single
logical resource-decision point within QH Core's domain/application boundary.
Its initial implementation is QH-5's `OwnerPolicyService`; do not introduce a
second AuthorizationService contract or duplicate owner checks in transports.
This is shared decision logic, not a process singleton or a new network service.

Keep three responsibilities distinct: OIDC authentication and general client
permissions; QH authorization of an operation on a resource; and filtering/
governance of shareable content. General OAuth permission and resource permission
must both allow access. Permission to operate on a space does not authorize all
of its content, revisions or projections for disclosure to a recipient.

Future REST routes (QH-9) and MCP operations (QH-24) must use the same backend QH
policy decisions. Transports enforce those decisions, never invent alternative
resource rules or accept unverified identity headers. MCP calls the authenticated
backend boundary; it neither imports backend implementation nor accesses
PostgreSQL/Neo4j directly. Service credentials or delegated OAuth scopes alone
cannot bypass the resource policy or content governance.

Default deny: authorize before private-content reads, semantic retrieval or
disclosure to an LLM. Looking up minimal ownership metadata to evaluate policy
is distinct from retrieving protected content. Initially the policy stays inside
the backend, explicitly injected through the existing QH-only port. A future
external engine, including Keycloak Authorization Services, belongs behind an
adapter to that port; no provider/framework types enter Core. No external engine
or authorization endpoint is introduced by this decision.

The implemented owner gate covers READ_CONTEXT only; other actions fail closed.
It is not complete selective governance. Granular projection/snapshot rules,
approved content scope and revocation remain in QH-14–QH-22. QH-7's replaceable
ContextEngine integration needs no new authorization service or artificial
technical dependency from this documentation change.

QH-29 review: QH-9 and QH-24 already require reusing QH-5 policy/identity and
forbid duplicate policy or MCP DB bypass; their Jira descriptions need no edits.
The unchanged owner and framework boundaries reuse the executed
[QH-5 evidence](../verification-qh-5.md); no application code or tests changed.

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
