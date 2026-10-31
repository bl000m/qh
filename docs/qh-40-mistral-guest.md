# Demo B — ASK_AI Mistral reale, attivato il 26 ottobre 2026

Decisione owner: guest verificati tramite OTP possono usare **mistral-small-2603**
nel solo sviluppo privato, sullo snapshot approvato. Il plafond condiviso fra chat,
UUM e guest è **10 EUR cumulativi, storico incluso**, senza quota totale/sessione
di richieste. Questa decisione supera il vincolo offline-only dell'incremento
precedente; test automatici e CI restano offline.

## Percorso attivo

Su [QH privato](https://localhost:5173/), Alice apre **Partager ce Context Space**.
Con ASK_AI selezionato, il provider predefinito disponibile è **Mistral Small — réel**;
resta selezionabile la simulazione locale senza costo. La preview e la singola
approvazione fissano anche il provider nella policy immutabile del nuovo snapshot.
Gli inviti/snapshot precedenti offline non cambiano provider automaticamente.

Clément verifica la mailbox, apre il solo snapshot, scrive e preme **Interroger le
snapshot**: nessun ulteriore popup/grant/consenso per chiamata. La UI indica modello
reale, budget QH residuo, costo e tentativo della risposta. Apertura pagina e polling
non avviano inferenze. OTP/mailbox/HTTPS e porte private rimangono quelli della
[guida Mac](qh-40-private-activation.md): 5173, 8080 e 8025, tutte via tunnel privato.

`GuestSnapshotChat` seleziona il percorso esclusivamente dal grant server-side.
`MistralSnapshotAnswers` riusa `PrivateSessionFactory.bind_global`, l'adapter Mistral,
il ledger QH45 originale e i diagnostici privati response-only a un'ora. Il grant
deve appartenere allo stesso owner di sviluppo e all'approvatore dello snapshot,
con policy ASK_AI, provider esatto, sessione OTP, expiry e revoca valide. Ricontrolli
precedono la prenotazione/invio e seguono la generazione; il payload deve restare
identico. Nessun accesso a fonti integrali, Space live o Neo4j nel percorso guest.

Al modello partono soltanto istruzioni applicative, il payload già minimizzato e
mascherato, e la domanda esplicita. Structured output, alias R esatti senza riconciliazioni,
support_basis e insufficienza indipendenti, filtro di disclosure riutilizzato e
rendering testuale restano separati da verità/qualità semantica. Nessuna scrittura
canonica o conferma automatica. Le regole conservative di disclosure non certificano
anonimato: un output riconosciuto sensibile/identificante può essere rifiutato anche
dopo HTTP200; il costo già sostenuto rimane contabilizzato e diagnosticato.

## Credito e controllo economico effettivi

- Screenshot owner del 26 ottobre: **quota API mensile inclusa EUR8,50, utilizzo
  visualizzato EUR0,01**, circa EUR8,49 residui. È quota inclusa, non una prova di
  saldo prepagato. La chiave standard non espone il saldo billing amministrativo.
- Plafond autorizzato globale **USD5,00**, con la già approvata conversione prudente
  **EUR2/USD**, senza assumere un cambio di mercato. Nessun refill mensile automatico.
- Un margine di un centesimo sul dato visualizzato limita il nuovo consumo alla
  quota osservata EUR8,48, cioè **USD4,24**, al netto delle chiamate QH successive
  all'osservazione. Il credit guard e il plafond globale valgono simultaneamente.
- Il ledger contiene un debit storico esterno conservativo **USD0,01798230**:
  QH8/QH33 condividono un solo ledger finale; i due esperimenti QH13 distinti e
  l'unico POST semantico QH51 sono conteggiati una volta. Copie archiviate, fixture,
  ledger-before e riepiloghi di smoke non sono nuovi consumi. Le prenotazioni
  storiche incerte sono mantenute prudenzialmente. I vecchi file restano immutati;
  registro delle fonti/hash e amendment metadata sono conservati privatamente.
- Tutte le 19 righe pre-smoke del ledger attivo sono identiche; nessuna chiamata
  azzerata, spostata o riscritta. Max_calls è `null`. `committed_cost` comprende
  storico esterno, costi osservati e prenotazioni aperte; `effective_ceiling` applica
  il minimo fra limite QH e guard sul credito, sotto lo stesso lock durabile.
- Ogni invio riserva **USD0,1572864**, il massimo prudenziale della finestra del
  modello, prima di HTTP. Le chiamate ordinarie non impongono max_tokens o microquote
  di sessione. Una prenotazione aperta impedisce doppia spesa concorrente. Restano
  antiabuso 30 tentativi/minuto per sessione, domanda bounded, TTL e capacità tecnica.
  Sono limiti temporali di servizio, non un numero totale di domande autorizzate.
- Insufficienza: HTTP402 prima dell'invio e messaggio **« Plafond IA atteint. Aucune
  nouvelle requête ne sera facturée. »** Nessun fallback o retry automatico. Errori
  HTTP/trasporto mantengono accounting e stop marker; nessuna riapertura automatica.

Preflight: un GET autenticato ha confermato il modello e completion_chat; nessun
POST in questa fase. Il [listino ufficiale Mistral](https://docs.mistral.ai/models/mistral-small-4-0-26-03)
verificato è USD0,15/M input e USD0,60/M output. La verifica prezzi esistente resta
obbligatoria e bounded; modello/listino inattesi chiudono il percorso.

## Esito verificato

| Verifica | Esito |
| --- | --- |
| Unit/economia/contratti esistenti e nuovo percorso simulato, rete disabilitata | 68 PASS; inclusi 21 invii consecutivi senza quota di sessione, alias/citazioni, revoca prima/dopo, costo/credit guard, concorrenza pending e HTTP429 senza retry |
| SQL/Neo4j/OIDC/SMTP mirati con Mistral MockTransport | 32 PASS; ulteriore controllo finale owner-snapshot 1 PASS, sovrapposto |
| Browser completo offline, build/TypeScript | 1 PASS (1.2m), nessuna chiamata pagata; revoca/expiry preservate |
| VPS reale HTTPS → Alice → nuova policy Mistral → mailbox UI/OTP → Clément → snapshot → domanda reale → revoca | PASS; una sola POST reale, nessun retry pagato e nessuna nuova conoscenza canonica |
| Risposta/accounting reale | Tentativo20 completed; 336 token input, 74 output; USD0,0000948; residuo al controllo USD4,23990520 |
| Fedeltà dell'esempio sintetico | Risposta pertinente: obiettivo di preparare un atelier, esplicitamente non confermato; alias R1 valido. Un solo esempio, non benchmark generale di verità |
| Preservazione | Prefisso storico19 righe identico, vecchi ledger/hash e infrastruttura/immagini preservati; schema0009 invariato; inviti sintetici tutti revocati |

JSON Mistral originale nel diagnostico privato, non nel repository/CI/log ordinari;
evidenza operativa e screenshot in `.local-archive/qh40-mistral-20261026/`. Il primo
driver si è fermato su due verifiche UI prima dell'invio: nessun POST/consumo è
stato ripetuto. La singola chiamata reale è protetta da marker esclusivo persistente.
La Full CI verde precedente rimane associata a `ed7f78a`; nessuna nuova campagna
generale è dichiarata su questo delta. Review/merge e accettazione fisica dal Mac
rimangono distinti dalla verifica operativa.

Rollback: `QH_GUEST_MISTRAL_ENABLED=false`, poi guarded `dev-up DEV_SERVICE=backend`.
Gli snapshot reali diventano indisponibili per ASK, senza fallback alla simulazione;
READ resta governato. Non ripristinare il vecchio ledger, non ridurre/azzerare storia
o prenotazioni, non cambiare schema o riscrivere policy immutabili. Le chiavi restano
server-side e l'abilitazione privata richiede sempre la receipt owner verificata.
