def retrieve(query: str, embedding_model, vector_store, top_k: int = 5):
    query_embedding = embedding_model.embed_query(query)
    results = vector_store.search(query_embedding, top_k=top_k)
    return results

def format_context(retrieved_results):
    return "\n\n".join(
        [f"[Chunk {i+1}] {item['chunk']}" for i, item in enumerate(retrieved_results)]
    )
