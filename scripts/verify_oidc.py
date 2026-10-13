"""Run real OIDC tests in Docker; credentials never enter command arguments."""

import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    values = dict(line.split("=", 1) for line in (ROOT / ".env").read_text().splitlines()
                  if "=" in line and not line.startswith("#"))
    names = ("QH_ALICE_PASSWORD", "QH_BOB_PASSWORD")
    if not all(values.get(name) for name in names):
        raise SystemExit("Run make oidc-up first.")
    environment = dict(os.environ)
    environment.update({name: values[name] for name in names})
    environment["QH_RUN_OIDC"] = "1"
    environment["FRONTEND_PORT"] = values.get("FRONTEND_PORT", "5173")
    command = ["docker", "compose", "--env-file", ".env", "-f", "infra/docker/docker-compose.yml",
               "exec", "-T"]
    for name in (*names, "QH_RUN_OIDC", "FRONTEND_PORT"):
        command += ["-e", name]
    command += ["backend", "python", "-m", "pytest", "-q", "-s",
                "/workspace/tests/oidc/test_keycloak.py"]
    raise SystemExit(subprocess.run(command, cwd=ROOT, env=environment).returncode)


if __name__ == "__main__":
    main()
