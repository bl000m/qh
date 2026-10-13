"""FastAPI composition checks, separate from framework-free contract tests."""

from fastapi.testclient import TestClient

from app.composition import ApplicationServices
from app.main import create_app
from app.policy.models import PolicyDecision
from app.projections.models import ContextProjection
from tests.fakes import (
    GENERATION, ITEM_REVISION, SOURCE_REVISION, RESULT,
    FakeChatService, FakeContextEngine, FakeContextService,
    FakeLLMProvider, FakePolicyService, FakeProjectionService,
)


def test_api_factory_preserves_explicit_service_bindings() -> None:
    services = ApplicationServices(
        context=FakeContextService(FakeContextEngine(RESULT)),
        policy=FakePolicyService(PolicyDecision(allowed=False, reason="test-only")),
        projections=FakeProjectionService(ContextProjection(text="test", item_revisions=(ITEM_REVISION,),
                                                          source_revisions=(SOURCE_REVISION,))),
        chat=FakeChatService(FakeLLMProvider(GENERATION)),
    )
    application = create_app(services=services)
    assert application.state.services is services
    with TestClient(application) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "qh-api"}


def test_health_scaffold_does_not_construct_business_services() -> None:
    application = create_app()
    assert application.state.services is None
    assert {route.path for route in application.routes} == {
        "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc", "/health", "/auth/me",
    }
