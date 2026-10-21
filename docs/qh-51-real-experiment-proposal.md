# QH-51 — Richiesta di esperimento reale circoscritto

**PROPOSTA, NON AUTORIZZATA. Nessuna chiamata Mistral reale eseguita.**
Preparata il2026-10-21. L’approvazione tecnica/review isolata non autorizza questa
spesa, disclosure esterna o attivazione VPS.

## Ambito e dati esatti da approvare

Massimo **5 richieste HTTP:1 GET di preflight e4 POST di inferenza**, una sola
sessione di prova entro30 minuti dall’attivazione. Provider Mistral AI, endpoint
`POST https://api.mistral.ai/v1/chat/completions`, modello datato
**`mistral-small-2603`**, senza alias/fallback, temperatura0, JSON object e
`max_tokens=2000` per richiesta. Nessuna ripetizione automatica o prova alternativa.

Le quattro richieste complete, con prompt, testi, identificativi sintetici, locator,
vocabolario e SHA-256, sono già esportate **senza rete** in
[experiment-payloads.json](evidence/qh51-20261021/experiment-payloads.json).
Si riproducono con `scripts/prepare_qh51_experiment.py`, che non contiene un client
HTTP e usa un Capture provider in memoria. I4 body JSON sono il perimetro esatto;
nessun dato dei Context Space reali del VPS viene letto o trasmesso.

| POST | Space isolato | Dati |
| --- | --- | --- |
| 1 | Bien-être sintetico |3 turni su sonno, serata calma, camminata, schermi ed energia; vocabolario iniziale vuoto |
| 2 | Projet professionnel sintetico |3 turni su isolamento dati, API, PostgreSQL, audit e disponibilità; vocabolario iniziale vuoto |
| 3 | Stesso Bien-être sintetico | « Je conserve cet objectif de sommeil. »; nomi sintetici espliciti Sommeil/Activité physique/Habitudes de vie/Énergie |
| 4 | Stesso Projet professionnel sintetico | « Nous conservons cet objectif d’isolation des données par service. »;5 nomi sintetici espliciti riportati nel JSON |

I vocabolari delle richieste3/4 provengono da assegnazioni di riferimento sintetiche
esplicite, non da output precedenti non revisionati. Consentono payload congelati
prima dell’approvazione e una misura del riuso dei nomi; non introducono una
classificazione globale o una nuova lettura dei dati personali. Eventuali output
nuovi non ampliano il payload autorizzato delle chiamate successive.

## Costi e limiti amministrativi

Verifica delle fonti ufficiali il2026-10-21: la
[scheda Small4](https://docs.mistral.ai/models/mistral-small-4-0-26-03) identifica
`mistral-small-2603`; il
[listino standard](https://docs.mistral.ai/inference/pricing) riporta
**0,15 USD/M input e0,60 USD/M output**. Nessuno sconto cache/batch presunto.

Budget proposto **massimo0,02 USD cumulativi e4 POST**, inclusi tentativi falliti;
non4 successi più retry. Bound amministrativo per richiesta: input<=8000 token,
output<=2000. A listino verificato il massimo teorico è
`4 × (8000 ×0,15 +2000 ×0,60) /1.000.000 =0,0096 USD`.
I payload esportati hanno un bound conservativo in byte più overhead inferiore
alla soglia input; verificare i contatori reali restituiti. Cambi di prezzo,
modello, endpoint, dato, budget o rischio di eccedenza fermano l’esperimento.

Prima dell’invio generare automaticamente manifest, hash e autorizzazione
specifica **purpose=QH-51 semantic extraction**; conservare request/response raw,
usage e receipt in evidenza privata. Contatore cumulativo dedicato e append-only
per questo nuovo esperimento, con prenotazione del costo massimo prima di POST;
mai azzerare, clonare come nuovo budget o riscrivere ledger/contatori QH-45.
Questa è una nuova allocazione economica esplicita da approvare, non un’estensione
implicita dell’allowlist/chat grant esistente. Nessuna modifica VPS è inclusa.

## Disponibilità: cosa è verificato e cosa manca

Alla lettura del2026-10-21 lo
[stato pubblico Mistral](https://status.mistral.ai/) indica sistemi operativi;
la credenziale locale risulta presente (verificato solo come booleano, mai esposta).
**L’accesso effettivo dell’account, il credito e la quota del modello non sono
certificati**: il mandato vieta ancora chiamate Mistral reali, quindi non sono stati
eseguiti neppure GET autenticati. Lo stato pubblico non garantisce la quota privata.

L’approvazione richiesta comprende al massimo **un GET autenticato `/v1/models`**
per verificare il modello. Se non disponibile, fermare prima delle inferenze.
Il GET non prova il credito: la prima POST è anche lo smoke, conta fra le4 e deve
fermare l’intero esperimento in caso di401/403/429/timeout/risposta inattesa.
Nessun retry, fallback o allargamento di autorizzazioni per superare un limite.
Ri-verificare prezzo/stato immediatamente prima dell’attivazione autorizzata.

## Evidenze e accettazione

Usare soltanto nuovi Space/database/namespace isolati con le identità sintetiche
Alice/Bob. L’Engine rimane quello verificato dalla PR QH-51: output raw immutabile,
risoluzione citazioni come derivazione separata, batch proposed atomico e review
QH-46. Output invalido/troncato non pubblica fratelli validi. Mai usare il normale
chat grant per autorizzare questa diversa disclosure.

Misurare separatamente: atomicità/fedeltà delle interpretazioni; pertinenza e
copertura dei temi/appartenenze multiple; corrispondenza esatta delle citazioni;
riuso dei nomi/false fusioni/split. L’owner annota la qualità semantica reale,
indipendentemente dai controlli automatici dei locator. Richiedere confronto
visibile fra i due Space, ruolo comune sotto temi differenti, rigetto selettivo
con fonte conservata, refresh e isolamento. Nessuna conferma implicita.

Le metriche delle fixture della PR sono controlli di conformità, **non** una prova
della qualità del modello. DONE prodotto resta subordinato a questa prova reale,
valutazione owner e dimostrazione convincente; integrazione della PR e attivazione
persistente rimangono decisioni separate.

Richiesta finale da sottoporre all’owner dopo la verifica tecnica: autorizzare
esclusivamente questi4 payload, il singolo GET di preflight, il modello/endpoint
indicati, massimo4 POST/0,02 USD e raccolta delle evidenze descritte. Nessuna spesa
è autorizzata dalla sola pubblicazione di questo documento.
