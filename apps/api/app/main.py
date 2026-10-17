from fastapi import FastAPI

from app.api.health import router as health_router
from app.composition import ApplicationServices
from app.api.auth import router as auth_router
from app.api.security import SecurityBindings
from app.api.context_spaces import router as spaces_router
from app.api.context_query import router as query_router
from app.api.context_browse import router as browse_router


def create_app(*, services: ApplicationServices | None = None,
               security: SecurityBindings | None = None, lifespan=None) -> FastAPI:
    """Compose the HTTP adapter with explicitly supplied application services.

    Health runs without business services; unbound authentication fails closed. Future business
    routes must require explicit bindings rather than silently installing fake
    or concrete adapters. This factory does not create any outbound adapter.
    """
    application = FastAPI(title="QH API", version="0.1.0", lifespan=lifespan)
    if services is not None and security is not None and services.policy is not security.policy:
        raise ValueError("Application and security must share the same PolicyService")
    application.state.services = services
    application.state.security = security
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(spaces_router)
    application.include_router(query_router)
    application.include_router(browse_router)
    return application


app = create_app()
