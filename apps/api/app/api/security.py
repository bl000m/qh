"""Inbound authentication and resource authorization, explicitly bound."""

from dataclasses import dataclass
import hashlib
from typing import Awaitable, Callable

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from adapters.oidc import GeneralPermissionDenied, IdentityUnavailable, InvalidCredentials
from app.core.models import ContextId, SubjectId
from app.policy.models import PolicyAction, PolicyRequest
from app.policy.services import PolicyService


@dataclass(frozen=True)
class SecurityBindings:
    authenticate: Callable[[str], Awaitable[SubjectId]]
    policy: PolicyService
    authenticate_with_expiry: Callable[[str], Awaitable[tuple[SubjectId, float]]] | None = None


bearer = HTTPBearer(auto_error=False)


async def authenticated_subject(request: Request,
                                credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> SubjectId:
    if credentials is None or len(request.headers.getlist("authorization")) != 1:
        raise HTTPException(401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
    bindings = request.app.state.security
    if bindings is None:
        raise HTTPException(503, "Identity service unavailable")
    try:
        return await bindings.authenticate(credentials.credentials)
    except InvalidCredentials:
        raise HTTPException(401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"}) from None
    except GeneralPermissionDenied:
        raise HTTPException(403, "General access denied") from None
    except IdentityUnavailable:
        raise HTTPException(503, "Identity service unavailable") from None


async def require_context_owner(request: Request, context_id: str,
                                subject: SubjectId = Depends(authenticated_subject)) -> SubjectId:
    try:
        decision = await request.app.state.security.policy.evaluate(PolicyRequest(
            subject_id=subject, action=PolicyAction.READ_CONTEXT,
            context_ids=(ContextId(context_id),),
        ))
    except IdentityUnavailable:
        raise HTTPException(503, "Identity service unavailable") from None
    if not decision.allowed:
        raise HTTPException(403, "Access denied")
    return subject


async def authenticated_chat_identity(request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    """Same OIDC verifier, exposing only verified expiry and a token binding hash."""
    from app.chat.sessions import ChatIdentity
    if credentials is None or len(request.headers.getlist('authorization')) != 1:
        raise HTTPException(401, 'Invalid credentials')
    security = request.app.state.security
    if security is None or security.authenticate_with_expiry is None:
        raise HTTPException(503, 'Verified identity expiry unavailable')
    try:
        subject, expiry = await security.authenticate_with_expiry(credentials.credentials)
    except InvalidCredentials:
        raise HTTPException(401, 'Invalid credentials') from None
    except GeneralPermissionDenied:
        raise HTTPException(403, 'General access denied') from None
    except IdentityUnavailable:
        raise HTTPException(503, 'Identity service unavailable') from None
    return ChatIdentity(subject, expiry, hashlib.sha256(credentials.credentials.encode()).hexdigest())
