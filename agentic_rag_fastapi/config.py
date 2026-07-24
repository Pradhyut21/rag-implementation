"""
Centralized configuration management for the Agentic RAG Platform.

Uses pydantic-settings to load and validate all configuration from
environment variables and .env files. Single source of truth for all
runtime parameters — no magic strings scattered across the codebase.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables / .env file.

    All settings are validated at startup. Missing required settings
    raise a ``ValidationError`` with a clear error message.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────────────────
    groq_api_key: str = Field(..., description="Groq API key (required)")
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model ID to use for all agent calls",
    )
    llm_temperature: float = Field(
        default=0.0, ge=0.0, le=2.0, description="LLM sampling temperature"
    )
    llm_max_retries: int = Field(default=5, ge=1, le=10, description="Max LLM retry attempts")

    # ── API Security ──────────────────────────────────────────
    api_key: str = Field(
        default="<your-api-key>",
        description="X-API-Key header value for endpoint protection",
    )
    demo_mode: bool = Field(
        default=False,
        description="If True, API key check is skipped (development only)",
    )

    # ── CORS ──────────────────────────────────────────────────
    allowed_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
        description="Comma-separated list of allowed CORS origins",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """Return parsed list of allowed CORS origins."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    # ── Rate Limiting ─────────────────────────────────────────
    rate_limit_query: str = Field(
        default="30/minute",
        description="slowapi rate limit for query endpoints",
    )
    rate_limit_upload: str = Field(
        default="20/hour",
        description="slowapi rate limit for upload endpoints",
    )

    # ── File Upload ───────────────────────────────────────────
    max_file_size_mb: int = Field(
        default=20, ge=1, le=500, description="Maximum upload file size in MB"
    )

    @property
    def max_file_size_bytes(self) -> int:
        """Return max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    # ── Chunking ──────────────────────────────────────────────
    chunk_size: int = Field(
        default=6, ge=1, le=50, description="Number of sentences per chunk"
    )
    chunk_overlap: int = Field(
        default=2, ge=0, le=10, description="Number of overlapping sentences between chunks"
    )
    max_context_chars: int = Field(
        default=14000,
        ge=1000,
        le=100000,
        description="Maximum characters in aggregated retrieval context",
    )

    # ── Pipeline ──────────────────────────────────────────────
    max_rag_iterations: int = Field(
        default=2, ge=1, le=5, description="Maximum self-correcting feedback loop iterations"
    )
    default_top_k: int = Field(
        default=3, ge=1, le=20, description="Default number of FAISS chunks to retrieve"
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="sentence-transformers model for embedding documents",
    )

    # ── Paths ─────────────────────────────────────────────────
    data_dir: Path = Field(
        default=Path("data"),
        description="Base data directory for uploads, indexes, debug runs",
    )

    @property
    def upload_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def index_dir(self) -> Path:
        return self.data_dir / "indexes"

    @property
    def debug_runs_dir(self) -> Path:
        return self.data_dir / "debug_runs"

    @property
    def registry_path(self) -> Path:
        return self.index_dir / "registry.json"

    # ── Observability ─────────────────────────────────────────
    observability_db_path: str = Field(
        default="observability.db",
        description="Path to the SQLite observability database",
    )
    log_level: str = Field(
        default="INFO",
        description="Python logging level (DEBUG, INFO, WARNING, ERROR)",
    )

    # ── Server ────────────────────────────────────────────────
    host: str = Field(default="0.0.0.0", description="Uvicorn bind host")
    port: int = Field(default=8002, ge=1024, le=65535, description="Uvicorn bind port")
    workers: int = Field(default=2, ge=1, le=32, description="Number of uvicorn workers")
    reload: bool = Field(default=False, description="Enable uvicorn auto-reload (dev only)")

    # ── Validators ────────────────────────────────────────────
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is a valid Python logging level."""
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            msg = f"log_level must be one of {valid}, got {v!r}"
            raise ValueError(msg)
        return upper

    @field_validator("chunk_overlap")
    @classmethod
    def overlap_less_than_chunk(cls, v: int, info) -> int:
        """Ensure chunk_overlap < chunk_size."""
        chunk_size = info.data.get("chunk_size", 6)
        if v >= chunk_size:
            msg = f"chunk_overlap ({v}) must be less than chunk_size ({chunk_size})"
            raise ValueError(msg)
        return v

    def create_directories(self) -> None:
        """Create all required data directories if they do not exist."""
        for d in [self.upload_dir, self.index_dir, self.debug_runs_dir]:
            d.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the singleton Settings instance.

    Uses ``lru_cache`` to ensure the .env file is parsed exactly once
    per process lifetime. Call ``get_settings.cache_clear()`` in tests
    to reload settings with different environment variables.
    """
    return Settings()


# Convenience alias for use in FastAPI ``Depends``
settings = get_settings()
