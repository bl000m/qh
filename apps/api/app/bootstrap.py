"""Runtime composition root: concrete adapters stay outside the inner modules."""

import os
import asyncio
from contextlib import asynccontextmanager

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
    policy = OwnerPolicyService(owner_for=reader.owner_for)

    @asynccontextmanager
    async def lifespan(application):
        runtime = None
        application.state.native_context = None
        enabled = os.environ.get("QH_NATIVE_CONTEXT_ENABLED", "false")
        if enabled not in ("true", "false"):
            raise ValueError("QH_NATIVE_CONTEXT_ENABLED must be true or false")
        if enabled == "true":
            from neo4j import GraphDatabase
            from adapters.context.runtime import NativeRuntime

            namespace = os.environ["QH_NATIVE_GRAPH_NAMESPACE"]
            if not namespace.strip():
                raise ValueError("Native graph namespace must be explicit")
            driver = GraphDatabase.driver(
                os.environ["NEO4J_URI"],
                auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
                connection_timeout=5, connection_acquisition_timeout=5,
                max_transaction_retry_time=5,
            )
            runtime = NativeRuntime(
                url=database_url(), driver=driver, policy=policy, namespace=namespace,
            )
            await asyncio.to_thread(runtime.start)
            application.state.native_context = runtime
        try:
            yield
        finally:
            if runtime is not None:
                await asyncio.to_thread(runtime.stop)
                application.state.native_context = None

    return create_app(
        security=SecurityBindings(authenticate=authenticator.authenticate, policy=policy),
        lifespan=lifespan,
    )
