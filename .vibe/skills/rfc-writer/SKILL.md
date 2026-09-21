---
name: rfc-writer
description: Rédiger des RFC techniques et des documents de conception suivant le template standard
user-invocable: true
---

# Rédacteur de RFC

Lorsqu'on vous demande de rédiger une RFC ou un document de conception, suivre cette
structure :

## Template

```markdown
# RFC : <Titre>

**Auteur :** <nom>
**Direction :** <direction / entité CDC>
**Date :** <date>
**Statut :** Brouillon
**Classification :** <publique / interne / confidentielle>
**Impact sécurité / souveraineté :** <résumé de l'impact ; données et exécution en Europe ?>

## Contexte

Quel est le problème ou l'opportunité ? Pourquoi prend-on cette décision maintenant ?
Inclure les métriques, incidents ou retours utilisateurs pertinents qui l'ont motivée.

## Décision

Que fait-on ? Décrire l'approche retenue clairement et de façon concise.
Inclure des schémas d'architecture ou des extraits de code lorsque c'est utile.

## Alternatives envisagées

| Alternative | Avantages | Inconvénients | Pourquoi écartée |
|------------|-----------|---------------|------------------|
| Option A | ... | ... | ... |
| Option B | ... | ... | ... |

## Conséquences

### Positives
- Qu'est-ce qui s'améliore ?

### Négatives
- Quels compromis acceptons-nous ?

### Risques
- Qu'est-ce qui pourrait mal tourner ? Comment l'atténuer ?

## Plan d'implémentation

1. Étape 1 — description (responsable, échéance)
2. Étape 2 — ...

## Questions ouvertes

- Questions qui restent à trancher avant de finaliser
```

## Bonnes pratiques
- Rester factuel et concis — les RFC s'adressent aux lecteurs futurs, pas au public
  présent
- Inclure des exemples de code pour les changements d'API
- Référencer les patterns existants dans le code
- Garder la section « Alternatives » honnête — montrer que d'autres options ont été
  envisagées
- La RFC doit être actionnable : quelqu'un doit pouvoir l'implémenter à partir d'elle
- En contexte CDC, renseigner systématiquement la classification et l'impact
  sécurité / souveraineté de l'en-tête
