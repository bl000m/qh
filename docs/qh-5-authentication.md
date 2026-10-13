# QH-5 local OIDC authentication

Approved boundary: [identity ADR](adr/0002-identity-and-authorization.md).
Keycloak 26.4.7 is a replaceable development IdP. PostgreSQL QH identities and
PolicyService remain independent. There is one active authentication mechanism.
The earlier uncommitted demo implementation is preserved only in ignored
`.local-archive/qh-5-demo-auth`, excluded from Docker builds.

## Bootstrap

```sh
make up                  # five base services; no IdP required for health
make oidc-up             # build/wait base services + optional Keycloak
make test-oidc           # real login and HTTP tests with an isolated database
make oidc-stop           # stop only the optional IdP, preserve its data
make down                # stop base stack, preserve named volumes
docker compose --env-file .env -f infra/docker/docker-compose.yml --profile oidc down
```

Never add `--volumes` to shutdown commands. `make oidc-up` generates missing
passwords in the ignored root `.env` (mode 0600) and imports `infra/keycloak/qh-realm.json`.
The JSON contains environment placeholders, not passwords. Alice and Bob's
passwords are `QH_ALICE_PASSWORD` / `QH_BOB_PASSWORD`; the initial `qh-admin`
password is `KEYCLOAK_ADMIN_PASSWORD`. Do not copy them into source or logs.

Keycloak imports a missing realm only. A repeatable reconciliation step installs
the committed subject, audience and role mappers without changing users,
passwords or sessions. Changing `.env` does not rotate existing IdP credentials;
use Keycloak administration rather than deleting the volume. Rotating a password
also requires updating the corresponding ignored test credential.

Keycloak stores local IdP state in its own `qh_keycloak_data` volume using
`dev-file` (embedded H2); it does not connect to QH PostgreSQL or join the internal
data network. HTTP 8080 is bound to loopback; readiness uses internal management
port 9000. Keycloak has a 1 GiB container limit. This stack was tested with
approximately 4 GiB RAM and 8 CPUs; 6 GiB RAM is recommended for concurrent builds.
This is local development, not a production
deployment. `start-dev` must not be published remotely.

## Issuer and login

The public issuer is `http://localhost:8080/realms/qh`, including when validation
runs inside Docker. The backend fetches keys through
`http://keycloak:8080/realms/qh/protocol/openid-connect/certs`; this transport URL
does not change the token issuer. `KEYCLOAK_PORT` changes the public port.

The public client `qh-web` uses Authorization Code with PKCE S256; password grants
are disabled for users. Its redirect URI is
`http://localhost:5173/oidc/callback` (or `FRONTEND_PORT`). The integration test
drives the real Keycloak login form and exchanges the code with its verifier.
There is no frontend login page in QH-5. An admin-only password grant is used by
the local realm configuration script; it is not the application authentication
flow. The API audience is `qh-api`, general scope `qh:api`, role `qh-user`.

JWT verification uses RSA/RS256 with a fixed allowlist, JWKS cache and bounded
unknown-key refresh. It checks issuer, audience, required expiration, issued-at,
subject and optional not-before. Token-supplied URLs cannot select a key endpoint.
JWTs, passwords, emails and external subjects are not returned by `/auth/me`.
Invalid/missing credentials yield 401; valid tokens lacking the general
scope/role yield 403; unavailable IdP/storage yields 503. Health remains public.
No user ID header or query parameter is trusted.

## Identity mapping and application activation

`user_identities` has primary key `(issuer, subject)`, a non-null `user_id`
foreign key to `users.id`, creation time and nonblank checks. Multiple external
identities may map to a QH user. There is no automatic account creation from
token claims. The local demo provisioning associates fixed, independent QH UUIDs
with the two imported IdP subjects, idempotently, refusing an existing binding
to another QH user. No Context Space is created by application provisioning.

The prepared additive revision is `0002_oidc_identities`. **It has not been
applied to database `qh`.** Both commands below require the owner's explicit
authorization for application deployment; neither is run by startup or tests:

```sh
make migration-current
make migrate             # only after explicit application migration approval
make seed-oidc-demo       # only after explicit application provisioning approval
```

Until then, a valid token cannot resolve its identity against the default `qh`
schema; `/auth/me` returns 503. Tests exercise the actual runtime composition
against isolated migrated databases, including persistent identity lookup.

The owner policy receives QH IDs only. General authentication/permissions run
first; Core authorization precedes private content reads. Missing and foreign
Context Spaces produce identical 403 responses. Private probe routes are
registered only by tests. Production exposes `/health` and `/auth/me`; it has no
`/context-spaces/{id}/access` or test routes.

## Repeat checks

```sh
python3 scripts/check_compose.py
python3 scripts/check_compose.py --oidc
make test-oidc
make verify-running
make verify-infra
docker compose --env-file .env -f infra/docker/docker-compose.yml exec -T backend \
  python -m pytest -q tests/test_owner_policy.py tests/test_oidc_security.py \
  tests/test_identity_migration.py tests/test_architecture.py
```

QH-5 tests create uniquely named `qh5_test_*` databases and retain them for
inspection; they never migrate/seed `qh`. The migration test compares all seven
canonical tables before/after upgrade and downgrade. Existing QH-4 tests remain
pinned to their foundation revision and remove only their own temporary test
databases. No global cleanup or persistent volume deletion is performed.

Remote MCP delegated OAuth, consent/grants and projection/sharing authorization
remain in later tickets. Unimplemented owner actions fail closed.

Implementation references: [Keycloak container setup](https://www.keycloak.org/server/containers),
[realm import placeholders](https://www.keycloak.org/server/importExport),
[hostname configuration](https://www.keycloak.org/server/hostname),
[JWT verification API](https://pyjwt.readthedocs.io/en/2.10.1/api.html).
