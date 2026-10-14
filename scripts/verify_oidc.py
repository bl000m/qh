"""Run real OIDC tests in Docker; credentials never enter command arguments."""

import os
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--application", action="store_true",
                        help="Read-only login checks against the deployed application database")
    args = parser.parse_args()
    values = dict(line.split("=", 1) for line in (ROOT / ".env").read_text().splitlines()
                  if "=" in line and not line.startswith("#"))
    names = ("QH_ALICE_PASSWORD", "QH_BOB_PASSWORD")
    if not all(values.get(name) for name in names):
        raise SystemExit("Run make oidc-up first.")
    environment = dict(os.environ)
    environment.update({name: values[name] for name in names})
    environment["QH_RUN_OIDC"] = "1"
    environment["QH_RUN_OIDC_APPLICATION"] = "1" if args.application else "0"
    environment["FRONTEND_PORT"] = values.get("FRONTEND_PORT", "5173")
    command = ["docker", "compose", "--env-file", ".env", "-f", "infra/docker/docker-compose.yml",
               "exec", "-T"]
    for name in (*names, "QH_RUN_OIDC", "QH_RUN_OIDC_APPLICATION", "FRONTEND_PORT"):
        command += ["-e", name]
    command += ["backend", "python", "-m", "pytest", "-q", "-s",
                "/workspace/tests/oidc/test_keycloak.py"]
    command += ["-k", "test_live_application_identity" if args.application
                else "test_real_oidc_login_mapping_and_owner_isolation"]
    raise SystemExit(subprocess.run(command, cwd=ROOT, env=environment).returncode)


if __name__ == "__main__":
    main()
