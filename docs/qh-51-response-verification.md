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
