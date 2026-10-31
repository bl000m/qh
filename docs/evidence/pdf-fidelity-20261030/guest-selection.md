# Correttivo della selezione guest

Base `44a9dd0`, branch `feat/QH-18-21-22-demo-b`, PR #29 draft, senza merge.
Il corpus resta quello di [corpus.json](corpus.json): nessuna nuova estrazione o
rigenerazione PDF, modifica di RH propre/RH 2, snapshot reali o Compréhension canonica.

## Causa e intervento

La risposta precedente poteva usare soltanto alias autorizzati e tuttavia ignorare
un incarico pertinente, confondere soggetti o associare una domanda contrattuale a
un altro argomento. Un contratto con citazioni valide non garantiva la selezione.
Le prime prove con selezione e testo pubblico nella stessa generazione hanno ancora
prodotto gruppi arbitrari, formazione inclusa fra gli incarichi e date non valide.
La sola aggiunta di istruzioni non ha superato il benchmark.

Il percorso finale usa due compiti piccoli attraverso gli stessi servizi/provider:

1. Selezione senza prosa pubblica: una valutazione di tipo e condizioni per **ogni**
   item autorizzato. Il server richiede esattamente tutti gli alias correnti e
   booleani validi; riferimenti esterni o campi fuori contratto sono rifiutati.
2. Il server ricava i criteri temporali espliciti dalla domanda e considera le sole
   date letterali del testo/quotazioni già autorizzati. Non chiede al modello date
   inventate, raggruppamenti per raggiungere un numero o un ordinamento degli item.
   Confronta intervalli alla precisione disponibile; se si sovrappongono o mancano,
   dichiara il limite. Non cambia date, fatti o relazioni canoniche.
3. Composizione sul solo sottoinsieme scelto, senza résumé generale o altri item.
   Le sezioni obbligatorie e i relativi supporti sono assegnati dal server: niente
   omissione di sezioni, nuove citazioni o riordinamento dei riferimenti da parte
   del modello. Il renderer conserva l'ordine nei follow-up.

Non ci sono regole per nomi, CV, freelance o contratti. Il riconoscimento temporale
è sintattico e generale: ISO, mesi italiani/francesi/inglesi e anni con contesto
temporale o intervalli. Numeri di versione e importi non diventano date. Non aggiunge
un RAG, un motore UUM, un accesso PDF o una persistenza della conversazione.

I controlli di accesso e di uguaglianza dello snapshot si ripetono prima/dopo ogni
fase. Il secondo HTTP non parte dopo revoca, variazione dello snapshot o budget
insufficiente. Una risposta positiva normale impiega due chiamate; un ordinale già
risolto una; nessun elemento pertinente o un ordine non fondato fermano il percorso
dopo la selezione. Empty/social conservano i percorsi esistenti senza inferenza.
Non è introdotto alcun retry automatico. Costi e token delle fasi si sommano nella
risposta; il ledger conserva separatamente i singoli tentativi.

## Risultati sul riferimento

| Controllo | Risultato verificato | Evidenza e limite della verifica |
|---|---|---|
| D1, entrambi i PDF | Orbite, poi freelance Nova; periodi e attività corretti | **PASS**. Replay del selettore reale riuscito con uguaglianza di prompt, schema e payload finale; applicazione del nuovo ordinamento server e replay della composizione reale sullo stesso sottoinsieme. |
| D1, solo CV | Stesse due esperienze, nessuna attività scambiata per incarico | **PASS replay**. Le valutazioni di pertinenza reali già corrette sono rieseguite nel nuovo contratto; gruppi/conteggi errati del prototipo non sono più parte del protocollo. Input di composizione identico a D1 completo, verificato per uguaglianza. Nessun nuovo HTTP addebitato per il replay. |
| D2, collegamenti | Amarante ↔ CRM/Sendinblue/SQL; Orbite ↔ Atlas/Matomo/Prometheus; freelance Nova ↔ Lumen/Rails/PostgreSQL | **PASS reale**, due chiamate sul percorso finale. |
| D3, entrambi | Helios, ruolo proposto, 1 marzo 2027, CDI senza fine fissata, 54.000 lordi annui, 35 ore, 2 giorni di telelavoro, Neptune900 su giustificativi, non firmato/non efficace | **PASS reale + replay**. Classificazione reale acquisita, decoder finale e composizione reale riutilizzata: identico input selezionato e citazioni approvate. |
| D3, solo CV | Nessun dato contrattuale, nessun richiamo a Rust o a un datore presunto; limite esplicito | **PASS replay** della classificazione reale negativa. Il server non avvia composizione e produce la risposta di contesto insufficiente senza citazioni. |
| Decisioni di progetto | Lumen adottata il 15 aprile 2026, poi Atlas adottata il 10 febbraio 2026 | **PASS reale**, due chiamate sul percorso finale. Escluse Neptune solo proposta, Iris più vecchia e l'attività di esecuzione del 10 giugno. |

Il caso di progetto aggiunge soltanto cinque dichiarazioni sintetiche nel payload,
con date e stati espliciti, senza un terzo PDF o un nuovo Context Space. La logica
di selezione, ordinamento e composizione è la stessa del caso professionale.

I replay sono eseguiti senza rete e non sono reinviati al modello come conoscenza
o cronologia. Il controllo di identità riguarda anche l'input dei compositori
riutilizzati; non sono presentate come nuove chiamate reali verifiche già pagate.
Non è una nuova verifica browser/OIDC o una nuova consolidazione produttiva PDF.

## Verifiche e contabilità

- **94 test mirati offline passati**, inclusi source confidentiality, document
  permissions, alias non autorizzati, revoca/scadenza e snapshot cambiato fra fasi,
  riferimenti ordinali, date mancanti/sovrapposte, precisione e prove letterali,
  sezioni mancanti/estranee, limite di memoria e mancanza del secondo candidato.
- La simulazione HTTP verifica il costo aggregato, nessuna quota artificiale di
  sessione e il blocco della composizione se il budget si esaurisce dopo selezione.
  Non sono chiamate reali nei test/CI.
- Ruff mirato e controllo whitespace: PASS. Nessuna Full Verification, migrazione,
  nuova dipendenza, browser campaign o modifica dei dati reali.
- **18 chiamate HTTP Mistral Small reali complessive**: 3 iniziali e tutte le 15
  aggiuntive esplicitamente autorizzate. Tutte HTTP 200 e contabilizzate come
  completed; le prove intermedie rifiutate dalla validazione sono incluse.
- Costo osservato: **0,00708615 USD** = 0,00205440 iniziali + 0,00503175 aggiuntivi.
  Nessuna chiamata extra per i replay. Ledger finale non bloccato, zero pending,
  nessun reset o aumento dei limiti. La riserva fallita precedente di
  **0,1572864 USD** rimane conservata nello storico, distinta da questi consumi.

## Limiti residui

L'intervento corregge recupero/selezione dei fatti già comunicabili; non sana gli
Understanding Items incompleti. Restano fuori scope le omissioni nel testo UUM e
lo stato formativo errato documentati nel benchmark iniziale. Le citazioni possono
essere usate solo se già approvate nel payload; nessuna lettura PDF le sostituisce.

Il riconoscimento di criteri e date è conservativo: periodi sovrapposti, formati non
riconosciuti o identità non ricostruibili non vengono risolti per supposizione.
La pertinenza semantica resta valutata dal modello, non certificata formalmente.
Una risposta D2 reale usa la prima persona: i legami e i fatti sono corretti, ma la
voce narrativa non è normalizzata da questo intervento.


## Follow-up dei FAIL manuali — 2026-10-31

La verifica sintetica precedente non dimostra la completezza del corpus reale.
Diagnosi successiva, senza HTTP Mistral o scritture canoniche:

- Il ramo cronologico di `context_clarification()` precedeva il selettore e cercava
  anni soltanto in `item.text`. Poteva negare periodi già presenti nelle citazioni
  approvate. Rimosso quel ramo duplicato: selezione e controllo temporale esistenti
  valutano testo e citazioni attualmente autorizzati. I periodi mancanti non sono
  inventati e le attività non diventano incarichi tramite questa modifica.
- Il riconoscimento degli ordinali richiedeva l'intero messaggio: la richiesta
  composta « Peux-tu détailler la deuxième ? Puis : Et la première ? » passava
  invece al selettore come nuova domanda. Ora richiede una precisazione senza HTTP.
  Inoltre la ricerca di una lista precedente saltava le risposte vuote/non-lista,
  e i ritorni locali non registravano l'interruzione. Ora una risposta senza lista
  interrompe quel riferimento; solo un elenco strutturato avvia la continuità e un
  dettaglio ordinale risolto conserva l'ordine originario.
- Il percorso recap è stato tracciato: `document_scope` → Guard →
  `projected_components`/`projected_recap` → `accessible_introduction`. Se il Guard
  ammette il generale, quest'ultimo viene conservato e prevale sul fallback di un
  singolo documento. Un test mirato verifica questa proprietà e l'esclusione del
  generale nel perimetro parziale. Nessuna modifica alla selezione dei recap è
  giustificata dai soli screenshot; non vengono assemblati estratti.

**Limite della diagnosi reale:** la lettura SQL in transazione read-only non trova
un Context Space chiamato « RH propre » nel database attivo. È stata richiesta
conferma dell'eventuale rinomina in « RH nuovo »; non sono stati assunti equivalenti
né esaminati al suo posto altri Space. Non è quindi verificata qui la cronologia
presente nel suo snapshot, né la causa specifica delle due preview identiche.
Il terzo FAIL e l'accettazione sul corpus reale rimangono aperti fino
all'identificazione del contesto. Nessuna modifica di RH, RH 2 o snapshot approvati.

Verifiche del correttivo: **108 test offline mirati PASS**, Ruff e controllo segreti
dell'indice PASS. Nessuna Full Verification, chiamata Mistral o nuova lettura PDF.
I test esercitano citazioni come unica evidenza temporale, assenza effettiva di date,
ordinali composti in tre lingue, interruzione della lista e conservazione dei dettagli
« deuxième » → « première », oltre a revoca/scadenza e isolamento esistenti.
