"""Explicit backend-only chat provider selection. Key presence never enables HTTP.

No receipts/ledgers are created here. Mistral activation needs separately authorized,
private existing files, verified pricing and exchange ceiling; no startup API call.
"""
from datetime import datetime, timezone
from decimal import Decimal
import json
import os
from pathlib import Path

from adapters.llm.chat_mock import MockChatProvider
from adapters.llm.mistral import ExperimentBudget, MistralProvider, MODEL, INPUT_USD_PER_M, OUTPUT_USD_PER_M


class ChatConfigurationError(RuntimeError):
    pass


def private_json(path):
    p = Path(path)
    if not p.is_file() or p.stat().st_mode & 0o077:
        raise ChatConfigurationError('Private existing chat authorization/ledger required')
    return json.loads(p.read_text())


class ScopedMistralChatProvider:
    def __init__(self, *, authorization_path, ledger_path, transport=None):
        try:
            receipt = private_json(authorization_path)
            now = datetime.now(timezone.utc)
            expires = datetime.fromisoformat(receipt['expires_at'])
            verified = datetime.fromisoformat(receipt['pricing_verified_at'])
            fx = Decimal(receipt['eur_per_usd_upper_bound'])
            if (receipt['purpose'] != 'QH-13 contextual chat' or receipt['model'] != MODEL
                or receipt['owner_authorized'] is not True or type(receipt['context_ids']) is not list or not receipt['context_ids']
                or not all(isinstance(x,str) and x for x in receipt['context_ids'])
                or expires <= now or verified > now or (now-verified).total_seconds() > 86400
                or (expires-verified).total_seconds() > 86400
                or not fx.is_finite() or not 0 < fx <= 25
                or Decimal(receipt['input_usd_per_million']) != INPUT_USD_PER_M
                or Decimal(receipt['output_usd_per_million']) != OUTPUT_USD_PER_M):
                raise ValueError()
            # Existing stricter experiment envelope: <=8 attempts / <=0.20 USD.
            # With the explicitly verified FX ceiling this cannot reserve >5 EUR.
            state = private_json(ledger_path)
            if not 1 <= state['max_calls'] <= 8 or not Decimal('0') < Decimal(state['max_usd']) <= Decimal('0.20'):
                raise ValueError()
            self.context_ids, self.expires, self.ledger_path = frozenset(receipt['context_ids']), expires, Path(ledger_path)
            self.provider = MistralProvider(budget=ExperimentBudget(ledger_path),
                max_input_tokens=12000, max_output_tokens=1000, transport=transport)
        except Exception:
            raise ChatConfigurationError('Chat authorization, pricing, key or ledger invalid') from None

    async def generate(self, request):
        try:
            scope = json.loads(request.messages[1].content)['context_space_id']
        except (IndexError,KeyError,ValueError,TypeError):
            raise ChatConfigurationError('Explicit authorized chat scope required') from None
        if scope not in self.context_ids or datetime.now(timezone.utc) >= self.expires:
            raise ChatConfigurationError('Chat disclosure grant unavailable')
        try:
            return await self.provider.generate(request)
        finally:
            # Do not keep web-request prompts or raw response bodies in a shared adapter.
            self.provider.last_exchange = None
            self.provider.last_request = None
            if self.provider.last_failure:
                self.provider.last_failure.pop('message', None)



def configured_chat_provider():
    mode = os.environ.get('QH_CHAT_PROVIDER', 'mock')
    if mode == 'mock':
        return MockChatProvider(), 'qh-mock-extractive/1'
    if mode == 'mistral':
        return ScopedMistralChatProvider(
            authorization_path=os.environ.get('QH_CHAT_AUTHORIZATION_FILE', ''),
            ledger_path=os.environ.get('QH_CHAT_LEDGER_FILE', '')), MODEL
    raise ChatConfigurationError('Unsupported chat provider; no fallback')
