# QH-51 — UUM: perimetro del reset e cutover preparato

Stato: **NON ESEGUITO sul VPS; conferma distruttiva finale richiesta**.
Decisione owner del 21 ottobre 2026, lavoro ripreso il 22 ottobre.
[ADR 0010](adr/0010-universal-understanding-model.md). PR #23 resta aperta;
nessun merge, inferenza, backfill, modifica PR #19 o migrazione 0007.

## Inventario effettivo e perimetro da approvare

Database applicativo `qh`, servizio `qh-postgres-1`, schema pubblico 0006.
Sono presenti 15 tabelle. La cancellazione riguarda **solo queste 11**:

| Tabella | Righe nel backup | Effetto |
| --- | ---: | --- |
| `context_spaces` | 11 | Tutti gli Space di prova, nomi e metadati di base |
| `owner_organization` | 1 | Domini, appartenenze, descrizioni e attività organizzative sperimentali |
| `sources` | 11 | Identità delle fonti di prova |
| `source_revisions` | 11 | Testi e provenance delle revisioni sorgente |
| `understanding_items` | 29 | Identità degli elementi e current pointer |
| `understanding_item_revisions` | 30 | Testi, descrittori/classificazioni, stati, receipt di review e revisioni |
| `item_revision_types` | 30 | Binding di profilo delle revisioni eliminate |
| `item_revision_provenance` | 30 | Appartenenze revisioni/fonti |
| `relation_revision_details` | 3 | Endpoint canonici delle relazioni |
| `context_projection_state` | 11 | Epoche/stato operativo degli Space eliminati |
| `projection_outbox` | 30 | Intenti di proiezione dipendenti da quelle revisioni |

**Conservate senza modifiche:** `users` (7), `user_identities` (2),
`semantic_type_versions` (14 definizioni immutabili), `alembic_version` (1, 0006).
I profili storici conservati sono configurazione versionata, non dati da convertire;
nessun nuovo adapter/backfill v1/v2. Verranno registrate esplicitamente le tre
definizioni UUM v3 solo nel successivo cutover approvato, senza modificare le 14
definizioni presenti. L'app nuova scrive v3; il database riparte senza Space o item.

Neo4j `qh-neo4j-1`: **92 nodi e 40 relazioni** nel backup completo.
Il perimetro proposto distingue:

- 86 nodi QH nativi (`QH30Slice/Sync/Item/Revision/Source`) del namespace
  `qh-native`, con 36 relazioni derivate;
- 6 nodi di prova del prototipo Graphiti (`Entity`, `Episodic`), con 4 relazioni,
  nei tre gruppi QH inventariati nel manifest privato. Nessun collegamento incrociato.

La conferma finale comprende entrambi i gruppi: sono dati applicativi sperimentali,
non codice/storia del prototipo. Si selezionano **gli ID e le proprietà inventariati**,
controllando prima l'identità completa e l'assenza di archi fuori perimetro.
Nessun `MATCH (n) DETACH DELETE n` globale. Un nodo/gruppo nuovo o un'altra
dipendenza non inventariata arresta il reset; non si amplia lo scope automaticamente.
Constraint, indici e account Neo4j rimangono. Nessun volume viene eliminato.

| Volume / percorso | Classificazione | Intervento previsto |
| --- | --- | --- |
| `qh_postgres_data` | Dati QH + identità/configurazione SQL | Conservare volume; svuotare solo le 11 tabelle elencate |
| `qh_neo4j_data` | Proiezioni QH native e prototipo di prova | Conservare volume/schema; cancellazione logica selettiva dei nodi/archi inventariati |
| `qh_neo4j_logs` | Log infrastrutturali | Conservare |
| `qh_keycloak_data` | Identità, credenziali e stato IdP | Conservare integralmente; nessuna operazione sul volume |
| Realm import readonly, immagine Keycloak versionata | Configurazione/artefatto IdP | Conservare byte, immagine e mount; nessun riavvio Keycloak |
| `.env`, bundle `/home/ubuntu/qh-runtime/current` | Segreti/configurazione/rollback | Conservare; copia privata del file ambiente nel backup |
| `.local-archive/qh45-runtime` e tutti i ledger/audit economici | Budget, autorizzazioni e contabilità | Conservare byte per byte, senza reset contatori o riallineamento Space |
| Git, benchmark, evidenze e catture Mistral | Codice/storia/prove | Conservare; nessuna correzione delle risposte originali |

Non risultano altre tabelle QH di snapshot/proiezioni approvate nello schema
attuale. PR #19 e la sua 0007 non sono installate né richieste. La conferma non
comprende tabelle eventualmente aggiunte dopo questo inventario.

## Backup e prove di ripristino effettivamente eseguite

Archivio privato: `/home/ubuntu/qh/.local-archive/qh51-uum-reset-20261021/`.
Contiene dati/credenziali: non pubblicarlo e non includerlo nella PR.

- `qh.dump`: dump custom completo del database QH, incluse le tabelle conservate,
  schema, vincoli, funzioni e trigger; lista archivio verificata con pg_restore.
  SHA-256 `11856295c7778f6c27908faa3b35f50a6b2fa9e9d0a01026078057f9f67abfdc`.
- `roles.sql`: backup protetto dei ruoli/globals PostgreSQL; non applicato sul VPS.
- `graph.json` e `graph-schema.json`: intero grafo logico con proprietà tipizzate,
  etichette, endpoint, inventario di indici/constraint. File graph SHA-256
  `6a1cf23f8c900667cd07210575150768d45ff59ff7a0a97057a881d080c4efc9`.
- `containers.private.json`, `dependencies.json`, `triggers.json`, snapshot SQL,
  file ambiente privato e hash dei file protetti completano il perimetro.

**PASS — restore PostgreSQL:** container nuovo con stessa immagine, tmpfs, nessuna
rete/porta/volume persistente; `pg_restore --exit-on-error --single-transaction`.
Conteggi e fingerprint di tutte le 15 tabelle coincidono con la sorgente.
**PASS — reset nel clone:** 11 tabelle a zero, 4 conservate identiche; definizioni
dei trigger ripristinate; confronto finale con SQL persistente invariato.
**PASS — rollback SQL nello stesso clone:** ripristino delle sole 11 tabelle
applicative nel medesimo database/transazione, identità/configurazione intatte;
confronto finale delle 15 tabelle e dei guard. Nessun cambio DB nelle app.
**PASS — restore Neo4j:** container dedicato tmpfs, credenziali sintetiche;
92 nodi/40 archi ricostruiti con confronto esatto di proprietà, tipi temporali,
etichette ed endpoint. Gli ID interni Neo4j vengono rimappati; le identità QH no.
**PASS — reset/rollback Neo4j selettivo:** prova nel clone con un nodo estraneo
aggiuntivo; eliminati solo gli ID del backup, nodo estraneo conservato, poi
ricostruiti esattamente i 92 nodi/40 archi applicativi senza toccare il canary.

Il backup è completo per il perimetro dati che sarà modificato. Keycloak non entra
nel reset o nel rollback: non è stata fatta una copia a caldo del suo database H2.
Il suo volume/immagine/configurazione rimangono al loro posto, senza ricreazione.
Il backup del solo filesystem H2 attivo non sarebbe una prova di ripristino coerente.

Prima dell'esecuzione si riverificano hash e inventario. Se i dati sono cambiati,
nuovo backup e restore di verifica sono controlli automatici obbligatori; se cambia
il perimetro distruttivo si torna alla decisione owner. Nessun vecchio manifest
viene riscritto per nascondere cambiamenti.

## Sequenza esatta del cutover, ancora da autorizzare

1. Verificare artefatto/HEAD approvato, backup e test; mantenere frontend/backend
   e worker fermi. Sono stati arrestati con `sudo -n make dev-stop` prima delle
   modifiche ai bind source: questo impedisce attivazioni premature dei sorgenti.
   PostgreSQL, Neo4j, Keycloak e MCP restano in esecuzione con le immagini originali.
2. Ricontrollare database `qh`, schema 0006, 15 tabelle, dipendenze FK, trigger,
   conteggi/fingerprint, mount, immagini e file economici. Non eseguire `make migrate`.
3. PostgreSQL: unica transazione, lock sulle tabelle interessate, sospensione
   esclusivamente dei cinque trigger **TRUNCATE** di immutabilità elencati sotto;
   `TRUNCATE` con lista esplicita delle 11 tabelle e `RESTRICT`, senza CASCADE,
   DROP o reset di sequenze; riattivazione dei medesimi trigger prima del COMMIT.
   I guard normali sulle nuove revisioni restano quelli originali.
4. Neo4j: transazione limitata ai nodi/archi inventariati dopo confronto esatto;
   non attraversare fuori dal perimetro. Le risorse infrastrutturali e gli altri
   namespace non fanno parte dell'operazione.
5. Registrare esplicitamente solo i tre profili generici v3; verificare identità
   SQL/OIDC, tabelle applicative vuote, profili originali invariati, guard attivi,
   contabilità e file protetti identici. Nessun seed demo o inferenza.
   Comando di provisioning: `python /workspace/scripts/provision_qh_semantics.py
   --register-uum-profiles`, in un container di manutenzione temporaneo con la
   stessa immagine backend verificata, bind readonly del codice e rete dati QH;
   riceve soltanto le variabili PostgreSQL da un file privato. Le due app restano
   ferme. Il comando richiede 0006 e tutte le 11 tabelle applicative vuote,
   serializza verifica/registrazione con lock e rifiuta dati preesistenti.
   È stato provato in isolamento per replay identico e rifiuto del non-vuoto.
6. Riallineare soltanto le due app via comandi guarded dopo verifica di compatibilità
   con DB vuoto/0006/v3; health e login Alice/Bob, lista Space vuota e isolamento.
   Nuovi Space/elementi durante la prova Mac saranno nuove scritture dell'owner.
   Il primo smoke automatico persistente sarà read-only; nessun dato sintetico
   verrà seminato per far apparire pronta la mappa.

Trigger temporaneamente sospesi, soltanto durante la transazione di reset:

| Tabella | Trigger TRUNCATE |
| --- | --- |
| `item_revision_provenance` | `qh_immutable_truncate` |
| `item_revision_types` | `qh30_immutable_truncate` |
| `relation_revision_details` | `qh30_immutable_truncate` |
| `source_revisions` | `qh_immutable_truncate` |
| `understanding_item_revisions` | `qh_immutable_truncate` |

Lo script SQL completo è `reset-rehearsed.sql` nell'archivio privato; è stato
eseguito solo nel clone, mai contro `qh-postgres-1`. Disabilitare indiscriminatamente i trigger,
usare session_replication_role o ampliare TRUNCATE è escluso. Il rollback usa
una lista distinta di trigger applicativi, senza disabilitare i vincoli FK interni.

## Rollback

PostgreSQL e Neo4j non condividono una transazione. Fino al successo dei controlli
di entrambi, le app restano ferme e non si accettano nuove scritture dell'owner.
Se la transazione SQL fallisce, rollback SQL conserva dati e guard. Se fallisce
Neo4j o una verifica successiva, non aprire il servizio sullo stato parziale.

Usare `rollback-rehearsed.private.sql` per ripristinare le sole 11 tabelle nello
stesso database, soltanto sul post-reset verificato e prima della riapertura alle
scritture. Il derivato di restore proviene dal dump immutato in ordine di dipendenza:
i current pointer vengono inseriti temporaneamente null e ripristinati esattamente
dopo le revisioni, nella stessa transazione, per rispettare il ciclo FK non
differibile. Non è una migrazione semantica. Identità/configurazione e altri
schemi non vengono svuotati o ripristinati.

Durante il solo restore vengono sospesi per nome i 21 trigger applicativi delle
11 tabelle inventariate, evitando enqueue automatici e controlli di assemblaggio
durante COPY; i vincoli FK interni restano attivi. Dopo COPY e ripristino pointer,
`SET CONSTRAINTS ALL IMMEDIATE` valida i vincoli prima della riattivazione dei
trigger. Conteggi/fingerprint, definizioni e guard devono tornare al checkpoint
prima della riapertura. Il percorso completo è stato provato nel clone; nessuna
disabilitazione è stata eseguita sul VPS.

Ripristinare il grafo dall'archivio tipizzato sul solo perimetro svuotato, con
schema/indici originali conservati. SQL e grafo provengono dallo stesso checkpoint
applicativo fermo. Eventuali definizioni v3 già registrate possono restare come
configurazione additiva non referenziata: non cancellare definizioni immutabili
per tornare al codice precedente. I sorgenti/artefatti rimangono in Git e nelle
immagini, senza reset --hard o perdita del lavoro corrente. Se il riallineamento
guarded non passa, mantenere le app ferme per riparazione forward.

Il rollback dati è verificato in isolamento; nessun rollback o cambio runtime
è stato eseguito sul VPS.
Il rollback dopo la riapertura e nuove scritture richiede un nuovo piano che
preservi tali scritture: nessun restore cieco del vecchio dump.

L'eliminazione degli Space rende i vecchi grant/allowlist riferimenti a ID non più
esistenti: restano conservati come contabilità/autorizzazione storica e falliscono
chiusi. Non vengono trasferiti ai nuovi ID. Provider semantico e nuove spese restano
disabilitati; nessun reset del ledger equivale a un nuovo plafond.

## Gate finale

La richiesta finale deve coprire esplicitamente: 11 tabelle/197 righe sperimentali,
86 nodi/36 archi nativi e 6 nodi/4 archi Graphiti QH, preservazione dei quattro
registri SQL e di tutti i volumi/IdP/contabilità, registrazione v3 e avvio delle
sole due app. Fino ad allora **nessuna cancellazione o registrazione persistente**.
Il collaudo isolato e la PR aperta non costituiscono questa conferma.
