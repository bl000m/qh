# QH-33 v2 — pacchetto per la verifica personale

**D1–D5 approvate. Verifica personale delle 74 unità non ancora attestata.**
Questo pacchetto applica le decisioni sul criterio evolutivo, sulla rubrica e sui
limiti del POC; i giudizi per unità rimangono proposte dell’assistente.
Nessun merge, Jira DONE o nuova inferenza è autorizzato da questa approvazione.

Apri la [matrice compatta e navigabile](review-matrix.it.md). Tutti i 74 ID sono
presenti, ciascuno con fonte, output, sette giudizi distinti e criticità. Le righe
**★** richiedono particolare attenzione; anche quelle senza stella vanno verificate.

1. Leggi le [14 fonti condivise e i 24 payload completi](case-payloads.it.md): quattro
   catture originali Mistral e venti controlli scritti per il test. I payload sono
   formattati per lettura, senza modifiche ai valori; i file originali restano intatti.
2. Per ogni ID confronta la [lettura e le motivazioni](unit-details.it.md) con la
   fonte e con tutti i campi del candidato, non soltanto con la citazione.
3. Approva o correggi giudizi indicando gli ID. Accettare un NO conferma un difetto;
   non richiede rendere perfette le estrazioni per chiudere il report QH-33.

**Le unità su cui concentrarsi:** i campi relativi allo sconto ipotetico, le due
negazioni operative omesse, il rifiuto personale attribuito a Jo, le classificazioni
parziali, le relazioni e le date isolate; inoltre le due esclusioni storiche e i
quattro controlli `.good` con limiti. Le tre riformulazioni del riferimento
(durata prevista, preferenza condizionale, desiderio di chiedere a Lee) sono marcate.

## Rubrica e metriche

La [rubrica v2](rubric.it.md) separa `semantic_support` da `citation_traceability`.
Citazione corretta non significa claim sostenuto; offset originali e risolvibilità
sono registrati separatamente nei [diagnostici e nelle metriche](metrics.json).
I quattro gruppi di unità e le sette dimensioni rimangono distinti, senza voto globale.

Restano 46 proposizioni originali; **44 entrano nel coverage attivo**. Le due
incertezze storiche risolte sono mantenute, con fonte ricostruibile e rating N/A,
non trasformate in pass. Lo stato di comprensione include le evoluzioni necessarie,
non solo l’ultimo messaggio. Cambi di rubrica/denominatore non misurano un miglioramento
Mistral: output e richieste sono invariati.

Gli errori del modello restano: sconto come applicato, non-approvazione/non-decisione
non estratte, inferenza personale, classificazioni e collegamenti temporali deboli.
I limiti sono accettati per il POC QH-33, non certificati come risolti. Il successivo
confronto controllato fra prompt resta [preparato, non eseguito](../qh33-semantic-20261016/future-protocol.json).

## Attestazioni ancora mancanti

Il [template personale](review-template.json) ha **74 decisioni pending, rating null,
revisore/data/indipendenza null, completezza e verifica dei payload false**.
Le metriche personali sono null, con 0/74 unità accettate. L’approvazione D1–D5
è registrata solo nel [benchmark v2](../../../apps/api/tests/fixtures/qh33/benchmark-v2.json),
separatamente da questi campi.

Il protocollo richiede la verifica personale di ogni unità, identificatore del
revisore, data con fuso e attestazioni esplicite di indipendenza, completezza del
riferimento e lettura dei payload. Non è necessario ricopiare il JSON: i giudizi e
le dichiarazioni effettivamente ricevuti possono essere trascritti fedelmente in un
file di review distinto, senza simulare firme o performance di lettura.

## Riproduzione e preservazione

```bash
# Solo stdlib: nessuna chiave, rete, database o provider.
python3 scripts/evaluate_qh33_v2.py --out /tmp/qh33-v2-personal-review
python3 docs/evidence/qh33-v2-20261016/audit.py
# Soltanto dopo una review personale effettivamente fornita:
python3 scripts/evaluate_qh33_v2.py --out /tmp/qh33-v2-reviewed --review /private/review.json
```

L’output deve essere una directory nuova. Il generatore v2 riusa le guardie personali
del valutatore v1 tramite un adattamento esplicito dei nomi, senza modificarlo.
Lo stesso Citation Resolver QH-32 produce solo diagnostici: nessuna pubblicazione
parziale o scrittura canonica. V1, annotazioni storiche, catture e ledger restano
immutati. Il manifest verifica identità e riproducibilità, non la verità dei giudizi.

[Report e stato QH-33](../../qh33-semantic-evaluation.md).


## Verifiche tecniche del pacchetto

- PASS: **19 test v1/v2**, 2,391 s, nell’immagine esatta senza rete, chiavi o bind
  dei sorgenti; generazione offline del pacchetto riuscita.
- PASS: audit v1 e v2, identità dei 74 ID, fonti/candidati e 518 motivazioni; link
  locali e ancoraggi espliciti della nuova matrice verificati.
- PASS: Ruff, actionlint, Git whitespace e guardia dell’indice per segreti/file privati.
- CI dell’ultimo commit: risultato registrato nella PR #8 dopo l’esecuzione.
- Verifica personale: **non attestata**, nessun giudizio importato.

Sorgente eseguibile/OCI `f745db5e62f65f35fd7960f93e367ff6fbeaa7f7`, immagine
`qh33-v2-review:f745db5e62f65f35fd7960f93e367ff6fbeaa7f7`, ID immutabile
`sha256:684d040c124af536ba6ed13f9e6fc738e0278354f9c5c60eb4259ba04ab969d0`.
Costruita da Git archive; modifiche documentali successive non cambiano tool,
fixture, test o configurazione. Questa è evidenza di preparazione, non Done.
