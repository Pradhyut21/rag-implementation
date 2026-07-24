"""
Planner Agent for the Agentic RAG pipeline.

Decomposes a complex user query into 2-5 focused sub-questions,
each targeting a distinct aspect of the information need.
This narrows the retrieval space and improves FAISS recall.
"""
from __future__ import annotations

import logging

from agents.llm import safe_generate
from utils.json_utils import extract_json_object

logger = logging.getLogger("agentic_rag.planner")


def planner_agent(query: str) -> list[str]:
    """
    Decompose a user query into targeted sub-questions.

    Args:
        query: The raw user question to decompose.

    Returns:
        A list of 2-5 sub-query strings. Falls back to ``[query]``
        if the LLM response cannot be parsed as a JSON array.

    Example::

        >>> planner_agent("How does the feedback loop improve RAG?")
        ["What is the feedback loop in RAG?",
         "How does the SC agent detect missing information?",
         "What queries are generated from feedback?"]
    """
    prompt = f"""You are a Planner Agent in an Agentic RAG system.

Break the user's query into 2 to 5 focused sub-questions that would help retrieve the required information.
Return ONLY a valid JSON array of strings.
Do not add any explanation.

User Query:
{query}
"""
    response = safe_generate(prompt)

    try:
        sub_queries = extract_json_object(response)
        if isinstance(sub_queries, list) and sub_queries:
            return [str(x) for x in sub_queries]
    except Exception as exc:
        logger.warning("Planner failed to parse LLM response: %s | response=%r", exc, response[:200])

    logger.info("Planner falling back to original query.")
    return [query]
