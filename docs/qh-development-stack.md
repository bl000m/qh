# QH VPS POC — sviluppo live nel checkout unico

## Owner Space erasure — activation pending, 2026-10-30

The delete action requires migration `0012_space_deletion`. Before activation,
requests fail closed with 503 and do not change Space data. No migration or real
Space deletion was performed while implementing the feature.

Activation is a separate explicitly authorized operation: obtain and verify a
private PostgreSQL backup/restore safeguard, apply only the reviewed forward
migration, then use `sudo -n make dev-restart DEV_SERVICE=backend` so the native
worker recognizes schema 0012 and resumes durable pending deletions. Preserve
all existing realm/configuration/volumes. Never use generic `make migrate` or
Compose lifecycle commands against this POC. Verify first with a disposable,
explicitly designated Space; no existing Space is a smoke-test target.

Deletion revokes access before graph work. On partial failure, retry the same
confirmed action or let the worker resume; do not reset jobs, disable triggers,
or restore old canonical data over a live database. Completed erasure keeps only
an owner-bound completion receipt; graph assertions, PDFs, history and shares
are removed for that Space. Aggregate cost/account records are preserved.

Decisione esplicita del proprietario, **2026-10-17**, durante QH-12 / [PR #13](https://github.com/bl000m/qh/pull/13).
Sostituisce per questa fase POC la gestione image-only di frontend/backend.
La PR resta aperta per la prova personale del proprietario; Jira QH-12 resta aperto.
Non è una release pubblica e non certifica la fedeltà semantica delle estrazioni.

## Stack attivo e confini

Un solo progetto Compose `qh`, nello stesso VPS e con gli stessi dati. La base è
`infra/docker/docker-compose.yml`, con overlay
[`qh-hot-reload.yml`](../infra/docker/qh-hot-reload.yml). Non usare
`--project-directory`, un altro progetto o porte alternative.

| Servizio | Modalità attiva | Accesso host |
| --- | --- | --- |
| frontend | Immagine dipendenze QH-12 + sorgenti React/shared dal checkout; Vite HMR | `127.0.0.1:5173` |
| backend | Immagine dipendenze QH-12 + app/adapters/tests/scripts dal checkout; Uvicorn factory con reload | `127.0.0.1:8000` |
| MCP | Container e immagine c723d32 precedenti, senza bind o reload; non gestito dai comandi dev | `127.0.0.1:3001` |
| PostgreSQL / Neo4j | Container, reti, credenziali e volumi persistenti invariati; schema 0005, namespace `qh-native` | Nessuna porta host |
| Keycloak | Container/volume e realm readonly invariati; issuer localhost, Code+PKCE | `127.0.0.1:8080` |

Le immagini dipendenze API/frontend sono quelle verificate da
`d70626bbe50c070c428b02564d22dec42b3b22b0`, con ID e OCI revision nel
[manifest originale](evidence/qh12-demo-a-20261017/candidate-images.json).
All'attivazione i sorgenti applicativi montati erano quelli di
`70c30b2ad998ea70fb29f958c042dd1c037c12ec`, senza differenze applicative rispetto
a d70626b. I commit successivi di questa transizione modificano gestione/test/docs,
non la logica API o React. In questa modalità **l'immagine da sola non identifica
il codice eseguito**: annotare sempre HEAD e modifiche locali. Il registro e la PR
documentano anche il commit della configurazione operativa.

## Later QH-43 login presentation operation — 2026-10-18

The owner explicitly authorized [QH theme/French activation](qh-43-keycloak-activation.md)
in the existing demo realm. Its operation/evidence supersedes the earlier unchanged-
IdP presentation statements below for **only those four language/theme fields and
installed static files**. Root realm import, issuer/client/PKCE, identities, session
lifetimes, ports, mounts, volumes and ordinary app-only dev commands stay unchanged.
Frozen theme files are installed in the existing container rather than source-bound;
future Keycloak replacement must reinstall them before serving the selected theme.
No generic Compose operation or automatic startup migration is authorized.

## Later QH-49 durable login activation — 2026-10-19

The explicitly approved [QH-49 operation](qh-49-keycloak-delivery.md) now serves
QH-50's native French/English login on the real VPS from a sealed versioned image.
It supersedes the old writable-layer delivery described above. Private
`QH_KEYCLOAK_IMAGE` selects the active image; the same existing data/import mounts,
realm/client/identity/session configuration and all five other services are preserved.
Only Keycloak was replaced; measured stop-to-readiness was 40.04 seconds. Cold
backup/isolated recovery, actual VPS authentication and idempotent apply pass.
No new general recreation permission follows. Ordinary dev commands remain app-only.

## Comandi ordinari

Da `/home/ubuntu/qh`, con accesso Docker; su questo VPS:

```sh
sudo -n make dev-status
sudo -n make dev-up
sudo -n make dev-logs
sudo -n make dev-restart
sudo -n make dev-stop
```

`dev-up` verifica progetto, pin/ID/OCI delle immagini, configurazione nativa/OIDC,
porte, reti, mount e ambiente dell'infrastruttura prima di usare `up --no-deps
--no-build` **solo frontend/backend**, attendendo la health. Non crea DB, utenti,
volumi, reti o profili. `dev-restart` riavvia solo queste app e attende la health;
`dev-stop` arresta solo queste app. Restart/stop rifiutano container non ancora
attivati con questo overlay. Le operazioni verificano che gli altri quattro
container abbiano conservato ID, immagine, avvio e mount. `dev-status` mostra lo
stato del progetto; `dev-logs` mostra le ultime 100 righe applicative sanitizzate.
Gli errori Docker completi restano in file temporanei mode 600, fuori da Git.

Verifiche dell'unità operativa `4d7b82f`: **15 test dei guard** più il test esistente
di sanitizzazione del browser harness, **16 PASS** complessivi nel run Docker
mirato; Ruff e whitespace PASS. Eseguiti anche `dev-status`, `dev-logs` (assenza
delle credenziali configurate nell'output), `dev-restart` con health finale e un
secondo `dev-up` idempotente, senza cambiare alcun container ID. `dev-stop` è
coperto dai guard test; non viene eseguito per lasciare il browser disponibile.

**`make up` non è sicuro sullo stack persistente:** può ricostruire/ricreare servizi
fuori dal perimetro. Anche `make verify`, `make oidc-up`, `make migrate`, seed e
generici comandi Compose non sono comandi di gestione di questo VPS. I test usano
infrastruttura isolata e non l'ambiente persistente.

## Modifiche e branch

React/shared src e Python app/adapters richiedono soltanto il salvataggio: Vite
aggiorna il DOM e Uvicorn ricarica il worker senza build Docker. Il reload Python
interrompe brevemente le richieste. Non modificare dipendenze durante richieste
importanti o scritture manuali. Cambi a variabili d'ambiente, Compose o mount
richiedono un nuovo allineamento controllato; un semplice restart non applica un
nuovo ambiente. Cambi a manifest/lockfile, Dockerfile o file non montati richiedono
build da Git archive, verifiche, nuovi pin/manifest e ricreazione delle sole app.
Nessun rebuild automatico contro lo stack persistente.

Prima di cambiare branch: salvare/committare il lavoro autorizzato, `dev-stop`,
verificare app arrestate e assenza di altri processi sorgente-dipendenti, controllare
identità/byte del realm e file privati. Solo allora effettuare lo switch Git senza
force, verificare compatibilità con 0005 e riattivare tramite `dev-up`. Non passare
a una branch vecchia/incompatibile né eseguire migrazioni implicite. Il checkout
rimane unico e una sola branch/task/PR resta attiva. CI, review e merge sono
obbligatori; il codice sorgente diventa visibile sul POC **prima** del merge.

## Browser del Mac

Inoltrare da VS Code **5173, 8000 e 8080**, con porte locali identiche e visibilità
privata. Aprire **http://localhost:5173/**. Il browser chiama `/api` sullo stesso
origin; Vite inoltra internamente a `backend:8000`. Il login e il callback usano
`http://localhost:8080/realms/qh` e `http://localhost:5173/oidc/callback`.
Non cambiare hostname/realm/CORS per aggirare un inoltro errato. Nessuna credenziale
è inclusa in questa guida. Token solo in memoria; un reload completo richiede un
nuovo accesso, eventualmente tramite SSO Keycloak.

Sul VPS il login inizialmente restituiva 401: non esistevano righe in
`user_identities`. Dopo **ulteriore consenso esplicito** del proprietario è stato
eseguito una volta il provisioning demo QH-5 già esistente, aggiungendo solo
Alice/Bob e i due collegamenti OIDC; nessun reseeding/startup automatico o cambio
di policy/realm. Le prove create/list/open hanno conservato due Space vuoti
`Vérification hot reload QH-12 — 2026-10-17`, appartenenti ad Alice. Il secondo
è stato creato per errore dallo smoke temporaneo, che controllava la lista prima
del caricamento; non è stato cancellato. Lo smoke corretto riapre il primo per ID
tramite navigazione SPA, senza altre creazioni o reload che perdano la sessione. Nessun elemento
Understanding è stato creato, confermato o riassegnato.

Le sette revisioni Understanding storiche appartengono ad altri proprietari
sintetici senza collegamento OIDC. Per Alice le ricerche nel nuovo Space vuoto
restituiscono correttamente zero: **non è un difetto UI**. Una demo popolata di
provenance nel browser richiede un'acquisizione sintetica separatamente autorizzata;
non è stata inventata una corrispondenza fra utenti e dati esistenti.

Il confronto SQL prima/dopo verifica ogni riga precedente. Le sole aggiunte sono
due utenti, due collegamenti OIDC, due Space e le rispettive righe `context_projection_state`
con avanzamento zero; le altre dieci tabelle sono identiche. Nessun intent outbox
è stato aggiunto/rimosso/reset. Il container isolato di restore è stato arrestato
e rimosso normalmente dopo la verifica; nessun volume persistente è stato creato
o rimosso.

## Evidenza e limiti delle verifiche eseguite

| Controllo | Risultato |
| --- | --- |
| Frontend, API health, discovery Keycloak | PASS, HTTP 200 sulle porte originali |
| Chromium sul vero VPS: login Alice/Bob Code+PKCE, API via proxy | PASS dopo provisioning demo autorizzato; nessun token in Web Storage |
| Space: creazione, lista, apertura; Bob negato | PASS; due Space sintetici conservati; riapertura del primo verificata per ID |
| Vista Compréhension: current/proposed/history e testo/descrittori | PASS, risposte 200 vuote coerenti con il nuovo Space |
| Understanding/provenance storici, controllo interno autorizzato readonly dopo restart | PASS; nessuna reinterpretazione o inferenza |
| Provenance con risultati popolati nel browser persistente | NOT TESTED: dati storici non appartenenti agli account demo |
| Guasto reale del grafo | PASS nel precedente test isolato QH-12; non provocato sul Neo4j persistente |
| HMR React | PASS: testo temporaneo visibile, frame WebSocket Vite, stesso documento, ripristino osservato |
| Reload Python | PASS: modifica/commento e ripristino rilevati da WatchFiles, stessi container/immagini, health finale OK |
| DB/Neo4j/IdP/MCP preservati | PASS: identici ID, immagini, avvio, reti, mount e configurazione; realm/.env/bundle invariati |
| Verifica personale dal Mac | Da eseguire dal proprietario: Chromium sul VPS non attesta il suo browser/forwarding |

I sorgenti di prova React/Python sono ripristinati byte per byte. Gli artefatti
operativi privati (smoke, screenshot e log senza pubblicazione di credenziali)
sono archiviati con il backup. Le [prove isolate QH-12](qh-12-context-understanding.md)
restano separate: 503 casi nativi senza skip e 24 frontend/browser nell'ultimo
checkpoint precedente; non sono test nuovi sul database persistente.

## Backup e rollback senza perdita di dati

Backup durevole mode 600: `/home/ubuntu/qh-runtime/backups/20261017-hot-reload/qh.dump`;
directory mode 700 con checksum SHA-256, lista archivio, inventario e hash SQL.
Prima del cutover è stato arrestato solo il backend/worker. `pg_dump -Fc` è stato
ripristinato con `pg_restore --exit-on-error` in PostgreSQL temporaneo **senza rete,
porte o volumi persistenti**: conteggi e hash di tutte le **14 tabelle** identici;
schema 0005 verificato. È una verifica del backup, non un secondo stack preview.
Il database QH non è stato ripristinato, migrato o sovrascritto.

Il bundle `/home/ubuntu/qh-runtime/current` e le precedenti immagini c723d32 restano
intatti per il rollback. Non rappresentano più la configurazione attiva delle due
app. Procedura di ripristino applicativo, soltanto durante un'operazione autorizzata:

1. Congelare le scritture, fermare solo frontend/backend, salvare il lavoro Git e
   verificare compatibilità 0005/dati e immagini esatte dal vecchio manifest.
2. Renderizzare privatamente base+`qh-immutable.yml`+`qh-idp-path.json` dal bundle,
   con la stessa `.env`, `-p qh`, senza `--project-directory`.
3. Eseguire `up -d --no-deps --no-build --wait` solo per frontend/backend. Lasciare
   MCP, PostgreSQL, Neo4j e Keycloak invariati. Verificare health, ID/mount/config,
   dati e outbox. La vecchia UI/API perde le nuove funzioni ma non i dati.
4. Non ripristinare il dump sopra nuovi dati, non fare downgrade, cancellare righe,
   svuotare code o resettare epoche. Se la compatibilità non è dimostrata, mantenere
   le app ferme per diagnosi e correzione forward.

Nessun `down -v`, prune, modifica del realm, migrazione, inferenza, tag/release,
merge o transizione Jira è compreso in questa attivazione.


## QH-45 scoped provider activation — owner authorization, 2026-10-19

The existing hot-reload override now accepts default-off provider-session flags
and a backend-only private `/run/qh-chat` mount. Only the backend receives the
server Mistral key. Actual scoped availability, expiry, preservation and rollback
are recorded in [the activation report](qh-45-live-activation.md); this is not
permission to recreate dependencies or extend that authorization.

Use `sudo -n make dev-up DEV_SERVICE=backend` for the specifically authorized
backend configuration activation/rollback. The guarded command validates images,
DB/OIDC/native settings, ports and source paths and compares every non-target
container afterward. `DEV_SERVICE` accepts only frontend/backend; omit it to retain
the original app-pair behavior. A normal dev-up is not permission to enable a
provider, renew receipts, replace ledgers or run an inference. Existing dev-stop
before branch switching and all persistent-data protections remain mandatory.

## PDF activation — owner authorization, 2026-10-29

The backend dependency image is now `qh-api:pdf-685f005`, built from Git archive
685f005 with pinned pypdf 6.21.4. Its exact ID/revision is retained in
`infra/docker/qh-backend-image.json`; the guard overlays only this backend pin,
leaving the historical image evidence and frontend/MCP pins intact. Application
sources still come from this checkout. Both native and sharing startup gates
explicitly accept additive schema `0011_source_documents`; unknown versions remain
refused. Only the backend was recreated/restarted with guarded `dev-*` commands.

A fresh private PostgreSQL dump was restored in a disposable, networkless tmpfs
container; every table fingerprint matched. Migration 0010→0011 was rehearsed
there, then applied alone to the persistent database while the backend was stopped.
All pre-existing table fingerprints remained unchanged. Backup, globals, SHA256
and restore receipts are retained with 0700/0600 protection under
`.local-archive/qh-pdf-activation-20261029/`. Never downgrade or restore over new
writes for application rollback; keep 0011 and existing original documents.

The actual HTTPS/OIDC browser path passed synthetic PDF upload, page text, exact
original download, a fresh persisted read and anonymous-download denial. No
memorization or paid inference ran in the verification browser, whose inference
routes were blocked. Authorization and `.env` hashes and all non-backend
container identities/start times/mounts were unchanged. The ledger changed during
the activation window independently of this browser path; it was not reset,
rewritten by maintenance or reconciled, and no pending attempt remained at the
final read-only check. Three
clearly labelled synthetic Spaces were retained after a browser-script error;
one contains the verification PDF. No existing Space was modified or deleted.
The owner's CV itself was not inspected: the previous generic complexity error
was reproduced on a valid synthetic PDF because pypdf was missing from the old
image; the same parser succeeds with the installed dependency and unchanged limits.
