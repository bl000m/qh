# QH-13 contextual chat verification — 2026-10-17

[Measurements](verification.json) pin executable source
`f88e690c27db553d02bcca269744ebb25ddd53da` and its successful
[hosted run](https://github.com/bl000m/qh/actions/runs/39060747371).
All four jobs passed. Final report/archive changes are documentation only;
the latest PR HEAD still requires its own green checks.

The existing browser harness ran with synthetic PostgreSQL/Neo4j/Keycloak and
Chromium on disposable hosted runners, no published ports or live QH credentials.
It verified populated chat, exact source/revision identity, explicit proposal use,
real Bob denial, temporary follow-up, late responses and errors, alongside existing
QH-9/10/11/12 regressions, real graph outage, backup restore and retained-ID reopening.
Outage counts include repeated contract checks and must not be added to the main
suite as unique cases. Dedicated VPS native checks reuse existing test servers.

A separate real VPS read-only probe logged Alice into an existing empty synthetic
Space and received an insufficient-context response without provider generation.
No source/item/Space was created. The old SQL checkpoint predates one additional
empty Space created before QH-13; it is retained and reported, never removed to
make hashes match. All previously retained table rows match the checkpoint exactly.
No actor/cause is invented. Private logs/snapshots/credentials remain outside Git.

No live Mistral call, real API usage, price/FX verification, personal Mac session,
human semantic approval, merge or Jira DONE is attested. Original QH-8/QH-33
captures, references and ledgers are unchanged. See the
[full report](../../qh-13-contextual-chat.md) for architecture, DoD and limitations.

Verify these two public files with Python 3 (no network/dependencies):

```sh
python3 - <<'PY'
import hashlib, json
from pathlib import Path
p = Path('docs/evidence/qh13-chat-20261017')
for name, expected in json.loads((p / 'sha256.json').read_text()).items():
    assert hashlib.sha256((p / name).read_bytes()).hexdigest() == expected, name
print('PASS: QH-13 evidence hashes')
PY
```
