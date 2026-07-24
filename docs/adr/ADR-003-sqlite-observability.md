# ADR-003: SQLite for Observability Storage

**Status:** Accepted  
**Date:** 2026-07-01  
**Author:** Pradhyut21

---

## Context

The platform requires a persistent telemetry store for session tracing, agent span attribution, error logging, CoT stage capture, and ToT branch scoring. The observability system must:

- Record every LLM call with latency attribution per agent
- Support session replay (retrieve full trace by `session_id`)
- Handle concurrent writes from multiple FastAPI workers
- Run without external infrastructure dependencies

Options considered:

| Option | Pros | Cons |
|--------|------|------|
| **SQLite** (chosen) | Zero config, ACID transactions, relational queries, file-based | Single-writer lock, no horizontal scale |
| PostgreSQL | Full horizontal scale, connection pooling | Requires a running database server, adds docker-compose complexity |
| Prometheus + Grafana | Industry standard for metrics, beautiful dashboards | Metrics only (no trace/span model), 2 additional containers required |
| OpenTelemetry + Jaeger | Full distributed trace standard | Complex setup, overkill for single-service architecture |
| MongoDB | Flexible document model | No relational joins, harder to query across span/event/session |
| In-memory only | Zero overhead | Lost on restart, no replay |

## Decision

Use **SQLite** with a **10-table normalized relational schema** stored at `data/observability.db`.

## Schema

```
sessions          - Top-level request tracking (session_id, query, reasoning_mode, total_latency)
spans             - Agent-level attribution (session_id, agent_name, duration_ms, status)
events            - Discrete events within spans (span_id, event_type, payload)
errors            - Structured error records (session_id, error_type, stack_trace, retry_count)
token_usage       - Per-call LLM token accounting (session_id, prompt_tokens, completion_tokens)
latency_buckets   - Histogram-style latency distribution (agent_name, bucket_ms, count)
cot_stages        - Chain-of-Thought stage capture (session_id, stage_name, stage_output)
tot_branches      - Tree-of-Thought branch metadata (session_id, branch_name, sub_queries)
branch_scores     - 5-dimensional branch scoring (branch_id, coverage, completeness, etc.)
branch_evals      - LLM evaluation details per branch (branch_id, evaluation_details)
```

## Rationale

1. **Zero operational overhead**: SQLite ships with Python — no database server process, no credentials, no port to expose. The full observability system activates with zero additional configuration.
2. **ACID guarantees**: SQLite's write-ahead logging (WAL mode) allows concurrent reads with a single write lock. Sufficient for the 2-worker FastAPI deployment described in `docker-compose.yml`.
3. **Relational joins for replay**: Session replay requires joining `sessions → spans → events → cot_stages`. SQLite's full SQL support makes this trivial vs document stores.
4. **File portability**: `observability.db` is a single file. Easy to inspect with any SQLite viewer, copy between environments, or attach to a Jupyter notebook for analysis.
5. **Hackathon context**: Adding PostgreSQL would require a third container, health checks, and initialization scripts — complexity with no quality benefit at this scale.

## Migration Path to Production Scale

When write throughput exceeds SQLite's single-writer limit (~5000 writes/second):

1. **SQLAlchemy Core** already abstracts all DB calls — swap `sqlite:///` for `postgresql://` connection string
2. Add Alembic for schema migrations
3. Point `docker-compose.yml` at a PostgreSQL service
4. Zero application code changes required

## Trade-offs Accepted

- **Single-writer lock**: Under concurrent load (>2 workers, >10 req/s), write contention on `observability.db` will emerge. Mitigation: WAL mode (`PRAGMA journal_mode=WAL`) enables concurrent reads. Production upgrade: PostgreSQL.
- **No push metrics**: SQLite cannot push metrics to Prometheus. Mitigation: `/observability/metrics` endpoint exposes aggregated stats in Prometheus text format for external scraping.

## Consequences

- `observability/storage/db.py`: SQLAlchemy Core, WAL mode enabled
- `observability/middleware/`: Context-var based session propagation (no thread-local)
- `observability/routes.py`: 10+ API endpoints exposing all 10 tables for the dashboard
- React dashboard: Full session replay, CoT stage viewer, ToT branch comparison UI
