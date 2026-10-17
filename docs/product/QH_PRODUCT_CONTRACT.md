# QH Product Contract

Stato: riferimento funzionale principale, definito dal proprietario del prodotto.
Questo contratto guida tutte le implementazioni future. Le ipotesi e le proposte
indicate come aperte non sono decisioni approvate né autorizzazioni a implementare.

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

Un link condivisibile permette inoltre di accedere a una proiezione senza
obbligare inizialmente il destinatario ad adottare QH come client. Modalità di
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
