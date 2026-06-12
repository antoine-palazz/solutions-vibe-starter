# solutions-vibe-starter

Example **Vibe** configuration over a minimal full-stack app, set up as a small
hands-on exercise.

> ⚠️ **These are examples to adapt, not a turnkey solution.** There is no
> one-size-fits-all setup — agents, skills, hooks and permissions should be tuned
> to your team, your roles, and your security requirements. The app behind the
> configs is a deliberately minimal placeholder; the value is in `.vibe/`.

## What this shows

Vibe isn't just a CLI — you configure a *team* of agents, each with its own role,
permissions, and skills. This repo packages a working example of that setup:
three role-based agents, reusable skills, automation hooks, project conventions,
and MCP connectors — over a tiny FastAPI + Next.js app so everything actually runs.

## The exercise

The repo ships at a **"before" state** with two pieces of work to do, so you can
replay a full session live with Vibe (see **[`DEMO.md`](./DEMO.md)** for the
step-by-step walkthrough):

1. **A bug to fix** — `GET /api/health/check` returns **500** when the database is
   down instead of degrading gracefully.
2. **A feature to build** — request rate limiting.

The completed version (fix + feature + tests + RFC) lives on the **`solution`**
branch (`git switch solution`) as a reference and a presenter fallback.

## What's inside

| Piece | Where | Purpose |
|---|---|---|
| Role agents | `.vibe/agents/{dev,po,devops}.toml` | Three roles with granular tool permissions |
| Hooks | `.vibe/hooks.toml` | Auto-format + append-only compliance audit log |
| Skills | `.vibe/skills/*` | Reusable playbooks (FastAPI, conventions, RFC, security, testing) |
| Project handbook | `AGENTS.md` | Conventions Vibe applies automatically in this repo |
| MCP config | `.vibe/config.toml.example` | How to wire Linear/Notion — or an on-prem MCP gateway |
| Demo walkthrough | `DEMO.md` | The live session script (bug → fix → feature → deploy → docs) |
| Example app | `apps/`, `deployment/` | Minimal FastAPI + Next.js so the configs run |

### The three agents

- **`@dev`** — full code access (read/write/edit, bash allowlist, Linear + Notion MCP). `safety = neutral`.
- **`@po`** — reads code, writes only docs/specs (`docs/*`, `*.md`); **no command execution**. `safety = safe`.
- **`@devops`** — docker/kubectl/helm, can edit `deployment/*` but **not** `apps/*`. `safety = destructive`.

Switch between them live with **`Shift+Tab`**. Each `.toml` declares per-tool
permissions (`always` / `ask` / `never`) with `allowlist`/`denylist` patterns, so
the PO can never run a command and the DevOps agent can never touch app code.

## Two layers of configuration

| Concept | Scope | Examples | Where |
|---|---|---|---|
| **AGENTS.md** | This repo | conventions, architecture, test patterns | `AGENTS.md` |
| **Skills** | Cross-repo | `fastapi`, `company-conventions`, `rfc-writer`, `security-review`, `python-testing` | `.vibe/skills/` or `~/.vibe/skills/` |
| **Agents** | Project or global | the three roles here | `.vibe/agents/` or `~/.vibe/agents/` |

> AGENTS.md is the **project handbook**. Skills are the **company toolbox**. A new
> developer clones the repo and gets the conventions; they install the skills and
> get the company best-practices everywhere.

Skills committed under `.vibe/skills/` are scoped to this repo. To reuse them
across repositories, move them to `~/.vibe/skills/`. The agent files don't change.

## Quickstart

```bash
# 1. Run an agent (Shift+Tab cycles dev → po → devops)
cd solutions-vibe-starter
vibe --agent dev

# 2. (optional) Wire MCP — copy the relevant parts into ~/.vibe/config.toml and
#    export the tokens. See .vibe/config.toml.example
/mcp                       # check connected servers from inside Vibe

# 3. Run the app
cd apps/backend && uv run pytest                                   # tests
cd apps/backend && uv run uvicorn main:app --app-dir src --reload  # http://localhost:8000
cd apps/frontend && pnpm install && pnpm dev                       # http://localhost:3000

# ...or the whole stack at once
docker compose -f deployment/docker/docker-compose.yml up --build
```

> On a fresh clone `GET /api/health/check` returns 500 (no database running) —
> that's issue #1, the bug to fix. Follow [`DEMO.md`](./DEMO.md).

Hooks fire automatically after every agent turn: Python is auto-formatted and each
turn is appended to `.vibe/audit.log` (a simple, auditable trail — useful in
regulated environments). For CI/CD, run Vibe headless:

```bash
vibe -p "run all tests and report failures" --output json
```

## Repository structure

```
solutions-vibe-starter/
├── .vibe/
│   ├── agents/{dev,po,devops}.toml   # role-based agents with scoped permissions
│   ├── hooks.toml                    # auto-format + compliance audit log
│   ├── config.toml.example           # MCP server setup (sanitized)
│   └── skills/                       # fastapi · company-conventions · rfc-writer
│       └── ...                       # security-review · python-testing
├── AGENTS.md                         # project conventions (loaded automatically)
├── DEMO.md                           # live walkthrough script
├── apps/
│   ├── backend/                      # minimal FastAPI (health check — has the bug)
│   └── frontend/                     # minimal Next.js status page
├── deployment/docker/                # docker-compose + Dockerfiles
└── .env.example
```
