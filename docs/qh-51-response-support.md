# QH-51 — supporto dialogico e canonico


## Contratto di risposta approvato — 22 ottobre 2026

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

Il protocollo iniziale di verifica reale usa il modello pinned
mistral-small-2603 e l'endpoint già approvato, una richiesta sintetica entro il
plafond residuo, prenotazione massima USD0.0024, zero retry/fallback. Nessuna
inferenza di startup o test automatico/CI; payload e JSON sanitari fittizi rimangono
privati. Le altre prove usano provider simulato. Non estende disponibilità o budget.


Il primo protocollo live a invio singolo è stato fermato su un formato reale errato
(reference_aliases object invece di array), conservando costo/JSON/stop marker.
Il mandato owner sul plafond attuale copre una verifica controllata del candidato
corretto: stesso payload/Space, un nuovo Envoyer dopo test offline/CI verde,
prenotazioneUSD0.0024 e nessun retry/fallback automatico. Nessun errore del modello
viene convertito euristicamente o cancellato dal ledger. Il prompt esplicita array
ed esempio vuoto, mentre il decoder continua a rifiutare anche l'object vuoto{}.
