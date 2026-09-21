---
name: company-conventions
description: Conventions d'ingénierie de l'entreprise — messages de commit, logging, templates de PR, revue de code
user-invocable: true
---

# Conventions d'ingénierie — Caisse des Dépôts

## Messages de commit
Suivre le format des commits conventionnels :
```
<type>(<scope>): <subject>

<body>
```

Types : `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`
Scope : module ou zone concernée (par ex. `health`, `auth`, `deploy`)
Sujet : à l'impératif, en minuscules, sans point final

Exemple :
```
fix(health): handle service unavailability gracefully

The health check endpoint was returning 500 when the workflow
service was down. Now returns degraded status with error details.
```

## Logging
- Utiliser un logging structuré avec des kwargs — jamais de f-strings dans les
  messages de log
- Pattern : `logger.info("action description", key1=value1, key2=value2)`
- Toujours inclure un champ `name` pour le service/module d'origine
- Niveaux de log : DEBUG pour le flux interne, INFO pour les événements métier,
  WARNING pour les problèmes récupérables, ERROR pour les échecs

## Template de Pull Request
```markdown
## Contexte
Pourquoi ce changement est nécessaire.

## Implémentation
Décisions de conception clés et compromis.

## Vérifications
- [ ] Les tests passent
- [ ] Aucune régression
- [ ] Conventions respectées (logging, gestion des erreurs, types)
```

## Checklist de revue de code
Lors d'une revue de code, vérifier :
- [ ] Gestion des erreurs : tous les appels externes enveloppés, aucun 500 brut
- [ ] Logging : structuré avec kwargs, niveaux appropriés
- [ ] Types : toutes les fonctions publiques ont des annotations de type
- [ ] Tests : le nouveau code a des tests, les corrections de bug ont un test de
  régression
- [ ] Sécurité : aucun secret dans le code, pas d'injection SQL, validation des
  entrées correcte

## Spécificités CDC
- **Revue de code obligatoire** : toute modification passe par une PR relue par au
  moins un pair avant merge — aucun push direct sur les branches protégées.
- **Gestion des secrets** : jamais de secret dans le code ni dans les logs ; utiliser
  des variables d'environnement ou un gestionnaire de secrets (voir la skill
  `security-review`).
- **Souveraineté** : les données et l'exécution restent en Europe. Toute dépendance
  ou service externe qui déroge à ce principe doit être signalé et validé.
- **Traçabilité** : les actions sensibles sont journalisées (voir le hook
  `compliance-log` dans `.vibe/hooks.toml`).
