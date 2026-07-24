from __future__ import annotations

from datetime import UTC, datetime
import logging
import time
from typing import TYPE_CHECKING, Any
import uuid

if TYPE_CHECKING:
    from collections.abc import Callable

from agents.llm import safe_generate
from agents.planner import planner_agent
from agents.rewriter import query_rewriter
from agents.sufficient_context import sufficient_context_agent
from agents.synthesis import synthesis_agent
from observability.storage.db import save_reasoning_chain, save_reasoning_stage
from rag.retrieval import retrieve

logger = logging.getLogger("agentic_rag.cot_reasoner")


def run_cot_reasoning(
    query: str,
    embedding_model: Any,
    vector_store: Any,
    top_k: int = 3,
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Executes the Chain of Thought (CoT) reasoning workflow, running through
    6 structured reasoning stages, measuring latency, and persisting telemetry.
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    logger.info(f"Running CoT reasoning workflow for session: {session_id}")

    # Save the root reasoning chain entry
    timestamp = datetime.now(UTC).isoformat()
    save_reasoning_chain(session_id, query, timestamp)

    stages_log: list[dict[str, Any]] = []

    # helper to run and record a stage
    def execute_stage(
        index: int, name: str, input_str: str, action_fn: Callable[[], tuple[Any, dict[str, Any]]]
    ) -> tuple[Any, dict[str, Any]]:
        start_time = time.time()
        stage_id = str(uuid.uuid4())
        status = "SUCCESS"
        output_summary = ""
        result = None

        try:
            result, output_summary = action_fn()
        except Exception as e:
            status = "FAILED"
            output_summary = f"Stage failed with error: {e!s}"
            logger.error(f"Error in stage {name}: {e}")

        duration = time.time() - start_time

        stage_data = {
            "stage_id": stage_id,
            "session_id": session_id,
            "stage_index": index,
            "stage_name": name,
            "input_data": input_str,
            "output_summary": output_summary,
            "execution_time": round(duration, 3),
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Save to SQLite db
        save_reasoning_stage(stage_data)
        stages_log.append(stage_data)

        if status == "FAILED" and result is None:
            raise RuntimeError(f"CoT reasoning failed at stage: {name}")

        return result, stage_data

    # --- Step 1: Understand the user query ---
    def stage_1_action() -> tuple[str, str]:
        prompt = f"""
Analyze the user query below. Write a short explanation of what the user is asking, identifying the core topic, implicit constraints, and subject area.
Do not use markdown formatting. Keep it to 2-3 sentences.

Query:
{query}
"""
        summary = safe_generate(prompt)
        return summary, summary

    query_analysis, _ = execute_stage(
        index=1, name="Step 1: Understand the user query", input_str=query, action_fn=stage_1_action
    )

    # --- Step 2: Identify required information ---
    def stage_2_action() -> tuple[str, str]:
        prompt = f"""
Given this query analysis: "{query_analysis}",
List the critical factual points, details, or documentation segments required to answer the query accurately.
Do not use markdown formatting. Keep it concise.
"""
        required_info = safe_generate(prompt)
        return required_info, required_info

    required_info, _ = execute_stage(
        index=2,
        name="Step 2: Identify required information",
        input_str=f"Analysis: {query_analysis}",
        action_fn=stage_2_action,
    )

    # --- Step 3: Determine retrieval strategy ---
    def stage_3_action() -> tuple[list[str], str]:
        sub_queries = planner_agent(query)
        summary = f"Planner split query into sub-queries: {sub_queries}"
        return sub_queries, summary

    sub_queries, _ = execute_stage(
        index=3,
        name="Step 3: Determine retrieval strategy",
        input_str=f"Required info: {required_info}",
        action_fn=stage_3_action,
    )

    # --- Step 4: Retrieve supporting evidence ---
    def stage_4_action() -> tuple[tuple[str, list[dict[str, Any]]], str]:
        retrieved_results = []
        rewritten_queries = []

        for sq in sub_queries:
            rewritten = query_rewriter(sq)
            rewritten_queries.append(rewritten)
            results = retrieve(rewritten, embedding_model, vector_store, top_k=top_k)
            retrieved_results.extend(results)

        # Deduplicate retrieved context
        seen_chunks = set()
        aggregated_context_list = []
        for r in retrieved_results:
            chunk = r["chunk"]
            if chunk not in seen_chunks:
                seen_chunks.add(chunk)
                aggregated_context_list.append(chunk)
        aggregated_context = "\n\n".join(aggregated_context_list)

        summary = (
            f"Retrieved {len(aggregated_context_list)} unique chunks matching rewritten queries."
        )
        return (aggregated_context, retrieved_results), summary

    (aggregated_context, retrieved_results), _ = execute_stage(
        index=4,
        name="Step 4: Retrieve supporting evidence",
        input_str=f"Sub-queries: {sub_queries}",
        action_fn=stage_4_action,
    )

    # --- Step 5: Evaluate context sufficiency ---
    # Create intermediate draft first
    draft_prompt = f"Use the context to answer the query:\nQUERY: {query}\nCONTEXT: {aggregated_context}\nWrite a draft answer."
    intermediate_draft = safe_generate(draft_prompt)

    def stage_5_action() -> tuple[dict[str, Any], str]:
        sc_result = sufficient_context_agent(query, aggregated_context, intermediate_draft)
        summary = (
            f"Context Sufficient: {sc_result['is_context_sufficient']}. "
            f"Evidence Type: {sc_result['evidence_type']}. "
            f"Reasoning: {sc_result['reasoning_summary']}"
        )
        return sc_result, summary

    sc_result, _ = execute_stage(
        index=5,
        name="Step 5: Evaluate context sufficiency",
        input_str=f"Context Length: {len(aggregated_context)} characters",
        action_fn=stage_5_action,
    )

    # --- Step 6: Generate grounded answer ---
    def stage_6_action() -> tuple[str, str]:
        final_answer = synthesis_agent(query, aggregated_context)
        summary = f"Grounded answer synthesized. Length: {len(final_answer)} characters."
        return final_answer, summary

    final_answer, _ = execute_stage(
        index=6,
        name="Step 6: Generate grounded answer",
        input_str=f"Final context length: {len(aggregated_context)}",
        action_fn=stage_6_action,
    )

    # citations
    citations = []
    seen_indices = set()
    for ret in retrieved_results:
        idx = ret["index"]
        if idx not in seen_indices:
            seen_indices.add(idx)
            citations.append(
                {
                    "chunk_index": idx,
                    "text_preview": ret["chunk"][:200] + "..."
                    if len(ret["chunk"]) > 200
                    else ret["chunk"],
                    "score": ret["score"],
                }
            )
    citations = sorted(citations, key=lambda x: x["score"], reverse=True)[:5]

    return {
        "query": query,
        "answer": final_answer,
        "context_sufficient": sc_result.get("is_context_sufficient", True),
        "missing_information": sc_result.get("missing_information", []),
        "citations": citations,
        "stages": stages_log,
        "final_context": aggregated_context,
    }
