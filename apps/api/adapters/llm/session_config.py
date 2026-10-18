"""QH-45 explicit private activation; no HTTP/key use or file creation by default."""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import os

from adapters.llm.chat_config import private_json, ChatConfigurationError
from adapters.llm.mistral import (ExperimentBudget, MistralProvider, MODEL,
                                  INPUT_USD_PER_M, OUTPUT_USD_PER_M)


class SessionBudget:
    """Same durable locked ledger enforces session and aggregate reservations atomically."""
    def __init__(self, ledger, session_id, max_calls, max_usd):
        self.ledger, self.session_id = ledger, session_id
        self.max_calls, self.max_usd = max_calls, max_usd

    def reserve(self, kind, maximum):
        return self.ledger.reserve(kind, maximum, session_id=self.session_id,
            session_max_calls=self.max_calls, session_max_usd=self.max_usd)

    def settle(self, index, **kwargs):
        return self.ledger.settle(index, **kwargs)

    def summary(self):
        def read(state):
            rows = [r for r in state['calls'] if r.get('session_id') == self.session_id]
            return dict(calls=len(rows), committed_usd=str(sum(
                (Decimal(r.get('observed_usd', r['reserved_usd'])) for r in rows), Decimal(0))),
                blocked=state['blocked'] or any(r['status'] == 'pending' for r in state['calls']))
        return self.ledger._change(read)


@dataclass
class SessionProviderBinding:
    provider: object
    budget: SessionBudget

    def summary(self):
        return self.budget.summary()


class PrivateSessionFactory:
    model = MODEL

    def __init__(self, *, authorization_path, ledger_path, transport=None):
        try:
            r = private_json(authorization_path)
            state = private_json(ledger_path)
            now = datetime.now(timezone.utc)
            expires = datetime.fromisoformat(r['expires_at'])
            verified = datetime.fromisoformat(r['pricing_verified_at'])
            fx = Decimal(r['eur_per_usd_upper_bound'])
            if (r['purpose'] != 'QH-45 interactive chat' or r['owner_authorized'] is not True
                or r['model'] != MODEL or expires <= now or verified > now
                or not 0 <= (now - verified).total_seconds() < 86400
                or not 0 < (expires - verified).total_seconds() <= 86400
                or not fx.is_finite() or not 0 < fx <= 25
                or Decimal(r['input_usd_per_million']) != INPUT_USD_PER_M
                or Decimal(r['output_usd_per_million']) != OUTPUT_USD_PER_M
                or state.get('purpose') != 'QH-45 interactive chat'
                or type(state['max_calls']) is not int or not 1 <= state['max_calls'] <= 8
                or not Decimal('0') < Decimal(state['max_usd']) <= Decimal('0.20')):
                raise ValueError()
            grants = r['grants']
            if (not isinstance(grants, list) or not grants or len(grants) > 100
                or any(type(g) is not dict or set(g) != {'subject_id', 'context_id'}
                       or any(not isinstance(v, str) or not v for v in g.values()) for g in grants)):
                raise ValueError()
            self.scopes = frozenset((g['subject_id'], g['context_id']) for g in grants)
            self.expires_at = expires.timestamp()
            self.max_calls = r.get('max_session_calls', 3)
            self.max_usd = r.get('max_session_usd', '0.01')
            if (type(self.max_usd) is not str or type(self.max_calls) is not int or not 1 <= self.max_calls <= state['max_calls']
                or not Decimal('0') < Decimal(self.max_usd) <= Decimal(state['max_usd'])):
                raise ValueError()
            self.ledger = ExperimentBudget(ledger_path)
            self.transport = transport
        except Exception:
            raise ChatConfigurationError('Interactive chat authorization/ledger invalid') from None

    def allowed(self, subject_id, context_id):
        return ((subject_id, context_id) in self.scopes
                and datetime.now(timezone.utc).timestamp() < self.expires_at)

    def bind(self, session_id, *, max_calls, max_usd):
        budget = SessionBudget(self.ledger, session_id, max_calls, max_usd)
        raw = MistralProvider(budget=budget, max_input_tokens=12000,
                             max_output_tokens=1000, transport=self.transport)

        class PrivateProvider:
            async def generate(self, request):
                try:
                    return await raw.generate(request)
                finally:
                    raw.last_request = raw.last_exchange = None
                    if raw.last_failure:
                        raw.last_failure.pop('message', None)

        return SessionProviderBinding(PrivateProvider(), budget)


def configured_session_factory():
    enabled = os.environ.get('QH_CHAT_SESSIONS_ENABLED', 'false')
    if enabled == 'false':
        return None
    if enabled != 'true':
        raise ChatConfigurationError('Explicit session activation required')
    return PrivateSessionFactory(
        authorization_path=os.environ.get('QH_CHAT_SESSION_AUTHORIZATION_FILE', ''),
        ledger_path=os.environ.get('QH_CHAT_SESSION_LEDGER_FILE', ''))
