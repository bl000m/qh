# Keycloak template provenance

`login/template.ftl` and `login/field.ftl` derive from Keycloak 26.4.7,
`keycloak.v2/login`, in the official `org.keycloak.keycloak-themes-26.4.7.jar`.
Upstream SCM revision: `38c38721ad4c1303fa2a1bc24ccece4799a8a242`.
The [Apache 2.0 license](KEYCLOAK-LICENSE.txt) applies to those upstream templates.
QH logo/bubble rights and approvals remain separate.

QH changes are marked at each file's beginning; inherited trailing whitespace is normalized:

- Template: omit the ordinary login page title only, replace the language select
  with links generated from Keycloak's own `locale.supported[].url`. Additional
  enabled languages retain real text links. Other page headings remain.
- Field: add a translated placeholder to the username field only.
- Native login form/action/hidden fields, CSRF/authentication session handling,
  password visibility module, passkeys, optional providers, additional methods,
  error sanitization, recovery/registration conditions and polling remain upstream.

For a Keycloak upgrade, diff these two overrides against that exact version's
upstream templates and rerun isolated FR/EN, errors, login/logout and OIDC checks.
Do not assume CSS inheritance alone updates overridden templates automatically.
