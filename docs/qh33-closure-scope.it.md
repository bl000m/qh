# QH-33 — chiusura tecnica e validazione differita

## Stato conclusivo — 17 ottobre 2026

**QH-33 è DONE per lo scope tecnico approvato; PR #8 è merged.** Il merge è
[`a7a2da3e43fca3fbcd54dd743956c14e0fa599e2`](https://github.com/bl000m/qh/commit/a7a2da3e43fca3fbcd54dd743956c14e0fa599e2),
con due genitori e storia dei commit preservata. La descrizione Jira contiene
l'addendum di scope datato 16 ottobre, conservando il testo originale; il
[commento di chiusura 10008](https://contextlab.atlassian.net/browse/QH-33?focusedCommentId=10008)
registra merge, prove e limiti. La transizione effettiva è stata verificata come
`Terminé(e)`, categoria DONE. La precedente proposta sotto è quindi approvata,
registrata ed eseguita, non più un impedimento alla chiusura.

| DoD tecnica approvata | Risultato verificato |
| --- | --- |
| Benchmark v2 riproducibile e metriche separate provvisorie | PASS — 74 unità, 46 proposizioni originali / 44 attive; nessuna metrica umana o indice complessivo |
| Confronti offline e controlli di integrità | PASS — audit v1/v2 e review gate; nove false accettazioni temporali eliminate, sette positivi conservati, senza nuova comprensione LLM misurata |
| CI dell'ultimo head PR `1b900fa` | PASS — [quality, OIDC e native](https://github.com/bl000m/qh/actions/runs/38901663903) verdi; 19 test benchmark/review, 383 native senza skip, due test OIDC; albero del merge identico all'head verificato |
| Report dei difetti residui e protocollo futuro | PASS — errori/riserve visibili; confronto Mistral baseline/candidato preparato, non eseguito |
| Review, merge effettivo e Jira allineato | PASS — chiusura autorizzata dal proprietario, merge verificato e QH-33 DONE |

La validazione umana indipendente completa è **differita, non completata**, in
[QH-38](https://contextlab.atlassian.net/browse/QH-38), ancora aperto e collegato
tramite `Relates`. I link della sua matrice/fonti/rubrica sono già riallineati a
`main`. Rimangono `human_review.metrics=null`, 0/74 unità accettate, template e
attestazioni non compilati. La seconda review GPT-6 resta AI-only; i due controlli
contestati conservano i giudizi v2. V1/v2, output originali, derivati e ledger
sono preservati. Nessuna promozione automatica a `confirmed`.

Codice integrato in `main` non significa codice distribuito: il runtime VPS resta
basato sulle immagini `c723d32c5d0825f9232ece560e7e666e69dceb27` e schema 0005.
Nessun deployment, migrazione o nuova inferenza è stato eseguito per la chiusura.
I difetti semantici e i gate del prossimo esperimento rimangono quelli documentati.

## Proposta e verifiche preparatorie del 16 ottobre (storico preservato)

Il testo seguente conserva il checkpoint precedente all'approvazione finale;
le sue indicazioni «aperta», «non DONE» e «non autorizzati» non sono lo stato corrente.

16 ottobre 2026 · [QH-33](https://contextlab.atlassian.net/browse/QH-33) ·
[PR #8](https://github.com/bl000m/qh/pull/8), aperta ·
branch `feat/QH-33-semantic-fidelity`, checkout `/home/ubuntu/qh`.

**Consegna tecnica pronta per review; non DONE.** Il proprietario ha richiesto di
documentare il differimento della validazione umana a
[QH-38](https://contextlab.atlassian.net/browse/QH-38). Questo documento propone
l'adeguamento esplicito dello scope; non modifica Jira e non attesta soddisfatta
la dipendenza originaria dal riferimento validato. Merge e transizione restano
non autorizzati. Non viene avviato QH-38 o un altro esperimento.

## Seconda verifica AI: esito riferito e riserve aperte

Fonte: [commento 10007 del proprietario su QH-33](https://contextlab.atlassian.net/browse/QH-33?focusedCommentId=10007),
letto via Atlassian MCP insieme alla descrizione di QH-38. Il commento riferisce
una seconda verifica GPT-6 delle 74 unità, delle quattro catture Mistral e dei
20 payload sintetici: nessuna anomalia negli ancoraggi source/JSON pointer,
principali difetti semantici confermati e due riserve aggiuntive.
È **una seconda verifica AI, non validazione umana indipendente**. Nel repository
si registra questa sintesi attribuita al commento, non un verbale completo della
sessione GPT-6 né una misura di accordo fra revisori. Gli audit riproducibili
verificano separatamente l'integrità tecnica, non la correttezza semantica.

I due output sotto sono **controlli sintetici scritti durante QH-33**, non nuove
generazioni Mistral. Il suffisso `.good` identifica il controllo, non una garanzia.

| Unità e payload completo | Fonte originale | Testo estratto, `/items/0/text` | Giudizio v2 conservato e riserva da decidere in QH-38 |
| --- | --- | --- | --- |
| [control.negation_en.good](evidence/qh33-v2-20261016/unit-details.it.md#unit-control-negation-en-good) | «No booking was approved; approval is still pending.» | `No booking has been approved.` | `active_coverage=pass`: conserva la non-approvazione ma non dice che l'approvazione è ancora attesa. Valutare `partial` per completezza; non trasformare l'omissione in un'affermazione di approvazione |
| [control.collective_it.good](evidence/qh33-v2-20261016/unit-details.it.md#unit-control-collective-it-good) | «Le tre delegate hanno votato insieme la pausa. Uma riferisce il risultato.» | `Le tre delegate hanno deciso insieme la pausa.` | `active_coverage=pass`: conserva le decisori collettive ma omette Uma come reporter. Valutare `partial` se quel ruolo è necessario alla comprensione/provenienza; non è un'attribuzione della decisione a Uma |

Nel Context Space le omissioni potrebbero perdere, rispettivamente, un processo
ancora aperto e il ruolo di chi riferisce una decisione. La rilevanza per il
coverage evolutivo va giudicata esplicitamente: non ogni dettaglio della fonte è
automaticamente un obbligo di estrazione. Questi sono impatti potenziali, non danni
osservati sui dati persistenti QH.

**Nessun rating v2 è stato modificato.** Matrice e dettagli congelati continuano a
mostrare i giudizi proposti prima di queste riserve, compreso «Nessuna criticità
proposta» per le due righe. Questo addendum rende visibile la contestazione senza
riscrivere la fotografia precedente. Le metriche restano provvisorie e non
incorporano le riserve. Un'eventuale rettifica richiederà una revisione esplicita
del riferimento e il ricalcolo delle metriche; v1/v2 resteranno ricostruibili.

## QH-38 copre formalmente il debito di validazione

QH-38 è stato letto in stato **À faire**, senza eseguire scritture. La descrizione
collega QH-33, PR #8, matrice, fonti/payload e rubrica v2; include entrambe le
riserve e i difetti principali. La sua DoD richiede:

- 74/74 unità lette da una persona, nessun pending e giudizi motivati;
- attestazioni effettive di indipendenza, completezza e lettura dei payload,
  con identificatore e data del revisore;
- metriche umane separate per dimensione e differenze dalle proposte AI;
- conservazione delle evidenze, controversie e decisioni, con collegamento QH-33;
- nessun esperimento a pagamento senza ulteriore autorizzazione.

Il perimetro copre 46 proposizioni originali (44 attive, due storiche
ricostruibili), tre extra-claim, cinque annotazioni e 20 controlli. Il protocollo
non viene indebolito: il template resta vuoto, 0/74 unità accettate,
`human_review.metrics=null`, attestazioni non fornite. QH-38 richiede di versionare
il riferimento quando cambia il denominatore; anche cambiamenti di rating/rubrica
devono mantenere una lineage esplicita rispetto alle versioni congelate.

Il collegamento fra i ticket è oggi testuale nelle descrizioni/commento, senza un
issue link Jira strutturato. Questo non rende assente il perimetro di QH-38, ma
non elimina la vecchia dipendenza scritta nella descrizione di QH-33.

## Scope e Definition of Done proposti

La sezione DONE effettiva di QH-33, riletta in Jira, dice:

> Report con metriche separate (coverage, supported claims, non-decisioni, temporality, provenance) e raccomandazione verificabile per il successivo esperimento; nessuna promozione automatica a confirmed.

Le attività/dipendenze richiedono inoltre una prima validazione umana indipendente
e un riferimento validato. **Quel requisito non è stato soddisfatto.** Si propone
di differirlo esplicitamente a QH-38, mantenendo la consegna attuale limitata a:

1. Benchmark v2 riproducibile, rubriche e metriche provvisorie per dimensione,
   con v1, output, fonti, derivati e ledger preservati.
2. Confronti offline e controlli tecnici con evidenze prima/dopo, distinti dalla
   comprensione del LLM; nessuna attestazione umana o metriche human_review.
3. Difetti residui, riserve della seconda AI e limiti del POC visibili; pacchetto
   completo per la futura verifica QH-38, senza iniziarla oggi.
4. Raccomandazione riproducibile per il confronto baseline/candidato, solo
   preparato; stati `proposed`, atomicità e provenienza conservati.
5. Review tecnica, controlli obbligatori verdi sull'ultimo commit; soltanto dopo
   approvazione esplicita, merge verificato e Jira allineato alla decisione di scope.

| Criterio | Verdetto e classificazione | Evidenza / limite |
| --- | --- | --- |
| Metriche separate e benchmark riproducibile | PASS — implementato e testato, giudizi provvisori | [Report v2](qh33-semantic-evaluation.md), [metriche](evidence/qh33-v2-20261016/metrics.json), audit di riproduzione |
| Fixture mirate e confronto offline | PASS — implementato e testato | 20 controlli scritti, confronto identico salvo guard temporale: nove false accettazioni rimosse, sette positivi conservati; nessun cambiamento ai payload LLM |
| Separazione significato/citazione/stato umano | PASS — implementato e testato | Sette dimensioni, gruppi distinti, review gate e metriche umane null; citazione autentica non implica sostegno semantico |
| Atomicità, provenienza e nessuna conferma automatica | PASS — implementato e testato | Regressioni QH-32/QH-33; multilingual rimane interamente respinto, nessuna promozione a `confirmed` |
| Integrità v1/v2, originali, ledger e template personale | PASS — implementato e testato | Audit e confronto Git con checkpoint `8ada49d`; nessuna modifica agli artefatti congelati |
| Report e raccomandazione per esperimento successivo | PASS — implementato e verificato come preparazione | Protocollo baseline/candidato congelato; efficacia del prompt NON TESTATA, nessuna nuova inferenza |
| Validazione umana completa | NOT TESTED — da differire a QH-38, fuori dallo scope proposto | Nessun revisore umano attestato; non registrare il requisito originario come PASS |
| Allineamento formale dello scope in QH-33 | PENDING — proposta documentata, Jira non modificato | Occorre approvare e registrare il differimento prima della futura chiusura |
| Review, merge e Jira DONE | PENDING — non eseguiti | PR #8 aperta; servono ulteriore autorizzazione e verifiche effettive |

Non emergono necessità di nuove funzionalità, architettura o inferenze per questa
consegna tecnica. **L'impedimento formale alla chiusura resta il disallineamento
dello scope in Jira**, oltre a review/merge e transizione non ancora autorizzati.
Accettare il differimento rende la verifica umana un debito esplicito QH-38;
non equivale a soddisfarla, certificare accuratezza o dichiarare QH-33 già DONE.

## Difetti residui e prossimo esperimento

Restano visibili il flag di sconto applicato senza supporto, le omissioni di
non-approvazione/non-decisione, il rifiuto personale inferito, classificazioni e
attribuzioni parziali, relazioni poco utili e date scollegate dalle proposizioni.
I due nuovi dubbi di completezza si aggiungono a questi limiti. Il controllo
temporale corregge un'accettazione tecnica; non risolve tali errori del modello.

Il prossimo esperimento raccomandato è il confronto Mistral baseline/candidato
già [preparato nel protocollo](evidence/qh33-semantic-20261016/README.md), cambiando
una sola variabile. **Non è stato eseguito né autorizzato qui.** Il differimento a
QH-38 non rimuove i gate di validazione/autorizzazione del protocollo congelato e
non permette di presentare il benchmark come standard umanamente validato.
Nessuna chiamata a pagamento, migrazione, deployment o altro sviluppo è avviato.

## Controlli eseguiti per questo aggiornamento documentale

- `python3 docs/evidence/qh33-v2-20261016/audit.py`: PASS; riproduzione v1/v2,
  74 ID, 44 proposizioni attive, attestazioni assenti e metriche umane null.
- Immagine già verificata `qh33-v2-review:f745db5e62f65f35fd7960f93e367ff6fbeaa7f7`,
  `--network none`, nessuna chiave o source bind:
  `python -m unittest discover -s tests -p 'test_qh33*.py' -v`:
  **19 test passati, 2,238 s**. Dimostrano integrità e review gate, non verità semantica.
- Confronto Git con `8ada49d`: nessun cambiamento a codice, test, workflow,
  configurazione, fixture, annotazioni o archivi congelati. Hash/mode dei file
  protetti, ledger e inventario dei container esistenti invariati.
- Collegamenti locali: **62 destinazioni/ancore** verificate nei cinque documenti
  modificati; controllo whitespace e guard del Git index contro segreti.
- [CI precedente](https://github.com/bl000m/qh/actions/runs/38898248816), commit
  `8ada49d`: quality/OIDC/native verdi, **383 test native senza skip**.
  L'esito della CI del nuovo commit documentale viene registrato nella PR #8,
  verificando lo SHA effettivo; i test precedenti non lo sostituiscono.

Nessuna nuova inferenza o scrittura Jira; nessun merge, deployment o intervento
sui database persistenti. Nessun nuovo test è aggiunto per la sola documentazione.
