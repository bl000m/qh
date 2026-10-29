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
from adapters.postgres.connections import runtime_connections
from adapters.postgres.security import PostgresSecurityReader
from adapters.postgres.spaces import PostgresContextSpaceRepository
from app.api.security import SecurityBindings
from app.main import create_app
from app.policy.owner import OwnerPolicyService
from app.context.service import ManagedContextService
from app.composition import ApplicationServices
from app.core.models import ContextRetrievalUnavailable


def create_sharing_runtime_app():
    """Explicit owner-enabled private deployment, never the default factory."""
    from adapters.sharing import private_sharing_settings
    return create_runtime_app(guest_settings=private_sharing_settings())


def create_runtime_app(*, guest_settings=None):
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
    guest_repository = None
    guest_http = None
    if guest_settings is not None:
        from adapters.postgres.guest import PostgresGuestRepository
        from adapters.guest_security import SecureGuestProofs
        from app.api.guest import GuestHTTPConfig
        SecureGuestProofs(guest_settings.verifier_key)
        guest_http=GuestHTTPConfig(origin=guest_settings.origin)
        guest_repository=PostgresGuestRepository(url=database_url())
    policy = OwnerPolicyService(owner_for=reader.owner_for,
        guest_for=guest_repository.guest_for if guest_repository else None)
    running = {}

    def retrieval_for(subject):
        runtime = running.get("runtime")
        if runtime is None:
            raise ContextRetrievalUnavailable("Context retrieval unavailable")
        return runtime.context_for(subject)

    @asynccontextmanager
    async def lifespan(application):
        # Dispose after request/worker shutdown, also when startup fails.
        with runtime_connections(database_url()):
            async with application_lifespan(application):
                yield

    @asynccontextmanager
    async def application_lifespan(application):
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
        if guest_settings is not None:
            try:
                if runtime is None or runtime.schema_version not in ('0009_guest_invitations','0010_context_consolidation'):
                    raise RuntimeError('Explicit sharing bindings require reviewed schema 0009')
                from adapters.sharing import bind_sharing
                application.state.services=bind_sharing(application.state.services,runtime,guest_repository,guest_settings,factory=factory)
            except Exception:
                running.clear()
                if runtime is not None:await asyncio.to_thread(runtime.stop)
                application.state.native_context=None
                raise
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
    from app.understanding.consolidation import ContextConsolidation
    from adapters.postgres.consolidation import PostgresConsolidationRepository
    from adapters.pdf import extract_pdf
    consolidation = ContextConsolidation(context=context, policy=policy, ai=automatic, pdf_parser=extract_pdf,
        repository_for=lambda subject: PostgresConsolidationRepository(url=database_url(), subject_id=subject,
            connection_options='-c statement_timeout=5000 -c lock_timeout=5000'))
    return create_app(
        services=ApplicationServices(
            context=context,
            enrichment=enrichment, development_ai=automatic, consolidation=consolidation,
            review=ReviewService(context=context, policy=policy, repository=PostgresReviewRepository(url=database_url())),
            environment=EnvironmentService(repository=PostgresOrganizationRepository(url=database_url()), policy=policy, context=context),
            chat=chat, chat_sessions=sessions,
            policy=policy,
        ),
        security=SecurityBindings(authenticate=authenticator.authenticate, policy=policy,
                                  authenticate_with_expiry=authenticator.authenticate_with_expiry,
                                  authenticate_session=authenticator.authenticate_session),
        lifespan=lifespan,guest_http=guest_http,
    )
