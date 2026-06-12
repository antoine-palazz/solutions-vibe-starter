---
name: security-review
description: Security review checklist for code changes — secrets, input validation, authz, and audit logging
user-invocable: true
---

# Security Review

Apply this checklist when writing or reviewing code that handles untrusted input,
authentication, or sensitive data. It pairs with the compliance audit-log hook in
`.vibe/hooks.toml`.

## Secrets & configuration
- No secrets in code or git history — use environment variables or a secret manager
- `.env` files are git-ignored; only `.env.example` (with empty values) is committed
- No credentials, tokens, or private keys in logs or error messages

## Input validation
- Validate and type all external input at the boundary (Pydantic models for APIs)
- Treat path, query, header, and body params as untrusted
- Parameterize database queries — never build SQL by string concatenation
- Bound sizes (payloads, uploads, list lengths) to prevent resource exhaustion

## AuthN / AuthZ
- Every protected endpoint checks authentication AND authorization (not just login)
- Enforce least privilege — deny by default, grant explicitly
- Do not trust client-supplied identifiers for access decisions (e.g. `user_id` in the body)

## Output & errors
- Return generic error messages to clients; log details server-side
- Never return stack traces or internal paths in API responses
- Use the correct status code (401 vs 403 vs 404)

## Auditability
- Log security-relevant events (auth, permission changes, data access) with structure
- Record who / what / when — never log the secret itself
- Keep an append-only audit trail for sensitive actions

## Dependencies
- Pin dependency versions; review new dependencies before adding them
- Watch for known-vulnerable packages
