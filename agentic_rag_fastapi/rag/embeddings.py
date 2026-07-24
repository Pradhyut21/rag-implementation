from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingModel:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts):
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return np.array(embeddings, dtype="float32")

    def embed_query(self, query: str):
        embedding = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        return embedding.astype("float32")
