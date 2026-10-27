"""Fail closed on original-source fields outside an explicitly approved snapshot."""
import re

from app.core.uum import PRIMARY_DIMENSIONS
from app.projections.guest import GuestUnavailable


def recipient_payload(payload, *, include_quotes=False):
    try:
        if (not isinstance(payload, dict) or set(payload)-{'format', 'items', 'recap', 'name'}
                or payload.get('format') != 'qh.disclosure/1'
                or not isinstance(payload.get('items'), list) or not 1 <= len(payload['items']) <= 100):
            raise ValueError()
        if 'name' in payload and (not isinstance(payload['name'], str) or not 1<=len(payload['name'])<=256):
            raise ValueError()
        refs = {i['reference'] for i in payload['items']}
        if len(refs) != len(payload['items']):
            raise ValueError()
        for item in payload['items']:
            _item(item, refs, include_quotes)
        if 'recap' in payload:
            recap = payload['recap']
            if (not isinstance(recap, dict) or set(recap) != {'title', 'text'}
                    or not isinstance(recap['title'], str) or not 1 <= len(recap['title'].strip()) <= 120
                    or not isinstance(recap['text'], str) or not 1 <= len(recap['text'].strip()) <= 1500
                    or len(recap['text'].split()) > 100):
                raise ValueError()
    except (ValueError, KeyError, TypeError):
        raise GuestUnavailable('Guest access unavailable') from None
    return payload


def _item(item, refs, include_quotes):
    if (set(item)-{'reference', 'text', 'validation_state', 'origin_kind', 'sources',
            'primary_dimension', 'relation', 'citations'}
            or not re.fullmatch(r'R[1-9][0-9]{0,2}', item['reference'])
            or not isinstance(item['text'], str) or not 1 <= len(item['text']) <= 16000
            or item['validation_state'] not in ('proposed', 'confirmed')
            or 'origin_kind' in item and (not isinstance(item['origin_kind'], str) or len(item['origin_kind']) > 64)
            or not isinstance(item['sources'], list)
            or any(not isinstance(s, str) or not re.fullmatch(r'S[1-9][0-9]{0,4}', s) for s in item['sources'])
            or 'citations' in item and include_quotes is not True):
        raise ValueError()
    if 'primary_dimension' in item:
        primary = item['primary_dimension']
        if (set(primary) != {'value', 'certainty', 'review_state'} or primary['value'] not in PRIMARY_DIMENSIONS
                or primary['certainty'] not in ('asserted', 'tentative') or primary['review_state'] not in ('proposed', 'accepted')):
            raise ValueError()
    if 'relation' in item and (set(item['relation']) != {'source', 'target'}
            or any(r not in refs for r in item['relation'].values())):
        raise ValueError()
    quotes = item.get('citations', [])
    if not isinstance(quotes, list) or len(quotes) > 100:
        raise ValueError()
    for quote in quotes:
        if (set(quote) != {'source', 'quote', 'redacted'} or quote['source'] not in item['sources']
                or not isinstance(quote['quote'], str) or not 1 <= len(quote['quote']) <= 16000
                or type(quote['redacted']) is not bool):
            raise ValueError()
