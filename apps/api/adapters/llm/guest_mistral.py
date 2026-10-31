"""Pinned guest inference uses the existing owner aggregate ledger, no retrieval."""
from decimal import Decimal

from app.core.models import ProviderBudgetExceeded
from app.projections.disclosure import LIVE_PROVIDER
from app.projections.guest import GuestDenied,GuestUnavailable
from app.chat.snapshot_answer import SnapshotAnswerError
from adapters.llm.mistral import MODEL
from app.chat.guest_context import clarification

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

    async def _available(self,owner,scope):
        if not self.allowed(owner,scope):raise GuestDenied('Vérification impossible.')
        remaining=self.factory.remaining()
        if Decimal(remaining['remaining_usd'])<self.factory.reservation_usd:raise ProviderBudgetExceeded()
        if remaining['blocked'] or not await self.factory.verified(owner,scope):raise GuestUnavailable('Verified provider unavailable')

    async def answer_payload(self,owner,scope,payload,question,recheck,history=None,conversation=None):
        from app.chat.guest_context import ordinal_focus
        from app.chat.selection import (selection_request,decode_selection,composition_request,
            decode_composition,SelectionError,unavailable,response_language)
        diagnostics=[];diagnostic=None;language=response_language(question);insufficient=False
        async def exchange(request,phase,decode):
            nonlocal diagnostic
            await self._available(owner,scope)
            await recheck()
            diagnostic=self.factory.diagnostic_call(owner,scope,'guest_chat')
            diagnostics.append(diagnostic)
            result=await self.factory.bind_global(diagnostic=diagnostic).generate(request)
            value=decode(result.message)
            diagnostic.check('guest.'+phase+'_authorized_supports',True)
            if not self.allowed(owner,scope):raise GuestDenied('Vérification impossible.')
            await recheck()
            diagnostic.finish('accepted','guest_'+phase)
            return value
        try:
            focus=ordinal_focus(question,conversation or [])
            if focus==[]:
                await recheck()
                return clarification(question)
            if focus:
                groups=[focus]
            else:
                plan=await exchange(selection_request(payload,question,history,conversation=conversation),'selection',
                    lambda message:decode_selection(message,payload,question))
                language=plan['language'];groups=plan['groups'];insufficient=plan['insufficient_context']
                if not groups:
                    value=unavailable(language,ordering=plan.get('ordering_unknown',False))
                    if plan['operation']=='clarify':
                        value.update(support_basis='dialogue',insufficient_context=plan['insufficient_context'])
                    return self._result(value,diagnostics)
            coverage=dict(available_subjects=len(groups),missing_requested_context=True) if insufficient else None
            value=await exchange(composition_request(payload,question,groups,language=language if not focus else None,coverage=coverage),'composition',
                lambda message:decode_composition(message,payload,groups))
            value['insufficient_context']=value['insufficient_context'] or insufficient
            return dict(self._result(value,diagnostics),budget=await self.status(owner,scope))
        except (GuestDenied,ProviderBudgetExceeded):
            if diagnostic:diagnostic.finish('rejected','guest_access_or_budget')
            raise
        except Exception as exc:
            if diagnostic:
                reason=exc.code if isinstance(exc,SnapshotAnswerError) else str(exc) if isinstance(exc,SelectionError) else type(exc).__name__
                diagnostic.check('guest.snapshot_answer_return',False,reason)
                diagnostic.finish('rejected','guest_snapshot_return')
            if isinstance(exc,SelectionError):
                await recheck()
                return self._result(unavailable(language),diagnostics)
            if isinstance(exc,SnapshotAnswerError) and exc.code in ('guest.internal_structure_in_answer','guest.unbound_list'):
                await recheck()
                return self._result(clarification(question),diagnostics)
            raise GuestUnavailable('Snapshot answer unavailable') from None

    @staticmethod
    def _result(value,diagnostics):
        summaries=[d.accounting_summary for d in diagnostics if d.accounting_summary]
        accounting=None
        if summaries:
            accounting=dict(summaries[-1],cost_usd=str(sum((Decimal(s['cost_usd']) for s in summaries),Decimal(0))),
                usage={key:sum(s['usage'][key] for s in summaries) for key in ('prompt_tokens','completion_tokens')})
        return dict(value,simulated=False,model=MODEL,accounting=accounting)
