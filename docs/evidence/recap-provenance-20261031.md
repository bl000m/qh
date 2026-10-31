# Provenance du résumé canonique — vérification ciblée

Branche `feat/QH-18-21-22-demo-b`, PR #29, sans merge.
Le plafond de deux supports a déjà été supprimé dans `7e637ee`.

## Correctif après le test manuel de mémorisation

Diagnostic privé lu sans nouvelle génération, le 31 octobre, heure de Paris :

- 08:51 : extraction et support exact du résumé acceptés, HTTP 200 ; la revue
  finale est rejetée par `uum.recap_claim_review`. Tous ses verdicts sont positifs
  et les spans couvrent le texte, mais elle sélectionne 7 des 21 supports déclarés
  du résumé général (14 inutilisés), et 14 des 15 du premier composant. La règle
  ajoutée par `1abd4e8`, `Unused recap supports`, transforme cette appréciation de
  minimalité en échec de toute la mémorisation. Ce n'est pas une citation inventée.
- 08:53 : deuxième échec, avec des verdicts négatifs ; le replay des spans montre
  aussi des chevauchements et un titre positif sans preuve sélectionnée. Ces
  violations structurelles demeurent bloquantes, même avec un verdict informatif.

Le correctif rend les verdicts négatifs et les supports déclarés inutilisés
**informatifs**. Il conserve le résumé naturel et tous ses supports d'origine,
avec `review_assessment.status=inconclusive`, sans preuve v4 ni privilège de
divulgation affinée. Le fallback de partage reste conservateur. Schéma, couverture,
citations, appartenance des preuves et publication atomique restent obligatoires.
Le test de non-régression couvre une publication atomique après verdict négatif,
la conservation de tous les supports, et le rejet d'un chevauchement même si le
verdict est négatif. Aucun appel payé ou changement des données réelles.
Vérification du correctif : 91 tests API ciblés passent, ainsi que Ruff et lint
TypeScript. Pas de nouvelle génération réelle ni de Full Verification.

Les sections suivantes documentent les vérifications initiales de `1abd4e8` ;
le rejet sur simple verdict négatif décrit ci-dessous est remplacé par cette règle V1.

## Vérification initiale de `1abd4e8`

La nouvelle présentation v4 conserve un seul résumé libre. Une revue sémantique
indépendante évalue ses assertions contre les statements déclarés et des citations
originales prévalidées. Les contrôles locaux imposent couverture complète des spans,
références exactes, correspondance citation/statement, absence de support inutilisé,
empreintes et appartenance à la version/source. La publication est atomique après
acceptation de toutes les composantes, sans réécriture ni retry automatique.
La génération peut proposer du texte ; elle ne peut pas s'auto-attribuer la revue.

Le jugement d'entailment et la granularité des assertions restent probabilistes.
Les tests de replay contrôlent le protocole, pas la vérité des verdicts simulés.
Le Guard conserve texte, masquages, présence de la base et contrôles d'autorisation.
Il inspecte tous les supports/citations nécessaires d'un résumé v4 révisé ;
il ne bloque pas à cause d'un item protégé étranger aux assertions. Une citation
originale trop large et sensible reste bloquante : elle n'est pas tronquée.

## Vérifications

143 tests API ciblés passent (replay offline, invariants de provenance/disclosure,
publication atomique et chemin PDF/consolidation concerné). Quatre tests browser
du diagnostic, lint TypeScript et Ruff passent également. Aucun de ces replays
n'effectue d'inférence payante ou d'écriture dans le runtime persistant.

- Corpus synthétique : projet proposé non adopté, décision datée adoptée, version
  expérimentale, déploiement conditionnel ; données protégées sans rapport.
- Plus de deux supports conservés avec leurs citations exactes.
- Couverture incomplète, référence/citation étrangère, attribution de citation au
  mauvais statement, support inutilisé et refus sémantique : rejet.
- Texte/support/citation sensibles, version/source modifiée, base absente : rejet.
- Zéro, un ou tous les originaux téléchargeables : même résumé et connaissance.
- Historique v3 sans revue : fallback dans les nouveaux partages V1, sans
  modification des snapshots précédemment approuvés.
- RH examiné exclusivement en version **1 à 36 items**, par transactions read-only :
  résumé owner lisible, 35 items sortants, fallback historique et contenu identique
  pour les trois sélections d'originaux. Aucun appel ni écriture de Compréhension.

## Appels réels autorisés

Deux HTTP `mistral-small-2603`, sans retry automatique :

| Tentative | Entrée / sortie | Coût USD | Résultat |
|---|---:|---:|---|
| 233, autorisation initiale | 735 / 367 tokens | 0,00033045 | Quatre assertions correctes acceptées, assertions inventées refusées ; faux négatif sur le titre descriptif, batch refusé. |
| 234, autorisation supplémentaire explicite | 807 / 459 tokens | 0,00039645 | Après précision de la règle des titres : titre et quatre assertions du candidat positif acceptés avec quatre supports ; les trois parties du candidat négatif refusées. |

La seconde réponse passe les contrôles locaux du composant positif : couverture
du titre/texte, sélection des quatre supports et correspondance des citations.
Le batch contenant aussi le candidat négatif est **correctement refusé**, sans
provenance partielle acceptée. Aucun modèle n'a réécrit le résumé candidat et aucun
résultat négatif n'a été silencieusement supprimé pour publier le reste.

Il s'agit d'une **revue réelle de candidats synthétiques**, pas d'une consolidation
PDF productive ni d'une écriture SQL réelle. Génération, liaison aux révisions,
lecture du résumé canonique persistable et Projection sont testées offline avec
verdicts contrôlés ; ces replays ne sont pas présentés comme un test sémantique réel.

Coût observé total : **0,00072690 USD**. Les deux tentatives sont HTTP 200/completed.
Ledger non bloqué, zéro pending, historique/plafonds et réserve technique de
0,1572864 USD conservés. Aucun déblocage/reset ou nouvel appel hors autorisation.
Les captures temporaires des réponses sont supprimées après vérification ; les
diagnostics privés ordinaires gardent leur portée authentifiée et rétention d'une heure.

Aucune régénération des PDF réels, migration ou Full Verification. Les données de
RH/RH propre/RH 2 et les snapshots approuvés ne sont pas des cibles d'écriture.
