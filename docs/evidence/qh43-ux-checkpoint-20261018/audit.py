"""Offline artifact consistency; no network, provider, database or consent changes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    results = json.loads((ROOT / 'results.json').read_text())
    final = results['final_isolated_run']
    assert final['frontend_browser_contracts_passed'] == 43 and final['harness_exit_code'] == 0
    assert final['oidc_passed'] == final['oidc_deselected'] == 1
    assert final['graph_outage_run_passed'] == 3 and final['restored_browser_run_passed'] == 1
    assert final['counts_overlap_do_not_sum'] and final['dump_restore_tables_match']
    assert final['graph_rebuild_canonical_tables_match']
    assert results['live']['result'] == 'PASS' and results['live']['bob_denials'] == 6
    assert len(results['live']['cases']) == 3
    assert all(c['provided'] == 6 and c['model'] == 'qh-mock-extractive/1'
               for c in results['live']['cases'])
    assert results['live_reflow']['reflow'] == 'PASS'
    assert results['live_reflow']['offscreen_elements'] == []
    assert not results['branding_applied'] and not results['theme_prepared']
    assert not results['theme_activated'] and results['paid_provider_calls'] == 0
    assets = json.loads((ROOT / 'asset-inventory.json').read_text())
    assert len(assets['original_files']) == 7 and not assets['svg_logo_present']
    assert sum(f.get('format') == 'PNG' for f in assets['original_files']) == 5
    assert assets['pdf']['pages'] == 24 and not assets['public_asset_imported']
    assert not assets['theme_prepared']
    preservation = json.loads((ROOT / 'preservation.json').read_text())
    assert preservation['fourteen_qh_tables_identical']
    assert preservation['six_container_identities_configurations_and_start_times_identical']
    assert preservation['env_realm_ledgers_identical'] and preservation['original_asset_hashes_unchanged']
    assert preservation['canonical_writes'] == preservation['paid_provider_calls'] == 0
    for png in ROOT.glob('screenshots/*.png'):
        assert png.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    print('PASS: sealed QH-43 functional results/screenshots, source hashes, private-asset inventory and preserved runtime; branding/theme gates remain open')


if __name__ == '__main__':
    main()
