---
name: rfc-writer
description: Draft technical RFCs and design documents following the standard template
user-invocable: true
---

# RFC Writer

When asked to write an RFC or design document, follow this structure:

## Template

```markdown
# RFC: <Title>

**Author:** <name>
**Date:** <date>
**Status:** Draft

## Context

What is the problem or opportunity? Why are we making this decision now?
Include relevant metrics, incidents, or user feedback that motivated this.

## Decision

What are we doing? Describe the chosen approach clearly and concisely.
Include architecture diagrams or code snippets where helpful.

## Alternatives Considered

| Alternative | Pros | Cons | Why Not |
|------------|------|------|---------|
| Option A | ... | ... | ... |
| Option B | ... | ... | ... |

## Consequences

### Positive
- What improves?

### Negative
- What tradeoffs are we accepting?

### Risks
- What could go wrong? How do we mitigate?

## Implementation Plan

1. Step 1 — description (owner, timeline)
2. Step 2 — ...

## Open Questions

- Questions that still need answers before finalizing
```

## Guidelines
- Be factual and concise — RFCs are for future readers, not present audiences
- Include code examples for API changes
- Reference existing patterns in the codebase
- Keep the "Alternatives" section honest — show you considered other options
- The RFC should be actionable: someone should be able to implement from it
