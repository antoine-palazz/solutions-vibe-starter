---
name: company-conventions
description: Company-wide engineering standards — commit messages, logging, PR templates, code review
user-invocable: true
---

# Company Engineering Conventions

## Commit Messages
Follow conventional commits format:
```
<type>(<scope>): <subject>

<body>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`
Scope: module or area affected (e.g., `health`, `auth`, `deploy`)
Subject: imperative, lowercase, no period at end

Example:
```
fix(health): handle service unavailability gracefully

The health check endpoint was returning 500 when the workflow
service was down. Now returns degraded status with error details.
```

## Logging
- Use structured logging with kwargs — never f-strings in log messages
- Pattern: `logger.info("action description", key1=value1, key2=value2)`
- Always include a `name` field for the originating service/module
- Log levels: DEBUG for internal flow, INFO for business events, WARNING for recoverable issues, ERROR for failures

## Pull Request Template
```markdown
## Context
Why this change is needed.

## Implementation
Key design decisions and tradeoffs.

## Checks
- [ ] Tests pass
- [ ] No regressions
- [ ] Conventions followed (logging, error handling, types)
```

## Code Review Checklist
When reviewing code, verify:
- [ ] Error handling: all external calls wrapped, no raw 500s
- [ ] Logging: structured with kwargs, appropriate levels
- [ ] Types: all public functions have type hints
- [ ] Tests: new code has tests, bug fixes have regression tests
- [ ] Security: no secrets in code, no SQL injection, proper input validation
