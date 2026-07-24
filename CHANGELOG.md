# Changelog

All notable changes to this project are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Centralized `config.py` with pydantic-settings for all runtime parameters
- `tests/` package with 40+ unit tests across agents, ingestion, schemas, and API
- GitHub Actions CI pipeline (lint, typecheck, security, test, Docker build)
- GitHub Actions CD pipeline (GHCR push, GitHub Releases)
- CodeQL Advanced Security scanning for Python and JavaScript
- Pre-commit hooks (ruff, bandit, detect-secrets, prettier, commitizen)
- `Makefile` with 20+ developer commands
- `CONTRIBUTING.md` development guide
- `SECURITY.md` vulnerability reporting policy
- `pyproject.toml` with unified tool configuration (ruff, mypy, bandit, pytest, coverage)
- `.pre-commit-config.yaml` with 15 hooks

---

## [3.0.0] — 2026-07-24

### Added
- **SSE Streaming endpoint** (`POST /stream-ask`) with real-time stage events
- **API Key authentication** on all write/query endpoints (`X-API-Key` header)
- **Rate limiting** via slowapi (30 req/min for queries, 20/hr for uploads)
- **Parallel fanout** in `search_fanout()` using `ThreadPoolExecutor`
- **OCR support** (`POST /upload-doc-ocr`) via Unstructured.io + Tesseract fallback
- **Atomic registry writes** using `os.replace()` temp-file swap
- **Thread-safe vector store cache** with `threading.Lock()`
- **File validation**: magic byte check for PDFs, 20MB size limit, filename sanitization
- **Input validation**: query length capped at 2000 chars, `ReasoningMode` enum, Field constraints
- **Docker multi-stage builds** for both backend (Python) and frontend (nginx)
- **docker-compose.yml** with named volumes, health checks, and network isolation
- **Conversation threading** in frontend (persistent message history)
- **Loading stage indicators** (Planning → Rewriting → Retrieving → Auditing → Synthesizing)
- **Toast notification system** (success/error/warning/info with auto-dismiss)
- **Mobile responsive** layout with hamburger sidebar and 44px touch targets
- **WCAG 2.1 AA accessibility** (ARIA labels, focus rings, prefers-reduced-motion, skip links)
- **15-query evaluation harness** covering 5 categories × 3 reasoning modes
- **Restricted CORS** (no wildcard — configured allowed origins list)
- **Inline SVG favicon** and Open Graph meta tags
- **Cancel query** button (aborts streaming mid-response)
- **OCR toggle** in sidebar for scanned PDF uploads

### Changed
- `ALLOWED_ORIGINS` restricted from `*` to configured list
- `registry.json` writes now use `os.replace()` instead of direct `open()`
- `search_fanout()` now parallel (was sequential) — reduces latency by ~60%
- `schemas.py` migrated from bare strings to `ReasoningMode`/`ResponseMode` enums
- Evaluation harness expanded from 2 to 15 queries

### Fixed
- Race condition on `loaded_vector_stores` dict under concurrent requests
- `registry.json` corruption on concurrent writes
- Directory traversal vulnerability in filename handling
- Missing `evidence_type` validation in SC Agent response
- `missing_information` field type coercion (string → list)

### Security
- Added `X-API-Key` authentication to all mutation endpoints
- Restricted CORS from wildcard to explicit origin list
- Added file size limit (20MB) and PDF magic byte validation
- Added filename sanitization against directory traversal
- Added rate limiting per endpoint category

---

## [2.0.0] — 2026-07-22

### Added
- Tree of Thought (ToT) reasoning mode with 3-branch parallel evaluation
- Chain of Thought (CoT) reasoning mode with 6-stage sequential pipeline
- 10-table SQLite observability schema with session replay
- Monkey-patching observability layer (zero-overhead tracing)
- ContextVar propagation for session_id across async boundaries
- ObservabilityWorkspace React dashboard component
- 3D animated landing page with scroll effects
- Claude-style white-theme main application
- Debug runs directory with JSON execution logs

---

## [1.0.0] — 2026-07-20

### Added
- Initial FastAPI backend with document upload, indexing, and querying
- FAISS IndexFlatIP vector store with cosine normalisation
- sentence-transformers all-MiniLM-L6-v2 embedding model
- Sentence-based chunking with configurable size and overlap
- Standard 5-phase agentic loop (Plan → Rewrite → Retrieve → SC-Check → Synthesise)
- Sufficient Context Agent with 3-state evidence classification
- Tenacity retry logic on Groq API rate-limit errors
- React frontend with document upload and query interface
- `/plan`, `/rewrite`, `/retrieve-only` agent inspection endpoints
- Registry-based document management with `registry.json`
