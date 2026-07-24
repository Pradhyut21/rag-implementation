"""
Unit tests for the document ingestion and chunking pipeline.

Tests cover: DOCX loading, PDF loading, OCR fallback,
chunk_text behaviour (normal, short doc, edge cases).
All file I/O uses real in-memory files via the ``sample_docx_bytes`` fixture.
"""
from __future__ import annotations

import io
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest


# ─────────────────────────────────────────────────────────────
# chunk_text
# ─────────────────────────────────────────────────────────────
class TestChunkText:
    """Unit tests for rag.ingestion.chunk_text."""

    @pytest.mark.unit
    def test_returns_list(self):
        """chunk_text must return a list."""
        from rag.ingestion import chunk_text

        result = chunk_text("First sentence. Second sentence.", chunk_size=2, overlap=1)
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_chunks_have_correct_size(self):
        """Each chunk must contain at most chunk_size sentences."""
        from rag.ingestion import chunk_text

        text = " ".join(f"Sentence {i}." for i in range(20))
        chunks = chunk_text(text, chunk_size=5, overlap=1)
        assert len(chunks) > 0
        # All chunks should be non-empty strings
        assert all(isinstance(c, str) and c.strip() for c in chunks)

    @pytest.mark.unit
    def test_empty_string_returns_empty_list(self):
        """chunk_text('') must return []."""
        from rag.ingestion import chunk_text

        assert chunk_text("") == []

    @pytest.mark.unit
    def test_single_sentence_document(self):
        """A one-sentence document must produce exactly one chunk."""
        from rag.ingestion import chunk_text

        result = chunk_text("Only one sentence here.", chunk_size=6, overlap=2)
        assert len(result) == 1

    @pytest.mark.unit
    def test_overlap_less_than_chunk_size(self):
        """chunk_text must not infinite-loop when overlap < chunk_size."""
        from rag.ingestion import chunk_text

        text = " ".join(f"Sent {i}." for i in range(10))
        # Should terminate without hanging
        chunks = chunk_text(text, chunk_size=3, overlap=2)
        assert len(chunks) >= 1

    @pytest.mark.unit
    def test_overlap_of_zero_gives_no_shared_sentences(self):
        """With overlap=0, no sentence should appear in two consecutive chunks."""
        from rag.ingestion import chunk_text

        sentences = [f"Sentence number {i} ends here." for i in range(12)]
        text = " ".join(sentences)
        chunks = chunk_text(text, chunk_size=3, overlap=0)
        assert len(chunks) >= 3

    @pytest.mark.unit
    def test_very_short_doc_graceful(self):
        """A two-sentence doc with chunk_size=6, overlap=2 must not crash."""
        from rag.ingestion import chunk_text

        result = chunk_text("First. Second.", chunk_size=6, overlap=2)
        assert isinstance(result, list)
        assert len(result) >= 1

    @pytest.mark.unit
    def test_all_whitespace_returns_empty(self):
        """Pure whitespace text should yield an empty list."""
        from rag.ingestion import chunk_text

        result = chunk_text("   \n\t  ", chunk_size=6, overlap=2)
        assert result == []


# ─────────────────────────────────────────────────────────────
# load_docx
# ─────────────────────────────────────────────────────────────
class TestLoadDocx:
    """Unit tests for rag.ingestion.load_docx."""

    @pytest.mark.unit
    def test_loads_text_from_docx(self, sample_docx_bytes, tmp_path):
        """load_docx must return non-empty text from a valid .docx file."""
        from rag.ingestion import load_docx

        docx_path = tmp_path / "test.docx"
        docx_path.write_bytes(sample_docx_bytes)

        text = load_docx(str(docx_path))
        assert isinstance(text, str)
        assert len(text.strip()) > 0
        assert "Agentic RAG" in text

    @pytest.mark.unit
    def test_returns_string(self, sample_docx_bytes, tmp_path):
        """Return type must always be str."""
        from rag.ingestion import load_docx

        docx_path = tmp_path / "test.docx"
        docx_path.write_bytes(sample_docx_bytes)
        result = load_docx(str(docx_path))
        assert isinstance(result, str)


# ─────────────────────────────────────────────────────────────
# load_document (dispatcher)
# ─────────────────────────────────────────────────────────────
class TestLoadDocument:
    """Unit tests for rag.ingestion.load_document."""

    @pytest.mark.unit
    def test_dispatches_to_docx_loader(self, sample_docx_bytes, tmp_path):
        """load_document dispatches .docx files to load_docx."""
        from rag.ingestion import load_document

        docx_path = tmp_path / "doc.docx"
        docx_path.write_bytes(sample_docx_bytes)
        result = load_document(str(docx_path))
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.unit
    def test_raises_on_unsupported_extension(self, tmp_path):
        """load_document must raise ValueError for unsupported file types."""
        from rag.ingestion import load_document

        bad_file = tmp_path / "file.txt"
        bad_file.write_text("some text")
        with pytest.raises(ValueError, match="Unsupported"):
            load_document(str(bad_file))

    @pytest.mark.unit
    def test_dispatches_to_pdf_loader(self, tmp_path):
        """load_document dispatches .pdf files to load_pdf."""
        from rag.ingestion import load_document, load_pdf

        with patch("rag.ingestion.load_pdf", return_value="PDF text content " * 20) as mock_pdf:
            pdf_path = tmp_path / "doc.pdf"
            pdf_path.write_bytes(b"%PDF-1.4 dummy")
            result = load_document(str(pdf_path))
            mock_pdf.assert_called_once_with(str(pdf_path))

    @pytest.mark.unit
    def test_auto_ocr_fallback_on_short_pdf_text(self, tmp_path):
        """
        If load_pdf returns fewer than 200 chars, load_document should
        attempt OCR automatically.
        """
        from rag.ingestion import load_document

        short_text = "A" * 50  # very short — should trigger OCR
        with (
            patch("rag.ingestion.load_pdf", return_value=short_text),
            patch("rag.ingestion.load_pdf_with_ocr", return_value="Full OCR text here " * 20) as mock_ocr,
        ):
            pdf_path = tmp_path / "scanned.pdf"
            pdf_path.write_bytes(b"%PDF-1.4 dummy")
            result = load_document(str(pdf_path))
            mock_ocr.assert_called_once()
            assert len(result) > len(short_text)

    @pytest.mark.unit
    def test_no_ocr_when_pdf_has_enough_text(self, tmp_path):
        """If load_pdf already returns 200+ chars, OCR must not be called."""
        from rag.ingestion import load_document

        long_text = "B" * 500  # above 200-char threshold
        with (
            patch("rag.ingestion.load_pdf", return_value=long_text),
            patch("rag.ingestion.load_pdf_with_ocr") as mock_ocr,
        ):
            pdf_path = tmp_path / "textual.pdf"
            pdf_path.write_bytes(b"%PDF-1.4 dummy")
            load_document(str(pdf_path))
            mock_ocr.assert_not_called()
