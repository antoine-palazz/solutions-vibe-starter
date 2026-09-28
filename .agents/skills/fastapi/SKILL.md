---
name: fastapi
description: Patterns FastAPI, middleware, injection de dépendances et bonnes pratiques de test
---

# Patterns FastAPI

## Routing
- Utiliser `APIRouter` avec `prefix` et `tags` pour l'organisation
- Regrouper les endpoints liés dans un même fichier de router
- Utiliser l'injection de dépendances via `Depends()` pour la logique partagée
  (auth, sessions db)

## Middleware
- Utiliser `@app.middleware("http")` pour les préoccupations transverses
- Pour le rate limiting, utiliser `slowapi` avec `Limiter` :
  ```python
  from slowapi import Limiter
  from slowapi.util import get_remote_address

  limiter = Limiter(key_func=get_remote_address)

  @router.get("/endpoint")
  @limiter.limit("10/minute")
  async def endpoint(request: Request):
      ...
  ```
- Configurer les limites via des variables d'environnement pour une flexibilité par
  environnement

## Gestion des erreurs
- Toujours envelopper les appels de services externes dans un try/except
- Renvoyer des réponses d'erreur structurées avec les bons codes HTTP
- Utiliser `HTTPException` pour les erreurs attendues, un middleware pour les
  inattendues
- Les endpoints de health-check ne doivent jamais crasher — renvoyer plutôt un
  statut dégradé :
  ```python
  try:
      status = await service.get_status()
  except Exception as e:
      logger.error("service unavailable", error=str(e))
      status = ServiceStatus(status=Status.ERROR, message=str(e))
  ```

## Tests
- Utiliser `pytest` avec `httpx.AsyncClient` pour les tests d'endpoints :
  ```python
  async with AsyncClient(app=app, base_url="http://test") as client:
      response = await client.get("/api/health/check")
      assert response.status_code == 200
  ```
- Tester les chemins de succès et d'erreur
- Utiliser `pytest.fixture` pour la configuration de test partagée

## Modèles Pydantic
- Définir les modèles de requête/réponse avec Pydantic v2
- Utiliser `model_validate()` pour la conversion ORM → DTO
- Garder les modèles d'API dans un `models/api_models.py` dédié
