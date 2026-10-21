# QH-54 / PR22 — Stabilizzazione dopo la decisione tematica

Mandato owner del 2026-10-21, stesso branch `feat/QH-54-context-understanding` in
`/home/ubuntu/qh`, baseline07d86ec. Jira letto via Atlassian MCP: QH-54, QH-51 e
QH-47; nessuna modifica Jira. Nessun merge, switch, schema o provider nuovo.

Questo rapporto congela le verifiche locali precedenti alla pubblicazione. Il
risultato della singola campagna completa e l’HEAD finale sono registrati sulla
[PR22](https://github.com/bl000m/qh/pull/22), dopo la pubblicazione di questo
rapporto: quel risultato determina READY FOR REVIEW, non i soli test locali.

## Delta e criteri della consegna

| Criterio | Classificazione | Verifica |
| --- | --- | --- |
| Niente nodi per singole revisioni, ruoli o titoli | Implementato e testato | `ContextMap` elimina letture/aggregazioni e nodi di revisione; conserva boule e stato minimo. Test prodotto mirato PASS |
| Accesso agli elementi, provenienza e review invariati | Implementato e testato | Stessa navigazione Éléments e UnderstandingWorkspace; test prodotto e A/B PASS; sola cronologia/errori fail closed PASS |
| Composer mobile | Implementato e testato | Ordine responsive: discussione prima della mappa; test browser mirato PASS, con focus/contrasto/assenza sovrapposizione |
| Logo originale | Implementato e testato | Stesso asset master876×768 nell’header; test browser mirato PASS, mantenuti i test sull’identità originale |
| Bozze, ownership, nessuna promozione automatica | Implementato e testato | 9 controlli focused PASS; protocollo Keycloak reale nel profilo isolato PASS; 5 casi prodotto PASS |
| Campagna completa sul candidato finale | Non verificato alla pubblicazione del rapporto | NOT TESTED finché il nuovo candidato non è pubblicato; una sola campagna autorizzata per questa correzione |
| Contratto minimo della mappa | Documentato, revisione statica PASS | Documentato, approvazione di prodotto già concessa: [contratto](qh-54-thematic-map-contract.md) |
| QH-51: proposta con dipendenze e criteri | Proposta documentata PASS; implementazione fuori scope | Documento preparato, **implementazione fuori scope**, approvazione tecnica pendente: [piano](qh-51-thematic-extraction-plan.md) |
| Veri nodi tematici e click sui membri | Non implementato; dipendenza futura esplicita | **Non implementati** in assenza di un contratto dati qualificato; nessun dato attuale viene promosso a tematica |

Il run precedente39565534914 su07d86ec è FAIL: quality/native-integration/oidc
verdi, browser87PASS/2FAIL e fase prodotto non raggiunta. Non si riusa quel run
come risultato verde. I test del composer e del logo restano invariati: corretta
l’implementazione, senza ridurre le aspettative. Le vecchie schermate dei nodi di
revisione sono preservate come evidenza storica superata dalla decisione owner.

## Cause e correzioni circoscritte

Il layout mobile accodava la chat a mappa e azioni, spostando il textarea oltre il
viewport: una regola grid mette ora prima la discussione a650px e sotto.
L’header dello Space sostituiva il master logo con il bitmap della boule: ripristinato
il master nel link home, conservando la boule nella testata e nella mappa.
`ContextMap` usava `itemTitle()` su sei revisioni e disegnava un nodo per ciascuna:
rimosso quel percorso, senza trasformare descrittori generici in tematiche.

Modificati `App.tsx`, `Chat.tsx`, `ContextMap.tsx`, `styles.css`, due file browser
mirati e documentazione Product Contract/changelog/registro. Nessun file backend,
contratto pubblico eseguibile, configurazione OIDC, migrazione o dato canonico.

## Comandi e prove

Eseguiti in Docker: build frontend e immagine browser; strict typecheck app/test;
9 test focused (drafts/origin/groups/reflow/tastiera),5 casi prodotto PASS,1 browser history/errori PASS e3 browser reali mirati alle
regressioni. Harness `scripts/test_qh11_browser.py --sudo-docker --understanding
--chat-sessions --focused-browser-only` con immagini `qh53-api:review`,
`qh54-web:review`, `qh54-browser:review`, filtro `chat composer leads|one approved
identity|skip link is first`. Per persistenza/isolamento aggiunto `--product-mode`
e filtro `QH-54 direct|QH-54 synthetic|QH-54 manual|QH-54 maquettes`.

Evidenza operativa protetta in `.local-archive/qh54-thematic-20261021`:
`ux-targeted.log`, `focused-web.log`, `product-targeted.log`, `history-targeted.log`, manifest dei singoli
harness e controlli preservation. I test usano database/rete/IdP isolati e fixture
sintetiche, nessuna inferenza esterna e nessuna scrittura demo persistente.
Non equivalgono ad accettazione umana dal Mac o a qualità semantica QH-51.

## Stato di review e limiti

PR22 rimane aperta, senza auto-merge. Jira resta invariato, non DONE. PR19 e schema
0007 restano intatti. L’unica correzione funzionale immediata della mappa è il
fallback veritiero; dati tematici, nuovo profilo, review assegnazioni e lettura
filtrata richiedono l’approvazione separata descritta nel piano QH-51.

Commit funzionale `486e607`: correzioni mappa/composer/logo, test allineati al nuovo
contratto e amendment di prodotto; typecheck,9 focused,4 browser mirati e5 casi
prodotto PASS. Il successivo commit documentale aggiunge piano QH-51, questo
rapporto e catture sintetiche con hash verificati; secret guard e diff check PASS.
Entrambi restano nella stessa PR, senza riscrivere i commit precedenti.

Preservation: file protetti, ledger e configurazione/immagini/mount degli otto
container originali invariati. Le differenze di organizzazione/Space rispetto al
checkpoint storico esistevano già prima di questa correzione; nessuna differenza
nelle tabelle di fonti, understanding e governance. Il confronto prima/dopo di
questa correzione restituisce gli stessi esiti; nessuna modifica dati eseguita.
[Schermate e risultati](evidence/qh54-thematic-20261021/README.md),
[controlli preservation sanitizzati](evidence/qh54-thematic-20261021/preservation.json).

Residui: P2 QH-51 richiede approvazione tecnica prima di profili/API/inferenza;
P2 le azioni di import/partage restano disabilitate fino ai workflow autorizzati.
Prossima azione su questa consegna: review owner della PR22 e del contratto QH-51,
con merge e autorizzazioni operative separati. Nessun ticket/status creato o mutato.
