"""OIDC resource-server adapter. Only configured JWKS endpoints are contacted."""

import asyncio
import hashlib
import json
from dataclasses import dataclass
import time
from typing import Awaitable, Callable

import httpx
import jwt

from app.core.models import SubjectId


class InvalidCredentials(Exception):
    pass


class GeneralPermissionDenied(Exception):
    pass


class IdentityUnavailable(Exception):
    pass


@dataclass(frozen=True)
class OIDCSettings:
    issuer: str
    jwks_url: str
    audience: str = "qh-api"
    scope: str = "qh:api"
    role: str = "qh-user"


class OIDCAuthenticator:
    def __init__(self, *, settings: OIDCSettings,
                 resolve_identity: Callable[[str, str], Awaitable[SubjectId | None]],
                 transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._settings = settings
        self._resolve = resolve_identity
        self._transport = transport
        self._keys: dict = {}
        self._refreshed = float("-inf")
        self._lock = asyncio.Lock()

    async def _key(self, kid: str):
        async with self._lock:
            now = time.monotonic()
            # Cache five minutes; unknown kids trigger a bounded refresh, not
            # attacker-controlled requests for every fabricated JWT.
            if now - self._refreshed >= 300 or (kid not in self._keys and now - self._refreshed >= 5):
                try:
                    async with httpx.AsyncClient(transport=self._transport, timeout=5,
                                                follow_redirects=False) as client:
                        response = await client.get(self._settings.jwks_url)
                        response.raise_for_status()
                        document = response.json()
                    keys = {}
                    if not isinstance(document, dict) or not isinstance(document.get("keys"), list):
                        raise ValueError("Invalid JWKS")
                    for entry in document["keys"]:
                        if not isinstance(entry, dict):
                            raise ValueError("Invalid JWK")
                        if (entry.get("kty") == "RSA" and entry.get("use", "sig") == "sig"
                                and entry.get("alg", "RS256") == "RS256"):
                            keys[entry["kid"]] = jwt.PyJWK.from_dict(entry).key
                    self._keys, self._refreshed = keys, now
                except (httpx.HTTPError, ValueError, KeyError, TypeError, jwt.PyJWTError):
                    raise IdentityUnavailable("Identity verification unavailable") from None
            if kid not in self._keys:
                raise InvalidCredentials("Invalid credentials")
            return self._keys[kid]

    async def authenticate(self, token: str) -> SubjectId:
        subject, _ = await self.authenticate_with_expiry(token)
        return subject

    async def authenticate_with_expiry(self, token: str) -> tuple[SubjectId, float]:
        verified = await self.authenticate_session(token)
        return verified.subject_id, verified.expires_at

    async def authenticate_session(self, token: str):
        from app.chat.sessions import ChatIdentity
        try:
            if not token or len(token) > 16384:
                raise InvalidCredentials("Invalid credentials")
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
                raise InvalidCredentials("Invalid credentials")
            key = await self._key(header["kid"])
            claims = jwt.decode(
                token, key, algorithms=["RS256"], audience=self._settings.audience,
                issuer=self._settings.issuer,
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
            if type(claims["exp"]) not in (int, float) or not 0 < claims["exp"] < float("inf"):
                raise InvalidCredentials("Invalid credentials")
            if not isinstance(claims["sub"], str) or not claims["sub"].strip():
                raise InvalidCredentials("Invalid credentials")
        except (jwt.PyJWTError, TypeError, ValueError):
            raise InvalidCredentials("Invalid credentials") from None
        scopes = claims.get("scope", "")
        roles = claims.get("realm_access", {})
        roles = roles.get("roles", []) if isinstance(roles, dict) else []
        if (not isinstance(scopes, str) or self._settings.scope not in scopes.split()
                or not isinstance(roles, list) or self._settings.role not in roles):
            raise GeneralPermissionDenied("General access denied")
        subject = await self._resolve(claims["iss"], claims["sub"])
        if subject is None:
            raise InvalidCredentials("Invalid credentials")
        sid,auth_time=claims.get('sid'),claims.get('auth_time')
        binding,work_expiry=None,None
        if (isinstance(sid,str) and 0<len(sid)<=512 and type(auth_time) in (int,float)
                and type(claims['iat']) in (int,float) and 0<auth_time<=time.time() and auth_time<=claims['iat']):
            binding=hashlib.sha256(json.dumps([claims['iss'],claims['sub'],subject,sid],separators=(',',':')).encode()).hexdigest()
            work_expiry=float(auth_time)+8*3600
        return ChatIdentity(subject,float(claims['exp']),hashlib.sha256(token.encode()).hexdigest(),binding,work_expiry)
