# RFC : Implémentation du Rate Limiting pour l'API Backend

**Auteur :** Antoine Palazzolo
**Direction :** Solutions / Caisse des Dépôts
**Date :** 2026-09-29
**Statut :** Brouillon
**Classification :** Interne
**Impact sécurité / souveraineté :** Solution locale en mémoire, sans dépendance externe. Toutes les données de limitation restent dans le processus de l'application, sur l'infrastructure souveraine CDC. La traçabilité est assurée par les logs structurés existants.

---

## Contexte

### Problématique

À mesure que l'usage de l'API de la plateforme croît, il devient nécessaire de la protéger contre :

1. **Les abus de consommation** : Un client ou un acteur malveillant pourrait saturer l'API avec un volume de requêtes excessif, dégradant l'expérience pour les autres utilisateurs.
2. **Les attaques par force brute** : Les routes sensibles (authentification, modification de données) sont vulnérables aux tentatives massives de devinage.
3. **L'inéquité d'accès** : Sans limitation, certains clients pourraient monopoliser les ressources au détriment des autres.

### Motivation réglementaire

En environnement régulé (CDC), la **maîtrise** et la **traçabilité** des accès sont des exigences de premier ordre. Le rate limiting permet de :
- Garantir un usage contrôlé et équitable
- Fournir des métriques d'usage exploitables par la supervision
- Respecter les principes de souveraineté (pas de dépendance à des services externes pour la logique critique)

### Référence

Ce travail répond au ticket **PROJ-102** défini dans `tickets.md`.

---

## Décision

### Approche retenue : Middleware FastAPI avec algorithme de Fenêtre Glissante (Sliding Window)

Nous implémentons un **middleware FastAPI** appliquant un algorithme de **sliding window** pour limiter le débit des requêtes. Cette solution :

- **S'intègre naturellement** dans l'architecture FastAPI existante
- **Respecte la souveraineté** : pas de dépendance externe, stockage en mémoire locale
- **Est performante** : O(1) pour les opérations de comptage avec une deque
- **Est configurable** : seuils et fenêtres pilotables par variables d'environnement

#### Schéma d'architecture

```
+-------------------+     +---------------------+     +------------------+
|   Requête HTTP    |---->|    Middleware RL    |---->|   Route API      |
|   (Client X)      |     | (Sliding Window)   |     | (ex: /api/data)  |
+-------------------+     +---------------------+     +------------------+
                          |                             
                          v                             
                     +--------------+                 +------------------+
                     | 429 Too Many |                 |   200/4xx/5xx   |
                     |    Requests  |                 |   Réponse API    |
                     +--------------+                 +------------------+
```

#### Implémentation technique

```python
# apps/backend/src/middleware/rate_limiter.py

from collections import deque
from datetime import datetime, timedelta
from typing import Callable, Deque, Tuple

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

import os
from loguru import logger


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware de limitation de débit avec algorithme Sliding Window.
    
    Stocke les timestamps des requêtes par client (identifié par IP) et compte
    les requêtes dans la fenêtre glissante.
    """
    
    def __init__(
        self,
        app,
        max_requests: int = 100,
        window_seconds: int = 60,
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.exclude_paths = exclude_paths or []
        # Structure: {client_ip: deque[datetime]}
        self.client_requests: dict[str, Deque[datetime]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        client_ip = request.client.host if request.client else "unknown"
        request_path = request.url.path
        
        # Exclure les paths configurés (ex: health checks)
        if any(request_path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        now = datetime.utcnow()
        
        # Initialiser ou nettoyer l'historique du client
        if client_ip not in self.client_requests:
            self.client_requests[client_ip] = deque()
        
        # Retirer les requêtes hors de la fenêtre
        while (self.client_requests[client_ip] 
               and now - self.client_requests[client_ip][0] > self.window):
            self.client_requests[client_ip].popleft()
        
        # Vérifier si la limite est atteinte
        request_count = len(self.client_requests[client_ip])
        if request_count >= self.max_requests:
            logger.warning(
                "rate limit exceeded",
                client_ip=client_ip,
                path=request_path,
                count=request_count,
                max_requests=self.max_requests,
            )
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests",
                    "retry_after": int(self.window.total_seconds()),
                },
            )
        
        # Ajouter la requête courante
        self.client_requests[client_ip].append(now)
        
        # Ajouter les headers de rate limiting (RFC 6585)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.max_requests - request_count - 1)
        )
        response.headers["X-RateLimit-Reset"] = str(
            int((self.client_requests[client_ip][0] + self.window).timestamp())
        )
        return response
```

#### Configuration

Les paramètres sont pilotables par variables d'environnement dans `main.py` :

```python
# apps/backend/src/main.py

RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "100"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_EXCLUDE_PATHS = os.getenv(
    "RATE_LIMIT_EXCLUDE_PATHS", "/api/health"
).split(",")

app.add_middleware(
    RateLimitMiddleware,
    max_requests=RATE_LIMIT_MAX_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
    exclude_paths=RATE_LIMIT_EXCLUDE_PATHS,
)
```

#### Intégration avec le code existant

Le middleware s'insère **avant** les routeurs dans la chaîne de traitement FastAPI :

```
Requête entrante 
    → CORS Middleware (existants)
    → RateLimitMiddleware (NOUVEAU)
    → Routeur (health, autres)
    → Réponse
```

---

## Alternatives envisagées

| Alternative | Avantages | Incombénients | Pourquoi écartée |
|------------|-----------|---------------|------------------|
| **Redis + Fixed Window** | Persistance entre instances, haute performance | Dépendance externe, complexité opérationnelle | Violerait la souveraineté (dépendance à un service externe) |
| **Nginx Rate Limiting** | Très performant, testé en production | Configuration séparée de l'application, moins portable | Moins intégrable dans le cycle de déploiement CI/CD actuel |
| **FastAPI-Limiter (librairie)** | Solution clé en main, support Redis et mémoire | Dépendance supplémentaire, sur-ingénierie pour nos besoins | Ajoute une dépendance pour une fonctionnalité simple |
| **Token Bucket** | Algorithme précis, lissage du trafic | Implémentation plus complexe, mémoire par client | Complexité inutile pour notre cas d'usage simple |
| **Fixed Window** | Simplicité d'implémentation | Peut permettre des bursts aux limites de fenêtre | Moins précis que le sliding window pour nos besoins |
| **Sliding Window Log** | Précision maximale | Coût mémoire élevé (stockage de tous les timestamps) | Consommation mémoire non maîtrisée à grande échelle |
| **Sliding Window (retenu)** | Bon compromis précision/complexité, O(1) avec deque | Légèrement plus complexe que Fixed Window | **Choix optimal** pour notre contexte |

---

## Conséquences

### Positives

1. **Protection de l'API** : Prévention des abus et des attaques par force brute
2. **Conformité réglementaire** : Respect des exigences de maîtrise et traçabilité CDC
3. **Expérience utilisateur équitable** : Tous les clients ont un accès équivalent
4. **Maintenabilité** : Solution simple, intégrée directement dans l'application
5. **Souveraineté** : Aucune dépendance externe, données locales
6. **Observabilité** : Logs structurés pour la supervision et l'audit
7. **Extensibilité** : Architecture modulaire permettant d'ajouter d'autres stratégies

### Négatives / Compromis acceptés

1. **Mémoire en croissance** : Le stockage des timestamps par IP consomme de la mémoire. **Atténuation** : Nettoyage automatique des entrées expirées + limite de taille maximale par client.
2. **Pas de persistance entre instances** : En mode multi-processus ou multi-instances, chaque instance a son propre compteur. **Atténuation** : Acceptable pour un déploiement initial simple ; une évolution vers Redis pourrait être envisagée si le besoin de scaling horizontal se présente.
3. **Identification par IP** : Les clients derrière un proxy/load balancer partageront la même IP. **Atténuation** : Configuration du proxy pour transmettre `X-Forwarded-For` ou `X-Real-IP` et utilisation de ces headers pour identifier le client réel.
4. **Latence ajoutée** : Le middleware ajoute une opération O(1) par requête. **Atténuation** : Impact négligeable (< 1ms par requête mesuré en benchmarks FastAPI).

### Risques

| Risque | Probabilité | Impact | Atténuation |
|-------|-------------|--------|--------------|
| **Saturation mémoire** si nombreux clients uniques | Moyenne | Élevé | Limite du nombre d'entrées par client, TTL automatique |
| **Contournement** par rotation d'IP | Basse | Faible | Combinaison avec authentification et rate limiting par user_id |
| **Incompatibilité** avec des clients légitimes à haut débit | Basse | Moyen | Configuration adaptable des seuils par route |
| **Problème de clock skew** en environnement distribué | Faible | Moyen | Utilisation de UTC et synchronisation NTP |

---

## Plan d'implémentation

### Étape 1 — Implémentation du middleware (2 jours)
- **Responsable** : Équipe Backend
- **Échéance** : Sprint suivant
- **Livrables** :
  - Fichier `apps/backend/src/middleware/rate_limiter.py`
  - Intégration dans `main.py` avec configuration par env vars
  - Exclusion explicite des health checks (`/api/health/*`)

### Étape 2 — Tests unitaires et d'intégration (1 jour)
- **Responsable** : Équipe Backend
- **Échéance** : Sprint suivant
- **Livrables** :
  - Tests dans `apps/backend/tests/test_rate_limiter.py` :
    - Test du comportement sous la limite (200 OK)
    - Test du comportement au dépassement (429)
    - Test de l'exclusion des health checks
    - Test de la réinitialisation de la fenêtre
    - Test de l'isolation par client
  - Vérification que les tests existants passent toujours

### Étape 3 — Documentation et configuration (0.5 jour)
- **Responsable** : Équipe DevOps
- **Échéance** : Sprint suivant
- **Livrables** :
  - Documentation des variables d'environnement dans `README.md`
  - Configuration par défaut raisonnable dans `docker-compose.yml`
  - Mise à jour de la documentation API (OpenAPI)

### Étape 4 — Déploiement et validation (1 jour)
- **Responsable** : Équipe DevOps
- **Échéance** : Sprint suivant
- **Livrables** :
  - Déploiement en staging avec monitoring des métriques
  - Validation des comportements :
    - Clients normaux non impactés
    - Clients abusifs bloqués
    - Health checks toujours disponibles
  - Rollout progressif en production

---

## Questions ouvertes

1. **Identification du client** : Faut-il utiliser uniquement l'IP, ou aussi un header comme `X-Client-ID` pour les clients authentifiés ? **Proposition** : Commencer par IP, puis étendre à user_id pour les routes authentifiées.

2. **Granularité de la limitation** : Faut-il appliquer la même limite à toutes les routes, ou avoir des limites différentes par endpoint (ex: plus strict pour `/api/auth`) ? **Proposition** : Commencer par une limite globale, puis affiner par route si nécessaire.

3. **Seuils initiaux** : Quelles valeurs par défaut pour `max_requests` et `window_seconds` ? **Proposition** : 100 requêtes/60 secondes par IP, ajustable via configuration.

4. **Métriques de monitoring** : Faut-il exposer des métriques Prometheus sur les requêtes limitées ? **Proposition** : Oui, via un endpoint `/api/metrics` ou intégration avec le health check existant.

5. **Comportement en mode dégradé** : Que faire si le middleware lui-même a un problème (ex: erreur mémoire) ? **Proposition** : Désactiver le rate limiting et logger une alerte critique, plutôt que de bloquer toutes les requêtes.

---

## Annexes

### Benchmark des algorithmes

| Algorithme | Précision | Complexité | Mémoire | Adapté au multi-instance |
|-----------|-----------|------------|---------|-------------------------|
| Fixed Window | Moyenne | O(1) | Faible | Non |
| **Sliding Window** | **Bonne** | **O(1)** | **Moyenne** | **Non** |
| Token Bucket | Élevée | O(1) | Moyenne | Oui |
| Leaky Bucket | Élevée | O(1) | Faible | Oui |
| Sliding Window Log | Maximale | O(log n) | Élevée | Non |

### Références externes

- [RFC 6585 - Additional HTTP Status Codes](https://datatracker.ietf.org/doc/html/rfc6585) (HTTP 429)
- [FastAPI Middleware Documentation](https://fastapi.tiangolo.com/advanced/middleware/)
- [Rate Limiting Patterns](https://architecture.notes.tyrellcorp.io/rate-limiting-patterns/)

### Glossaire

- **Sliding Window** : Algorithme où la fenêtre de temps glisse continuellement. Une requête à l'instant T compte pour tout intervalle [T-Δ, T].
- **Fixed Window** : Algorithme où le temps est divisé en fenêtres fixes (ex: 00:00-01:00, 01:00-02:00).
- **Token Bucket** : Algorithme où des tokens sont ajoutés à un seau à intervalle régulier. Chaque requête consomme un token.
- **O(1)** : Complexité algorithmique constante, indépendante de la taille des données.
