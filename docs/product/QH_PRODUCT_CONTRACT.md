# QH Product Contract

Stato: riferimento funzionale principale, definito dal proprietario del prodotto.
Questo contratto guida tutte le implementazioni future. Le ipotesi e le proposte
indicate come aperte non sono decisioni approvate né autorizzazioni a implementare.

## Provenance del résumé canonico — correttivo owner

Il résumé rimane unico, libero nella formulazione e persistito con la versione
canonica. La generazione non limita più a due i supporti: usa tutti e soli quelli
necessari, entro i limiti tecnici già esistenti. Il contratto atomico UUM non cambia.
La revisione `recap_claim_review`, il suo HTTP obbligatorio e i controlli di claims,
spans e selezione successiva dei supporti sono rimossi dalla V1. Restano il contratto
strutturato del résumé, i supporti esatti negli item generati, la validazione delle
citazioni originali e della provenance da parte dell'Engine, e la pubblicazione
atomica. Non viene eseguita inferenza per caricare, condividere o consultare un résumé.

**Decisione owner, 2026-10-31 (semplificazione).** Il résumé è presentazione
probabilistica: non condiziona più la memorizzazione. Gli Understanding Items con
citazioni originali esatte e provenance validate vengono pubblicati anche quando il
résumé è assente o non valido; in quel caso la versione resta senza résumé e lo
segnala, e solo «Régénérer» avvia esplicitamente una nuova analisi. Citazioni non
valide negli item restano sempre un rifiuto. L'unica correzione ammessa è la
deduplicazione deterministica di supporti strettamente identici. Il résumé è unico:
i riassunti per documento e il filtro dei supporti in estrazione, legati alla vecchia
condivisione per PDF, sono rimossi; le versioni già persistite restano leggibili.

Owner, aperçu e guest riusano lo stesso résumé persistito. La Projection risolve i
supporti dichiarati nelle revisioni canoniche della medesima versione, con base
interamente presente. Il Guard verifica il testo divulgato (titolo e testo, senza
maschere né termini sensibili riconosciuti) e che ogni supporto sia un item divulgato:
un supporto escluso (testo sensibile, stato non ammesso, relazione pendente, o
citazione protetta quando le citazioni sono condivise) blocca il résumé. Le citazioni
originali non divulgate e le maschere sul testo di un supporto non lo bloccano: non
lasciano il perimetro e il testo del résumé è controllato direttamente.
I PDF originali rimangono una scelta esclusiva di consultazione/download.

**Limite esplicito:** la risoluzione esatta dei supporti e delle citazioni non prova
logicamente l'entailment del testo libero. La sintesi rimane proposta, senza conferma
umana automatica; non si attribuisce una certificazione semantica al résumé.

Le presentazioni v2, v3 e v4 già persistite, incluse le versioni modulari, usano gli
stessi controlli sul résumé generale, senza esigere un'attestazione del revisore. Snapshot approvati, contenuto
canonico e documenti rimangono immutati; nessuna migrazione o rigenerazione segue
dal correttivo. I diagnostici storici della revisione restano leggibili.

## Condivisione V1 del Context Space — decisione owner, 2026-10-31

Questa decisione sostituisce, per **nuove condivisioni**, la politica storica che
legava la conoscenza derivata dai PDF al permesso di consultarne gli originali.
Si condivide la Compréhension unica dello Space (documenti, dialoghi e altre fonti),
proiettata attraverso i filtri esistenti. Provenance, citazioni esatte, stato proposto,
autorizzazione owner/Space e verifica canonica/grafo restano invariati.

L'owner indica email, scadenza e facoltà di proporre modifiche. Consultazione e
interrogazione restano incluse; finalità e controlli facoltativi restano disponibili.
La scelta **Documents originaux accessibles**, vuota per default, concede soltanto
consultazione/download dei PDF. Cambiarla non modifica fatti interrogabili o recap.
L'interfaccia spiega esplicitamente che la conoscenza di un PDF non scaricabile può
restare interrogabile. Nessuna nuova revisione obbligatoria degli item o conferma
intermedia; il pulsante di creazione approva ancora l'esatta disclosure preparata.

**Esclusioni aggiuntive in linguaggio naturale: rinviate.** Non esistono campo libero,
classificazione manuale o traduzione di richieste in prompt di sicurezza. La V1
mantiene soltanto il Guard deterministico esistente: mascheramento di email, URL e
formati riconosciuti di coordinate/num ID; esclusione dei testi/citazioni con termini
sensibili riconosciuti (salute, sessualità, suicidio, password/chiavi API). Il filtro
lessicale non garantisce anonimato, rilevamento completo, né protezione semantica di
salari, negoziazioni o budget: non condividere lo Space se tali fatti devono restare
privati. Gli originali scaricabili possono contenere ulteriori dati non filtrati.

Il recap globale canonico è riutilizzato solo se interamente ammesso dai controlli
sul testo e sulla provenance, con i supporti canonici e la base descritti sopra.
Altrimenti la V1 mostra il fallback
privato: nessuna inferenza al caricamento, collage di estratti o promozione del
recap di un solo PDF a résumé dell'intero contesto. I fatti ammessi restano interrogabili.

Nuove richieste dichiarano `knowledge_scope: context`; questo valore è conservato
nella policy JSON approvata con report di scope v3. Richieste prive di questa scelta
esplicita o contenenti vecchi campi di selezione aggiuntiva vengono rifiutate, evitando
che client precedenti amplino inavvertitamente la condivisione. Nessuna migrazione,
backfill, nuova architettura o feature flag di rollout. Le policy senza questo marker
mantengono **esclusivamente per compatibilità** il vecchio filtro documentale e i loro
fingerprint. Nessun invito esistente acquisisce conoscenza o accesso agli originali:
il nuovo perimetro richiede un nuovo snapshot approvato. Revoca, scadenza, immutabilità
e risposte IA limitate al payload approvato restano vincolanti.

## Demo B: condivisione governata — decisione owner, 2026-10-25

**Share access to the context, not manually selected pieces of context.**

Le decisioni del 25 ottobre in [QH-55](https://contextlab.atlassian.net/browse/QH-55),
[QH-18](https://contextlab.atlassian.net/browse/QH-18),
[QH-19](https://contextlab.atlassian.net/browse/QH-19),
[QH-20](https://contextlab.atlassian.net/browse/QH-20),
[QH-21](https://contextlab.atlassian.net/browse/QH-21),
[QH-22](https://contextlab.atlassian.net/browse/QH-22) e
[QH-40](https://contextlab.atlassian.net/browse/QH-40) prevalgono sulle descrizioni
storiche incompatibili: selezione manuale obbligatoria e accesso tramite solo link
non appartengono al percorso ordinario Demo B. È un contratto approvato per le
prossime implementazioni, non una dichiarazione di funzionalità già disponibili.

### Access Policy, Disclosure Guard e Approved Snapshot

L'owner condivide lo stato di comprensione persistente dello Space configurando
email specifica del destinatario, finalità, diritti `READ` e/o `ASK_AI`, scadenza,
revoca e condizioni di protezione. Può limitare il provider IA nei percorsi in cui
QH ne controlla effettivamente l'accesso. Non deve selezionare decine di item o
revisioni; un'eventuale selezione manuale avanzata serve soltanto a restringere.

| Responsabilità | Contratto Demo B |
| --- | --- |
| Access Policy — QH-18 | Definisce chi può usare il contesto, per quale finalità, con quali diritti e per quanto tempo; il frontend non concede autorizzazioni |
| Outbound Disclosure Guard — QH-55 | Determina automaticamente scope canonico e rappresentazione minima divulgabile, con esclusioni, mascheramenti e controllo dei rischi |
| Approved Snapshot — QH-19 | Materializza il risultato già autorizzato, minimizzato e mascherato, con revisioni, policy, finalità e limiti riproducibili e auditabili; non è una copia dinamica dello Space né un semplice elenco di ID da risolvere sui dati originali |

PolicyService autorizza prima del recupero e della divulgazione. QH-55 costruisce
una allowlist deterministica e delimitata di coppie `item_id/revision_id` dello
stesso Space, riutilizzando il motore QH-14/15/16. Scope vuoto, ambiguo, cross-Space,
grafo non verificabile o relazione con endpoint fuori scope sono negati. Le proposte
non confermate sono escluse per default; l'owner può autorizzarne esplicitamente
la disclosure mantenendone stato e avvertenze, senza confermarle epistemicamente.

Prima dell'approvazione l'owner vede un'anteprima sintetica reale: contenuti
divulgabili, esclusioni, mascheramenti, rischi ed eventuali eccezioni da approvare
in modo mirato. Non è una checklist obbligatoria di tutti gli item. Il backend
applica il Guard prima di ogni uscita verso guest o provider, anche a preview,
metadati, citazioni, risposte IA ed errori. Le fonti integrali sono escluse per
default; provenienza e citazioni restano solo quando autorizzate e senza consentire
il recupero dei dati originali esclusi o mascherati.

Non si promette anonimizzazione perfetta: anche combinazioni di attributi possono
reidentificare. Se il rischio non è sufficientemente valutabile, negare oppure
richiedere una decisione mirata, senza divulgare prima dell'autorizzazione. Demo B
usa dati sintetici e non attesta sicurezza per dati sensibili reali in produzione.
Una modifica allo Space o alla policy non amplia né riscrive uno snapshot condiviso:
occorre un nuovo snapshot approvato. La revoca dell'accesso resta distinta dalla sua
storia immutabile.

### Destinatario e sessione guest

**Il solo possesso del link non concede accesso.** Percorso senza account QH:

1. Alice indica l'email precisa del destinatario e approva la disclosure.
2. QH crea un invito associato allo snapshot approvato e ai diritti autorizzati.
3. L'invitato apre il link e inserisce la propria email.
4. Il backend verifica la corrispondenza con l'email invitata e invia un codice monouso a quella casella.
5. L'invitato conferma il codice; solo allora riceve una sessione guest temporanea vincolata a invito, snapshot, email verificata, diritti e scadenza.

La verifica prova il controllo della casella, non l'identità civile della persona.
Prima della verifica non si mostrano contenuti, citazioni, anteprime o metadati
privati. Ogni richiesta riesamina sessione, diritti, scadenza e revoca, efficaci
anche sulle sessioni già aperte; altri destinatari richiedono inviti separati.
QH-20/22 governano OTP e token sicuri a vita breve, verifier protetti non in chiaro,
consumo monouso, limiti di tentativi/invii, rate limit e risposte anti-enumerazione,
TLS, sessione con cookie HttpOnly/SameSite sicuro e audit minimo. Email e token non
vanno esposti agli altri destinatari o nei log. Questo percorso guest non cambia
l'identità interna degli owner né il loro login OIDC.

QH-21 offre consultazione `READ` e domanda `ASK_AI` solo se concessi. La domanda usa
esclusivamente il payload e le citazioni autorizzati dello snapshot, tramite il
provider ammesso nel flusso QH-controllato; nessun recupero dallo Space live, dalle
fonti originali o da Neo4j fuori snapshot. Verifica guest, autorizzazione alla
disclosure e controlli economici precedono l'eventuale invio IA. Non si promette
di impedire al destinatario di copiare dati già ricevuti fuori da QH.

### Comprensione, collaborazione e accettazione

Validazione epistemica, autorizzazione alla divulgazione e diritto a proporre
modifiche sono tre decisioni distinte. Le sei dimensioni UUM strutturano la
comprensione persistente: non sono permessi né classi di sensibilità. Demo B non
attribuisce `PROPOSE_UPDATE` o `CONFIRM_UPDATE` ai guest.
[QH-41](https://contextlab.atlassian.net/browse/QH-41) resta roadmap successiva:
membership/ownership da decidere, contributi autenticati attraverso lo stesso
Understanding Engine e un Inbound Contribution Guard per attribuzione, provenance,
scope, input non affidabile, possibili bias/manipolazioni e conflitti. Ogni modifica
rimane proposta fino alla review autorizzata; controlli automatici non certificano
verità o assenza di bias. Questa evoluzione non blocca Demo B.

Sequenza: motore QH-14/15/16 già integrato → QH-55 scope e disclosure automatici →
QH-18 Access Policy Editor → QH-19 snapshot → QH-20 invito/verifica/sessione →
QH-21 esperienza guest → QH-22 sicurezza → QH-40 accettazione browser. QH-17
(selezione libera in linguaggio naturale), MCP e collaborazione non sono prerequisiti.
QH-22/40 devono verificare con fixture sintetiche: esclusioni/mascheramenti senza
leak su tutti i canali, isolation, grafo stale, provider o diritti negati, richieste
avversarie, immutabilità, link inoltrato inutilizzabile da solo, email errata, OTP
errato/scaduto/riusato, abuso dei tentativi e revoca/scadenza a sessione aperta.
L'accettazione include consegna e ricezione del codice tramite mailbox di test o
sandbox dichiarata, senza codice iniettato nel browser o email reali a terzi nei test.
Questa decisione non autorizza migrazioni VPS, cambi runtime o chiamate IA pagate.

## Chat et mémorisation — owner amendment, 2026-10-23

Le panneau chat place composer puis Mémoriser au-dessus de la conversation, avec
modèle/disponibilité/budget réel au pied. Le reste de la page et la carte restent
inchangés. Mémoriser ouvre trois explications: Comprendre, Proposer, Enregistrer.
Continuer autorise une fois l'analyse Mistral et la conservation de toute la
conversation courante (rôles/provenance préservés) comme source et propositions
non confirmées. Même Understanding Engine, citations exactes, publication atomique,
idempotence, aucune confirmation globale. Voir la proposition ouvre la review.
En cas de transport ambigu, ne pas prétendre qu'aucune écriture n'a eu lieu;
une nouvelle tentative explicite conserve la même identité d'opération.

## Risposte fondate sul dialogo — owner amendment, 2026-10-22

Un messaggio esplicitamente inviato può sostenere una risposta anche senza revisioni
canoniche. `support_basis` distingue dialogue/canonical/mixed/insufficient; QH ne
verifica compatibilità con gli input e le citazioni realmente trasmessi, non la
verità tramite la dichiarazione del modello. Alias canonici validi obbligatori
per canonical/mixed; nessuna invenzione o riconciliazione euristica. Dialogo e
risposta restano temporanei; estrazione UUM e conferma QH46 sono azioni distinte.
Rettifica owner successiva: `insufficient_context` è indipendente da
`support_basis`, indica insufficienza per una risposta completa e non vieta una
risposta utile parziale. La combinazione dialogue/true/[] è ammessa con dialogo
inviato; canonical/mixed richiedono sempre citazioni canoniche valide. La UI mostra
avviso di incompletezza separato da provenienza e conferma. Non dedurre il booleano
dalla categoria o dall'assenza di revisioni.
Gli errori owner/provenance/JSON/snapshot/budget bloccano, gli avvisi epistemici
restano separati. [Contratto tecnico approvato](../qh-51-response-support.md).

## UUM e nuovo ambiente dati — owner amendment, 2026-10-21

La successiva decisione owner adotta sei dimensioni universali di navigazione:
`situation_information`, `objectives_intentions`, `decisions_actions`,
`constraints_preferences`, `hypotheses_uncertainties`, `open_questions`.
Ogni elemento atomico ha una primaria oppure rimane non classificato. La mappa
mostra sempre sei nodi con presenza/vuoti verificati e click sui membri reali;
Non classés ed Éléments mantengono accessibile il contenuto senza primaria.
Non sono domini organizzativi né tipi strutturali; entità e relazioni restano
trasversali. Temi specifici dello Space diventano metadati aperti facoltativi.
Provenance, epistemica, temporalità, certezza e review restano indipendenti.
Frasi con significati autonomi richiedono proposte distinte con evidenze proprie.

Questa decisione sostituisce i nodi tematici primari QH-54/QH-51 e la precedente
strategia di migrazione funzionale: i dati sperimentali v1/v2 saranno abbandonati
nel nuovo ambiente attivo, senza backfill o adapter di conversione. Non riscrive
profili, benchmark, output originali o storia; l'immutabilità vale per i nuovi dati.
Il reset persistente resta soggetto a inventario, backup verificato e conferma
finale owner. Identità/Keycloak, segreti, ledger, budget e audit economici restano
conservati. [ADR 0010](../adr/0010-universal-understanding-model.md) e
[piano operativo](../qh-51-uum-reset-plan.md) distinguono autorizzazione e attivazione.
Nessuna inferenza, merge #23 o modifica PR #19/0007 è implicata.

## Browse-first understanding — owner amendment, 2026-10-17

> QH does not require users to know what to search for before showing them what their Context Space understands. Browsing is the primary experience; search is a complementary capability.

A Context Space is navigable evolving understanding. Opening it must expose
accessible existing understanding without first requiring the owner to guess a
query. Search remains complementary. Canonical content, open descriptors,
structural entities/relations, original sources, immutable revisions and provenance
are distinct; no descriptor is a mandatory domain category or proof of truth.

The structured preview is deterministic: literal excerpts and data-derived groups,
labelled with bounded/partial coverage, not interpretative narrative or a validated
synthesis. An explicitly validated canonical synthesis and a future LLM-generated
proposal are different artifacts; QH-12 defines no summary registration/selection
convention and runs no generative synthesis. A summary-like descriptor alone grants
neither summary authority nor validation. No automatic priority or semantic grouping.

Current confirmed heads, proposals and complete retained history remain separate.
An empty current view does not mean an empty Space; proposals and historical-only
content must be discoverable. Descriptor assignment certainty is independent from
human validation and real-world truth. Progressive disclosure proceeds from overview
to exploration, readable detail, sources and revisions; technical IDs/JSON remain
available without dominating the overview. No interactive confirmation/editing,
new ontology or advanced graph UI is implied.

[ADR 0005](../adr/0005-browse-first-context-understanding.md#product-decisions-and-rationale)
records the adopted decisions, motivations, alternatives, consequences and open
questions. The scoped read-only browse API preserves the canonical PostgreSQL,
replaceable native graph and shared policy guarantees of ADRs 0003/0004; QH-10
search remains unchanged. [QH-12 acceptance](../qh-12-context-understanding.md#owner-approved-acceptance-criteria)
makes this decision verifiable. Approval of the decision is not evidence of
implementation completion, test success or human acceptance.

## Principi confermati: definizione e oggetto fondamentale

QH è un ambiente sovrano di contesto, indipendente dai provider e dai modelli
di IA, che permette alle persone di costruire, conservare, interrogare, governare
e condividere selettivamente il proprio stato di comprensione.

Il suo oggetto fondamentale è il **Context Space**: uno stato persistente, evolutivo e
strutturato di comprensione di una situazione, costruito progressivamente
attraverso interazioni tra persone, IA e fonti informative. Non è una cartella
di file, un insieme di chunk vettoriali o una semplice cronologia di conversazioni.

Lo stato di comprensione può rappresentare, fra altri significati, i seguenti
**esempi non esaustivi**. Non sono categorie strutturali obbligatorie:

| Elemento | Significato |
| --- | --- |
| OBJECTIVES | Obiettivi |
| CURRENT STATE | Stato attuale della situazione |
| DECISIONS | Decisioni e relativo stato di validazione |
| HYPOTHESES | Ipotesi non necessariamente confermate |
| OPEN QUESTIONS | Questioni aperte |
| CONSTRAINTS | Vincoli |
| PREFERENCES | Preferenze rilevanti |
| CONCEPTS AND ENTITIES | Concetti e soggetti |
| RELATIONSHIPS | Relazioni tra elementi |
| UNCERTAINTIES | Incertezze |
| PROVENANCE | Riferimenti alle evidenze e storia delle informazioni |

Il modello è universale, estensibile e indipendente dai domini: uno stesso spazio
può combinare significati già noti e nuovi. `item`, `entity`, `relation` sono forme
strutturali per identità, revisioni ed endpoint; non costituiscono una tassonomia
semantica completa. Decisioni, ipotesi, osservazioni e altri significati possono
vivere nello stesso tipo strutturale generico, senza una categoria obbligatoria.
Contenuti strutturati e descrittori facoltativi possono esprimerli senza enum chiusi.
Tipi specializzati sono estensioni opzionali motivate da reali esigenze di schema
o regole versionate; non occorre registrare un tipo per ogni nuovo significato.

Provenienza, temporalità, versionamento, stato di validazione e autorizzazioni sono
dimensioni trasversali, indipendenti dal significato e dal dominio. Affidabilità della
fonte, confidenza del modello e validazione umana restano distinte. Questo elenco
non impone tabelle, enum o un grafo proprietario. Le fonti originali devono essere distinguibili dalle interpretazioni
e dagli elementi di comprensione derivati.

QH non è un agente che decide autonomamente il futuro stato di un progetto.
Le IA possono identificare, aggiornare e proporre elementi di comprensione;
le decisioni sostanziali e le autorizzazioni restano sotto controllo umano.
Proposte IA e revisioni correnti approvate sono distinte. Una modifica sostanziale
o una conferma crea una nuova revisione immutabile, senza sostituire automaticamente
la revisione corrente approvata. Confermare un'ipotesi come elemento da conservare
non significa considerarla un fatto verificato.

## Principi confermati: proiezioni e autorizzazioni

Il proprietario può creare proiezioni per finalità e destinatari differenti:
collaborazione, recruiting, servizi, agenti IA e altri utilizzi. Una proiezione
non equivale all'esportazione indiscriminata del Context Space.

QH governa quali informazioni siano effettivamente accessibili, a chi, per quale
scopo e secondo quali autorizzazioni. Il backend applica le autorizzazioni **prima**
che informazioni siano trasmesse a un LLM esterno. L'adapter MCP applica le
stesse autorizzazioni del Core; il client o il provider non sono il punto di
enforcement delle autorizzazioni QH.

## Principi confermati: modalità di accesso

1. **Client QH:** interfaccia universale nella quale l'utente sceglie il modello
   IA; QH gestisce direttamente recupero, conversazione e proposta di aggiornamento
   del contesto.
2. **Connettore MCP:** un client IA esterno accede a proiezioni autorizzate.
   QH controlla l'accesso alle informazioni, ma non necessariamente l'intero
   ciclo conversazionale del client esterno.

Un link di invito permette inoltre l'accesso a uno snapshot senza account QH,
soltanto dopo verifica dell'email invitata tramite codice monouso in Demo B.
Il link da solo non concede accesso. Modalità di
accesso diverse non autorizzano a cambiare il perimetro delle informazioni condivise.

## Principi confermati: differenziazione e architettura

Il valore distintivo è uno stato di comprensione persistente, controllabile dal
proprietario, indipendente dalle IA, interrogabile, portabile e condivisibile
selettivamente. Il contesto possiede identità e ciclo di vita propri, indipendenti
dai modelli che lo utilizzano. RAG, Graphiti, Neo4j, routing LLM e automazione
sono strumenti possibili; non definiscono il prodotto.

- QH Core è indipendente dai framework infrastrutturali.
- QH-30 autorizza un QH Context Engine nativo dietro ContextEngine; il prototipo
  Graphiti resta conservato nella branch storica, non una dipendenza di runtime.
- Neo4j è il Context Graph operativo derivato e ricostruibile, secondo
  [ADR 0003](../adr/0003-native-context-engine.md).
- PostgreSQL è canonico per fonti originali, comprensione persistita, revisioni,
  entità e relazioni semantiche canoniche, proiezioni approvate e governance QH.
  Neo4j contiene soltanto la proiezione operativa e gli indici utili al recupero;
  deve poter essere ricostruito dai dati canonici e dagli embedding conservati,
  senza ripetere interpretazione LLM o dipendere da formati Graphiti. La ricostruzione
  non modifica automaticamente decisioni umane approvate.
- FastAPI espone le API applicative; MCP è un adapter esterno.
- Le informazioni non autorizzate non devono essere trasmesse ai provider IA.
- La piattaforma deve restare compatibile con un'evoluzione SaaS, self-hosted o ibrida.

I confini tecnici stabiliti sono descritti in [architecture.md](../architecture.md)
e [ADR 0001](../adr/0001-modular-architecture.md). L'ADR sui confini non approva
implicitamente un modello canonico di comprensione o una mappatura di persistenza.

## Scelte della V0.1, rivedibili solo con approvazione

Le proiezioni **approvate sono snapshot immutabili**. Un cambiamento del contesto
originale non deve ampliare silenziosamente le informazioni già condivise.
Ogni Share punta a uno specifico Approved Snapshot, non alla Projection modificabile.

La V0.1 è un POC locale, non una release pronta per dati sensibili o MCP pubblico
multiutente. Usa lo scaffold React/TypeScript/Vite, FastAPI e MCP Python e i cinque
servizi Compose già stabiliti. Non implica che tutte le capacità di prodotto
siano implementate, né autorizza implementazioni anticipate di ticket futuri.

## Modello V0.1 approvato

Si distinguono Context Space, Source, Understanding Item, Projection, Approved
Snapshot e Share. Ogni fonte, elemento e proiezione appartiene a un solo Context
Space; una proiezione produce più snapshot e uno snapshot può avere più share.
L'owner delle entità figlie deriva dallo spazio, senza duplicazioni inutili.

Nel modello storico QH-4 gli Understanding Items hanno identità stabile, spazio, categoria, contenuto
strutturato, origine, validazione e provenienza. Categorie storiche QH-4: objective,
current_state, decision, hypothesis, open_question, constraint, preference,
concept, entity, relationship, uncertainty. Classificazione epistemica e stato
di validazione sono dimensioni differenti.

Chiarimento approvato QH-30/QH-8/QH-10 (2026-10-15): il nucleo semantico è
universale e queste categorie non chiudono la tassonomia. Tipi e proprietà sono
estensibili tramite schemi versionati; uno spazio può mescolare domini.
Provenienza, revisioni, temporalità, incertezza e validazione restano comuni,
con governance indipendente dal dominio. I Domain Packs sono una possibilità
futura componibile, non una funzionalità implementata. Il modello SQL QH-30 è approvato: registro unico tipo/versione, forme strutturali
item/entity/relation, endpoint universali con identità e revisioni immutabili,
temporalità comune. Le migrazioni 0003/0004 e il worker sono stati verificati in isolamento e attivati
con autorizzazione nel cutover del 2026-10-15 (immagine `fd50b1b`, evidenze QH-30).
La [semantic foundation post-cutover](../qh-semantic-consolidation.md) attua i tre profili generici
iniziali, i descrittori multipli facoltativi con valore libero e certezza dell’assegnazione
(distinta dalla validazione dell’elemento) e la selezione strutturata autorizzata.
Queste scelte sono approvate dal proprietario e attivate con autorizzazione nella
consolidazione finale: PostgreSQL 0005, tre profili generici e selezione interna
operativa, immagini da main `c723d32` senza mount dei sorgenti applicativi.
Il [registro deployment](../deployments.md) conserva evidenze e storia 0004/fd50.
Nessun nuovo contratto pubblico, estrazione LLM o ricerca vettoriale è implicito.

Le revisioni dei singoli elementi persistenti sono immutabili; non si introducono
event sourcing completo o revisioni globali del Context Space. Uno snapshot
contiene esattamente contenuti e revisioni autorizzati all'approvazione.
PostgreSQL garantisce integrità, unicità, coerenza e protezione dell'immutabilità;
QH Core decide le autorizzazioni, con enforcement backend anche per gli adapter.

ContextId identifica lo spazio, con identità distinte per elementi, revisioni e
risultati di recupero. Gli adattamenti minimi dei contratti QH-2 sono autorizzati.
[ADR 0002](../adr/0002-canonical-understanding-persistence.md) registra D1–D7,
cardinalità e perimetro QH-4 approvati; la [revisione QH-4](QH4_MODEL_REVIEW.md)
conserva le alternative storiche. Le precedenti raccomandazioni aperte non
prevalgono sulle decisioni approvate.

QH-4 predispone schema e migrazioni; non implementa ingestione Graphiti, validazione,
Projection Engine, link, chat o client React. Tabelle differibili senza perdere
integrità sono introdotte nei relativi ticket. Non replicare il grafo Graphiti
in PostgreSQL né implementare un Comprehension Graph proprietario durante QH-4.
Aggiornamento autorizzato del 2026-10-15: QH-30 sostituisce la scelta Graphiti con
un motore QH nativo (ADR 0003), senza riaprire le altre invarianti. Il modello SQL
è approvato, verificato e attivato a 0004. Le categorie storiche non classificano
le nuove revisioni: il binding registrato governa schema e forma, mentre il significato
non è limitato ai nomi del registro. Source Vault (QH-31) resta futuro: la rappresentazione inline
non impone che i byte originali siano conservati in PostgreSQL.

## Chiarimento approvato — ingresso della comprensione (2026-10-16)

QH possiede un unico Understanding Engine indipendente dai provider per validare,
riconciliare in modo governato e persistere proposte nel Context Space. Il client QH
può estrarre dalla propria fonte conversazionale tramite LLMProvider (oggi esperimento
Mistral, in futuro modello open-weight ospitato sostituibile). Client esterni MCP
possono in futuro inviare direttamente proposte strutturate previa autorizzazione,
senza obbligo di trasmettere tutta la conversazione o di una seconda inferenza.
Entrambi i canali convergono sulle stesse invarianti canoniche e di governance.

La provenienza distingue supporto verificabile su fonti originali disponibili e
proposte dichiarate esternamente senza verifica diretta. Nessuna proposta IA viene
confermata automaticamente. La decisione non introduce ora un tool/API MCP, una
nuova autorizzazione, servizio, modello ospitato o migrazione: il relativo ingresso
è solo documentato in [ADR 0004](../adr/0004-unified-understanding-engine.md).
I vincoli esistenti di scope, validazione e disclosure restano in vigore.

## Ipotesi da validare ed evoluzioni del modello

Riutilizzo delle fonti fra più spazi, ontologia completa, formati di interoperabilità
e strategie concrete di ricostruzione del motore restano evoluzioni da valutare.
La ricostruibilità è un requisito approvato, non un test già superato da QH-4.

## Evoluzioni future e regola di consultazione

SaaS, self-hosted, modalità ibride e adapter alternativi sono direzioni da
mantenere possibili; non sono funzionalità da costruire automaticamente ora.

Prima di decidere su Context Space, comprensione, provenienza, proiezioni,
ownership, autorizzazioni o condivisione, leggere le sezioni pertinenti di questo
contratto e gli ADR. Nuove decisioni strutturali richiedono approvazione preventiva;
i dettagli implementativi coerenti con le decisioni già approvate sono autonomi.
Non riaprire scelte approvate salvo contraddizione concreta, rischio nuovo o
vincolo tecnico che le renda impraticabili.

Applicare **STOP AND ASK** secondo [AGENTS.md](../../AGENTS.md) quando manca una
decisione, esiste una contraddizione o cambia una responsabilità strutturale.
Esporre alternative, conseguenze, vantaggi, rischi e raccomandazione, poi attendere
approvazione per la parte coinvolta. Un ticket non autorizza implicitamente a
risolvere queste scelte o a derogare al contratto.

## Scoped ephemeral contextual chat — owner amendment, 2026-10-17

The owner approves QH-13's distinct single-Space owner CHAT operation, not a
promotion of READ_CONTEXT to disclosure authority. Confirmed-current is default;
proposals need explicit opt-in, retain unconfirmed state, and canonical history is
excluded. Browser dialogue and model answers remain temporary/untrusted, never
canonical understanding or confirmation. Browsing remains primary. See
[ADR 0006](../adr/0006-scoped-contextual-chat.md) and the
[implementation/verification record](../qh-13-contextual-chat.md).

Mock is the default. External inference requires separate explicit authorization,
private backend configuration and a bounded budget; key presence is not consent.
Semantic correctness and robustness of a live model are not established by canonical
reference checks. Conversation-to-understanding remains QH-39, local-model hosting
remains QH-35, and no second engine, canonical store or automatic confirmation follows.

## Demo A experience — owner amendment, 2026-10-17

This later owner decision sets the **next UX increment**, not an implemented change
in QH-13 / PR #14. Earlier browse-first and scoped-chat sections retain the decisions
and implemented placement at their checkpoints. ADRs 0003/0004/0005/0006 and their
historical evidence are preserved. The owner now chooses chat as the primary
in-Space interaction, with understanding exploration accessible without a query.
This updates interaction priority, not canonical responsibilities or epistemic rules.

The durable principle is that QH never requires users to know what to search for
before revealing what their Space understands. Search remains complementary;
chat-first placement must not hide the existence or state of canonical understanding.
The expandable explorer must be visible and usable before sending a question.

### Product decisions and rationale

| Adopted decision | Rationale / alternative considered | UX and architectural consequences / limits |
| --- | --- | --- |
| After login, open `Mon environnement` | Establish orientation and owner overview instead of automatically reopening the last Space | Future client routing change; retain Code+PKCE and in-memory tokens. Current QH-11 return-path behavior is not claimed changed here |
| Dashboard presents the owner's Spaces; evolve toward `Mon environnement → Domaine → Context Space` | Express a personal environment instead of a flat document-search entry point | Presentation direction only. No Domain entity, storage, fake grouping or sharing capability is approved by the hierarchy; a real Domain model needs a separate decision |
| Inside a Space, `Discuter avec ce contexte` is primary | Let owners ask about their authorized understanding; prefer conversational entry over the current exploration-first layout | Future UI reordering, not a second engine. QH-13 answers remain ephemeral; proposal inclusion requires explicit choice and visible unconfirmed state |
| `Explorer la compréhension` is a visible expandable section | Progressive disclosure preserves orientation without making IDs/JSON the main experience | Reuse overview, open data-derived descriptors, items/entities/relations, provenance and revision history. No mandatory search query, taxonomy, editing or automatic confirmation |
| QH visual identity extends to login while Keycloak hosts OIDC | Avoid a disconnected experience; reject a custom replacement login/authentication system | Use supported presentation/theme mechanisms. Preserve issuer, redirect, state/verifier, token boundaries and owner policy; activation needs separate runtime approval |
| Start with the owner's logo and presentation identity: white, black, red, glass sphere, restrained iridescence | Coherence with supplied product references; reject an invented logo or a general redesign in this PR | Assets are not assumed available. Confirm source/licence, light/dark readability, contrast and keyboard use; effects never obscure epistemic labels. Public asset selection and typography await owner references |

A deterministic preview, an explicitly validated canonical synthesis and a future
LLM-generated proposal remain different. Chat does not silently create any of them
or confirm content. Descriptor certainty, confirmation, revision history and source
support remain separate. Reordering UI does not authorize a new public contract,
Domain model, provider disclosure, registry entry, migration or deployment.

The [operational plan and proposed small UX ticket](../qh-13-demo-a-plan.md)
record fixture selection, write inventory, source/ID fingerprints, create-receipt
reconciliation, backup/failure controls, asset hand-off and Mac checks. The next UX
ticket must be confirmed before creation; no ticket or UI implementation follows
from this documentation alone. Asset details and Domain semantics remain open.

Keep three capabilities distinct: **QH-13** reads bounded authorized understanding
and produces ephemeral answers; **demo seed** is a separately authorized synthetic
publication using QH-8/QH-32 and CanonicalRepository/outbox/worker; **QH-39** will
connect an authorized conversation to a source revision and new proposed understanding.
No seed is executed here. A script materializing fixture expectations is not LLM
comprehension; current retrieval is bounded UUID enumeration, not semantic ranking.

Any real Mistral demo needs separate explicit synthetic-only transmission/spending
consent, exact scope/payload and a verified maximum **EUR 5** envelope with the
prepared stricter request/token/USD limits. Existing ledgers and frozen outputs
remain intact; no call, confirmation or persistent import is authorized by this
amendment. A future local model remains replaceable through LLMProvider.

## QH-43 presentation checkpoint — owner approval, 2026-10-18

The owner approved the QH-43 plan (`41ee02f`) and independently authorized its
asset-independent layout: every successful login lands at Mon environnement,
owned Spaces remain discoverable, chat is primary inside a Space, and canonical
exploration remains visible as an accessible disclosure before any question.
This implements the earlier Demo A amendment without changing domain, ownership,
policy, ephemeral chat, source/validation semantics or public contracts.

The [checkpoint and original-asset proposal](../qh-43-visual-proposal.md) distinguish
the working neutral layout from private design references. Final branding requires
owner approval of selected original assets; the missing authoritative SVG is not
reconstructed. Keycloak theme source preparation follows asset approval, and VPS
activation still requires separate consent. Existing warnings derived from verified
canonical proposed states remain mandatory even if generated prose omits them.
No presentation mockup authorizes Domains, sharing/projections, provider selection,
conversation ingestion, synthetic medical facts, paid inference or confirmation.


## QH-43 second UX checkpoint — owner direction, 2026-10-18

The owner accepts the functional layout as a base rather than final UX. Make the
question and actual question/answer sequence visually primary; place implementation
explanations in a secondary disclosure. Explicit proposal inclusion and applicable
warnings derived from canonical states must remain visible, independent of provider
prose or disclosure state. Mock output remains explicitly extractive, not generative
comprehension. Keep the full explorer discoverable before a question; technical IDs,
JSON and extended provenance remain inspectable without dominating initial reading.

The owner confirms the seven files in `QH-design 2/` as the intended references;
no ZIP is needed. Approved direction: original compact decorative bubble on
Mon environnement/welcome, white/black, red accents and discreet iridescence.
No portraits or future-feature mockups as product controls. A private, traceable
comparison of existing logo variants precedes public asset selection. Simple
crops are derivatives, not supplied logo masters. Logo choice and public usage
rights still require owner confirmation; do not invent/redraw the mark. Keycloak
theme preparation waits for that approval and activation needs separate consent.
See the [dated checkpoint](../qh-43-visual-proposal.md). No new domain, capability,
AI inference, canonical write, provider disclosure or confirmation follows.


## QH-43 selected identity — owner approval, 2026-10-18

The owner selects the precise original geometric red-circle/black-H mark shown
in their approval message. Logo comparison is closed: do not offer alternate UI
marks, rotate/reinterpret it or generate creative variants. Minimal faithful crops,
responsive placement and whole-mark icon resampling are authorized for QH product
preview/frontend integration and source-only login preparation. This is not a
claim of a general artwork licence or final UX acceptance.

Use the selected mark as the common identity on welcome, Mon environnement and
Space headers. Keep the original iridescent bubble compact/decorative on welcome
and environment only; never displace the in-Space question. White/black, restrained
red, visible proposal consent and canonical epistemic warnings remain mandatory.
Full explorer/provenance/history stays accessible. No new product capability or
AI behavior follows from the visual references.

The [selected identity checkpoint](../qh-43-branding-checkpoint.md) records source
hashes/crop provenance, raster limitations and actual screenshots/tests. Keycloak
inherits its existing credential/validation/OIDC forms; sources and isolated preview
are authorized, **persistent VPS activation is not**. Realm, identities, permission,
session and Code+PKCE contracts remain unchanged. Merge and Jira DONE require
separate owner approval.

## QH-43 hero/capsule iteration — owner correction, 2026-10-18

The owner requests a wider immersive welcome with a large **central** original
bubble, a more prominent central environment bubble, and owned-Space capsules with
that same original artwork. This supersedes the earlier compact/side-decoration
choice **on those surfaces**; the chosen mark, image bytes and Keycloak preparation
are unchanged. No bubble hero is introduced ahead of the in-Space question.

| Decision | Rationale / alternative | Consequences and limits |
| --- | --- | --- |
| Full-width centered welcome and central environment artwork | Replace the narrow card/side ornament with a clearer QH environment identity | Responsive CSS, original proportional image only; no animation, new illustration, Domain or graph meaning |
| One bubble per owned Space, centered title above its capsule | Show navigable context objects rather than administrative rows | Same decorative asset for every Space; it encodes no status, category, count, sharing or unique generated identity |
| Shorten overview titles after ten user-perceived characters, adding `…` | Keep captions consistent without renaming canonical Spaces | Grapheme-safe display only; complete accessible link name, tooltip, metadata and detail heading remain intact. Navigation/React identity uses the Space UUID, never the truncated label |
| Give chat a larger primary panel/composer | Make the conversation visually dominant | Existing provider behavior, explicit opt-in, epistemic warnings and ephemeral state remain unchanged. Explorer and Space metadata stay visible disclosures below chat |
| Explain excluded proposals separately from missing active support | An empty answer must not imply no understanding exists | Use authorized current/proposed availability; explicitly explain unchecked proposal inclusion before and after an insufficient answer. Never select it automatically |
| Distinguish no retained understanding revisions from history-only | No current/proposed hit alone proves neither an empty Space nor absent sources | Only when both active views are empty, read one authorized graph-verified history row. On error stay unavailable; never fall back to SQL or call missing data empty. History remains excluded from chat |

The empty state describes **understanding revisions**, not absence of source-only
records or other Space metadata. Insufficiency for a particular question remains
different from overall Space completeness. UI explanations are deterministic;
no textual rules invent model answers or semantic relevance. No new persistence,
API, policy, real provider activation, confirmation or Keycloak realm change.


## QH-43 real branded login — owner decision, 2026-10-18

The owner now requires the actual VPS redirect login to use the selected original
QH mark/bubble, light white/black/red presentation and French text. This explicitly
supersedes the earlier preparation-only gate **for theme activation in the demo
qh realm**, after preflight, narrow backup, rollback and live verification.
[Controlled operation and evidence](../qh-43-keycloak-activation.md).

| Decision | Rationale / alternative | Consequences / boundary |
| --- | --- | --- |
| Activate the existing inherited Keycloak QH theme | Isolated screenshots alone do not satisfy the real user experience | Only static theme files and four realm presentation/language fields; preserve upstream forms and OIDC security |
| Send standard `ui_locales=fr` from the QH client, enable fr/en/default fr in the realm | Browser English can override only setting the realm default | Presentation hint only; no issuer/client/redirect/scope, token storage, session lifetime or identity change |
| Keep real Keycloak-hosted credential entry and redirect | Avoid React password forwarding, ROPC and iframe embedding | Keycloak URL remains visible; this is not a same-origin/native React auth claim |
| Verify actual VPS authentication and reversible theme selection | Show actual desktop/mobile and existing Alice/Bob security behavior | Wrong password and state/nonce/PKCE controls are expected failures, not silent exceptions; real regressions roll back |

QH-42 retains any future BFF/same-origin architecture and threat model. QH-45
(real LLM chat) is not started here. No credential export, new auth/provider system,
canonical write, paid inference, automatic confirmation, merge or Jira DONE.

## QH-45 scoped provider session — owner-approved contract, 2026-10-18

The owner explicitly approves a single authenticated owner/Space/model/snapshot
session for contextual chat, with disclosure consent **separate** from proposed
revision inclusion. This is approval to implement/test offline, not transmission,
spending, live provider configuration, canonical writes or a new OIDC contract.

Mock remains default and available. A real session additionally requires a private
server allowlist/authorization/ledger and explicit browser consent after preview
of the exact authorized context, current question and temporary dialogue. CHAT
policy and graph-backed canonical verification apply before disclosure; immutable
revision aliases/provenance and canonical epistemic warnings remain mandatory.
Context changes require renewed consent. No historical/rejected data is added.

The grant binds owner, Space, model, token and exact context; at most five minutes,
never beyond verified access-token/private-authorization expiry. Revocation,
logout, changing Space/proposal choice/provider, new discussion, reload or backend
restart must not silently resume it. Local cleanup cannot recall already transmitted
data; unacknowledged offline revocation relies on the short expiry. Default is
three requests/0.01 USD, configurable server limits within the aggregate existing
eight attempts/0.20 USD and owner-approved EUR ceiling. Opening new sessions cannot
reset durable accounting. No retry, fallback or silent renewal. Pending/unknown
spend and errors stop further automatic work.

The 300-second OIDC lifetime is unchanged: late consent may leave only seconds.
QH-42 owns any future renewal/BFF/session redesign. Generated prose, canonical
reference identity, source provenance, validation state and semantic support are
distinct. No model response becomes Understanding State (QH-39 remains separate).
[ADR 0007](../adr/0007-scoped-provider-sessions.md) records rationale and alternatives;
[implementation/evidence](../qh-45-generative-chat.md) separates measured offline
checks from the unexecuted real-session experiment. QH-49 tracks reproducible
Keycloak theme delivery and is required before its future ordinary recreation.


## QH-45 RESULT FIRST and usable scoped provider — owner decision, 2026-10-19

The owner approves a usable private-POC Mistral choice for Alice's synthetic Projet
pilote, not another preparation checkpoint. The normal experience is **choose
Mistral → inspect what is shared → consent → converse**. Mock remains the default.
Governance, manifest hashes, spend reservations and receipt checks run automatically;
implementation details remain inspectable but never become extra owner approvals
inside the already authorized scope. Separate proposed-content and external-
disclosure consent stay visible, affirmative and required for every new session.

Provider availability lasts exactly 30 days from activation, with no automatic
renewal or widening to other Spaces/owners/models. This replaces the earlier
24-hour receipt maximum for this authorization only. Each conversation grant still
lasts at most five minutes and never outlives its verified OIDC token; no refresh/BFF
or automatic resumption. Subsequent manually submitted questions need no additional
consent while the snapshot, owner/scope/model/permissions and grant remain unchanged.

Prices are verified automatically from the fixed official model documentation,
without key, user data, Mistral API GET or paid generation. Successful checks are
fresh for at most 24 hours; unrecognized/increased prices, failed verification or
retired model fail closed after expiry of the last verification. This neither
extends the authorization nor resets accounting. Pinned prices remain conservative
cost ceilings, not invoice guarantees. Backend receipts additionally pin the exact
six proposed revisions/context snapshot; a changed snapshot is outside this receipt.

The fixed cumulative ledger allows at most 8 POST/0.20 USD across all sessions,
including at most one Codex real smoke; each session is at most 3 POST/0.01 USD.
No daily/new-session reset, retry/fallback, implicit confirmation, canonical chat
persistence or additional model lookup. Private expiry/global residual budget are
visible in the product. Explicit revocation and late-answer suppression apply.
A narrowly backed-up backend-only configuration/recreation is authorized; preserve
all other containers, OIDC, canonical data and historical ledgers. PR #16 remains
open and QH-45 cannot be DONE until the owner's later review/merge authorization.

## Owner-approved UX V2 amendment — 2026-10-19

Seven editable personal domains organize existing Spaces without classifying their
meaning or granting access. A Space can belong to several domains without identity
or content duplication. Profile/preferences are transversal. Organization is
owner-only metadata, distinct from canonical understanding.

Explicit owner confirmation/rejection appends immutable review revisions; only
confirmation advances confirmed-current. Text correction appends a human proposal.
Previous evidence, extraction, lineage and history remain reconstructible. Pending
review and historical proposed retrieval are distinct. Neither a descriptor nor
a quote establishes semantic correctness. Presentation of lineage does not imply
automatic reconciliation. [ADR 0008](../adr/0008-personal-organization-and-owner-review.md)
records the approved contracts and limits; [QH-50](../qh-50-ux-v2.md) tracks execution.

### Later UX V2 navigation/login refinement — 2026-10-19

Mon environnement is a destination chooser: two compact independent shelves, not a
persistent domain filter. A domain opens its own stable-ID view and only its associated
Spaces; an explicit nested route preserves the actual entry domain when opening a
Space. Resume/direct Space links never invent domain provenance. Editable organization,
profile and all/unclassified collections remain secondary. A missing/removed domain
does not delete its Spaces. The domain view's creation action preselects its primary
domain; membership and canonical understanding remain separate.

An explicitly requested domain route can survive validated OIDC reauthentication;
ordinary login still opens Mon environnement. This is not automatic last-Space resume
or persistent browser tokens. The selected original login mockup is a presentation
reference for the native Keycloak form, not permission to implement React password
collection or change identity/session contracts. QH-50 source refinements are tested
in isolation; durable theme installation/activation remains subject to QH-49 and
explicit runtime authorization. See [ADR 0008](../adr/0008-personal-organization-and-owner-review.md#later-owner-refinement--hierarchical-navigation-2026-10-19).

### Official three-page visual reference and destructive-action gate — 2026-10-19

The owner's three approved maquettes are the visual reference for environment/domain/
Space layout, not fixtures to import. Cards show authorized full names within two lines;
the earlier ten-character visual cut is superseded. The domain hero is centered. Space
chat is primary beside secondary sources, independent canonical understanding and metadata;
mobile support navigation preserves temporary chat/review state. Sources always refer to
actual response revisions. Mock replies and unconfirmed support remain clearly identified.
Unavailable descriptions, avatar identities and example answers are never invented.

Owner assignment uses the existing optimistic organization version and explicit saving.
Supprimer requires a typed **exact full Space name**. No deletion/archive lifecycle is
approved or implemented: the complete confirmation UX states that limitation and its final
execution stays disabled. No destructive request, successful deletion, archive or retention
promise is simulated. A future lifecycle decision must precede any enabling backend change.
See [ADR 0008](../adr/0008-personal-organization-and-owner-review.md#later-owner-amendment--three-official-maquettes-2026-10-19)
and the [visual comparison record](../qh-50-maquette-fidelity.md).


## Selected chat enrichment — owner QH-39 increment, 2026-10-19

Conversing, explicitly retaining a selected source/proposals, and human confirmation
are distinct actions. `Enrichir ce contexte` previews the exact selected messages,
requires separate persistence consent, and produces only `proposed` understanding
through the single Engine. No chat answer itself writes or confirms understanding.
The owner remains free to review/correct/refuse through the existing workflow.

Submission identity and source acquisition time are authenticated/server recorded;
browser dialogue roles/times are declarations. Assistant text is not human evidence.
Source snapshots remain reconstructible with exact text, turn locators and provenance.
Failed generation/validation/publication commits nothing; valid empty extraction is
an explicitly labelled zero-proposal result, never fake understanding.

The first implementation is a visibly labelled offline literal control, not semantic
classification or a live Mistral extraction. Chat-provider consent/budgets do not
extend to extraction; no external call or historical ledger reset is authorized.
No advanced reconciliation/ranking/sharing or MCP ingress is implied. See
[ADR 0009](../adr/0009-selected-conversation-enrichment.md) and
[QH-39 acceptance](../qh-39-living-context.md).


## QH-52 approved development stabilization — 2026-10-20

Owner approval of contracts A/B/C in [QH-52](../qh-52-stabilization.md) permits
implementation and isolated testing, with persistent activation separately gated.
Bounded memory-only OIDC refresh preserves temporary drafts without browser storage.
Optional verified-session disclosure remains tied to the same exact canonical
snapshot, Space, model and purpose, for at most thirty minutes within the work
session and administrative availability. Token renewal and new consent cannot reset
durable work-session or aggregate budgets. New data or wider scope require consent;
provider enablement, disclosure permission and epistemic confirmation remain distinct.

Owner-only domain/Space descriptions are plain organizational metadata (500
characters) in schema0006, not understanding, classification or permission. Empty
Spaces can receive a first user-authored information through existing explicit
QH-39 source/proposal persistence without an external provider. Literal retention
is labelled and unconfirmed; QH-51 semantic extraction remains future. Normal chat
uses an authorized real provider or explicit unavailability; mock is test/replay only.

## QH-53 approved presentation refinement —2026-10-20

The owner-approved definitive maquettes use a single ordered Space navigation:
Discussion, Éléments, Modèle, Conseils, Paramètres. Browsing remains available before
any question through Éléments, with provenance/history/review retained. The primary
conversation avoids administrative vocabulary; actual exact-snapshot disclosure,
affirmative proposed inclusion, separate persistence consent, backend policy and
accounting are preserved in accessible dialogs or secondary disclosures.

Adding an element accepts general user-authored meaning through existing literal
source/proposal persistence; it introduces no mandatory semantic categories.
Mémoriser cette conversation conserves only explicitly selected messages, without
claiming a durable whole-chat archive, semantic extraction or human confirmation.
Conseils are editable question starters requiring explicit send, not generated
recommendations. Model/budget come from real capabilities; unavailable settings and
unimplemented deletion/sharing controls are not displayed as functioning actions.

## QH-54 direct declaration and understanding presentation — owner amendment, 2026-10-20

The explicit manual **Ajouter au contexte** button expresses consent to preserve
that supplied text; no second self-confirmation checkbox is needed. QH-39 retains
the source, provenance and proposed canonical revision without certifying truth or
performing semantic classification. Selected conversation memory and external
provider disclosure retain their distinct consents and scopes.

Understanding distinguishes literal owner declarations (only when established by
stored provider/locator/source evidence) from actual QH interpretations. Direct
information is presented as **Vos informations** even while its current backend
lifecycle remains proposed; the real state stays inspectable. AI proposals remain
**À vérifier** until QH-46 human review. Corrections preserve immutable revision and
new-human-proposal rules. No formal lifecycle change or auto-confirmation follows.
A primary list/detail and complementary data-derived overview open through
Éléments → Compréhension; source/history/audit remain accessible secondarily.


## QH-54 owner-approved temporary draft recovery — 2026-10-21

The later owner approval permits a narrow exception to QH-52's memory-only draft
contract: the unsent message and manual-element text may enter sessionStorage
only for explicit reconnection, for at most30 minutes. Restoration requires the
same backend-verified QH owner and successfully authorized exact Context Space.
Remove the stored copy upon restoration, logout, account change or explicit
“Effacer les brouillons”; reject expired, malformed and mismatched data. Ordinary
typing remains in memory. No tokens, conversation history, automatic submission
or canonical save are permitted. All token, TTL, disclosure and budget contracts
remain unchanged. See [the review amendment](../qh-54-maquette-alignment.md).

## QH-54 thematic map — owner amendment, 2026-10-21

Map nodes represent explicit Space-specific **themes**, not individual revisions.
Themes concern what an element is about; semantic roles concern its function.
Neither organizational domains, structural kinds, generic legacy descriptors nor
item titles establish thematic membership. Themes are open and multiple per item;
assignment certainty, provenance and human validation remain independent.

Only verifiable thematic assignments may produce nodes and member navigation;
pagination/partial coverage must remain explicit. Where no qualified assignments
are available, preserve the orb, a minimal truthful state and access to Éléments.
No keyword/title classifier, retroactive classification or fixed taxonomy follows.
The approved [presentation contract](../qh-54-thematic-map-contract.md) is distinct
from the [QH-51 technical proposal](../qh-51-thematic-extraction-plan.md), pending
approval before schema/contract changes or inference. No migration or provider call
is authorized by this amendment.

## QH-51 semantic assignments — approved isolated increment, 2026-10-21

The owner approves version2 of generic profiles with explicit thematic/semantic_role
dimensions, open values, assignment certainty and exact citation references, without
rewriting old profiles or revisions. The same Engine/provider port, resolver and
atomic Source/proposed/outbox pipeline apply. Literal manual retention remains
available; semantic processing is an explicit choice when separately enabled.

The [selective-review decision](../qh-51-assignment-review-decision.md) is approved:
backend-only assignment review_state proposed/accepted/rejected, optional exact
Space name_candidate, and QH-46 review_assignments creating an immutable proposed
successor. Text, certainty, sources and current pointer are preserved. Item validity,
assignment validity, extractor certainty and human confirmation remain independent.
No model-assigned human state, lexical/vector merge, global theme taxonomy or
separate review store. Proposed name equivalences require explicit owner choice.

Authorized thematic map nodes open bounded exact member lists, keep provenance and
states, and declare partial coverage. No node from a revision/title or legacy role.
All new profiles and semantic adapters are verified only with simulated/replay
providers and disposable synthetic data. Real provider experiment and VPS profile
provisioning/activation remain separately gated; no new paid call is authorized.


## Superseding development AI decision — 2026-10-22

The owner explicitly replaces prior development UI snapshot/session consents and
Alice/Projet pilote eligibility with ordinary AI use by the exact verified owner
OIDC account in all its owned Spaces, present/future. **Envoyer** authorizes one
chat processing request; **Proposer avec Mistral** authorizes one selected-source
UUM extraction. There is no preliminary activation, provider checkbox, mandatory
snapshot preview/confirmation or per-Space/conversation grant. No inference on
opening a page. The active model and transmitted data scope are visible. Only
confirmed-current Space elements and the explicitly submitted dialogue are sent
by default; proposed inclusion is a separate user choice. Chat never confirms or
persists facts; UUM creates proposed revisions reviewed through QH46.

This exception retains verified OIDC/CHAT/owner policy, graph freshness, exact
source validation, immutable revisions and isolated ownership. Only development,
one configured OIDC principal, Mistral AI/mistral-small-2603. Preserve the original
QH45 ledger and aggregate8 requests/USD0.20, old entries and absolute expiry; no
QH51 allocation transfer or reset. Historical3 requests/USD0.01 session limits do
not apply in this mode. Reserve the bounded maximum cost atomically before HTTP;
concurrent requests cannot overspend. No retry/fallback. Insufficient global
reservation returns « Plafond IA atteint. Aucune nouvelle requête ne sera facturée. »
before sending. Previous decisions above remain historical and continue outside
this precisely scoped development mode. See [implementation contract](../qh-51-essai-ia.md).

## Explicit two-account demo authorization — owner, 2026-10-28

Alice and Bob may use the same server-side Mistral Small configuration in their
own Spaces. Both exact verified OIDC subject/principal pairs must be explicitly
listed in private authorization; all other accounts remain denied. Sharing the
provider key grants no access to another account's Spaces or conversations.
The existing aggregate ledger, history, USD5/EUR10 envelope, observed-credit guard,
expiry and maximum-cost reservations are unchanged and shared, never per-account
or replenished. No paid call is needed to check availability. Non-eligible accounts
receive valid disabled capabilities rather than an invalid quota-free response.

## Context Space V0.2 — owner UX pivot, 2026-10-26

The explicit Context Space V0.2 request supersedes mandatory item/dimension review
as the ordinary user journey. Discussion is the default; one closed-by-default,
expandable, read-only Understanding panel replaces Elements/Overview/Sources/
History/Review/Advice navigation. Provenance stays available on demand.

Explicit Mémoriser consolidates the complete retained intake through the existing
UUM Engine, preserving attribution, uncertainty and original evidence. A machine
consolidation is usable without individual review but **does not set human
confirmation**. Existing canonical proposals/review and sharing exclusion rules
remain intact. The consolidated version selects exact immutable revisions for
chat; pending corrections remain distinguishable until the next consolidation.
Source/proposals/outbox/version publish atomically, with durable idempotency and
retained previous versions. A failed/empty analysis never claims consolidation.

Portable versioned owner export and validated import preserve origin identities
and uncertainty; imports become pending intake rather than overwrite current
understanding. This is separate from controlled third-party disclosure. No new
provider/model/budget, paid automatic test, persistent migration or runtime
activation is authorized by this implementation. See [implementation and manual
acceptance](../context-space-v02.md), including the remaining PDF limitation.

### Concise understanding and source sovereignty — owner, 2026-10-27

The recap describes the subject and available knowledge autonomously, in the main
language of the original memorized content: usually 40–80 words when useful, no
minimum and at most 100 words. Detailed structured knowledge retains complete
procedures, tools and activities for chat; the recap is not its retrieval limit.
No automatic re-extraction on questions. Missing authorized detail stays explicit.

Projection READ/ASK_AI does not grant access to original conversations, documents,
internal revisions, diagnostics or owner export. Original evidence stays preserved
and owner-accessible. Existing explicit minimized-quote approval remains separate
and restrictive by default. A recap may enter a newly approved snapshot only when
its complete basis survives the disclosure scope without masking; otherwise omit
it rather than disclose excluded knowledge. Existing approved snapshots remain
immutable. Guest chat uses only the authorized materialized projection.

### Unified document sharing and Space introduction — owner, 2026-10-30

The later owner decision supersedes separate semantic/download choices. New sharing
requests select exact SourceRevision IDs once (`documents`, empty by default),
granting both document-derived knowledge and original PDF access. Mixed items require
all supporting document sources. All-current selection freezes the current IDs;
later uploads remain private. Retained policies/snapshots/invitations are unchanged.

Owner Understanding, preview and guest show one general title/introduction only.
Existing document synopses remain immutable metadata, without automatic presentation.
New introductions describe the subject and broad scope, using minimal exact UUM
support rather than a catalogue of private document details. The independently
reviewed introduction may be approved without releasing its detailed supporting
items or PDFs. The complete canonical supports still pass graph/citation checks and
the unchanged Disclosure Guard: excluded/masked supports or an unsafe introduction
prevent its release. A general label alone grants nothing. The general synopsis is
stable across document selections; document items and downloads follow the selected
IDs. Summary-only snapshots are allowed with exact owner approval. Sharing and
snapshot opening perform no inference. No persistent migration is required.
An introduction-only projection represents the exact verified synopsis as its
sole minimized item, anchored to its existing canonical support. It creates no
canonical Understanding Item and releases no underlying document details.

### Confirmed owner erasure — owner, 2026-10-30

The owner may irreversibly delete one Space after exact-name confirmation. This
explicit erasure is the sole scoped exception to immutable history retention;
ordinary updates/deletes/truncation remain forbidden. A durable deleting state
revokes invitations/sessions and blocks reads/writes before graph cleanup. An
idempotent fenced graph purge precedes transactional SQL erasure. Failures retain
the revoked pending operation for worker recovery; only complete graph/SQL erasure
returns success. A minimal owner-bound receipt (IDs, confirmation hash, timestamps)
supports safe retry after ambiguous responses and contains no Space content.
Other Spaces, account identities and aggregate financial ledgers are preserved.
Migration 0012 must be explicitly authorized and backed up before VPS activation.

### Source confidentiality correction — owner, 2026-10-30 (historical document scope)

This later owner decision supersedes the introduction exception above: every
PDF-derived item and recap requires all supporting PDF revisions to be authorized.
Filter before recap selection and close relations over retained endpoints. Retained
snapshots remain immutable; access-time checks may only restrict their frozen
contents using support/permission metadata, never add live canonical knowledge.
Untrusted guest history is validated but not forwarded to generation. Guest
follow-ups use only ordered groups of validated current item aliases from prior
answers, never prior prose or questions. This process-local memory retains at most
six turns for 15 minutes across at most 128 sessions, bound to the exact session,
snapshot ID and authorized payload fingerprint. A changed payload clears the
references; fresh access checks still fence revocation and expiry. Missing or
ambiguous referents require clarification; process restart loses this temporary
continuity. Current authorized items remain the only factual knowledge.

When no communicable knowledge remains, Projection emits only the shared name and
its fixed insufficient-access notice. The existing nonempty snapshot envelope
stores that notice as an unanchored `projection_notice` presentation entry; it is
never a canonical item, knowledge, citation or model input. Sharing and answering
that empty projection perform no inference. No schema change is required.
Exact owner acknowledgements and attachment notifications get short deterministic
replies; attachment presence must first be checked against the authorized original
metadata. Questions, compound instructions and ambiguous messages retain normal AI.


### Guest conversation fidelity correction — owner, 2026-10-30

Guest employment chronology requires employers, roles, periods and relationships
already present in authorized items. Activities cannot substitute for missing jobs;
missing UUM facts remain explicit without source re-extraction or live hydration.
Ordinal lists are rendered from ordered public subjects with validated references;
follow-ups retain that list order and use its selected authorized supports. Missing
or ambiguous references and rejected internal-structure explanations receive a
safe clarification without repeating generation or disclosing rejected text.
The later owner regression correction withdraws the automatic three-excerpt
fallback: unrelated facts are not a semantic recap. New previews may reuse the
single canonical document synopsis that survives the existing scoped Guard when
the general recap cannot be disclosed. No arbitrary choice between several safe
synopses, new inference on sharing, source hydration into old grants or snapshot
rewrite. Existing grants without such an approved synopsis need a new owner
approval to acquire one. Empty projections retain the deterministic privacy notice.
Structured sections supply their own authorized citations; global references and
conversation referents are derived by the server rather than independently repeated
by the provider. Extraction preserves contextual actors, roles, periods and explicit
links in item.text with exact evidence; the UUM wire schema remains unchanged.

### Authorized evidence fidelity — owner, 2026-10-30

When an approved snapshot explicitly includes minimized source quotations, the
private chat request retains those exact, already guarded quotations under their
item alias (deduplicated within each item). The question serializer must not discard
available evidence that qualifies dates, contractual conditions or attribution.
Absence of quote approval still means no quotation in model input. No original PDF
read, canonical hydration, new snapshot enrichment, inference on load or automatic
confirmation follows from this correction. Fresh document scope, revocation and
expiry checks continue to restrict both item text and its approved quotations.

### Guest evidence selection and composition — owner correction

Guest response generation separates a private relevance assessment from public
composition. The first phase assesses every current authorized item against the
requested subject and conditions; it neither composes prose nor chooses a subset
to satisfy a count. The server validates complete coverage and exact authorized
aliases. Explicit first/last counts and conservative ordering use only literal
dates in current item text or already approved quotations; missing or overlapping
temporal evidence requires clarification, never invented precision or item-order
selection. No canonical extraction, source hydration or new semantic type follows.

Composition receives only the selected items and their approved quotations, without
a broader recap or discarded items. Required subject slots and their supporting
aliases are fixed by the server; the model cannot drop slots, change citation
assignments or redefine ordinal order. Follow-ups keep only the existing bounded,
current-payload-bound alias groups, never previous answer prose. Large complete
enumerations are not truncated to fit reference memory; instead old ordinal
references are cleared when the list cannot be retained within its existing bound.

A positive question normally uses selection then composition. An already resolved
ordinal uses composition only; absence/ordering limits stop after selection, and
existing empty/social paths still avoid inference. These are fixed purposeful
phases, not paid retry/fallback. Authorization, snapshot equality, receipt, expiry,
revocation and aggregate budget are checked around each HTTP; each reserves its
technical maximum atomically and retains durable accounting. Response cost/usage
aggregate the executed phases without changing limits, history or public contracts.
