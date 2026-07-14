from agents.llm import safe_generate

def query_rewriter(sub_query: str):
    prompt = f"""
You are a Query Rewriter for retrieval.

Rewrite the following question into a concise search query optimized for semantic retrieval from a technical document.
Return only the rewritten query and nothing else.

Question:
{sub_query}
"""
    response = safe_generate(prompt)
    return response.strip()
