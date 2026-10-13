"""Reconcile the local demo scope after import; never change users/passwords."""

import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    values = dict(line.split("=", 1) for line in (ROOT / ".env").read_text().splitlines()
                  if "=" in line and not line.startswith("#"))
    base = "http://localhost:" + values.get("KEYCLOAK_PORT", "8080")
    form = urllib.parse.urlencode({"grant_type": "password", "client_id": "admin-cli",
                                  "username": "qh-admin", "password": values["KEYCLOAK_ADMIN_PASSWORD"]}).encode()
    with urllib.request.urlopen(urllib.request.Request(
            base + "/realms/master/protocol/openid-connect/token", data=form), timeout=10) as response:
        token = json.load(response)["access_token"]
    def request(path, *, payload=None, method="GET"):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(base + "/admin/realms/qh/" + path, data=data, method=method,
                                     headers={"Authorization": "Bearer " + token,
                                              "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read()
            return json.loads(body) if body else None
    realm = json.loads((ROOT / "infra/keycloak/qh-realm.json").read_text())
    desired = realm["clientScopes"][0]
    current = next(s for s in request("client-scopes") if s["name"] == desired["name"])
    # Preserve realm/users/sessions and update only this controlled scope.
    existing = request("client-scopes/" + current["id"] + "/protocol-mappers/models")
    for mapper in desired["protocolMappers"]:
        found = next((m for m in existing if m["name"] == mapper["name"]), None)
        if found:
            request("client-scopes/" + current["id"] + "/protocol-mappers/models/" + found["id"],
                    payload=dict(mapper, id=found["id"]), method="PUT")
        else:
            request("client-scopes/" + current["id"] + "/protocol-mappers/models",
                    payload=mapper, method="POST")
    print("Local QH OIDC scope reconciled; users, passwords and volumes preserved.")


if __name__ == "__main__":
    main()
