# QH-54 — Mappa tematica: contratto minimo

Decisione di prodotto approvata dall’owner il 2026-10-21; correzione nella PR22.
Il [contratto tecnico QH-51](qh-51-thematic-extraction-plan.md) rimane una proposta
separata. Questa decisione non autorizza migrazioni, registrazioni persistenti,
inferenze, nuove API o classificazione retroattiva dei dati.

## Significato e presentazione approvati

Un nodo rappresenta una **tematica dello Space**, ossia ciò di cui parlano gli
Elementi. Il ruolo semantico (decisione, ipotesi, obiettivo, domanda), la forma
item/entity/relation, la provenienza, la certezza dell’assegnazione e la conferma
umana sono dimensioni distinte. Non si ricavano temi dal titolo, da frammenti,
dai domini organizzativi o dal semplice nome di un descrittore.

Le tematiche sono aperte e specifiche dello Space; un elemento può appartenere a
più tematiche. Nessuna tassonomia globale o categoria fissa. Un collegamento tra
boule e tema esprime un’appartenenza esplicita, non una relazione inferita tra item.
Un futuro click su un tema deve aprire i suoi membri autorizzati, conservando
revisioni esatte, provenienza, stato, certezza e controlli QH-46. I temi tentativi
devono essere riconoscibili senza diventare conferme dell’elemento.

Copertura, filtri e paginazione devono essere dichiarati. Una pagina parziale non
stabilisce cardinalità globale, esaustività o assenza di altre tematiche. Errori di
autorizzazione/freschezza eliminano i dati visibili; nessun recupero SQL alternativo.

## Struttura disponibile e intervento immediato

| Struttura disponibile | Dati effettivi | Limite | Intervento |
| --- | --- | --- | --- |
| `content.descriptors`, coppie valore/certezza | Audit Bien-être: 5/6 elementi, 6 assegnazioni; `decision`, `hypothesis`, `open_question`, `reversible_pause`, `stated_by` asserted; `expected_effect` tentative | Nessun discriminante tematico; nessuna appartenenza tematica verificabile | Non promuovere alcuno di questi valori a tema |
| Revisioni canoniche e relativo dettaglio | 6 proposte, nessuna corrente confermata nell’audit | Una revisione non è una macroarea | Rimuovere i nodi costruiti da `itemTitle()`; lasciare gli elementi consultabili |
| `owner_organization` / domini | Organizzazione dei Context Space | Non assegna tematiche agli item | Nessun riuso semantico dei domini |
| Boule e card mappa | Struttura grafica approvata | Mancano dati tematici qualificati | Conservare boule, fullscreen, aggiunta, ricentramento e accesso Éléments; stato « Aucun regroupement thématique vérifié n’est disponible dans cette vue. » |
| Persistenza di macroaree/appartenenze | Nessuna struttura dedicata nell’inventario dell’audit | Mancano identità/storia autonome; non richieste per il primo incremento | Preferire descrittori versionati; nessuna nuova persistenza oggi |

Audit in sola lettura del 2026-10-21, non una classificazione o riscrittura degli
item. Il messaggio si riferisce alla vista disponibile: non dichiara che il tema
sia assente dal significato del testo o da ogni possibile pagina.

## File e verifica

- `apps/web/src/ContextMap.tsx`: `ContextMap` non legge titoli o descrittori generici,
  non crea nodi di revisione e non richiede scansioni delle pagine.
- `apps/web/src/Chat.tsx`: usa la disponibilità già autorizzata; apre la stessa
  mappa minimale per contenuto corrente, proposto o solo storico.
- `apps/web/src/App.tsx`: l’azione della boule/stato apre l’onglet Éléments.
- `apps/web/src/UnderstandingWorkspace.tsx`: elenco/dettaglio, provenance e review
  invariati; `groupsIn()` resta un riepilogo di descrittori della pagina, non temi.
- `apps/web/tests/maquette-alignment.browser.spec.ts`: nessun nodo inventato da sei
  dichiarazioni personali o dal fixture semantico; gli elementi salvati sono
  ancora apribili e conservano il contenuto esatto.

La visualizzazione di **veri nodi tematici e del relativo elenco filtrato** richiede
il contratto dati ancora da approvare per QH-51. Non è dichiarata implementata o
validata sul VPS da questa correzione: oggi nessuna assegnazione è identificabile
come tematica. Le precedenti schermate con sei nodi di revisione restano evidenza
storica della granularità rifiutata, non accettazione del prodotto corrente.
