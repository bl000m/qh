# ADR 0010 — Universal Understanding Model e nuovo ambiente applicativo

Data: 2026-10-21. Stato: **decisione prodotto/architetturale approvata dall'owner**;
implementazione isolata autorizzata, reset persistente subordinato a conferma finale.
Raffina ADR 0004/0005 e sostituisce la tematica come struttura primaria QH-54/QH-51.
Preserva ADR 0001/0003, PostgreSQL canonico, Neo4j derivato e le policy esistenti.

## Decisione

La mappa mostra sempre sei dimensioni di comprensione comuni a tutti gli Space:

| ID indipendente dalla lingua | Etichetta francese |
| --- | --- |
| `situation_information` | Situation & informations |
| `objectives_intentions` | Objectifs & intentions |
| `decisions_actions` | Décisions & actions |
| `constraints_preferences` | Contraintes & préférences |
| `hypotheses_uncertainties` | Hypothèses & incertitudes |
| `open_questions` | Questions ouvertes |

Sono un asse di navigazione/classificazione facoltativo, non domini organizzativi
né sei nuovi tipi strutturali. Ogni revisione atomica ha una primaria oppure
rimane non classificata; più significati autonomi richiedono proposte distinte
con evidenze proprie. Preservare attribuzione, negazione, condizioni e modalità;
quando il significato non consente una scelta, astenersi. Non classificare da titoli
o parole chiave. La dimensione non certifica verità, esecuzione o conferma umana.

Entità/relazioni rimangono strutture trasversali. Provenance, epistemica, temporalità,
revisioni, certezza e review umana rimangono indipendenti. I temi aperti dello Space
sono metadati facoltativi; non sono richiesti dalla nuova estrazione primaria.

## Contratto tecnico

Profili generici v3 additivi con `content.primary_dimension` opzionale, oggetto
`value/certainty/evidence_refs/review_state`. Unicità per forma singola; ID fra i
sei, certezza asserted/tentative e review proposed/accepted/rejected. Assenza o
assegnazione rejected significa nessuna appartenenza effettiva. Registrazione
esplicita; nessun mutamento delle definizioni storiche v1/v2 o migrazione SQL.

Nuovo formato `qh.atomic-understanding/1`: lista di proposizioni con testo,
primaria nullable, certezza se classificata e quote esatte. Nessun ID, offset,
indice di evidenza o stato umano generato dal modello. Il medesimo Engine valida
l'intero batch, QH-32 risolve quote uniche nei turni autorizzati; backend genera
identità, citazioni e riferimenti. Originale nel checkpoint e candidato originale
con hash nell'audit canonico restano distinguibili dai derivati. Zero proposte è
un esito esplicito; conserva la fonte selezionata con consenso, senza inventare item.

QH-46 `review_primary` accetta/rifiuta l'assegnazione esistente o propone un nuovo
valore con evidenze. Nuova revisione proposed, receipt, optimistic concurrency,
idempotenza e current invariati. Una sostituzione nasce tentative/proposed;
confermare l'item non accetta la primaria. Una correzione del testo rimuove la
primaria dal successore per richiederne la nuova valutazione; lo storico resta intatto.

Sei nodi fissi, viste corrente/proposte distinte, accesso Non classés e Éléments.
Membri filtrati prima del LIMIT. La lettura di presenza verifica tutte le dimensioni
e non classificati con selezioni bounded, policy e grafo, fissando lo stesso token
di proiezione per l'intera risposta. Un cambio di epoca/versione o indisponibilità
fa fallire la lettura; nessuna assenza dedotta da una pagina parziale o fallback SQL.
Nessun conteggio globale. Fonte/dettaglio/storia e review rimangono accessibili.

## Reset e limiti

L'owner abbandona i dati sperimentali nel nuovo stato attivo: nessun backfill,
migrazione semantica o nuovo adapter funzionale v1/v2. Le vecchie versioni/codice
rimangono storia e fixture di regressione, non un percorso di conversione runtime.
Le nuove scritture dell'app usano v3, anche per il controllo letterale non classificato.

Il [piano di reset](../qh-51-uum-reset-plan.md) distingue dati applicativi da identità,
configurazione e contabilità, con backup/restore e rollback. Cancellazione sul VPS
solo dopo conferma finale del perimetro e del backup. Nessuna PR #19/0007, merge #23,
inferenza, modifica economica o attivazione provider autorizzata da questa decisione.

QH-47 resta responsabile di identità semantica, duplicati, split/merge, aggiornamenti
e contraddizioni tra sessioni. Le sei dimensioni non risolvono tali problemi.
La qualità di un provider reale e l'accettazione prodotto richiedono prove e review
separate; test con fixture non dimostrano qualità del modello.
