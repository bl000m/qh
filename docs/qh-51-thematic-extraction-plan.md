# QH-51 — Estrazione tematica nello stesso Understanding Engine

**Proposta tecnica da approvare, non implementata.** Preparata il 2026-10-21 dopo
lettura via Atlassian MCP di QH-51, QH-47 e QH-54. La distinzione tematica/ruolo e
la [presentazione minima](qh-54-thematic-map-contract.md) sono già approvate;
la rappresentazione seguente e i nuovi contratti di lettura/review non lo sono.
Nessuna inferenza, nuova migrazione, registrazione o scrittura demo è eseguita.

## Contratto circoscritto proposto

Riutilizzare `content.descriptors` delle revisioni generiche con una **nuova
versione del profilo**, senza cambiare i profili registrati o le revisioni storiche.
Esempio illustrativo, non dati da applicare a Bien-être:

```json
{
  "dimension": "thematic",
  "value": "Sommeil",
  "certainty": "tentative",
  "evidence_refs": [0]
}
```

`dimension` distingue `thematic` da `semantic_role`; questi sono discriminanti di
dimensione, non una tassonomia dei valori. `value` rimane aperto. Ogni assegnazione
riferisce una o più citazioni della **stessa revisione**, qui tramite indici nella
lista immutabile `content.citations`. Validare presenza, limiti e risoluzione degli
indici, source revision, turno e locator esatto attraverso il resolver QH-32.
Una citazione esistente non prova che l’assegnazione sia semanticamente corretta.
La valutazione e la review di questa correttezza restano distinte.

Conservare più assegnazioni e certezza asserted/tentative per ciascuna. Il provider
non decide owner, IDs, profilo fidato, stato di validazione o current pointer.
Assenza di `dimension` nei dati precedenti significa **descrittore non qualificato**,
non ruolo o tema inferito. Nessun backfill automatico, blacklist di ruoli o analisi
di parole/titoli. Descrittori fuori contratto invalidano il batch, non sono ignorati
per pubblicare i fratelli validi. Limiti di batch/testo restano quelli concordati;
i nuovi campi devono rientrare nel payload bounded.

L’estrattore attuale in `app/understanding/extractor.py` ammette soltanto
`value/certainty`: non basta inviare campi nuovi. Occorre versionare insieme
output del provider, validatore, profilo registrato, proiezione e DTO di lettura.
Verificare prima in isolamento che i JSON canonici esistenti possano ospitare il
nuovo profilo senza DDL; **nessuna migrazione SQL è proposta come prerequisito**.
Anche una registrazione di profilo persistente sul VPS resta una scrittura da
autorizzare separatamente. Non riscrivere 0005/0006 o introdurre 0007 di PR19.

## Denominazioni fra estrazioni successive

1. Il backend raccoglie dal medesimo Space soltanto valori tematici qualificati e
   autorizzati. Un vocabolario bounded incluso nel prompt fa parte del payload
   esatto da mostrare nel consenso di disclosure; non inviare item o temi nascosti.
   Dichiararne la copertura: un elenco troncato non dimostra novità di un tema.
2. Normalizzazione conservativa proposta: Unicode NFC, spazi iniziali/finali e
   ripetuti. Nessuna traduzione, stemming, fusione per somiglianza, rimozione di
   accenti o case folding automatico. Chiave derivata `(Space, valore normalizzato)`;
   non una nuova identità canonica globale.
3. L’estrattore riusa l’esatto valore esistente quando propone la stessa tematica;
   duplicati nello stesso batch vengono unificati soltanto quando identici anche
   per certezza ed evidenze. Duplicati discordanti invalidano l’intero batch prima
   della pubblicazione. Replay dell’operazione restituisce gli stessi IDs QH-39.
4. Un nome nuovo potenzialmente equivalente rimane una **proposta da rivedere**:
   mostrare nuovo nome, possibili corrispondenze ed evidenze. L’owner sceglie riuso
   del nome esatto oppure tema distinto; nessun merge semantico del modello.
   Fino a tale scelta non aggiungere un secondo nodo attivo indistinguibile.
   Serve una review esplicita delle assegnazioni, da integrare nel percorso QH-46:
   il solo `asserted` non equivale ad approvazione del nome o dell’elemento.
5. Una rinomina approvata si esprime con nuove revisioni proposte/review delle
   assegnazioni coinvolte; non cambia silenziosamente le revisioni precedenti.
   Non promettere un alias duraturo senza rappresentarlo: due estrazioni possono
   riproporre la variante, che torna in review. Se diventano necessari alias
   persistenti, omonimi distinti, rinomina globale, storia o identità autonoma del
   tema, fermare quel requisito e presentare una decisione di persistenza dedicata.

Il contratto evita duplicati **automaticamente attivati** senza promettere una
riconciliazione semantica perfetta. La qualità del riuso dei nomi, i falsi merge e
i falsi split devono essere misurati separatamente. Non deduplicare item diversi
solo perché condividono un tema.

## Percorso applicativo e lettura della mappa

Riutilizzare `ConversationEnrichment` → estrattore QH-8/risoluzione QH-32 → repository
canonico (Source + batch proposed + outbox atomici) → worker Neo4j → recupero con
policy e verifica del grafo. LLMProvider resta un adapter sostituibile; nessun
secondo engine, servizio o archivio di verità. QH-46 governa revisione/conferma;
certezza tematica, origine e stato dell’item restano indipendenti.

Proporre un read model tematico bounded nello stesso servizio Understanding,
con Space, valore esatto, certezza delle assegnazioni, revisioni membri e copertura.
Prima dell’implementazione approvare l’estensione del contratto pubblico: filtro
**dimensione + valore** applicato prima del LIMIT, paginazione dei membri e lista
dei temi con indicatore di copertura. L’attuale filtro `descriptor` da solo non
separa temi e ruoli omonimi. La scoperta globale delle facet è differita da ADR0005:
non sostituirla con una scansione client illimitata o conteggi SQL senza verifica
Neo4j. Una prima vista può essere esplicitamente parziale, senza conteggi globali.

Il click del nodo riusa l’elenco/dettaglio autorizzato di UnderstandingWorkspace,
con più appartenenze, certezza visibile e stati/provenienza/review inalterati;
visualizza ulteriori pagine solo su richiesta. Un errore o dato graph stale elimina
nodi e membri precedenti. Nessun titolo o descrizione di nodo deve essere generato
da frammenti casuali; etichetta dal valore tematico approvato, descrizione solo da
un campo esplicito futuro, altrimenti omessa.

## Dipendenze e sequenza verificabile

| Unità | Dipendenze / gate | Criteri verificabili prima della consegna |
| --- | --- | --- |
| 1. Versione del contratto e fixture offline | Approvazione di questo memo; ADR0004/0009 e QH-39 esistenti | Vecchi descrittori restano non qualificati; due dimensioni omonime distinte; multipli temi; certezza indipendente; nessuna chiamata esterna |
| 2. Adapter semantico e validazione | LLMProvider/QH-8, resolver QH-32; profili nuovi soltanto in DB isolato | Citazioni false, ambigue, fuori scope, indici errati e batch misti rifiutati; zero scritture parziali; replay identico e conflitto su payload diverso |
| 3. Lettura tematica e review | Contratto pubblico e review assegnazioni approvati; QH-46 | Filtro prima di LIMIT, più pagine, ruolo/tema omonimo, tentative, nuove denominazioni in review; A/B e freshness fail closed; click mostra membri esatti con provenance |
| 4. Valutazione semantica offline | Benchmark QH-33/38 con annotazione umana, casi multi-sessione | Precisione/recall delle assegnazioni e riuso nomi, falsi merge/split, qualità citazioni e persistenza misurate separatamente; soglie approvate prima del gate live |
| 5. Eventuale prova reale circoscritta | Autorizzazione separata payload/provider/endpoint/modello/prezzi/limiti e costi estrazione | Consenso specifico distinto da chat, budget/ledger preservati, zero retry/fallback; 429/timeout fail closed; nessun invio in startup/test/CI |
| 6. Eventuale attivazione VPS | Revisione PR, configurazione/profilo/artefatto verificati e autorizzazione persistente dedicata | Backup/rollback provati, schema e dati preservati, controlli runtime mirati; nessun backfill implicito |

QH-14/15/16 e PR19 non sono prerequisiti di una classificazione tematica interna;
nessuna loro integrazione o migrazione è autorizzata. QH-51 può essere verificato
interamente offline prima di chiedere una prova pagata.

## Confine con QH-47 e decisione richiesta

QH-51 estrae proposte supportate da evidenze e riusa nomi espliciti secondo regole
conservative. QH-47 decide se **gli item** sono nuovi/aggiornati/contraddittori/
superati/invariati, identità nel tempo, merge e temporalità, concorrenza e conflitti.
Non assegnare a QH-51 la fusione semantica delle revisioni o l’aggiornamento del
current state. La semplice uguaglianza dei nomi tematici non risolve QH-47.
Identità/storia autonome dei temi richiederebbero un’estensione esplicita del mandato,
non sono già coperte dal titolo di QH-47.

Richiesta per il successivo passo: approvare o correggere la rappresentazione
versionata delle assegnazioni con evidenze, la riconciliazione conservativa dei
nomi e il percorso di review/lettura bounded. Questo memo **non** chiede né concede
budget, inferenze, migrazioni o attivazioni VPS. Fino all’approvazione, la PR22
mantiene il fallback senza nodi inventati.
