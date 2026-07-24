"""
Test package for the Agentic RAG Platform backend.

Test organisation
-----------------
tests/
├── conftest.py              — shared fixtures (FastAPI TestClient, mock LLM, mock FAISS)
├── test_health.py           — /health endpoint
├── test_upload.py           — /upload-doc, /upload-doc-ocr, /documents
├── test_query.py            — /ask, /vanilla-ask, /ask-debug
├── test_agents.py           — unit tests for each agent function
├── test_ingestion.py        — PDF/DOCX loading + chunking
├── test_schemas.py          — Pydantic schema validation
├── test_security.py         — auth, CORS, rate limiting, file validation
└── test_integration.py      — end-to-end pipeline smoke tests

Markers
-------
- @pytest.mark.unit        : no I/O, all external calls mocked
- @pytest.mark.integration : requires running backend + real files
- @pytest.mark.slow        : takes more than 5 s
- @pytest.mark.llm         : calls the real Groq API
"""
