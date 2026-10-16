# QH-33 — sintesi per la decisione del proprietario

**Aggiornamento di chiusura:** la [proposta corrente](qh33-closure-scope.it.md)
registra la seconda verifica AI e il differimento della validazione umana a
[QH-38](https://contextlab.atlassian.net/browse/QH-38). Il protocollo personale
rimane invariato; la sequenza precedente sotto è conservata come storia, non
come requisito aggiuntivo della consegna tecnica proposta. Jira QH-33 richiede
ancora l'allineamento formale dello scope prima della chiusura.

**Aggiornamento: D1–D5 approvate, con le precisazioni del proprietario.** Il testo
sotto conserva il percorso decisionale precedente; le richieste D1–D5 non sono
più pendenti. La verifica personale di tutte le unità non è invece attestata.
Apri il [pacchetto v2](evidence/qh33-v2-20261016/README.md) e la
[matrice compatta](evidence/qh33-v2-20261016/review-matrix.it.md).

**Fasi 1–2: riesame dell’assistente completato su 74/74 unità; validazione umana
ancora da svolgere.** Nessun merge o aggiornamento Jira è autorizzato da questo
riesame. Nessuna nuova inferenza, funzionalità, migrazione o promozione a confirmed.

Il criterio è quello indicato dal proprietario: stato di comprensione evolutivo,
non trascrizione. Conservo lo stato attuale, le evoluzioni necessarie e le
incertezze rilevanti; non trasformo dubbi già risolti in obblighi di copertura attiva.
Questo criterio è già definito: D1–D5 ne approvano l’applicazione al benchmark; resta da verificare
personalmente ogni unità, senza riaprire la scelta generale fra storia e riepilogo.

La [tabella completa delle 74 unità](reviews/qh33-unit-review-20261016.it.md)
riporta per ciascun ID sette giudizi separati, motivazione, evidenza letterale e
collegamento al payload. I [dettagli strutturati](reviews/qh33-reassessment-proposal-20261016.json)
aggiungono motivazioni per dimensione, campi generati e osservazioni sugli offset.
Tutti i payload sono stati riletti: 37 candidati originali e 20 candidati sintetici.
Le annotazioni precedenti non sono state usate come ground truth.

## Risultati da validare

| Categoria | Riscontro diretto / valutazione proposta | Impatto potenziale |
| --- | --- | --- |
| Errore direttamente riscontrabile come fatto attuale | `multilingual.discount_applied`: fonte «Se lo sconto…», proprietà `discount_applied=true`. La fonte non sostiene il flag come fatto attuale; il testo mantiene invece la condizione | Prezzo ipotetico trattato come ottenuto |
| Inferenza personale non sostenuta | `evolving.personal_rejection`: «scegliamo invece» diventa «Jo rejects Mina's proposal». Non prova un rifiuto personale; neppure prova che Jo non abbia mai rifiutato | Posizione/conflitto attribuito a Jo senza supporto esplicito |
| Omissioni significative attuali | `multilingual.no_order_approved`, `multilingual.not_decided`: nessun ordine approvato e nessuna decisione presa sono solo nelle citazioni | Perdere il confine fra possibilità e autorizzazione |
| Classificazioni discutibili | `counter-proposal` accompagna un testo che conserva la scelta; `Jo suspends` perde il plurale ma non dice «Jo da solo» | Annotazione incompleta o sintesi discutibile, non automaticamente fatto falso |
| Relazioni poco utili | `work.relation_encoding`: pilota→obiettivo anziché team→pannello; `multilingual.order_possible`: soglia di sconto→incarico/data ignoti | Collegamenti validi come forma ma poco chiari nel significato |
| Temporalità strutturata | `evolving.unlinked_time_1/2/3`: date autentiche isolate dagli eventi; `personal.future_intent`: data prevista in `fact_from`, testo ancora condizionale | Una lettura dei soli campi temporali può perdere evento o modalità |
| Provenienza mancante | Tre relazioni multilingual senza propria `evidence`; unità `tax_bases`, `excess`, `order_possible` coinvolte | Il batch resta interamente respinto; plausibilità non basta alla pubblicazione |
| Risultati positivi | Work conserva obiettivo/ipotesi/assenza di misure/vincoli; evolving conserva ritiro, mai-adottata, sospensione e ripresa ignota; personal conserva preferenze circoscritte e presenza non confermata; multilingual mantiene netto/lordo, incarico non assegnato e consegna ignota | Evita di trattare l’intera estrazione come sbagliata |

Gli impatti non sono danni osservati nel QH persistente. La tracciabilità di una
citazione non dimostra la verità dell’interpretazione; `proposed` e `asserted`
non sono conferme umane. Nessun voto complessivo o nuova metrica indipendente è
calcolato in questa fase. Le vecchie metriche restano la fotografia del benchmark v1.

## Decisioni D1–D5 approvate, unità ancora da verificare

| ID | Decisione approvata | Applicazione in v2 |
| --- | --- | --- |
| **D1 — criterio evolutivo applicato** | Escludere dal coverage attivo `multilingual.initial_tax_uncertainty` e `multilingual.initial_fit_hypothesis`, conservandole come storia ricostruibile; mantenere invece le due negazioni attuali come omissioni. Riformulare `evolving.trial_duration` come durata **prevista**, `personal.temporary_avoidance` come preferenza condizionale, `personal.ask_intent` come desiderio di chiedere, senza asserire che Lee non abbia agito | Stessi 74 ID; due unità storiche fuori dal denominatore attivo delle 46 proposizioni, tre significati precisati. Niente cancellazione di fonti o trasformazione di un’omissione in pass |
| **D2 — giudizi ambigui e struttura** | Usare i PARZ della tabella per controproposta, attribuzione della sospensione, relazioni poco utili e collegamenti temporali incompleti; distinguere questi casi dal rifiuto personale aggiunto e dal flag sconto applicato | Ratings e applicabilità della v2 espliciti; nessun obbligo nuovo di tipi canonici, nodi persona o campi pubblici |
| **D3 — controlli `.good` riesaminati** | `conditional_es.good` conserva il “se” ma omette permesso non concesso: completezza parziale/negazione mancante. `lifecycle_de.good`, `future_intent_en.good`, `past_completed_it.good` conservano sequenza/passato ma perdono date, “venerdì prossimo”, “ieri”: temporalità parziale. Gli altri controlli sono motivati riga per riga | Non considerare `.good` un verdetto. Non richiedere una trascrizione: segnalare separatamente la precisione temporale persa, senza risolvere date relative inventando ancoraggi |
| **D4 — separare significato e provenienza** | In questo riesame G giudica la tracciabilità della citazione propria; S giudica il sostegno semantico. Una citazione autentica di una frase alterata ha G OK e S NO; una frase fedele con citazione inventata ha S OK e G NO. Offset originali e risolvibilità restano campi distinti | Chiarimento/cambiamento della rubrica v1, che usava provenienza contestuale: va versionato, non confrontato come miglioramento del modello |
| **D5 — limiti accettabili del POC** | Accettare per QH-33 il risultato di misurazione/report, con difetti LLM e limiti strutturali espliciti: il validatore non è un giudice generale del significato; nove controlli alterati passano strutturalmente come proposte. Non promettere che il prompt candidato sia migliore | Permette di verificare la DoD reale senza inventare il requisito “correggere tutti gli errori del modello” o eseguire ora nuove inferenze |

**D1–D5 approvate; i limiti D5 sono accettati per il POC, non risolti o certificati.**
La v2 è separata e preserva v1, catture, template e ledger. Le nuove metriche sono
provvisorie, per versione e dimensione; il cambio di denominatore non è un
miglioramento del modello. Puoi ancora correggere i singoli giudizi per ID.

## Che cosa richiede davvero la validazione personale

Il protocollo esistente, in `scripts/evaluate_qh33.py:human_review`, richiede:

1. Tutti i 74 ID presenti, ogni unità accettata e ogni dimensione applicabile giudicata.
   Accettare il giudizio può confermare un **NO**: non significa dichiarare corretto
   il candidato, né correggere tutti i difetti prima di chiudere il report.
2. Identificatore del revisore e data con fuso della review realmente svolta.
3. Dichiarazione esplicita di indipendenza dall’assistente autore.
4. Verifica esplicita della completezza del riferimento e dei payload completi.

**Sì: il protocollo richiede che il revisore controlli personalmente tutte le unità,
fonti e payload, non soltanto questa sintesi.** La tabella e gli allegati rendono
possibile farlo senza ricostruire manualmente i dati. Non posso attestarlo al tuo
posto, né sostituire queste verifiche con il mio riesame.

Approvare D1–D5 non prova di per sé che tu abbia letto tutte le 74 righe. Se restano
unità non controllate o contestate, le metriche umane restano null e la review
pendente. Non serve ricopiare JSON a mano: dopo le tue dichiarazioni effettive posso
trascrivere fedelmente i giudizi approvati nel formato del protocollo, riportando
correzioni e provenienza dell’approvazione senza inventare firme o attestazioni.
Una rubrica modificata richiede prima v2; il protocollo attuale rifiuta variazioni
di applicabilità sullo stesso benchmark.

## DoD effettiva di Jira QH-33, senza nuovi requisiti

Ticket riletto via Atlassian MCP: QH-33, stato **À faire**, descrizione invariata.
La sua sezione DONE dice:

> Report con metriche separate (coverage, supported claims, non-decisioni, temporality, provenance) e raccomandazione verificabile per il successivo esperimento; nessuna promozione automatica a confirmed.

| Requisito realmente presente | Risultato disponibile | Stato rispetto alla chiusura |
| --- | --- | --- |
| Report con metriche separate | Report e metriche v1/v2 riproducibili; 74 unità distinte per sette dimensioni | Implementato/verificato tecnicamente; versione validata e metriche umane ancora pendenti |
| Raccomandazione verificabile per il successivo esperimento | Protocollo baseline/candidato preparato, una sola variabile, richieste e budget limitati | Implementato/verificato come preparazione; inferenza non eseguita e non necessaria per questa DoD |
| Nessuna promozione automatica a confirmed | Atomicità/proposte e guardie già verificate; nessuna modifica runtime in questo riesame | PASS tecnico; non equivale a correttezza semantica |
| Attività/dipendenza: riferimento validato indipendentemente | Tabella, fonti, payload e decisioni per il proprietario | NOT TESTED: manca la validazione umana effettiva |
| Attività: fixture e confronto offline separati da offset/JSON | Controlli sintetici, confronto del guard temporale, risultati e limiti registrati | PASS tecnico; nessuna misura di miglioramento del LLM |
| Policy: review, merge effettivo e Jira allineato | PR #8 aperta; CI del commit di partenza 60249f6 verde | Non eseguiti; merge e DONE richiedono una tua autorizzazione successiva esplicita |

Il ticket non richiede un’estrazione perfetta, una nuova ontologia o un’inferenza
pagata per chiudere il report. Non userò però il semplice completamento dei test
per sostituire il requisito di riferimento validato.

Dopo la tua approvazione del riferimento: integrazione delle sole modifiche
approvate, audit/test pertinenti, CI sull’ultimo commit e report conclusivo.
**Ti sottoporrò poi l’esito per l’autorizzazione esplicita a merge e transizione DONE.**
L’approvazione semantica non autorizza quelle operazioni.

Follow-up raccomandato: confronto controllato Mistral baseline/candidato, dopo un
riferimento validato e autorizzazione separata al budget. Nessuna esecuzione o avvio
di altro ticket oggi. Finché manca la verifica personale, QH-33 rimane aperto.
