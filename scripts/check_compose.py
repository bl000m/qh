"""Check resolved Compose isolation without printing environment secrets.

Requires Docker Compose, but not a running daemon. Uses only Python stdlib.
"""

import argparse
import json
from pathlib import Path
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compose-cli", help="Optional standalone Compose executable")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    command = [args.compose_cli] if args.compose_cli else ["docker", "compose"]
    command += [
        "--env-file", ".env", "-f", "infra/docker/docker-compose.yml",
        "config", "--format", "json",
    ]
    # Capture configuration in memory: resolved environment contains credentials.
    result = subprocess.run(command, cwd=root, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit("FAIL: Compose config could not be resolved; run make config locally.")
    config = json.loads(result.stdout)
    services = config["services"]
    assert set(services) == {"frontend", "backend", "mcp", "neo4j", "postgres"}
    assert config["networks"]["data"]["internal"] is True
    for name in ("neo4j", "postgres"):
        service = services[name]
        assert not service.get("ports"), f"{name}: database port published"
        assert set(service["networks"]) == {"data"}
        assert any(mount["type"] == "volume" for mount in service["volumes"])
    for name in ("frontend", "backend", "mcp"):
        assert services[name]["ports"]
        assert all(port["host_ip"] == "127.0.0.1" for port in services[name]["ports"])
        assert services[name].get("build")
    assert set(services["backend"]["networks"]) == {"app", "data"}
    assert set(services["frontend"]["networks"]) == {"app"}
    assert set(services["mcp"]["networks"]) == {"app"}
    for service in services.values():
        assert service["healthcheck"]["test"]
    print("PASS: five services, healthchecks, persistent DB volumes, loopback app ports,")
    print("      no published DB ports, internal data network; resolved configuration only.")


if __name__ == "__main__":
    main()
