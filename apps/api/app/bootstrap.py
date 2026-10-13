"""Runtime composition root: concrete adapters stay outside the inner modules."""

import os

from adapters.oidc import OIDCAuthenticator, OIDCSettings
from adapters.postgres.config import database_url
from adapters.postgres.security import PostgresSecurityReader
from app.api.security import SecurityBindings
from app.main import create_app
from app.policy.owner import OwnerPolicyService


def create_runtime_app():
    reader = PostgresSecurityReader(url=database_url())
    authenticator = OIDCAuthenticator(
        settings=OIDCSettings(
            issuer=os.environ.get("OIDC_ISSUER", "http://localhost:8080/realms/qh"),
            jwks_url=os.environ.get("OIDC_JWKS_URL", "http://keycloak:8080/realms/qh/protocol/openid-connect/certs"),
            audience=os.environ.get("OIDC_AUDIENCE", "qh-api"),
        ),
        resolve_identity=reader.resolve_identity,
    )
    return create_app(security=SecurityBindings(
        authenticate=authenticator.authenticate, policy=OwnerPolicyService(owner_for=reader.owner_for),
    ))
