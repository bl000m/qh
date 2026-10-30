# PDF → UUM → guest: unico scenario sintetico

Esito complessivo: **FAIL, fedeltà completa non dimostrata**. Base `3eaf9f7`;
correttivo circoscritto alla serializzazione delle evidenze già approvate.
Nessuna rigenerazione o modifica di RH propre, RH 2 o snapshot reali.

## Corpus e percorso eseguito

[corpus.json](corpus.json) fissa prima delle chiamate 11 gruppi di fatti, le
citazioni attese e tre domande naturali. I due originali effettivamente importati
sono [CV](cv-alex-synthetique.pdf) e [progetto di contratto](projet-contrat-synthetique.pdf),
una pagina ciascuno. Ogni riga del corpus è stata ritrovata esattamente nel testo
estratto da `adapters.pdf.extract_pdf`.

Il runner manuale privato ha usato `ContextConsolidation.import_pdf` e
`ContextConsolidation.consolidate`, `DevelopmentAI`, il singolo Engine UUM,
`PostgresConsolidationRepository` e la proiezione Neo4j. Il database PostgreSQL,
il grafo e il Context Space erano nuovi e usa e getta. Sono stati inizializzati
con lo schema esistente, senza nuove migrazioni o operazioni sul runtime reale.
Un'identità di harness verificata riproduce il contesto applicativo del proprietario;
non è una nuova verifica del login browser/OIDC. La consegna email OTP è locale.

Una sola consolidazione reale, una sola chiamata di estrazione/sintesi, 10 elementi
proposti persistiti. Una nuova istanza di repository li ha riletti da SQL; tutti
gli offset/citazioni corrispondono esattamente alle SourceRevision originali e
nessun elemento è stato confermato automaticamente. Nessun elemento è stato
eliminato fra risposta candidata, validazione e persistenza.

Due snapshot sono stati preparati e approvati con i servizi produttivi:
entrambi i PDF (10 elementi), solo CV (5 elementi, 5 esclusioni documentali).
In questo scenario l'approvazione delle citazioni è esplicita (`include_quotes=True`).
Invito, OTP, sessione, autorizzazione e `GuestSnapshotChat.ask` usano i servizi e
repository produttivi. Gli snapshot restano gli stessi anche dopo il correttivo.

Le domande del corpus sono: D1 ultime due esperienze, ruoli e periodi; D2 freelance
e attività associate ai tre incarichi; D3 datore, ruolo, date, durata, retribuzione,
orario, telelavoro, clausola Neptune, condizioni e stato del contratto.

## Tabella dei fatti

U1–U10 identificano, solo per questo resoconto, gli elementi riletti da SQL.
Le citazioni fra virgolette sono esatte; tutti gli ancoraggi sono alla pagina 1.
PASS indica il controllo realmente eseguito, non una garanzia per altre domande.

| Fatto nel PDF | Understanding Item persistito | Provenance esatta | Risposta alla domanda | Esito |
|---|---|---|---|---|
| C1: Orbite, ricerca, settembre 2023–oggi | U10 conserva ruolo, azienda, periodo e attività | CV: "Orbite - Ingenieur de recherche - septembre 2023 a ce jour." | D1 entrambi e CV: primo incarico corretto | PASS |
| C2: freelance full-stack, gennaio 2022–agosto 2023 | U3 conserva periodo, cliente Nova e Lumen | CV: "Freelance - Developpeur full-stack - janvier 2022 a aout 2023." | D1 CV corretto; D1 entrambi omette il freelance, prima **e dopo** il correttivo. D2 lo recupera | **FAIL recupero/ordine** |
| C3: Amarante, coordinamento data/digital, giugno 2018–dicembre 2021 | U7 conserva ruolo, azienda e periodo | CV: "Amarante - Coordinateur data/digital - juin 2018 a decembre 2021." | D2 nei due perimetri corretto; D1 entrambi lo sceglie erroneamente come secondo più recente | **FAIL selezione cronologica** |
| C4: Atlas/Matomo/Prometheus appartengono a Orbite | U10 conserva il collegamento | CV: intestazione C1 + "Dans cet emploi chez Orbite : projet Atlas, deploiement Matomo et monitoring Prometheus." | D2 entrambi e CV corretto | PASS |
| C5: Lumen/Rails/PostgreSQL per Nova appartengono al freelance | U3 conserva il collegamento | CV: intestazione C2 + "Client de cette mission freelance : association Nova. Projet Lumen : portail Ruby on Rails et PostgreSQL." | D2 entrambi e CV corretto | PASS |
| C6: CRM/Sendinblue/SQL appartengono ad Amarante | U7 conserva il collegamento | CV: intestazione C3 + "Dans cet emploi chez Amarante : migration CRM vers Sendinblue et analyses SQL." | D2 entrambi e CV corretto | PASS |
| K1: Helios, ingegnere software proposto, contratto non firmato | U5 conserva datore/ruolo proposti; U1 conserva non firma e assenza di efficacia | Contratto: "Employeur propose : Helios. Poste propose : ingenieur logiciel."; "STATUT : NON SIGNE. Ce projet ne constitue pas un engagement effectif." | D3 entrambi prima/dopo distingue proposta e contratto efficace | PASS |
| K2: inizio previsto 1 marzo 2027, CDI senza fine fissata | U5 conserva l'inizio; **CDI e assenza di fine sono solo nella citazione, non nel testo semantico** | Contratto: "Debut envisage : 1er mars 2027. Projet de CDI, sans date de fin fixee." | D3 prima omette la durata; dopo recupera correttamente CDI e assenza di termine | **FAIL registrazione semantica; recupero dopo PASS** |
| K3: 54.000 euro lordi annui proposti | U8 conserva importo, periodicità, lordo e proposta | Contratto: "Remuneration proposee : 54 000 euros bruts par an." | D3 entrambi prima/dopo corretto, con non efficacia esplicita | PASS |
| K4: proposta 35 ore e 2 giorni di telelavoro settimanali | U9 conserva quantità, frequenza e proposta | Contratto: "Temps de travail propose : 35 heures par semaine ; deux jours de teletravail par semaine." | D3 entrambi prima/dopo corretto | PASS |
| K5: Neptune, premio900 proposto solo su giustificativi | U4 conserva importo/condizione; **il nome Neptune resta solo nella citazione** | Contratto: "Clause Neptune : prime de mobilite proposee de 900 euros, uniquement sur justificatifs de demenagement." | D3 prima nega la presenza del nome; dopo lo recupera insieme alla condizione | **FAIL registrazione semantica; recupero dopo PASS** |

Controlli aggiuntivi: U6 trasforma la formazione 2022–2024 in formazione **"en cours"**,
stato non affermato dalla fonte. U2 conserva invece correttamente il desiderio Rust
senza iscrizione decisa. Diverse risposte D1/D2 sono in francese o miste benché la
domanda sia italiana: anche la coerenza linguistica resta imperfetta.

Con solo CV, D3 dopo il correttivo ha `insufficient_context=True`; nel payload non
entrano datore Helios, stipendio, date o clausole del contratto. La risposta non
divulga questi fatti, ma associa indebitamente la richiesta contrattuale alla
formazione Rust. Ripetere "Neptune", già nella domanda, non è recupero dal contratto.
**Isolamento documentale PASS; pertinenza completa della risposta FAIL.**

## Passaggi responsabili e correttivo

L'estrazione perde parte della semantica di K2/K5 nel testo e introduce lo stato
non supportato di U6. Le citazioni originali rimangono esatte; né la validazione
strutturale né SQL certificano l'equivalenza semantica del testo proposto.

Separatamente, `question_payload` eliminava tutte le citazioni anche quando già
incluse nello snapshot approvato. Il correttivo trasmette quelle sole citazioni
come `evidence_quotes` sotto il rispettivo alias, eliminando duplicati identici.
Nessun accesso ai PDF, nessuna ricostruzione da cronologia, nessuna estensione di
autorizzazione, nessun arricchimento dello snapshot. Senza approvazione delle
citazioni il payload rimane senza evidenze: questo limite è intenzionale.

La stessa D3 reale, sullo stesso snapshot, recupera ora durata e clausola. Per D1
entrambi, invece, U3/freelance e periodi sono presenti anche nel payload HTTP: la
perdita avviene nella **selezione della risposta**, non in SQL o nella Projection.
Un accesso ulteriore al PDF non è necessario per questo caso e non è stato aggiunto.
Non è stata introdotta una regola ad hoc per ordinare lavori tramite parole chiave,
né una riparazione automatica dei fatti proposti o un altro strato RAG.

## Chiamate, contabilità e verifiche

- **9 HTTP Mistral Small reali**, tutti 200/completati: 1 consolidazione, 5 risposte
  iniziali, 3 verifiche dopo il correttivo. Nessun retry automatico.
- Un ulteriore tentativo è stato riservato ma bloccato **prima dell'HTTP** dal runner:
  un controllo cercava "Neptune" anche nella domanda, invece che nel solo snapshot.
  Quindi 10 tentativi nel ledger, ma 9 chiamate reali. Il controllo è stato corretto.
- Costo osservato delle 9 chiamate: **0,00525975 USD**. La riserva fallita di
  **0,1572864 USD** rimane integralmente impegnata, separata dal costo osservato.
  Lo sblocco è stato esplicitamente autorizzato dal proprietario ed è registrato;
  storico, record fallito, consumi e limiti precedenti sono conservati.
  Ledger finale non bloccato, nessun tentativo pending.
- 58 test offline mirati passati: source confidentiality, guest answer contract,
  guest references, guest Mistral simulato e document semantic permissions.
  Ruff sui tre file Python modificati: PASS. Nessuna Full Verification.
- Replay offline delle due proiezioni effettive: CDI/Neptune raggiungono il modello
  solo con entrambi i documenti autorizzati. Il test negativo copre assenza di
  approvazione delle citazioni, esclusione del documento, ritiro dell'accesso,
  deduplicazione e immutabilità dei dati di partenza. I casi esistenti di revoca e
  scadenza restano verdi.

Questo scenario non chiude la fedeltà end-to-end: restano la selezione cronologica
errata con entrambi i documenti, le omissioni nel testo semantico UUM, lo stato
formativo inventato e l'associazione gratuita a Rust. Gli elementi reali preesistenti
non sono stati corretti o rigenerati. Raw JSON/payload privati non sono pubblicati.
Database e grafo usa e getta sono stati rimossi al termine. Le catture aggiuntive
del runner e il suo env file privato sono eliminati prima della pubblicazione;
i diagnostici del provider mantengono la normale retention privata di un'ora.
