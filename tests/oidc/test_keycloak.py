"""Real Keycloak Authorization Code/PKCE and HTTP/owner/persistence integration."""

import base64
import hashlib
from html.parser import HTMLParser
import os
import secrets
import socket
import subprocess
import sys
import time
from urllib.parse import parse_qs, urlencode, urlparse
from uuid import uuid4

from alembic import command
from fastapi import Depends
from fastapi.testclient import TestClient
import httpx
import jwt
import pytest

from adapters.postgres.demo_identities import DEMO_IDENTITIES, provision_demo
from app.api.security import require_context_owner
from app.bootstrap import create_runtime_app
from tests.oidc_database import connect, isolated_database

pytestmark = pytest.mark.skipif(os.environ.get("QH_RUN_OIDC") != "1", reason="Run make test-oidc")
ISSUER = os.environ.get("OIDC_ISSUER", "http://localhost:8080/realms/qh")
INTERNAL = "http://keycloak:8080"


class LoginForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.action = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form" and attrs.get("id") == "kc-form-login":
            self.action = attrs["action"]


def internal_url(value):
    parsed = urlparse(value)
    assert parsed.netloc == urlparse(ISSUER).netloc
    return INTERNAL + parsed.path + ("?" + parsed.query if parsed.query else "")


def login(username, password):
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(24)
    redirect = "http://localhost:" + os.environ.get("FRONTEND_PORT", "5173") + "/oidc/callback"
    query = urlencode({"client_id": "qh-web", "redirect_uri": redirect, "response_type": "code",
                       "scope": "openid qh:api", "state": state,
                       "code_challenge": challenge, "code_challenge_method": "S256"})
    with httpx.Client(timeout=10, follow_redirects=False) as client:
        response = client.get(INTERNAL + "/realms/qh/protocol/openid-connect/auth?" + query)
        assert response.status_code == 200, "OIDC authorization page unavailable"
        form = LoginForm()
        form.feed(response.text)
        assert form.action, "Expected Keycloak login form"
        response = client.post(internal_url(form.action), data={"username": username, "password": password})
        assert response.status_code == 302, "OIDC login did not complete"
        callback = response.headers["location"]
        assert callback.startswith(redirect + "?"), "Unexpected callback"
        parameters = parse_qs(urlparse(callback).query)
        assert parameters["state"] == [state]
        assert "error" not in parameters
        response = client.post(INTERNAL + "/realms/qh/protocol/openid-connect/token", data={
            "grant_type": "authorization_code", "client_id": "qh-web",
            "code": parameters["code"][0], "redirect_uri": redirect, "code_verifier": verifier,
        })
        assert response.status_code == 200, "PKCE token exchange failed"
        return response.json()["access_token"]


def test_real_oidc_login_mapping_and_owner_isolation():
    with isolated_database() as config:
        command.upgrade(config, "head")
        spaces = [uuid4(), uuid4()]
        with connect() as connection:
            provision_demo(connection, issuer=ISSUER)
            provision_demo(connection, issuer=ISSUER)
            for space, identity in zip(spaces, DEMO_IDENTITIES):
                connection.execute("INSERT INTO context_spaces (id,owner_id,name) VALUES (%s,%s,'Private')",
                                   (space, identity[1]))
        # Actual production composition with real JWKS and PostgreSQL adapters.
        application = create_runtime_app()
        assert "/context-spaces/{id}/access" not in application.openapi()["paths"]
        assert set(application.openapi()["paths"]) == {"/health", "/auth/me"}
        reads = []
        @application.get("/test/private/{context_id}")
        async def private(context_id: str, subject=Depends(require_context_owner)):
            reads.append(context_id)
            return {"private": context_id}
        tokens = [login("alice", os.environ["QH_ALICE_PASSWORD"]),
                  login("bob", os.environ["QH_BOB_PASSWORD"])]
        for token, identity in zip(tokens, DEMO_IDENTITIES):
            claims = jwt.decode(token, options={"verify_signature": False})
            assert claims["iss"] == ISSUER
            assert "qh-api" in ([claims["aud"]] if isinstance(claims["aud"], str) else claims["aud"])
            assert claims["sub"] == identity[2], "Imported demo subject differs from configured mapping"
        with TestClient(application) as client:
            for index, (token, identity) in enumerate(zip(tokens, DEMO_IDENTITIES)):
                headers = {"Authorization": "Bearer " + token, "X-User-ID": str(DEMO_IDENTITIES[1-index][1])}
                assert client.get("/auth/me?user_id=spoof", headers=headers).json() == {"user_id": str(identity[1])}
                own = str(spaces[index])
                assert client.get("/test/private/" + own, headers=headers).status_code == 200
                foreign = client.get("/test/private/" + str(spaces[1-index]), headers=headers)
                missing = client.get("/test/private/" + str(uuid4()), headers=headers)
                assert foreign.status_code == missing.status_code == 403
                assert foreign.json() == missing.json() == {"detail": "Access denied"}
            assert client.get("/auth/me").status_code == 401
            assert client.get("/auth/me", headers={"Authorization": "Bearer false"}).status_code == 401
            assert client.get("/test/private/" + str(spaces[0])).status_code == 401
        assert reads == list(map(str, spaces))
        # New app/authenticator proves the identity is persisted, not in-memory.
        with TestClient(create_runtime_app()) as client:
            assert client.get("/auth/me", headers={"Authorization": "Bearer " + tokens[0]}).json() == {
                "user_id": str(DEMO_IDENTITIES[0][1])}
        # Exercise the same production factory over TCP, with the isolated DB.
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.bootstrap:create_runtime_app", "--factory",
             "--host", "127.0.0.1", "--port", str(port)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 15
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=5) as client:
                while True:
                    assert server.poll() is None, "Isolated HTTP server failed to start"
                    try:
                        if client.get("/health").status_code == 200:
                            break
                    except httpx.ConnectError:
                        pass
                    assert time.monotonic() < deadline, "Isolated HTTP server not ready"
                    time.sleep(0.1)
                for token, identity in zip(tokens, DEMO_IDENTITIES):
                    response = client.get("/auth/me", headers={"Authorization": "Bearer " + token})
                    assert response.status_code == 200
                    assert response.json() == {"user_id": str(identity[1])}
                assert client.get("/auth/me").status_code == 401
                assert client.get("/test/private/anything").status_code == 404
        finally:
            server.terminate()
            server.wait(timeout=10)
        with connect() as connection:
            assert connection.execute("SELECT count(*) FROM users").fetchone() == (2,)
            assert connection.execute("SELECT count(*) FROM user_identities").fetchone() == (2,)
