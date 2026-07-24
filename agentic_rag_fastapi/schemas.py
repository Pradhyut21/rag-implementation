from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ReasoningMode(str, Enum):
    standard = "standard"
    cot = "cot"
    tot = "tot"


class ResponseMode(str, Enum):
    compact = "compact"
    detailed = "detailed"


class QueryRequest(BaseModel):
    query: str = Field(
        ..., min_length=1, max_length=2000, description="User query (max 2000 chars)"
    )
    doc_id: str = Field(..., min_length=4, max_length=16, description="8-char hex document ID")
    top_k: int = Field(3, ge=1, le=20, description="Number of chunks to retrieve (1-20)")
    include_trace: bool = Field(False, description="Include full iteration trace in response")
    response_mode: ResponseMode = Field(ResponseMode.compact, description="compact | detailed")
    reasoning_mode: ReasoningMode = Field(
        ReasoningMode.standard, description="standard | cot | tot"
    )

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be blank or whitespace only.")
        return v.strip()


class RetrievedChunk(BaseModel):
    chunk: str
    score: float
    index: int


class FanoutResult(BaseModel):
    sub_query: str
    rewritten_query: str
    retrieved: list[dict[str, Any]]


class SufficientContextResult(BaseModel):
    is_context_sufficient: bool
    missing_information: list[str]
    feedback_log: str
    reasoning_summary: str | None = None
    evidence_type: str | None = None


class TraceItem(BaseModel):
    iteration: int
    sub_queries: list[str]
    fanout_results: list[dict[str, Any]]
    aggregated_context: str
    intermediate_draft: str
    sufficient_context_result: dict[str, Any]


class CitationInfo(BaseModel):
    chunk_index: int
    text_preview: str
    score: float


class AskResponse(BaseModel):
    query: str
    answer: str
    iterations: int
    context_sufficient: bool
    missing_information: list[str]
    citations: list[CitationInfo]
    trace: list[dict[str, Any]] | None = None
    final_context: str | None = None
    session_id: str | None = None
    evidence_type: str | None = None
    fallback_used: bool | None = False


class VanillaAskResponse(BaseModel):
    query: str
    answer: str
    retrieved_chunks: list[dict[str, Any]]
    context: str
    citations: list[CitationInfo] | None = None


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
    ocr_used: bool | None = False


class PlanRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)

    @field_validator("query")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be blank.")
        return v.strip()


class PlanResponse(BaseModel):
    query: str
    sub_queries: list[str]


class RewriteRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)

    @field_validator("query")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be blank.")
        return v.strip()


class RewriteResponse(BaseModel):
    query: str
    rewritten_query: str


class RetrieveOnlyRequest(BaseModel):
    doc_id: str = Field(..., min_length=4, max_length=16)
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(5, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be blank.")
        return v.strip()


class RetrieveOnlyChunk(BaseModel):
    chunk: str
    score: float
    index: int


class RetrieveOnlyResponse(BaseModel):
    original_query: str
    rewritten_query: str | None = None
    retrieved_chunks: list[RetrieveOnlyChunk]


class AskDebugResponse(BaseModel):
    query: str
    answer: str
    iterations: int
    context_sufficient: bool
    missing_information: list[str]
    citations: list[CitationInfo]
    trace: list[dict[str, Any]]
    final_context: str
    fallback_used: bool
    session_id: str | None = None
    evidence_type: str | None = None
