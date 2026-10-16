# V2 — fonti originali e payload completi

14 fonti distinte, 4 output Mistral originali e 20 controlli scritti. Nessuna correzione ai payload. Fonte condivisa fra good/mutated leggibile una sola volta.

<a id="source-work"></a>
## Fonte work

```text
Nora: L’obiettivo del progetto Faro è ridurre del 20% il tempo tra richiesta e assegnazione, senza cambiare il CRM.
Eli: Decidiamo un pilota di due settimane con il team Aster. Il team Aster gestirà il pannello delle assegnazioni.
Nora: Ipotizzo che un pannello condiviso riduca i passaggi duplicati; non abbiamo ancora misurazioni.
Eli: Vincoli: budget massimo 300 EUR e nessuna esportazione di dati dal CRM. La scadenza è il 2026-11-20.
Nora: Resta aperto chi autorizzerà l’accesso al pannello. Non abbiamo ancora scelto un responsabile sicurezza.
```

<a id="source-evolving"></a>
## Fonte evolving

```text
Mina: Il 2026-11-02T09:00:00Z propongo riunioni settimanali di un’ora. È solo una proposta.
Jo: Il 2026-11-03T10:00:00Z scegliamo invece una prova di briefing giornalieri di dieci minuti, per una settimana.
Mina: Ritiro la proposta delle riunioni settimanali. Non è mai stata adottata.
Jo: Il 2026-11-04T08:00:00Z sospendiamo anche la prova giornaliera: due partecipanti sono assenti.
Mina: La situazione attuale è prova sospesa, non ritorno alle riunioni settimanali. Quando riprenderemo resta da decidere.
```

<a id="source-personal"></a>
## Fonte personal

```text
Robin: Preferisco incontrarci in un bar tranquillo; per oggi eviterei i locali affollati, senza dire che li evito sempre.
Casey: Il mio treno è stato cancellato il 2026-10-09T17:30:00Z. Questo è un evento passato, non il viaggio di domani.
Robin: Ho intenzione di fare una passeggiata il 2026-10-17T09:00:00Z. Non l’ho ancora fatta e potrei rinunciare se piove.
Casey: Forse verrò alla passeggiata, ma non ho confermato la mia presenza.
Robin: Vorrei chiedere a Lee se conosce un percorso coperto. La scelta del percorso è ancora aperta.
```

<a id="source-multilingual"></a>
## Fonte multilingual

```text
Camille: Le devis est de 300 EUR hors taxes. Je ne sais pas encore si notre plafond inclut la TVA.
Alex: Il nostro tetto è 350 EUR IVA inclusa. Forse il preventivo rientra, ma dobbiamo verificarlo.
Drew: The final total is 360 EUR including tax. That resolves the apparent 300 versus 360 discrepancy; they use different tax bases.
Camille: Donc le devis dépasse le plafond de 10 EUR. Aucune commande n’est approuvée pour le moment.
Alex: Se lo sconto ci porta a 350 EUR tutto incluso, potremmo ordinare. Non è una decisione presa.
Drew: Who will ask for the discount? We have not assigned that task. The delivery date is still unknown.
```

<a id="source-control-conditional-es-good"></a>
## Fonte control.conditional_es.good

```text
Reporter: Si se concede el permiso, el envío podría salir; todavía no se ha concedido.
Recorder: No additional event is stated.
Recorder: End of this synthetic record.
```

<a id="source-control-negation-en-good"></a>
## Fonte control.negation_en.good

```text
Reporter: No booking was approved; approval is still pending.
Recorder: No additional event is stated.
Recorder: End of this synthetic record.
```

<a id="source-control-actual-discount-fr-good"></a>
## Fonte control.actual_discount_fr.good

```text
Reporter: La remise de 8 % a été appliquée. Le montant payé est 92 EUR.
Recorder: No additional event is stated.
Recorder: End of this synthetic record.
```

<a id="source-control-collective-it-good"></a>
## Fonte control.collective_it.good

```text
Reporter: Le tre delegate hanno votato insieme la pausa. Uma riferisce il risultato.
Recorder: No additional event is stated.
Recorder: End of this synthetic record.
```

<a id="source-control-individual-en-good"></a>
## Fonte control.individual_en.good

```text
Reporter: I, Ren, authorized the release; the committee did not vote.
Recorder: No additional event is stated.
Recorder: End of this synthetic record.
```

<a id="source-control-lifecycle-de-good"></a>
## Fonte control.lifecycle_de.good

```text
Reporter: Am 2030-05-01 wurde der Test vorgeschlagen, am 2030-05-02 angenommen und am 2030-05-03 ausgesetzt. Er wurde nicht wiederaufgenommen.
Recorder: No additional event is stated.
Recorder: End of this synthetic record.
```

<a id="source-control-future-intent-en-good"></a>
## Fonte control.future_intent_en.good

```text
Reporter: I intend to cycle next Friday if it is dry. I have not done that ride yet.
Recorder: No additional event is stated.
Recorder: End of this synthetic record.
```

<a id="source-control-past-completed-it-good"></a>
## Fonte control.past_completed_it.good

```text
Reporter: La visita è avvenuta ieri. Non è una semplice intenzione futura.
Recorder: No additional event is stated.
Recorder: End of this synthetic record.
```

<a id="source-control-uncertain-fr-good"></a>
## Fonte control.uncertain_fr.good

```text
Reporter: Peut-être que Sam participera; sa présence n’est pas confirmée.
Recorder: No additional event is stated.
Recorder: End of this synthetic record.
```

<a id="source-control-provenance-unicode-good"></a>
## Fonte control.provenance_unicode.good

```text
Reporter: The café reopening was announced, not completed: é, é and 🙂 remain distinct.
Recorder: No additional event is stated.
Recorder: End of this synthetic record.
```

<a id="output-work"></a>
## Output work

Mistral originale congelato.

```json
{
  "items": [
    {
      "local_id": "work-1",
      "shape": "item",
      "text": "L’obiettivo del progetto Faro è ridurre del 20% il tempo tra richiesta e assegnazione, senza cambiare il CRM.",
      "descriptors": [
        {
          "value": "obiettivo del progetto Faro",
          "certainty": "asserted"
        }
      ],
      "evidence": [
        {
          "source_revision_id": "2ec42859-b01c-534c-b7ca-22428aad5895",
          "start": 6,
          "end": 70,
          "quote": "L’obiettivo del progetto Faro è ridurre del 20% il tempo tra richiesta e assegnazione, senza cambiare il CRM."
        }
      ]
    },
    {
      "local_id": "work-2",
      "shape": "item",
      "text": "Decidiamo un pilota di due settimane con il team Aster. Il team Aster gestirà il pannello delle assegnazioni.",
      "descriptors": [
        {
          "value": "decisione pilota",
          "certainty": "asserted"
        }
      ],
      "evidence": [
        {
          "source_revision_id": "2ec42859-b01c-534c-b7ca-22428aad5895",
          "start": 121,
          "end": 195,
          "quote": "Decidiamo un pilota di due settimane con il team Aster. Il team Aster gestirà il pannello delle assegnazioni."
        }
      ]
    },
    {
      "local_id": "work-3",
      "shape": "item",
      "text": "Ipotizzo che un pannello condiviso riduca i passaggi duplicati; non abbiamo ancora misurazioni.",
      "descriptors": [
        {
          "value": "ipotesi su pannello condiviso",
          "certainty": "asserted"
        }
      ],
      "evidence": [
        {
          "source_revision_id": "2ec42859-b01c-534c-b7ca-22428aad5895",
          "start": 237,
          "end": 310,
          "quote": "Ipotizzo che un pannello condiviso riduca i passaggi duplicati; non abbiamo ancora misurazioni."
        }
      ]
    },
    {
      "local_id": "work-4",
      "shape": "item",
      "text": "Vincoli: budget massimo 300 EUR e nessuna esportazione di dati dal CRM. La scadenza è il 2026-11-20.",
      "descriptors": [
        {
          "value": "vincoli del progetto",
          "certainty": "asserted"
        }
      ],
      "properties": {
        "budget": "300 EUR",
        "scadenza": "2026-11-20"
      },
      "evidence": [
        {
          "source_revision_id": "2ec42859-b01c-534c-b7ca-22428aad5895",
          "start": 338,
          "end": 438,
          "quote": "Vincoli: budget massimo 300 EUR e nessuna esportazione di dati dal CRM. La scadenza è il 2026-11-20."
        }
      ]
    },
    {
      "local_id": "work-5",
      "shape": "item",
      "text": "Resta aperto chi autorizzerà l’accesso al pannello. Non abbiamo ancora scelto un responsabile sicurezza.",
      "descriptors": [
        {
          "value": "decisione aperta su accesso al pannello",
          "certainty": "asserted"
        },
        {
          "value": "responsabile sicurezza non scelto",
          "certainty": "asserted"
        }
      ],
      "evidence": [
        {
          "source_revision_id": "2ec42859-b01c-534c-b7ca-22428aad5895",
          "start": 445,
          "end": 549,
          "quote": "Resta aperto chi autorizzerà l’accesso al pannello. Non abbiamo ancora scelto un responsabile sicurezza."
        }
      ]
    },
    {
      "local_id": "relation-1",
      "shape": "relation",
      "text": "Il team Aster gestirà il pannello delle assegnazioni.",
      "relation": {
        "source": "work-2",
        "target": "work-1",
        "predicate": "gestisce_pannello_per"
      },
      "evidence": [
        {
          "source_revision_id": "2ec42859-b01c-534c-b7ca-22428aad5895",
          "start": 121,
          "end": 195,
          "quote": "Decidiamo un pilota di due settimane con il team Aster. Il team Aster gestirà il pannello delle assegnazioni."
        }
      ]
    },
    {
      "local_id": "relation-2",
      "shape": "relation",
      "text": "Un pannello condiviso è ipotizzato per ridurre i passaggi duplicati.",
      "relation": {
        "source": "work-3",
        "target": "work-1",
        "predicate": "ipotizza_misura_per"
      },
      "evidence": [
        {
          "source_revision_id": "2ec42859-b01c-534c-b7ca-22428aad5895",
          "start": 237,
          "end": 310,
          "quote": "Ipotizzo che un pannello condiviso riduca i passaggi duplicati; non abbiamo ancora misurazioni."
        }
      ]
    },
    {
      "local_id": "relation-3",
      "shape": "relation",
      "text": "I vincoli includono budget massimo e scadenza.",
      "relation": {
        "source": "work-4",
        "target": "work-1",
        "predicate": "definisce_vincoli_per"
      },
      "evidence": [
        {
          "source_revision_id": "2ec42859-b01c-534c-b7ca-22428aad5895",
          "start": 338,
          "end": 438,
          "quote": "Vincoli: budget massimo 300 EUR e nessuna esportazione di dati dal CRM. La scadenza è il 2026-11-20."
        }
      ]
    },
    {
      "local_id": "relation-4",
      "shape": "relation",
      "text": "Resta aperta la decisione su chi autorizzerà l’accesso al pannello.",
      "relation": {
        "source": "work-5",
        "target": "work-2",
        "predicate": "decisione_aperta_su"
      },
      "evidence": [
        {
          "source_revision_id": "2ec42859-b01c-534c-b7ca-22428aad5895",
          "start": 445,
          "end": 549,
          "quote": "Resta aperto chi autorizzerà l’accesso al pannello. Non abbiamo ancora scelto un responsabile sicurezza."
        }
      ]
    }
  ]
}
```

<a id="output-evolving"></a>
## Output evolving

Mistral originale congelato.

```json
{
  "items": [
    {
      "local_id": "evolving-1",
      "shape": "item",
      "text": "Il 2026-11-02T09:00:00Z propongo riunioni settimanali di un’ora. È solo una proposta.",
      "descriptors": [
        {
          "value": "proposal",
          "certainty": "asserted"
        }
      ],
      "evidence": [
        {
          "source_revision_id": "3f2a8b04-ebe5-5f75-9173-f4cb4f45172b",
          "start": 6,
          "end": 91,
          "quote": "Il 2026-11-02T09:00:00Z propongo riunioni settimanali di un’ora. È solo una proposta."
        }
      ]
    },
    {
      "local_id": "evolving-2",
      "shape": "item",
      "text": "Il 2026-11-03T10:00:00Z scegliamo invece una prova di briefing giornalieri di dieci minuti, per una settimana.",
      "descriptors": [
        {
          "value": "counter-proposal",
          "certainty": "asserted"
        }
      ],
      "evidence": [
        {
          "source_revision_id": "3f2a8b04-ebe5-5f75-9173-f4cb4f45172b",
          "start": 96,
          "end": 206,
          "quote": "Il 2026-11-03T10:00:00Z scegliamo invece una prova di briefing giornalieri di dieci minuti, per una settimana."
        }
      ]
    },
    {
      "local_id": "evolving-3",
      "shape": "item",
      "text": "Ritiro la proposta delle riunioni settimanali. Non è mai stata adottata.",
      "descriptors": [
        {
          "value": "withdrawal",
          "certainty": "asserted"
        }
      ],
      "evidence": [
        {
          "source_revision_id": "3f2a8b04-ebe5-5f75-9173-f4cb4f45172b",
          "start": 213,
          "end": 285,
          "quote": "Ritiro la proposta delle riunioni settimanali. Non è mai stata adottata."
        }
      ]
    },
    {
      "local_id": "evolving-4",
      "shape": "item",
      "text": "Il 2026-11-04T08:00:00Z sospendiamo anche la prova giornaliera: due partecipanti sono assenti.",
      "descriptors": [
        {
          "value": "suspension",
          "certainty": "asserted"
        }
      ],
      "evidence": [
        {
          "source_revision_id": "3f2a8b04-ebe5-5f75-9173-f4cb4f45172b",
          "start": 290,
          "end": 384,
          "quote": "Il 2026-11-04T08:00:00Z sospendiamo anche la prova giornaliera: due partecipanti sono assenti."
        }
      ]
    },
    {
      "local_id": "evolving-5",
      "shape": "item",
      "text": "La situazione attuale è prova sospesa, non ritorno alle riunioni settimanali. Quando riprenderemo resta da decidere.",
      "descriptors": [
        {
          "value": "status update",
          "certainty": "asserted"
        }
      ],
      "evidence": [
        {
          "source_revision_id": "3f2a8b04-ebe5-5f75-9173-f4cb4f45172b",
          "start": 391,
          "end": 507,
          "quote": "La situazione attuale è prova sospesa, non ritorno alle riunioni settimanali. Quando riprenderemo resta da decidere."
        }
      ]
    },
    {
      "local_id": "proposal-1",
      "shape": "entity",
      "text": "riunioni settimanali di un’ora",
      "properties": {
        "frequency": "weekly",
        "duration": "1 hour"
      },
      "evidence": [
        {
          "source_revision_id": "3f2a8b04-ebe5-5f75-9173-f4cb4f45172b",
          "start": 30,
          "end": 58,
          "quote": "riunioni settimanali di un’ora"
        }
      ]
    },
    {
      "local_id": "proposal-2",
      "shape": "entity",
      "text": "prova di briefing giornalieri di dieci minuti",
      "properties": {
        "frequency": "daily",
        "duration": "10 minutes",
        "trial": true
      },
      "evidence": [
        {
          "source_revision_id": "3f2a8b04-ebe5-5f75-9173-f4cb4f45172b",
          "start": 138,
          "end": 186,
          "quote": "prova di briefing giornalieri di dieci minuti"
        }
      ]
    },
    {
      "local_id": "status-1",
      "shape": "entity",
      "text": "prova sospesa",
      "properties": {
        "state": "suspended"
      },
      "evidence": [
        {
          "source_revision_id": "3f2a8b04-ebe5-5f75-9173-f4cb4f45172b",
          "start": 427,
          "end": 440,
          "quote": "prova sospesa"
        }
      ]
    },
    {
      "local_id": "relation-1",
      "shape": "relation",
      "text": "Jo rejects Mina's proposal",
      "relation": {
        "source": "evolving-2",
        "target": "proposal-1",
        "predicate": "rejects"
      },
      "evidence": [
        {
          "source_revision_id": "3f2a8b04-ebe5-5f75-9173-f4cb4f45172b",
          "start": 96,
          "end": 206,
          "quote": "Il 2026-11-03T10:00:00Z scegliamo invece una prova di briefing giornalieri di dieci minuti, per una settimana."
        }
      ]
    },
    {
      "local_id": "relation-2",
      "shape": "relation",
      "text": "Mina withdraws proposal-1",
      "relation": {
        "source": "evolving-3",
        "target": "proposal-1",
        "predicate": "withdraws"
      },
      "evidence": [
        {
          "source_revision_id": "3f2a8b04-ebe5-5f75-9173-f4cb4f45172b",
          "start": 213,
          "end": 285,
          "quote": "Ritiro la proposta delle riunioni settimanali."
        }
      ]
    },
    {
      "local_id": "relation-3",
      "shape": "relation",
      "text": "Jo suspends proposal-2",
      "relation": {
        "source": "evolving-4",
        "target": "proposal-2",
        "predicate": "suspends"
      },
      "evidence": [
        {
          "source_revision_id": "3f2a8b04-ebe5-5f75-9173-f4cb4f45172b",
          "start": 290,
          "end": 384,
          "quote": "Il 2026-11-04T08:00:00Z sospendiamo anche la prova giornaliera: due partecipanti sono assenti."
        }
      ]
    },
    {
      "local_id": "temporal-1",
      "shape": "entity",
      "text": "2026-11-02T09:00:00Z",
      "temporal": {
        "fact_from": "2026-11-02T09:00:00Z"
      },
      "evidence": [
        {
          "source_revision_id": "3f2a8b04-ebe5-5f75-9173-f4cb4f45172b",
          "start": 6,
          "end": 29,
          "quote": "Il 2026-11-02T09:00:00Z"
        }
      ]
    },
    {
      "local_id": "temporal-2",
      "shape": "entity",
      "text": "2026-11-03T10:00:00Z",
      "temporal": {
        "fact_from": "2026-11-03T10:00:00Z"
      },
      "evidence": [
        {
          "source_revision_id": "3f2a8b04-ebe5-5f75-9173-f4cb4f45172b",
          "start": 96,
          "end": 125,
          "quote": "Il 2026-11-03T10:00:00Z"
        }
      ]
    },
    {
      "local_id": "temporal-3",
      "shape": "entity",
      "text": "2026-11-04T08:00:00Z",
      "temporal": {
        "fact_from": "2026-11-04T08:00:00Z"
      },
      "evidence": [
        {
          "source_revision_id": "3f2a8b04-ebe5-5f75-9173-f4cb4f45172b",
          "start": 290,
          "end": 319,
          "quote": "Il 2026-11-04T08:00:00Z"
        }
      ]
    }
  ]
}
```

<a id="output-personal"></a>
## Output personal

Mistral originale congelato.

```json
{
  "items": [
    {
      "local_id": "personal-1",
      "shape": "item",
      "text": "Preferisco incontrarci in un bar tranquillo; per oggi eviterei i locali affollati, senza dire che li evito sempre.",
      "descriptors": [
        {
          "value": "preference for quiet bar meeting",
          "certainty": "asserted"
        }
      ],
      "evidence": [
        {
          "source_revision_id": "83253202-fb5d-5073-a27a-ab83e117f09c",
          "start": 7,
          "end": 121,
          "quote": "Preferisco incontrarci in un bar tranquillo; per oggi eviterei i locali affollati, senza dire che li evito sempre."
        }
      ]
    },
    {
      "local_id": "personal-2",
      "shape": "item",
      "text": "Il mio treno è stato cancellato il 2026-10-09T17:30:00Z. Questo è un evento passato, non il viaggio di domani.",
      "descriptors": [
        {
          "value": "train cancellation event",
          "certainty": "asserted"
        }
      ],
      "temporal": {
        "fact_from": "2026-10-09T17:30:00Z"
      },
      "evidence": [
        {
          "source_revision_id": "83253202-fb5d-5073-a27a-ab83e117f09c",
          "start": 129,
          "end": 239,
          "quote": "Il mio treno è stato cancellato il 2026-10-09T17:30:00Z. Questo è un evento passato, non il viaggio di domani."
        }
      ]
    },
    {
      "local_id": "personal-3",
      "shape": "item",
      "text": "Ho intenzione di fare una passeggiata il 2026-10-17T09:00:00Z. Non l’ho ancora fatta e potrei rinunciare se piove.",
      "descriptors": [
        {
          "value": "planned walk event",
          "certainty": "asserted"
        }
      ],
      "temporal": {
        "fact_from": "2026-10-17T09:00:00Z"
      },
      "evidence": [
        {
          "source_revision_id": "83253202-fb5d-5073-a27a-ab83e117f09c",
          "start": 247,
          "end": 361,
          "quote": "Ho intenzione di fare una passeggiata il 2026-10-17T09:00:00Z. Non l’ho ancora fatta e potrei rinunciare se piove."
        }
      ]
    },
    {
      "local_id": "personal-4",
      "shape": "item",
      "text": "Forse verrò alla passeggiata, ma non ho confermato la mia presenza.",
      "descriptors": [
        {
          "value": "uncertain attendance to walk",
          "certainty": "asserted"
        }
      ],
      "evidence": [
        {
          "source_revision_id": "83253202-fb5d-5073-a27a-ab83e117f09c",
          "start": 369,
          "end": 436,
          "quote": "Forse verrò alla passeggiata, ma non ho confermato la mia presenza."
        }
      ]
    },
    {
      "local_id": "personal-5",
      "shape": "item",
      "text": "Vorrei chiedere a Lee se conosce un percorso coperto. La scelta del percorso è ancora aperta.",
      "descriptors": [
        {
          "value": "inquiry about covered path",
          "certainty": "asserted"
        },
        {
          "value": "open path selection",
          "certainty": "asserted"
        }
      ],
      "evidence": [
        {
          "source_revision_id": "83253202-fb5d-5073-a27a-ab83e117f09c",
          "start": 444,
          "end": 537,
          "quote": "Vorrei chiedere a Lee se conosce un percorso coperto. La scelta del percorso è ancora aperta."
        }
      ]
    }
  ]
}
```

<a id="output-multilingual"></a>
## Output multilingual

Mistral originale congelato.

```json
{
  "items": [
    {
      "descriptors": [
        {
          "certainty": "asserted",
          "value": "quotation"
        }
      ],
      "evidence": [
        {
          "end": 98,
          "quote": "Le devis est de 300 EUR hors taxes. Je ne sais pas encore si notre plafond inclut la TVA.",
          "source_revision_id": "192dbd71-0831-55d5-8cea-b2fa67c499a8",
          "start": 9
        }
      ],
      "local_id": "item-1",
      "properties": {
        "currency": "EUR",
        "tax_included": false,
        "value": 300
      },
      "shape": "entity",
      "text": "Le devis est de 300 EUR hors taxes."
    },
    {
      "descriptors": [
        {
          "certainty": "asserted",
          "value": "quotation"
        }
      ],
      "evidence": [
        {
          "end": 197,
          "quote": "Il nostro tetto è 350 EUR IVA inclusa. Forse il preventivo rientra, ma dobbiamo verificarlo.",
          "source_revision_id": "192dbd71-0831-55d5-8cea-b2fa67c499a8",
          "start": 105
        }
      ],
      "local_id": "item-2",
      "properties": {
        "currency": "EUR",
        "tax_included": true,
        "value": 350
      },
      "shape": "entity",
      "text": "Il nostro tetto è 350 EUR IVA inclusa."
    },
    {
      "descriptors": [
        {
          "certainty": "asserted",
          "value": "quotation"
        }
      ],
      "evidence": [
        {
          "end": 330,
          "quote": "The final total is 360 EUR including tax. That resolves the apparent 300 versus 360 discrepancy; they use different tax bases.",
          "source_revision_id": "192dbd71-0831-55d5-8cea-b2fa67c499a8",
          "start": 204
        }
      ],
      "local_id": "item-3",
      "properties": {
        "currency": "EUR",
        "tax_included": true,
        "value": 360
      },
      "shape": "entity",
      "text": "The final total is 360 EUR including tax."
    },
    {
      "descriptors": [
        {
          "certainty": "asserted",
          "value": "quotation"
        }
      ],
      "evidence": [
        {
          "end": 431,
          "quote": "Donc le devis dépasse le plafond de 10 EUR. Aucune commande n’est approuvée pour le moment.",
          "source_revision_id": "192dbd71-0831-55d5-8cea-b2fa67c499a8",
          "start": 340
        }
      ],
      "local_id": "item-4",
      "properties": {
        "currency": "EUR",
        "excess": 10,
        "tax_included": true
      },
      "shape": "entity",
      "text": "le devis dépasse le plafond de 10 EUR"
    },
    {
      "descriptors": [
        {
          "certainty": "asserted",
          "value": "quotation"
        }
      ],
      "evidence": [
        {
          "end": 530,
          "quote": "Se lo sconto ci porta a 350 EUR tutto incluso, potremmo ordinare. Non è una decisione presa.",
          "source_revision_id": "192dbd71-0831-55d5-8cea-b2fa67c499a8",
          "start": 438
        }
      ],
      "local_id": "item-5",
      "properties": {
        "currency": "EUR",
        "discount_applied": true,
        "tax_included": true,
        "value": 350
      },
      "shape": "entity",
      "text": "Se lo sconto ci porta a 350 EUR tutto incluso"
    },
    {
      "descriptors": [
        {
          "certainty": "asserted",
          "value": "quotation"
        }
      ],
      "evidence": [
        {
          "end": 635,
          "quote": "Who will ask for the discount? We have not assigned that task. The delivery date is still unknown.",
          "source_revision_id": "192dbd71-0831-55d5-8cea-b2fa67c499a8",
          "start": 537
        }
      ],
      "local_id": "item-6",
      "properties": {
        "discount_assigned": false,
        "delivery_date_known": false
      },
      "shape": "entity",
      "text": "Who will ask for the discount? We have not assigned that task. The delivery date is still unknown."
    },
    {
      "local_id": "relation-1",
      "relation": {
        "predicate": "exceeds",
        "source": "item-4",
        "target": "item-2"
      },
      "shape": "relation",
      "text": "le devis dépasse le plafond de 10 EUR"
    },
    {
      "local_id": "relation-2",
      "relation": {
        "predicate": "resolves_discrepancy_with",
        "source": "item-3",
        "target": "item-1"
      },
      "shape": "relation",
      "text": "That resolves the apparent 300 versus 360 discrepancy; they use different tax bases."
    },
    {
      "local_id": "relation-3",
      "relation": {
        "predicate": "implies_discount_target",
        "source": "item-5",
        "target": "item-6"
      },
      "shape": "relation",
      "text": "Se lo sconto ci porta a 350 EUR tutto incluso, potremmo ordinare."
    }
  ]
}
```

<a id="output-control-conditional-es-good"></a>
## Output control.conditional_es.good

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-conditional-es-mutated"></a>
## Output control.conditional_es.mutated

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-negation-en-good"></a>
## Output control.negation_en.good

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-negation-en-mutated"></a>
## Output control.negation_en.mutated

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-actual-discount-fr-good"></a>
## Output control.actual_discount_fr.good

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-actual-discount-fr-mutated"></a>
## Output control.actual_discount_fr.mutated

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-collective-it-good"></a>
## Output control.collective_it.good

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-collective-it-mutated"></a>
## Output control.collective_it.mutated

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-individual-en-good"></a>
## Output control.individual_en.good

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-individual-en-mutated"></a>
## Output control.individual_en.mutated

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-lifecycle-de-good"></a>
## Output control.lifecycle_de.good

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-lifecycle-de-mutated"></a>
## Output control.lifecycle_de.mutated

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-future-intent-en-good"></a>
## Output control.future_intent_en.good

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-future-intent-en-mutated"></a>
## Output control.future_intent_en.mutated

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-past-completed-it-good"></a>
## Output control.past_completed_it.good

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-past-completed-it-mutated"></a>
## Output control.past_completed_it.mutated

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-uncertain-fr-good"></a>
## Output control.uncertain_fr.good

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-uncertain-fr-mutated"></a>
## Output control.uncertain_fr.mutated

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-provenance-unicode-good"></a>
## Output control.provenance_unicode.good

Controllo scritto per il benchmark: non generato da Mistral.

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

<a id="output-control-provenance-unicode-mutated"></a>
## Output control.provenance_unicode.mutated

Controllo scritto per il benchmark: non generato da Mistral.

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
