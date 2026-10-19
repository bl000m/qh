"""QH-45 explicit private activation; no HTTP/key use or file creation by default."""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os

from adapters.llm.pricing import OfficialPricing
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

    def __init__(self, *, authorization_path, ledger_path, transport=None, pricing=None):
        try:
            r = private_json(authorization_path)
            state = private_json(ledger_path)
            now = datetime.now(timezone.utc)
            expires = datetime.fromisoformat(r['expires_at'])
            activated = datetime.fromisoformat(r.get('activated_at', r['pricing_verified_at']))
            fx = Decimal(r['eur_per_usd_upper_bound'])
            if (r['purpose'] != 'QH-45 interactive chat' or r['owner_authorized'] is not True
                or r['model'] != MODEL or expires <= now or activated > now
                or not 0 < (expires - activated).total_seconds() <= 30 * 86400
                or not fx.is_finite() or not 0 < fx <= 25
                or Decimal(r['input_usd_per_million']) != INPUT_USD_PER_M
                or Decimal(r['output_usd_per_million']) != OUTPUT_USD_PER_M
                or state.get('purpose') != 'QH-45 interactive chat'
                or type(state['max_calls']) is not int or not 1 <= state['max_calls'] <= 8
                or not Decimal('0') < Decimal(state['max_usd']) <= Decimal('0.20')):
                raise ValueError()
            grants = r['grants']
            if (not isinstance(grants, list) or not grants or len(grants) > 100
                or any(type(g) is not dict or set(g) not in ({'subject_id', 'context_id'}, {'subject_id', 'context_id', 'snapshot_sha256'})
                       or any(not isinstance(v, str) or not v for v in g.values()) for g in grants)):
                raise ValueError()
            self.authorization_path = authorization_path
            self.authorization_hash = hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest()
            self.snapshots = {(g['subject_id'], g['context_id']): g.get('snapshot_sha256') for g in grants}
            if transport is None and any(not isinstance(v, str) or len(v) != 64 or any(c not in '0123456789abcdef' for c in v) for v in self.snapshots.values()):
                raise ValueError('Live authorization requires exact context snapshots')
            self.pricing = pricing or OfficialPricing()
            self.scopes = frozenset((g['subject_id'], g['context_id']) for g in grants)
            self.expires_at = expires.timestamp()
            self.max_calls = r.get('max_session_calls', 3)
            self.max_usd = r.get('max_session_usd', '0.01')
            if (type(self.max_usd) is not str or type(self.max_calls) is not int or not 1 <= self.max_calls <= min(3, state['max_calls'])
                or not Decimal('0') < Decimal(self.max_usd) <= min(Decimal('0.01'), Decimal(state['max_usd']))):
                raise ValueError()
            self.ledger = ExperimentBudget(ledger_path)
            self.transport = transport
        except Exception:
            raise ChatConfigurationError('Interactive chat authorization/ledger invalid') from None

    def allowed(self, subject_id, context_id):
        try:
            current = private_json(self.authorization_path)
            return ((subject_id, context_id) in self.scopes
                and datetime.now(timezone.utc).timestamp() < self.expires_at
                and hashlib.sha256(json.dumps(current, sort_keys=True).encode()).hexdigest() == self.authorization_hash)
        except Exception:
            return False

    def remaining(self):
        def read(state):
            spent = Decimal(0)
            for row in state['calls']:
                value = Decimal(row.get('observed_usd', row['reserved_usd']))
                if not value.is_finite() or value < 0:
                    raise ValueError('Invalid ledger amounts')
                spent += value
            blocked = state['blocked'] or any(r['status'] == 'pending' for r in state['calls'])
            return dict(remaining_calls=max(0, min(state['max_calls'], 8)-len(state['calls'])),
                remaining_usd=str(max(Decimal(0), min(Decimal(state['max_usd']), Decimal('0.20'))-spent)),
                blocked=blocked)
        return self.ledger._change(read)

    async def verified(self, subject_id, context_id):
        return self.allowed(subject_id, context_id) and await self.pricing.verify()

    async def available(self, subject_id, context_id):
        if not self.allowed(subject_id, context_id):
            return False
        try:
            remaining = self.remaining()
            if remaining['blocked'] or not remaining['remaining_calls'] or Decimal(remaining['remaining_usd']) < Decimal('0.0024'):
                return False
            return await self.pricing.verify()
        except Exception:
            return False

    def accepts_snapshot(self, subject_id, context_id, digest):
        expected = self.snapshots.get((subject_id, context_id))
        return expected is None or expected == digest

    def bind(self, session_id, *, max_calls, max_usd):
        budget = SessionBudget(self.ledger, session_id, max_calls, max_usd)
        raw = MistralProvider(budget=budget, max_input_tokens=12000,
                             max_output_tokens=1000, transport=self.transport)

        checker = self.pricing

        class PrivateProvider:
            async def generate(self, request):
                try:
                    if not await checker.verify():
                        raise ChatConfigurationError('Official price verification unavailable')
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
    authorization_path = os.environ.get('QH_CHAT_SESSION_AUTHORIZATION_FILE', '')
    receipt = private_json(authorization_path)
    if datetime.fromisoformat(receipt['expires_at']) <= datetime.now(timezone.utc):
        return None  # Expired availability never disables the default mock or renews spend.
    return PrivateSessionFactory(
        authorization_path=authorization_path,
        ledger_path=os.environ.get('QH_CHAT_SESSION_LEDGER_FILE', ''))
