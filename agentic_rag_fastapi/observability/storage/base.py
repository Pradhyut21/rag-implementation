"""
observability/storage/base.py — Abstract database interface for observability storage.

Defines the contract that any DB backend (SQLite, PostgreSQL, etc.) must implement.
Swap backends by setting DATABASE_URL env var and returning the appropriate
implementation from get_db() in db.py.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseDB(ABC):
    """Abstract base class for observability storage backends."""

    # ── Session & query tracing ───────────────────────────────

    @abstractmethod
    def save_session(self, session_id: str, query: str, timestamp: str) -> None: ...

    @abstractmethod
    def save_query_trace(self, data: dict[str, Any]) -> None: ...

    @abstractmethod
    def save_retrieval_result(self, data: dict[str, Any]) -> None: ...

    @abstractmethod
    def save_llm_call(self, data: dict[str, Any]) -> None: ...

    @abstractmethod
    def save_agent_step(self, data: dict[str, Any]) -> None: ...

    @abstractmethod
    def save_final_answer(self, data: dict[str, Any]) -> None: ...

    @abstractmethod
    def save_error_event(self, data: dict[str, Any]) -> None: ...

    @abstractmethod
    def save_pipeline_metric(self, data: dict[str, Any]) -> None: ...

    # ── Tree of Thought ───────────────────────────────────────

    @abstractmethod
    def save_reasoning_tree(
        self, session_id: str, query: str, timestamp: str, latency: float
    ) -> None: ...

    @abstractmethod
    def save_reasoning_branch(self, data: dict[str, Any]) -> None: ...

    @abstractmethod
    def save_branch_score(self, data: dict[str, Any]) -> None: ...

    @abstractmethod
    def save_branch_evaluation(
        self, branch_id: str, details: str, score: float
    ) -> None: ...

    @abstractmethod
    def save_winning_branch(
        self, session_id: str, branch_id: str, score: float
    ) -> None: ...

    # ── Reads ─────────────────────────────────────────────────

    @abstractmethod
    def get_sessions(self, limit: int = 50) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_session_trace(self, session_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def get_pipeline_metrics(self, limit: int = 100) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_dashboard_summary(self) -> dict[str, Any]: ...
