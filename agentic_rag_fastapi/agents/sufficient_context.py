"""
Sufficient Context Agent for the Agentic RAG pipeline.

Evaluates whether the retrieved context contains enough information
to answer the user's query. Returns a structured verdict with:

- ``is_context_sufficient``: bool — whether to proceed to synthesis
- ``missing_information``: list[str] — what gaps remain
- ``feedback_log``: str — targeted search query for the next iteration
- ``reasoning_summary``: str — explanation of the verdict
- ``evidence_type``: "explicit" | "partial" | "missing"

Evidence types
--------------
explicit
    The exact answer is directly stated in the retrieved context.
partial
    The topic is covered but key details are missing — retry recommended.
missing
    The context contains no relevant information — retry with different queries.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from agents.llm import safe_generate
from utils.json_utils import extract_json_object

logger = logging.getLogger("agentic_rag.sufficient_context")

VALID_EVIDENCE_TYPES: frozenset[str] = frozenset({"explicit", "partial", "missing"})

_SC_PROMPT_TEMPLATE = """You are a Sufficient Context Agent in an Agentic RAG system.

Your task is to evaluate whether the RETRIEVED CONTEXT below contains enough information
to fully answer the USER QUERY.

USER QUERY:
{query}

RETRIEVED CONTEXT:
{context}

INTERMEDIATE DRAFT (generated from the context):
{draft}

Classify the evidence quality using exactly one of three types:
- "explicit"  → The exact answer is directly and clearly stated in the context.
- "partial"   → The topic is discussed but key details are absent.
- "missing"   → The context contains no relevant information.

Return ONLY a valid JSON object (no explanation, no markdown) with these exact keys:
{{
  "is_context_sufficient": <true if explicit, false if partial or missing>,
  "missing_information": [<list of specific things not found, empty if explicit>],
  "feedback_log": "<one targeted search query to retrieve missing info, empty if explicit>",
  "reasoning_summary": "<one-sentence explanation of your verdict>",
  "evidence_type": "<explicit|partial|missing>"
}}"""


def sufficient_context_agent(
    query: str,
    context: str,
    intermediate_draft: str,
) -> dict[str, Any]:
    """
    Evaluate whether retrieved context is sufficient to answer the query.

    Args:
        query: The original user question.
        context: The aggregated text retrieved from FAISS.
        intermediate_draft: An intermediate draft answer generated from the context.

    Returns:
        A dict with keys:
        - ``is_context_sufficient`` (bool)
        - ``missing_information`` (list[str])
        - ``feedback_log`` (str)
        - ``reasoning_summary`` (str)
        - ``evidence_type`` ("explicit" | "partial" | "missing")

    Notes:
        On any parse failure, returns a conservative fallback with
        ``is_context_sufficient=False`` and ``evidence_type="missing"``.
        This triggers another retrieval iteration rather than producing
        a hallucinated answer.
    """
    prompt = _SC_PROMPT_TEMPLATE.format(
        query=query,
        context=context[:8000],  # Limit context to avoid token overflow
        draft=intermediate_draft[:2000],
    )

    raw_response = safe_generate(prompt)

    try:
        data = extract_json_object(raw_response)

        # Handle LLM wrapping result in a list
        if isinstance(data, list) and data:
            data = data[0]

        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data).__name__}")

        # Normalise evidence_type — enforce known values
        evidence_type = str(data.get("evidence_type", "missing")).lower().strip()
        if evidence_type not in VALID_EVIDENCE_TYPES:
            logger.warning("Unknown evidence_type %r — defaulting to 'missing'", evidence_type)
            evidence_type = "missing"

        # Coerce missing_information to list[str]
        missing_raw = data.get("missing_information", [])
        if isinstance(missing_raw, str):
            missing_info: list[str] = [missing_raw] if missing_raw else []
        elif isinstance(missing_raw, list):
            missing_info = [str(x) for x in missing_raw]
        else:
            missing_info = []

        return {
            "is_context_sufficient": bool(data.get("is_context_sufficient", False)),
            "missing_information": missing_info,
            "feedback_log": str(data.get("feedback_log", "")),
            "reasoning_summary": str(data.get("reasoning_summary", "")),
            "evidence_type": evidence_type,
        }

    except Exception as exc:
        logger.error(
            "SC Agent failed to parse LLM response: %s | raw=%r",
            exc,
            raw_response[:300],
        )
        # Conservative fallback: treat as insufficient to avoid hallucination
        return {
            "is_context_sufficient": False,
            "missing_information": ["Context evaluation failed — retry retrieval."],
            "feedback_log": query,
            "reasoning_summary": f"Failed to parse SC Agent response: {exc}",
            "evidence_type": "missing",
        }
