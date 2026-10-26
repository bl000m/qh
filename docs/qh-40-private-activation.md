# Demo B privata — attivazione eseguita il 25 ottobre 2026

L'owner ha autorizzato migrazioni additive e attivazione privata; ha poi approvato
separatamente le due aggiunte HTTPS al client Keycloak `qh-web`. Questa esecuzione
supera il precedente gate di sola preparazione in [QH-40](qh-40-demo-b.md).
**Schema persistente 0009, Sharing/Guest e mailbox sandbox sono attivi. Nessun reset.**

## Accesso dal Mac

In VS Code Remote SSH inoltrare con visibilità **privata**, mantenendo gli stessi
numeri locali, le porte **5173, 8080 e 8025**. Non usare un tunnel pubblico.
Non è necessario inoltrare 8000: il browser usa il proxy HTTPS `/api`.

| Uso | URL locale sul Mac |
| --- | --- |
| QH / Sharing / Guest | **https://localhost:5173/** |
| OIDC esistente | http://localhost:8080/realms/qh |
| Mailbox sandbox | **http://localhost:8025/** |

Prima dell'accesso, copiare sul Mac il solo certificato pubblico
`.local-archive/qh40-activation-20261025/qh-local-ca.crt`, disponibile dal checkout
remoto. Importarlo in **Accesso Portachiavi → login**, verificare il fingerprint
SHA-256 contro quello del file remoto, e autorizzarlo per SSL. Chiudere e riaprire
il browser se necessario. Non copiare chiavi private o `.env`. La CA privata dura
90 giorni e il certificato localhost 30 giorni; il rinnovo è un intervento locale
esplicito, non un rinnovo automatico. Il sito usa `localhost`, non l'IP pubblico VPS.

Login Alice con le credenziali abituali, invariate. Per provare il percorso:

1. Aprire o creare un Context Space e conservarvi un testo sintetico manuale.
   È disponibile anche `Vérification Sharing HTTPS — synthétique`, creato dalla
   verifica operativa con un solo testo manuale non confermato.
2. Nel riquadro **Actions utiles**, sopra mappa/chat, premere l'unico
   **Partager ce Context Space**. Inserire `clement@example.test`, finalità e scadenza.
3. Se il contenuto è soltanto proposto, scegliere **Inclure les Propositions, sans
   les confirmer**. Preparare la preview; esaminare contenuti minimizzati, esclusioni,
   mascheramenti e il rischio residuo esplicitamente nominato. Approvare la disclosure.
4. Copiare il link creato in una finestra privata: il link da solo non mostra contenuti.
   Inserire `clement@example.test`, richiedere il codice e leggerlo nella mailbox
   sandbox. Inserire il codice nella pagina guest; consultare il solo snapshot.
5. Se ASK_AI è stato scelto, il pulsante usa una **simulazione locale dichiarata**,
   con estratti del solo snapshot. Non è un'inferenza reale e non comporta costi.
6. Da Alice revocare l'invito. Il backend nega subito le nuove richieste; la pagina
   guest aperta elimina il contenuto al successivo controllo, entro circa tre secondi.

La mailbox cattura localmente le email, senza relay: **nessuna consegna a caselle
esterne**. Tutti i messaggi della sandbox sono visibili a chi possiede questo
accesso SSH privato; serve a interpretare entrambi i ruoli della demo, non è una
casella personale di produzione. SMTP non ha una porta pubblicata; la UI 8025 è
legata solo a 127.0.0.1. I messaggi stanno in tmpfs, massimo 200, persi al riavvio.
OTP monouso cinque minuti, sessione guest massimo trenta minuti e sempre entro
l'expiry dell'invito; limiti invii/tentativi e revoca rimangono durevoli in PostgreSQL.

## Operazioni e verifiche eseguite

- Backup SQL completo e globals 0600, conservati fuori Git; ripristino isolato
  PASS e upgrade della copia 0006→0007→0008→0009 PASS, con fingerprint originali
  preservati. Poi stesso upgrade additivo sul database persistente, senza cancellazioni.
  Il backup verificato è in `.local-archive/qh40-activation-20261025/`.
- Keycloak: soltanto `https://localhost:5173/oidc/callback` aggiunto a `redirectUris`
  e `https://localhost:5173` a `webOrigins`. Valori HTTP precedenti conservati;
  gli insiemi riletti e tutti gli altri campi sono stati confrontati. Keycloak ha
  riordinato `webOrigins`, senza ulteriori differenze. Nessun riavvio o cambio TTL,
  utenti/password, mapper, issuer o import readonly.
- Guarded `dev-stop` / `dev-up` soltanto frontend/backend; stesse immagini pin.
  Overlay esplicito `qh-private-sharing.yml`, flag frontend e factory opt-in,
  chiave verifier privata, TLS e trust proxy vincolato all'esatto IP frontend.
  Il proxy sostituisce gli header di forwarding forniti dal chiamante. Porte QH
  solo loopback; servizi/volumi infrastrutturali e ledger/autorizzazione IA preservati.
- **27 PASS** nei test mirati di configurazione/guard/privacy; Ruff e whitespace PASS.
  **1 scenario browser isolato PASS** (1.2m), build/TypeScript PASS: unica azione
  funzionante in viewport, un solo dialogo, SMTP/OTP, snapshot, revoca e expiry.
- **Browser sul VPS reale PASS**: HTTPS/catena privata, login OIDC Alice, un solo
  Space sintetico e una proposta manuale tramite UI, preview/approval, SMTP reale,
  codice letto nella UI mailbox, cookie Secure/HttpOnly/SameSite Strict, refresh,
  guest negato sullo Space, ASK offline e revoca della sessione aperta. Nessuna IA
  pagata o modifica guest ai dati canonici. Tutti gli inviti di verifica sono revocati.
- Il client di verifica inizialmente non conosceva la CA per le richieste API Node;
  è stato corretto usando la CA esplicita, senza indebolire il TLS applicativo.
  Un cookie sintetico incluso nel diagnostico è stato revocato e il diagnostico
  redatto. Nessun segreto è incluso in Git, CI o in questo documento.
- Riutilizzata la Full CI verde [40204911173](https://github.com/bl000m/qh/actions/runs/40204911173)
  sul precedente `ed7f78a`: Quality/OIDC/Native/Browser SUCCESS. Il successivo delta
  UX/attivazione usa le verifiche mirate sopra; non si attribuisce quella Full al
  nuovo commit e non è stata avviata un'altra campagna generale.

La prova fisica dal Mac e l'accettazione owner restano da eseguire. OIDC mantiene
l'issuer HTTP loopback esistente, veicolato nel tunnel SSH, mentre QH/guest usa HTTPS.
Questo è un POC privato sintetico: nessun servizio pubblico, anonimizzazione
universale, email esterna, IA guest reale o diritto di contribuzione è promesso.

## Rollback applicativo non distruttivo

1. Fermare soltanto le due app con `sudo -n make dev-stop`.
2. Rimuovere da `.env` soltanto le due aggiunte `QH_PRIVATE_SHARING` e
   `QH_SHARING_FRONTEND_IP`, preservando ogni altra configurazione corrente.
3. Ripristinare le app con `sudo -n make dev-up`: overlay standard, frontend HTTP
   originale e factory senza Sharing/Guest. Mantenere schema 0009, chiave privata,
   snapshot, inviti, contatori e revoche; **nessun downgrade o restore del database**.
4. Se desiderato, fermare soltanto il nuovo container `qh-guest-mailbox` dopo averne
   verificato label/immagine. I messaggi tmpfs si perdono; non riaprire guest su un
   vecchio backup. Il rollback ordinario non rimuove volumi o ledger.
5. Le due aggiunte HTTPS Keycloak possono rimanere inattive, oppure essere rimosse
   con un delta inverso circoscritto dopo rilettura; mai ripristinare l'intero realm.
   L'eventuale fiducia alla CA sul Mac si rimuove manualmente dal Portachiavi.
