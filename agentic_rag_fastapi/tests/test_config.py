"""
Config module unit tests.

Tests validate settings loading, property helpers, validators,
and the lru_cache singleton behaviour.
"""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest


class TestSettings:
    """Tests for config.Settings."""

    @pytest.mark.unit
    def test_default_demo_mode_is_true(self):
        from config import Settings

        s = Settings(groq_api_key="test-key")
        assert s.demo_mode is True

    @pytest.mark.unit
    def test_allowed_origins_list_parses_csv(self):
        from config import Settings

        s = Settings(
            groq_api_key="k",
            allowed_origins="http://localhost:3000,http://localhost:5173",
        )
        origins = s.allowed_origins_list
        assert "http://localhost:3000" in origins
        assert "http://localhost:5173" in origins
        assert len(origins) == 2

    @pytest.mark.unit
    def test_max_file_size_bytes_computed(self):
        from config import Settings

        s = Settings(groq_api_key="k", max_file_size_mb=10)
        assert s.max_file_size_bytes == 10 * 1024 * 1024

    @pytest.mark.unit
    def test_invalid_log_level_raises(self):
        from pydantic import ValidationError

        from config import Settings

        with pytest.raises(ValidationError):
            Settings(groq_api_key="k", log_level="VERBOSE")

    @pytest.mark.unit
    def test_valid_log_levels_accepted(self):
        from config import Settings

        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            s = Settings(groq_api_key="k", log_level=level)
            assert s.log_level == level

    @pytest.mark.unit
    def test_overlap_gte_chunk_size_raises(self):
        from pydantic import ValidationError

        from config import Settings

        with pytest.raises(ValidationError, match="chunk_overlap"):
            Settings(groq_api_key="k", chunk_size=3, chunk_overlap=3)

    @pytest.mark.unit
    def test_directory_properties_are_under_data_dir(self):
        from pathlib import Path

        from config import Settings

        s = Settings(groq_api_key="k", data_dir=Path("my_data"))
        assert s.upload_dir == Path("my_data") / "uploads"
        assert s.index_dir == Path("my_data") / "indexes"
        assert s.registry_path == Path("my_data") / "indexes" / "registry.json"

    @pytest.mark.unit
    def test_get_settings_returns_singleton(self):
        """get_settings() must return the same instance on repeated calls."""
        from config import get_settings

        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
        get_settings.cache_clear()
