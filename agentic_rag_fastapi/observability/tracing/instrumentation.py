from datetime import datetime
import logging
import time
import traceback
import uuid

from observability.storage.db import save_error, save_event, save_session, save_span
from observability.tracing.context import (
    active_iteration_var,
    get_trace_context,
    init_trace_context,
    update_accumulated_tokens,
)

logger = logging.getLogger("observability.instrumentation")

# Store original functions to avoid infinite recursion
_originals = {}


def wrapped_safe_generate(prompt: str, temperature: float = 0):
    # NOTE: We delegate to the ORIGINAL safe_generate (stored in _originals) which
    # has the tenacity retry/back-off decorator for rate-limit errors.  Calling
    # client.chat.completions.create directly here would bypass those retries.

    ctx = get_trace_context()
    session_id = ctx["session_id"] or str(uuid.uuid4())
    request_id = ctx["request_id"] or str(uuid.uuid4())
    correlation_id = ctx["correlation_id"]
    workflow_id = ctx["workflow_id"]
    iteration = ctx["active_iteration"]

    start_time = time.time()
    span_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat() + "Z"

    try:
        # Delegate to the original decorated function so tenacity retries fire.
        original_generate = _originals.get("safe_generate")
        if original_generate is None:
            raise RuntimeError("safe_generate original not registered in _originals yet")
        content = original_generate(prompt, temperature)

        # ----------------------------------------------------------------
        # Re-run a lightweight call just to capture usage metadata.
        # The Groq client stores the last response; we can also approximate
        # tokens via the cost utility if we don't have direct access.
        # For accuracy, we estimate from prompt/completion char lengths.
        # ----------------------------------------------------------------
        from observability.utils.cost import calculate_llm_cost, estimate_token_count

        prompt_tokens = estimate_token_count(prompt)
        completion_tokens = estimate_token_count(content)
        total_tokens = prompt_tokens + completion_tokens
        model_name = "llama-3.3-70b-versatile"
        cost = calculate_llm_cost(model_name, prompt_tokens, completion_tokens)

        # Update accumulator
        update_accumulated_tokens(prompt_tokens, completion_tokens, total_tokens, cost)

        latency = time.time() - start_time

        save_span(
            {
                "span_id": span_id,
                "session_id": session_id,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "workflow_id": workflow_id,
                "name": "llm_generate",
                "status": "SUCCESS",
                "inputs": {"prompt": prompt[:500], "temperature": temperature},
                "outputs": {"response": content[:500]},
                "latency": latency,
                "timestamp": timestamp,
                "iteration": iteration,
                "extra_data": {
                    "model": model_name,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "cost": cost,
                },
            }
        )
        return content
    except Exception as e:
        latency = time.time() - start_time
        tb = traceback.format_exc()

        # Classify error type for better observability
        error_type = (
            "Rate Limit Error" if "rate" in str(e).lower() or "429" in str(e) else "LLM Error"
        )

        save_span(
            {
                "span_id": span_id,
                "session_id": session_id,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "workflow_id": workflow_id,
                "name": "llm_generate",
                "status": "FAILED",
                "inputs": {"prompt": prompt[:500], "temperature": temperature},
                "outputs": None,
                "error": str(e),
                "latency": latency,
                "timestamp": timestamp,
                "iteration": iteration,
                "extra_data": {"error_type": error_type},
            }
        )

        save_error(
            {
                "error_id": str(uuid.uuid4()),
                "session_id": session_id,
                "request_id": request_id,
                "error_type": error_type,
                "message": str(e),
                "stack_trace": tb,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )
        raise e


def wrapped_planner_agent(query: str):
    ctx = get_trace_context()
    session_id = ctx["session_id"] or str(uuid.uuid4())
    request_id = ctx["request_id"] or str(uuid.uuid4())
    correlation_id = ctx["correlation_id"]
    workflow_id = ctx["workflow_id"]

    start_time = time.time()
    span_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat() + "Z"

    save_event(
        {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "request_id": request_id,
            "name": "Planner Started",
            "timestamp": timestamp,
            "extra_data": {"query": query},
        }
    )

    try:
        original = _originals["planner_agent"]
        sub_queries = original(query)
        latency = time.time() - start_time

        save_span(
            {
                "span_id": span_id,
                "session_id": session_id,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "workflow_id": workflow_id,
                "name": "planner",
                "status": "SUCCESS",
                "inputs": {"query": query},
                "outputs": {"sub_queries": sub_queries},
                "latency": latency,
                "timestamp": timestamp,
                "iteration": 0,
                "extra_data": {"sub_queries": sub_queries},
            }
        )

        save_event(
            {
                "event_id": str(uuid.uuid4()),
                "session_id": session_id,
                "request_id": request_id,
                "name": "Planner Completed",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "extra_data": {"sub_queries": sub_queries, "latency": latency},
            }
        )
        return sub_queries
    except Exception as e:
        latency = time.time() - start_time
        tb = traceback.format_exc()

        save_span(
            {
                "span_id": span_id,
                "session_id": session_id,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "workflow_id": workflow_id,
                "name": "planner",
                "status": "FAILED",
                "inputs": {"query": query},
                "outputs": None,
                "error": str(e),
                "latency": latency,
                "timestamp": timestamp,
                "iteration": 0,
                "extra_data": {},
            }
        )

        # Check if JSON parsing failure
        err_type = "JSON Parsing Error" if "parse" in str(e).lower() else "Exception"
        save_error(
            {
                "error_id": str(uuid.uuid4()),
                "session_id": session_id,
                "request_id": request_id,
                "error_type": err_type,
                "message": str(e),
                "stack_trace": tb,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )
        raise e


def wrapped_query_rewriter(sub_query: str):
    ctx = get_trace_context()
    session_id = ctx["session_id"] or str(uuid.uuid4())
    request_id = ctx["request_id"] or str(uuid.uuid4())
    correlation_id = ctx["correlation_id"]
    workflow_id = ctx["workflow_id"]
    iteration = ctx["active_iteration"]

    start_time = time.time()
    span_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat() + "Z"

    save_event(
        {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "request_id": request_id,
            "name": "Rewrite Started",
            "timestamp": timestamp,
            "extra_data": {"sub_query": sub_query},
        }
    )

    # Reason for rewrite: If active iteration is 0, it's a planner subquery. Otherwise, feedback.
    rewrite_reason = (
        "Planner subquery optimization" if iteration == 0 else "Feedback loop query enhancement"
    )

    try:
        original = _originals["query_rewriter"]
        rewritten = original(sub_query)
        latency = time.time() - start_time

        save_span(
            {
                "span_id": span_id,
                "session_id": session_id,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "workflow_id": workflow_id,
                "name": "rewriter",
                "status": "SUCCESS",
                "inputs": {"sub_query": sub_query},
                "outputs": {"rewritten_query": rewritten},
                "latency": latency,
                "timestamp": timestamp,
                "iteration": iteration,
                "extra_data": {"reason": rewrite_reason},
            }
        )

        save_event(
            {
                "event_id": str(uuid.uuid4()),
                "session_id": session_id,
                "request_id": request_id,
                "name": "Rewrite Completed",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "extra_data": {"rewritten_query": rewritten, "latency": latency},
            }
        )
        return rewritten
    except Exception as e:
        latency = time.time() - start_time
        tb = traceback.format_exc()

        save_span(
            {
                "span_id": span_id,
                "session_id": session_id,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "workflow_id": workflow_id,
                "name": "rewriter",
                "status": "FAILED",
                "inputs": {"sub_query": sub_query},
                "outputs": None,
                "error": str(e),
                "latency": latency,
                "timestamp": timestamp,
                "iteration": iteration,
                "extra_data": {},
            }
        )

        save_error(
            {
                "error_id": str(uuid.uuid4()),
                "session_id": session_id,
                "request_id": request_id,
                "error_type": "Exception",
                "message": str(e),
                "stack_trace": tb,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )
        raise e


def wrapped_retrieve(query: str, embedding_model, vector_store, top_k: int = 5):
    ctx = get_trace_context()
    session_id = ctx["session_id"] or str(uuid.uuid4())
    request_id = ctx["request_id"] or str(uuid.uuid4())
    correlation_id = ctx["correlation_id"]
    workflow_id = ctx["workflow_id"]
    iteration = ctx["active_iteration"]
    doc_id = ctx["doc_id"]

    start_time = time.time()
    span_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat() + "Z"

    save_event(
        {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "request_id": request_id,
            "name": "Retrieval Started",
            "timestamp": timestamp,
            "extra_data": {"query": query, "top_k": top_k},
        }
    )

    try:
        original = _originals["retrieve"]
        results = original(query, embedding_model, vector_store, top_k)
        latency = time.time() - start_time

        chunk_ids = [r["index"] for r in results]
        scores = [r["score"] for r in results]

        save_span(
            {
                "span_id": span_id,
                "session_id": session_id,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "workflow_id": workflow_id,
                "name": "retriever",
                "status": "SUCCESS",
                "inputs": {"query": query, "top_k": top_k},
                "outputs": {"retrieved_results": results},
                "latency": latency,
                "timestamp": timestamp,
                "iteration": iteration,
                "extra_data": {"chunk_ids": chunk_ids, "scores": scores, "doc_id": doc_id},
            }
        )

        save_event(
            {
                "event_id": str(uuid.uuid4()),
                "session_id": session_id,
                "request_id": request_id,
                "name": "Retrieval Completed",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "extra_data": {"results_count": len(results), "latency": latency},
            }
        )
        return results
    except Exception as e:
        latency = time.time() - start_time
        tb = traceback.format_exc()

        save_span(
            {
                "span_id": span_id,
                "session_id": session_id,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "workflow_id": workflow_id,
                "name": "retriever",
                "status": "FAILED",
                "inputs": {"query": query, "top_k": top_k},
                "outputs": None,
                "error": str(e),
                "latency": latency,
                "timestamp": timestamp,
                "iteration": iteration,
                "extra_data": {},
            }
        )

        save_error(
            {
                "error_id": str(uuid.uuid4()),
                "session_id": session_id,
                "request_id": request_id,
                "error_type": "Exception",
                "message": str(e),
                "stack_trace": tb,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )
        raise e


def wrapped_sufficient_context_agent(query: str, context: str, intermediate_draft: str):
    ctx = get_trace_context()
    session_id = ctx["session_id"] or str(uuid.uuid4())
    request_id = ctx["request_id"] or str(uuid.uuid4())
    correlation_id = ctx["correlation_id"]
    workflow_id = ctx["workflow_id"]
    iteration = ctx["active_iteration"]

    start_time = time.time()
    span_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat() + "Z"

    save_event(
        {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "request_id": request_id,
            "name": "Context Evaluation Started",
            "timestamp": timestamp,
            "extra_data": {"iteration": iteration},
        }
    )

    try:
        original = _originals["sufficient_context_agent"]
        sc_result = original(query, context, intermediate_draft)
        latency = time.time() - start_time

        save_span(
            {
                "span_id": span_id,
                "session_id": session_id,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "workflow_id": workflow_id,
                "name": "sufficient_context",
                "status": "SUCCESS",
                "inputs": {
                    "query": query,
                    "context_len": len(context),
                    "intermediate_draft_len": len(intermediate_draft),
                },
                "outputs": sc_result,
                "latency": latency,
                "timestamp": timestamp,
                "iteration": iteration,
                "extra_data": {
                    "is_context_sufficient": sc_result.get("is_context_sufficient"),
                    "evidence_type": sc_result.get("evidence_type"),
                    "missing_information": sc_result.get("missing_information"),
                    "reasoning_summary": sc_result.get("reasoning_summary"),
                    "feedback_log": sc_result.get("feedback_log"),
                },
            }
        )

        save_event(
            {
                "event_id": str(uuid.uuid4()),
                "session_id": session_id,
                "request_id": request_id,
                "name": "Context Evaluation Completed",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "extra_data": {
                    "sufficient": sc_result.get("is_context_sufficient"),
                    "evidence_type": sc_result.get("evidence_type"),
                    "latency": latency,
                },
            }
        )
        active_iteration_var.set(iteration + 1)
        return sc_result
    except Exception as e:
        latency = time.time() - start_time
        tb = traceback.format_exc()

        save_span(
            {
                "span_id": span_id,
                "session_id": session_id,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "workflow_id": workflow_id,
                "name": "sufficient_context",
                "status": "FAILED",
                "inputs": {
                    "query": query,
                    "context_len": len(context),
                    "intermediate_draft_len": len(intermediate_draft),
                },
                "outputs": None,
                "error": str(e),
                "latency": latency,
                "timestamp": timestamp,
                "iteration": iteration,
                "extra_data": {},
            }
        )

        save_error(
            {
                "error_id": str(uuid.uuid4()),
                "session_id": session_id,
                "request_id": request_id,
                "error_type": "Exception",
                "message": str(e),
                "stack_trace": tb,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )
        raise e


def wrapped_synthesis_agent(query: str, context: str):
    ctx = get_trace_context()
    session_id = ctx["session_id"] or str(uuid.uuid4())
    request_id = ctx["request_id"] or str(uuid.uuid4())
    correlation_id = ctx["correlation_id"]
    workflow_id = ctx["workflow_id"]
    iteration = ctx["active_iteration"]

    start_time = time.time()
    span_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat() + "Z"

    save_event(
        {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "request_id": request_id,
            "name": "Synthesis Started",
            "timestamp": timestamp,
            "extra_data": {},
        }
    )

    try:
        original = _originals["synthesis_agent"]
        final_answer = original(query, context)
        latency = time.time() - start_time

        save_span(
            {
                "span_id": span_id,
                "session_id": session_id,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "workflow_id": workflow_id,
                "name": "synthesis",
                "status": "SUCCESS",
                "inputs": {"query": query, "context_len": len(context)},
                "outputs": {"answer": final_answer},
                "latency": latency,
                "timestamp": timestamp,
                "iteration": iteration,
                "extra_data": {"prompt_preview": f"Query: {query}\nContext length: {len(context)}"},
            }
        )

        save_event(
            {
                "event_id": str(uuid.uuid4()),
                "session_id": session_id,
                "request_id": request_id,
                "name": "Synthesis Completed",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "extra_data": {"latency": latency},
            }
        )
        return final_answer
    except Exception as e:
        latency = time.time() - start_time
        tb = traceback.format_exc()

        save_span(
            {
                "span_id": span_id,
                "session_id": session_id,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "workflow_id": workflow_id,
                "name": "synthesis",
                "status": "FAILED",
                "inputs": {"query": query, "context_len": len(context)},
                "outputs": None,
                "error": str(e),
                "latency": latency,
                "timestamp": timestamp,
                "iteration": iteration,
                "extra_data": {},
            }
        )

        save_error(
            {
                "error_id": str(uuid.uuid4()),
                "session_id": session_id,
                "request_id": request_id,
                "error_type": "Exception",
                "message": str(e),
                "stack_trace": tb,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )
        raise e


def _run_with_iterative_tracking(original_func, query, *args, **kwargs):
    """
    Helper to run RAG workflow wrapper while updating iteration context and session database state.
    """
    ctx = get_trace_context()

    # If no session initialized in middleware, initialize now
    if not ctx["session_id"]:
        ctx = init_trace_context()

    session_id = ctx["session_id"]
    request_id = ctx["request_id"]
    correlation_id = ctx["correlation_id"]
    workflow_id = ctx["workflow_id"]
    doc_id = ctx["doc_id"]

    start_time = time.time()
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Save initial Session Record
    save_session(
        {
            "session_id": session_id,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "workflow_id": workflow_id,
            "query": query,
            "answer": None,
            "status": "RUNNING",
            "timestamp": timestamp,
            "total_latency": 0.0,
            "doc_id": doc_id,
        }
    )

    # We will override active_iteration_var dynamically as agentic_rag runs!
    # Wait, how do we track iterations?
    # We can patch agentic_rag to set active_iteration_var per loop or hook it.
    # In agentic_rag, the loop does:
    # for iteration in range(1, max_iterations + 1):
    # If we intercept/monkey-patch internal loop steps, we can set iteration number.
    # Let's inspect agents.agentic_loop:
    # In each loop, search_fanout, intermediate_draft, and sufficient_context_agent are called.
    # If we update active_iteration_var.set(iteration) when sufficient_context_agent or search_fanout is called, it will track properly!
    # Let's design that inside the wrappers of sufficient_context, query_rewriter, retrieve.
    # Inside agentic_rag loop, it performs iteration.
    # We can write a custom wrapper for agentic_rag that sets the context variable active_iteration_var.set(1) first, and dynamically increments it.
    # Let's look at agents.agentic_loop: we can wrap the agents to increment the iteration or read it.
    # Wait, inside agentic_loop.py, the loop runs.
    # Can we just intercept when 'Sufficient Context' is checked to know the iteration?
    # In agentic_loop:
    # for iteration in range(1, max_iterations + 1):
    #   sc_result = sufficient_context_agent(...)
    # If we look at the RAG's trace length or track it dynamically, that is perfect!
    # Inside wrapped sufficient_context, we can read active_iteration_var.get() and set it to iteration + 1 at the end, or increment it!
    # Actually, we can increment active_iteration_var every time the feedback loop runs or during sufficient context agent.
    # Let's see: if we increment it at the start of search_fanout, or at the start of sufficient_context_agent.
    # Let's increment it in the retrieval / sufficient_context wrapper if it hasn't been set!
    # Actually, we can write a simple stateful tracker:
    # Each time a retrieve is called, we can count it or set it based on flow.
    # Or, we can let the agentic_rag wrapper itself inspect the output trace size to set iterations!
    # Yes! At the end of agentic_rag, the returned dictionary has:
    # "iterations": len(trace)
    # We can use that!

    try:
        res = original_func(query, *args, **kwargs)
        latency = time.time() - start_time

        # Extract final answer
        final_answer = res.get("answer") if isinstance(res, dict) else str(res)
        iterations = res.get("iterations", 1) if isinstance(res, dict) else 1

        # Read final accumulated tokens
        final_ctx = get_trace_context()

        save_session(
            {
                "session_id": session_id,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "workflow_id": workflow_id,
                "query": query,
                "answer": final_answer,
                "status": "SUCCESS",
                "timestamp": timestamp,
                "total_latency": latency,
                "prompt_tokens": final_ctx.get("prompt_tokens", 0),
                "completion_tokens": final_ctx.get("completion_tokens", 0),
                "total_tokens": final_ctx.get("total_tokens", 0),
                "estimated_cost": final_ctx.get("estimated_cost", 0.0),
                "iterations_count": iterations,
                "doc_id": doc_id,
            }
        )

        save_event(
            {
                "event_id": str(uuid.uuid4()),
                "session_id": session_id,
                "request_id": request_id,
                "name": "Workflow Completed",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "extra_data": {"status": "SUCCESS", "latency": latency},
            }
        )

        return res
    except Exception as e:
        latency = time.time() - start_time
        tb = traceback.format_exc()

        final_ctx = get_trace_context()

        save_session(
            {
                "session_id": session_id,
                "request_id": request_id,
                "correlation_id": correlation_id,
                "workflow_id": workflow_id,
                "query": query,
                "answer": None,
                "status": "FAILED",
                "error_message": str(e),
                "stack_trace": tb,
                "timestamp": timestamp,
                "total_latency": latency,
                "prompt_tokens": final_ctx.get("prompt_tokens", 0),
                "completion_tokens": final_ctx.get("completion_tokens", 0),
                "total_tokens": final_ctx.get("total_tokens", 0),
                "estimated_cost": final_ctx.get("estimated_cost", 0.0),
                "iterations_count": 0,
                "doc_id": doc_id,
            }
        )

        save_event(
            {
                "event_id": str(uuid.uuid4()),
                "session_id": session_id,
                "request_id": request_id,
                "name": "Workflow Completed",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "extra_data": {"status": "FAILED", "latency": latency, "error": str(e)},
            }
        )

        save_error(
            {
                "error_id": str(uuid.uuid4()),
                "session_id": session_id,
                "request_id": request_id,
                "error_type": "Exception",
                "message": f"Workflow failed: {e!s}",
                "stack_trace": tb,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )
        raise e


def wrapped_agentic_rag(query: str, *args, **kwargs):
    # Set iteration hooks helper
    # We will dynamically increment iteration inside agentic_rag.
    # To do this, we can set up an execution listener:
    # Since agentic_rag executes sequentially, we can capture the iteration number
    # by intercepting sufficient_context_agent or retrieval calls, or by managing it in a thread/coroutine local counter.
    # Let's reset active_iteration_var to 1 at the beginning of agentic_rag,
    # and we can increment it every time a new iteration starts.
    # Wait, how does agentic_rag signal a new iteration?
    # In agentic_loop.py:
    # for iteration in range(1, max_iterations + 1):
    #   # calls search_fanout -> query_rewriter, retrieve
    # So we can increment it when search_fanout is entered, or inside sufficient_context_agent.
    # Actually, let's increment active_iteration_var inside a hook.
    # A very simple way: since RAG execution is synchronous per thread, we can set:
    # active_iteration_var.set(1) at start.
    # And inside sufficient_context_agent (which is called at the end of each iteration),
    # we increment it: active_iteration_var.set(active_iteration_var.get() + 1)!
    # This matches perfectly! Iteration 1 starts, calls retrieve (iteration 1), calls sufficient_context_agent (iteration 1),
    # then sufficient_context_agent wrapper increments active_iteration_var to 2.
    # Iteration 2 starts, calls retrieve (iteration 2), sufficient_context_agent (iteration 2), increments to 3, and so on.
    # This is incredibly simple and elegant!

    active_iteration_var.set(1)

    original = _originals["agentic_rag"]
    return _run_with_iterative_tracking(original, query, *args, **kwargs)


def wrapped_vanilla_rag(query: str, *args, **kwargs):
    active_iteration_var.set(0)  # Vanilla RAG doesn't have iteration loops
    original = _originals["vanilla_rag"]
    return _run_with_iterative_tracking(original, query, *args, **kwargs)


def setup_observability():
    """
    Performs monkey-patching of the Agentic RAG core modules.
    Safe to call multiple times (checks for existing hooks).
    """
    if _originals:
        logger.info("Observability is already instrumented. Skipping setup.")
        return

    logger.info("Monkey-patching Agentic RAG functions for Observability...")

    # Import modules to patch
    import agents.agentic_loop
    import agents.llm
    import agents.planner
    import agents.rewriter
    import agents.sufficient_context
    import agents.synthesis
    import rag.retrieval

    # 1. safe_generate
    _originals["safe_generate"] = agents.llm.safe_generate
    agents.llm.safe_generate = wrapped_safe_generate

    # 2. planner_agent
    _originals["planner_agent"] = agents.planner.planner_agent
    agents.planner.planner_agent = wrapped_planner_agent

    # 3. query_rewriter
    _originals["query_rewriter"] = agents.rewriter.query_rewriter
    agents.rewriter.query_rewriter = wrapped_query_rewriter

    # 4. retrieve
    _originals["retrieve"] = rag.retrieval.retrieve
    rag.retrieval.retrieve = wrapped_retrieve

    # 5. sufficient_context_agent
    _originals["sufficient_context_agent"] = agents.sufficient_context.sufficient_context_agent
    agents.sufficient_context.sufficient_context_agent = wrapped_sufficient_context_agent

    # 6. synthesis_agent
    _originals["synthesis_agent"] = agents.synthesis.synthesis_agent
    agents.synthesis.synthesis_agent = wrapped_synthesis_agent

    # 7. agentic_rag & vanilla_rag
    _originals["agentic_rag"] = agents.agentic_loop.agentic_rag
    _originals["vanilla_rag"] = agents.agentic_loop.vanilla_rag
    agents.agentic_loop.agentic_rag = wrapped_agentic_rag
    agents.agentic_loop.vanilla_rag = wrapped_vanilla_rag

    # 8. Align imports inside agentic_loop module
    agents.agentic_loop.safe_generate = wrapped_safe_generate
    agents.agentic_loop.planner_agent = wrapped_planner_agent
    agents.agentic_loop.query_rewriter = wrapped_query_rewriter
    agents.agentic_loop.retrieve = wrapped_retrieve
    agents.agentic_loop.sufficient_context_agent = wrapped_sufficient_context_agent
    agents.agentic_loop.synthesis_agent = wrapped_synthesis_agent

    # 9. Dynamically patch already imported namespaces across sys.modules
    import sys

    for mod_name, mod in list(sys.modules.items()):
        if mod is None or mod_name == __name__:
            continue
        try:
            if (
                hasattr(mod, "agentic_rag")
                and mod.agentic_rag is not wrapped_agentic_rag
            ):
                mod.agentic_rag = wrapped_agentic_rag
            if (
                hasattr(mod, "vanilla_rag")
                and mod.vanilla_rag is not wrapped_vanilla_rag
            ):
                mod.vanilla_rag = wrapped_vanilla_rag
            if (
                hasattr(mod, "planner_agent")
                and mod.planner_agent is not wrapped_planner_agent
            ):
                mod.planner_agent = wrapped_planner_agent
            if (
                hasattr(mod, "query_rewriter")
                and mod.query_rewriter is not wrapped_query_rewriter
            ):
                mod.query_rewriter = wrapped_query_rewriter
            if hasattr(mod, "retrieve") and mod.retrieve is not wrapped_retrieve:
                mod.retrieve = wrapped_retrieve
            if (
                hasattr(mod, "sufficient_context_agent")
                and mod.sufficient_context_agent is not wrapped_sufficient_context_agent
            ):
                mod.sufficient_context_agent = wrapped_sufficient_context_agent
            if (
                hasattr(mod, "synthesis_agent")
                and mod.synthesis_agent is not wrapped_synthesis_agent
            ):
                mod.synthesis_agent = wrapped_synthesis_agent
            if (
                hasattr(mod, "safe_generate")
                and mod.safe_generate is not wrapped_safe_generate
            ):
                mod.safe_generate = wrapped_safe_generate
        except Exception:
            pass

    # Initialize the DB schema
    from observability.storage.db import init_db

    init_db()

    logger.info("Monkey-patching completed successfully.")
