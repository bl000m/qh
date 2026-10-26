"""Opt-in deployment cannot read a public, symlinked or malformed verifier file."""
import os
from unittest.mock import patch

import pytest

from adapters.sharing import private_sharing_settings


@pytest.mark.parametrize('kind',['valid','public','short','symlink'])
def test_private_verifier_binding(tmp_path,monkeypatch,kind):
    path=tmp_path/'verifier.key';path.write_bytes(b'x'*(31 if kind=='short' else 32));path.chmod(0o644 if kind=='public' else 0o600)
    if kind=='symlink':
        target=tmp_path/'target';path.rename(target);path.symlink_to(target)
    monkeypatch.setenv('QH_SHARING_ORIGIN','https://localhost:5173')
    with patch('adapters.sharing.Path',return_value=path):
        if kind!='valid':
            with pytest.raises(ValueError):private_sharing_settings()
        else:
            result=private_sharing_settings()
            assert result.origin==os.environ['QH_SHARING_ORIGIN']
            assert 'xxxxxxxx' not in repr(result)
