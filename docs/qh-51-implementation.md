# QH-51 — Comprensione semantica e review, incremento isolato

Mandato owner del2026-10-21; Jira [QH-51](https://contextlab.atlassian.net/browse/QH-51).
La [decisione di review selettiva](qh-51-assignment-review-decision.md) è stata
approvata esplicitamente durante l’implementazione. La verifica tecnica riguarda
fixture e infrastruttura usa e getta: **non dimostra la qualità semantica Mistral**.
Prova reale, accettazione prodotto, integrazione e attivazione VPS restano separate.

## Risultato e confini

Lo stesso Understanding Engine riceve informazioni manuali o messaggi originali
selezionati e propone interpretazioni atomiche con descrittori qualificati.
`SemanticExtractionProvider` adatta il prompt attraverso `LLMProvider`; estrattore,
resolver QH-32, repository canonico e outbox restano quelli esistenti. Il provider
simulato delle prove riconosce esclusivamente input sintetici completi ed esatti:
non è un classificatore per parole chiave, né un fallback del runtime.

I profili generici v2 conservano dimensione `thematic|semantic_role`, valore aperto,
certezza, riferimenti alle citazioni e review assegnata dal backend. I profili v1
e le revisioni storiche restano invariati. Il modello non può impostare owner,
identità canoniche, stato umano o current pointer. Una citazione corretta prova il
locator, non la pertinenza del tema o la verità dell’interpretazione.

La mappa riusa la boule e i nodi approvati: solo temi espliciti, massimo sei nodi
da due pagine bounded di20 elementi, current e ultime proposte. Non genera titoli
o descrizioni. Il click usa filtri dimensione/valore applicati prima del LIMIT
nella stessa lettura autorizzata e verificata su Neo4j. Pagine ulteriori sono
richieste dall’utente; copertura parziale esplicita, nessun conteggio globale.

QH-46 estende la propria operazione con `review_assignments`: accettazione/rifiuto
selettivo o scelta esplicita di un nome esatto dello stesso Space. Crea una nuova
revisione proposed, preservando testo, certezza, fonti e current pointer. Confermare
l’elemento non accetta automaticamente le assegnazioni. Un candidato di nome
irrisolto non crea un secondo nodo; nessun alias duraturo o fusione per similarità.
QH-47 mantiene identità e riconciliazione degli item canonici.

## File e responsabilità

| Percorso / funzione | Responsabilità |
| --- | --- |
| `app/understanding/semantic.py:SemanticExtractionProvider` | Prompt versionato e vocabolario esatto bounded, stesso port provider |
| `app/core/assignments.py:qualified_assignments` | Dimensioni, evidenze, normalizzazione NFC/spazi, duplicati discordanti invalidi |
| `app/understanding/extractor.py`, `selected.py`, `enrichment.py` | Validazione completa, risoluzione locator e pubblicazione Source/batch/outbox atomica |
| `adapters/postgres/semantic_profiles.py:semantic_definitions` | Profili v2 espliciti, registrati soltanto nei database isolati |
| `adapters/postgres/canonical.py:browse` | Filtro prima di LIMIT; hydration, ownership, fingerprint e freshness invariati |
| `app/review/service.py`, `adapters/postgres/review.py` | Stesso QH-46, nuove revisioni/receipt, lock e ricontrollo del nome nel medesimo scope |
| `apps/web/src/thematic.ts`, `ContextMap.tsx` | Gruppi espliciti multipli, esclusione rejected/candidate, copertura bounded |
| `UnderstandingWorkspace.tsx`, `ReviewControls.tsx` | Membri, citazioni/storia e review selettiva nello stesso percorso |
| `ManualInformation.tsx`, `EnrichConversation.tsx` | Scelta semantica esplicita solo se la composizione la offre; default letterale |
| `Understanding.tsx:usePage`, `Chat.tsx` | Attesa bounded della proiezione dopo pubblicazione riuscita, solo GET autorizzati |

I percorsi Python sono relativi ad `apps/api`. Nessun modulo Core importa adapter,
SDK LLM o framework; nessun nuovo servizio, tabella o migrazione.

## Definition of Done verificabile

Questa tabella registra il checkpoint locale prima della pubblicazione. Il gate CI
finale, il suo HEAD e lo stato corrente di review sono riportati nei check della PR
e nel commento di consegna Jira; non sono sostituiti dai conteggi locali.

| Criterio del ticket e del mandato | Classificazione / esito | Evidenza e limite |
| --- | --- | --- |
| Unico Engine, policy e Source/proposed/outbox atomici | Implementato e testato / PASS | Integrazione SQL/Neo4j: replay, conflitti e invalidità dell’intero batch; nessun fratello parziale |
| Interpretazioni atomiche, ruoli e temi aperti distinti | Implementato e testato con simulazione / PASS |8 elementi di riferimento nei due Space; qualità del modello reale NOT TESTED |
| Evidenze esatte e molteplici appartenenze | Implementato e testato / PASS | Citazioni/turni/revisioni esatti; indici errati, ambigui e fuori scope rifiutati |
| Review selettiva, fonte conservata, stati indipendenti | Implementato e testato / PASS | Rifiuto Nutrition, scelta Sommeil, revisione proposed, current invariato e conferma item separata |
| Nomi conservativi, stesso Space e nessuna fusione automatica | Implementato e testato / PASS | Riuso esatto dopo lock; candidato estraneo negato; qualità di naming del modello NOT TESTED |
| Mappa di temi reali, click membri e copertura esplicita | Implementato e testato / PASS | Due Space sintetici, fallback v1, membership multipla e pagine bounded |
| Refresh, Alice/Bob e fail-closed | Implementato e testato / PASS | Policy prima del provider, grafo indisponibile nega disclosure, nessun fallback |
| Timeout/429/invalidità senza retry o scritture parziali | Implementato e testato / PASS | Provider simulato singolo tentativo e conteggi canonici invariati |
| Disclosure/budget estrazione separati da chat | Proposta preparata / PASS per il mandato isolato | [Esperimento esatto](qh-51-real-experiment-proposal.md); autorizzazione economica NON ricevuta |
| Misure estrazione/temi/evidenze/nomi distinte | Implementato e testato con fixture / PASS | [Metriche provvisorie](evidence/qh51-20261021/fixture-metrics.json); non benchmark umano indipendente |
| Test offline/isolati, nessuna modifica dati demo o profili VPS | Implementato e verificato / PASS | Schema0006, zero registrazioni v2 persistenti; nessuna migrazione0007 |
| Una CI completa finale e PR dedicata | Verifica/pubblicazione pendenti | Nessun merge autonomo |
| Qualità reale e accettazione prodotto | Fuori dall’incremento autorizzato / NOT TESTED | Richiedono esperimento economico specifico e valutazione owner |

## Correzioni autonome e verifica

La verifica browser ha esposto il ritardo del worker che proietta una revisione
per ciclo: un batch semantico poteva superare l’attesa prevista per un singolo
elemento letterale. Dopo una pubblicazione riuscita la UI attende fino a16 GET
in7,5 secondi; il percorso ordinario conserva il limite precedente. Anche la
disponibilità della chat e il dettaglio appena pubblicato riusano questa attesa.
Un errore definitivo elimina i dati precedenti, senza bypass SQL o retry provider.

La regressione QH-39 mirata ha inoltre rilevato che il nuovo segnale di refresh
ricreava la vista avanzata dopo una conferma, perdendo la selezione. Il pannello
ora conserva lo stato di navigazione e passa un contatore di refresh alle letture;
non viene rimontato per una modifica dei dati. La verifica precedente su storico,
composer mobile e asset logo è passata (3 casi); il caso di review corretto è passato:1 PASS, inclusi replay, conferma e Bob.

Il ricontrollo canonico del nome riusato è stato spostato dopo il lock della
proiezione, evitando una race fra verifica del vocabolario e scrittura della review.
I test di riuso esatto/foreign name sono stati rieseguiti con esito PASS.

Controlli mirati eseguiti in container con dipendenze locked; i test SQL/Neo4j usano
`qh30-sql-test`/`qh30-native-neo4j-test`, database univoci e namespace dedicati.
Il helper privato `run-targeted.py` verifica nomi, rete test e assenza di porte
pubblicate prima di avviare pytest; non accede allo stack persistente.

| Comando / suite eseguita | Risultato osservato |
| --- | --- |
| `pytest` su assegnazioni, adapter semantico e regressioni enrichment |41 PASS |
| Integrazione mirata pipeline semantica, QH-46 e enrichment precedente |54 PASS |
| Nuovi controlli API capabilities/query/review e owner/freshness |4 PASS |
| Valutazione fixture due Space su entrambi gli schemi di test |2 PASS |
| Riuso nome dopo lock e negazione candidato estraneo |2 PASS |
| `playwright --grep 'QH-51 map\|QH-54 origin\|QH-54 groups\|QH-54 drafts\|chat reflow\|QH-53 tab keys'` |11 PASS |
| `playwright` scenario semantico due Space |1 PASS, dopo correzioni mirate |
| `playwright --grep 'QH-51 semantic conversation'` |1 PASS; tre POST chat esclusivamente simulati, nessuna HTTP Mistral reale |
| Regressioni browser QH-39 e QH-54 letterale/maquette |1+4 PASS, più3 casi storico/composer/logo già superati |
| `npm run build:web && npm run typecheck` |PASS nel container browser candidato |
| `ruff check --no-cache app adapters tests /workspace/scripts` |PASS |
| `make lint-workflows` |PASS con actionlint1.7.7 |
| Generatore esperimento in container `--network none`, `cmp` del JSON |PASS: quattro payload riproducibili byte per byte |

I conteggi si riferiscono ai singoli checkpoint mirati, con sovrapposizioni; non
si sommano come test indipendenti. Dettagli privati in
`.local-archive/qh51-20261021/`, [evidenza pubblicabile](evidence/qh51-20261021/README.md).
Il checkpoint hash verifica che i sorgenti applicativi delle immagini provate
corrispondano al checkout, senza stampare configurazioni o credenziali.

Il primo avvio hosted `39601957963` non ha completato il gate: l’audit storico
QH-33 confrontava l’estrattore corrente con il codice congelato del2026-10-16;
il controllo architetturale ha inoltre rifiutato una dipendenza review→understanding.
Correzioni: contratto puro condiviso in Core e nuovo `scripts/audit_qh33_history.py`
che materializza soltanto evidenze pubbliche manifestate e lo snapshot esatto
dell’estrattore e del test architetturale storici in una capsula temporanea.
Il checker corrente ammette `unicodedata`, libreria standard usata per NFC;
le dipendenze verso adapter/framework rimangono vietate. Manifest, audit originali,
metriche, capture e ledger congelati restano byte per byte identici; l’estrattore
corrente è verificato dai gate correnti, senza fingere che abbia l’hash storico.
Nessun secondo checkout o Engine runtime. Due regressioni verificano immutabilità
del runtime e rigetto di snapshot/evidenze alterati. Anche l’allowlist di verifica
OIDC include ora soltanto l’esatto GET capabilities approvato, mantenendo le
versioni precedenti per il verificatore read-only. Controlli mirati dopo correzione:
21 unittest QH-33, audit storico completo,63 test composizione/assegnazioni/
architettura,6 integrazioni reali review/scope e Ruff/actionlint PASS. I91 test
browser del primo avvio sono passati; il job si è fermato sul successivo controllo
OIDC della medesima allowlist, ora corretto. Il candidato corretto richiede un nuovo avvio del gate hosted dopo questa
correzione; il tentativo fallito resta documentato, senza dichiararlo CI verde.

Le fixture includono intenzionalmente un’assegnazione errata Nutrition per provare
il rifiuto. Prima della review:8/8 atomi e ruoli di riferimento,15/16 assegnazioni
tematiche corrette su15 di riferimento,8/8 locator esatti. Questi numeri misurano
conformità a output scritti a mano; non sono una stima delle prestazioni Mistral.
Copertura semantica completa e naming reale restano NOT TESTED.

## Integrazione precedente, preservazione e passi residui

PR22 integrata senza squash al merge `5b9c0f3d7ca1b42f80fa220c38c9700cdae5b7c5`,
preservando HEAD approvato `40cd6e7cb3347a31e324feac9b0a1daa87c97c11` e i suoi
commit. Quattro job già verdi riusati, nessuna ripetizione della sua CI. Jira QH-54
aggiornato con commento di evidenza10040, senza transizione automatica.
PR19 resta aperta e intatta a `18bac2c5f3e78e2b00fccb7b6705af19d02ad854`.

Checkout unico `/home/ubuntu/qh`, branch `feat/QH-51-semantic-understanding`, base
main verificata al merge PR22. Stop/up delle sole app durante il cambio branch
tramite comandi guarded; nessuna sostituzione di container/immagini/configurazioni.
La composizione VPS rimane letterale, senza provider semantico o nuovi profili.

Commit iniziale `41a850c`: contratti, Engine, profili e review canonica atomica;
41 controlli puri/legacy e54 verifiche backend mirate prima del commit. `a43df1b` aggiunge mappa, membri e review UI (scenario browser due Space PASS);
`5d84ca5` completa il lock sul nome e i controlli API/metriche (4+2+2 PASS mirati).
`e500bce` conserva la selezione della vista avanzata, con regressione
QH-39 eseguita e superata.
La CI finale è elencata nell’evidenza di consegna della PR.

Residui: P1 accettazione semantica reale e review PR, P2 eventuale attivazione VPS
con gate dedicato; nessun difetto tecnico estraneo viene implementato. Non vengono
modificati budget, ledger, allowlist, OIDC, dati canonici o PR19. QH-51 non è DONE:
review/merge, autorizzazione prova reale, accettazione prodotto e chiusura Jira
restano azioni distinte. Nessuna transizione Jira è implicita.
