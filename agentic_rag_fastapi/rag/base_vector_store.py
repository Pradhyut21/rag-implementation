"""
rag/base_vector_store.py — Abstract interface for vector store backends.

Defines the contract any vector store implementation must satisfy.
Allows swapping FAISS for Pinecone, pgvector, Weaviate, etc. by:
  1. Subclassing BaseVectorStore
  2. Setting VECTOR_BACKEND env var
  3. Returning the implementation from create_vector_store()

Example future backends:
    VECTOR_BACKEND=pinecone  → PineconeVectorStore
    VECTOR_BACKEND=pgvector  → PgVectorStore
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


class BaseVectorStore(ABC):
    """
    Abstract base class for vector store backends.

    All implementations must support indexing, similarity search,
    and persistence (save/load).
    """

    @abstractmethod
    def build_index(self, embeddings: np.ndarray, chunks: list[str]) -> None:
        """
        Build the search index from embedding vectors and their source chunks.

        Args:
            embeddings: 2D float32 array of shape (n_chunks, embedding_dim).
            chunks: Corresponding text chunks, one per embedding row.
        """
        ...

    @abstractmethod
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[dict]:
        """
        Search for the top_k most similar chunks.

        Args:
            query_embedding: 2D float32 array of shape (1, embedding_dim).
            top_k: Number of results to return.

        Returns:
            List of dicts with keys: ``chunk`` (str), ``score`` (float), ``index`` (int).
        """
        ...

    @abstractmethod
    def save(self, index_path: str, chunks_path: str) -> None:
        """Persist the index and chunks to disk."""
        ...

    @abstractmethod
    def load(self, index_path: str, chunks_path: str) -> None:
        """Load the index and chunks from disk."""
        ...
