"""Verify live Compose services and database isolation using Docker CLI only.

The host uses Python stdlib; probes execute inside the existing containers.
No containers, images or volumes are created, removed or replaced by this script.
Resolved environment and inspect payloads are captured, never printed.
"""

import argparse
import ipaddress
import json
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"frontend", "backend", "mcp", "postgres", "neo4j"}
NODE_PROBE = """
const net = require('node:net');
async function denied(host, port) {
  return new Promise((resolve, reject) => {
    const socket = net.createConnection({host, port});
    socket.setTimeout(2000);
    socket.once('connect', () => {
      socket.destroy(); reject(new Error('Unexpected database connection'));
    });
    socket.once('error', () => resolve());
    socket.once('timeout', () => { socket.destroy(); resolve(); });
  });
}
(async () => {
  for (const [host, port] of JSON.parse(process.argv[1])) await denied(host, port);
})().catch(() => process.exit(1));
"""
PYTHON_PROBE = """
import json, socket, sys
for host, port in json.loads(sys.argv[1]):
    try:
        connection = socket.create_connection((host, port), timeout=2)
    except OSError:
        continue
    connection.close()
    raise SystemExit('Unexpected database connection')
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run(argv: list[str], label: str, timeout: int = 40) -> str:
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    # Do not dump raw output: inspect and future driver errors can contain secrets.
    require(result.returncode == 0, f"{label} failed (exit {result.returncode})")
    return result.stdout


def inspect_services(docker: str, compose: list[str]) -> dict:
    ids = run(compose + ["ps", "--all", "--quiet"], "Compose container listing").split()
    require(len(ids) in (5, 6), "Expected five base containers and optional Keycloak")
    entries = json.loads(run([docker, "inspect", *ids], "Container inspection"))
    services = {}
    for entry in entries:
        name = entry["Config"]["Labels"]["com.docker.compose.service"]
        if name == "keycloak" and entry["State"]["Status"] == "exited":
            continue  # A stopped optional profile must not break base checks.
        require(name not in services, "Duplicate Compose service")
        require(entry["State"]["Status"] == "running", f"{name} is not running")
        require(entry["State"].get("Health", {}).get("Status") == "healthy", f"{name} is not healthy")
        services[name] = entry
    require(set(services) in (EXPECTED, EXPECTED | {"keycloak"}), "Unexpected Compose service set")
    return services


def verify_topology(docker: str, services: dict) -> list[list]:
    networks = {name: set(info["NetworkSettings"]["Networks"]) for name, info in services.items()}
    require(len(networks["postgres"]) == 1, "PostgreSQL must have one internal network")
    require(networks["neo4j"] == networks["postgres"], "DB networks differ")
    data = next(iter(networks["postgres"]))
    require(len(networks["frontend"]) == 1, "Frontend must have one app network")
    app = next(iter(networks["frontend"]))
    require(app != data, "App and data networks must be separate")
    require(networks["mcp"] == {app}, "MCP must join only the app network")
    require(networks["backend"] == {app, data}, "Backend must join app and data networks")
    if "keycloak" in services:
        require(networks["keycloak"] == {app}, "Keycloak must not join the data network")
        require(any(m["Type"] == "volume" and m["Destination"] == "/opt/keycloak/data"
                    for m in services["keycloak"]["Mounts"]), "Keycloak requires persistent storage")
    metadata = json.loads(run([docker, "network", "inspect", data], "Data network inspection"))
    require(metadata[0]["Internal"] is True, "Data network is not internal")
    projects = {info["Config"]["Labels"]["com.docker.compose.project"] for info in services.values()}
    require(len(projects) == 1, "Services belong to different Compose projects")
    project = next(iter(projects))
    for name, mounts in {
        "postgres": {"/var/lib/postgresql/data": "postgres_data"},
        "neo4j": {"/data": "neo4j_data", "/logs": "neo4j_logs"},
    }.items():
        info = services[name]
        require(not info["HostConfig"].get("PortBindings"), f"{name} publishes host ports")
        for destination, volume in mounts.items():
            require(any(m["Type"] == "volume" and m["Destination"] == destination
                        and m["Name"] == f"{project}_{volume}" for m in info["Mounts"]),
                    f"{name} is missing named persistent storage at {destination}")
    for name in ({"frontend", "backend", "mcp"} | ({"keycloak"} if "keycloak" in services else set())):
        bindings = services[name]["HostConfig"].get("PortBindings") or {}
        require(bool(bindings), f"{name} has no published application port")
        require(all(binding["HostIp"] == "127.0.0.1"
                    for entries in bindings.values() for binding in entries or []),
                f"{name} publishes an application port outside loopback")
    targets = []
    for name, port in (("postgres", 5432), ("neo4j", 7687)):
        address = services[name]["NetworkSettings"]["Networks"][data]["IPAddress"]
        ipaddress.ip_address(address)
        targets.append([address, port])
    return targets


def verify_connections(compose: list[str], targets: list[list]) -> None:
    output = run(compose + [
        "exec", "-T", "backend", "python", "-m", "pytest", "-q",
        "/workspace/tests/smoke/test_services.py", "-k",
        "postgres_authenticated_internal_connection or neo4j_authenticated_internal_connection",
    ], "Authenticated backend database probes")
    require("2 passed" in output, "Both positive database probes must run and pass")
    print("PASS: backend authenticates and queries both databases")
    payload = json.dumps(targets)
    for name, command in (
        ("frontend", ["node", "-e", NODE_PROBE, payload]),
        ("mcp", ["python", "-c", PYTHON_PROBE, payload]),
    ):
        run(compose + ["exec", "-T", name, *command], f"{name} database denial probes")
        print(f"PASS: {name} cannot connect to either DB IP/port (two TCP probes)")


def verify_persistence(docker: str, compose: list[str], before: dict) -> None:
    token = uuid4().hex
    helper = compose + ["exec", "-T", "backend", "python", "/workspace/tests/infra/persistence_probe.py"]
    print(f"Persistence probe token: {token}", flush=True)
    try:
        run(helper + ["write", token], "Writing disposable persistence markers")
        print("Restarting only postgres and neo4j; retaining containers and volumes", flush=True)
        run(compose + ["restart", "--timeout", "30", "postgres", "neo4j"], "Database restart", timeout=90)
        deadline = time.monotonic() + 180
        while True:
            entries = json.loads(run([docker, "inspect", before["postgres"]["Id"], before["neo4j"]["Id"]],
                                     "Database readiness inspection"))
            if all(entry["State"].get("Health", {}).get("Status") == "healthy" for entry in entries):
                break
            require(time.monotonic() < deadline, "Databases did not become healthy after restart")
            time.sleep(2)
        after = inspect_services(docker, compose)
        require(all(after[name]["Id"] == info["Id"] for name, info in before.items()),
                "A container was replaced during the probe")
        verify_topology(docker, after)
        for name in ("postgres", "neo4j"):
            require(after[name]["Mounts"] == before[name]["Mounts"], "Database mounts changed")
        run(helper + ["read", token], "Reading persistence markers after restart")
        print("PASS: both database markers survived restart; container IDs and volume mounts unchanged", flush=True)
    finally:
        try:
            run(helper + ["cleanup", token], "Cleanup of this probe's markers")
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            print(f"FAIL: probe cleanup incomplete; retry helper cleanup with token {token}", file=sys.stderr)
            raise
        print("PASS: only this probe's SQL schema and Neo4j node removed; cleanup confirmed", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker-cli", default="docker")
    parser.add_argument("--persistence", action="store_true",
                        help="Write disposable markers and restart only the existing database containers")
    args = parser.parse_args()
    compose = [args.docker_cli, "compose", "--env-file", ".env", "-f", "infra/docker/docker-compose.yml"]
    services = inspect_services(args.docker_cli, compose)
    targets = verify_topology(args.docker_cli, services)
    print("PASS: five healthy base services" + (" + optional Keycloak" if "keycloak" in services else "")
          + ", internal DB network, named volumes and loopback app ports")
    verify_connections(compose, targets)
    if args.persistence:
        verify_persistence(args.docker_cli, compose, services)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError) as error:
        print(f"FAIL: {type(error).__name__}: infrastructure verification did not complete", file=sys.stderr)
        raise SystemExit(1)
