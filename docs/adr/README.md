# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Agentic RAG Platform.
ADRs document significant technical decisions with the context, alternatives considered, and rationale.

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](ADR-001-faiss-vector-store.md) | FAISS as Vector Store | Accepted | 2026-07-01 |
| [ADR-002](ADR-002-groq-llm-provider.md) | Groq LPU as LLM Provider | Accepted | 2026-07-01 |
| [ADR-003](ADR-003-sqlite-observability.md) | SQLite for Observability Storage | Accepted | 2026-07-01 |

## How to Create a New ADR

1. Copy the template below
2. Name the file `ADR-NNN-short-title.md`
3. Fill in Status (Proposed | Accepted | Deprecated | Superseded)
4. Add a row to the index above

### Template

```markdown
# ADR-NNN: Title

**Status:** Proposed
**Date:** YYYY-MM-DD
**Author:** GitHub username

## Context
What is the problem or opportunity?

## Decision
What was decided?

## Rationale
Why was this the best option?

## Trade-offs Accepted
What did we give up?

## Consequences
What changes in the codebase?
```
