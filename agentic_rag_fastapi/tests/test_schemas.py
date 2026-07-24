"""
Unit tests for Pydantic schema validation.

Tests cover: required field enforcement, field constraints (min/max),
enum validation (ReasoningMode, ResponseMode), blank-query rejection,
and correct default values.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError


# ─────────────────────────────────────────────────────────────
# QueryRequest
# ─────────────────────────────────────────────────────────────
class TestQueryRequest:
    """Tests for schemas.QueryRequest."""

    @pytest.mark.unit
    def test_valid_request_minimal(self):
        """Minimal valid QueryRequest must not raise."""
        from schemas import QueryRequest

        req = QueryRequest(query="Hello world?", doc_id="abc12345")
        assert req.query == "Hello world?"
        assert req.doc_id == "abc12345"
        assert req.top_k == 3                        # default
        assert req.reasoning_mode.value == "standard"  # default

    @pytest.mark.unit
    def test_query_too_long_raises(self):
        """Query longer than 2000 chars must raise ValidationError."""
        from schemas import QueryRequest

        with pytest.raises(ValidationError, match="2000"):
            QueryRequest(query="x" * 2001, doc_id="abc12345")

    @pytest.mark.unit
    def test_blank_query_raises(self):
        """Blank / whitespace-only query must raise ValidationError."""
        from schemas import QueryRequest

        with pytest.raises(ValidationError):
            QueryRequest(query="   ", doc_id="abc12345")

    @pytest.mark.unit
    def test_query_stripped(self):
        """Leading/trailing whitespace should be stripped from query."""
        from schemas import QueryRequest

        req = QueryRequest(query="  trimmed  ", doc_id="abc12345")
        assert req.query == "trimmed"

    @pytest.mark.unit
    def test_top_k_min_max(self):
        """top_k must be between 1 and 20 inclusive."""
        from schemas import QueryRequest

        with pytest.raises(ValidationError):
            QueryRequest(query="q", doc_id="abc12345", top_k=0)
        with pytest.raises(ValidationError):
            QueryRequest(query="q", doc_id="abc12345", top_k=21)

    @pytest.mark.unit
    def test_valid_reasoning_modes(self):
        """All three reasoning mode values must be accepted."""
        from schemas import QueryRequest, ReasoningMode

        for mode in ["standard", "cot", "tot"]:
            req = QueryRequest(query="q", doc_id="abc12345", reasoning_mode=mode)
            assert req.reasoning_mode == ReasoningMode(mode)

    @pytest.mark.unit
    def test_invalid_reasoning_mode_raises(self):
        """An unknown reasoning_mode value must raise ValidationError."""
        from schemas import QueryRequest

        with pytest.raises(ValidationError):
            QueryRequest(query="q", doc_id="abc12345", reasoning_mode="gpt4")

    @pytest.mark.unit
    def test_valid_response_modes(self):
        """Both response_mode values must be accepted."""
        from schemas import QueryRequest

        for mode in ["compact", "detailed"]:
            req = QueryRequest(query="q", doc_id="abc12345", response_mode=mode)
            assert req.response_mode.value == mode

    @pytest.mark.unit
    def test_doc_id_too_short_raises(self):
        """doc_id shorter than 4 chars must raise ValidationError."""
        from schemas import QueryRequest

        with pytest.raises(ValidationError):
            QueryRequest(query="q", doc_id="ab")


# ─────────────────────────────────────────────────────────────
# PlanRequest / RewriteRequest / RetrieveOnlyRequest
# ─────────────────────────────────────────────────────────────
class TestAuxiliarySchemas:
    """Tests for auxiliary request schemas."""

    @pytest.mark.unit
    def test_plan_request_blank_raises(self):
        from schemas import PlanRequest

        with pytest.raises(ValidationError):
            PlanRequest(query="  \t  ")

    @pytest.mark.unit
    def test_rewrite_request_valid(self):
        from schemas import RewriteRequest

        req = RewriteRequest(query="What is the latency?")
        assert req.query == "What is the latency?"

    @pytest.mark.unit
    def test_retrieve_only_top_k_bounds(self):
        from schemas import RetrieveOnlyRequest

        with pytest.raises(ValidationError):
            RetrieveOnlyRequest(doc_id="abc12345", query="q", top_k=25)

    @pytest.mark.unit
    def test_retrieve_only_valid(self):
        from schemas import RetrieveOnlyRequest

        req = RetrieveOnlyRequest(doc_id="abc12345", query="test query", top_k=5)
        assert req.top_k == 5


# ─────────────────────────────────────────────────────────────
# Response models
# ─────────────────────────────────────────────────────────────
class TestResponseSchemas:
    """Tests for response model instantiation."""

    @pytest.mark.unit
    def test_ask_response_instantiation(self):
        from schemas import AskResponse, CitationInfo

        resp = AskResponse(
            query="test query",
            answer="test answer",
            iterations=1,
            context_sufficient=True,
            missing_information=[],
            citations=[CitationInfo(chunk_index=0, text_preview="preview", score=0.9)],
        )
        assert resp.answer == "test answer"
        assert resp.iterations == 1
        assert len(resp.citations) == 1

    @pytest.mark.unit
    def test_upload_doc_response(self):
        from schemas import UploadDocResponse

        resp = UploadDocResponse(
            message="Document indexed",
            doc_id="abc12345",
            file_name="test.pdf",
            num_chunks=10,
        )
        assert resp.num_chunks == 10

    @pytest.mark.unit
    def test_document_info_response_ocr_defaults_false(self):
        from schemas import DocumentInfoResponse

        resp = DocumentInfoResponse(
            doc_id="abc12345",
            file_name="doc.pdf",
            uploaded_at="2026-01-01T00:00:00Z",
            num_chunks=5,
            chunk_size=6,
            overlap=2,
            embedding_model="all-MiniLM-L6-v2",
        )
        assert resp.ocr_used is False

    @pytest.mark.unit
    def test_plan_response(self):
        from schemas import PlanResponse

        resp = PlanResponse(query="q", sub_queries=["sq1", "sq2"])
        assert len(resp.sub_queries) == 2
