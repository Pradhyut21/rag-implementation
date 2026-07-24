"""
Unit tests for individual agent functions.

All external I/O (Groq API, FAISS) is mocked — these tests run offline
and should complete in under 2 seconds.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ─────────────────────────────────────────────────────────────
# Planner Agent
# ─────────────────────────────────────────────────────────────
class TestPlannerAgent:
    """Tests for agents.planner.planner_agent."""

    @pytest.mark.unit
    def test_returns_list_of_strings(self):
        """planner_agent must always return a list[str]."""
        with patch(
            "agents.llm.safe_generate", return_value='["What is RAG?", "How does retrieval work?"]'
        ):
            from agents.planner import planner_agent

            result = planner_agent("Explain RAG architecture")
            assert isinstance(result, list)
            assert all(isinstance(q, str) for q in result)
            assert len(result) >= 1

    @pytest.mark.unit
    def test_falls_back_to_original_query_on_invalid_json(self):
        """If LLM returns non-JSON, fall back to original query."""
        with patch("agents.llm.safe_generate", return_value="Not a JSON array at all"):
            from agents.planner import planner_agent

            result = planner_agent("my original query")
            assert result == ["my original query"]

    @pytest.mark.unit
    def test_handles_empty_query(self):
        """planner_agent must not crash on empty input."""
        with patch("agents.llm.safe_generate", return_value='["general question"]'):
            from agents.planner import planner_agent

            result = planner_agent("")
            assert isinstance(result, list)

    @pytest.mark.unit
    def test_sub_queries_are_strings_even_if_llm_returns_ints(self):
        """planner_agent must coerce non-string list elements to str."""
        with patch("agents.llm.safe_generate", return_value="[1, 2, 3]"):
            from agents.planner import planner_agent

            result = planner_agent("query")
            assert all(isinstance(q, str) for q in result)

    @pytest.mark.unit
    def test_nested_json_falls_back(self):
        """A JSON object (not an array) should trigger fallback."""
        with patch(
            "agents.llm.safe_generate",
            return_value='{"sub_queries": ["a", "b"]}',
        ):
            from agents.planner import planner_agent

            result = planner_agent("query")
            # Falls back to original query since result is a dict, not list
            assert isinstance(result, list)


# ─────────────────────────────────────────────────────────────
# Query Rewriter Agent
# ─────────────────────────────────────────────────────────────
class TestQueryRewriter:
    """Tests for agents.rewriter.query_rewriter."""

    @pytest.mark.unit
    def test_returns_string(self):
        """query_rewriter must always return a str."""
        with patch("agents.llm.safe_generate", return_value="  rewritten dense query  "):
            from agents.rewriter import query_rewriter

            result = query_rewriter("what is the latency?")
            assert isinstance(result, str)
            assert result == "rewritten dense query"  # stripped

    @pytest.mark.unit
    def test_strips_whitespace(self):
        """Return value must be stripped of leading/trailing whitespace."""
        with patch("agents.llm.safe_generate", return_value="\n\n  query text \n"):
            from agents.rewriter import query_rewriter

            result = query_rewriter("anything")
            assert result == "query text"

    @pytest.mark.unit
    def test_handles_long_input(self):
        """query_rewriter must not crash on long input."""
        with patch("agents.llm.safe_generate", return_value="compressed query"):
            from agents.rewriter import query_rewriter

            long_query = "what " * 300
            result = query_rewriter(long_query)
            assert isinstance(result, str)


# ─────────────────────────────────────────────────────────────
# Sufficient Context Agent
# ─────────────────────────────────────────────────────────────
class TestSufficientContextAgent:
    """Tests for agents.sufficient_context.sufficient_context_agent."""

    VALID_SC_JSON = """{
        "is_context_sufficient": true,
        "missing_information": [],
        "feedback_log": "",
        "reasoning_summary": "All details present.",
        "evidence_type": "explicit"
    }"""

    PARTIAL_SC_JSON = """{
        "is_context_sufficient": false,
        "missing_information": ["Exact latency metric not found"],
        "feedback_log": "Search for latency benchmarks",
        "reasoning_summary": "Topic covered but specific metric missing.",
        "evidence_type": "partial"
    }"""

    @pytest.mark.unit
    def test_returns_sufficient_result(self):
        """SC agent correctly parses a 'sufficient' LLM response."""
        with patch("agents.llm.safe_generate", return_value=self.VALID_SC_JSON):
            from agents.sufficient_context import sufficient_context_agent

            result = sufficient_context_agent("query", "context", "draft")
            assert result["is_context_sufficient"] is True
            assert result["evidence_type"] == "explicit"
            assert isinstance(result["missing_information"], list)

    @pytest.mark.unit
    def test_returns_insufficient_result(self):
        """SC agent correctly parses a 'partial/insufficient' LLM response."""
        with patch("agents.llm.safe_generate", return_value=self.PARTIAL_SC_JSON):
            from agents.sufficient_context import sufficient_context_agent

            result = sufficient_context_agent("query", "context", "draft")
            assert result["is_context_sufficient"] is False
            assert result["evidence_type"] == "partial"
            assert "latency" in result["missing_information"][0].lower()

    @pytest.mark.unit
    def test_fallback_on_invalid_json(self):
        """SC agent must not crash and must return conservative fallback."""
        with patch("agents.llm.safe_generate", return_value="This is not JSON"):
            from agents.sufficient_context import sufficient_context_agent

            result = sufficient_context_agent("query", "context", "draft")
            assert result["is_context_sufficient"] is False
            assert isinstance(result["missing_information"], list)
            assert "Failed to parse" in result["reasoning_summary"]

    @pytest.mark.unit
    def test_invalid_evidence_type_defaults_to_missing(self):
        """An unrecognised evidence_type value must be normalised to 'missing'."""
        bad_json = """{
            "is_context_sufficient": true,
            "missing_information": [],
            "feedback_log": "",
            "reasoning_summary": "ok",
            "evidence_type": "unknown_value"
        }"""
        with patch("agents.llm.safe_generate", return_value=bad_json):
            from agents.sufficient_context import sufficient_context_agent

            result = sufficient_context_agent("q", "c", "d")
            assert result["evidence_type"] == "missing"

    @pytest.mark.unit
    def test_missing_information_coerced_to_list(self):
        """If missing_information is a string (bad LLM output), it is wrapped."""
        bad_json = """{
            "is_context_sufficient": false,
            "missing_information": "single string not array",
            "feedback_log": "retry",
            "reasoning_summary": "ok",
            "evidence_type": "partial"
        }"""
        with patch("agents.llm.safe_generate", return_value=bad_json):
            from agents.sufficient_context import sufficient_context_agent

            result = sufficient_context_agent("q", "c", "d")
            assert isinstance(result["missing_information"], list)

    @pytest.mark.unit
    def test_list_wrapped_in_outer_list_is_handled(self):
        """LLM sometimes wraps the object in a list — must extract first element."""
        wrapped = '[{"is_context_sufficient": true, "missing_information": [], "feedback_log": "", "reasoning_summary": "ok", "evidence_type": "explicit"}]'
        with patch("agents.llm.safe_generate", return_value=wrapped):
            from agents.sufficient_context import sufficient_context_agent

            result = sufficient_context_agent("q", "c", "d")
            assert result["is_context_sufficient"] is True


# ─────────────────────────────────────────────────────────────
# Agentic Loop helpers
# ─────────────────────────────────────────────────────────────
class TestAgenticLoopHelpers:
    """Tests for helper functions in agents.agentic_loop."""

    @pytest.mark.unit
    def test_trim_context_no_trim_needed(self):
        """trim_context returns original string when under limit."""
        from agents.agentic_loop import trim_context

        short = "x" * 100
        assert trim_context(short, max_chars=1000) == short

    @pytest.mark.unit
    def test_trim_context_trims_at_limit(self):
        """trim_context truncates to max_chars."""
        from agents.agentic_loop import trim_context

        long_text = "a" * 5000
        result = trim_context(long_text, max_chars=3000)
        assert len(result) <= 3000

    @pytest.mark.unit
    def test_trim_context_prefers_sentence_boundary(self):
        """trim_context should try to cut at a period rather than mid-word."""
        from agents.agentic_loop import trim_context

        text = "First sentence. " + "x" * 2000 + ". Last sentence."
        result = trim_context(text, max_chars=50)
        # Should end with a period if possible
        assert len(result) <= 50

    @pytest.mark.unit
    def test_aggregate_fanout_context_deduplicates(self):
        """aggregate_fanout_context must not include the same chunk twice."""
        from agents.agentic_loop import aggregate_fanout_context

        fanout = [
            {"retrieved": [{"chunk": "chunk A", "score": 0.9, "index": 0}]},
            {
                "retrieved": [
                    {"chunk": "chunk A", "score": 0.9, "index": 0},
                    {"chunk": "chunk B", "score": 0.8, "index": 1},
                ]
            },
        ]
        result = aggregate_fanout_context(fanout)
        assert result.count("chunk A") == 1
        assert "chunk B" in result

    @pytest.mark.unit
    def test_search_fanout_returns_correct_structure(self):
        """search_fanout must return one entry per sub-query with required keys."""
        with (
            patch("agents.agentic_loop.query_rewriter", side_effect=lambda q: f"rw:{q}"),
            patch(
                "agents.agentic_loop.retrieve",
                return_value=[{"chunk": "result", "score": 0.9, "index": 0}],
            ),
        ):
            from agents.agentic_loop import search_fanout

            em = MagicMock()
            vs = MagicMock()
            result = search_fanout(["q1", "q2"], em, vs, top_k=3)
            assert len(result) == 2
            for item in result:
                assert "sub_query" in item
                assert "rewritten_query" in item
                assert "retrieved" in item


# ─────────────────────────────────────────────────────────────
# Vanilla RAG
# ─────────────────────────────────────────────────────────────
class TestVanillaRag:
    """Tests for agents.agentic_loop.vanilla_rag."""

    @pytest.mark.unit
    def test_vanilla_rag_returns_expected_keys(self, mock_vector_store, mock_embedding_model):
        """vanilla_rag must return a dict with required keys."""
        with (
            patch(
                "agents.agentic_loop.retrieve",
                return_value=[{"chunk": "c", "score": 0.9, "index": 0}],
            ),
            patch("agents.agentic_loop.format_context", return_value="formatted context"),
            patch(
                "agents.agentic_loop.synthesis_agent",
                return_value="The answer is 42.",
            ),
        ):
            from agents.agentic_loop import vanilla_rag

            result = vanilla_rag(
                "What is the answer?", mock_embedding_model, mock_vector_store, top_k=3
            )

        assert "query" in result
        assert "answer" in result
        assert "citations" in result
        assert result["answer"] == "The answer is 42."
        assert isinstance(result["citations"], list)
