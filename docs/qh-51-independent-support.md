# QH-51 — provenienza e sufficienza indipendenti

Mandato owner successivo al candidato f5e4db2, PR23 aperta. Ticket QH-51 e commenti
riletti tramite Atlassian; il mandato corrente rettifica il precedente contratto
di risposta. Nessuna scrittura Jira, modifica PR19 o inferenza reale.

Il caso owner riportato ha HTTP provider200,968 input/445 output e costo
USD0.00041220 completed; QH503 alla regola
`chat.support_basis_matches_transmitted_inputs`, con dialogue/true/[]. Questi sono
metadati riferiti dall'owner, non una nuova chiamata o un replay pagato. Il JSON
originale e il ledger non sono modificati.

La regola `insufficient != (basis == 'insufficient')` confondeva due assi. Era
duplicata nel validatore TypeScript: entrambi rifiutavano dialogue/true/[] prima
di mostrare la risposta. Sono rimossi solo questi vincoli di accoppiamento.

`insufficient_context` conserva il significato di informazioni insufficienti per
una risposta completa; resta booleano, non viene cancellato o ricalcolato dagli
alias. Tutti i valori esistenti di support_basis ammettono entrambi i booleani
alle condizioni del [contratto corrente](qh-51-response-support.md). Nessun nuovo
campo, enum, schema o adapter. Alias canonici esatti obbligatori per canonical e
mixed; presence/membership/owner/snapshot/JSON/budget restano verificati.

La UI usa AnswerSupport sia nel turno Chat sia nel pannello Sources: provenienza,
avviso di incompletezza e avviso di dialogo non confermato sono separati. Nessuna
memorizzazione o review automatica. L'etichetta del valore storico insufficient
diventa « Appui non établi » per distinguerlo dal booleano.

## Criteri verificabili ed evidenze

| Criterio | Classificazione / esito |
| --- | --- |
| dialogue/true/[] ammesso senza coercizione | Implementato e testato / PASS: matrice Python e TypeScript, HTTP con booleano preservato |
| canonical/mixed con flag true mantengono citazioni obbligatorie | Implementato e testato / PASS: matrice Python e TypeScript, HTTP con booleano preservato |
| Dialogo reale inviato, alias e contesto coerenti obbligatori | Implementato e testato / PASS: input/alias/contesto e route autenticata, guard invariati |
| Risposta e due avvisi visibili in Chat e Sources | Implementato e testato / PASS: Chromium reale con Keycloak/API/SQL isolati |
| Nessuna fonte/revisione/conoscenza scritta dalla chat | Implementato e testato / PASS: repository non invocato e history vuota prima di Proposer |
| CI Quality/Native/Browser/OIDC sul candidato finale | NOT TESTED: da eseguire dopo i controlli mirati |
| Caso journal nel futuro benchmark, senza nuovo agente | Documentato: [caso e limiti](qh-51-semantic-fidelity-benchmark.md) |
| Inferenze reali, merge e Jira DONE | Fuori scope; PR23 resta aperta, nessuna chiamata pagata |

Controlli mirati eseguiti nel container candidato, senza rete provider:

- `python -m pytest -q tests/test_chat_support.py tests/test_development_ai.py
  tests/test_ai_diagnostics.py tests/test_chat_sessions.py
  tests/test_chat_sessions_api.py tests/test_chat_context.py
  tests/test_chat_references.py`:159 PASS; Ruff sui file Python cambiati PASS.
- `npm run lint --workspace apps/web`, `npm run build --workspace apps/web`:PASS.
  Playwright `tests/chat.spec.ts tests/ai-diagnostics.spec.ts`:6 PASS.
- `scripts/test_qh11_browser.py` con immagini candidate, `--understanding
  --chat-sessions --product-mode --uum-mode --development-ai-mode
  --browser-grep 'QH-51 ordinary AI' --focused-browser-only`:1 browser PASS,
  inclusi i due avvisi Chat/Sources,0 history prima dell'esplicita estrazione,
  nessun popup, lettura/eliminazione diagnostica e limite economico. Harness OIDC
  isolato1 PASS. Questa esecuzione focalizzata non equivale alla CI completa.

La campagna finale parte dalla pubblicazione del candidato; il suo esito effettivo
è registrato nelle evidenze operative sul medesimo HEAD, senza riscrivere il report
per dichiarare in anticipo un successo.
Evidenza operativa finale, senza contenuti privati:
`.local-archive/qh51-independent-support-20261022/SAFE-RESULTS.md` e relativo JSON.
Il confronto in sola lettura registra tabelle/hash, file protetti, container e
ledger prima/dopo; attività concorrente owner va distinta da scritture del test.
