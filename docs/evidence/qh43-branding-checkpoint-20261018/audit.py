"""Offline selected-asset integrity, not owner acceptance or a browser rerun."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

ARTIFACTS = Path(__file__).resolve().parent
REPO = ARTIFACTS.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-current-assets', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((ARTIFACTS / 'manifest.json').read_text())
    for name, expected in manifest['files'].items():
        target = (ARTIFACTS / name).resolve()
        assert target.is_relative_to(ARTIFACTS) and digest(target) == expected, name
    assets = json.loads((ARTIFACTS / 'asset-manifest.json').read_text())
    assert not assets['full_pdf_or_mockups_published'] and not assets['theme_activated_on_vps']
    results = json.loads((ARTIFACTS / 'results.json').read_text())
    assert results['full_run']['browser_count'] == 48
    assert results['full_run']['receipt']['qh_login_theme_preview']
    assert results['ready_capture_run']['receipt']['browser_filter'] == 'one approved identity'
    for run in ['full_run', 'ready_capture_run']:
        receipt = results[run]['receipt']
        for key in ['browser_and_contract_checks', 'existing_real_oidc_regression',
                    'real_graph_outage', 'synthetic_backup_restore_rebuild_browser']:
            assert receipt[key] == 'PASS', key
        assert receipt['live_qh_access'] is False and receipt['paid_calls'] == 0
    assert results['live']['bob_denials'] == 6 and len(results['live']['cases']) == 3
    assert all(results['preservation'].values())
    if args.check_current_assets:
        for asset in assets['files']:
            path = (REPO / asset['path']).resolve()
            assert path.is_relative_to(REPO) and digest(path) == asset['sha256'], asset['path']
            if path.suffix == '.png':
                assert struct.unpack('>II', path.read_bytes()[16:24]) == (asset['width'], asset['height'])
        frontend = REPO / 'apps/web/src/brand'
        theme = REPO / 'infra/keycloak/themes/qh/login/resources/img'
        for name in ['qh-logo.png', 'qh-bubble.png']:
            assert (frontend / name).read_bytes() == (theme / name).read_bytes()
        assert (theme / 'favicon.ico').read_bytes()[22:] == (frontend / 'qh-icon.png').read_bytes()
    print('PASS: sealed selected-logo/bubble/icon evidence; VPS theme activation and owner review remain gated')


if __name__ == '__main__':
    main()
