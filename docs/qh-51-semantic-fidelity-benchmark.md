# QH-51 — cas à retenir pour le benchmark de fidélité sémantique

Statut : cas signalé par le Product Owner le 22 octobre 2026, à intégrer dans un
futur benchmark. Aucun nouvel appel provider, évaluateur ou second agent introduit
par cette correction. Aucun dossier, prompt complet ou JSON diagnostique copié ici.

| Entrée rapportée | Reformulation erronée observée | Invariant attendu |
| --- | --- | --- |
| « J'ai décidé de commencer un journal » | « Vous avez commencé un journal » | Une décision de commencer ne prouve pas que l'action a commencé |

Une reformulation fidèle peut dire « Vous avez décidé de commencer un journal ».
L'identité de l'acteur, la décision, la temporalité et l'absence de preuve
d'exécution doivent être conservées. Le passage décision → action accomplie est
une affirmation supplémentaire non soutenue par cette seule phrase.

Ce défaut est **sémantique** : un JSON conforme, des alias existants ou une réponse
HTTP 200 n'établissent pas la fidélité du sens. La correction structurelle
support_basis/insufficient_context ne le résout pas et ne doit pas être présentée
comme une validation de qualité du modèle. La réponse originale n'est ni réparée
ni promue automatiquement en connaissance QH.

Critères futurs : pénaliser toute assertion d'action commencée/accomplie sans
évidence distincte ; accepter la décision explicitement conservée ; séparer ce
score des contrôles JSON, citations, admission et review humaine. Prévoir aussi
les variantes négatives, conditionnelles, attribuées à un tiers et les cas où
une preuve séparée confirme réellement le début de l'action. Ces variantes
restent un plan de benchmark, pas des résultats mesurés.
