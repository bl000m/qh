"""Offline hero checkpoint integrity; no runtime or provider access."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def main():
    manifest = json.loads((HERE / 'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        path = (HERE / name).resolve()
        assert path.is_relative_to(HERE)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    results = json.loads((HERE / 'results.json').read_text())
    receipt = results['receipt']
    assert receipt['browser_filter'] is None
    assert receipt['qh_login_theme_locale'] == 'fr'
    for key in ['browser_and_contract_checks', 'existing_real_oidc_regression',
                'real_graph_outage', 'synthetic_backup_restore_rebuild_browser']:
        assert receipt[key] == 'PASS', key
    assert not receipt['live_qh_access'] and receipt['paid_calls'] == 0
    assert all(results['preservation'].values())
    assert not results['merge_or_jira_write'] and not results['vps_theme_activation']
    for name, digest in results['source_hashes'].items():
        assert hashlib.sha256((REPO / name).read_bytes()).hexdigest() == digest, name
    for directory, digest in results['prior_manifest_hashes'].items():
        path = HERE.parent / directory
        assert hashlib.sha256((path / 'manifest.json').read_bytes()).hexdigest() == digest
        for name, expected in json.loads((path / 'manifest.json').read_text())['files'].items():
            assert hashlib.sha256((path / name).read_bytes()).hexdigest() == expected, name
    subprocess.run([sys.executable, str(HERE.parent / 'qh43-branding-checkpoint-20261018/audit.py'),
                    '--check-current-assets'], check=True)
    print('PASS: sealed hero/capsule captures, source identity, previous archives and preservation')


if __name__ == '__main__':
    main()
