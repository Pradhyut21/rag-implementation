"""
rag/vector_store.py — FAISS vector store implementation + backend factory.

FaissVectorStore: concrete implementation of BaseVectorStore using FAISS IndexFlatIP.
create_vector_store(): factory function that reads VECTOR_BACKEND env var.

To add a new backend:
    1. Subclass BaseVectorStore
    2. Implement all abstract methods
    3. Add a branch in create_vector_store()
"""
from __future__ import annotations

import logging
import os
import pickle

import faiss
import numpy as np

from rag.base_vector_store import BaseVectorStore

logger = logging.getLogger("agentic_rag.vector_store")


class FaissVectorStore(BaseVectorStore):
    """
    FAISS-based vector store using IndexFlatIP (inner product = cosine similarity
    when embeddings are L2-normalized, as produced by sentence-transformers).
    """

    def __init__(self) -> None:
        self.index: faiss.Index | None = None
        self.chunks: list[str] = []

    def build_index(self, embeddings: np.ndarray, chunks: list[str]) -> None:
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        self.index = index
        self.chunks = list(chunks)
        logger.info(f"FAISS index built: {len(chunks)} chunks, dim={dimension}")

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[dict]:
        if self.index is None:
            raise ValueError("FAISS index is not built yet.")
        scores, indices = self.index.search(query_embedding, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0], strict=False):
            if idx == -1:
                continue
            results.append({"chunk": self.chunks[idx], "score": float(score), "index": int(idx)})
        return results

    def save(self, index_path: str, chunks_path: str) -> None:
        if self.index is None:
            raise ValueError("No index to save.")
        faiss.write_index(self.index, index_path)
        with open(chunks_path, "wb") as f:
            pickle.dump(self.chunks, f)
        logger.info(f"FAISS index saved → {index_path}")

    def load(self, index_path: str, chunks_path: str) -> None:
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index not found at {index_path}")
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(f"Chunks file not found at {chunks_path}")
        self.index = faiss.read_index(index_path)
        with open(chunks_path, "rb") as f:
            self.chunks = pickle.load(f)
        logger.info(f"FAISS index loaded ← {index_path} ({len(self.chunks)} chunks)")


# ── Backend factory ───────────────────────────────────────────

# Alias for backwards compatibility — existing code that imports VectorStore
# directly will continue to work unchanged.
VectorStore = FaissVectorStore


def create_vector_store(backend: str = "faiss") -> BaseVectorStore:
    """
    Factory function that returns the appropriate vector store implementation.

    Reads VECTOR_BACKEND env var (default: "faiss").

    Args:
        backend: One of "faiss" (default), "pinecone", "pgvector".

    Returns:
        A BaseVectorStore instance ready to build_index / load.

    Migration guide:
        - pinecone: pip install pinecone-client, implement PineconeVectorStore(BaseVectorStore)
        - pgvector: pip install pgvector sqlalchemy, implement PgVectorStore(BaseVectorStore)
    """
    backend = backend.lower()
    if backend == "faiss":
        return FaissVectorStore()
    if backend in ("pinecone", "pgvector", "weaviate"):
        raise NotImplementedError(
            f"Vector backend '{backend}' is not yet implemented. "
            f"Implement a subclass of BaseVectorStore and register it here. "
            f"See rag/base_vector_store.py for the required interface."
        )
    raise ValueError(
        f"Unknown VECTOR_BACKEND='{backend}'. Supported values: 'faiss'. "
        f"Set VECTOR_BACKEND=faiss in your .env to use the default."
    )
