# QH-51 — risposta dialogica e correzioni CI

Mandato owner22 ottobre2026, PR23 aperta. Jira QH-51 letto con il suo commento;
nessuna scrittura o transizione Jira. Il contratto corrente è
[qh-51-response-support.md](qh-51-response-support.md); l'audit precedente rimane
storico. Questo incremento non costituisce conferma umana della comprensione.

| Criterio | Classificazione / verifica |
| --- | --- |
| Risposta da dialogo con zero canonico | Implementato e testato: decoder, ChatResponse, tre ingressi HTTP, DTO/validator TypeScript e UI, senza fallback al vecchio formato |
| Coerenza dichiarazione/input/alias | Implementato e testato:19 casi supporto, inclusi canonical/mixed senza alias, alias inventati/duplicati, dialogue senza utente o con riferimenti, booleano incoerente e campo assente |
| Dichiarazione non equivale a verità | UI e contratto espliciti; controlli di appartenenza/presenza, non un verificatore automatico generale di entailment. Epistemica e review rimangono indipendenti |
| Nessuna conoscenza automatica | Implementato e testato: risposte dialogiche senza Source/revisioni; UUM/review restano azioni distinte. Policy/snapshot/JSON/budget/provenance conservati |
| Vecchio harness non scrive raw su429 | Implementato e testato su SQL/Neo4j: cattura errori opt-in solo nella factory privata; writer storico richiede200. Test sia default-off sia cattura forzata; GET+POST poi STOP, nessun retry, nessuna pubblicazione |
| Readiness conserva invarianti | Implementato e testato: sei dimensioni realmente vuote e inserimento compatto; form/descrizioni/refresh/logout/owner isolation. Mobile verifica breadcrumb visibile e H1 accessibile, non il box intenzionalmente assente di display:contents |
| Dossier sanitario fittizio offline | Implementato e testato privatamente: HTTP200 su FastAPI/DevelopmentAI/decoder con MockTransport, poi DTO e componenti React reali in Chromium. dialogue,0 riferimenti,0 conoscenza; fixture fuori Git e CI |
| CI finale e chiamata reale | Evidenze di esecuzione nel risultato operativo finale indicato sotto, sullo stesso HEAD. Non confondere i test simulati con il risultato reale o con accettazione owner |
| Merge, accettazione finale e Jira DONE | Fuori scope: PR23 aperta, owner review pendente. Non applicare0007 o modificare PR19 |

I test di supporto controllano la compatibilità dichiarativa con gli input. Canonical
può includere una revisione proposta solo se esplicitamente autorizzata: significa
provenienza persistita, non verità/approvazione umana. Insufficient può citare fonti
valide ma inadeguate; il bool deve essere true esattamente in questo caso. Gli avvisi
su proposte e copertura parziale rimangono anche quando il modello non li menziona.

## Cause della CI39827829662

Quality e OIDC erano verdi. Native:368 PASS/1 FAIL; il nuovo last_exchange includeva
HTTP429 e il writer storico salvava ogni exchange come raw.json. Ripristinata la
semantica predefinita successful-JSON e separata la cattura privata esplicita;
seconda barriera nel writer200-only. Nessuna assertion di riservatezza rimossa.
Il test ora dimostra anche che un errore catturato esplicitamente non finisce nel
raw storico. Fonti originali/ledger/reservations/failure-state sono conservati.

Browser:113 PASS base,47 outage,1 restore/rebuild; prodotto8 PASS/1 FAIL sul vecchio
heading « J’ajoute un élément ». Dopo la correzione è emersa l'assertion mobile
sul wrapper display:contents, anch'essa sostituita con gli invarianti visivi e di
accessibilità pertinenti. Il layout non è stato modificato per soddisfare il test.

## Esecuzioni mirate (batch sovrapposti, non sommare)

- Docker backend:168 PASS chat/context/alias/sessioni/development/diagnostica e
  pipeline SQL/grafo;87 PASS supporto/429/Mistral/architettura;36 PASS su supporto,
  diagnostica e composition. Ruff PASS.
- Frontend:10 PASS sui contratti chat/diagnostica/trasporto; TypeScript e build Vite
  PASS. Fixture medica privata:API e componenti UI PASS, provider simulato.
- Browser nativo product readiness:1 PASS, comprendendo descrizioni, persistenza
  manuale esplicita, mobile/zoom, riapertura, logout e Bob. Il primo tentativo ha
  rilevato la vecchia assertion geometrica, poi corretta e verificata.
- Il percorso ordinary AI verifica anche basis dialogue,0 riferimenti, history
  vuota prima dell'esplicita estrazione UUM, warning e geometria invariata.

Checkout unico `/home/ubuntu/qh`, branch `feat/QH-51-semantic-understanding`, baseline
387e8c4. Commit337c40e: isolamento cattura errori e correzione readiness. Il successivo
commit di contratto aggiorna backend/DTO/UI/test/docs, preservando gli output storici.
Una sola pubblicazione del candidato avvia la campagna CI; correggere eventuali
regressioni reali non significa reinterpretare la vecchia campagna rossa come verde.

Il [registro operativo](deployments.md) documenta app-only cutover e protocollo live.
Evidenze private/durevoli: `.local-archive/qh51-support-basis-20261022/`;
`SAFE-RESULTS.json` contiene esiti, HEAD/run CI, token/costo e preservazione senza
contenuti/prompt. Il JSON provider resta nel solo archivio diagnostico privato,
scade un'ora dopo la chiamata e non viene copiato in un artefatto CI/repository.
La prova reale non effettua UUM o conferma; non misura la qualità semantica generale.


## Regressione del primo candidato e correzione

La campagna39839733344 sul candidato2dcbf76 ha Quality/OIDC verdi e Native903 PASS.
Browser113 PASS/1 FAIL: secondo turno nel flusso storico QH45. La selezione trasmessa
è vincolata al grant e non può restringersi silenziosamente quando cresce il dialogo.
Il nuovo prompt aveva2767 byte contro2054 precedenti, riducendo il margine entro il
bound12000. Una nuova regressione con sei record vicini al limite8KB riproduce il
rifiuto sul vecchio prompt; il prompt compatto conserva le istruzioni e il nuovo
contratto in1894 byte, senza aumentare limiti/token/costi o indebolire lo snapshot.
Il test verifica sia il follow-up entro bound con gli stessi sei record/prefix,
sia il rifiuto prima dell'HTTP di un follow-up troppo lungo. Il browser verifica
anche il bound calcolato e HTTP200 prima dell'esistenza del secondo turno.
La precedente verifica browser focalizzata, da sola, non aveva dimostrato il margine
sulla campagna completa. La nuova campagna resta obbligatoria sul candidato corretto.

Il log del singolo fallimento CI non conteneva il bound della preview, e la sola
ripetizione focalizzata è passata anche prima della compattazione: l'attribuzione
di quel singolo evento al margine resta un'inferenza. Il difetto di headroom è
invece riprodotto deterministicamente dal nuovo test limite (vecchio prompt FAIL,
compatto PASS). Gli ulteriori assert browser rendono esplicito questo dato nelle
campagne successive, senza mascherare eventuali altre cause di errore HTTP.


## Primo invio reale dopo CI verde e correzione del tipo indicato nel prompt

CI39843014907/4e57ce4: tutti4 job verdi, Native905 PASS, browser114 base +48 outage
+1 restore/rebuild +9 prodotto +2 UUM +6 ciclo radiale/IA ordinaria. La prova reale
è stata eseguita **una volta** con quel candidato e non è stata ripetuta dal gestore
di errore: HTTP Mistral200,620 input/144 output, USD0.00017940 completed, HTTP QH503.
Il modello ha restituito `reference_aliases: {}` (object), pur dichiarando dialogue
con insufficient_context=false. Il decoder ha correttamente respinto il tipo errato.
Il prompt compatto aveva omesso la parola array: correzione del prompt, non del JSON
originale o della regola. Ora specifica JSON array,[] se vuoto,mai object, e fornisce
un esempio dialogico eseguibile validato dallo stesso decoder. Una regressione
con il tipo effettivo{} resta bloccata e il motivo privato indica il campo esatto.

Il primo invio, il suo stop marker, il costo e la risposta diagnostica rimangono
immutati; nessun backfill o riparazione silenziosa. La creazione esplicita ha lasciato
lo Space con0 fonti/elementi/revisioni. Il ledger aveva7 chiamate prima della prova
(una ulteriore chiamata owner durante l'attesa),8 dopo:92 richieste/USD2.49642760.
La verifica del candidato corretto usa lo stesso input congelato e lo stesso Space,
con un nuovo invio esplicito separato dopo test offline e CI verde. È nel plafond
owner attuale, massimoUSD0.0024, senza retry HTTP/fallback o reset contabile; nessun
meccanismo applicativo invia nuovamente automaticamente dopo un errore.

Dopo la correzione array/esempio:126 test mirati PASS nel container candidato
con le evidenze storiche montate/copia corretta e Ruff PASS. Una prima esecuzione
nel container runtime aveva123 PASS/3 errori di fixture assente (docs/evidence non
montato); non erano fallimenti delle assertion. La ripetizione nel candidato con
le fixture originali ha verificato tutti126 casi, compresi margine e rifiuti.
