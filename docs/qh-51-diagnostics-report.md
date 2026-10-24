# QH-51 — diagnostica privata, plafond e audit, 22 ottobre 2026

Jira: QH-51, prosecuzione autorizzata della PR23; nessuna scrittura Jira.
Obiettivo: rendere ispezionabili le chiamate reali, ampliare il plafond conservando
la contabilità e proporre il contratto di validazione prima di modificarne le regole.

## Risultato e criteri verificabili

| Criterio | Classificazione | Esito / evidenza e limite |
| --- | --- | --- |
| Plafond condiviso chat/UUM, storico incluso | Implementato e testato | PASS:100 tentativi/USD2.50, EUR2/USD conservativo; sei righe precedenti identiche, USD0.00298080 spesi,94/USD2.49701920 residui. Nessun reset/retry; scadenza18 novembre2026,05:30 Europe/Rome invariata |
| Prenotazione prima dell'HTTP e concorrenza | Implementato e testato | PASS: test_development_ai + test_ai_diagnostics verificano cap100, saldo insufficiente con zero HTTP, pending/concorrenza, nessun refill al login/cambio Space |
| Risposta originale prima della pulizia | Implementato e testato | PASS offline: HTTP200/1079+536/completed e successivo rifiuto canonico riprodotti; risposta JSON completa nel privato, accounting separato, nessuna richiesta/prompt/header. Non è una nuova chiamata reale |
| Diagnostica owner/principal/Space, cancellazione e retention | Implementato e testato | PASS: accesso OIDC autenticato, CHAT, identità esatta, false identity/Space negati, cancellazione senza mutare ledger, expiry simulata, file0700/0600 e capacità100; probe VPS GET200 privato senza chiamate provider |
| Dettagli delle verifiche | Implementato e testato | PASS: trasporto/usage/modello/token/accounting/completion, regole JSON/alias/snapshot/chat, formato UUM/primaria/evidenze/QH32/profili/batch, esito pubblicazione. Check assenti significano non eseguiti/non strumentati, mai PASS implicito; nessun verificatore generale di verità |
| Audit e proposta funzionale | Implementato e verificato tramite lettura codice + riproduzione offline | PASS: [tabella e contratto](qh-51-validation-audit.md); nessuna regola di ammissione o epistemica allentata |
| Causa esatta del 503 storico | Non verificabile retroattivamente | NOT TESTED: ledger e token/costo corrispondono; JSON precedente già eliminato. Il rifiuto indicato è riproducibile ma non attribuibile con certezza a quella risposta |
| Correzioni CI9d4a420 | Implementate; verifiche mirate descritte sotto | Import standard decimal e aspettative browser legacy; la vecchia CI resta rossa, non viene reinterpretata come verde |
| Nuova inferenza / modifica dati canonici, schema, PR19 | Fuori scope | Nessuna eseguita; fingerprint15 tabelle SQL, file protetti, immagini/ID/mount e avvii infrastruttura invariati |
| Approvazione del nuovo contratto di risposta | Non implementato intenzionalmente | Gate owner aperto: non rimuovere l'obbligo canonico prima dell'approvazione. Il dialogo senza canonico può ancora essere respinto dalla regola attuale |
| Merge/review/chiusura Jira | Fuori scope | PR23 aperta e non integrata, review owner pendente; nessuna transizione Jira |

## Implementazione

- `adapters/llm/diagnostics.py`: archivio privato temporaneo e observer request-local.
  Nessun repository di transcript, SQL, servizio o migrazione. Risposta completa
  come JSON, non dump dei byte/header HTTP. Un eventuale eco della chiave nota viene
  mascherato e segnalato esplicitamente, mai presentato come copia identica.
- `session_config.py` cattura prima di azzerare last_exchange; `mistral.py` osserva
  trasporto/contabilità. Budget rimane lo stesso file flock/fsync, con cap espliciti
  autorizzati dalla receipt. Adapter storici mantengono default8/USD0.20.
- `chat/context.py` e `implementation.py`, `understanding/{selected,extractor,uum}.py`
  riportano gli esiti senza cambiare le condizioni di accettazione. HTTP200,
  completed economico, validità QH e conferma umana sono distinti.
- GET `.../ai/diagnostics`, DELETE `.../ai/diagnostics/{id}`: OIDC completo, owner,
  principal development e CHAT, no-store. Nessun controllo del prezzo o provider
  necessario per consultare risultati già prodotti; nessun modello invocato.
- UI: **Modèles → Diagnostics IA privés → Charger les diagnostics privés**.
  Risultati del solo Space corrente; aprire ciascun tentativo per regole, JSON,
  accounting e cancellazione. Nessuna persistenza browser dei risultati.
- Retention1 ora, pruning a ogni operazione e ogni30 secondi durante runtime;
  startup elimina gli scaduti prima del servizio. App ferma non può eseguire
  housekeeping. File temporanei da crash eliminati sotto lock. Capacità100 record,
  massimo1MiB/record; storage indisponibile blocca prima dell'HTTP quando rilevato
  al preflight. Un errore di storage sopravvenuto non può annullare un costo già
  sostenuto. Nessun recupero dei payload storici già eliminati.

## Verifiche eseguite (campagne mirate, non sommare i duplicati)

- Runner Docker isolato `run_targeted.py`:102 PASS su development/chat/architettura/
  composition;103 PASS su diagnostica/development/sessioni/UUM e pipeline SQL/grafo;
 63 PASS su diagnostica/architettura/composition;61 PASS su adapter Mistral/chat;
 83 PASS su diagnostica/UUM/architettura; infine12 PASS sui casi diagnostici finali.
  I batch si sovrappongono; non sono un conteggio di test distinti.
- Frontend:9 PASS (`ai-diagnostics.spec.ts`, `chat.spec.ts`, `contracts.spec.ts`),
  Ruff, TypeScript e build Vite PASS. Nessun pacchetto/runtime host installato.
- Chromium/OIDC/API/PostgreSQL/Neo4j isolati, Mistral MockTransport:1 PASS sul
  percorso ordinario, chat +UUM, nuova Space, nessun consenso, lettura del JSON,
  cancellazione diagnostica senza richieste provider aggiuntive, budget insufficiente
  simulato. Evidenze private in `browser-ordinary/`.
- CI precedente39813687385: quality592 PASS/1 FAIL/359 SKIP; native664 PASS/1 FAIL;
  browser109 PASS/2 FAIL; OIDC SKIPPED. Cause e correzioni nell'audit. Ripetizione mirata
  dei due scenari browser:2 PASS sul candidato corretto (`browser-ci-fixes-final/`).
  Correzioni nel commit73a9911. Una prima esecuzione mirata ha rilevato anche
  l'asserzione legacy sulla grande card; corretta e verificata, senza cambio UI.
- VPS: `make dev-stop/up/status` guarded, app sane. Probe Playwright autenticato,
  tutti i POST applicativi bloccati/intercettati,0 inferenze e0 scritture canoniche:
  diagnostica GET200/no-store,94 richieste eUSD2.49701920 disponibili. Impossibile
  verificare un nuovo JSON reale senza una nuova inferenza, esclusa dal mandato.
- Le copie private pre-intervento e la registrazione di amendment conservano
  hash e sei righe storiche. Il ledger non è un artefatto da ripristinare in rollback.

## Compatibilità, preservazione e pubblicazione

AGENTS, ADR0007 e contratti QH45/QH52 esplicitano l'amendment. Le vecchie decisioni
rimangono storiche; nessun nuovo consenso/attivazione per richiesta o Space.
La receipt mantiene gli identificativi e la scadenza originali. [Registro operativo](deployments.md)
registra avvio app, backup privati e rollback che preserva la contabilità corrente.

Checkout `/home/ubuntu/qh`, branch `feat/QH-51-semantic-understanding`, PR
[23](https://github.com/bl000m/qh/pull/23), base di intervento9d4a420. Il commit73a9911 corregge le aspettative CI; il successivo commit di funzionalità
include diagnostica/plafond/contratti e questo rapporto, senza riscritture. I controlli
mirati sopra sono PASS; la CI remota sul nuovo HEAD sarà avviata automaticamente
dalla pubblicazione ordinaria e il suo esito resta separato, non ancora dichiarato verde.
La sola pubblicazione ordinaria della branch non autorizza merge, Jira o PR19.
La modifica di titolo/descrizione GitHub resta manuale dopo il precedente403:
[descrizione pronta](reviews/qh51-pr23-current-description.md), nessun nuovo tentativo.
Il prossimo passo funzionale è la decisione owner sul contratto di risposta,
non l'allentamento autonomo dei controlli.
