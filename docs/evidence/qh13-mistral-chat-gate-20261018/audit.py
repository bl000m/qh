"""Audit the sealed synthetic proposal; never call a provider or read secrets."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      allow_nan=False, separators=(',', ':')).encode()


def main():
    raw = (ROOT / 'manifest.json').read_bytes()
    manifest = json.loads(raw)
    assert sha(raw) == (ROOT / 'manifest.sha256').read_text().split()[0]
    assert not manifest['owner_authorized'] and not manifest['disclosure_consent']
    assert manifest['observed_api_cost'] is None
    assert manifest['observed_api_input_tokens'] is None
    assert manifest['observed_api_output_tokens'] is None
    assert manifest['ledger_initial_blocked'] and manifest['ledger_initial_calls'] == 0
    assert manifest['no_automatic_retries'] and manifest['one_space_per_request']
    assert manifest['max_total_attempts'] == 4 <= manifest['existing_absolute_attempt_cap'] == 8
    assert manifest['metadata_request']['ledger_attempts'] == 1
    assert manifest['planned_paid_chat_requests'] == len(manifest['requests']) == 3
    language = manifest['language']
    for kind in ('active', 'candidate'):
        data = (ROOT / language[kind + '_system_file']).read_bytes()
        assert sha(data) == language[kind + '_system_sha256']
    candidate = (ROOT / language['candidate_system_file']).read_text()
    scopes = set()
    for entry in manifest['requests']:
        payload = json.loads((ROOT / entry['payload_file']).read_text())
        assert sha(canonical(payload)) == entry['canonical_payload_sha256']
        assert payload['model'] == manifest['model'] == 'mistral-small-2603'
        assert payload['max_tokens'] == manifest['max_output_tokens'] == 1000
        assert payload['stream'] is False and payload['tool_choice'] == 'none'
        messages = payload['messages']
        assert [m['role'] for m in messages] == ['system', 'user', 'user']
        assert messages[0]['content'] == candidate
        assert messages[2]['content'] == entry['question']
        pairs = [(m['role'], m['content']) for m in messages]
        assert sha(json.dumps(pairs, ensure_ascii=False, separators=(',', ':')).encode()) == entry['request_sha256']
        context_bytes = messages[1]['content'].encode()
        assert sha(context_bytes) == entry['context_sha256']
        assert len(context_bytes) == entry['context_bytes'] <= manifest['context_bytes_cap'] == 8000
        bound = sum(len(m['content'].encode()) + 256 for m in messages)
        assert bound == entry['candidate_input_bound'] <= manifest['input_bound_cap'] == 12000
        packet = json.loads(context_bytes)
        assert packet['format'] == 'qh.chat.context/1' and not packet['partial_coverage']
        assert packet['context_space_id'] == entry['context_id']
        assert entry['context_id'] not in scopes
        scopes.add(entry['context_id'])
        rows = []
        for packed in packet['revisions']:
            assert not packet['common_metadata'].keys() & packed.keys()
            row = deepcopy(packet['common_metadata'] | packed)
            row['provenance'] = [deepcopy(packet['sources'][ref]) for ref in row['provenance']]
            assert row['context_space_id'] == entry['context_id']
            assert row['validation_state'] == 'proposed' and row['is_current_confirmed'] is False
            assert row['current_revision_id'] is None
            assert row['validated_by'] is None and row['validated_at'] is None
            assert all(s['source_revision_id'] in entry['source_revision_ids'] for s in row['provenance'])
            rows.append(row)
        assert len(rows) == 6 and [r['revision_id'] for r in rows] == entry['revision_ids']
        assert sha(canonical(rows)) == entry['canonical_records_sha256']
        assert sorted(packet['sources']) == entry['source_revision_ids']
    prices = manifest['prices_usd_per_million']
    per_chat = (Decimal(12000) * Decimal(prices['input']) + Decimal(1000) * Decimal(prices['output'])) / Decimal(1000000)
    assert per_chat == Decimal(manifest['maximum_per_chat_reservation_usd'])
    total = per_chat * 3
    assert total == Decimal(manifest['planned_three_chat_reservation_usd']) <= Decimal(manifest['max_usd']) == Decimal('.20')
    fx = Decimal(manifest['eur_per_usd_upper_bound'])
    assert total * fx == Decimal(manifest['planned_eur_at_upper_bound'])
    assert Decimal(manifest['max_usd']) * fx <= Decimal(manifest['max_owner_eur']) == Decimal('5')
    print('PASS: sealed manifest, three exact scoped six-record payloads, hashes, states and reservation; no network/approval/inference')


if __name__ == '__main__':
    main()
