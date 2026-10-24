# QH-51 — audit e contratto di validazione proposto, 22 ottobre 2026

Stato storico: audit del candidato 9d4a420. Contratto successivamente **approvato**
dall’owner il22 ottobre2026; [matrice corrente](qh-51-response-support.md).
Le sezioni del gate sotto sono conservate come storia della decisione.
La diagnostica osserva i controlli: non cambia l'ammissione delle risposte.

| Regola | Dove | Cosa rifiuta | Motivazione | Decisione che la autorizza | Necessaria o discutibile | Proposta |
| --- | --- | --- | --- | --- | --- | --- |
| OIDC, owner, CHAT, identità development | `adapters/oidc.py`, `chat/development.py::_authorize`, `chat/implementation.py::_authorize` | Token scaduto, altro owner/principal, Space estraneo | Isolamento prima della disclosure | Product Contract; ADR 0002/0004/0007, decisione owner 22/10 | Necessaria | Conservare, bloccare prima del provider e sopprimere risposte dopo perdita di accesso |
| Plafond, modello, listino e prenotazione atomica | `adapters/llm/session_config.py`, `mistral.py::reserve/_request` | Credenziali/configurazione non valide, modello diverso, quota insufficiente, pending/failure | Impedire spesa/disclosure non autorizzate | ADR 0007 e successive autorizzazioni economiche owner | Necessaria | Nuovo limite cumulativo, nessun reset/retry; distinguere accounting da accettazione QH |
| JSON esatto e chiavi uniche | `chat/context.py::decode_answer`; `understanding/extractor.py::decode_output`; `web/src/chat.ts::chatAnswer` | JSON invalido, duplicati, campi extra, tipi errati | Contratto wire deterministico, niente riparazioni nascoste | QH-13/45; QH-51 e ADR 0010 per UUM | Necessaria come integrità; campi esatti sono una scelta di protocollo | Bloccare formato invalido; registrare regola precisa; eventuale nuovo DTO richiede approvazione |
| Citazione canonica obbligatoria se `insufficient_context=false` | `chat/context.py::decode_answer`: `if not insufficient and not ids`; duplicata in `web/src/chat.ts` | Risposta anche pertinente basata solo sul dialogo, con elenco canonico vuoto | Originario contratto di risposta contestuale QH-13 | Documentata nell'implementazione QH-13; ADR 0007 conserva il DTO, ma non stabilisce che il dialogo debba avere citazioni canoniche | **Discutibile come requisito funzionale**, non barriera owner/sicurezza | Separare supporto dialogico da supporto canonico; attendere approvazione prima di cambiarla |
| `insufficient_context` | `chat/context.py::SYSTEM/decode_answer`; `web/src/Chat.tsx` e `chat.ts` | Tipo diverso da bool; false senza citazioni | Segnalare limiti, non confermare fatti | Product Contract distingue provenienza, interpretazione e conferma | Bool necessario al DTO; equivalenza assenza canonico/insufficienza discutibile | Avviso distinto su supporto e copertura; non trattare true come errore. Oggi true + alias vuoti è ammesso |
| Alias, source catalog e snapshot trasmesso | `chat/context.py::decode_answer`, `chat/references.py`, `serialization.py` | Alias sconosciuto/duplicato, UUID inventato, mappa non conforme ai record inviati | Vietare fonti inventate o di altri Space | ADR 0004/0007; QH-13 contratto alias | Necessaria | Conservare rifiuto; citazioni indicano appartenenza, **non entailment** |
| Input/output limitati | `chat/context.py::build_context/decode_answer`; `mistral.py::generate/_request`; `api/chat.py`; `understanding/enrichment.py`, `extractor.py` | Dialogo >7 messaggi, >4096 caratteri/turno, bound input >12000, risposta >4096 caratteri, output troncato, usage oltre cap; segmento UUM >8 turni/20000 byte | Budget, integrità e limiti tecnici | QH-13/45/51, ADR 0007 | Necessari; valori numerici sono scelte tecniche da misurare | Niente troncamento silenzioso o retry. Messaggio specifico via diagnostica; testare separatamente token e caratteri |
| Contesto cambiato / grafo non affidabile | `chat/implementation.py::prepare/respond`, `DevelopmentAI.respond`, `enrichment.py::enrich` | Fingerprint modificato, selezione non verificabile, policy persa | La risposta deve riferirsi alla selezione autorizzata realmente inviata | ADR 0003/0004/0007 | Necessaria per disclosure/identità delle fonti; soppressione per qualunque cambiamento è conservativa | Conservare ora; eventuale visualizzazione come snapshot storico è decisione futura, non un rilassamento implicito |
| QH-32 evidenza testuale esatta | `understanding/uum.py::normalize_output`, `citations.py::resolve_output_citations`, `extractor.py::_resolve` | Quote assente/ambigua/non esatta, source/span/turno estraneo | Provenance verificabile prima di pubblicare proposte | QH-32, ADR 0003/0010 e contratto UUM approvato | Necessaria | Rifiuto atomico del batch, nessun dato canonico parziale, niente correzione delle quote |
| Dimensione, certezza, review e profili | `core/uum.py::validate_primary`, `understanding/uum.py`, `extractor.py::_resolve` | Dimensione non ammessa, certezza incompatibile, review inventata, campi/endpoint/temporalità non supportati | Non confondere classificazione, epistemica e approvazione umana | ADR 0010, contratto review QH-46 | Necessaria | Proposte soltanto; primaria null ammessa; review scritta dal backend. Nessuna classificazione obbligatoria |
| Controlli epistemici sul significato | `chat/context.py::SYSTEM`, `understanding/uum.py::INSTRUCTIONS`; avvisi UI derivati dagli stati canonici | Le istruzioni chiedono negazione/incertezza/attribuzione, ma **non esiste un verificatore generale di verità o entailment** | Non elevare ipotesi/proposte a fatti | Product Contract, ADR 0005/0007/0010 | Principio necessario; non dichiarare una garanzia semantica che il codice non fornisce | Distinguere istruzioni, controlli strutturali e review umana; una citazione valida non prova qualità |
| Conversazione / proposta / corrente | `chat/implementation.py` (nessuna scrittura), `understanding/enrichment.py` (Source + proposed + outbox atomici), QH-46 review | Chat non scrive conoscenza; estrazione senza azione/persistenza esplicita; conferma automatica | Separare dialogo temporaneo e conoscenza governata | Product Contract, QH-39/46, ADR 0008/0010 | Necessaria | Conservare; usare il dialogo appena inviato senza convertirlo automaticamente in fatti |

## Caso riportato

Il ledger live contiene il tentativo con indice zero-based 5: completed,
1079 token input, 536 output, USD 0.00048345. `MistralProvider._request`
registra il costo **prima** di `decode_answer`: completed significa accounting
del trasporto, non risposta accettata. La condizione segnalata può generare il 503
in uno Space vuoto se il modello restituisce false e nessun alias. Non significa
che il contenuto sia semanticamente sbagliato. Senza il JSON originale già
eliminato non possiamo provare che sia stata quella precisa causa nel caso storico.
La nuova diagnostica non recupera retroattivamente contenuti cancellati.

## Contratto funzionale proposto — gate owner ancora aperto

1. **Bloccare** identità/policy/scope non validi, fonti o alias inventati,
   snapshot incoerente, formato non interpretabile, risposta troncata, limiti
   tecnici/economici superati. Nessun retry o pagamento aggiuntivo automatico.
2. **Mostrare con avvertenze** una risposta strutturalmente valida fondata sul
   dialogo esplicitamente inviato, anche con zero revisioni canoniche. Distinguere
   `support_basis` (`dialogue`, `canonical`, `mixed`, `insufficient`) da
   `insufficient_context`; mantenere alias obbligatori per supporto canonico
   dichiarato. Il backend verifica identità dei riferimenti, non verità del testo.
   Il nuovo campo non conferisce autorità al modello. Warning: « Réponse fondée
   sur cette conversation, sans connaissance confirmée enregistrée. ».
   Copertura parziale e uso di proposte rimangono avvisi indipendenti.
3. **Solo proposte da revisionare**: ogni informazione estratta dal dialogo,
   incluse risposte dell'assistente non verificate. Azione UUM distinta, quote
   esatte e source attribuita, stato proposed, QH-46 per confermare/correggere.
   Nessuna risposta di chat o HTTP 200 cambia la comprensione corrente.

Questa proposta richiede modifica coordinata prompt/DTO/decoder backend/frontend
e test; **non è implementata da questo intervento**. Qualità della risposta,
validità strutturale, costo contabilizzato e conferma umana restano esiti separati.

## CI 9d4a420

Quality: 592 PASS / 1 FAIL / 359 SKIP. Native: 664 PASS / 1 FAIL.
Entrambi rifiutano l'import standard-library `decimal` in `chat/development.py`:
la allowlist del test architetturale era incompleta, non c'è una dipendenza esterna.
Browser: 109 PASS / 2 FAIL. I test chat si aspettavano la cancellazione del dialogo
al cambio di inclusione proposte; il flusso corrente lo conserva. Occorre verificare
che il nuovo turno abbia le nuove fonti e quello storico mantenga le proprie, senza
aspettarsi la rinumerazione a Échange 1. OIDC non eseguito perché dipende da quality.
Non dichiarare questa campagna verde.

La vérification ciblée a ensuite révélé une troisième assertion obsolète, masquée
par le premier échec : l'ancien titre de grande carte « J’ajoute un élément »
n'existe plus dans la composition radiale approuvée. Le test doit vérifier les
six états vides réels et le bouton compact « Ajouter un élément ». Aucun changement
de présentation n'est nécessaire pour ce correctif.


## Primo contratto di risposta — 22 ottobre 2026 (storico, rettificato sotto)

L'owner approva il contratto dell'audit con `support_basis` obbligatorio:

| Valore | Condizioni controllate sugli input effettivamente inviati |
| --- | --- |
| dialogue | Messaggio utente esplicito non vuoto; nessun alias citato; insufficient_context=false. Può esistere contesto canonico disponibile ma non dichiarato come supporto |
| canonical | Almeno un alias esatto, distinto e risolvibile fra quelli trasmessi; insufficient_context=false |
| mixed | Condizioni canonical più presenza del dialogo utente effettivamente inviato; insufficient_context=false |
| insufficient | insufficient_context=true; eventuali riferimenti devono comunque essere validi e possono indicare supporto pertinente ma inadeguato |

Il backend verifica packet/snapshot/record/alias e presenza del dialogo, **non**
entailment o verità del testo. Il frontend verifica il DTO rispetto allo Space,
alla selezione ricevuta e al dialogo della richiesta. La dichiarazione del modello
non è una prova autonoma; nessuna riconciliazione o correzione euristica. Canonical
indica revisioni persistite autorizzate, anche proposte se esplicitamente incluse:
non significa automaticamente conoscenza confermata o verità. Stati epistemici e
avvisi su proposte/copertura parziale rimangono indipendenti.

UI: appui déclaré leggibile e avviso per dialogue/mixed: informazioni conversazionali
non confermate/registrate, nessuna memorizzazione automatica. UUM rimane un'azione
distinta; Source/proposte/outbox e review QH46 restano invariati. Autorizzazione,
provenance, struttura JSON, snapshot e plafond restano bloccanti. Nessun fallback
al vecchio protocollo: campo assente o incoerente viene respinto. Le evidenze storiche
non vengono riscritte. Il precedente divieto di implementazione era un gate ora
soddisfatto, non una regola funzionale permanente.

La sola verifica reale autorizzata da questo mandato usa il modello pinned
mistral-small-2603 e l'endpoint già approvato, una richiesta sintetica entro il
plafond residuo, prenotazione massima USD0.0024, zero retry/fallback. Nessuna
inferenza di startup o test automatico/CI; payload e JSON sanitari fittizi rimangono
privati. Le altre prove usano provider simulato. Non estende disponibilità o budget.


## Rettifica owner successiva — provenienza e sufficienza indipendenti

La precedente matrice accoppiava erroneamente `insufficient_context` a
`support_basis == insufficient`. Questa equivalenza è ritirata dalla decisione
esplicita del Product Owner: provenienza e sufficienza sono indipendenti.
`dialogue / true / []` è ammesso e mostrato con avvisi, senza conoscenza automatica.
Canonical/mixed mantengono citazioni valide obbligatorie anche con flag true;
JSON, scope, owner, provenance, snapshot e plafond restano bloccanti. La struttura
DTO non cambia. Nessuna nuova inferenza o retry per questa correzione.
[Contratto corrente](qh-51-response-support.md).
