# QH login theme — source-only owner preview

For Keycloak 26.4.7, inherit `keycloak.v2`; retain all upstream templates, credential
fields, validation, scripts, errors and Code+PKCE flows. The child adds only local
CSS, the selected original mark/bubble, a whole-mark favicon and QH header text.
It uses a light background, dark text/buttons and the logo's red accent; no custom
login endpoint, password collector, session or authentication behavior.

**Not activated on the VPS.** Do not change the persistent realm, readonly realm
import, IdP container/configuration or theme selection without separate owner
permission. Preparation and isolated testing are not activation authorization.

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
