# QH-33 — riesame completo delle 74 unità

**Proposta dell’assistente in attesa del proprietario. Non è validazione umana.** Tutti i 74 ID sono conservati e giudicati di nuovo sulle fonti e sui payload completi. Le precedenti annotazioni non fungono da ground truth. Nessuna modifica al benchmark v1, nessuna metrica indipendente o voto complessivo.

Questa matrice usa il criterio evolutivo indicato dal proprietario e propone cambiamenti di rubrica: non è intercambiabile con le metriche v1. D1–D5 nella [sintesi](../qh33-owner-decisions.it.md) richiedono ancora approvazione.

C = completezza della proposizione attiva; S = significato; A = attori; N = negazioni; T = temporalità; U = incertezza; G = provenienza/tracciabilità proposta. OK/PARZ/NO/— = soddisfatto/parziale/non soddisfatto/non applicabile. Nessun rating è una promozione canonica.

G giudica una citazione propria localizzabile, anche dopo risoluzione deterministica univoca. S giudica se la fonte sostiene il significato: una citazione autentica può accompagnare un claim falso (G OK, S NO). I difetti degli offset originali sono riportati separatamente nei dettagli JSON. G OK sul singolo elemento non rende pubblicabile il batch multilingual.

Le celle applicabili sono motivate nella colonna finale e, separatamente per dimensione, nel [JSON completo](qh33-reassessment-proposal-20261016.json). Le note non sono giudizi del proprietario.

## Work

| ID | C | S | A | N | T | U | G | Evidenza / output | Giudizio motivato e decisioni pendenti |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `work.objective` | OK | OK | — | — | — | OK | OK | [fonte](#evidenza-work-1) · [payload](../evidence/qh8-mistral-20261016/work/output.json) /items/0/text | Il testo mantiene obiettivo, percentuale e contesto; non dichiara una riduzione misurata. |
| `work.crm_unchanged` | OK | OK | — | OK | — | — | OK | [fonte](#evidenza-work-1) · [payload](../evidence/qh8-mistral-20261016/work/output.json) /items/0/text | Senza cambiare il CRM è nel testo, non solo nella citazione. |
| `work.pilot` | OK | OK | OK | — | OK | — | OK | [fonte](#evidenza-work-2) · [payload](../evidence/qh8-mistral-20261016/work/output.json) /items/1/text | Decidiamo mantiene la scelta collettiva e due settimane è durata prevista, non prova del completamento. |
| `work.panel_actor` | OK | OK | OK | — | OK | — | OK | [fonte](#evidenza-work-2) · [payload](../evidence/qh8-mistral-20261016/work/output.json) /items/1/text, /items/5/text | Il soggetto team Aster e il futuro gestirà restano nel testo; la qualità degli estremi della relazione è giudicata separatamente. |
| `work.hypothesis` | OK | OK | — | — | — | OK | OK | [fonte](#evidenza-work-3) · [payload](../evidence/qh8-mistral-20261016/work/output.json) /items/2/text, /items/6/text | Ipotizzo e ipotizza_misura_per non convertono la spiegazione in effetto dimostrato; asserted riguarda il descrittore. |
| `work.no_measurements` | OK | OK | — | OK | OK | OK | OK | [fonte](#evidenza-work-3) · [payload](../evidence/qh8-mistral-20261016/work/output.json) /items/2/text | La negazione temporanea è estratta esplicitamente; non viene dichiarato che il beneficio sia stato provato. |
| `work.budget` | OK | OK | — | — | — | — | OK | [fonte](#evidenza-work-4) · [payload](../evidence/qh8-mistral-20261016/work/output.json) /items/3/text, /items/7/text | Massimo resta nel testo. La proprietà budget=300 EUR non afferma che sia stata spesa quella cifra. |
| `work.no_export` | OK | OK | — | OK | — | — | OK | [fonte](#evidenza-work-4) · [payload](../evidence/qh8-mistral-20261016/work/output.json) /items/3/text | Nessuna esportazione è conservato; il sommario della relazione non elimina il vincolo nell’elemento principale. |
| `work.deadline` | OK | OK | — | — | OK | — | OK | [fonte](#evidenza-work-4) · [payload](../evidence/qh8-mistral-20261016/work/output.json) /items/3/text | Testo e proprietà riportano la data senza aggiungere ora o fuso non presenti. |
| `work.authorizer_unknown` | OK | OK | OK | — | OK | OK | OK | [fonte](#evidenza-work-5) · [payload](../evidence/qh8-mistral-20261016/work/output.json) /items/4/text, /items/8/text | Non viene assegnata l’autorizzazione a Nora, Eli o al team solo perché menzionati. |
| `work.security_unselected` | OK | OK | OK | OK | OK | OK | OK | [fonte](#evidenza-work-5) · [payload](../evidence/qh8-mistral-20261016/work/output.json) /items/4/text | Il testo conserva non abbiamo ancora scelto; non attribuisce l’incarico a nessuno. |
| `work.relation_encoding` | — | PARZ | PARZ | — | — | — | OK | [fonte](#evidenza-work-2) · [payload](../evidence/qh8-mistral-20261016/work/output.json) /items/5/relation | Gli estremi work-2/work-1 sono enunciati, consentiti dal modello; non identificano direttamente i ruoli descritti. Utilità parziale, non FK invalide. **D2** |

## Evolving

| ID | C | S | A | N | T | U | G | Evidenza / output | Giudizio motivato e decisioni pendenti |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `evolving.original_proposal` | OK | OK | OK | — | OK | OK | OK | [fonte](#evidenza-evolving-1) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/0/text, /items/5/text | Il testo mantiene proponente, data e solo una proposta; nessuna adozione è inferita. |
| `evolving.proposal_only` | OK | OK | — | OK | OK | OK | OK | [fonte](#evidenza-evolving-1) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/0/text | È solo una proposta è esplicito; il successivo ritiro non viene letto come revoca di una decisione adottata. |
| `evolving.adopted_trial` | OK | PARZ | OK | — | OK | — | OK | [fonte](#evidenza-evolving-2) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/1/text, /items/6/text | Scegliamo e frequenza/durata sono nel testo; counter-proposal rende l’annotazione dell’adozione discutibile, senza cancellare la scelta. **D2** |
| `evolving.trial_duration` | OK | OK | — | — | OK | — | OK | [fonte](#evidenza-evolving-2) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/1/text | La conversazione sceglie una prova per una settimana ma la sospende il giorno successivo. Il significato v1 lasts one week va precisato. **D1** |
| `evolving.withdrawn` | OK | OK | OK | — | OK | — | OK | [fonte](#evidenza-evolving-3) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/2/text, /items/9/text | Ritiro nel testo e Mina withdraws nella relazione concordano; non è attribuito a Jo il ritiro. |
| `evolving.never_adopted` | OK | OK | — | OK | OK | — | OK | [fonte](#evidenza-evolving-3) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/2/text | Non è mai stata adottata è nel testo; questa storia serve a capire perché la sospensione non le ripristina. |
| `evolving.suspension` | OK | OK | OK | — | OK | — | OK | [fonte](#evidenza-evolving-4) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/3/text | L’elemento conserva sospendiamo, data e oggetto. Il testo più singolare della relazione è valutato nell’unità personal_suspension. |
| `evolving.absence_reason` | OK | OK | — | — | OK | — | OK | [fonte](#evidenza-evolving-4) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/3/text | Il motivo segue i due punti della fonte e rimane nel testo; non si inventano identità degli assenti. |
| `evolving.current_suspended` | OK | OK | — | — | OK | — | OK | [fonte](#evidenza-evolving-5) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/4/text, /items/7/text | Testo e state=suspended concordano; le precedenti scelte non sono presentate come attività attuale in corso. |
| `evolving.no_return` | OK | OK | — | OK | OK | — | OK | [fonte](#evidenza-evolving-5) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/4/text | La negazione resta esplicita nell’aggiornamento di stato. |
| `evolving.restart_unknown` | OK | OK | — | — | OK | OK | OK | [fonte](#evidenza-evolving-5) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/4/text | Nessuna data di riavvio viene generata; il dubbio è tuttora rilevante allo stato finale. |
| `evolving.counter_proposal` | — | PARZ | — | — | PARZ | — | OK | [fonte](#evidenza-evolving-2) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/1/descriptors | Può indicare il ruolo di alternativa, non necessariamente negare l’adozione. Propongo partial, non errore fattuale certo. **D2** |
| `evolving.personal_rejection` | — | NO | NO | — | — | — | OK | [fonte](#evidenza-evolving-2) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/8/text | Scegliamo invece documenta una scelta collettiva; non prova Jo rejects Mina. Non affermo l’opposto, cioè che Jo non abbia mai rifiutato. **D2** |
| `evolving.personal_suspension` | — | PARZ | PARZ | — | OK | — | OK | [fonte](#evidenza-evolving-4) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/10/text | Jo suspends perde il plurale, ma non afferma Jo da solo. Propongo attribuzione parziale, non invenzione certa di decisione esclusiva. **D2** |
| `evolving.unlinked_time_1` | — | OK | — | — | PARZ | — | OK | [fonte](#evidenza-evolving-1) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/11/temporal | Temporal-1 riporta un timestamp corretto. Il fatto qualificato conserva la data nel testo ma non ha un campo temporale o un legame con quel nodo-data. **D2** |
| `evolving.unlinked_time_2` | — | OK | — | — | PARZ | — | OK | [fonte](#evidenza-evolving-2) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/12/temporal | Temporal-2 riporta un timestamp corretto. Il fatto qualificato conserva la data nel testo ma non ha un campo temporale o un legame con quel nodo-data. **D2** |
| `evolving.unlinked_time_3` | — | OK | — | — | PARZ | — | OK | [fonte](#evidenza-evolving-4) · [payload](../evidence/qh8-mistral-20261016/evolving/output.json) /items/13/temporal | Temporal-3 riporta un timestamp corretto. Il fatto qualificato conserva la data nel testo ma non ha un campo temporale o un legame con quel nodo-data. **D2** |

## Personal

| ID | C | S | A | N | T | U | G | Evidenza / output | Giudizio motivato e decisioni pendenti |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `personal.quiet_preference` | OK | OK | — | — | — | — | OK | [fonte](#evidenza-personal-1) · [payload](../evidence/qh8-mistral-20261016/personal/output.json) /items/0/text | La preferenza non è trasformata in diagnosi o tratto permanente. |
| `personal.temporary_avoidance` | OK | OK | OK | OK | OK | OK | OK | [fonte](#evidenza-personal-1) · [payload](../evidence/qh8-mistral-20261016/personal/output.json) /items/0/text | Eviterei e senza dire che li evito sempre sono mantenuti. Il riferimento v1 crowds are avoided oggi suona più fattuale della fonte e va riformulato. **D1** |
| `personal.past_train` | OK | OK | OK | — | OK | — | OK | [fonte](#evidenza-personal-2) · [payload](../evidence/qh8-mistral-20261016/personal/output.json) /items/1/text | Testo e timestamp concordano; non sono applicati al viaggio futuro. |
| `personal.not_tomorrow` | OK | OK | — | OK | OK | — | OK | [fonte](#evidenza-personal-2) · [payload](../evidence/qh8-mistral-20261016/personal/output.json) /items/1/text | La distinzione temporale e la negazione rimangono nel testo. |
| `personal.future_intent` | OK | OK | OK | — | PARZ | OK | OK | [fonte](#evidenza-personal-3) · [payload](../evidence/qh8-mistral-20261016/personal/output.json) /items/2/text | Il testo non dice che sia avvenuta. fact_from data l’evento pianificato senza tipizzarne la modalità: cautela strutturale, non contenuto falso certo. **D2** |
| `personal.not_completed` | OK | OK | — | OK | OK | — | OK | [fonte](#evidenza-personal-3) · [payload](../evidence/qh8-mistral-20261016/personal/output.json) /items/2/text | Non l’ho ancora fatta è esplicito. Non leggere il solo fact_from come una conferma dell’accaduto. |
| `personal.weather_condition` | OK | OK | — | — | OK | OK | OK | [fonte](#evidenza-personal-3) · [payload](../evidence/qh8-mistral-20261016/personal/output.json) /items/2/text | Potrei e se conservano la condizione; né pioggia né rinuncia sono dichiarate avvenute. |
| `personal.attendance_possible` | OK | OK | OK | — | — | OK | OK | [fonte](#evidenza-personal-4) · [payload](../evidence/qh8-mistral-20261016/personal/output.json) /items/3/text | Forse e il descrittore uncertain attendance mantengono l’incertezza; asserted classifica quel descrittore, non conferma la presenza. |
| `personal.attendance_unconfirmed` | OK | OK | OK | OK | — | OK | OK | [fonte](#evidenza-personal-4) · [payload](../evidence/qh8-mistral-20261016/personal/output.json) /items/3/text | La non-conferma è nel testo; non si inventa una risposta affermativa. |
| `personal.ask_intent` | OK | OK | OK | — | — | OK | OK | [fonte](#evidenza-personal-5) · [payload](../evidence/qh8-mistral-20261016/personal/output.json) /items/4/text | Vorrei è più debole di un incarico deciso. Il riferimento non deve trasformare l’assenza di un’azione attribuita a Lee nella certezza che Lee non abbia agito. **D1** |
| `personal.route_open` | OK | OK | — | — | OK | OK | OK | [fonte](#evidenza-personal-5) · [payload](../evidence/qh8-mistral-20261016/personal/output.json) /items/4/text | Nessun percorso o decisore viene inventato; la questione è ancora rilevante. |

## Multilingual

| ID | C | S | A | N | T | U | G | Evidenza / output | Giudizio motivato e decisioni pendenti |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `multilingual.net` | OK | OK | — | — | — | — | OK | [fonte](#evidenza-multilingual-1) · [payload](../evidence/qh8-mistral-20261016/multilingual/output.json) /items/0/text | Testo, valore e tax_included=false sono coerenti; il netto resta significativo accanto al lordo. |
| `multilingual.initial_tax_uncertainty` | — | — | — | — | — | — | — | [fonte](#evidenza-multilingual-1) · [payload](../evidence/qh8-mistral-20261016/multilingual/output.json) nessun claim estratto | Il dubbio non è estratto come proposizione. Con il criterio evolutivo non lo penalizzerei come assenza attiva: non è una falsa estrazione né un pass fittizio. **D1** |
| `multilingual.ceiling` | OK | OK | — | — | — | — | OK | [fonte](#evidenza-multilingual-2) · [payload](../evidence/qh8-mistral-20261016/multilingual/output.json) /items/1/text | Valore e base fiscale sono preservati. Il descrittore quotation non modifica il testo tetto. |
| `multilingual.initial_fit_hypothesis` | — | — | — | — | — | — | — | [fonte](#evidenza-multilingual-2) · [payload](../evidence/qh8-mistral-20261016/multilingual/output.json) nessun claim estratto | La fonte ne conserva la storia, ma non deve restare una possibilità attuale in competizione con lo sforamento noto. Esclusione proposta dal solo coverage attivo. **D1** |
| `multilingual.gross` | OK | OK | — | — | — | — | OK | [fonte](#evidenza-multilingual-3) · [payload](../evidence/qh8-mistral-20261016/multilingual/output.json) /items/2/text | Numero e imposte concordano con la fonte; non sostituiscono retroattivamente il prezzo netto. |
| `multilingual.tax_bases` | OK | OK | — | — | — | — | NO | [fonte](#evidenza-multilingual-3) · [payload](../evidence/qh8-mistral-20261016/multilingual/output.json) /items/7/text | La relazione conserva la spiegazione, ma non ha una propria evidence. Il supporto leggibile nella fonte non sostituisce il collegamento di provenienza mancante. **D4** |
| `multilingual.excess` | OK | OK | — | — | — | — | PARZ | [fonte](#evidenza-multilingual-4) · [payload](../evidence/qh8-mistral-20261016/multilingual/output.json) /items/3/text, /items/6/text | Il testo e l’elemento item-4 sono supportati; la duplicazione relation-1 non ha evidence. Provenienza parziale del complesso di affermazioni. **D4** |
| `multilingual.no_order_approved` | NO | — | — | NO | — | — | — | [fonte](#evidenza-multilingual-4) · [payload](../evidence/qh8-mistral-20261016/multilingual/output.json) nessun claim estratto | L’informazione è solo nella citazione: manca nei testi, proprietà e relazioni estratti. È uno stato operativo attuale, non un dubbio storico superato. **D1** |
| `multilingual.discount_condition` | PARZ | PARZ | — | — | — | NO | OK | [fonte](#evidenza-multilingual-5) · [payload](../evidence/qh8-mistral-20261016/multilingual/output.json) /items/4/text | Se resta nel testo, ma discount_applied=true contraddice la modalità. La copertura e il significato del candidato completo sono parziali; la cautela nelle proprietà fallisce. **D4** |
| `multilingual.order_possible` | OK | PARZ | — | — | — | OK | NO | [fonte](#evidenza-multilingual-5) · [payload](../evidence/qh8-mistral-20261016/multilingual/output.json) /items/8/text | Il testo della relazione mantiene la condizione. Il collegamento implies_discount_target termina però sull’elemento incarico/data ignoti, e manca evidence: il senso del grafo è poco chiaro. **D2, D4** |
| `multilingual.not_decided` | NO | — | — | NO | — | — | — | [fonte](#evidenza-multilingual-5) · [payload](../evidence/qh8-mistral-20261016/multilingual/output.json) nessun claim estratto | Potremmo è preservato nella relazione, ma la non-decisione esplicita non è estratta. È distinta dallo stato nessun ordine approvato. **D1** |
| `multilingual.unassigned` | OK | OK | OK | OK | — | OK | OK | [fonte](#evidenza-multilingual-6) · [payload](../evidence/qh8-mistral-20261016/multilingual/output.json) /items/5/text | Testo e discount_assigned=false mantengono il ruolo non assegnato, senza attribuirlo a chi parla. |
| `multilingual.delivery_unknown` | OK | OK | — | — | OK | OK | OK | [fonte](#evidenza-multilingual-6) · [payload](../evidence/qh8-mistral-20261016/multilingual/output.json) /items/5/text | delivery_date_known=false e il testo non inventano scadenze; incertezza tuttora rilevante. |
| `multilingual.discount_applied` | — | NO | — | — | — | NO | OK | [fonte](#evidenza-multilingual-5) · [payload](../evidence/qh8-mistral-20261016/multilingual/output.json) /items/4/properties/discount_applied | La fonte dice se; il booleano true presenta come ottenuto ciò che è condizionale. La citazione è autentica, non l’interpretazione del campo. **D4** |

## Controlli sintetici (nessun output Mistral)

| ID | C | S | A | N | T | U | G | Evidenza / output | Giudizio motivato e decisioni pendenti |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `control.conditional_es.good` | PARZ | OK | — | NO | — | OK | OK | [fonte](#evidenza-control-conditional-es) · [payload](#payload-control-conditional-es-good) /items/0/text | Il candidato conserva la condizione, ma non esplicita che il permesso manca ancora. Il nome good non basta a dichiararlo completo. **D3** |
| `control.conditional_es.mutated` | NO | NO | — | NO | NO | NO | OK | [fonte](#evidenza-control-conditional-es) · [payload](#payload-control-conditional-es-mutated) /items/0/text | Inventa concessione e spedizione compiuta; capovolge la negazione e perde la condizione. |
| `control.negation_en.good` | OK | OK | — | OK | OK | — | OK | [fonte](#evidenza-control-negation-en) · [payload](#payload-control-negation-en-good) /items/0/text | La non-approvazione è esplicita e restituisce lo stato operativo rilevante. |
| `control.negation_en.mutated` | NO | NO | — | NO | NO | — | OK | [fonte](#evidenza-control-negation-en) · [payload](#payload-control-negation-en-mutated) /items/0/text | Dichiara approvata la prenotazione contro la negazione della fonte. |
| `control.actual_discount_fr.good` | OK | OK | — | — | OK | — | OK | [fonte](#evidenza-control-actual-discount-fr) · [payload](#payload-control-actual-discount-fr-good) /items/0/text | Traduzione e booleano true sono giustificati: non bisogna vietare tutti gli sconti applicati. |
| `control.actual_discount_fr.mutated` | NO | NO | — | NO | NO | — | OK | [fonte](#evidenza-control-actual-discount-fr) · [payload](#payload-control-actual-discount-fr-mutated) /items/0/text | Nega uno sconto esplicitamente applicato e omette il pagamento; false contraddice la fonte. |
| `control.collective_it.good` | OK | OK | OK | — | OK | — | OK | [fonte](#evidenza-control-collective-it) · [payload](#payload-control-collective-it-good) /items/0/text | Il gruppo decisore è conservato senza confondere il ruolo di Uma. |
| `control.collective_it.mutated` | PARZ | NO | NO | — | OK | — | OK | [fonte](#evidenza-control-collective-it) · [payload](#payload-control-collective-it-mutated) /items/0/text | Mantiene il tema della pausa ma inventa una decisione esclusiva di Uma. |
| `control.individual_en.good` | OK | OK | OK | OK | OK | — | OK | [fonte](#evidenza-control-individual-en) · [payload](#payload-control-individual-en-good) /items/0/text | Attore individuale e assenza del voto sono mantenuti: una decisione individuale può essere corretta. |
| `control.individual_en.mutated` | NO | NO | NO | NO | OK | — | OK | [fonte](#evidenza-control-individual-en) · [payload](#payload-control-individual-en-mutated) /items/0/text | Sostituisce Ren con il comitato e perde la negazione del voto. |
| `control.lifecycle_de.good` | OK | OK | — | OK | PARZ | — | OK | [fonte](#evidenza-control-lifecycle-de) · [payload](#payload-control-lifecycle-de-good) /items/0/text | Sequenza e stato finale sono conservati, ma le tre date spariscono dal claim. Limite di precisione temporale, non sequenza falsa. **D3** |
| `control.lifecycle_de.mutated` | NO | NO | — | NO | NO | — | OK | [fonte](#evidenza-control-lifecycle-de) · [payload](#payload-control-lifecycle-de-mutated) /items/0/text | Inventa una ripresa attuale e perde proposta/adozione/sospensione. |
| `control.future_intent_en.good` | OK | OK | — | OK | PARZ | OK | OK | [fonte](#evidenza-control-future-intent-en) · [payload](#payload-control-future-intent-en-good) /items/0/text | Mantiene intenzione, meteo e non-compimento, ma sostituisce venerdì prossimo con un futuro generico. **D3** |
| `control.future_intent_en.mutated` | NO | NO | — | NO | NO | NO | OK | [fonte](#evidenza-control-future-intent-en) · [payload](#payload-control-future-intent-en-mutated) /items/0/text | Trasforma un’intenzione condizionata in un evento completato. |
| `control.past_completed_it.good` | OK | OK | — | OK | PARZ | — | OK | [fonte](#evidenza-control-past-completed-it) · [payload](#payload-control-past-completed-it-good) /items/0/text | Già avvenuta conserva il passato compiuto, ma perde la precisazione relativa ieri. **D3** |
| `control.past_completed_it.mutated` | NO | NO | — | NO | NO | — | OK | [fonte](#evidenza-control-past-completed-it) · [payload](#payload-control-past-completed-it-mutated) /items/0/text | Trasforma un fatto passato in una sola intenzione futura. |
| `control.uncertain_fr.good` | OK | OK | OK | OK | — | OK | OK | [fonte](#evidenza-control-uncertain-fr) · [payload](#payload-control-uncertain-fr-good) /items/0/text | Sam e la non-conferma sono preservati, senza diventare fatto certo. |
| `control.uncertain_fr.mutated` | NO | NO | OK | NO | — | NO | OK | [fonte](#evidenza-control-uncertain-fr) · [payload](#payload-control-uncertain-fr-mutated) /items/0/text | Mantiene Sam come soggetto ma inventa la conferma della presenza. |
| `control.provenance_unicode.good` | OK | OK | — | OK | OK | — | OK | [fonte](#evidenza-control-provenance-unicode) · [payload](#payload-control-provenance-unicode-good) /items/0/text | Il significato e la negazione sono preservati; la citazione con Unicode resta letterale. |
| `control.provenance_unicode.mutated` | OK | OK | — | OK | OK | — | NO | [fonte](#evidenza-control-provenance-unicode) · [payload](#payload-control-provenance-unicode-mutated) /items/0/text | Il significato del testo resta fedele, ma la citazione Invented support never spoken non esiste nella fonte. |

## Evidenze originali consultabili

Le citazioni sono letterali. Gli offset sono Unicode, intervalli `[start,end)`. Per le conversazioni, gli speaker si ricostruiscono dai turni del source.json. Per i controlli il testo è quello scritto nella fixture; non proviene da un modello.

<a id="evidenza-work-1"></a>
### work-1

[Fonte originale](../evidence/qh8-mistral-20261016/work/source.json) · revisione `2ec42859-b01c-534c-b7ca-22428aad5895` · turno `work-1` · `[6,115)`.

> L’obiettivo del progetto Faro è ridurre del 20% il tempo tra richiesta e assegnazione, senza cambiare il CRM.

<a id="evidenza-work-2"></a>
### work-2

[Fonte originale](../evidence/qh8-mistral-20261016/work/source.json) · revisione `2ec42859-b01c-534c-b7ca-22428aad5895` · turno `work-2` · `[121,230)`.

> Decidiamo un pilota di due settimane con il team Aster. Il team Aster gestirà il pannello delle assegnazioni.

<a id="evidenza-work-3"></a>
### work-3

[Fonte originale](../evidence/qh8-mistral-20261016/work/source.json) · revisione `2ec42859-b01c-534c-b7ca-22428aad5895` · turno `work-3` · `[237,332)`.

> Ipotizzo che un pannello condiviso riduca i passaggi duplicati; non abbiamo ancora misurazioni.

<a id="evidenza-work-4"></a>
### work-4

[Fonte originale](../evidence/qh8-mistral-20261016/work/source.json) · revisione `2ec42859-b01c-534c-b7ca-22428aad5895` · turno `work-4` · `[338,438)`.

> Vincoli: budget massimo 300 EUR e nessuna esportazione di dati dal CRM. La scadenza è il 2026-11-20.

<a id="evidenza-work-5"></a>
### work-5

[Fonte originale](../evidence/qh8-mistral-20261016/work/source.json) · revisione `2ec42859-b01c-534c-b7ca-22428aad5895` · turno `work-5` · `[445,549)`.

> Resta aperto chi autorizzerà l’accesso al pannello. Non abbiamo ancora scelto un responsabile sicurezza.

<a id="evidenza-evolving-1"></a>
### evolving-1

[Fonte originale](../evidence/qh8-mistral-20261016/evolving/source.json) · revisione `3f2a8b04-ebe5-5f75-9173-f4cb4f45172b` · turno `evolving-1` · `[6,91)`.

> Il 2026-11-02T09:00:00Z propongo riunioni settimanali di un’ora. È solo una proposta.

<a id="evidenza-evolving-2"></a>
### evolving-2

[Fonte originale](../evidence/qh8-mistral-20261016/evolving/source.json) · revisione `3f2a8b04-ebe5-5f75-9173-f4cb4f45172b` · turno `evolving-2` · `[96,206)`.

> Il 2026-11-03T10:00:00Z scegliamo invece una prova di briefing giornalieri di dieci minuti, per una settimana.

<a id="evidenza-evolving-3"></a>
### evolving-3

[Fonte originale](../evidence/qh8-mistral-20261016/evolving/source.json) · revisione `3f2a8b04-ebe5-5f75-9173-f4cb4f45172b` · turno `evolving-3` · `[213,285)`.

> Ritiro la proposta delle riunioni settimanali. Non è mai stata adottata.

<a id="evidenza-evolving-4"></a>
### evolving-4

[Fonte originale](../evidence/qh8-mistral-20261016/evolving/source.json) · revisione `3f2a8b04-ebe5-5f75-9173-f4cb4f45172b` · turno `evolving-4` · `[290,384)`.

> Il 2026-11-04T08:00:00Z sospendiamo anche la prova giornaliera: due partecipanti sono assenti.

<a id="evidenza-evolving-5"></a>
### evolving-5

[Fonte originale](../evidence/qh8-mistral-20261016/evolving/source.json) · revisione `3f2a8b04-ebe5-5f75-9173-f4cb4f45172b` · turno `evolving-5` · `[391,507)`.

> La situazione attuale è prova sospesa, non ritorno alle riunioni settimanali. Quando riprenderemo resta da decidere.

<a id="evidenza-personal-1"></a>
### personal-1

[Fonte originale](../evidence/qh8-mistral-20261016/personal/source.json) · revisione `83253202-fb5d-5073-a27a-ab83e117f09c` · turno `personal-1` · `[7,121)`.

> Preferisco incontrarci in un bar tranquillo; per oggi eviterei i locali affollati, senza dire che li evito sempre.

<a id="evidenza-personal-2"></a>
### personal-2

[Fonte originale](../evidence/qh8-mistral-20261016/personal/source.json) · revisione `83253202-fb5d-5073-a27a-ab83e117f09c` · turno `personal-2` · `[129,239)`.

> Il mio treno è stato cancellato il 2026-10-09T17:30:00Z. Questo è un evento passato, non il viaggio di domani.

<a id="evidenza-personal-3"></a>
### personal-3

[Fonte originale](../evidence/qh8-mistral-20261016/personal/source.json) · revisione `83253202-fb5d-5073-a27a-ab83e117f09c` · turno `personal-3` · `[247,361)`.

> Ho intenzione di fare una passeggiata il 2026-10-17T09:00:00Z. Non l’ho ancora fatta e potrei rinunciare se piove.

<a id="evidenza-personal-4"></a>
### personal-4

[Fonte originale](../evidence/qh8-mistral-20261016/personal/source.json) · revisione `83253202-fb5d-5073-a27a-ab83e117f09c` · turno `personal-4` · `[369,436)`.

> Forse verrò alla passeggiata, ma non ho confermato la mia presenza.

<a id="evidenza-personal-5"></a>
### personal-5

[Fonte originale](../evidence/qh8-mistral-20261016/personal/source.json) · revisione `83253202-fb5d-5073-a27a-ab83e117f09c` · turno `personal-5` · `[444,537)`.

> Vorrei chiedere a Lee se conosce un percorso coperto. La scelta del percorso è ancora aperta.

<a id="evidenza-multilingual-1"></a>
### multilingual-1

[Fonte originale](../evidence/qh8-mistral-20261016/multilingual/source.json) · revisione `192dbd71-0831-55d5-8cea-b2fa67c499a8` · turno `multilingual-1` · `[9,98)`.

> Le devis est de 300 EUR hors taxes. Je ne sais pas encore si notre plafond inclut la TVA.

<a id="evidenza-multilingual-2"></a>
### multilingual-2

[Fonte originale](../evidence/qh8-mistral-20261016/multilingual/source.json) · revisione `192dbd71-0831-55d5-8cea-b2fa67c499a8` · turno `multilingual-2` · `[105,197)`.

> Il nostro tetto è 350 EUR IVA inclusa. Forse il preventivo rientra, ma dobbiamo verificarlo.

<a id="evidenza-multilingual-3"></a>
### multilingual-3

[Fonte originale](../evidence/qh8-mistral-20261016/multilingual/source.json) · revisione `192dbd71-0831-55d5-8cea-b2fa67c499a8` · turno `multilingual-3` · `[204,330)`.

> The final total is 360 EUR including tax. That resolves the apparent 300 versus 360 discrepancy; they use different tax bases.

<a id="evidenza-multilingual-4"></a>
### multilingual-4

[Fonte originale](../evidence/qh8-mistral-20261016/multilingual/source.json) · revisione `192dbd71-0831-55d5-8cea-b2fa67c499a8` · turno `multilingual-4` · `[340,431)`.

> Donc le devis dépasse le plafond de 10 EUR. Aucune commande n’est approuvée pour le moment.

<a id="evidenza-multilingual-5"></a>
### multilingual-5

[Fonte originale](../evidence/qh8-mistral-20261016/multilingual/source.json) · revisione `192dbd71-0831-55d5-8cea-b2fa67c499a8` · turno `multilingual-5` · `[438,530)`.

> Se lo sconto ci porta a 350 EUR tutto incluso, potremmo ordinare. Non è una decisione presa.

<a id="evidenza-multilingual-6"></a>
### multilingual-6

[Fonte originale](../evidence/qh8-mistral-20261016/multilingual/source.json) · revisione `192dbd71-0831-55d5-8cea-b2fa67c499a8` · turno `multilingual-6` · `[537,635)`.

> Who will ask for the discount? We have not assigned that task. The delivery date is still unknown.

<a id="evidenza-control-conditional-es"></a>
### control.conditional_es

[Fonte originale](../../apps/api/tests/fixtures/qh33/benchmark.json) · revisione `6e319b5e-21bc-51cd-9555-ff78e02919b6` · turno `focus` · `[10,86)`.

> Si se concede el permiso, el envío podría salir; todavía no se ha concedido.

<a id="evidenza-control-negation-en"></a>
### control.negation_en

[Fonte originale](../../apps/api/tests/fixtures/qh33/benchmark.json) · revisione `673e78e3-2f6f-5377-a249-d77c8be9d577` · turno `focus` · `[10,61)`.

> No booking was approved; approval is still pending.

<a id="evidenza-control-actual-discount-fr"></a>
### control.actual_discount_fr

[Fonte originale](../../apps/api/tests/fixtures/qh33/benchmark.json) · revisione `c804a55c-ace0-5fa1-9358-640e1fab2ff6` · turno `focus` · `[10,71)`.

> La remise de 8 % a été appliquée. Le montant payé est 92 EUR.

<a id="evidenza-control-collective-it"></a>
### control.collective_it

[Fonte originale](../../apps/api/tests/fixtures/qh33/benchmark.json) · revisione `7900861d-59c9-5ceb-957d-1133b6da7fb1` · turno `focus` · `[10,84)`.

> Le tre delegate hanno votato insieme la pausa. Uma riferisce il risultato.

<a id="evidenza-control-individual-en"></a>
### control.individual_en

[Fonte originale](../../apps/api/tests/fixtures/qh33/benchmark.json) · revisione `ec2590a9-f153-59e1-ab0c-473150e41907` · turno `focus` · `[10,69)`.

> I, Ren, authorized the release; the committee did not vote.

<a id="evidenza-control-lifecycle-de"></a>
### control.lifecycle_de

[Fonte originale](../../apps/api/tests/fixtures/qh33/benchmark.json) · revisione `133d0391-44d2-5960-98a7-a8abd28b3ff6` · turno `focus` · `[10,142)`.

> Am 2030-05-01 wurde der Test vorgeschlagen, am 2030-05-02 angenommen und am 2030-05-03 ausgesetzt. Er wurde nicht wiederaufgenommen.

<a id="evidenza-control-future-intent-en"></a>
### control.future_intent_en

[Fonte originale](../../apps/api/tests/fixtures/qh33/benchmark.json) · revisione `fad3d229-eff0-5bd0-a97b-756c5351c1e9` · turno `focus` · `[10,84)`.

> I intend to cycle next Friday if it is dry. I have not done that ride yet.

<a id="evidenza-control-past-completed-it"></a>
### control.past_completed_it

[Fonte originale](../../apps/api/tests/fixtures/qh33/benchmark.json) · revisione `55d5dc90-6939-592d-af04-dd2aeb53c3ce` · turno `focus` · `[10,74)`.

> La visita è avvenuta ieri. Non è una semplice intenzione futura.

<a id="evidenza-control-uncertain-fr"></a>
### control.uncertain_fr

[Fonte originale](../../apps/api/tests/fixtures/qh33/benchmark.json) · revisione `3b209587-d463-5f03-90c5-25374ecd5ca6` · turno `focus` · `[10,73)`.

> Peut-être que Sam participera; sa présence n’est pas confirmée.

<a id="evidenza-control-provenance-unicode"></a>
### control.provenance_unicode

[Fonte originale](../../apps/api/tests/fixtures/qh33/benchmark.json) · revisione `b884e38c-0852-505e-8257-036b7a99f56a` · turno `focus` · `[10,87)`.

> The café reopening was announced, not completed: é, é and 🙂 remain distinct.

## Payload integrali dei controlli

Per le quattro conversazioni i collegamenti nella matrice aprono i JSON originali completi (37 candidati). Qui sono presenti tutti i 20 payload sintetici, inclusi proprietà e citazioni. I nomi good/mutated indicano l’intenzione originaria dell’autore, non l’esito di questa rilettura.

<a id="payload-control-conditional-es-good"></a>
### control.conditional_es.good

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "El envío solo podría salir si se concede el permiso.",
      "evidence": [
        {
          "source_revision_id": "6e319b5e-21bc-51cd-9555-ff78e02919b6",
          "start": 10,
          "end": 86,
          "quote": "Si se concede el permiso, el envío podría salir; todavía no se ha concedido."
        }
      ]
    }
  ]
}
```

<a id="payload-control-conditional-es-mutated"></a>
### control.conditional_es.mutated

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "El permiso se ha concedido y el envío salió.",
      "evidence": [
        {
          "source_revision_id": "6e319b5e-21bc-51cd-9555-ff78e02919b6",
          "start": 10,
          "end": 86,
          "quote": "Si se concede el permiso, el envío podría salir; todavía no se ha concedido."
        }
      ]
    }
  ]
}
```

<a id="payload-control-negation-en-good"></a>
### control.negation_en.good

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "No booking has been approved.",
      "evidence": [
        {
          "source_revision_id": "673e78e3-2f6f-5377-a249-d77c8be9d577",
          "start": 10,
          "end": 61,
          "quote": "No booking was approved; approval is still pending."
        }
      ]
    }
  ]
}
```

<a id="payload-control-negation-en-mutated"></a>
### control.negation_en.mutated

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "The booking has been approved.",
      "evidence": [
        {
          "source_revision_id": "673e78e3-2f6f-5377-a249-d77c8be9d577",
          "start": 10,
          "end": 61,
          "quote": "No booking was approved; approval is still pending."
        }
      ]
    }
  ]
}
```

<a id="payload-control-actual-discount-fr-good"></a>
### control.actual_discount_fr.good

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "A discount of 8% was applied; EUR 92 was paid.",
      "evidence": [
        {
          "source_revision_id": "c804a55c-ace0-5fa1-9358-640e1fab2ff6",
          "start": 10,
          "end": 71,
          "quote": "La remise de 8 % a été appliquée. Le montant payé est 92 EUR."
        }
      ],
      "properties": {
        "discount_applied": true
      }
    }
  ]
}
```

<a id="payload-control-actual-discount-fr-mutated"></a>
### control.actual_discount_fr.mutated

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "No discount was applied.",
      "evidence": [
        {
          "source_revision_id": "c804a55c-ace0-5fa1-9358-640e1fab2ff6",
          "start": 10,
          "end": 71,
          "quote": "La remise de 8 % a été appliquée. Le montant payé est 92 EUR."
        }
      ],
      "properties": {
        "discount_applied": false
      }
    }
  ]
}
```

<a id="payload-control-collective-it-good"></a>
### control.collective_it.good

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "Le tre delegate hanno deciso insieme la pausa.",
      "evidence": [
        {
          "source_revision_id": "7900861d-59c9-5ceb-957d-1133b6da7fb1",
          "start": 10,
          "end": 84,
          "quote": "Le tre delegate hanno votato insieme la pausa. Uma riferisce il risultato."
        }
      ]
    }
  ]
}
```

<a id="payload-control-collective-it-mutated"></a>
### control.collective_it.mutated

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "Uma ha deciso da sola la pausa.",
      "evidence": [
        {
          "source_revision_id": "7900861d-59c9-5ceb-957d-1133b6da7fb1",
          "start": 10,
          "end": 84,
          "quote": "Le tre delegate hanno votato insieme la pausa. Uma riferisce il risultato."
        }
      ]
    }
  ]
}
```

<a id="payload-control-individual-en-good"></a>
### control.individual_en.good

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "Ren authorized the release; no committee vote occurred.",
      "evidence": [
        {
          "source_revision_id": "ec2590a9-f153-59e1-ab0c-473150e41907",
          "start": 10,
          "end": 69,
          "quote": "I, Ren, authorized the release; the committee did not vote."
        }
      ]
    }
  ]
}
```

<a id="payload-control-individual-en-mutated"></a>
### control.individual_en.mutated

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "The committee authorized the release.",
      "evidence": [
        {
          "source_revision_id": "ec2590a9-f153-59e1-ab0c-473150e41907",
          "start": 10,
          "end": 69,
          "quote": "I, Ren, authorized the release; the committee did not vote."
        }
      ]
    }
  ]
}
```

<a id="payload-control-lifecycle-de-good"></a>
### control.lifecycle_de.good

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "The test was proposed, then adopted, then suspended; it has not resumed.",
      "evidence": [
        {
          "source_revision_id": "133d0391-44d2-5960-98a7-a8abd28b3ff6",
          "start": 10,
          "end": 142,
          "quote": "Am 2030-05-01 wurde der Test vorgeschlagen, am 2030-05-02 angenommen und am 2030-05-03 ausgesetzt. Er wurde nicht wiederaufgenommen."
        }
      ]
    }
  ]
}
```

<a id="payload-control-lifecycle-de-mutated"></a>
### control.lifecycle_de.mutated

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "The test is now active again.",
      "evidence": [
        {
          "source_revision_id": "133d0391-44d2-5960-98a7-a8abd28b3ff6",
          "start": 10,
          "end": 142,
          "quote": "Am 2030-05-01 wurde der Test vorgeschlagen, am 2030-05-02 angenommen und am 2030-05-03 ausgesetzt. Er wurde nicht wiederaufgenommen."
        }
      ]
    }
  ]
}
```

<a id="payload-control-future-intent-en-good"></a>
### control.future_intent_en.good

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "A future ride is intended, conditional on dry weather, and has not happened.",
      "evidence": [
        {
          "source_revision_id": "fad3d229-eff0-5bd0-a97b-756c5351c1e9",
          "start": 10,
          "end": 84,
          "quote": "I intend to cycle next Friday if it is dry. I have not done that ride yet."
        }
      ]
    }
  ]
}
```

<a id="payload-control-future-intent-en-mutated"></a>
### control.future_intent_en.mutated

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "The ride was completed.",
      "evidence": [
        {
          "source_revision_id": "fad3d229-eff0-5bd0-a97b-756c5351c1e9",
          "start": 10,
          "end": 84,
          "quote": "I intend to cycle next Friday if it is dry. I have not done that ride yet."
        }
      ]
    }
  ]
}
```

<a id="payload-control-past-completed-it-good"></a>
### control.past_completed_it.good

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "La visita è già avvenuta.",
      "evidence": [
        {
          "source_revision_id": "55d5dc90-6939-592d-af04-dd2aeb53c3ce",
          "start": 10,
          "end": 74,
          "quote": "La visita è avvenuta ieri. Non è una semplice intenzione futura."
        }
      ]
    }
  ]
}
```

<a id="payload-control-past-completed-it-mutated"></a>
### control.past_completed_it.mutated

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "La visita è soltanto un’intenzione futura.",
      "evidence": [
        {
          "source_revision_id": "55d5dc90-6939-592d-af04-dd2aeb53c3ce",
          "start": 10,
          "end": 74,
          "quote": "La visita è avvenuta ieri. Non è una semplice intenzione futura."
        }
      ]
    }
  ]
}
```

<a id="payload-control-uncertain-fr-good"></a>
### control.uncertain_fr.good

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "Sam may attend; attendance is unconfirmed.",
      "evidence": [
        {
          "source_revision_id": "3b209587-d463-5f03-90c5-25374ecd5ca6",
          "start": 10,
          "end": 73,
          "quote": "Peut-être que Sam participera; sa présence n’est pas confirmée."
        }
      ]
    }
  ]
}
```

<a id="payload-control-uncertain-fr-mutated"></a>
### control.uncertain_fr.mutated

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "Sam has confirmed attendance.",
      "evidence": [
        {
          "source_revision_id": "3b209587-d463-5f03-90c5-25374ecd5ca6",
          "start": 10,
          "end": 73,
          "quote": "Peut-être que Sam participera; sa présence n’est pas confirmée."
        }
      ]
    }
  ]
}
```

<a id="payload-control-provenance-unicode-good"></a>
### control.provenance_unicode.good

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "The café reopening is announced, not completed.",
      "evidence": [
        {
          "source_revision_id": "b884e38c-0852-505e-8257-036b7a99f56a",
          "start": 10,
          "end": 87,
          "quote": "The café reopening was announced, not completed: é, é and 🙂 remain distinct."
        }
      ]
    }
  ]
}
```

<a id="payload-control-provenance-unicode-mutated"></a>
### control.provenance_unicode.mutated

```json
{
  "items": [
    {
      "local_id": "claim",
      "shape": "item",
      "text": "The café reopening is announced, not completed.",
      "evidence": [
        {
          "source_revision_id": "b884e38c-0852-505e-8257-036b7a99f56a",
          "start": 10,
          "end": 87,
          "quote": "Invented support never spoken."
        }
      ]
    }
  ]
}
```

## Osservazioni trasversali dal payload completo

- `multilingual relation-3`: il testo condizionale è sostenuto, ma il predicato `implies_discount_target` collega la soglia di prezzo all’elemento su incarico/data ignoti; utilità dubbia già motivata in `multilingual.order_possible`, senza inventare una nuova unità obbligatoria.
- `personal-3`: `fact_from` non prova che la passeggiata sia avvenuta. Il testo e il descrittore planned conservano l’intenzione. Il problema è l’uso strutturato del tempo, non un’affermazione esplicita di evento compiuto.
- `work-4`: il budget nelle proprietà non ripete massimo, ma il testo lo mantiene; non inferire che il modello abbia dichiarato una spesa già sostenuta.
- Nei controlli `.good`, conservare ordine o passato non significa conservare tutta la precisione temporale della fonte. Al contrario, parole neutre o dettagli decorativi Unicode non devono diventare nuovi obblighi di copertura.
- Il riesame non stima precisione esaustiva di ogni sotto-clausola generata, né accordo fra revisori indipendenti. Le dimensioni sono per unità: più righe possono riferirsi allo stesso candidato, e i gruppi non vanno sommati in un indice generale.
- Fonti e timeline sono sintetiche: le date narrative dichiarate non sono prove di eventi reali; non si deduce il tempo del fatto dal tempo di acquisizione.

Tutte le decisioni del proprietario restano **pending**. La tabella permette una lettura completa; non sostituisce l’attestazione personale richiesta dal protocollo.
