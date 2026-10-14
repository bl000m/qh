"""Minimum index guard. Report filenames/rules only, never matching values."""

import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DIRECTORIES = {"secrets", ".secrets", ".aws", ".ssh", ".local-archive",
                       "node_modules", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
PRIVATE_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".db", ".sqlite", ".sqlite3", ".dump", ".backup")
PATTERNS = (
    ("private key", re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{36,255}\b")),
    ("LLM API key", re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b")),
)
SECRET_NAME = re.compile(r"(?:^|_)(?:PASSWORD|SECRET|TOKEN|API_KEY)$")
PLACEHOLDER = re.compile(r"\$\{[A-Z_][A-Z0-9_]*\}")


def env_values(content: str) -> dict[str, str]:
    values = {}
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return values


def violations(files: dict[str, bytes], *, local_secrets: tuple[bytes, ...] = ()) -> list[tuple[str, str]]:
    failures = []
    for name, content in files.items():
        path = Path(name)
        if (set(path.parts) & PRIVATE_DIRECTORIES
                or (path.name.startswith(".env") and path.name != ".env.example")
                or name.endswith(PRIVATE_SUFFIXES) or path.name.startswith("id_rsa")
                or path.name.startswith("credentials") and path.suffix == ".json"
                or path.parts[:1] == ("data",)
                or path.parts[:3] in (("infra", "docker", "data"), ("infra", "docker", "volumes"))):
            failures.append((name, "private/generated file in Git index"))
        for label, pattern in PATTERNS:
            if pattern.search(content):
                failures.append((name, label))
        if any(value and value in content for value in local_secrets):
            failures.append((name, "local secret value in Git index"))
        if path.name == ".env.example":
            for key, value in env_values(content.decode()).items():
                if SECRET_NAME.search(key) and value and not PLACEHOLDER.fullmatch(value):
                    failures.append((name, "non-placeholder example credential"))
        if name == "infra/keycloak/qh-realm.json":
            try:
                realm = json.loads(content)
                passwords = [c.get("value", "") for u in realm.get("users", [])
                             for c in u.get("credentials", []) if c.get("type") == "password"]
                client_secrets = [c["secret"] for c in realm.get("clients", []) if c.get("secret")]
                if any(not isinstance(v, str) or not PLACEHOLDER.fullmatch(v) for v in passwords + client_secrets):
                    failures.append((name, "non-placeholder realm credential"))
            except (ValueError, TypeError, AttributeError):
                failures.append((name, "invalid realm JSON"))
    return failures


def main() -> None:
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    files = {name: subprocess.check_output(["git", "show", ":" + name], cwd=ROOT)
             for name in names if name}
    env = ROOT / ".env"
    values = env_values(env.read_text()) if env.exists() else {}
    secrets = tuple(value.encode() for key, value in values.items()
                    if SECRET_NAME.search(key) and value and not PLACEHOLDER.fullmatch(value))
    failures = violations(files, local_secrets=secrets)
    for name, label in failures:
        print("FAIL: " + json.dumps(name) + ": " + label)
    if failures:
        raise SystemExit(1)
    print("PASS: Git index private-file/credential guard; no sensitive values printed")


if __name__ == "__main__":
    main()
