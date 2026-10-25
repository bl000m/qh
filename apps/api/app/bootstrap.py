"""Runtime composition root: concrete adapters stay outside the inner modules."""

import os
import time
import asyncio
from contextlib import asynccontextmanager

from adapters.llm.chat_config import ChatConfigurationError, configured_chat_provider
from adapters.llm.session_config import configured_session_factory
from app.review.service import ReviewService
from app.understanding.enrichment import ConversationEnrichment
from adapters.postgres.enrichment import PostgresEnrichmentRepository
from adapters.llm.offline import LiteralSegmentProvider
from adapters.postgres.review import PostgresReviewRepository
from adapters.postgres.environment import PostgresOrganizationRepository
from app.environment.service import EnvironmentService
from app.chat.sessions import ProviderSessions
from app.chat.implementation import ContextualChatService
from adapters.oidc import OIDCAuthenticator, OIDCSettings
from adapters.postgres.config import database_url
from adapters.postgres.security import PostgresSecurityReader
from adapters.postgres.spaces import PostgresContextSpaceRepository
from app.api.security import SecurityBindings
from app.main import create_app
from app.policy.owner import OwnerPolicyService
from app.context.service import ManagedContextService
from app.composition import ApplicationServices
from app.core.models import ContextRetrievalUnavailable


def create_runtime_app():
    # The public mock route must never become an implicit provider-disclosure path.
    if os.environ.get('QH_CHAT_PROVIDER', 'mock') != 'mock':
        raise ChatConfigurationError('Runtime default must be mock; use scoped provider sessions')
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
    running = {}

    def retrieval_for(subject):
        runtime = running.get("runtime")
        if runtime is None:
            raise ContextRetrievalUnavailable("Context retrieval unavailable")
        return runtime.context_for(subject)

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
            running["runtime"] = runtime
        async def purge_diagnostics():
            while True:
                if factory and factory.diagnostics:
                    await asyncio.to_thread(factory.diagnostics.purge_expired)
                await asyncio.sleep(30)
        housekeeping = asyncio.create_task(purge_diagnostics())
        try:
            yield
        finally:
            housekeeping.cancel()
            try:
                await housekeeping
            except asyncio.CancelledError:
                pass
            running.clear()
            if runtime is not None:
                await asyncio.to_thread(runtime.stop)
                application.state.native_context = None

    provider, model = configured_chat_provider()
    context = ManagedContextService(repository=PostgresContextSpaceRepository(url=database_url()),
                                    policy=policy, retrieval_for=retrieval_for)
    chat = ContextualChatService(context=context, policy=policy,
                                 provider=provider, model=model, clock=time.perf_counter)
    binding=os.environ.get('QH_CHAT_SESSION_BINDING','credential')
    if binding not in ('credential','oidc'):
        raise ChatConfigurationError('Invalid chat session binding')
    factory = configured_session_factory()
    sessions = ProviderSessions(chat=chat, factory=factory, clock=time.time, session_binding=binding=='oidc')
    enrichment = ConversationEnrichment(context=context, policy=policy,
        repository_for=lambda subject: PostgresEnrichmentRepository(url=database_url(), subject_id=subject,
            connection_options='-c statement_timeout=5000 -c lock_timeout=5000'),
        provider=LiteralSegmentProvider(), uum=True)
    from app.chat.development import DevelopmentAI
    automatic = DevelopmentAI(chat=chat, enrichment=enrichment, factory=factory, clock=time.time) if factory and factory.development_account else None
    return create_app(
        services=ApplicationServices(
            context=context,
            enrichment=enrichment, development_ai=automatic,
            review=ReviewService(context=context, policy=policy, repository=PostgresReviewRepository(url=database_url())),
            environment=EnvironmentService(repository=PostgresOrganizationRepository(url=database_url()), policy=policy, context=context),
            chat=chat, chat_sessions=sessions,
            policy=policy,
        ),
        security=SecurityBindings(authenticate=authenticator.authenticate, policy=policy,
                                  authenticate_with_expiry=authenticator.authenticate_with_expiry,
                                  authenticate_session=authenticator.authenticate_session),
        lifespan=lifespan,
    )
