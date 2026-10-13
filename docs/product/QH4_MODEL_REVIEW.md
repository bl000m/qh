# QH-4: decisioni sul modello da approvare

Stato: **revisione storica, risolta dall'approvazione dell'utente**. Le alternative
e raccomandazioni sotto documentano l'analisi precedente alla decisione, non
istruzioni ancora bloccanti. D1–D7 e le tre scelte strutturali sono approvati con
le precisazioni registrate in [ADR 0002](../adr/0002-canonical-understanding-persistence.md).
QH-4 è autorizzato su database isolati; applicazione al database QH ancora vietata.
Riferimento funzionale: [QH Product Contract](QH_PRODUCT_CONTRACT.md).
Ticket: [QH-4](https://contextlab.atlassian.net/browse/QH-4).

## Stato della bozza preservata

Il commit `5325cea` configura Alembic, credenziali da ambiente, dipendenze bloccate
e test della configurazione. La revisione `0001_qh_schema`, i test PostgreSQL e
le modifiche a Makefile/test architetturali sono ancora non committati.

La bozza crea users, context_spaces, sources, projections e shares. Gli oggetti
owned richiedono lo stesso owner dei loro riferimenti; fonti e proiezioni hanno
un solo Context Space, shares un riferimento alla proiezione. Non rappresenta
Understanding Items, revisioni, provenienza o snapshot approvati. Queste scelte
strutturali non sono state approvate come modello canonico.

Prima della sospensione: build backend riuscita; 29 test mirati prima del commit,
poi 3 test di migrazione su database isolati e 31 test architetturali passati.
Quei risultati dimostrano il funzionamento tecnico della bozza, non la sua
correttezza di dominio. La suite finale QH-4 non è stata eseguita.
L'ultimo controllo in sola lettura ha trovato il database qh senza tabelle
applicative/alembic_version e senza database residui qh4_test_*; l'upgrade al
database QH non è stato eseguito. Questo intervento documentale non applica
migrazioni e non riesegue test che creano o modificano database.

## D1 — Autorità della comprensione: PostgreSQL e Graphiti

Alternative concretamente realizzabili:

- **Graphiti come autorità semantica**, PostgreSQL per fonti/governance e snapshot.
  Riduce duplicazione iniziale; richiede un contratto di esportazione e ricostruzione
  per sostituire Graphiti senza perdere lo stato QH.
- **PostgreSQL come autorità canonica**, Graphiti come vista semantica ricostruibile.
  Offre controllo e portabilità espliciti; introduce già ora modello e sincronizzazione
  della comprensione, rischiando un Comprehension Graph proprietario prematuro.
- **Responsabilità ripartite ed esplicite**, senza doppia autorità sullo stesso dato:
  PostgreSQL per evidenze/governance/snapshot; Graphiti per rappresentazione semantica
  nella V0.1, dietro ContextEngine e con identità/provenienza QH portabili.
  Evita una seconda rappresentazione completa; export, ripristino e consistenza
  fra archivi restano requisiti da definire e verificare.

Raccomandazione da approvare: la terza alternativa come direzione V0.1, dopo aver
definito per ciascun dato autorità, identificativi, esportazione e ripristino.
La sostituibilità di un Protocol non dimostra da sola la portabilità dei dati.
Non introdurre dual write o un grafo proprietario durante QH-4.

## D2 — Modello minimo di Understanding Items

Alternative: elementi identificati e revisionabili di dominio QH; oppure risultati
semantici temporanei del motore, senza un'identità QH persistente.
La prima sostiene governo, provenienza e riferimenti stabili, ma richiede un
modello minimo approvato. La seconda riduce lavoro iniziale, ma non basta come
rappresentazione dello stato persistente e controllabile descritto dal contratto.

Raccomandazione: approvare un contratto minimo con identità QH, associazione al
Context Space, contenuto interpretato, categoria, stato di validazione, revisione
e provenienza. È una proposta concettuale: categorie, cardinalità, valori ammessi
e storage non sono ancora fissati. Non creare una tabella per ogni categoria,
un'ontologia completa o un nuovo motore a grafo.

## D3 — Revisioni e provenienza

Alternative: aggiornamenti in-place con soli timestamp; revisioni immutabili di
fonti/elementi con collegamenti espliciti alle evidenze; event sourcing completo.
I timestamp sono semplici ma non ricostruiscono origine e interpretazioni storiche.
Le revisioni permettono riferimenti verificabili con complessità contenuta; event
sourcing aggiunge replay e gestione eventi che non sono richiesti dalla V0.1.

Raccomandazione: revisioni esplicite dove serve ricostruire evidenze e approvazioni,
distinguendo autore/origine da interpretazione e validazione. Fissare se le fonti
sono immutabili o revisionabili, come si riferisce un estratto, come si registra
affidabilità/incertezza e come si gestiscono ritiro/cancellazione. Evitare event
sourcing completo. L'identificativo Graphiti non sostituisce implicitamente
identità QH o provenienza verificabile.

## D4 — Context Space, Source, Projection, Snapshot, Share

Alternative da deliberare: fonte in un solo spazio o riutilizzabile in più spazi;
proiezione limitata a uno spazio o estesa a più spazi autorizzati; condivisione
che segue una proiezione mutabile o punta a uno snapshot approvato.

Raccomandazione: tenere distinti contenitore di comprensione, evidenza originale,
elemento derivato, configurazione di proiezione, snapshot approvato e autorizzazione
di condivisione. Il legame Share → snapshot approvato è coerente con il vincolo
V0.1; un riferimento alla sola proiezione mutabile rischia ampliamenti silenziosi.
La cardinalità di fonti e spazi e il numero di spazi per proiezione restano da
approvare: non derivarli dal context_space_id della bozza.

## D5 — Ownership, autorizzazioni e invarianti DB

Alternative: soli controlli applicativi; controlli applicativi più vincoli DB
mirati; aggiunta di RLS e autorizzazioni multiutente complete già ora.
I soli controlli applicativi lasciano possibili riferimenti incoerenti; i vincoli
mirati aiutano ma dipendono dalle cardinalità approvate. RLS introduce un secondo
meccanismo di enforcement e configurazione non ancora progettato.

Raccomandazione: vincoli di identità, riferimenti e campi obbligatori dopo aver
approvato il modello. Decidere il significato di owner, riferimenti tra owner,
unicità delle revisioni, validità dell'approvazione e immutabilità dello snapshot.
Stabilire per ogni invariante se servano vincoli SQL, privilegi o controlli backend;
una FK non autorizza una richiesta e uno stato draft non equivale ad approvazione.
Se in scope con i ticket sharing, scadenza/revoca e hash del token devono restare
coerenti con QH-20. Non aggiungere autorizzazioni o trigger per supposizione.

## D6 — Cosa definire ora e cosa rimandare

Alternative: congelare subito un modello completo; oppure approvare i confini
essenziali e introdurre persistenza progressivamente. Un modello completo anticipa
decisioni non validate; una base puramente generica può rendere ambigui identità,
provenienza e confini di accesso.

Raccomandazione: approvare ora significati, autorità dei dati, identità, separazione
fonti/interpretazioni e collegamento delle condivisioni agli snapshot immutabili.
Poi delimitare quali parti QH-4 debba effettivamente migrare, eventualmente
rivedendone la descrizione con autorizzazione separata.
Rimandare ontologia completa, grafo proprietario, event sourcing, automazione di
workflow e deployment SaaS. Implementazioni di ingestione, approvazione e sharing
restano nei loro ticket; rimandarle non significa ignorarne i requisiti strutturali.

## D7 — ContextRecord e ContextId di QH-2

Oggi ContextRecord contiene id/content/title e ContextId è un alias di stringa.
Nessuno dei due distingue spazio, fonte, elemento o revisione; ContextProjection
contiene testo e context_ids, senza contratto di snapshot persistente.

Alternative: assegnare loro ora un significato canonico; oppure mantenerli come
contratti provvisori di recupero e introdurre tipi espliciti solo dopo approvazione.
La prima rischia di consolidare un'ambiguità e cambiare i contratti pubblici; la
seconda conserva lo scaffold ma richiede una futura mappatura documentata.

Raccomandazione: la seconda. Non equiparare ContextId a context_spaces.id né
ContextRecord a una fonte o Understanding Item senza decisione. Approvare prima
semantica, riferimenti a revisioni/provenienza e compatibilità; se cambiano i
contratti, approvare l'aggiornamento dei relativi tipi, test e ADR.

## Esito della revisione

L'utente ha approvato PostgreSQL canonico, Graphiti derivato e ricostruibile,
revisioni immutabili, un solo spazio per fonte/elemento/proiezione, Share verso
snapshot approvato, identità distinte e integrazione limitata allo schema minimo.
La raccomandazione storica di autorità semantica Graphiti è superata. Sono approvati
nuova revisione per conferma e versionamento per elemento senza revisione globale
dello spazio. L'applicazione al database QH richiede autorizzazione separata.
