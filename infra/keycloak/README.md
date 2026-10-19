# QH Keycloak theme packaging

The owner-authorized [QH-49 operation](../../docs/qh-49-keycloak-delivery.md) activates
the QH-50 native login on the existing VPS using a versioned image. It supersedes
the earlier source-only delivery boundary, not the OIDC identity/session contract.
The frozen theme's README describes its historical preparation; do not edit those
sealed files merely to update a deployment status.

[The release manifest](qh-theme-release.json) records the exact public theme payload,
source/base and active/rollback IDs. Verify all listed hashes and reject additional
files before building. [Dockerfile.theme](Dockerfile.theme) copies only that theme;
it neither embeds environment/credentials nor selects a realm. A fresh local install
retains upstream 26.4.7 when `QH_KEYCLOAK_IMAGE` is empty.

Example packaging, after inspecting/verifying the manifest, from repository root:

```text
docker build --network none -f infra/keycloak/Dockerfile.theme \
  -t qh-keycloak:new-reviewed-candidate infra/keycloak
```

Use a NEW candidate tag. Never overwrite the active or rollback tag to hide a changed
image. Verify the packaged file set/hashes again, record its image ID, test recreation/
rollback in isolation and obtain authorization before replacing a live container.
The source revision label identifies the frozen theme source, not a claim that later
documentation/recipe commits were in that source commit. Exact image recovery uses
the protected saved archive; fresh build metadata may yield a different image ID.

The private VPS image selector keeps app-only guards consistent with the active
Keycloak image. Future Keycloak maintenance must additionally check its exact sealed
ID, stable data/import mounts and recoverable backup; a mutable tag alone is not an
integrity check. No theme source bind or `docker cp` deployment is used. Existing
`make dev-*` commands still target only frontend/backend. No automatic realm setting,
import, credential change, migration or public Mistral activation follows packaging.
