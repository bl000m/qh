# QH login theme — inherited presentation and controlled activation

For Keycloak 26.4.7, inherit `keycloak.v2`; retain all upstream templates, credential
fields, validation, scripts, errors and Code+PKCE flows. The child adds only local
CSS, the selected original mark/bubble, a whole-mark favicon and QH header text.
It uses a light background, dark text/buttons and the logo's red accent; no custom
login endpoint, password collector, session or authentication behavior.

The owner authorized controlled VPS activation on 2026-10-18, superseding the
previous source-only gate for this demo realm. See the [activation/rollback record](../../../../docs/qh-43-keycloak-activation.md)
for executed evidence and current status. Other environments or further realm,
container/authentication changes still require separate permission. The readonly
root realm import remains unchanged; source preparation never activates a realm
by itself.

The existing browser harness has an explicit disposable-only opt-in:

```bash
python3 scripts/test_qh11_browser.py --sudo-docker \
  --backend-image qh43-api:checkpoint --browser-image qh43-browser:branding \
  --understanding --qh-login-theme --output /tmp/qh43-branding-fresh
```

It copies the public realm fixture into its temporary directory, selects
`loginTheme=qh` and enables French/English with French as the default in that
disposable copy, and mounts this theme read-only on its own
Keycloak. Real credentials remain generated test environment values. Without the
flag the original fixture/theme path is unchanged. The hosted browser job enables
this preview; its French login test requests browser locale `fr-FR` (browser language
otherwise takes precedence over the realm default). The separate OIDC job also
retains the original unthemed regressions.

Logo/bubble PNGs must be byte-identical to the frontend's selected assets. The ICO
contains the same 64×64 PNG as the client favicon. No original deck, font download,
portrait, future-capability mockup or alternate mark belongs in the theme.
[Traceability and checkpoint](../../../../docs/qh-43-branding-checkpoint.md).

## QH-50 source refinement — 2026-10-19

The owner-selected private reference is `QH-design 2/Interface de connexion QH minimaliste.png`.
Its layout is implemented with the existing original mark and bubble: small centered
header, rounded white card, central bubble, pill inputs/submit and real FR/EN links.
The ordinary login heading is omitted; headings for recovery/additional steps remain.
The native form and password visibility control are retained. Registration/recovery
appear only when the existing realm permits them. No decorative registration promise
is added. Flag glyph appearance follows the browser's emoji font; language labels,
44px targets and selected/focus states remain accessible independently of the glyph.

The two small upstream template overrides and maintenance responsibilities are recorded
in [UPSTREAM](UPSTREAM.md). This supersedes the earlier CSS-only description above.
Locale links come from Keycloak itself and retain the current authentication session.
Switching language may discard unsubmitted fields: QH never persists passwords in
storage, URLs or custom scripts to work around that native behavior.

**Prepared/tested source is distinct from VPS activation.** QH-50 does not copy these
new files into the live container or change its realm. The existing QH-43 login stays
functional. QH-49 tracks durable installation before any ordinary recreation.

Reproduction uses the existing disposable browser harness with `--qh-login-theme`:
it mounts the whole versioned theme read-only on an isolated Keycloak 26.4.7 instance,
then starts login with the ordinary Code+PKCE client. For a future authorized deployment,
package the entire theme directory from an exact Git revision into a versioned Keycloak
image or a separately managed immutable mount, record SHA-256 hashes, verify readiness
and test recreation before selecting `loginTheme=qh`. Preserve the previous image/theme
bundle and settings backup for rollback. Do not use `docker cp` into a writable layer
as a new deployment recipe; image/mount choice and persistent activation remain QH-49's
authorized operation, not implicit work in this PR.
