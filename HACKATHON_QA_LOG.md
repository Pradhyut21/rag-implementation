# 🏆 Hackathon Judge Q&A Log
## Enterprise Agentic RAG Platform — July 14, 2026

> Complete record of the hackathon judge Q&A session.
> Use this as a reference for future architectural discussions, interviews, and submission updates.

---

## Round 1 — Error Detection & Correction Mechanisms

**Judge Question:**
> What kind of mechanisms are you considering for initiating the correction process once an error is detected?

**Our Answer:**

**1. Evidence-Type Classification (3-state, not binary confidence)**
The `Sufficient Context Agent` classifies retrieved evidence into: `explicit` (facts present), `partial` (topic present but metrics missing), or `missing` (no relevant info). Three-state model distinguishes vague answers from missing answers, triggering different responses.

**2. Intermediate Draft Auditing**
Before marking context sufficient, the system generates an **Intermediate Draft** from current context, then evaluates the draft against the original query. The SCA sees both raw retrieved chunks AND the draft simultaneously.

**3. Structured Missing Information Extraction**
When an error is detected, the agent outputs `missing_information[]` — a structured array of specific factual gaps, not a generic "try again." Each item is individually passed through the **Query Rewriter Agent** before the next FAISS search.

**4. Adaptive Feedback Loop**
```
Insufficient → Extract missing_information[] + feedback_log
            → Query Rewriter densifies each gap into search queries  
            → New FAISS retrieval targets exactly the missing facts
            → Re-aggregate + re-audit (up to N=2 iterations)
            → Only synthesize when evidence_type = "explicit"
```

**5. Zero-Hallucination Contract on Synthesis**
Synthesis Agent is explicitly prompted to refuse to generate content not present in verified context. If after N iterations context is still insufficient, the system states that explicitly.

**6. Full Observability for Pattern Detection**
Every error logged to SQLite `errors` table with `error_type`, `stack_trace`, and `retry_count`. `feedback_log` from every SCA evaluation stored in spans for retrospective analysis.

**7. ToT Multi-Branch Evidence (extra layer)**
Branch with strongest `evidence_quality` score (0.20 weight) wins, ensuring highest-density factual content reaches the synthesizer.

---

## Round 2 — Latency Management with Iterative Loops

**Judge Question:**
> How are you managing the potential latency impact of these iterative correction loops, especially with the draft auditing and N-iterations?

**Our Answer:**

**1. Hard Cap on Iterations (N=2)**
Bounded at `max_iterations=2` in `agentic_rag()`. Worst-case is exactly 2 full retrieval + audit cycles — never an unbounded loop.

**2. Groq LPU — Not GPU**
`llama-3.3-70b-versatile` via Groq's LPU delivers sub-2-second completion per call. Even 4-5 LLM calls per request stays within a 15-second SLA.

**3. Context Hard Cap (12,000 chars)**
Aggregated context trimmed to 12,000 characters before any LLM call. Directly controls token count and therefore latency of every downstream call.

**4. In-Memory LRU Cache**
```python
loaded_vector_stores: Dict[str, VectorStore] = {}
```
FAISS indexes cached in-memory after first load. Repeated queries bypass disk I/O entirely.

**5. Chunk Deduplication Before LLM**
Duplicate chunks removed by text hash before reaching SCA. Reduces context payload and LLM token count.

**6. Per-Agent Latency Attribution**
Observability stack tracks latency per agent: `planner | rewriter | retriever | sufficient_context | synthesis`. Exact bottleneck visibility without guessing.

**7. Vanilla RAG Fallback**
`POST /vanilla-ask` — single-pass retrieval + synthesis with zero agent overhead for latency-sensitive queries. Operators get a conscious quality-vs-latency dial.

**Honest tradeoff:** 2-iteration agentic run costs ~2-3× latency of vanilla RAG. Acceptable for enterprise Q&A where hallucination has real consequences. v3.1 roadmap adds SSE streaming.

---

## Round 3 — Model Routing & Cost Optimization

**Judge Question:**
> Have you considered using smaller, potentially fine-tuned models for certain agentic tasks to optimize performance and cost?

**Our Answer:**

Yes — our architecture isolates each agent behind its own function boundary, making model routing a **one-line change per agent**.

**Natural routing strategy for v3.0:**
| Agent | Model | Reason |
|---|---|---|
| Planner + Rewriter | `llama-3.1-8b-instant` | Simple structured JSON, no reasoning depth required |
| Sufficient Context Agent | `llama-3.3-70b` | Nuanced evidence classification — keep large model |
| Intermediate Draft | `llama-3.1-8b-instant` | Draft just needs to be good enough for auditor to evaluate |
| Synthesis Agent | `llama-3.3-70b` | Final answer quality — keep large model |

**~60-65% cost reduction** while preserving accuracy where it matters. All models on same Groq API interface — zero integration changes.

**SQLite → Production Path:**
Abstracted behind `get_db_connection()` — single-file swap. Schema maps to OpenTelemetry format, so future migration to Jaeger/Grafana Tempo requires only an exporter swap.

**Knowledge Base Versioning:**
```json
{
  "doc_id": "9b12fe0a",
  "versions": [
    { "version": 1, "index_path": "..._v1.index", "active": false },
    { "version": 2, "index_path": "..._v2.index", "active": true }
  ]
}
```

**Key Clarification:** The Intermediate Draft Auditor feeds its output back into the SCA as a **combined input** — SCA receives `(query, retrieved_context, intermediate_draft)` simultaneously for a single unified sufficiency judgment.

---

## Round 4 — A/B Testing Metrics for Knowledge Base Versions

**Judge Question:**
> What specific metrics from your SQLite Telemetry DB will be most critical for comparing the performance of different knowledge base versions during A/B tests?

**Our Answer — 6 metrics, all queryable from existing schema:**

**Metric 1 — Context Sufficiency Rate (Primary KPI)**
```sql
SELECT doc_id, 
       AVG(CASE WHEN context_sufficient = 1 THEN 1.0 ELSE 0.0 END) as sufficiency_rate
FROM sessions WHERE doc_id IN ('v_A_id', 'v_B_id') GROUP BY doc_id;
```

**Metric 2 — Average Feedback Loop Iterations**
```sql
SELECT doc_id, AVG(iterations_count) as avg_iterations
FROM sessions GROUP BY doc_id;
```

**Metric 3 — FAISS Cosine Similarity Distribution**
```sql
SELECT s.doc_id, AVG(json_extract(sp.extra_data, '$.scores')) as avg_retrieval_score
FROM spans sp JOIN sessions s ON sp.session_id = s.session_id
WHERE sp.name = 'retriever' GROUP BY s.doc_id;
```

**Metric 4 — Evidence Type Distribution**
```sql
SELECT s.doc_id, json_extract(sp.extra_data, '$.evidence_type') as evidence_type, COUNT(*) as count
FROM spans sp JOIN sessions s ON sp.session_id = s.session_id
WHERE sp.name = 'sufficient_context' GROUP BY s.doc_id, evidence_type;
```

**Metric 5 — Cost Per Successful Answer**
```sql
SELECT doc_id,
       SUM(estimated_cost) / SUM(CASE WHEN context_sufficient = 1 THEN 1 ELSE 0 END) as cost_per_success
FROM sessions GROUP BY doc_id;
```

**Metric 6 — ToT Winning Branch Score**
```sql
SELECT s.doc_id, AVG(wb.score) as avg_winning_score
FROM winning_branches wb JOIN sessions s ON wb.session_id = s.session_id GROUP BY s.doc_id;
```

**A/B Decision Rule:** Version B wins if: ↑ sufficiency_rate, ↓ avg_iterations, ↑ avg_retrieval_score, more `explicit` evidence, ↓ cost_per_success, ↑ winning branch score. All 6 queries run against existing schema with zero migration.

---

## Round 5 — Canary Deployment Strategy

**Judge Question:**
> Will the roll-out of a new "active" knowledge base version be an instant flip, or a gradual canary deployment?

**Our Answer: Canary deployment — never an instant flip.**

**Phase 1 — Shadow Mode (0% live traffic)**
Version B runs on all queries in background. Results logged to telemetry but never returned to users. Real query distribution data with zero user risk.
```json
{ "active_version": 1, "versions": [{"version": 2, "active": false, "shadow": true}] }
```

**Phase 2 — Canary (10% live traffic)**
If shadow metrics show `sufficiency_rate_B ≥ sufficiency_rate_A + 5%`, route 10% of queries to B via `session_id % 10 == 0`.
- **Auto-rollback trigger:** sufficiency_rate drops >10% below version A baseline

**Phase 3 — Progressive Roll-out**
- `10% → 50%`: automatic after 200 queries with sustained improvement
- `50% → 100%`: **HUMAN APPROVAL REQUIRED**
- Version A stays on disk 7 days after 100% for instant rollback

---

## Round 6 — Auto-Rollback Safeguards

**Judge Question:**
> What safeguards ensure the auto-rollback doesn't cause false positives or frequent version switches?

**Our Answer — 5 safeguards:**

**Safeguard 1 — Minimum Sample Size Gate**
Rollback cannot trigger until **30 queries** processed against canary version. Below this, variance too high to distinguish signal from noise.

**Safeguard 2 — Sustained Degradation Window**
Rollback fires only if regression persists across **rolling 20-query window**:
```
Condition: sufficiency_rate < baseline - 10% FOR 20 consecutive queries
```

**Safeguard 3 — Cooldown Period**
4-hour cooldown after any rollback before next promotion attempt:
```json
{ "last_rollback": "2026-07-14T12:00:00Z", "cooldown_until": "2026-07-14T16:00:00Z" }
```

**Safeguard 4 — Human Approval Gate at 50%**
```
0% → 10%:  automatic (shadow metrics pass)
10% → 50%: automatic (canary metrics pass, 200 queries)
50% → 100%: HUMAN APPROVAL REQUIRED
```

**Safeguard 5 — Full Audit Log**
```sql
CREATE TABLE rollback_events (
    event_id TEXT PRIMARY KEY,
    timestamp TEXT,
    from_version INTEGER, to_version INTEGER,
    trigger_reason TEXT,
    metrics_at_trigger TEXT,  -- JSON snapshot of all 6 KPIs
    action TEXT               -- 'rollback' | 'promote' | 'hold'
);
```

**Meta-Safeguard:** After 3 months, analyze false-positive rate in `rollback_events`. Thresholds recalibrated based on operational data — automation is itself data-driven.

---

## Round 7 — Operator Alert & Promotion Dashboard

**Judge Question:**
> What alerts do operators get and what dashboard do they see to make the 50% → 100% promotion decision?

**Our Answer:**

**Alert Payload (Slack/email/PagerDuty):**
```json
{
  "event": "CANARY_READY_FOR_PROMOTION",
  "queries_evaluated": 200,
  "metrics_summary": {
    "sufficiency_rate_v1": 0.71, "sufficiency_rate_v2": 0.84,
    "avg_iterations_v1": 1.6, "avg_iterations_v2": 1.2,
    "cost_per_success_v1": 0.0042, "cost_per_success_v2": 0.0031
  },
  "approve_url": "http://api/admin/promote-version/9b12fe0a/v2",
  "reject_url":  "http://api/admin/rollback-version/9b12fe0a/v1"
}
```
One-click approve/reject from Slack — no login required.

**Dashboard (ObservabilityWorkspace.jsx extension):**

| Metric | V1 Active | V2 Candidate | Verdict |
|---|---|---|---|
| Context Sufficiency Rate | 71% | 84% | ✅ +13% |
| Avg Feedback Iterations | 1.6 | 1.2 | ✅ −25% |
| FAISS Avg Cosine Score | 0.62 | 0.71 | ✅ +15% |
| Evidence Type: Explicit% | 58% | 74% | ✅ +16% |
| Cost Per Successful Answer | $0.0042 | $0.0031 | ✅ −26% |
| ToT Winning Branch Score | 0.71 | 0.79 | ✅ +11% |

Additional panels: Failure Pattern Analysis, p50/p95/p99 Latency Distribution, Error Log Diff.

Every action writes to `rollback_events` with operator identity, timestamp, and metric snapshot. Locked baseline becomes new threshold — system calibrates upward, never downward.

---

## Round 8 — Operator Training & Metric Interpretation

**Judge Question:**
> What processes ensure operators are consistently trained, updated on metric interpretations, and aware of evolving system behaviors?

**Our Answer — 4-Pillar Framework:**

**Pillar 1 — Living Runbook (versioned in Git)**
Evolves from `DEMO_NOTES.md` into a full Operator Handbook with: Metric Definitions (exact SQL + good/concerning value guidance), Decision Trees for each metric pattern, Escalation Paths. Lives in same GitHub repo — versioned and PR-reviewed.

**Pillar 2 — Automated Metric Explanations**
Dashboard shows plain-language interpretations at decision time:
```
✅ Sufficiency Rate: 84% vs 71% baseline (+13%)
   → "Version 2 answers 13% more queries without feedback loops."

⚠️ P95 Latency: 18.2s vs 14.1s (+29%)
   → "Review spans table for slow queries — see session_id list."
```
New operators make good decisions on day one — no memorization needed.

**Pillar 3 — Post-Decision Review Loop**
48-hour retrospective after every promotion/rollback compares metric predictions vs actual outcomes:
```sql
SELECT re.metrics_at_trigger, AVG(s.context_sufficient) as actual_rate
FROM rollback_events re JOIN sessions s ON s.timestamp > re.timestamp
WHERE re.action = 'promote' GROUP BY re.event_id;
```
Thresholds recalibrated if predictions were inaccurate.

**Pillar 4 — Drift Alerts**
System fires alerts when metric distributions shift significantly without a version change:
```
⚠️ DRIFT DETECTED: avg_retrieval_score dropped 0.71 → 0.59 over 14 days.
   Possible causes: query pattern shift, document coverage gap, embedding drift.
   Recommended: Review top 10 queries → consider document refresh.
```

**Core Principle:** The system explains itself to operators at the moment of decision. Training is continuous and embedded in the tooling — not a one-time event.

---

## Quick Reference — Complete Tech Stack

| Component | Spec |
|---|---|
| LLM | `llama-3.3-70b-versatile` via Groq LPU |
| v3.0 Routing (cheap) | `llama-3.1-8b-instant` for Planner/Rewriter/Draft |
| Vector DB | FAISS `IndexFlatIP` (384-dim cosine, exact) |
| Embeddings | `all-MiniLM-L6-v2` (SentenceTransformers) |
| Telemetry DB | SQLite — 10 tables |
| Reasoning Modes | Standard (5-phase) \| CoT (6-stage) \| ToT (3-branch) |
| Instrumented Functions | 8 monkey-patched agents |
| REST Endpoints | 19 total |
| Frontend | React 18 + Vite + TailwindCSS |
| Max Iterations | 2 (hard-capped in `agentic_rag()`) |
| Context Window Cap | 12,000 characters |
| Retry Policy | 5× exponential backoff 2s→32s (`tenacity`) |
| LLM Temperature | 0 (fully deterministic) |
| Cost Saving (v3.0 routing) | ~60-65% vs single large model |
| A/B Testing Metrics | 6 SQL queries on existing schema, zero migration |
| Canary Gates | Shadow → 10% → 50% (human gate) → 100% |
| Rollback Minimum Sample | 30 queries |
| Rollback Window | 20-query rolling window |
| Cooldown After Rollback | 4 hours |
