---
name: python-testing
description: Patterns pytest pour FastAPI — fixtures, TestClient, branches pilotées par l'environnement, et quoi vérifier
user-invocable: false
---

# Tests Python (pytest)

## Structure
- Refléter l'arborescence source sous `tests/`
- Un comportement par test ; nommer les tests `test_<unit>_<expectation>`
- Configurer les chemins d'import dans `pyproject.toml` :
  ```toml
  [tool.pytest.ini_options]
  pythonpath = ["src"]
  ```

## Endpoints FastAPI
- Utiliser `fastapi.testclient.TestClient` pour les tests d'endpoints synchrones :
  ```python
  from fastapi.testclient import TestClient
  from main import app

  client = TestClient(app)

  def test_health_ok():
      resp = client.get("/api/health/check")
      assert resp.status_code == 200
      assert resp.json()["status"] == "OK"
  ```
- Pour tester directement des helpers async, utiliser `httpx.AsyncClient` avec un
  transport ASGI.

## Fixtures & isolation
- Utiliser `pytest.fixture` pour la configuration partagée ; garder les fixtures
  petites et explicites
- Utiliser `monkeypatch.setenv(...)` pour piloter les branches dépendantes de la
  config
- Éviter l'état mutable partagé entre les tests (stores en mémoire, variables
  globales de module)

## Quoi vérifier
- Tester à la fois le chemin de succès et le chemin d'échec
- Toute correction de bug est livrée avec un test de régression qui échoue avant le
  correctif
- Vérifier les codes de statut ET la forme de la réponse, pas seulement l'un des deux
