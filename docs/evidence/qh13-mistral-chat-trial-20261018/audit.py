"""Pure offline audit of original first-chat evidence and fail-closed stop."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text())


def sha(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      allow_nan=False, separators=(',', ':')).encode()


def main():
    manifest = read('manifest.json')
    for name, digest in manifest['files'].items():
        assert sha((ROOT / name).read_bytes()) == digest, name
    gate_path = ROOT.parent / 'qh13-mistral-chat-gate-20261018/manifest.json'
    assert sha(gate_path.read_bytes()) == manifest['approved_manifest_sha256']
    gate = json.loads(gate_path.read_text())
    summary = read('results.json')
    assert summary['actual_attempts'] == 2 and summary['get_requests'] == summary['post_requests'] == 1
    assert summary['automatic_retries'] == 0 and summary['ledger_blocked']
    assert all(c['status'] == 'NOT_EXECUTED_STOP_AFTER_PROJECT' for c in summary['cases'][1:])
    assert all(c['usage'] is c['latency'] is c['cost'] is None for c in summary['cases'][1:])
    request = read('project/request.json')
    assert sha(canonical(request)) == gate['requests'][0]['canonical_payload_sha256']
    packet = json.loads(request['messages'][1]['content'])
    rows = read('project/provided-revisions.json')
    expanded = []
    for packed in packet['revisions']:
        row = packet['common_metadata'] | packed
        row['provenance'] = [packet['sources'][ref] for ref in row['provenance']]
        expanded.append(row)
    assert expanded == rows and len(rows) == 6
    assert sha(canonical(rows)) == gate['requests'][0]['canonical_records_sha256']
    assert all(r['validation_state'] == 'proposed' and not r['is_current_confirmed'] for r in rows)
    raw = read('project/raw-response.json')
    assert raw['choices'][0]['message']['content'].encode() == (ROOT / 'project/output.json').read_bytes()
    assert raw['choices'][0]['finish_reason'] == 'stop' and raw['model'] == gate['model']
    answer = read('project/output.json')
    revision_ids = {r['revision_id'] for r in rows}
    item_ids = {r['item_id'] for r in rows}
    assert len(answer['revision_ids']) == 4
    assert len(set(answer['revision_ids']) & revision_ids) == 1
    assert len(set(answer['revision_ids']) & item_ids) == 3
    assert not set(answer['revision_ids']) <= revision_ids
    assert read('project/qh-response.json') == {'http_status': 503, 'body': {'detail': 'Chat unavailable; no automatic retry'}}
    before, after = read('ledger-before.json'), read('ledger-after.json')
    assert before['calls'] == [] and before['blocked'] and after['blocked']
    assert after['max_calls'] == before['max_calls'] == 4
    assert len(after['calls']) == 2 and all(c['status'] == 'completed' for c in after['calls'])
    assert len(after['authorizations']) == 1 and after['authorizations'][0]['calls_retained'] == 0
    usage = raw['usage']
    assert usage['prompt_tokens'] + usage['completion_tokens'] == usage['total_tokens']
    assert usage['prompt_tokens'] == summary['observed_prompt_tokens'] == 3251
    assert usage['completion_tokens'] == summary['observed_completion_tokens'] == 234
    estimate = (Decimal(3251) * Decimal('.15') + Decimal(234) * Decimal('.60')) / 1000000
    assert estimate == Decimal(summary['estimated_list_price_usd']) == Decimal(after['calls'][1]['observed_usd'])
    assert estimate <= Decimal(after['calls'][1]['reserved_usd']) <= Decimal(after['max_usd'])
    mock = read('project/mock-comparison.json')['response']
    assert mock['model'] == 'qh-mock-extractive/1' and len(mock['provided_revisions']) == 6
    assert all(r['revision_id'] in revision_ids for r in mock['references'])
    preservation = read('preservation.json')
    assert preservation['fourteen_tables_identical'] and preservation['env_realm_identical']
    assert preservation['six_container_configuration_identities_identical'] and preservation['canonical_writes'] == 0
    print('PASS: sealed original response/request, 3 wrong-kind IDs, QH rejection, observed usage, estimated cost, blocked 2/4 ledger and preservation; no network')


if __name__ == '__main__':
    main()
