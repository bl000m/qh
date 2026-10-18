"""Offline artifact audit, not browser execution or owner acceptance."""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        target = (ROOT / name).resolve()
        assert target.is_relative_to(ROOT), name
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, name
    result = json.loads((ROOT / 'results.json').read_text())
    for name, expected in result['layout']['after'].items():
        before = result['layout']['before'][name]
        assert expected['question_y'] < before['question_y']
        assert expected['scroll_width'] == expected['viewport']
        for phase in ('before', 'after'):
            data = (ROOT / 'screenshots' / (phase + '-' + name + '.png')).read_bytes()
            assert data.startswith(b'\x89PNG\r\n\x1a\n')
            assert struct.unpack('>I', data[16:20])[0] == expected['viewport']
    assert min(result['live_accessibility']['textarea_and_placeholder_contrast']) >= 4.5
    assert result['live_reflow']['offscreen_elements'] == []
    assert result['live']['bob_denials'] == 6 and len(result['live']['cases']) == 3
    assert all(c['provided'] == 6 and c['model'] == 'qh-mock-extractive/1' for c in result['live']['cases'])
    assert result['final_isolated_run']['browser_and_contract_checks'] == 'PASS'
    assert result['final_isolated_run']['real_graph_outage'] == 'PASS'
    assert result['final_isolated_run']['synthetic_backup_restore_rebuild_browser'] == 'PASS'
    assert all(result['preservation'].values())
    assert result['public_brand_derivatives'] == result['paid_calls'] == result['canonical_writes'] == 0
    assert not result['theme_prepared'] and not result['theme_activated']
    assert not result['logo_selected'] and not result['public_asset_rights_confirmed']
    print('PASS: sealed comparisons, result receipts and preservation; logo/rights/theme/owner gates remain open')


if __name__ == '__main__':
    main()
