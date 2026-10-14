"""Index guard must reject leaks without reporting the matching values."""

import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "qh_secret_guard", Path(__file__).resolve().parents[2] / "scripts/check_secrets.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


@pytest.mark.parametrize("name", [".env", "apps/api/.env.local", "private.pem", "credentials.json",
                                   "node_modules/file.js", ".local-archive/demo.py", "data/store.db"])
def test_private_files_are_rejected(name):
    assert guard.violations({name: b"harmless content"})


def test_known_local_secret_is_rejected_without_echoing_it():
    secret = b"generated-local-credential-value"
    failures = guard.violations({"config.txt": secret}, local_secrets=(secret,))
    assert failures == [("config.txt", "local secret value in Git index")]
    assert secret.decode() not in repr(failures)


def test_key_and_token_detection():
    for content in [b"-----BEGIN " + b"PRIVATE KEY-----", b"ghp_" + b"a" * 36,
                    b"sk-" + b"a" * 48]:
        assert guard.violations({"config.txt": content})


def test_examples_and_realm_must_use_placeholders():
    realm = {"users": [{"credentials": [{"type": "password", "value": "${QH_ALICE_PASSWORD}"}]}]}
    files = {".env.example": b"POSTGRES_PASSWORD=\nOIDC_AUDIENCE=qh-api\n",
             "infra/keycloak/qh-realm.json": json.dumps(realm).encode()}
    assert not guard.violations(files)
    files[".env.example"] = b"POSTGRES_PASSWORD=unapproved-test-value"
    assert guard.violations(files)
    files[".env.example"] = b"POSTGRES_PASSWORD="
    realm["users"][0]["credentials"][0]["value"] = "unapproved-test-value"
    files["infra/keycloak/qh-realm.json"] = json.dumps(realm).encode()
    assert guard.violations(files)
