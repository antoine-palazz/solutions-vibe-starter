# Demo walkthrough — a day of dev with Vibe

A ~20-minute live session: **three agents** (dev / po / devops), **two issues**
(a bug, then a feature), from investigation to PR review to deploy. The repo ships
at the "before" state; the finished code is on the **`solution`** branch as a
fallback.

> This is a script, not a transcript — adapt the prompts to your style. The point
> is to show *how* you work with Vibe: sub-agents, plan mode, PR review, role-based
> agents, skills, hooks.

---

## The two issues

Track these in whatever your team uses — GitHub Issues, Linear, Jira, etc. The
agents reach it through that tool's **MCP server**. Linear and Notion are only the
examples wired in `.vibe/config.toml.example`; swap in any software that exposes an
MCP (including an internal/custom one). Or just keep the issues in this file and
point the agent at it.

**Issue #1 — Bug, urgent.** `GET /api/health/check` returns **500** when the
database is down. It should degrade gracefully: return **200** with a per-service
status so monitoring/readiness probes get a stable signal. Right now one failing
dependency takes the whole endpoint down.

**Issue #2 — Feature.** Add **request rate limiting** to the API to protect it as
usage grows (brute-force protection on sensitive routes, fair usage). Health
checks must stay un-throttled.

---

## Setup tour (2–3 min)

Give a quick tour of the `.vibe/` setup *before* touching any code — this is the
part that lands: **"you don't configure a tool, you configure a team."**

```bash
cd solutions-vibe-starter
vibe --agent dev
```

**Agents — `.vibe/agents/*.toml`.** Cycle with **`Shift+Tab`**: dev / po / devops.
Open `dev.toml` and show the permission model — `permission = "always" | "ask" |
"never"` per tool, with `allowlist` / `denylist`. *"Three roles: the dev codes, the
PO writes docs and can't run anything, the devops deploys but can't touch app code.
Each is a few lines of TOML."*

**Skills — `.vibe/skills/`.** Reusable playbooks the agents pull in automatically:
`fastapi`, `company-conventions`, `rfc-writer`, `security-review`, `python-testing`.
Open one (e.g. `security-review/SKILL.md`). *"Skills are the company toolbox —
best-practices that travel across repos. Committed here for this repo; move them to
`~/.vibe/skills/` to share them everywhere."*

**Connectors (MCP) — `.vibe/config.toml.example` + `/mcp`.** Run `/mcp` to show the
connected servers — *"this is how the agents reach your tools."* Linear and Notion
are just the examples wired here; replace them with whatever your team uses (Jira,
Confluence, ServiceNow, an internal/custom MCP). The agent prompts don't change,
only the server config.

**Hooks — `.vibe/hooks.toml`.** *"Automated actions after each turn."* Show the two:
auto-format (ruff after edits) and an append-only audit log (`.vibe/audit.log`).
*"For a regulated environment, that's an audit trail for free — we'll watch it fill
up."*

**Project handbook — `AGENTS.md`.** Loaded automatically. *"These are the project's
conventions — the agent follows them without being told. It even states the rule
we're about to see broken: health endpoints must never crash."*

---

## Issue #1 — investigate & fix the bug (`@dev`)

**1. Reproduce it.**
```bash
uv run uvicorn main:app --app-dir apps/backend/src   # in a second terminal
curl -s localhost:8000/api/health/check              # -> 500
```
*"A health-check 500 — let's find out why."*

**2. Read the issue.** *"Read issue #1 and summarize the bug."* (via MCP, or point
it at the section above).

**3. Dispatch a sub-agent to explore the codebase.**
> *"Launch a sub-agent to map how the health check works — which router handles it,
> what it depends on, and where the 500 could come from. Report back a short
> summary."*

Show the point: the sub-agent does the wide search and returns a digest, so the
main session's context stays clean. It comes back with `routers/health.py` and the
un-guarded database probe.

**4. Plan mode — and review the plan.**
- `Shift+Tab` → plan mode. *"Plan the fix for issue #1."*
- The agent proposes: wrap each probe in try/except, return a per-service
  `ServiceStatus(ERROR)` and an aggregate `DEGRADED`, add a regression test.
- **Review it with the agent** — push back, adjust scope, then approve. *"Plan mode
  means nothing runs until I say so."*

**5. Implement.** `Shift+Tab` → work mode. The agent edits `routers/health.py` and
adds a test. The `fastapi` and `python-testing` skills guide the patterns
(degraded status, `TestClient`). `AGENTS.md` already states the rule it's enforcing:
*"health endpoints must never crash."*

**6. Verify.**
```bash
uv run pytest                              # green, incl. the new regression test
curl -s localhost:8000/api/health/check    # -> 200, status DEGRADED (DB still down)
```

**7. Open a PR.** *"Commit with a conventional-commit message and open a PR for
issue #1."* The `company-conventions` skill shapes the message; the PR is created
via MCP / `gh`.

**8. Review the PR.** Read the diff and leave **inline comments** — either on
GitHub (review-with-comments on the repo) or directly in Vibe (the VS Code diff
view, `@routers/health.py` references). Example comment: *"add a NOT_INITIALIZED
case for a DB that's reachable but empty."* Then: *"address the review comments"* →
the agent pushes a follow-up commit. Merge when green.

---

## Issue #2 — design first, then build (`@po` → `@dev`)

**1. Switch to the PO agent.** `Shift+Tab` → `@po`. *"This agent reads code and
writes docs, but can't run anything."*

**2. Write an RFC with the specialized agent.**
> *"Draft an RFC for the rate limiting approach in `docs/rfcs/rate-limiting.md`.
> Read the codebase, explain the design, alternatives, and tradeoffs. Use the
> rfc-writer skill."*

The PO agent reads the code (read-only), uses the `rfc-writer` template, and writes
the doc. Try to make it edit a `.py` file — it can't (permissions in action).
Review the RFC in ~30s.

**3. Switch back to dev and implement.** `Shift+Tab` → `@dev`. *"Implement the rate
limiting from the RFC."* It adds the middleware (slowapi), env-var config, excludes
the health route, and writes tests. → PR → review → merge (same loop as issue #1).

---

## Deploy (`@devops`)

`Shift+Tab` → `@devops`. *"Build and run the stack with docker compose, then verify
the health check and the rate limit."*
```bash
docker compose -f deployment/docker/docker-compose.yml up --build
curl -s localhost:8000/api/health/check          # 200
for i in $(seq 1 70); do curl -s -o /dev/null -w "%{http_code} " localhost:8000/api/demo/ping; done   # ... 429
```
The devops agent has docker rights but **cannot** edit `apps/` — show the denied
edit.

---

## Close the loop

- *"Update issues #1 and #2: mark done, add a summary comment."* (via MCP).
- **Hooks:** after each edit the code was auto-formatted, and every agent turn is
  appended to `.vibe/audit.log` — open it. *"For a regulated environment, that's an
  audit trail for free."*
- **Programmatic mode** for CI/CD:
  ```bash
  vibe -p "run all tests and report failures" --output json
  ```

---

## Epilogue

Three agents, two issues: a bug fixed, a feature designed and built, the app
deployed, the tickets closed — all audited. You don't configure a tool; you
configure a *team*. Each agent has its role, its permissions, its skills. And it
all runs on your own infrastructure.

> **Fallback:** the finished code is on the `solution` branch — `git switch solution`
> — if anything stalls during the live demo.
