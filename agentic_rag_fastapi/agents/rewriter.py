"""
Query Rewriter Agent for the Agentic RAG pipeline.

Transforms a natural-language sub-question into a concise,
dense-retrieval-optimised search query. This improves FAISS cosine
similarity scores by removing conversational noise and expanding
technical abbreviations.
"""
from __future__ import annotations

import logging

from agents.llm import safe_generate

logger = logging.getLogger("agentic_rag.rewriter")


def query_rewriter(sub_query: str) -> str:
    """
    Rewrite a sub-question for dense semantic retrieval.

    Strips conversational language and produces a concise noun-phrase
    or keyword query that maximises semantic similarity to relevant
    document chunks.

    Args:
        sub_query: A natural-language sub-question from the planner.

    Returns:
        A rewritten search query string (stripped of leading/trailing whitespace).
        Returns the original ``sub_query`` if the rewriter produces an empty result.

    Example::

        >>> query_rewriter("What is the average latency for the standard pipeline?")
        "standard RAG pipeline end-to-end latency benchmarks"
    """
    prompt = f"""You are a Query Rewriter for retrieval.

Rewrite the following question into a concise search query optimized for semantic retrieval from a technical document.
Return only the rewritten query and nothing else.

Question:
{sub_query}
"""
    response = safe_generate(prompt).strip()

    if not response:
        logger.warning("Rewriter returned empty response for sub_query=%r — using original.", sub_query)
        return sub_query

    return response
