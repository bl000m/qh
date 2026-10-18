"""Offline live-login receipt and file integrity, not a new VPS operation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def main():
    manifest = json.loads((HERE / 'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        path = (HERE / name).resolve()
        assert path.is_relative_to(HERE)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    result = json.loads((HERE / 'results.json').read_text())
    assert all(v == 'PASS' for v in result['live_acceptance']['checks'].values())
    assert result['live_acceptance']['clock_acceleration'] is False
    assert result['live_acceptance']['natural_expiry_wait_seconds'] >= 300
    assert result['live_acceptance']['paid_calls'] == result['live_acceptance']['qh_writes'] == 0
    assert result['restarts'] == result['recreations'] == 0
    assert result['rollback_live_render_verified'] and result['rollback_available']
    assert result['final_realm_settings'] == {
        'loginTheme': 'qh', 'internationalizationEnabled': True,
        'supportedLocales': ['en', 'fr'], 'defaultLocale': 'fr',
    }
    assert all(result['preservation'].values())
    assert not result['merge_or_jira_write']
    for name, digest in result['source_hashes'].items():
        assert hashlib.sha256((REPO / name).read_bytes()).hexdigest() == digest, name
    for name, digest in result['theme_files'].items():
        assert hashlib.sha256((REPO / 'infra/keycloak/themes/qh' / name).read_bytes()).hexdigest() == digest
    print('PASS: sealed actual VPS login, natural expiry, rollback and preserved contracts/data')


if __name__ == '__main__':
    main()
