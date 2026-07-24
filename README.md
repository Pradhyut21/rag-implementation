# 🧠 Agentic RAG Platform

> A self-correcting Retrieval-Augmented Generation pipeline that checks its own work before answering.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org) [![CI](https://github.com/Pradhyut21/rag-implementation/actions/workflows/ci.yml/badge.svg)](https://github.com/Pradhyut21/rag-implementation/actions) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Pradhyut21/rag-implementation/blob/main/LICENSE)

Most RAG systems retrieve once and answer — even when the retrieved context is incomplete. This pipeline plans the query, retrieves in parallel, **audits whether the retrieved context is actually sufficient**, and loops back to re-retrieve if it isn't — before generating an answer. Two selectable reasoning modes (CoT, ToT), full SSE streaming, and a 10-table observability schema logging every decision.

> 📖 Full technical spec: [FEATURES.md](FEATURES.md) · Judge Q&A and design defense: [HACKATHON_QA_LOG.md](HACKATHON_QA_LOG.md)

## 📊 Evaluation Results

Run against a 15-query harness spanning 5 categories (factual, comparative, procedural, multi-hop, missing-info detection) × 3 reasoning modes:

| Metric | Result |
| --- | --- |
| Overall Context Sufficiency Accuracy | 93.3% (14/15 queries grounded) |
| Best-Performing Reasoning Mode | Tree of Thought (ToT) |
| Avg Iterations to Sufficient Context | 1.2 iterations |

Full methodology and per-category breakdown: run `python evaluate_agentic_rag.py` → `evaluation_report.json`.

## 🚀 Quick Start

### Option A — Docker (Recommended)

```bash
cp .env.example .env
# Add your GROQ_API_KEY to .env
docker-compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8002
- API Docs: http://localhost:8002/docs

### Option B — Local Development

```bash
# Backend
cd agentic_rag_fastapi
cp ../.env.example .env
# Edit .env with your GROQ_API_KEY
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8002 --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    React Frontend                    │
│   Landing (3D) → Main App → Observability Dashboard │
└────────────────────┬────────────────────────────────┘
                     │ SSE Streaming / REST
┌────────────────────▼────────────────────────────────┐
│                  FastAPI Backend                     │
│  /upload-doc  /ask  /stream-ask  /vanilla-ask        │
│  /plan  /rewrite  /retrieve-only  /ask-debug         │
└─────────────────────┬───────────────────────────────┘
                      │
     ┌────────────────┼────────────────┐
     ▼                ▼                ▼
┌─────────┐    ┌──────────────┐  ┌──────────────┐
│  FAISS  │    │  Groq LPU    │  │  SQLite 10T  │
│  Index  │    │  llama-3.3   │  │  Observ. DB  │
└─────────┘    └──────────────┘  └──────────────┘
```

**Why Groq:** the agentic loop makes 4–6 LLM calls per query (plan → rewrite → retrieve → audit → synthesize). Groq's LPU inference keeps that chain fast enough to stream stage-by-stage in real time rather than making the user wait on a single slow call.

**Why FAISS over a managed vector DB:** zero external dependency for a self-contained demo/deploy — `IndexFlatIP` gives exact cosine similarity with no infra to provision, at the query volumes this pipeline targets.

### 5-Phase Agentic Pipeline
```
Query → [Planner] → [Query Rewriter] → [FAISS Fanout]
     → [Sufficient Context Agent] → [Feedback Loop]
     → [Synthesis Agent] → Answer + Citations + Trace
```

---

## ✨ Features

> 📖 For a detailed technical specification of all system capabilities, see [FEATURES.md](FEATURES.md).

### AI Pipeline
| Feature | Description |
|---------|-------------|
| **Standard Mode** | 5-phase agentic loop with self-correcting feedback |
| **Chain of Thought** | 6-stage sequential reasoning with explicit intermediate outputs |
| **Tree of Thought** | 3-branch parallel evaluation scored across 5 dimensions |
| **SC Agent** | 3-state context auditor: explicit / partial / missing |
| **Parallel Fanout** | All sub-queries retrieved concurrently via ThreadPoolExecutor |
| **SSE Streaming** | Real-time stage-by-stage response streaming |
| **OCR Support** | Scanned PDF handling via Unstructured.io + Tesseract fallback |

### Security
| Feature | Implementation |
|---------|----------------|
| **API Key Auth** | X-API-Key header validation |
| **Rate Limiting** | slowapi: 30 req/min (query), 20/hr (upload) |
| **CORS** | Restricted to configured allowed origins |
| **File Validation** | Extension + PDF magic bytes + 20MB size limit |
| **Path Sanitization** | `os.path.basename()` prevents directory traversal |
| **Atomic Writes** | Registry writes use `os.replace()` for corruption prevention |
| **Thread Safety** | `threading.Lock()` on vector store cache |

### Observability (10-Table SQLite Schema)
- Sessions, Spans, Events, Errors, Tokens, Latency
- CoT Stages, ToT Branches, Branch Scores, Branch Evaluations
- Real-time dashboard with replay functionality

### Frontend
- 🎨 Claude-style white theme with brand violet
- 📱 Fully responsive (mobile, tablet, desktop)
- ♿ WCAG 2.1 AA accessible (ARIA, focus rings, reduced motion, skip links)
- 💬 Conversation threading with persistent message history
- ⚡ Real-time streaming with stage indicators
- 🔔 Toast notification system (success/error/warning/info)
- 🔍 Dev tools: retrieval inspector, planner, query rewriter
- 🖥️ Observability dashboard with session replay

---

## 🔒 API Reference

All protected endpoints require the `X-API-Key` header.

```bash
# Example query with auth
curl -X POST http://localhost:8002/ask-debug \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-rag-2026" \
  -d '{"query": "What is the SC agent?", "doc_id": "abc12345", "reasoning_mode": "cot"}'
```

### Endpoints

| Method | Path | Auth | Rate Limit | Description |
|--------|------|------|------------|-------------|
| GET | `/health` | No | — | Health check |
| POST | `/upload-doc` | Yes | 20/hr | Upload PDF/DOCX |
| POST | `/upload-doc-ocr` | Yes | 10/hr | Upload scanned PDF with OCR |
| GET | `/documents` | No | — | List all documents |
| DELETE | `/documents/{doc_id}` | Yes | — | Delete document |
| POST | `/ask` | Yes | 30/min | Agentic RAG query |
| POST | `/vanilla-ask` | Yes | 30/min | Single-pass RAG |
| POST | `/ask-debug` | Yes | 20/min | Debug mode (saves run log) |
| POST | `/stream-ask` | Yes | 20/min | SSE streaming query |
| POST | `/plan` | Yes | 30/min | Query decomposition only |
| POST | `/rewrite` | Yes | 30/min | Query rewriting only |
| POST | `/retrieve-only` | Yes | 30/min | FAISS retrieval only |
| GET | `/reasoning/cot/{session_id}` | No | — | CoT stage details |
| GET | `/reasoning/tot/{session_id}` | No | — | ToT branch details |

### Query Request Schema
```json
{
  "query": "string (1-2000 chars)",
  "doc_id": "string (8-char hex)",
  "top_k": "integer (1-20, default 3)",
  "reasoning_mode": "standard | cot | tot",
  "response_mode": "compact | detailed",
  "include_trace": "boolean"
}
```

---

## 🧪 Evaluation

Run the 15-query evaluation harness (covers 5 categories × 3 modes):

```bash
cd agentic_rag_fastapi
python evaluate_agentic_rag.py
```

**Query categories:** factual, comparative, procedural, multi-hop, missing-info detection  
**Modes tested:** standard, cot, tot  
**Output:** `evaluation_report.json` with per-category accuracy, avg iterations, and mode comparison

---

## 🛠️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | Required | Groq API key |
| `API_KEY` | `demo-rag-2026` | Backend API protection key |
| `ALLOWED_ORIGINS` | `localhost:5173` | CORS allowed origins |
| `DEMO_MODE` | `false` | Skip API key check in demo (set true for local dev) |
| `MAX_FILE_SIZE_MB` | `20` | Max upload size |
| `VITE_API_URL` | `http://localhost:8002` | Frontend → backend URL |
| `VITE_API_KEY` | `demo-rag-2026` | Frontend API key |

---

## 📁 Project Structure

```
agentic-rag/
├── agentic_rag_fastapi/
│   ├── app.py                  # FastAPI app (auth, rate limiting, streaming)
│   ├── schemas.py              # Pydantic models with validation
│   ├── evaluate_agentic_rag.py # 15-query evaluation harness
│   ├── Dockerfile              # Multi-stage production build
│   ├── agents/
│   │   ├── agentic_loop.py     # Parallel fanout + feedback loop
│   │   ├── cot_reasoner.py     # Chain of Thought implementation
│   │   ├── tree_of_thought.py  # Tree of Thought implementation
│   │   ├── sufficient_context.py # SC Agent (3-state auditor)
│   │   ├── planner.py          # Query decomposition
│   │   ├── rewriter.py         # Dense retrieval optimizer
│   │   ├── synthesis.py        # Final answer generation
│   │   └── llm.py              # Groq client with retry logic
│   ├── rag/
│   │   ├── ingestion.py        # PDF/DOCX + OCR extraction
│   │   ├── embeddings.py       # sentence-transformers wrapper
│   │   ├── vector_store.py     # FAISS IndexFlatIP
│   │   └── retrieval.py        # Cosine similarity retrieval
│   └── observability/          # 10-table SQLite telemetry
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Landing ↔ MainApp router
│   │   ├── MainApp.jsx         # Chat + conversation threading
│   │   ├── pages/LandingPage.jsx # 3D animated landing
│   │   ├── api/client.js       # Axios + SSE streaming client
│   │   └── components/
│   │       ├── Toast.jsx       # Notification system
│   │       └── ObservabilityWrapper.jsx
│   ├── Dockerfile.frontend     # Nginx multi-stage build
│   └── index.html              # Favicon + skip links + SEO
├── docker-compose.yml          # Full stack orchestration
├── .env.example                # Configuration template
└── README.md
```

---

## 🏆 Hackathon Evaluation Gaps — Addressed

| Judge Criticism | Status | Implementation |
|-----------------|--------|----------------|
| No JWT/Auth | ✅ Fixed | API Key auth with demo-mode bypass |
| No rate limiting | ✅ Fixed | slowapi: per-endpoint limits |
| Stateful architecture | ✅ Improved | Thread-safe cache, atomic writes |
| OCR missing | ✅ Fixed | Unstructured.io + Tesseract pipeline |
| Only 2 eval queries | ✅ Fixed | 15 queries × 3 modes × 5 categories |
| No deployment | ✅ Fixed | Docker + docker-compose |
| CORS wildcard | ✅ Fixed | Configured allowed origins |
| No streaming | ✅ Fixed | SSE /stream-ask endpoint |
| No conversation history | ✅ Fixed | Persistent message threading |
| No mobile support | ✅ Fixed | Responsive + hamburger sidebar |
| No accessibility | ✅ Fixed | WCAG 2.1 AA: ARIA, focus, motion |
| No favicon | ✅ Fixed | Inline SVG favicon |
| No success toasts | ✅ Fixed | Toast notification system |
| No stage indicators | ✅ Fixed | Real-time Planning→Synthesizing |
| Race condition on dict | ✅ Fixed | threading.Lock() |
| Registry corruption risk | ✅ Fixed | Atomic os.replace() writes |
| No file size limit | ✅ Fixed | 20MB max + magic byte validation |
| Path traversal risk | ✅ Fixed | os.path.basename() sanitization |
| Sequential fanout | ✅ Fixed | ThreadPoolExecutor parallel fanout |

---

## 📐 Architecture Decision Records

Key technical decisions are documented as ADRs in [`docs/adr/`](docs/adr/):

| ADR | Decision | Why |
|-----|----------|-----|
| [ADR-001](docs/adr/ADR-001-faiss-vector-store.md) | **FAISS** over ChromaDB/Pinecone | Zero-latency in-process search; no network hop for 6–9 queries/request |
| [ADR-002](docs/adr/ADR-002-groq-llm-provider.md) | **Groq LPU** over OpenAI/Anthropic | 4–8× faster (0.8s vs 3–8s per call); free tier covers demo load |
| [ADR-003](docs/adr/ADR-003-sqlite-observability.md) | **SQLite** over PostgreSQL/Prometheus | Zero config, ACID, relational joins for replay; SQLAlchemy abstraction ready for PG migration |

---

## 📄 License

MIT License — see [LICENSE](LICENSE)
