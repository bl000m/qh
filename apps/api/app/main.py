from fastapi import FastAPI

from app.api.health import router as health_router
from app.composition import ApplicationServices
from app.api.auth import router as auth_router
from app.api.security import SecurityBindings


def create_app(*, services: ApplicationServices | None = None,
               security: SecurityBindings | None = None, lifespan=None) -> FastAPI:
    """Compose the HTTP adapter with explicitly supplied application services.

    Health runs without business services; unbound authentication fails closed. Future business
    routes must require explicit bindings rather than silently installing fake
    or concrete adapters. This factory does not create any outbound adapter.
    """
    application = FastAPI(title="QH API", version="0.1.0", lifespan=lifespan)
    application.state.services = services
    application.state.security = security
    application.include_router(health_router)
    application.include_router(auth_router)
    return application


app = create_app()
