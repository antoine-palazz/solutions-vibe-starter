# Pas-à-pas de démo — une journée de dev avec Vibe

Une session live d'environ 20 minutes : **trois agents** (dev / po / devops), **deux
tickets** (un bug, puis une fonctionnalité), de l'investigation à la revue de PR
jusqu'au déploiement. Le repo est livré dans l'état « avant » ; la version aboutie
se reconstruit en rejouant le scénario ci-dessous.

> C'est un script, pas une transcription — adaptez les prompts à votre style.
> L'objectif est de montrer *comment* on travaille avec Vibe : sous-agents, plan
> mode, revue de PR, agents par rôle, skills, hooks.

---

## Les deux tickets

**Les deux tickets sont définis ci-dessous, directement dans ce fichier** — c'est la
voie la plus simple pour la démo : pointez l'agent dessus (« lis le ticket n°1 dans
`DEMO.md` et résume-le »), aucun outil externe requis.

En conditions réelles, vous les suivriez plutôt dans l'outil de votre équipe — Jira,
Confluence, GitHub Issues, Linear, etc. — auquel les agents accèdent via son
**serveur MCP**. Linear et Notion ne sont que les exemples câblés dans
`.vibe/config.toml.example` ; remplacez-les par le logiciel de votre choix exposant
un MCP (y compris interne/sur mesure — par exemple votre Jira ou votre Confluence via
la gateway MCP interne CDC). *(Si le MCP Linear affiche une erreur d'authentification
au lancement, ignorez-la : ce n'est pas nécessaire pour la démo — utilisez les
tickets ci-dessous.)*

**Ticket n°1 — Bug, urgent.** `GET /api/health/check` renvoie **500** quand la base
de données est indisponible. Il devrait se dégrader proprement : renvoyer **200**
avec un statut par service, pour que les sondes de supervision/readiness reçoivent un
signal stable. Aujourd'hui, une seule dépendance en échec fait tomber tout
l'endpoint.

**Ticket n°2 — Fonctionnalité.** Ajouter la **limitation de débit (rate limiting)**
des requêtes à l'API pour la protéger à mesure que l'usage grandit (protection
anti-force brute sur les routes sensibles, usage équitable). Les health-checks
doivent rester non limités.

---

## Visite de la configuration (2–3 min)

Faites un tour rapide de la configuration `.vibe/` *avant* de toucher au code —
c'est la partie qui marque : **« on ne configure pas un outil, on configure une
équipe. »**

```bash
cd solutions-vibe-starter
vibe --agent dev
```

**Agents — `.vibe/agents/*.toml`.** Défilez avec **`Shift+Tab`** : dev / po /
devops. Ouvrez `dev.toml` et montrez le modèle de permissions — `permission =
"always" | "ask" | "never"` par outil, avec `allowlist` / `denylist`. *« Trois
rôles : le dev code, le PO écrit la doc et ne peut rien exécuter, le devops déploie
mais ne peut pas toucher au code applicatif. Chacun tient en quelques lignes de
TOML. »*

**Skills — `.agents/skills/`.** Des playbooks réutilisables que les agents mobilisent
automatiquement : `fastapi`, `company-conventions`, `rfc-writer`, `security-review`,
`python-testing`. Ouvrez-en un (par ex. `security-review/SKILL.md`). *« Les skills
sont la boîte à outils de l'entreprise — des bonnes pratiques qui voyagent d'un repo
à l'autre. Commitées ici pour ce repo ; déplacez-les vers `~/.agents/skills/` pour
les partager partout. »* Insistez sur l'emplacement : `.agents/skills/` est le
**répertoire standard, indépendant de l'outil** (le même que lisent Vibe, Claude,
OpenCode…), et non un dossier propriétaire — vos bonnes pratiques restent portables
si l'équipe change d'assistant. *« Un point qui compte pour une institution
souveraine : on ne se verrouille pas sur un outil. »*

> **`user-invocable`.** Vous pouvez appeler une skill au slash (`/company-conventions`).
> Ce champ vaut **`true` par défaut** — une skill est donc invocable même sans le
> déclarer (voir `fastapi`, qui l'omet) ; mettez `user-invocable: false` pour la
> réserver au modèle et la masquer des commandes slash (voir `python-testing`).

**Connecteurs (MCP) — `.vibe/config.toml.example` + `/mcp`.** Lancez `/mcp` pour
afficher les serveurs connectés — *« voilà comment les agents atteignent vos
outils. »* Linear et Notion ne sont que les exemples câblés ici ; remplacez-les par
ce qu'utilise votre équipe (Jira, Confluence, ServiceNow, un MCP interne/sur
mesure). Les prompts des agents ne changent pas, seule la config du serveur change.

**Hooks — `.vibe/hooks.toml`.** *« Des actions automatisées après chaque tour. »*
Montrez les deux : l'auto-formatage (ruff après les éditions) et un journal d'audit
en ajout seul (`.vibe/audit.log`). *« Pour un environnement régulé, c'est une piste
d'audit gratuite — on va la voir se remplir. »*

**Guide du projet — `AGENTS.md`.** Chargé automatiquement. *« Ce sont les
conventions du projet — l'agent les suit sans qu'on le lui dise. Il y est même écrit
la règle qu'on est sur le point de voir enfreinte : les endpoints health ne doivent
jamais crasher. »*

---

## Ticket n°1 — investiguer et corriger le bug (`@dev`)

**1. Le reproduire.**
```bash
uv run uvicorn main:app --app-dir apps/backend/src   # dans un second terminal
curl -s localhost:8000/api/health/check              # -> 500
```
*« Un health-check en 500 — trouvons pourquoi. »*

**2. Lire le ticket.** *« Lis le ticket n°1 et résume le bug. »* (via MCP, ou en le
pointant sur la section ci-dessus).

**3. Déléguer l'exploration du code à un sous-agent.**
> *« Lance un sous-agent pour cartographier le fonctionnement du health-check —
> quel router le gère, de quoi il dépend, et d'où le 500 peut venir. Renvoie un
> court résumé. »*

Montrez l'intérêt : le sous-agent fait la recherche large et renvoie une synthèse,
si bien que le contexte de la session principale reste propre. Il revient avec
`routers/health.py` et la sonde base de données non protégée.

**4. Plan mode — et revue du plan.**
- `Shift+Tab` → plan mode. *« Planifie la correction du ticket n°1. »*
- L'agent propose : envelopper chaque sonde dans un try/except, renvoyer un
  `ServiceStatus(ERROR)` par service et un `DEGRADED` agrégé, ajouter un test de
  régression.
- **Passez-le en revue avec l'agent** — challengez, ajustez le périmètre, puis
  approuvez. *« Le plan mode signifie que rien ne s'exécute avant que je le dise. »*

**5. Implémenter.** `Shift+Tab` → work mode. L'agent édite `routers/health.py` et
ajoute un test. Les skills `fastapi` et `python-testing` guident les patterns
(statut dégradé, `TestClient`). `AGENTS.md` énonce déjà la règle qu'il applique :
*« les endpoints health ne doivent jamais crasher. »*

**6. Vérifier.**
```bash
uv run pytest                              # vert, y compris le nouveau test de régression
curl -s localhost:8000/api/health/check    # -> 200, statut DEGRADED (DB toujours down)
```

**7. Ouvrir une PR.** *« Commite avec un message en commit conventionnel et ouvre
une PR pour le ticket n°1. »* La skill `company-conventions` met en forme le
message ; la PR est créée via MCP / `gh` (ou une PR GitLab dans votre stack).

**8. Passer la PR en revue.** Lisez le diff et laissez des **commentaires inline** —
soit sur GitHub/GitLab (revue avec commentaires sur le repo), soit directement dans
Vibe (la vue diff de VS Code, avec des références `@routers/health.py`). Exemple de
commentaire : *« ajoute un cas NOT_INITIALIZED pour une DB joignable mais vide. »*
Ensuite : *« traite les commentaires de revue »* → l'agent pousse un commit de
suivi. Mergez quand c'est vert.

---

## Ticket n°2 — concevoir d'abord, construire ensuite (`@po` → `@dev`)

**1. Basculer sur l'agent PO.** `Shift+Tab` → `@po`. *« Cet agent lit le code et
écrit la doc, mais ne peut rien exécuter. »*

**2. Rédiger une RFC avec l'agent spécialisé.**
> *« Rédige une RFC pour l'approche de rate limiting dans
> `docs/rfcs/rate-limiting.md`. Lis le code, explique la conception, les
> alternatives et les compromis. Utilise la skill rfc-writer. »*

L'agent PO lit le code (en lecture seule), utilise le template `rfc-writer` et écrit
le document. Essayez de lui faire éditer un fichier `.py` — il ne peut pas (les
permissions à l'œuvre). Passez la RFC en revue en ~30 s.

**3. Repasser sur dev et implémenter.** `Shift+Tab` → `@dev`. *« Implémente le rate
limiting à partir de la RFC. »* Il ajoute un middleware de rate limiting (ici en
mémoire, sans dépendance externe — le pattern `slowapi` reste une alternative), la
config par variables d'environnement (`RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS`),
un endpoint de démonstration `/api/demo/ping`, exclut la route health et écrit des
tests. → PR → revue → merge (même boucle que le ticket n°1).

---

## Déployer (`@devops`)

`Shift+Tab` → `@devops`. *« Build et lance la stack avec docker compose, puis vérifie
le health-check et la limitation de débit. »*
```bash
docker compose -f deployment/docker/docker-compose.yml up --build
curl -s localhost:8000/api/health/check          # 200
for i in $(seq 1 70); do curl -s -o /dev/null -w "%{http_code} " localhost:8000/api/demo/ping; done   # ... 429
```
L'agent devops a les droits docker mais **ne peut pas** éditer `apps/` — montrez
l'édition refusée.

---

## Boucler la boucle

- *« Mets à jour les tickets n°1 et n°2 : passe-les en terminé, ajoute un
  commentaire de synthèse. »* (via MCP).
- **Hooks :** après chaque édition le code a été auto-formaté, et chaque tour d'agent
  est ajouté à `.vibe/audit.log` — ouvrez-le. *« Pour un environnement régulé, c'est
  une piste d'audit gratuite. »*
- **Mode programmatique** pour la CI/CD :
  ```bash
  vibe -p "run all tests and report failures" --output json
  ```

---

## Épilogue

Trois agents, deux tickets : un bug corrigé, une fonctionnalité conçue et
construite, l'app déployée, les tickets clôturés — le tout audité. On ne configure
pas un outil ; on configure une *équipe*. Chaque agent a son rôle, ses permissions,
ses skills. Et tout tourne sur votre propre infrastructure.

> **Repli :** si quelque chose se bloque pendant la démo live, rejouez le scénario
> étape par étape ci-dessus — le fil conducteur suffit à reconstruire la version
> aboutie.
