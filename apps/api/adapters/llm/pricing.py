"""Public official USD list-price verification; never sends a key or QH data."""
import asyncio
from decimal import Decimal
import hashlib
import json
import re
import time

import httpx

from adapters.llm.mistral import MODEL, INPUT_USD_PER_M, OUTPUT_USD_PER_M

PRICE_URL = 'https://docs.mistral.ai/models/mistral-small-4-0-26-03'
MAX_AGE = 86400
MAX_BYTES = 2_000_000


def parse_prices(html):
    if MODEL not in html or 'Mistral Small 4' not in html:
        raise ValueError('Pinned model absent')
    found = []
    for match in re.finditer(r'self\.__next_f\.push\((.*?)\)</script>', html):
        chunk = json.loads(match[1])
        if not isinstance(chunk, list) or len(chunk) != 2 or not isinstance(chunk[1], str):
            continue
        if re.search(r'"isRetired":\s*true', chunk[1]):
            raise ValueError('Retired model')
        for price in re.finditer(r'"pricing":', chunk[1]):
            value, _ = json.JSONDecoder().raw_decode(chunk[1][price.end():].lstrip())
            if not isinstance(value, dict):
                continue
            if value.get('type') != 'custom' or value.get('free') is not False:
                raise ValueError('Unknown pricing basis')
            amounts = []
            for name, ceiling in [('input', INPUT_USD_PER_M), ('output', OUTPUT_USD_PER_M)]:
                rows = value[name]
                if len(rows) != 1 or set(rows[0]) != {'type', 'price', 'denominator'}:
                    raise ValueError('Unrecognized price tiers')
                row = rows[0]
                if type(row['price']) not in (int, float):
                    raise ValueError('Invalid numeric price')
                amount = Decimal(str(row['price']))
                if (row['type'] != 'range' or row['denominator'] != '/M Tokens'
                        or not amount.is_finite() or not 0 < amount <= ceiling):
                    raise ValueError('Price ceiling exceeded')
                amounts.append(str(amount))
            found.append(tuple(amounts))
    if not found or len(set(found)) != 1:
        raise ValueError('Missing or conflicting pricing')
    return found[0]


class OfficialPricing:
    def __init__(self, *, transport=None, clock=time.time):
        self.transport, self.clock = transport, clock
        self.receipt = None
        self.last_failure = None
        self.lock = asyncio.Lock()

    async def verify(self):
        async with self.lock:
            now = self.clock()
            if self.receipt and 0 <= now-self.receipt['verified_at'] < MAX_AGE:
                return True
            self.receipt = None
            if self.last_failure is not None and 0 <= now-self.last_failure < 60:
                return False
            try:
                async with httpx.AsyncClient(transport=self.transport or httpx.AsyncHTTPTransport(retries=0),
                        timeout=httpx.Timeout(10, connect=5), follow_redirects=False, trust_env=False) as client:
                    async with client.stream('GET', PRICE_URL, headers={'Accept': 'text/html'}) as response:
                        if response.status_code != 200 or 'text/html' not in response.headers.get('content-type', ''):
                            raise ValueError('Official price source unavailable')
                        data = bytearray()
                        async for block in response.aiter_bytes():
                            data.extend(block)
                            if len(data) > MAX_BYTES:
                                raise ValueError('Price page bound exceeded')
                incoming, outgoing = parse_prices(data.decode('utf-8'))
                self.receipt = dict(source=PRICE_URL, model=MODEL, verified_at=self.clock(),
                    sha256=hashlib.sha256(data).hexdigest(), input_usd_per_million=incoming,
                    output_usd_per_million=outgoing)
                self.last_failure = None
                return True
            except Exception:
                self.last_failure = self.clock()
                return False
