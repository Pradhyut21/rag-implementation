from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    query: str
    doc_id: str
    top_k: int = 3
    include_trace: bool = False
    response_mode: str = "compact"  # "compact" | "detailed"
    reasoning_mode: Optional[str] = "standard"  # "standard" | "cot" | "tot"

class RetrievedChunk(BaseModel):
    chunk: str
    score: float
    index: int

class FanoutResult(BaseModel):
    sub_query: str
    rewritten_query: str
    retrieved: List[Dict[str, Any]]

class SufficientContextResult(BaseModel):
    is_context_sufficient: bool
    missing_information: List[str]
    feedback_log: str
    reasoning_summary: Optional[str] = None
    evidence_type: Optional[str] = None

class TraceItem(BaseModel):
    iteration: int
    sub_queries: List[str]
    fanout_results: List[Dict[str, Any]]
    aggregated_context: str
    intermediate_draft: str
    sufficient_context_result: Dict[str, Any]

class CitationInfo(BaseModel):
    chunk_index: int
    text_preview: str
    score: float

class AskResponse(BaseModel):
    query: str
    answer: str
    iterations: int
    context_sufficient: bool
    missing_information: List[str]
    citations: List[CitationInfo]
    trace: Optional[List[Dict[str, Any]]] = None
    final_context: Optional[str] = None
    session_id: Optional[str] = None

class VanillaAskResponse(BaseModel):
    query: str
    answer: str
    retrieved_chunks: List[Dict[str, Any]]
    context: str

class UploadDocResponse(BaseModel):
    message: str
    doc_id: str
    file_name: str
    num_chunks: int

class DocumentInfoResponse(BaseModel):
    doc_id: str
    file_name: str
    uploaded_at: str
    num_chunks: int
    chunk_size: int
    overlap: int
    embedding_model: str

# New Debug / Helper Endpoint Schemas
class PlanRequest(BaseModel):
    query: str

class PlanResponse(BaseModel):
    query: str
    sub_queries: List[str]

class RewriteRequest(BaseModel):
    query: str

class RewriteResponse(BaseModel):
    query: str
    rewritten_query: str

class RetrieveOnlyRequest(BaseModel):
    doc_id: str
    query: str
    top_k: int = 5

class RetrieveOnlyChunk(BaseModel):
    chunk: str
    score: float
    index: int

class RetrieveOnlyResponse(BaseModel):
    original_query: str
    rewritten_query: Optional[str] = None
    retrieved_chunks: List[RetrieveOnlyChunk]

class AskDebugResponse(BaseModel):
    query: str
    answer: str
    iterations: int
    context_sufficient: bool
    missing_information: List[str]
    citations: List[CitationInfo]
    trace: List[Dict[str, Any]]
    final_context: str
    fallback_used: bool
    session_id: Optional[str] = None
