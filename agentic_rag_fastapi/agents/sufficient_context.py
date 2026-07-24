"""
Sufficient Context Agent for the Agentic RAG pipeline.

Evaluates whether the retrieved context contains enough information
to answer the user's query. Returns a structured verdict with:

- ``is_context_sufficient``: bool — whether to proceed to synthesis
- ``missing_information``: list[str] — what gaps remain
- ``feedback_log``: str — targeted search query for the next iteration
- ``reasoning_summary``: str — explanation of the verdict
- ``evidence_type``: "explicit" | "partial" | "missing"
"""

from __future__ import annotations

import logging
from typing import Any

from agents.llm import fast_generate
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
- "partial"   → The topic is covered, but specific metrics, numbers, or facts asked by the user are missing.
- "missing"   → The context contains no relevant information.

Respond with a single valid JSON object with these keys:
  "is_context_sufficient": bool,
  "missing_information": list of strings,
  "feedback_log": string,
  "reasoning_summary": string,
  "evidence_type": string

Do not include any explanation outside the JSON object.
"""


def sufficient_context_agent(
    query: str,
    context: str,
    intermediate_draft: str = "",
) -> dict[str, Any]:
    """
    Audit retrieved context against the user query.

    Args:
        query: The raw user question.
        context: The aggregated retrieved text chunks.
        intermediate_draft: Optional draft answer generated so far.

    Returns:
        A dict containing:
        - ``is_context_sufficient`` (bool)
        - ``missing_information`` (list[str])
        - ``feedback_log`` (str)
        - ``reasoning_summary`` (str)
        - ``evidence_type`` ("explicit" | "partial" | "missing")
    """
    prompt = _SC_PROMPT_TEMPLATE.format(
        query=query,
        context=context[:3000],
        draft=intermediate_draft[:500],
    )

    raw_response = fast_generate(prompt, max_tokens=256)

    try:
        data = extract_json_object(raw_response)
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            data = data[0]
        if isinstance(data, dict):
            evidence_type = str(data.get("evidence_type", "")).lower()
            if evidence_type not in VALID_EVIDENCE_TYPES:
                evidence_type = "missing"

            missing_info = data.get("missing_information", [])
            if isinstance(missing_info, str):
                missing_info = [missing_info] if missing_info else []
            elif not isinstance(missing_info, list):
                missing_info = []

            return {
                "is_context_sufficient": bool(data.get("is_context_sufficient", False)),
                "missing_information": [str(x) for x in missing_info],
                "feedback_log": str(data.get("feedback_log", "")),
                "reasoning_summary": str(data.get("reasoning_summary", "")),
                "evidence_type": evidence_type,
            }
    except Exception as exc:
        logger.warning("SC Agent failed to parse response: %s | raw=%r", exc, raw_response[:200])

    return {
        "is_context_sufficient": False,
        "missing_information": ["Failed to parse sufficiency audit response"],
        "feedback_log": f"Re-query context for: {query}",
        "reasoning_summary": "Failed to parse SC response — defaulting to insufficient.",
        "evidence_type": "missing",
    }
