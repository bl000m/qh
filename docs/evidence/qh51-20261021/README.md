# QH-51 — Evidenza isolata, 2026-10-21

Solo dati sintetici. [Rapporto e criteri](../../qh-51-implementation.md),
[decisione approvata](../../qh-51-assignment-review-decision.md),
[proposta economica non autorizzata](../../qh-51-real-experiment-proposal.md).

Le catture provengono da Chromium → Keycloak → backend pubblico → PostgreSQL e
Neo4j usa e getta. I due Space sono creati dall’interfaccia; il provider test-only
restituisce output scritti a mano per input completi esatti. Nessuna inferenza reale.
Il dominio organizzativo scelto è intenzionalmente diverso dai temi estratti.
Le sei catture della mappa/review sono del singolo scenario due Space superato
nel run locale6; il consenso conversazione è del run7 superato. La successiva
correzione della vista avanzata è verificata separatamente dal caso QH-39.
[source-checkpoint.json](source-checkpoint.json) identifica le immagini del
candidato finale e verifica la corrispondenza dei suoi sorgenti al checkout.

- [Bien-être desktop](qh51-wellbeing-themes-desktop.png) e
  [mobile](qh51-wellbeing-themes-mobile.png): temi espliciti e copertura della pagina.
- [Membri Sommeil](qh51-wellbeing-members.png): due membri reali, ruoli e più temi.
- [Review selettiva](qh51-selective-review.png): Nutrition è un errore intenzionale
  della fixture; viene rifiutato senza perdere testo/fonte. Non è una categoria fissa.
- [Projet professionnel](qh51-professional-themes-desktop.png): temi differenti.
- [Consenso conversazione](qh51-conversation-semantic-consent.png): solo i tre
  messaggi originali selezionati, quattro proposte e fonte verificata dopo salvataggio.
- [Stati indipendenti](qh51-item-and-assignment-states.png): elemento confermato,
  assegnazioni ancora proposte.

[local-checks.json](local-checks.json) riporta i conteggi mirati e i controlli di
preservazione, con sovrapposizioni esplicite. La campagna CI finale resta il gate
completo della PR.

[fixture-metrics.json](fixture-metrics.json) misura conformità provvisoria della
fixture:8/8 atomi e ruoli,15/16 assegnazioni corrette su15 di riferimento,8/8 locator.
Non è una valutazione umana indipendente né una misura della qualità Mistral.
Il riuso dei nomi e il rifiuto di candidati estranei sono testati come contratto;
qualità semantica e naming del provider reale restano NOT TESTED.

[experiment-payloads.json](experiment-payloads.json) contiene quattro body sintetici
esatti generati offline: non è un’autorizzazione alla loro trasmissione.

Log completi degli esperimenti/test, tentativi falliti e controlli di preservazione
sono conservati nella destinazione privata `.local-archive/qh51-20261021/`; non si
pubblicano configurazioni, token, credenziali, dati demo o ledger.
