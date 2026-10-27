"""Pinned guest inference uses the existing owner aggregate ledger, no retrieval."""
from decimal import Decimal

from app.core.models import ProviderBudgetExceeded
from app.projections.disclosure import LIVE_PROVIDER
from app.projections.guest import GuestDenied,GuestUnavailable
from app.chat.snapshot_answer import decode_snapshot_answer, projection_request
from adapters.llm.mistral import MODEL

AUTHORIZATION=dict(owner_authorized=True,environment='private-development',model=MODEL,
    scope='owned-approved-snapshots',verification='otp')



class MistralSnapshotAnswers:
    def __init__(self,factory):
        if factory is None or not factory.poc or factory.diagnostics is None or LIVE_PROVIDER!=MODEL:
            raise ValueError('Approved shared development budget required')
        self.factory=factory

    def allowed(self,owner,scope):
        from adapters.llm.chat_config import private_json
        try:
            receipt=private_json(self.factory.authorization_path)
            return (receipt.get('guest_snapshot_access')==AUTHORIZATION and self.factory.development_account
                and owner==self.factory.development_account['subject_id'] and self.factory.allowed(owner,scope))
        except Exception:return False

    async def status(self,owner,scope):
        if not self.allowed(owner,scope):return dict(enabled=False,simulated=False,model=MODEL,remaining_usd=None)
        remaining=self.factory.remaining()
        return dict(enabled=await self.factory.available(owner,scope),simulated=False,model=MODEL,
            remaining_usd=remaining['remaining_usd'],plafond_reached=not remaining['blocked'] and Decimal(remaining['remaining_usd'])<self.factory.reservation_usd,
            authorized_total_eur='10.00',budget_scope='development_global')

    async def respond(self,grant,payload,question,recheck):
        return await self.answer_payload(grant.owner_id,grant.context_id,payload,question,recheck)

    async def answer_payload(self,owner,scope,payload,question,recheck):
        if not self.allowed(owner,scope):raise GuestDenied('Vérification impossible.')
        remaining=self.factory.remaining()
        if Decimal(remaining['remaining_usd'])<self.factory.reservation_usd:raise ProviderBudgetExceeded()
        if remaining['blocked'] or not await self.factory.verified(owner,scope):raise GuestUnavailable('Verified provider unavailable')
        diagnostic=self.factory.diagnostic_call(owner,scope,'guest_chat')
        try:
            await recheck()  # Revocation/expiry immediately before paid reservation/HTTP.
            provider=self.factory.bind_global(diagnostic=diagnostic)
            result=await provider.generate(projection_request(payload,question))
            value=decode_snapshot_answer(result.message,payload)
            diagnostic.check('guest.snapshot_answer_exact_aliases_and_disclosure',True)
            await recheck()
            diagnostic.check('guest.post_generation_access',True)
            diagnostic.finish('accepted','guest_snapshot_return')
            return dict(**value,simulated=False,model=MODEL,budget=await self.status(owner,scope),accounting=diagnostic.accounting_summary)
        except (GuestDenied,ProviderBudgetExceeded):
            diagnostic.finish('rejected','guest_access_or_budget');raise
        except Exception as exc:
            diagnostic.check('guest.snapshot_answer_return',False,type(exc).__name__)
            diagnostic.finish('rejected','guest_snapshot_return')
            raise GuestUnavailable('Snapshot answer unavailable') from None
