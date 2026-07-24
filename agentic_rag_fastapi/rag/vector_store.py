import faiss
import os
import pickle
import numpy as np


class VectorStore:
    def __init__(self):
        self.index = None
        self.chunks = []

    def build_index(self, embeddings: np.ndarray, chunks):
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # cosine-like because embeddings normalized
        index.add(embeddings)

        self.index = index
        self.chunks = chunks

    def search(self, query_embedding: np.ndarray, top_k: int = 5):
        if self.index is None:
            raise ValueError("FAISS index is not built yet.")

        scores, indices = self.index.search(query_embedding, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append({"chunk": self.chunks[idx], "score": float(score), "index": int(idx)})

        return results

    def save(self, index_path: str, chunks_path: str):
        if self.index is None:
            raise ValueError("No index to save.")

        faiss.write_index(self.index, index_path)

        with open(chunks_path, "wb") as f:
            pickle.dump(self.chunks, f)

    def load(self, index_path: str, chunks_path: str):
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index not found at {index_path}")
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(f"Chunks file not found at {chunks_path}")

        self.index = faiss.read_index(index_path)

        with open(chunks_path, "rb") as f:
            self.chunks = pickle.load(f)
