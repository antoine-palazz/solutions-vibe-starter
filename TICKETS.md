# Backlog

Deux éléments de travail sur l'API de la plateforme.

---

## PROJ-101 — Le health-check renvoie 500 quand une dépendance est indisponible

- **Type :** Bug
- **Priorité :** Haute
- **Composant :** Backend / API
- **Endpoint :** `GET /api/health/check`

### Description

Quand la base de données est injoignable, l'endpoint de health-check renvoie une
erreur **500**. Une seule dépendance en échec fait donc tomber tout l'endpoint.

Résultat : les sondes de supervision et de readiness (orchestrateur, load balancer,
supervision) ne reçoivent plus aucun signal exploitable et considèrent le service
comme totalement hors ligne, alors que l'application elle-même répond.

### Comportement actuel

- Dépendance en échec → exception non gérée → **HTTP 500**, corps d'erreur générique.
- Impossible de distinguer « service dégradé » de « service complètement indisponible ».

### Comportement attendu

- L'endpoint ne doit **jamais** planter. Même en cas de dépendance en échec, il
  renvoie **HTTP 200** avec un **statut par service** dans le corps de la réponse.
- Le statut agrégé reflète l'état réel : `OK` si tout va bien, `DEGRADED` si au moins
  une dépendance est en erreur.
- Chaque dépendance expose son propre statut (`OK` / `ERROR`) et, en cas d'erreur, un
  détail lisible pour le diagnostic.

### Critères d'acceptation

- [ ] `GET /api/health/check` renvoie 200 même lorsque la base de données est
      indisponible.
- [ ] Le corps de réponse contient le statut global **et** le statut de chaque
      service.
- [ ] Une dépendance en échec apparaît en `ERROR` sans faire échouer les autres.
- [ ] Un test de régression couvre le cas « dépendance indisponible → 200 dégradé ».

---

## PROJ-102 — Limitation de débit (rate limiting) sur l'API

- **Type :** Demande d'évolution (Feature request)
- **Priorité :** Moyenne
- **Composant :** Backend / API

### Contexte

À mesure que l'usage de l'API croît, il faut la protéger : limiter les abus, prévenir
la force brute sur les routes sensibles et garantir un usage équitable entre clients.
C'est aussi une exigence attendue en environnement régulé, où la maîtrise et la
traçabilité des accès sont de premier ordre.

### Besoin

Introduire une **limitation de débit** des requêtes entrantes, appliquée par client,
avec un comportement clair au dépassement.

### Exigences

- Limiter le nombre de requêtes par client sur une fenêtre de temps donnée.
- Le seuil et la fenêtre doivent être **configurables** (sans redéploiement de code).
- Au dépassement, l'API répond avec un code **HTTP 429** explicite.
- Les **health-checks doivent rester exclus** de la limitation, pour ne pas fausser la
  supervision.
- La solution doit rester légère et adaptée à un déploiement souverain / sur site
  (pas de dépendance à un service externe pour la logique de limitation).

### Critères d'acceptation

- [ ] Au-delà du seuil configuré, les requêtes reçoivent un **HTTP 429**.
- [ ] Le seuil et la fenêtre sont pilotables par configuration.
- [ ] `GET /api/health/check` n'est **jamais** limité.
- [ ] Le comportement (limite atteinte / réinitialisation de fenêtre / isolation par
      client) est couvert par des tests.
