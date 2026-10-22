# QH-51 UUM — evidenza isolata e preparazione reset

22 ottobre 2026, Europe/Rome. [Decisione approvata](../../adr/0010-universal-understanding-model.md).
Queste prove non autorizzano reset, merge o provider. Il database QH del VPS è
ancora quello originale; frontend/backend rimangono fermi per evitare hot reload
del nuovo contratto prima del cutover.

## Risultato verificato

Profilo generico v3 con primaria facoltativa singola, quote esatte nel medesimo
Engine/QH-32, nuova review primaria QH-46 senza conferma dell'item o spostamento
automatico del current. Lettura di presenza e membri verificati sul grafo.
Mappa a sei nodi con corrente/proposte, non classificati, vuoti e indisponibilità
distinti; nessuna aggregazione di titoli, nessun backfill v1/v2.

| Controllo eseguito | Esito osservato | Limite |
| --- | --- | --- |
| Docker pytest mirato UUM + regressioni semantiche/enrichment/review/browse/architettura | **188 PASS**, 359,61 s | PostgreSQL/Neo4j dedicati; non è una nuova campagna CI completa |
| Candidato backend: `test_uum`, `test_uum_presence`, `test_uum_pipeline`, composizione API e guard architetturali | **64 PASS**, 118,01 s | Comprende fixture, atomicità, quote, owner, replay, review e rebuild; nessun modello reale |
| Nuova route presenza e whitelist OIDC esatta | **10 PASS**, 4,80 s, sovrapposti | Root tests/scripts montati readonly correnti, senza rilassare il rifiuto di route/metodi ignoti |
| Provisioning UUM esplicito su 0006 vuoto, replay, preservazione registro e rifiuto non-vuoto | **1 PASS**, 3,60 s | Test reale SQL isolato, con lock; nessun provisioning sul VPS |
| Unit frontend: origine/provenance, temi secondari, wire enrichment e controllo letterale v3 | **7 PASS**, 10,7 s | Nessuna prova di qualità semantica del provider |
| Browser UUM su dataset pulito, output sintetici dichiarati | **2 PASS**, 1,6 min | Vero Chromium/OIDC/API/SQL/Neo4j; cinque Space e trenta proposizioni scritte a mano |
| OIDC rotazione/revoca/logout nel medesimo harness usa e getta | **1 PASS**, 2 deselect | Realm sintetico isolato; Keycloak reale del VPS intatto |
| Build frontend + TypeScript app/shared/test | **PASS** nel browser harness | Immagini di test, nessuna attivazione |
| Ruff, whitespace e index/secrets guard | **PASS** | Nessun segreto nelle evidenze pubblicate |
| Audit sigillato QH-33 v1/v2 | **PASS** | Originali riprodotti senza cambi o nuova inferenza; validazione umana indipendente non dedotta |

Conteggi sovrapposti: **non sommarli**. I controlli completi hosted del candidato
pubblicato sono consultabili nei check della [PR #23](https://github.com/bl000m/qh/pull/23);
non sono sostituiti dai test mirati di questo report.

Il primo avvio hosted sul checkpoint `624f84e`,
[39734120735](https://github.com/bl000m/qh/actions/runs/39734120735), ha quality,
OIDC e native-integration verdi (**899 PASS, zero skip**). Browser: **91 PASS,
1 FAIL**, perché il test storico cercava ancora il nome accessibile « Carte
thématique de ce contexte ». La correzione aggiorna il selettore a « Dimensions
de compréhension » e verifica anche i sei nodi, mantenendo tutte le asserzioni
di storico e fail-closed. Nessun codice applicativo o dato è cambiato per correggere
questo test. Il risultato fallito resta conservato; i check del nuovo HEAD
determinano la readiness finale, senza attribuire al vecchio commit una CI verde.
Ricontrollo mirato: caso storico **1 PASS**, 19,1 s, sullo stesso profilo di sessione
legacy del job principale; maquette e recupero bozze **2 PASS** sul profilo prodotto.
Un primo lancio combinato usava il profilo prodotto anche per il driver storico
che richiede la home dopo login: errore di configurazione del test, conservato
nei log privati e corretto separando i due profili, senza cambiare l'applicazione.

Comandi locali: `python3 .local-archive/qh51-uum-reset-20261021/run_targeted.py`
con i moduli elencati sopra; Docker con bind readonly di app, tests e scripts,
credenziali dedicate temporanee e soli server `qh30-sql-test` e
`qh30-native-neo4j-test`. Il runner nativo completo rimane
`scripts/run_qh30_integration.py`, con nuove prove UUM incluse.

Browser finale:

```text
python3 scripts/test_qh11_browser.py --sudo-docker
  --backend-image qh-uum-api:final --frontend-image qh-uum-web:final3
  --browser-image qh-uum-browser:final3 --understanding --chat-sessions
  --product-mode --uum-mode --focused-browser-only
  --browser-grep 'QH-51 UUM'
  --output .local-archive/qh51-uum-reset-20261021/browser-settled
```

Il flag focused registra un collaudo mirato, non dichiara la CI completa eseguita.
Log, metadati e ricevute locali rimangono nell'archivio privato. Gli artefatti
Docker/fixture non montano `.env`, database o volumi QH persistenti.

## Cinque Space e prove UI

Santé, Projet QH, Recruiting, Voyage e Relations personnelles contengono ciascuno
sei enunciati sintetici espliciti, uno per dimensione. Il test verifica i sei nodi
presenti, il filtro esatto sul nodo obiettivi, una sola appartenenza pertinente,
testo/citazione originale accessibili, review primaria accepted mantenendo item
proposed, refresh con SSO e rifiuto reale 404 per Bob. Un sesto Space vuoto prova
sei vuoti verificati e primo inserimento letterale non classificato; una risposta
503 sulla presenza conserva nodi indisponibili e non produce falsi vuoti.

Le etichette/assegnazioni sono riferimenti scritti a mano: **nessun classificatore,
inferenza o risultato Mistral simulato come reale**. Questa evidenza dimostra
contratti e comportamento applicativo; non misura accuracy o copertura del modello.
L'estrazione automatica di nuove entità/relazioni non è aggiunta dal formato atomico;
la struttura canonica trasversale e i percorsi esistenti rimangono disponibili.

[Mappa desktop](uum-map-desktop.png) · [Mappa mobile](uum-map-mobile.png).
Le catture attendono dati e controlli caricati; non rappresentano il VPS attivo.

## Backup/reset/rollback verificati senza cancellazione sul VPS

Inventario: 15 tabelle SQL; perimetro proposto di 11 tabelle/197 righe applicative,
con 7 utenti, 2 identità OIDC, 14 definizioni di profilo e schema0006 conservati.
Grafo: 86 nodi/36 archi nativi e 6 nodi/4 archi del vecchio prototipo QH.
Nessun volume, identità Keycloak, segreto o ledger fa parte della cancellazione.

- **PASS:** dump SQL completo e restore tmpfs senza rete, confronto dei contenuti
  di tutte le 15 tabelle con fingerprint SHA-256 delle righe canoniche.
- **PASS:** reset delle sole 11 tabelle nel clone, vincoli/guard conservati.
- **PASS:** rollback delle sole righe applicative nello stesso clone/database,
  current pointer e tutti i contenuti tornati al checkpoint, senza toccare identità.
- **PASS:** archivio Neo4j tipizzato e restore esatto di proprietà, label ed endpoint.
- **PASS:** cancellazione selettiva nel clone con canary estraneo preservato,
  poi ricostruzione esatta dei 92 nodi/40 archi.
- **PASS:** 39 hash protetti invariati, incluse configurazioni, contabilità runtime
  e archivio dell'esperimento Mistral originale; zero trigger applicativi disabilitati
  nel PostgreSQL persistente.

Dump SQL SHA-256: `11856295c7778f6c27908faa3b35f50a6b2fa9e9d0a01026078057f9f67abfdc`.
Grafo SHA-256: `6a1cf23f8c900667cd07210575150768d45ff59ff7a0a97057a881d080c4efc9`.
Backups completi e script di rehearsal/rollback sono protetti nell'archivio
`.local-archive/qh51-uum-reset-20261021/`; non pubblicarli perché contengono dati
e configurazione privata. [Piano esatto e gate](../../qh-51-uum-reset-plan.md).

## Correzioni emerse e verificate

Il nuovo dispatch review inizialmente ometteva lo stato/actor proposed per
`review_primary`: corretto, poi verificato su SQL reale e browser. La toolbar
allargata copriva un nodo: controlli in una riga separata, nodi cliccabili anche
su mobile. Il controllo letterale v3 richiedeva origine/provenance coerenti:
aggiornato il riconoscimento rigoroso, senza promuovere interpretazioni AI a
informazioni personali. Driver di test riallineati a sessione in memoria,
progressive disclosure delle fonti e nomi accessibili dei controlli. Le catture
sono state ripetute dopo il caricamento, senza modificare le prove storiche.
I tentativi locali falliti sono conservati nell'archivio, non riclassificati PASS.

## Criteri e stato

| Criterio | Classificazione / esito |
| --- | --- |
| Decisione UUM e nuovo stato applicativo senza migrazione v1/v2 | Approvata e documentata / PASS |
| Profili/DTO/Engine/provenance/review/ownership/fail-closed | Implementato e testato in isolamento / PASS |
| Sei nodi universali, membri, vuoti, non classificati e mobile | Implementato e testato in isolamento / PASS |
| Inventario, backup completo del perimetro, reset e rollback | Preparati e testati sui cloni / PASS; cancellazione VPS NOT EXECUTED |
| Nuove chiamate Mistral, backfill, migrazione0007 e modifica PR19 | Fuori scope, non eseguiti |
| Qualità semantica reale UUM e nuova estrazione con provider | NOT TESTED; provider runtime non attivato |
| Merge #23 e stato DONE Jira | Non eseguiti; nessuna autorizzazione implicita |
| QH realmente attivo sul nuovo dataset e prova personale Mac | Pendenti dopo conferma del perimetro distruttivo e cutover |

QH-51 rimane il ticket corrente. Nessun aggiornamento/stato Jira automatico.
La prossima decisione è la conferma finale del perimetro/backup, dopo review
del candidato; non l'avvio di un altro ticket o l'estensione del provider.
