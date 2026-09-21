# Conventions du projet — Vibe Starter (Caisse des Dépôts)

> Ce fichier est le guide du projet. Vibe le charge automatiquement, si bien que
> chaque agent suit les mêmes conventions. Les **skills** (dans `.vibe/skills/` ou
> `~/.vibe/skills/`) sont la boîte à outils multi-repo ; **ce fichier**, lui,
> contient ce qui est spécifique à *ce* repo.

> Contexte CDC : institution publique en environnement régulé. Les données et
> l'exécution restent en Europe (souveraineté), et la traçabilité (journal d'audit,
> gestion des secrets) est une exigence de premier ordre, pas une option.

## Architecture
- **Backend** : FastAPI (Python 3.11+) dans `apps/backend/` — un endpoint de
  health-check. Volontairement minimal.
- **Frontend** : Next.js + TypeScript dans `apps/frontend/` — une page de statut.
- **Déploiement** : Docker Compose en local, dans `deployment/docker/`.

## Standards de code

### Python (Backend)
- Utiliser un logging structuré avec des kwargs — jamais `print()` ni de f-strings
  dans les messages de log (`logger.info("message", key=value)`).
- Les annotations de type sont obligatoires sur toutes les fonctions publiques.
- Utiliser des modèles Pydantic pour les schémas de requête/réponse de l'API.

### Gestion des erreurs
- Envelopper les appels de services externes dans un try/except avec un logging
  d'erreur approprié.
- Les endpoints de l'API renvoient des codes de statut HTTP appropriés — jamais de
  500 bruts.
- Les endpoints de health-check ne doivent jamais crasher — renvoyer plutôt un
  statut dégradé (voir `apps/backend/src/routers/health.py`).

### Tests
- Utiliser `pytest` ; les tests vivent dans `tests/` en miroir de la structure du
  code source.
- Utiliser `fastapi.testclient.TestClient` pour les tests d'endpoints.
- Toute correction de bug doit inclure un test de régression.

### Conventions Git
- Commits conventionnels (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
- Un seul changement logique par commit.

## Commandes du projet
```bash
# Backend
cd apps/backend && uv run pytest                                   # tests
cd apps/backend && uv run uvicorn main:app --app-dir src --reload  # serveur de dev

# Frontend
cd apps/frontend && pnpm install && pnpm dev                       # http://localhost:3000

# Stack complète
docker compose -f deployment/docker/docker-compose.yml up --build
```
