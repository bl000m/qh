"""Cryptographic token validation and HTTP enforcement; no demo auth."""

import asyncio
import time

from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends
from fastapi.testclient import TestClient
import httpx
import jwt
import pytest

from adapters.oidc import (
    GeneralPermissionDenied, IdentityUnavailable, InvalidCredentials,
    OIDCAuthenticator, OIDCSettings,
)
from app.api.security import SecurityBindings, require_context_owner
from app.core.models import SubjectId
from app.main import create_app
from app.policy.owner import OwnerPolicyService

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
SETTINGS = OIDCSettings(issuer="https://idp.example/realms/qh", jwks_url="https://idp.example/certs")
QH_ALICE, QH_BOB = SubjectId("qh-alice"), SubjectId("qh-bob")


def token(**changes):
    values = {"iss": SETTINGS.issuer, "sub": "external-alice", "aud": "qh-api",
              "iat": int(time.time()) - 10, "exp": int(time.time()) + 300,
              "nbf": int(time.time()) - 10, "scope": "openid qh:api",
              "realm_access": {"roles": ["qh-user"]}}
    values.update(changes)
    return jwt.encode(values, KEY, algorithm="RS256", headers={"kid": "current"})


def build_auth(*, mapping=None, handler=None, settings=SETTINGS, resolver=None):
    calls = []
    async def resolve(issuer, subject):
        calls.append((issuer, subject))
        if resolver is not None:
            return await resolver(issuer, subject)
        return (mapping if mapping is not None else {"external-alice": QH_ALICE}).get(subject)
    def jwks(request):
        assert str(request.url) == SETTINGS.jwks_url
        key = jwt.algorithms.RSAAlgorithm.to_jwk(KEY.public_key(), as_dict=True)
        return httpx.Response(200, json={"keys": [dict(key, kid="current", use="sig", alg="RS256")]})
    return OIDCAuthenticator(settings=settings, resolve_identity=resolve,
                             transport=httpx.MockTransport(handler or jwks)), calls


@pytest.mark.parametrize("changes", [
    {"iss": "https://wrong.example"}, {"aud": "other-api"}, {"exp": 1},
    {"nbf": lambda: int(time.time()) + 600}, {"iat": lambda: int(time.time()) + 600},
    {"sub": ""}, {"sub": 123}, {"exp": None}, {"aud": None},
])
def test_invalid_claims_fail_before_identity_lookup(changes):
    # A long full-suite run must not age a collection-time future claim into validity.
    changes = {key: value() if callable(value) else value for key, value in changes.items()}
    auth, calls = build_auth()
    with pytest.raises(InvalidCredentials):
        asyncio.run(auth.authenticate(token(**changes)))
    assert calls == []


@pytest.mark.parametrize("value", [
    "false", "",
    jwt.encode({"sub": "external-alice"}, "test-only-key", algorithm="HS256", headers={"kid": "current"}),
    jwt.encode({"sub": "external-alice"}, OTHER_KEY, algorithm="RS256", headers={"kid": "current"}),
    jwt.encode({"sub": "external-alice"}, KEY, algorithm="RS256", headers={"kid": "unknown"}),
])
def test_invalid_signatures_algorithms_and_kids(value):
    auth, calls = build_auth()
    with pytest.raises(InvalidCredentials):
        asyncio.run(auth.authenticate(value))
    assert calls == []


@pytest.mark.parametrize("changes", [{"scope": "openid"}, {"realm_access": {"roles": []}},
                                    {"scope": []}, {"realm_access": None}])
def test_general_gate_precedes_qh_identity(changes):
    auth, calls = build_auth()
    with pytest.raises(GeneralPermissionDenied):
        asyncio.run(auth.authenticate(token(**changes)))
    assert calls == []


def test_verified_identity_uses_issuer_and_subject_only():
    auth, calls = build_auth()
    assert asyncio.run(auth.authenticate(token(user_id="qh-bob", email="bob@example.invalid"))) == QH_ALICE
    assert calls == [(SETTINGS.issuer, "external-alice")]


def test_unmapped_identity_is_denied():
    auth, _ = build_auth(mapping={})
    with pytest.raises(InvalidCredentials):
        asyncio.run(auth.authenticate(token()))


def test_jwks_failure_is_unavailable_and_never_resolves_identity():
    auth, calls = build_auth(handler=lambda request: httpx.Response(503))
    with pytest.raises(IdentityUnavailable):
        asyncio.run(auth.authenticate(token()))
    assert calls == []


def test_unknown_kid_refresh_is_bounded_and_rotation_is_supported():
    requests = []
    def handler(request):
        requests.append(request)
        key = jwt.algorithms.RSAAlgorithm.to_jwk(KEY.public_key(), as_dict=True)
        return httpx.Response(200, json={"keys": [dict(key, kid="rotated", alg="RS256", use="sig")]})
    auth, _ = build_auth(handler=handler)
    rotated = jwt.encode(jwt.decode(token(), options={"verify_signature": False}), KEY,
                         algorithm="RS256", headers={"kid": "rotated"})
    async def exercise():
        assert await auth.authenticate(rotated) == QH_ALICE
        for _ in range(4):
            with pytest.raises(InvalidCredentials):
                await auth.authenticate(token())
        auth._refreshed -= 301
        assert await auth.authenticate(rotated) == QH_ALICE
    asyncio.run(exercise())
    assert len(requests) == 2


def test_test_only_private_routes_enforce_owner_before_read():
    auth, _ = build_auth(mapping={"external-alice": QH_ALICE, "external-bob": QH_BOB})
    async def owner_for(space):
        return {"A": QH_ALICE, "B": QH_BOB}.get(space)
    app = create_app(security=SecurityBindings(authenticate=auth.authenticate,
                          policy=OwnerPolicyService(owner_for=owner_for)))
    reads = []
    @app.get("/test/private/{context_id}")
    async def private(context_id: str, subject=Depends(require_context_owner)):
        reads.append(context_id)
        return {"content": context_id}
    with TestClient(app) as client:
        alice = {"Authorization": "Bearer " + token()}
        bob = {"Authorization": "Bearer " + token(sub="external-bob")}
        assert client.get("/auth/me", headers=alice).json() == {"user_id": QH_ALICE}
        assert client.get("/auth/me", headers=bob).json() == {"user_id": QH_BOB}
        assert client.get("/test/private/A", headers=alice).status_code == 200
        assert client.get("/test/private/B", headers=bob).status_code == 200
        for headers, denied in [(alice, "B"), (bob, "A"), (alice, "missing")]:
            response = client.get("/test/private/" + denied, headers=headers)
            assert response.status_code == 403 and response.json() == {"detail": "Access denied"}
        for headers in ({}, {"X-User-ID": QH_ALICE}, {"Authorization": "Bearer false"}):
            assert client.get("/test/private/A?user_id=qh-alice", headers=headers).status_code == 401
        assert client.get("/auth/me", headers={"Authorization": "Bearer " + token(scope="openid")}).status_code == 403
        assert client.get("/auth/me", headers=[("Authorization", alice["Authorization"]),
                                              ("Authorization", bob["Authorization"])]).status_code == 401
    assert reads == ["A", "B"]
    assert all(not route.path.startswith("/test/") and "/access" not in route.path
               for route in create_app().routes)


def test_unconfigured_authentication_is_closed_but_health_works():
    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/auth/me").status_code == 401
        assert client.get("/auth/me", headers={"Authorization": "Bearer " + token()}).status_code == 503


@pytest.mark.parametrize("changes", [{"iss": "wrong"}, {"aud": "wrong"}, {"exp": 1},
                                    {"nbf": int(time.time()) + 600}])
def test_http_rejects_invalid_tokens_with_401(changes):
    auth, calls = build_auth()
    async def owner_for(space):
        pytest.fail("Owner lookup must not occur before authentication")
    app = create_app(security=SecurityBindings(authenticate=auth.authenticate,
                    policy=OwnerPolicyService(owner_for=owner_for)))
    with TestClient(app) as client:
        response = client.get("/auth/me", headers={"Authorization": "Bearer " + token(**changes)})
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"
    assert calls == []


def test_token_jku_cannot_select_a_jwks_endpoint():
    auth, _ = build_auth()
    claims = jwt.decode(token(), options={"verify_signature": False})
    value = jwt.encode(claims, KEY, algorithm="RS256",
                       headers={"kid": "current", "jku": "https://attacker.example/certs"})
    assert asyncio.run(auth.authenticate(value)) == QH_ALICE
