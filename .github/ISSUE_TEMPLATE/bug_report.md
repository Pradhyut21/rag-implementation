---
name: Bug Report
about: Report a reproducible bug in the Agentic RAG Platform
title: "[BUG] "
labels: ["bug", "needs-triage"]
assignees: []
---

## Bug Description
A clear and concise description of what the bug is.

## Steps to Reproduce
1. Upload a document via `POST /upload-doc`
2. Query with `POST /ask` using `reasoning_mode: "cot"`
3. Observe the error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened. Include the full error message/stack trace if available.

## Environment
- OS: [e.g. Ubuntu 22.04, Windows 11]
- Python version: [e.g. 3.11.5]
- Docker version (if applicable): [e.g. 24.0.5]
- Browser (if frontend issue): [e.g. Chrome 120]
- Deployment method: [local | docker-compose]

## Minimal Reproduction
```bash
curl -X POST http://localhost:8002/ask \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "...", "doc_id": "abc12345"}'
```

## Additional Context
- Observability session_id (if available):
- Relevant logs from `docker logs rag_backend`:
