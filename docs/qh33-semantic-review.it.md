# QH-33 — guida alla revisione semantica

**D1–D5 ora approvate; verifica personale non attestata.** Questa guida conserva
gli esempi precedenti. Per la review corrente usa la [matrice v2](evidence/qh33-v2-20261016/review-matrix.it.md)
e il [pacchetto con rubriche e istruzioni](evidence/qh33-v2-20261016/README.md).

Aggiornamento: il proprietario ha definito il criterio di **comprensione evolutiva**.
La scelta generale “storia completa o stato finale?” sotto non è più aperta;
consulta la [sintesi decisionale aggiornata](qh33-owner-decisions.it.md) e il
[riesame di tutte le 74 unità](reviews/qh33-unit-review-20261016.it.md). Restano
da validare i giudizi concreti; fonti e JSON di questa guida sono invariati.

16 ottobre 2026 · [PR #8](https://github.com/bl000m/qh/pull/8), aperta.
**Review indipendente da svolgere.** Questa guida è preparata con assistenza IA:
“significato da preservare” è una lettura da verificare, non una risposta validata.
I punteggi precedenti non sono usati come prova. Nessuna annotazione è modificata.

Leggi prima le [fonti senza annotazioni](evidence/qh33-semantic-20261016/source-only.md).
I JSON sotto riportano campi originali, omettendo gli altri per leggibilità
(`true` = sì, `false` = no). Le spiegazioni italiane sono mie. Gli impatti sono **potenziali**, non osservati
sui dati persistenti. Gli elementi accettati nei test restano `proposed`
(proposte da rivedere, non conoscenze confermate).
`multilingual` è bloccato interamente per citazioni mancanti; gli altri tre batch
superano il controllo tecnico dopo il resolver, che non certifica il significato.

| Distinzione da valutare | Domanda semplice |
| --- | --- |
| Omissione | Un’informazione esplicita è sparita dall’elemento estratto? |
| Inferenza non autorizzata | L’output aggiunge una conclusione che la fonte non sostiene? |
| Perdita di incertezza | Un “se”, “forse” o “non ancora” diventa un fatto acquisito? |
| Attribuzione | Chi parla viene confuso con chi decide? |
| Temporalità | Si distinguono proposta, adozione, sospensione, passato e futuro? |
| Relazione poco utile | Il collegamento permette di capire chi fa cosa, oppure collega oggetti diversi da quelli descritti? |

## 1. Multilingual: sconto ipotetico e decisione non presa

**Originale.**

> Alex: Se lo sconto ci porta a 350 EUR tutto incluso, potremmo ordinare. Non è una decisione presa.

**Significato da preservare.** Raggiungere 350 EUR è una condizione possibile;
non è detto che lo sconto sia stato applicato né che l’ordine sia stato deciso.

**Mistral, `item-5`.**

```json
{
  "local_id": "item-5",
  "text": "Se lo sconto ci porta a 350 EUR tutto incluso",
  "properties": {"currency": "EUR", "discount_applied": true, "tax_included": true, "value": 350}
}
```

**Differenza / impatto — incertezza e inferenza aggiunta.** Il testo conserva
“Se”, ma `discount_applied: true` dice “sconto applicato”: leggere solo le proprietà
potrebbe far apparire ottenuto un prezzo ipotetico. “Non è una decisione presa”
rimane soltanto nella citazione. **Da verificare:** coerenza fra testo e proprietà,
e necessità di estrarre esplicitamente la mancata decisione.

## 2. Multilingual: mancata approvazione dell’ordine omessa

**Originale.**

> Camille: Donc le devis dépasse le plafond de 10 EUR. Aucune commande n’est approuvée pour le moment.

**Significato da preservare.** Il preventivo supera il tetto di 10 EUR **e nessun
ordine è approvato al momento**.

**Mistral, `item-4`.**

```json
{
  "local_id": "item-4",
  "text": "le devis dépasse le plafond de 10 EUR",
  "properties": {"currency": "EUR", "excess": 10, "tax_included": true}
}
```

**Differenza / impatto — omissione.** Nell’output completo manca l’affermazione
“ordine non approvato”, presente solo nella citazione. QH potrebbe ricordare il costo
ma non quel vincolo; ciò non autorizza a dedurre “approvato”. **Da verificare:**
questa negazione è indispensabile nel benchmark?

## 3. Evolving: decisione adottata o controproposta?

**Originale.**

> Jo: Il 2026-11-03T10:00:00Z scegliamo invece una prova di briefing giornalieri di dieci minuti, per una settimana.

**Significato da preservare.** Il gruppo sceglie una prova giornaliera di una
settimana, distinguendola dalla proposta settimanale precedente.

**Mistral, `evolving-2`.**

```json
{
  "local_id": "evolving-2",
  "text": "Il 2026-11-03T10:00:00Z scegliamo invece una prova di briefing giornalieri di dieci minuti, per una settimana.",
  "descriptors": [{"value": "counter-proposal", "certainty": "asserted"}]
}
```

**Differenza / impatto — classificazione discutibile.** “Scegliamo” resta nel
testo. “Controproposta” può descrivere l’alternativa oppure farla sembrare ancora
da adottare; una ricerca per etichette potrebbe non trovare la decisione.
**Da verificare:** etichetta fuorviante, incompleta o accettabile? Il vocabolario è
aperto: una parola diversa, da sola, non prova un errore.

## 4. Evolving: chi decide, e chi sta riferendo?

**Originali.**

> Jo: Il 2026-11-03T10:00:00Z scegliamo invece una prova di briefing giornalieri di dieci minuti, per una settimana.

> Jo: Il 2026-11-04T08:00:00Z sospendiamo anche la prova giornaliera: due partecipanti sono assenti.

**Significato da preservare.** Jo riferisce azioni al plurale: “scegliamo” e
“sospendiamo”. La fonte non dice che Jo abbia personalmente respinto Mina.

**Mistral, relazioni effettive.**

```json
{
  "local_id": "relation-1",
  "text": "Jo rejects Mina's proposal",
  "relation": {"source": "evolving-2", "target": "proposal-1", "predicate": "rejects"}
}
```

```json
{
  "local_id": "relation-3",
  "text": "Jo suspends proposal-2",
  "relation": {"source": "evolving-4", "target": "proposal-2", "predicate": "suspends"}
}
```

**Differenza / impatto — attribuzione e inferenza.** “Jo rejects” aggiunge un
rifiuto personale alla scelta collettiva; potrebbe attribuirgli un conflitto non
espresso. “Jo suspends” perde il plurale, ma non dice “Jo da solo”. **Da verificare:**
distinguere il rifiuto aggiunto dalla sintesi collettiva eventualmente incompleta.

## 5. Evolving: date presenti, collegamento agli eventi debole

**Originali, nella loro sequenza.**

> Mina: Il 2026-11-02T09:00:00Z propongo riunioni settimanali di un’ora. È solo una proposta.

> Jo: Il 2026-11-03T10:00:00Z scegliamo invece una prova di briefing giornalieri di dieci minuti, per una settimana.

> Jo: Il 2026-11-04T08:00:00Z sospendiamo anche la prova giornaliera: due partecipanti sono assenti.

> Mina: La situazione attuale è prova sospesa, non ritorno alle riunioni settimanali. Quando riprenderemo resta da decidere.

**Significato da preservare.** 2 novembre: proposta; 3 novembre: scelta della
prova; 4 novembre: sospensione. Stato finale: prova sospesa, nessun ritorno alle
riunioni settimanali e ripresa ancora da decidere.

**Mistral, esempio `temporal-2`.**

```json
{
  "local_id": "temporal-2",
  "shape": "entity",
  "text": "2026-11-03T10:00:00Z",
  "temporal": {"fact_from": "2026-11-03T10:00:00Z"}
}
```

**Differenza / impatto — temporalità.** Le tre date sono autentiche, ma i campi
temporali appartengono a elementi che rappresentano solo date, senza collegamenti
agli eventi. Questi mantengono le date nel testo; `evolving-5` conserva sospensione e ripresa incerta.
Una domanda strutturata “quando fu scelta la prova?” richiederebbe di reinterpretare
la prosa. **Da verificare:** per il benchmark basta il testo o serve il collegamento
strutturato? Il controllo sugli offset non risolve questa domanda.

## 6. Work: relazione formalmente valida, ma utile?

**Originale.**

> Eli: Decidiamo un pilota di due settimane con il team Aster. Il team Aster gestirà il pannello delle assegnazioni.

**Significato da preservare.** È deciso un pilota; il team Aster gestirà il
pannello delle assegnazioni.

**Mistral, `relation-1`.**

```json
{
  "local_id": "relation-1",
  "text": "Il team Aster gestirà il pannello delle assegnazioni.",
  "relation": {"source": "work-2", "target": "work-1", "predicate": "gestisce_pannello_per"}
}
```

**Differenza / impatto — relazione poco utile?** Gli estremi sono l’enunciato
sul pilota (`work-2`) e l’obiettivo del 20% (`work-1`), non team e pannello.
Una navigazione “team → pannello” potrebbe risentirne. Collegare enunciati è però
consentito: non rende falsa la frase. **Da verificare:** a quale domanda serve
questa relazione?

## 7. Personal e Work: controlli di fedeltà, non errori presunti

### Personal: intenzione futura e presenza non confermata

**Originali.**

> Robin: Ho intenzione di fare una passeggiata il 2026-10-17T09:00:00Z. Non l’ho ancora fatta e potrei rinunciare se piove.

> Casey: Forse verrò alla passeggiata, ma non ho confermato la mia presenza.

**Significato da preservare.** La passeggiata è un’intenzione condizionata alla
pioggia, non un evento compiuto; Casey potrebbe partecipare, senza conferma.

**Mistral.**

```json
{
  "local_id": "personal-3",
  "text": "Ho intenzione di fare una passeggiata il 2026-10-17T09:00:00Z. Non l’ho ancora fatta e potrei rinunciare se piove.",
  "temporal": {"fact_from": "2026-10-17T09:00:00Z"}
}
```

```json
{
  "local_id": "personal-4",
  "text": "Forse verrò alla passeggiata, ma non ho confermato la mia presenza.",
  "descriptors": [{"value": "uncertain attendance to walk", "certainty": "asserted"}]
}
```

**Confronto — controllo positivo con cautela temporale.** Il testo conserva
“non ancora”, meteo e presenza incerta. La data in `fact_from` è prevista, non prova
di un evento compiuto. `asserted` riguarda l’etichetta “presenza incerta”, non la
conferma di Casey. **Impatto potenziale:** confondere piano e fatto leggendo solo
la data. Distinguere questo rischio da un errore effettivo dell’estrazione.

### Work: ipotesi esplicitamente non misurata

**Originale.**

> Nora: Ipotizzo che un pannello condiviso riduca i passaggi duplicati; non abbiamo ancora misurazioni.

**Significato da preservare.** Il beneficio del pannello è un’ipotesi, senza
misurazioni che lo dimostrino.

**Mistral.**

```json
{
  "local_id": "work-3",
  "text": "Ipotizzo che un pannello condiviso riduca i passaggi duplicati; non abbiamo ancora misurazioni.",
  "descriptors": [{"value": "ipotesi su pannello condiviso", "certainty": "asserted"}]
}
```

**Confronto:** ipotesi e mancanza di misure sono conservate. `asserted` non ne fa
un risultato misurato. **Da verificare:** controllo positivo, senza penalizzare
l’etichetta in sé.

## 8. Multilingual: dubbi iniziali e provenienza delle relazioni

### Omissioni storiche da discutere, non errori già decisi

**Originali.**

> Camille: Le devis est de 300 EUR hors taxes. Je ne sais pas encore si notre plafond inclut la TVA.

> Alex: Il nostro tetto è 350 EUR IVA inclusa. Forse il preventivo rientra, ma dobbiamo verificarlo.

**Significato da preservare se interessa la storia del ragionamento.** All’inizio
Camille non sa se il tetto includa l’IVA; Alex ipotizza che il preventivo rientri,
ma chiede verifica. Drew chiarisce poi che il totale è 360 EUR IVA inclusa.

**Mistral.**

```json
{
  "local_id": "item-1",
  "text": "Le devis est de 300 EUR hors taxes.",
  "properties": {"currency": "EUR", "tax_included": false, "value": 300}
}
```

```json
{
  "local_id": "item-2",
  "text": "Il nostro tetto è 350 EUR IVA inclusa.",
  "properties": {"currency": "EUR", "tax_included": true, "value": 350}
}
```

**Differenza / impatto — omissione discutibile.** Restano gli importi, non i
dubbi iniziali: si perde parte dell’evoluzione della comprensione. Per un riepilogo
finale potrebbe essere ragionevole. **D1 approvata:** questi due dubbi risolti non restano nel coverage attivo,
ma devono essere ricostruibili; non si eliminano le evoluzioni significative.

### Relazioni prive di citazione propria

**Originale.**

> Drew: The final total is 360 EUR including tax. That resolves the apparent 300 versus 360 discrepancy; they use different tax bases.

**Significato da preservare.** 300 EUR senza IVA e 360 EUR con IVA usano basi
diverse; non sono necessariamente due preventivi in contraddizione.

**Mistral, `relation-2` completa.**

```json
{
  "local_id": "relation-2",
  "relation": {
    "predicate": "resolves_discrepancy_with",
    "source": "item-3",
    "target": "item-1"
  },
  "shape": "relation",
  "text": "That resolves the apparent 300 versus 360 discrepancy; they use different tax bases."
}
```

**Differenza / impatto — provenienza.** Il senso è plausibile, ma manca
`evidence`, la citazione propria della relazione, come nelle altre due relazioni
del batch. Le citazioni degli elementi collegati non bastano: il batch è respinto
interamente. **Da verificare:** plausibilità del significato e supporto tracciabile
vanno giudicati separatamente.

## 9. Controlli sintetici: cosa dovrebbe distinguere il benchmark

**Questi JSON non provengono da Mistral:** sono coppie scritte per il test.
“Coerente/alterato” indica l’intenzione dell’autore, ancora da verificare.
Nel benchmark i nomi hanno prefisso `control.` e varianti `.good`/`.mutated`.

| Controllo e frase originale | Significato da verificare / impatto dell’alterazione | JSON coerente / alterato, scritto per il test |
| --- | --- | --- |
| `conditional_es` — Si se concede el permiso, el envío podría salir; todavía no se ha concedido. | Il permesso non è concesso; la partenza è solo possibile. L’alterazione inventa sia il permesso sia la spedizione compiuta. | Coerente: `{"text":"El envío solo podría salir si se concede el permiso."}`<br>Alterato: `{"text":"El permiso se ha concedido y el envío salió."}` |
| `negation_en` — No booking was approved; approval is still pending. | Nessuna prenotazione approvata; attesa di approvazione. L’alterazione capovolge la negazione. | Coerente: `{"text":"No booking has been approved."}`<br>Alterato: `{"text":"The booking has been approved."}` |
| `actual_discount_fr` — La remise de 8 % a été appliquée. Le montant payé est 92 EUR. | Sconto realmente applicato e 92 EUR pagati. Deve poter essere rappresentato: vietare sempre `discount_applied=true` sarebbe sbagliato. | Coerente: `{"text":"A discount of 8% was applied; EUR 92 was paid.","properties":{"discount_applied":true}}`<br>Alterato: `{"text":"No discount was applied.","properties":{"discount_applied":false}}` |
| `collective_it` — Le tre delegate hanno votato insieme la pausa. Uma riferisce il risultato. | Decidono insieme le tre delegate; Uma riferisce. L’alterazione inventa una decisione individuale esclusiva. | Coerente: `{"text":"Le tre delegate hanno deciso insieme la pausa."}`<br>Alterato: `{"text":"Uma ha deciso da sola la pausa."}` |
| `individual_en` — I, Ren, authorized the release; the committee did not vote. | Ren autorizza; il comitato non vota. Non bisogna correggere automaticamente ogni decisione individuale in collettiva. | Coerente: `{"text":"Ren authorized the release; no committee vote occurred."}`<br>Alterato: `{"text":"The committee authorized the release."}` |
| `lifecycle_de` — Am 2030-05-01 wurde der Test vorgeschlagen, am 2030-05-02 angenommen und am 2030-05-03 ausgesetzt. Er wurde nicht wiederaufgenommen. | Test proposto il 1° maggio, adottato il 2, sospeso il 3, mai ripreso. L’alterazione inventa una riattivazione e perde la sequenza. | Coerente: `{"text":"The test was proposed, then adopted, then suspended; it has not resumed."}`<br>Alterato: `{"text":"The test is now active again."}` |
| `future_intent_en` — I intend to cycle next Friday if it is dry. I have not done that ride yet. | Uscita futura condizionata al tempo asciutto, non ancora compiuta. L’alterazione registra come avvenuto un piano. | Coerente: `{"text":"A future ride is intended, conditional on dry weather, and has not happened."}`<br>Alterato: `{"text":"The ride was completed."}` |
| `past_completed_it` — La visita è avvenuta ieri. Non è una semplice intenzione futura. | Visita già avvenuta ieri. L’alterazione trasforma un evento passato in una semplice intenzione. | Coerente: `{"text":"La visita è già avvenuta."}`<br>Alterato: `{"text":"La visita è soltanto un’intenzione futura."}` |
| `uncertain_fr` — Peut-être que Sam participera; sa présence n’est pas confirmée. | Sam forse parteciperà, senza conferma. L’alterazione presenta la presenza come confermata. | Coerente: `{"text":"Sam may attend; attendance is unconfirmed."}`<br>Alterato: `{"text":"Sam has confirmed attendance."}` |
| `provenance_unicode` — The café reopening was announced, not completed: é, é and 🙂 remain distinct. | Riapertura annunciata, non completata. Il contenuto resta identico, ma la citazione alterata è inventata: errore di provenienza, non di significato del testo. | Coerente: `{"evidence":[{"quote":"The café reopening was announced, not completed: é, é and 🙂 remain distinct."}]}`<br>Alterato: `{"evidence":[{"quote":"Invented support never spoken."}]}` |

Nel replay, i nove candidati con significato alterato passano i controlli
strutturali come `proposed`; quello con citazione inventata è respinto. QH non ha
riconosciuto automaticamente i nove errori. Questi pochi controlli, scritti durante
lo sviluppo, non dimostrano affidabilità su conversazioni nuove. Nel caso Unicode
non va normalizzata la citazione per farla corrispondere.

## 10. Decisione del revisore: cosa manca prima dell’esperimento

Rispondi **condivido / da correggere / non determinabile**, con una motivazione.
Nessuna risposta è già approvata. Controlla anche gli
[output completi](evidence/qh33-semantic-20261016/review-packet.md): questa selezione
potrebbe non coprire tutte le omissioni o aggiunte.

| Scelta | Risposta del proprietario |
| --- | --- |
| Le letture delle quattro conversazioni rispettano le fonti, comprese le ambiguità segnalate? | Da compilare |
| Applicare D1 alle due incertezze storiche, conservando fonti ed evoluzioni significative? | Criterio approvato; unità da verificare personalmente |
| Le omissioni, le attribuzioni e le etichette contestabili sono distinte dagli errori espliciti? | Da compilare |
| I dieci controlli hanno davvero significato coerente/alterato come proposto? Ne mancano di importanti? | Da compilare |
| Vanno aggiunte, separate o riformulate proposizioni prima di usare le metriche? | Da compilare |
| Il riferimento è sufficientemente affidabile per proporre il confronto controllato dei prompt? | Da compilare |

La [griglia](evidence/qh33-semantic-20261016/review-template.json) resta vuota:
74 unità in attesa. Correzioni al benchmark richiedono una revisione esplicita.
L’eventuale approvazione del riferimento non autorizza le inferenze: il
[protocollo e budget](qh33-semantic-evaluation.md) richiedono consenso separato.
Nessun merge, aggiornamento Jira o nuova chiamata LLM.

### Riscontro e limiti di questa consegna

PASS: copertura di tutte e quattro le conversazioni e dieci coppie di controlli;
citazioni e frammenti JSON riscontrati nei file originali; archivi e annotazioni
immutati. La revisione di fedeltà da parte del proprietario è **NOT TESTED / in attesa**.
Questo è materiale di supporto, non una nuova misura di precisione o un consenso.

Fonti: per ogni conversazione, i file originali [work](evidence/qh8-mistral-20261016/work/output.json),
[evolving](evidence/qh8-mistral-20261016/evolving/output.json),
[personal](evidence/qh8-mistral-20261016/personal/output.json),
[multilingual](evidence/qh8-mistral-20261016/multilingual/output.json) e i rispettivi
`source.json` nelle stesse directory. I controlli sono nel
[benchmark](../apps/api/tests/fixtures/qh33/benchmark.json), senza usare i suoi
`draft_ratings` come risposte validate. Il documento contiene una selezione di campi;
non altera alcun file di evidenza.
