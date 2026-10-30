"""Explicitly opt-in HTTPS guest adapter. No proof in URLs or private pre-auth preview."""
import asyncio
from dataclasses import dataclass
import time
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field, StrictStr

from app.api.security import authenticated_subject
from app.projections.drafts import ProjectionNotFound, ProjectionUnavailable
from app.projections.drafts import ProjectionConflict
from app.projections.disclosure import DisclosureDecisionRequired
from app.projections.guest import GuestDenied, GuestRateLimited, GuestUnavailable
from app.core.models import ProviderBudgetExceeded

COOKIE = '__Host-qh_guest'


@dataclass(frozen=True, slots=True, kw_only=True)
class GuestHTTPConfig:
    origin: str
    minimum_response_seconds: float = 0.15

    def __post_init__(self):
        parts = urlsplit(self.origin)
        if (parts.scheme != 'https' or not parts.hostname or parts.username or parts.password
                or parts.path or parts.query or parts.fragment or self.origin.endswith('/')):
            raise ValueError('Exact HTTPS browser origin required')
        if not 0 <= self.minimum_response_seconds <= 1:
            raise ValueError('Bounded response floor required')


class GuestRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()
        async def guarded(request):
            started = time.monotonic()
            try:
                config = request.app.state.guest_http
                if request.url.scheme != 'https':
                    raise HTTPException(403, 'Transport sécurisé requis.')
                if request.query_params:
                    raise HTTPException(400, 'Requête invalide.')
                if request.method not in ('GET', 'HEAD'):
                    if request.headers.get('origin') != config.origin:
                        raise HTTPException(403, 'Requête refusée.')
                    if request.headers.get('content-type', '').split(';')[0] != 'application/json':
                        raise HTTPException(400, 'Requête invalide.')
                    length = request.headers.get('content-length', '')
                    limit=128000 if request.url.path=='/guest/ask' else 4096
                    if not length.isdecimal() or int(length) > limit:
                        raise HTTPException(413, 'Requête invalide.')
                result = await handler(request)
            except RequestValidationError:
                result = JSONResponse(status_code=400, content={'detail': 'Requête invalide.'})
            except GuestDenied:
                result = JSONResponse(status_code=401, content={'detail': 'Vérification impossible.'})
            except GuestRateLimited:
                result = JSONResponse(status_code=429, content={'detail': 'Trop de tentatives.'}, headers={'Retry-After': '60'})
            except ProviderBudgetExceeded:
                result = JSONResponse(status_code=402,content={'detail':'Plafond IA atteint. Aucune nouvelle requête ne sera facturée.'})
            except ProjectionNotFound:
                result = JSONResponse(status_code=404, content={'detail': 'Projection not found'})
            except ProjectionConflict:
                result = JSONResponse(status_code=409, content={'detail': 'La prévisualisation a changé ou expiré. Recommencez.'})
            except (DisclosureDecisionRequired,ValueError):
                result = JSONResponse(status_code=400, content={'detail': 'Décision de divulgation requise ou requête invalide.'})
            except (GuestUnavailable, ProjectionUnavailable):
                result = JSONResponse(status_code=503, content={'detail': 'Guest access unavailable'})
            except HTTPException as error:
                result = JSONResponse(status_code=error.status_code, content={'detail': error.detail}, headers=error.headers)
            result.headers.update({'Cache-Control': 'private, no-store', 'Pragma': 'no-cache',
                'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff'})
            if request.url.path.startswith('/guest/') and request.method == 'POST':
                await asyncio.sleep(max(0, request.app.state.guest_http.minimum_response_seconds-(time.monotonic()-started)))
            return result
        return guarded


router = APIRouter(route_class=GuestRoute, tags=['verified guest'])


class CodeRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    invitation_token: StrictStr = Field(min_length=1, max_length=256)
    email: StrictStr = Field(min_length=1, max_length=254)


class EmptyRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')


class VerifyRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    invitation_token: StrictStr = Field(min_length=1, max_length=256)
    challenge_id: UUID
    code: StrictStr = Field(max_length=64)


def bound(request):
    service=request.app.state.services.guest
    if service is None:raise GuestUnavailable('Guest access unavailable')
    return service


def peer(request):
    # Never use a caller-supplied email, peer ID or X-Forwarded-For as a limiter key.
    return request.client.host if request.client else 'unknown'


def proof(request):
    if sum(h.count(COOKIE+'=') for h in request.headers.getlist('cookie')) != 1:
        raise GuestDenied('Vérification impossible.')
    value = request.cookies.get(COOKIE)
    if not value or len(value) > 256:
        raise GuestDenied('Vérification impossible.')
    return value


async def session_view(request, access, token):
    right='READ' if 'READ' in access.rights else 'ASK_AI'
    payload=await bound(request).snapshot(token, access.snapshot_id, right)
    return dict(name=payload.get('name','Contexte partagé'),can_ask='ASK_AI' in access.rights,
        expires_at=access.expires_at,verification='mailbox_control',
        recap=payload.get('recap') if 'READ' in access.rights else None,
        **({'notice':payload['notice']} if 'notice' in payload else {}),
        **({'semantic_document_count':payload['semantic_document_count']} if 'READ' in access.rights
            and 'semantic_document_count' in payload else {}))


@router.post('/context-spaces/{scope}/snapshots/{snapshot_id}/invitations', status_code=201)
async def create(scope: UUID, snapshot_id: UUID, document: EmptyRequest, request: Request, subject=Depends(authenticated_subject)):
    result = await bound(request).create(subject, str(scope), str(snapshot_id))
    return dict(id=result.id, snapshot_id=result.snapshot_id, expires_at=result.expires_at, invitation_token=result.token)


@router.get('/context-spaces/{scope}/invitations')
async def invitations(scope: UUID, request: Request, subject=Depends(authenticated_subject)):
    return await bound(request).list(subject, str(scope))


@router.post('/context-spaces/{scope}/invitations/{invitation_id}/revoke', status_code=204)
async def revoke(scope: UUID, invitation_id: UUID, document: EmptyRequest, request: Request, subject=Depends(authenticated_subject)):
    await bound(request).revoke(subject, str(scope), str(invitation_id))
    return Response(status_code=204)


@router.post('/guest/code', status_code=202)
async def code(document: CodeRequest, request: Request):
    return await bound(request).request_code(document.invitation_token, document.email, peer(request))


@router.post('/guest/verify')
async def verify(document: VerifyRequest, request: Request, response: Response):
    result = await bound(request).verify(document.invitation_token, str(document.challenge_id), document.code, peer(request))
    # Backend checks expiry/revocation on every request even if a stale cookie remains.
    response.set_cookie(COOKIE, result.token, max_age=1800, expires=result.access.expires_at,
        path='/', secure=True, httponly=True, samesite='strict')
    return await session_view(request,result.access,result.token)


@router.get('/guest/session')
async def session(request: Request):
    return await session_view(request,await bound(request).session(proof(request)),proof(request))


@router.post('/guest/logout', status_code=204)
async def logout(document: EmptyRequest, request: Request, response: Response):
    if request.cookies.get(COOKIE):
        await bound(request).logout(proof(request))
    response.delete_cookie(COOKIE, path='/', secure=True, httponly=True, samesite='strict')
    response.status_code = 204
    return response


@router.get('/guest/documents')
async def documents(request: Request):
    return await bound(request).documents(proof(request))


@router.get('/guest/documents/{revision_id}')
async def document(revision_id: UUID, request: Request):
    from app.api.consolidation import document_response
    return document_response(await bound(request).documents(proof(request),str(revision_id)))
