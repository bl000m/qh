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


def test_sharing_output_redacts_invitation_otp_email_and_verifier_key():
    sanitize = runpy.run_path(str(Path('/workspace/scripts/test_qh11_browser.py')))['sanitized_output']
    cleaned = sanitize('/guest#invite=private-invitation code 12345678 clement@example.test private-key',
                       {'QH_SHARING_VERIFIER_KEY': 'private-key'})
    for value in ['private-invitation', '12345678', 'clement@example.test', 'private-key']:
        assert value not in cleaned
    assert '/guest#invite=' in cleaned
