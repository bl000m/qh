"""Generate local development credentials without overwriting existing .env."""

import os
from pathlib import Path
import secrets


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    content = (root / ".env.example").read_text()
    for key in ("POSTGRES_PASSWORD", "NEO4J_PASSWORD"):
        content = content.replace(f"{key}=\n", f"{key}={secrets.token_hex(24)}\n")
    try:
        fd = os.open(root / ".env", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise SystemExit(".env already exists; preserved. Edit it locally if needed.")
    with os.fdopen(fd, "w") as env_file:
        env_file.write(content)
    print("Created local .env (0600); credentials were not printed.")


if __name__ == "__main__":
    main()
