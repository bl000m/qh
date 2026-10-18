"""Offline final-review evidence integrity; no runtime access or acceptance claim."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        target = (ROOT / name).resolve()
        assert target.is_relative_to(ROOT)
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, name
    results = json.loads((ROOT / 'results.json').read_text())
    receipt = results['receipt']
    assert receipt['qh_login_theme_preview'] and receipt['qh_login_theme_locale'] == 'fr'
    assert receipt['browser_filter'] == 'source-only QH login theme|selected original mark'
    assert results['targeted_browser_count'] == 2
    for key in ['browser_and_contract_checks', 'existing_real_oidc_regression',
                'real_graph_outage', 'synthetic_backup_restore_rebuild_browser']:
        assert receipt[key] == 'PASS', key
    assert not receipt['live_qh_access'] and receipt['paid_calls'] == 0
    assert all(results['preservation'].values())
    assert not results['theme_activated_on_vps'] and not results['merge_or_jira_write']
    for name, digest in results['unchanged_runtime_source_hashes'].items():
        assert hashlib.sha256((REPO / name).read_bytes()).hexdigest() == digest, name
    subprocess.run([sys.executable, str(ROOT.parent / 'qh43-branding-checkpoint-20261018/audit.py'),
                    '--check-current-assets'], check=True)
    print('PASS: sealed French preview, inherited OIDC, selected assets and final preservation evidence')


if __name__ == '__main__':
    main()
