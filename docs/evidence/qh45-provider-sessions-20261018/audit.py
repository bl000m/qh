"""Offline QH-45 receipt integrity; does not authenticate, mutate or call providers."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    manifest = json.loads((HERE / 'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        path = (HERE / name).resolve()
        assert path.is_relative_to(HERE) and path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    for name, digest in manifest['source_hashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    proposal = HERE.parent / 'qh45-session-proposal-20261018'
    for name, digest in json.loads((proposal / 'manifest.json').read_text())['files'].items():
        assert hashlib.sha256((proposal / name).read_bytes()).hexdigest() == digest, name
    browser = json.loads((HERE / 'browser-receipt.json').read_text())
    assert browser['paid_calls'] == 0 and browser['live_qh_access'] is False
    assert browser['qh45_http_simulated_sessions'] and not browser['published_ports']
    assert all(browser[k] == 'PASS' for k in ['browser_and_contract_checks',
        'existing_real_oidc_regression', 'real_graph_outage', 'synthetic_backup_restore_rebuild_browser'])
    live = json.loads((HERE / 'vps-readonly.json').read_text())
    assert all(live[k] == 0 for k in ['paid_calls', 'canonical_writes', 'configuration_writes'])
    assert all(live[k] == 'PASS' for k in ['alice_three_caps_disabled', 'bob_three_caps_denied',
                                        'mock_six_proposed', 'real_ui_unavailable'])
    results = json.loads((HERE / 'results.json').read_text())
    assert all(results['preservation'].values())
    assert results['real_mistral_requests'] == 0 and not results['merge_or_jira_done']
    assert results['native']['verdict'] == 'PASS' and results['native']['skips'] == 0
    print('PASS: sealed offline QH-45 sessions, exact source fingerprints, VPS disabled and preserved data/ledgers')


if __name__ == '__main__':
    main()
