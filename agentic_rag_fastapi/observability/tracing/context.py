import uuid
from contextvars import ContextVar
from typing import Optional, Dict, Any

# Context variables for trace tracking
session_id_var: ContextVar[Optional[str]] = ContextVar("session_id", default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
workflow_id_var: ContextVar[Optional[str]] = ContextVar("workflow_id", default=None)
active_iteration_var: ContextVar[int] = ContextVar("active_iteration", default=0)
active_doc_id_var: ContextVar[Optional[str]] = ContextVar("active_doc_id", default=None)

# Accumulates tokens and cost for the current request
# Structure: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "estimated_cost": 0.0}
token_accumulator_var: ContextVar[Optional[Dict[str, Any]]] = ContextVar("token_accumulator", default=None)

def init_trace_context(
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    doc_id: Optional[str] = None,
) -> Dict[str, str]:
    """
    Initializes a new context trace with unique identifiers.
    Returns the initialized IDs.
    """
    s_id = session_id or str(uuid.uuid4())
    r_id = request_id or str(uuid.uuid4())
    c_id = correlation_id or str(uuid.uuid4())
    w_id = workflow_id or str(uuid.uuid4())
    
    session_id_var.set(s_id)
    request_id_var.set(r_id)
    correlation_id_var.set(c_id)
    workflow_id_var.set(w_id)
    active_iteration_var.set(0)
    active_doc_id_var.set(doc_id)
    
    token_accumulator_var.set({
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "estimated_cost": 0.0
    })
    
    return {
        "session_id": s_id,
        "request_id": r_id,
        "correlation_id": c_id,
        "workflow_id": w_id,
        "doc_id": doc_id or ""
    }

def get_trace_context() -> Dict[str, Any]:
    """
    Retrieves the current trace identifiers and token accumulation values.
    """
    accum = token_accumulator_var.get() or {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "estimated_cost": 0.0
    }
    return {
        "session_id": session_id_var.get(),
        "request_id": request_id_var.get(),
        "correlation_id": correlation_id_var.get(),
        "workflow_id": workflow_id_var.get(),
        "active_iteration": active_iteration_var.get(),
        "doc_id": active_doc_id_var.get(),
        **accum
    }

def update_accumulated_tokens(prompt: int, completion: int, total: int, cost: float):
    """
    Adds token usage and cost to the current tracking context.
    """
    accum = token_accumulator_var.get()
    if accum is not None:
        accum["prompt_tokens"] += prompt
        accum["completion_tokens"] += completion
        accum["total_tokens"] += total
        accum["estimated_cost"] += cost
        token_accumulator_var.set(accum)
