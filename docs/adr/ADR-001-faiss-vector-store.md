# ADR-001: FAISS as Vector Store

**Status:** Accepted  
**Date:** 2026-07-01  
**Author:** Pradhyut21

---

## Context

The Agentic RAG Platform requires a vector similarity search engine to retrieve semantically relevant document chunks during the retrieval phase. Options considered:

| Option | Pros | Cons |
|--------|------|------|
| **FAISS** (chosen) | Zero latency (in-process), no network hop, Apache 2.0, battle-tested at Meta scale | Single-node (no native distributed mode), requires manual index persistence |
| **ChromaDB** | Embedded or server mode, built-in metadata filtering | Extra network hop in server mode, more complex setup for hackathon |
| **Pinecone** | Fully managed, horizontal scale | Requires API key + billing, network latency per query, vendor lock-in |
| **Weaviate** | Hybrid search (BM25 + vector), GraphQL API | Heavyweight for single-document context, JVM dependency |
| **Qdrant** | Rust-native, payload filtering | Overkill for <10k chunks per document |

## Decision

Use **FAISS `IndexFlatIP`** (inner product / cosine similarity after L2 normalization) embedded directly in the FastAPI process.

## Rationale

1. **Zero added latency**: FAISS runs in-process — no network round-trip to a vector database server. This is critical when the agentic loop runs FAISS queries 6–9 times per request (3 branches × 3 sub-queries in ToT mode).
2. **Per-document index isolation**: Each uploaded document gets its own `.index` file. This maps directly to the multi-tenant access model — no risk of cross-document chunk leakage.
3. **Deterministic scoring**: `IndexFlatIP` with normalized vectors produces exact cosine similarity (no approximation error). This is important for the Branch Scoring system in Tree of Thought, where small score differences determine branch selection.
4. **No infrastructure dependencies**: The platform runs fully on `docker-compose up` without any third-party service accounts or API keys beyond Groq.

## Trade-offs Accepted

- **No distributed scale**: FAISS is single-node. If the platform needs horizontal scaling, indexes would need to be shared via NFS or migrated to Qdrant/Pinecone. This is the planned v4.0 migration path.
- **Manual persistence**: Index files must be explicitly saved/loaded. This is handled by `vector_store.py` with atomic `os.replace()` writes to prevent corruption.

## Consequences

- `rag/vector_store.py`: FAISS `IndexFlatIP`, thread-safe with `threading.Lock()`
- `rag/retrieval.py`: Returns `(chunk, score, index)` tuples ranked by cosine similarity
- Index files: `data/indexes/{doc_id}.index` + `{doc_id}_chunks.pkl`
