"""
Query Rewriter Agent for the Agentic RAG pipeline.

Transforms a sub-question into a technical search query
optimized for dense vector retrieval (FAISS + sentence-transformers).
"""

from __future__ import annotations

import logging
import agents.llm as llm

logger = logging.getLogger("agentic_rag.rewriter")


def query_rewriter(sub_query: str) -> str:
    """
    Rewrite a sub-query for dense retrieval.

    Args:
        sub_query: A single sub-question string.

    Returns:
        The rewritten search query string. Falls back to original
        if the LLM yields an empty or invalid response.
    """
    prompt = f"""You are a Query Rewriter for retrieval.

Rewrite the following question into a concise search query optimized for semantic retrieval from a technical document.
Return only the rewritten query and nothing else.

Question:
{sub_query}
"""
    response = llm.safe_generate(prompt).strip()

    if not response:
        logger.warning(
            "Rewriter returned empty response for sub_query=%r — using original.", sub_query
        )
        return sub_query

    return response
