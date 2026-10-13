"""Append missing local IdP secrets; preserve existing environment values."""

from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parents[1]
SECRET_KEYS = ("KEYCLOAK_ADMIN_PASSWORD", "QH_ALICE_PASSWORD", "QH_BOB_PASSWORD")


def main() -> None:
    path = ROOT / ".env"
    if not path.exists():
        raise SystemExit("Run python3 scripts/init_env.py first.")
    lines = path.read_text().splitlines()
    values = dict(line.split("=", 1) for line in lines if "=" in line and not line.startswith("#"))
    for key in SECRET_KEYS:
        if not values.get(key):
            lines = [line for line in lines if not line.startswith(key + "=")]
            lines.append(key + "=" + secrets.token_urlsafe(32))
    path.write_text("\n".join(lines) + "\n")
    path.chmod(0o600)
    print("Local OIDC secrets ready in ignored .env; existing values preserved.")


if __name__ == "__main__":
    main()
