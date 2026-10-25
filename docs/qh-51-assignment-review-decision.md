# QH-51 — Decisione mirata sulla review delle assegnazioni

Stato: **approvato dall’owner il2026-10-21 per implementazione e test isolati**. Il mandato QH-51 del2026-10-21 richiede una decisione preventiva se
l’estensione QH-46 introduce un nuovo contratto persistente.

## Necessità riscontrata

QH-46 oggi conserva una decisione per l’intera revisione (`confirm/reject/correct`),
non per singolo descrittore. Usare quello stato come validazione del tema
confonderebbe validità dell’elemento, assegnazione, certezza e conferma umana.

## Soluzione minima proposta

Nella nuova versione2 dei profili generici, ogni assegnazione conserva i campi già
approvati `dimension`, `value`, `certainty`, `evidence_refs`, più un campo
**`review_state: proposed|accepted|rejected`**, scritto soltanto dal backend.
Il modello non può dichiararlo: l’Engine inizializza ogni assegnazione a proposed.
I vecchi profili/dati restano identici e non vengono qualificati retroattivamente.

Per una possibile equivalenza di nomi il modello può proporre `name_candidate`
facoltativo, solo un nome esatto del vocabolario autorizzato dello stesso Space,
conservato come suggerimento da verificare, mai come alias/merge. Questa assegnazione
non produce un nodo attivo finché l’owner sceglie riuso o tema distinto.

Estendere la stessa operazione QH-46 con `action=review_assignments` e decisioni
per indice del descrittore: accepted/rejected e, solo per un tema accettato,
eventuale nome sostitutivo esplicito. Il backend valida indici, dimensione, certezza
ed evidenze immutate e l’ambito del nome riusato; non accetta actor/stato dal modello.
L’accettazione del nome distinto risolve il suggerimento senza fusione automatica.

La decisione crea una **nuova revisione proposed** dello stesso item attraverso
repository/outbox esistenti, con `based_on_revision_id`, receipt `qh_review`, actor
server e timestamp canonico. Preserva testo, origine dell’interpretazione,
certezza, fonti, citazioni e revisione originale. Nessuna modifica current pointer,
nessuna conferma implicita dell’elemento. La conferma dell’elemento resta l’azione
QH-46 separata e non accetta implicitamente le assegnazioni ancora proposte.
Rifiutare un’assegnazione non rifiuta il testo né cancella la fonte. Il rifiuto
rimane consultabile nella storia; stessa concorrenza/idempotenza/policy QH-46.

La mappa usa assegnazioni tematiche non rifiutate, esplicite e senza un suggerimento
di nome ancora da decidere; distingue proposte/certezza/review. Conteggi e gruppi
restano relativi alla pagina verificata, senza dichiarazioni globali. Un tema può
contenere elementi confermati con assegnazioni proposte e viceversa.

Nessuna nuova tabella/migrazione, autorità o sistema parallelo di review. Profili2
registrati e verificati soltanto in infrastruttura isolata; nessuna registrazione,
nuovo dato, inferenza o cambio configurazione sul VPS.

Alternativa: conservare soltanto review dell’intero item, rimandando il rifiuto
selettivo. Non soddisfa il requisito di questo incremento. Una tabella autonoma
per decisioni tematiche aggiungerebbe identità/storia non necessarie: sconsigliata.

## Verifiche richieste

Rifiuto selettivo con fonte conservata; stato elemento indipendente; asserted non
confirmed; doppia appartenenza; stessa operazione replay; conflitto concorrente;
owner estraneo/graph stale negati; suggerimento nome estraneo rifiutato; refresh e
storia; nessuna scrittura parziale. L’approvazione ricevuta sblocca implementazione e test isolati; nessun campo o profilo viene attivato sul VPS.
