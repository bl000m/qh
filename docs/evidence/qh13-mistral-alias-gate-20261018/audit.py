"""Offline sealed alias-gate audit; no QH access, consent change or HTTP."""
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
    m = json.loads(raw)
    assert sha(raw) == (ROOT / 'manifest.sha256').read_text().split()[0]
    assert m['owner_authorized'] is False and m['disclosure_consent'] is False
    assert m['observed_api_input_tokens'] is m['observed_api_output_tokens'] is m['observed_api_cost'] is None
    assert m['planned_get_requests'] == 0 and m['planned_post_requests'] == m['max_total_attempts'] == 1
    assert m['no_automatic_retry'] and m['max_usd'] == '0.01'
    payload = json.loads((ROOT / m['payload_file']).read_text())
    assert sha(canonical(payload)) == m['canonical_payload_sha256']
    assert payload['model'] == m['model'] == 'mistral-small-2603'
    assert payload['max_tokens'] == m['max_output_tokens'] == 1000
    assert payload['response_format'] == {'type': 'json_object'}
    assert payload['temperature'] == 0 and payload['random_seed'] == 42
    assert payload['stream'] is False and payload['n'] == 1 and payload['tool_choice'] == 'none'
    messages = payload['messages']
    assert [x['role'] for x in messages] == ['system', 'user', 'user']
    pairs = [(x['role'], x['content']) for x in messages]
    assert sha(json.dumps(pairs, ensure_ascii=False, separators=(',', ':')).encode()) == m['request_sha256']
    system = (ROOT / m['system_file']).read_bytes()
    assert messages[0]['content'].encode() == system and sha(system) == m['system_sha256']
    assert messages[2]['content'] == m['question'] == 'Di che cosa parla questo Context Space?'
    packet = json.loads(messages[1]['content'])
    assert packet['format'] == m['protocol'] == 'qh.chat.context/2'
    assert packet['context_space_id'] == m['context_id'] == 'eb122625-1830-4557-b805-473d3b66132a'
    assert packet['partial_coverage'] is False
    assert len(messages[1]['content'].encode()) == m['context_bytes'] == 6733 <= m['context_bytes_cap'] == 8000
    assert sum(len(x['content'].encode()) + 256 for x in messages) == m['input_bound'] == 9594 <= m['max_input_bound'] == 12000
    rows = []
    for packed in packet['revisions']:
        assert not packet['common_metadata'].keys() & packed.keys()
        row = packet['common_metadata'] | packed
        row['provenance'] = [packet['sources'][ref] for ref in row['provenance']]
        assert row['context_space_id'] == m['context_id']
        assert row['validation_state'] == 'proposed' and row['is_current_confirmed'] is False
        assert row['current_revision_id'] is row['validated_by'] is row['validated_at'] is None
        rows.append(row)
    assert len(rows) == 6 and sha(canonical(rows)) == m['canonical_records_sha256']
    assert rows == json.loads((ROOT / m['canonical_records_file']).read_text())
    aliases = json.loads((ROOT / m['aliases_file']).read_text())
    assert aliases == packet['allowed_reference_aliases']
    assert aliases == {f'R{i}': ref for i, ref in enumerate(sorted(r['revision_id'] for r in rows), 1)}
    assert len(set(aliases.values())) == 6 and sha(canonical(aliases)) == m['aliases_sha256']
    parent = json.loads((ROOT / m['parent']['ledger_file']).read_text())
    assert sha(canonical(parent)) == m['parent']['state_sha256']
    assert parent['blocked'] and len(parent['calls']) == m['parent']['attempts'] == 2
    assert not any(c['status'] == 'pending' for c in parent['calls'])
    previous = sum(Decimal(c.get('observed_usd', c['reserved_usd'])) for c in parent['calls'])
    assert previous == Decimal(m['parent']['estimated_spend_usd'])
    ledger = json.loads((ROOT / 'ledger-proposal.json').read_text())
    assert ledger['blocked'] and ledger['calls'] == [] and ledger['max_calls'] == 1
    assert ledger['max_usd'] == '0.01' and ledger['manifest_sha256'] == sha(raw)
    assert ledger['parent'] == m['parent']
    reserve = (Decimal(12000) * Decimal(m['price_input_usd_per_million']) + Decimal(1000) * Decimal(m['price_output_usd_per_million'])) / 1000000
    assert reserve == Decimal(m['maximum_reservation_usd']) <= Decimal(m['max_usd'])
    assert previous + Decimal(m['max_usd']) <= Decimal(m['existing_usd_cap']) == Decimal('.20')
    assert (previous + Decimal(m['max_usd'])) * Decimal(m['eur_per_usd_upper_bound']) <= Decimal(m['owner_eur_cap'])
    assert m['parent']['attempts'] + m['max_total_attempts'] == m['cumulative']['maximum_attempts_after_trial'] <= m['existing_absolute_attempt_cap']
    print('PASS: sealed one-POST alias payload, exact six canonical records, bijection, unchanged historical snapshot and linked blocked ledger; no network/approval')


if __name__ == '__main__':
    main()
