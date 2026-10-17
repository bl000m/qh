"""Browser failures must not echo credentials/tokens/callback values into CI."""
from pathlib import Path
import runpy


def test_child_output_redacts_credentials_and_oidc_values():
    sanitize = runpy.run_path(str(Path('/workspace/scripts/test_qh11_browser.py')))['sanitized_output']
    text = 'fill("ephemeral-password"); Bearer eyJhbGci.testpayload.testsignature /oidc/callback?code=code-value&state=state-value; /api/context-spaces'
    cleaned = sanitize(text, {'QH_ALICE_PASSWORD': 'ephemeral-password'})
    for value in ['ephemeral-password', 'eyJhbGci.testpayload.testsignature', 'code-value', 'state-value']:
        assert value not in cleaned
    assert '/api/context-spaces' in cleaned
