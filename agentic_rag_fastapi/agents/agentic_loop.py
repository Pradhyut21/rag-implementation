import logging
from rag.retrieval import retrieve, format_context
from agents.planner import planner_agent
from agents.rewriter import query_rewriter
from agents.sufficient_context import sufficient_context_agent
from agents.synthesis import synthesis_agent
from agents.llm import safe_generate

logger = logging.getLogger("agentic_rag.agentic_loop")

def build_intermediate_draft(query: str, context: str):
    prompt = f"""
You are generating an intermediate draft answer.
Use the context below to draft a possible answer to the user's question.

USER QUERY:
{query}

CONTEXT:
{context}

Write a draft answer.
"""
    return safe_generate(prompt)

def search_fanout(sub_queries, embedding_model, vector_store, top_k=3):
    all_results = []

    for sq in sub_queries:
        rewritten = query_rewriter(sq)
        retrieved = retrieve(rewritten, embedding_model, vector_store, top_k=top_k)

        all_results.append({
            "sub_query": sq,
            "rewritten_query": rewritten,
            "retrieved": retrieved
        })

    return all_results

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

def trim_context(context: str, max_chars: int = 12000):
    if len(context) <= max_chars:
        return context
    return context[:max_chars]

def vanilla_rag(query: str, embedding_model, vector_store, top_k: int = 5):
    logger.info(f"Running Vanilla RAG query: {query}")
    retrieved = retrieve(query, embedding_model, vector_store, top_k=top_k)
    context = format_context(retrieved)
    answer = synthesis_agent(query, context)

    # Compile citations
    citations = []
    for ret in retrieved:
        citations.append({
            "chunk_index": ret["index"],
            "text_preview": ret["chunk"][:200] + "..." if len(ret["chunk"]) > 200 else ret["chunk"],
            "score": ret["score"]
        })

    return {
        "query": query,
        "retrieved_chunks": retrieved,
        "context": context,
        "answer": answer,
        "citations": citations
    }

def agentic_rag(query: str, embedding_model, vector_store, max_iterations: int = 2, top_k: int = 3, reasoning_mode: str = "standard"):
    logger.info(f"Starting Agentic RAG for query: {query} with mode: {reasoning_mode}")

    # Check reasoning mode
    import uuid as _uuid
    from observability.tracing.context import get_trace_context
    ctx = get_trace_context()
    # Guard: session_id can be None when called outside the HTTP middleware (e.g. eval scripts).
    session_id = ctx.get("session_id") or str(_uuid.uuid4())

    if reasoning_mode == "cot":
        from agents.cot_reasoner import run_cot_reasoning
        result = run_cot_reasoning(
            query=query,
            embedding_model=embedding_model,
            vector_store=vector_store,
            top_k=top_k,
            session_id=session_id
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
            "session_id": session_id
        }

    trace = []
    fallback_used = False

    # Step 1: Planner
    if reasoning_mode == "tot":
        from agents.tree_of_thought import (
            generate_reasoning_tree, evaluate_branch, select_best_branch, merge_branches
        )
        from observability.storage.db import (
            save_reasoning_tree, save_reasoning_branch, save_branch_score,
            save_winning_branch, save_branch_evaluation
        )
        import time
        from datetime import datetime

        start_tot_time = time.time()
        
        # 1. Generate branches
        branches = generate_reasoning_tree(query)
        
        # 2. Evaluate all branches
        evaluated_branches = []
        for b in branches:
            b_eval = evaluate_branch(b, query, embedding_model, vector_store, top_k=top_k)
            evaluated_branches.append(b_eval)
            
        # 3. Select best branch
        best_branch, ranked_branches = select_best_branch(evaluated_branches)
        
        # 4. Merge if close
        merged_queries, was_merged = merge_branches(ranked_branches)
        
        tot_latency = time.time() - start_tot_time

        # 5. Persist to DB — only when session_id is set (avoids NULL PK error)
        timestamp = datetime.utcnow().isoformat() + "Z"
        if session_id:
            save_reasoning_tree(session_id, query, timestamp, tot_latency)
        
        if session_id:
            for b in ranked_branches:
                save_reasoning_branch({
                    "branch_id": b["branch_id"],
                    "session_id": session_id,
                    "branch_name": b["branch_name"],
                    "retrieval_query": ", ".join(b["sub_queries"]),
                    "rewritten_query": ", ".join(b.get("rewritten_queries", [])),
                    "expected_evidence": b["expected_evidence"],
                    "status": "EVALUATED"
                })
                save_branch_score({
                    "branch_id": b["branch_id"],
                    "retrieval_similarity": b["scores"]["retrieval_similarity"],
                    "coverage": b["scores"]["coverage"],
                    "completeness": b["scores"]["completeness"],
                    "evidence_quality": b["scores"]["evidence_quality"],
                    "confidence": b["scores"]["confidence"],
                    "final_score": b["scores"]["final_score"]
                })
                save_branch_evaluation(
                    b["branch_id"],
                    b["evaluation_details"],
                    b["scores"]["final_score"]
                )
            save_winning_branch(session_id, best_branch["branch_id"], best_branch["final_score"])
        
        sub_queries = merged_queries
        logger.info(f"Tree of Thought Planner generated sub-queries: {sub_queries}")
    else:
        sub_queries = planner_agent(query)
        logger.info(f"Planner generated sub-queries: {sub_queries}")

    current_sub_queries = sub_queries
    final_context = ""
    final_sc_result = None

    for iteration in range(1, max_iterations + 1):
        logger.info(f"Starting iteration {iteration} of Agentic RAG")
        
        # Step 2: Search fanout
        fanout_results = search_fanout(current_sub_queries, embedding_model, vector_store, top_k=top_k)
        logger.debug(f"Search fanout complete for {len(current_sub_queries)} sub-queries")

        # Step 3: Aggregate context
        aggregated_context = aggregate_fanout_context(fanout_results)
        # Trim context to avoid LLM context window issues
        aggregated_context = trim_context(aggregated_context, max_chars=12000)

        # Step 4: Intermediate draft
        intermediate_draft = build_intermediate_draft(query, aggregated_context)

        # Step 5: Sufficient context check
        sc_result = sufficient_context_agent(query, aggregated_context, intermediate_draft)

        # Track if parser fallback was triggered
        if "Failed to parse" in sc_result.get("reasoning_summary", ""):
            fallback_used = True

        # Structured debug logs
        logger.info(f"Iteration {iteration} Sufficient Context check: sufficient={sc_result.get('is_context_sufficient')}")
        logger.debug(f"Sub-queries for iteration {iteration}: {current_sub_queries}")
        logger.debug(f"Aggregated context length: {len(aggregated_context)}")
        logger.debug(f"Intermediate draft preview: {intermediate_draft[:200]}...")
        logger.debug(f"SC Result feedback log: {sc_result.get('feedback_log')}")

        trace.append({
            "iteration": iteration,
            "sub_queries": current_sub_queries,
            "fanout_results": fanout_results,
            "aggregated_context": aggregated_context,
            "intermediate_draft": intermediate_draft,
            "sufficient_context_result": sc_result
        })

        final_context = aggregated_context
        final_sc_result = sc_result

        if sc_result.get("is_context_sufficient", False):
            logger.info("Context determined to be sufficient. Exiting loop.")
            break

        # feedback loop - strengthen by query rewriting on missing and feedback
        missing = sc_result.get("missing_information", [])
        feedback = sc_result.get("feedback_log", "")

        feedback_queries = []
        for item in missing:
            # pass missing info items through query rewriter to make them search-friendly
            feedback_queries.append(query_rewriter(item))

        if feedback:
            # pass feedback log through query rewriter
            feedback_queries.append(query_rewriter(feedback))

        # fallback
        if not feedback_queries:
            feedback_queries = [query]

        current_sub_queries = feedback_queries
        logger.info(f"Feedback queries for next iteration: {current_sub_queries}")

    # Step 6: Final synthesis
    final_answer = synthesis_agent(query, final_context)
    logger.info("Final synthesis completed.")

    # Extract unique supporting chunk citations from all iterations
    citations = []
    seen_chunk_indices = set()
    for iter_trace in trace:
        for f_res in iter_trace["fanout_results"]:
            for ret in f_res["retrieved"]:
                idx = ret["index"]
                if idx not in seen_chunk_indices:
                    seen_chunk_indices.add(idx)
                    citations.append({
                        "chunk_index": idx,
                        "text_preview": ret["chunk"][:200] + "..." if len(ret["chunk"]) > 200 else ret["chunk"],
                        "score": ret["score"]
                    })
    # Sort citations by retrieval score descending and keep top 5
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
        "session_id": session_id
    }
