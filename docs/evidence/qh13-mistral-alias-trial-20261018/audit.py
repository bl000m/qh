"""Offline-only integrity, exact alias resolution and ledger-lineage audit."""
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
    gate_dir = ROOT.parent / 'qh13-mistral-alias-gate-20261018'
    assert sha((gate_dir / 'manifest.json').read_bytes()) == manifest['approved_manifest_sha256']
    gate = json.loads((gate_dir / 'manifest.json').read_text())
    request = read('project/request.json')
    assert sha(canonical(request)) == gate['canonical_payload_sha256']
    assert request == json.loads((gate_dir / gate['payload_file']).read_text())
    assert request['model'] == gate['model'] == 'mistral-small-2603'
    assert sha(request['messages'][0]['content'].encode()) == gate['system_sha256']
    assert request['messages'][-1]['content'] == gate['question']
    packet = json.loads(request['messages'][1]['content'])
    assert packet['format'] == 'qh.chat.context/2'
    assert packet['context_space_id'] == gate['context_id'] and not packet['partial_coverage']
    rows = read('project/provided-revisions.json')
    assert sha(canonical(rows)) == gate['canonical_records_sha256']
    assert rows == json.loads((gate_dir / gate['canonical_records_file']).read_text())
    expanded = []
    for packed in packet['revisions']:
        assert not packet['common_metadata'].keys() & packed.keys()
        row = packet['common_metadata'] | packed
        row['provenance'] = [packet['sources'][ref] for ref in row['provenance']]
        expanded.append(row)
    assert expanded == rows and len(rows) == 6
    assert all(r['validation_state'] == 'proposed' and not r['is_current_confirmed']
               and r['context_space_id'] == gate['context_id'] for r in rows)
    aliases = {f'R{i}': ref for i, ref in enumerate(sorted(r['revision_id'] for r in rows), 1)}
    assert aliases == packet['allowed_reference_aliases']
    assert aliases == json.loads((gate_dir / gate['aliases_file']).read_text())
    raw = read('project/raw-response.json')
    assert raw['choices'][0]['message']['content'].encode() == (ROOT / 'project/output.json').read_bytes()
    assert raw['model'] == gate['model'] and raw['choices'][0]['finish_reason'] == 'stop'
    output = read('project/output.json')
    assert set(output) == {'answer', 'reference_aliases', 'insufficient_context'}
    refs = output['reference_aliases']
    assert len(refs) == len(set(refs)) == 6 and all(ref in aliases for ref in refs)
    assert not output['insufficient_context']
    assert read('project/alias-resolution.json') == {ref: aliases[ref] for ref in refs}
    qh = read('project/qh-response.json')
    assert qh['http_status'] == 200
    body = qh['body']
    assert body['answer'] == output['answer'] and body['model'] == raw['model']
    assert body['provided_revisions'] == rows and not body['partial_coverage']
    indexed = {row['revision_id']: row for row in rows}
    assert body['references'] == [indexed[aliases[ref]] for ref in refs]
    # The deterministic UI predicates are true, irrespective of generated prose.
    assert any(r['validation_state'] == 'proposed' for r in body['references'])
    assert body['provided_revisions'] and all(r['validation_state'] == 'proposed'
                                            for r in body['provided_revisions'])
    summary = read('results.json')
    assert summary['actual_attempts'] == summary['post_requests'] == 1
    assert summary['get_requests'] == summary['automatic_retries'] == 0
    assert summary['provider_http_status'] == summary['qh_http_status'] == 200
    assert summary['observed_invoice_charge'] is None and not summary['public_live_provider_session']
    assert body['context_bytes'] == gate['context_bytes']
    assert body['input_bound'] == gate['input_bound']
    usage = raw['usage']
    assert usage['prompt_tokens'] == summary['observed_prompt_tokens'] == 3609
    assert usage['completion_tokens'] == summary['observed_completion_tokens'] == 101
    assert usage['prompt_tokens'] + usage['completion_tokens'] == usage['total_tokens'] == 3710
    estimate = (Decimal(usage['prompt_tokens']) * Decimal('.15')
                + Decimal(usage['completion_tokens']) * Decimal('.60')) / 1_000_000
    before, after = read('ledger-before.json'), read('ledger-after.json')
    assert before['calls'] == [] and before['blocked'] and after['blocked']
    assert after['max_calls'] == before['max_calls'] == 1
    assert after['max_usd'] == before['max_usd'] == '0.01'
    assert after['parent'] == before['parent'] == gate['parent']
    assert len(after['calls']) == 1 and after['calls'][0]['status'] == 'completed'
    assert after['calls'][0]['usage'] == {k: usage[k] for k in ('prompt_tokens', 'completion_tokens')}
    assert estimate == Decimal(summary['estimated_list_price_usd']) == Decimal(after['calls'][0]['observed_usd'])
    assert estimate <= Decimal(after['calls'][0]['reserved_usd']) <= Decimal(after['max_usd'])
    assert len(after['authorizations']) == len(after['closures']) == 1
    assert after['authorizations'][0]['calls_retained'] == 0
    assert after['closures'][0]['calls_retained'] == 1
    parent = json.loads((gate_dir / gate['parent']['ledger_file']).read_text())
    assert sha(canonical(parent)) == gate['parent']['state_sha256']
    assert len(parent['calls']) == 2 and parent['blocked']
    assert estimate + Decimal(gate['parent']['estimated_spend_usd']) == Decimal(summary['cumulative_estimated_list_price_usd'])
    mock = read('project/mock-comparison.json')
    assert mock['status'] == 200 and mock['response']['model'] == 'qh-mock-extractive/1'
    assert mock['response']['provided_revisions'] == rows
    preservation = read('preservation.json')
    assert preservation['fourteen_tables_identical'] and preservation['table_count'] == 14
    assert preservation['env_realm_identical'] and preservation['six_container_configuration_identities_identical']
    assert preservation['canonical_writes'] == 0 and preservation['historical_private_ledger_byte_identical']
    assert preservation['temporary_secret_links_removed'] and preservation['public_provider_always_mock']
    assessment = read('assessment.json')
    assert assessment['human_validation'] is False
    assert assessment['proposed_confirmed']['verdict'] == 'PARTIAL'
    assert assessment['reference_usefulness']['verdict'] == 'PARTIAL'
    print('PASS: one sealed POST, exact six alias/canonical resolutions, QH 200, original output, observed usage, estimated cost, closed linked ledger and unchanged persistent/runtime state; no network')


if __name__ == '__main__':
    main()
