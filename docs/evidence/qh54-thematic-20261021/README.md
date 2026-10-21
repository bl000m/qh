# QH-54 — Evidenza della correzione tematica

Cinque schermate reali di Chromium, dati sintetici e stack disposable con Keycloak,
PostgreSQL e Neo4j; nessuna scrittura demo o inferenza esterna. Empty e populated
restano distinti, ma nessun titolo di revisione diventa un nodo tematico.

- [Populated desktop](populated-desktop.png), [mobile](populated-mobile.png),
  [viewport ridotto](populated-zoom200.png).
- [Empty desktop](empty-desktop.png), [mobile](empty-mobile.png).
- [Risultati mirati](targeted-results.txt) e [hash sorgenti/immagini/catture](captures.json).

Le vecchie catture `../qh54-maquettes-20261021` sono conservate come evidenza
storica: i sei nodi di revisione non rappresentano il prodotto approvato dopo
l’audit. Il manifesto nuovo confronta il sorgente frontend nell’immagine realmente
eseguita con il checkout; non pubblica configurazioni/diagnostiche runtime,
credenziali, payload del ledger o dati canonici del VPS.

La campagna CI completa e lo stato finale sono nel
[rapporto di stabilizzazione](../../qh-54-thematic-stabilization.md).
