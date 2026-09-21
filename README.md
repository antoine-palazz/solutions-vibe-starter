# Exemple de configuration Vibe — Caisse des Dépôts

Exemple de configuration **Vibe** aux couleurs de la Caisse des Dépôts, posée sur
une petite application full-stack minimale, présentée comme un exercice pratique.

> ⚠️ **Ce sont des exemples à adapter, pas une solution clé en main.** Il n'existe
> pas de configuration universelle — agents, skills, hooks et permissions doivent
> être réglés selon votre équipe, vos rôles et vos exigences de sécurité. L'app
> derrière ces configs est une application d'exemple délibérément minimale ; la
> valeur est dans `.vibe/`.

## Ce que ça montre

Vibe n'est pas qu'un CLI — vous configurez une *équipe* d'agents, chacun avec son
rôle, ses permissions et ses skills. Ce repo réunit un exemple fonctionnel de cette
configuration : trois agents par rôle, des skills réutilisables, des hooks
d'automatisation, des conventions de projet et des connecteurs MCP — le tout sur une
petite app FastAPI + Next.js pour que tout tourne réellement. Le message central :
« on ne configure pas un outil, on configure une équipe » — utile pour une
institution publique et régulée comme la CDC, où les rôles et les garde-fous
comptent autant que le code.

## L'exercice

Le repo est livré dans un **état « avant »** avec deux travaux à réaliser, pour que
vous puissiez rejouer une session complète en direct avec Vibe (voir
**[`DEMO.md`](./DEMO.md)** pour le pas-à-pas) :

1. **Un bug à corriger** — `GET /api/health/check` renvoie **500** quand la base de
   données est indisponible, au lieu de se dégrader proprement.
2. **Une fonctionnalité à construire** — la limitation de débit (rate limiting) des
   requêtes.

La version aboutie (correctif + fonctionnalité + tests + RFC) se reconstruit en
rejouant le scénario du pas-à-pas ; elle sert de fil conducteur pour la démo.

## Ce qu'il y a dedans

| Élément | Où | Rôle |
|---|---|---|
| Agents par rôle | `.vibe/agents/{dev,po,devops}.toml` | Trois rôles avec des permissions d'outils granulaires |
| Hooks | `.vibe/hooks.toml` | Auto-formatage + journal d'audit de conformité en ajout seul |
| Skills | `.vibe/skills/*` | Playbooks réutilisables (FastAPI, conventions, RFC, sécurité, tests) |
| Guide du projet | `AGENTS.md` | Conventions que Vibe applique automatiquement dans ce repo |
| Config MCP | `.vibe/config.toml.example` | Comment câbler Linear/Notion — ou une gateway MCP interne on-prem |
| Pas-à-pas de démo | `DEMO.md` | Le script de la session live (bug → correctif → fonctionnalité → déploiement → docs) |
| App d'exemple | `apps/`, `deployment/` | FastAPI + Next.js minimal pour que les configs tournent |

### Les trois agents

- **`@dev`** — accès complet au code (lecture/écriture/édition, liste d'autorisation
  bash, MCP Linear + Notion). `safety = neutral`.
- **`@po`** — lit le code, n'écrit que docs/specs (`docs/*`, `*.md`) ; **aucune
  exécution de commande**. `safety = safe`.
- **`@devops`** — docker/kubectl/helm, peut éditer `deployment/*` mais **pas**
  `apps/*`. `safety = destructive`.

Basculez de l'un à l'autre en direct avec **`Shift+Tab`**. Chaque `.toml` déclare
des permissions par outil (`always` / `ask` / `never`) avec des motifs
`allowlist`/`denylist`, si bien que le PO ne peut jamais lancer de commande et que
l'agent DevOps ne peut jamais toucher au code applicatif.

## Deux niveaux de configuration

| Concept | Portée | Exemples | Où |
|---|---|---|---|
| **AGENTS.md** | Ce repo | conventions, architecture, patterns de test | `AGENTS.md` |
| **Skills** | Multi-repo | `fastapi`, `company-conventions`, `rfc-writer`, `security-review`, `python-testing` | `.vibe/skills/` ou `~/.vibe/skills/` |
| **Agents** | Projet ou global | les trois rôles présents ici | `.vibe/agents/` ou `~/.vibe/agents/` |

> AGENTS.md est le **guide du projet**. Les skills sont la **boîte à outils de
> l'entreprise**. Un nouveau développeur clone le repo et récupère les conventions ;
> il installe les skills et récupère les bonnes pratiques de l'entreprise partout.

Les skills commitées sous `.vibe/skills/` sont limitées à ce repo. Pour les
réutiliser sur plusieurs repositories, déplacez-les vers `~/.vibe/skills/`. Les
fichiers d'agents, eux, ne changent pas.

## Démarrage rapide

```bash
# 1. Lancer un agent (Shift+Tab fait défiler dev → po → devops)
cd solutions-vibe-starter
vibe --agent dev

# 2. (optionnel) Câbler MCP — copier les parties utiles dans ~/.vibe/config.toml et
#    exporter les tokens. Voir .vibe/config.toml.example
/mcp                       # vérifier les serveurs connectés depuis Vibe

# 3. Lancer l'app
cd apps/backend && uv run pytest                                   # tests
cd apps/backend && uv run uvicorn main:app --app-dir src --reload  # http://localhost:8000
cd apps/frontend && pnpm install && pnpm dev                       # http://localhost:3000

# ...ou toute la stack d'un coup
docker compose -f deployment/docker/docker-compose.yml up --build
```

> Sur un clone frais, `GET /api/health/check` renvoie 500 (aucune base de données ne
> tourne) — c'est le point n°1, le bug à corriger. Suivez [`DEMO.md`](./DEMO.md).

Les hooks se déclenchent automatiquement après chaque tour d'agent : le Python est
auto-formaté et chaque tour est ajouté à `.vibe/audit.log` (une piste simple et
auditable — utile en environnement régulé). Pour la CI/CD, lancez Vibe en mode
headless :

```bash
vibe -p "run all tests and report failures" --output json
```

## Structure du repository

```
solutions-vibe-starter/
├── .vibe/
│   ├── agents/{dev,po,devops}.toml   # agents par rôle avec permissions cadrées
│   ├── hooks.toml                    # auto-formatage + journal d'audit de conformité
│   ├── config.toml.example           # configuration des serveurs MCP (assainie)
│   └── skills/                       # fastapi · company-conventions · rfc-writer
│       └── ...                       # security-review · python-testing
├── AGENTS.md                         # conventions du projet (chargées automatiquement)
├── DEMO.md                           # script du pas-à-pas live
├── apps/
│   ├── backend/                      # FastAPI minimal (health-check — contient le bug)
│   └── frontend/                     # page de statut Next.js minimale
├── deployment/docker/                # docker-compose + Dockerfiles
└── .env.example
```
