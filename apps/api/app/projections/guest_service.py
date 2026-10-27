"""Explicit invitation → delivered OTP → limited session; no raw proof persistence."""
from datetime import datetime, timezone
from uuid import uuid4

from app.projections.drafts import identifier
from app.projections.guest_payload import recipient_payload
from app.projections.guest import GuestDenied, GuestRateLimited, GuestSession, GuestSnapshot, GuestUnavailable, Invitation, MailUnavailable


class GuestInvitationService:
    def __init__(self, *, disclosures, repository, proofs, mailer, authorize, clock=None):
        self.disclosures, self.repository, self.proofs = disclosures, repository, proofs
        self.mailer, self.authorize = mailer, authorize
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    async def create(self, subject, scope, snapshot_id):
        snapshot = await self.disclosures.snapshot(subject, scope, snapshot_id)
        if snapshot.policy.expires_at <= self.clock():
            raise GuestDenied('Vérification impossible.')
        token = self.proofs.token()
        row = await self.repository.create(subject, scope, snapshot_id, self.proofs.token_hash(token, 'invitation'))
        return Invitation(id=row['id'], snapshot_id=snapshot_id, expires_at=row['expires_at'], token=token)

    async def list(self, subject, scope):
        await self.disclosures.drafts._allow(subject, scope)
        return await self.repository.list(subject, scope)

    async def revoke(self, subject, scope, invitation_id):
        await self.disclosures.drafts._allow(subject, scope)
        identifier(invitation_id)
        await self.repository.revoke(subject, scope, invitation_id)

    async def _limit(self, peer, phase, maximum):
        if not await self.repository.limit(self.proofs.peer_hash(peer, phase), maximum):
            raise GuestRateLimited('Trop de tentatives. Réessayez plus tard.')

    async def request_code(self, token, email, peer):
        await self._limit(peer, 'request', 10)
        challenge, code = str(uuid4()), self.proofs.code()
        token_hash = self.proofs.token_hash(token, 'invitation')
        delivery = await self.repository.issue(token_hash, email, challenge,
            self.proofs.code_hash(token_hash, challenge, code))
        if delivery is not None:
            sent = False
            try:
                await self.mailer.send(delivery, code)
                sent = True
            except MailUnavailable:
                pass
            await self.repository.delivered(challenge, sent)
        # Same response for unknown link/email, cooldown, send cap and delivery failure.
        return dict(challenge_id=challenge, message='Si cet accès est autorisé, un code a été envoyé à la boîte invitée.')

    async def verify(self, token, challenge_id, code, peer):
        await self._limit(peer, 'verify', 30)
        identifier(challenge_id)
        token_hash = self.proofs.token_hash(token, 'invitation')
        session = self.proofs.token()
        access = await self.repository.verify(token_hash, challenge_id,
            self.proofs.code_hash(token_hash, challenge_id, code), self.proofs.token_hash(session, 'session'))
        if access is None:
            raise GuestDenied('Vérification impossible.')
        right = 'READ' if 'READ' in access.rights else 'ASK_AI'
        if not await self.authorize(access, right):
            raise GuestDenied('Vérification impossible.')
        return GuestSession(access=access, token=session)

    async def session(self, token):
        grant = await self.repository.authenticate(self.proofs.token_hash(token, 'session'))
        if grant is None or grant.expires_at <= self.clock():
            raise GuestDenied('Vérification impossible.')
        right = 'READ' if 'READ' in grant.rights else 'ASK_AI'
        if not await self.authorize(grant, right):
            raise GuestDenied('Vérification impossible.')
        return grant

    async def snapshot(self, token, snapshot_id, right='READ'):
        identifier(snapshot_id)
        grant = await self.session(token)
        if grant.snapshot_id != snapshot_id or right not in ('READ', 'ASK_AI') or not await self.authorize(grant, right):
            raise GuestDenied('Vérification impossible.')
        result = await self.repository.payload(grant, right)
        if (not isinstance(result, GuestSnapshot) or result.context_id != grant.context_id
                or result.snapshot_id != snapshot_id):
            raise GuestUnavailable('Guest access unavailable')
        payload = result.payload
        if not await self.authorize(grant, right):
            raise GuestDenied('Vérification impossible.')
        return recipient_payload(payload, include_quotes=result.include_quotes)

    async def logout(self, token):
        await self.repository.logout(self.proofs.token_hash(token, 'session'))
