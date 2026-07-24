import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from rag.retrieval import retrieve, format_context
from agents.planner import planner_agent
from agents.rewriter import query_rewriter
from agents.sufficient_context import sufficient_context_agent
from agents.synthesis import synthesis_agent
from agents.llm import safe_generate

logger = logging.getLogger("agentic_rag.agentic_loop")

MAX_CONTEXT_CHARS = 14000   # Increased from 12k
MAX_ITERATIONS = 2


def build_intermediate_draft(query: str, context: str) -> str:
    prompt = f"""You are generating an intermediate draft answer.
Use the context below to draft a possible answer to the user's question.

USER QUERY:
{query}

CONTEXT:
{context}

Write a concise draft answer grounded only in the context."""
    return safe_generate(prompt)


def _process_single_subquery(sq: str, embedding_model, vector_store, top_k: int) -> dict:
    """Worker function for parallel fanout — runs in thread pool."""
    rewritten = query_rewriter(sq)
    retrieved = retrieve(rewritten, embedding_model, vector_store, top_k=top_k)
    return {
        "sub_query": sq,
        "rewritten_query": rewritten,
        "retrieved": retrieved,
    }


def search_fanout(sub_queries, embedding_model, vector_store, top_k=3):
    """
    Parallelised fan-out retrieval.
    All sub-queries are processed concurrently via ThreadPoolExecutor,
    cutting latency from O(N × LLM_time) to O(max_LLM_time).
    """
    results = [None] * len(sub_queries)

    with ThreadPoolExecutor(max_workers=min(len(sub_queries), 6)) as executor:
        future_to_idx = {
            executor.submit(_process_single_subquery, sq, embedding_model, vector_store, top_k): i
            for i, sq in enumerate(sub_queries)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                logger.error(f"Sub-query {sub_queries[idx]!r} failed: {e}")
                results[idx] = {
                    "sub_query": sub_queries[idx],
                    "rewritten_query": sub_queries[idx],
                    "retrieved": [],
                }

    return results


def aggregate_fanout_context(fanout_results):
    seen = set()
    ordered_chunks = []
    for item in fanout_results:
        for r in item["retrieved"]:
            chunk = r["chunk"]
            if chunk not in seen:
                seen.add(chunk)
                ordered_chunks.append(chunk)
    return "\n\n".join(ordered_chunks)


def trim_context(context: str, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    if len(context) <= max_chars:
        return context
    # Trim at sentence boundary where possible
    trimmed = context[:max_chars]
    last_period = trimmed.rfind(".")
    if last_period > max_chars * 0.8:
        return trimmed[: last_period + 1]
    return trimmed


def vanilla_rag(query: str, embedding_model, vector_store, top_k: int = 5):
    logger.info(f"Vanilla RAG: {query!r}")
    retrieved = retrieve(query, embedding_model, vector_store, top_k=top_k)
    context = format_context(retrieved)
    answer = synthesis_agent(query, context)
    citations = [
        {
            "chunk_index": r["index"],
            "text_preview": r["chunk"][:200] + ("..." if len(r["chunk"]) > 200 else ""),
            "score": r["score"],
        }
        for r in retrieved
    ]
    return {
        "query": query,
        "retrieved_chunks": retrieved,
        "context": context,
        "answer": answer,
        "citations": citations,
    }


def agentic_rag(
    query: str,
    embedding_model,
    vector_store,
    max_iterations: int = MAX_ITERATIONS,
    top_k: int = 3,
    reasoning_mode: str = "standard",
):
    logger.info(f"Agentic RAG | query={query!r} | mode={reasoning_mode}")

    import uuid as _uuid
    from observability.tracing.context import get_trace_context

    ctx = get_trace_context()
    session_id = ctx.get("session_id") or str(_uuid.uuid4())

    # ── Chain of Thought ──────────────────────────────────────
    if reasoning_mode == "cot":
        from agents.cot_reasoner import run_cot_reasoning
        result = run_cot_reasoning(
            query=query,
            embedding_model=embedding_model,
            vector_store=vector_store,
            top_k=top_k,
            session_id=session_id,
        )
        return {
            "query": result["query"],
            "answer": result["answer"],
            "iterations": 1,
            "context_sufficient": result["context_sufficient"],
            "missing_information": result["missing_information"],
            "trace": [],
            "final_context": result["final_context"],
            "citations": result["citations"],
            "fallback_used": False,
            "session_id": session_id,
            "evidence_type": result.get("evidence_type", "explicit"),
        }

    trace = []
    fallback_used = False

    # ── Tree of Thought ───────────────────────────────────────
    if reasoning_mode == "tot":
        from agents.tree_of_thought import (
            generate_reasoning_tree, evaluate_branch, select_best_branch, merge_branches,
        )
        from observability.storage.db import (
            save_reasoning_tree, save_reasoning_branch, save_branch_score,
            save_winning_branch, save_branch_evaluation,
        )
        import time
        from datetime import datetime

        t0 = time.time()
        branches = generate_reasoning_tree(query)

        # Evaluate branches in parallel
        evaluated_branches = []
        with ThreadPoolExecutor(max_workers=min(len(branches), 4)) as exe:
            futures = {exe.submit(evaluate_branch, b, query, embedding_model, vector_store, top_k): b for b in branches}
            for f in as_completed(futures):
                try:
                    evaluated_branches.append(f.result())
                except Exception as e:
                    logger.error(f"Branch evaluation failed: {e}")

        best_branch, ranked_branches = select_best_branch(evaluated_branches)
        merged_queries, _ = merge_branches(ranked_branches)
        tot_latency = time.time() - t0

        timestamp = datetime.utcnow().isoformat() + "Z"
        if session_id:
            save_reasoning_tree(session_id, query, timestamp, tot_latency)
            for b in ranked_branches:
                save_reasoning_branch({
                    "branch_id": b["branch_id"], "session_id": session_id,
                    "branch_name": b["branch_name"],
                    "retrieval_query": ", ".join(b["sub_queries"]),
                    "rewritten_query": ", ".join(b.get("rewritten_queries", [])),
                    "expected_evidence": b["expected_evidence"], "status": "EVALUATED",
                })
                save_branch_score({
                    "branch_id": b["branch_id"],
                    "retrieval_similarity": b["scores"]["retrieval_similarity"],
                    "coverage": b["scores"]["coverage"],
                    "completeness": b["scores"]["completeness"],
                    "evidence_quality": b["scores"]["evidence_quality"],
                    "confidence": b["scores"]["confidence"],
                    "final_score": b["scores"]["final_score"],
                })
                save_branch_evaluation(b["branch_id"], b["evaluation_details"], b["scores"]["final_score"])
            save_winning_branch(session_id, best_branch["branch_id"], best_branch["final_score"])

        sub_queries = merged_queries
        logger.info(f"ToT sub-queries: {sub_queries}")
    else:
        sub_queries = planner_agent(query)
        logger.info(f"Planner sub-queries: {sub_queries}")

    # ── Standard / ToT feedback loop ─────────────────────────
    current_sub_queries = sub_queries
    final_context = ""
    final_sc_result = None

    for iteration in range(1, max_iterations + 1):
        logger.info(f"Iteration {iteration}/{max_iterations}")

        fanout_results = search_fanout(current_sub_queries, embedding_model, vector_store, top_k=top_k)
        aggregated_context = trim_context(aggregate_fanout_context(fanout_results))
        intermediate_draft = build_intermediate_draft(query, aggregated_context)
        sc_result = sufficient_context_agent(query, aggregated_context, intermediate_draft)

        if "Failed to parse" in sc_result.get("reasoning_summary", ""):
            fallback_used = True

        logger.info(f"Iteration {iteration} SC: sufficient={sc_result.get('is_context_sufficient')}")

        trace.append({
            "iteration": iteration,
            "sub_queries": current_sub_queries,
            "fanout_results": fanout_results,
            "aggregated_context": aggregated_context,
            "intermediate_draft": intermediate_draft,
            "sufficient_context_result": sc_result,
        })
        final_context = aggregated_context
        final_sc_result = sc_result

        if sc_result.get("is_context_sufficient", False):
            logger.info("Context sufficient — exiting loop.")
            break

        # Build feedback queries from missing info
        missing = sc_result.get("missing_information", [])
        feedback = sc_result.get("feedback_log", "")

        # Parallelise query rewriting for feedback loop
        feedback_items = missing + ([feedback] if feedback else [])
        if feedback_items:
            with ThreadPoolExecutor(max_workers=min(len(feedback_items), 4)) as exe:
                current_sub_queries = list(exe.map(query_rewriter, feedback_items))
        else:
            current_sub_queries = [query]

        logger.info(f"Feedback queries: {current_sub_queries}")

    # ── Final synthesis ───────────────────────────────────────
    final_answer = synthesis_agent(query, final_context)
    logger.info("Synthesis complete.")

    # Build deduplicated citations sorted by score
    citations = []
    seen_idx = set()
    for iter_trace in trace:
        for f_res in iter_trace["fanout_results"]:
            for ret in f_res["retrieved"]:
                idx = ret["index"]
                if idx not in seen_idx:
                    seen_idx.add(idx)
                    citations.append({
                        "chunk_index": idx,
                        "text_preview": ret["chunk"][:200] + ("..." if len(ret["chunk"]) > 200 else ""),
                        "score": ret["score"],
                    })
    citations = sorted(citations, key=lambda x: x["score"], reverse=True)[:5]

    return {
        "query": query,
        "answer": final_answer,
        "iterations": len(trace),
        "context_sufficient": final_sc_result.get("is_context_sufficient", True) if final_sc_result else True,
        "missing_information": final_sc_result.get("missing_information", []) if final_sc_result else [],
        "trace": trace,
        "final_context": final_context,
        "citations": citations,
        "fallback_used": fallback_used,
        "session_id": session_id,
        "evidence_type": final_sc_result.get("evidence_type", "explicit") if final_sc_result else "explicit",
    }
