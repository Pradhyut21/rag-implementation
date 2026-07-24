from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import logging
import os
import threading
import uuid

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import nltk
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sse_starlette.sse import EventSourceResponse

from agents.agentic_loop import agentic_rag, vanilla_rag
from agents.planner import planner_agent
from agents.rewriter import query_rewriter
from rag.embeddings import EmbeddingModel
from rag.ingestion import chunk_text, load_document
from rag.retrieval import retrieve
from rag.vector_store import FaissVectorStore, VectorStore, create_vector_store
from schemas import (
    AskDebugResponse,
    AskResponse,
    DocumentInfoResponse,
    PlanRequest,
    PlanResponse,
    QueryRequest,
    RetrieveOnlyRequest,
    RetrieveOnlyResponse,
    RewriteRequest,
    RewriteResponse,
    UploadDocResponse,
    VanillaAskResponse,
)

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("agentic_rag_api")

# ── Observability setup ───────────────────────────────────────
from observability import ObservabilityMiddleware, setup_observability
from observability.routes import router as observability_router

setup_observability()

# ── NLTK ─────────────────────────────────────────────────────
try:
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)
except Exception as e:
    logger.warning(f"NLTK download failed: {e}")

# ── Rate Limiter ──────────────────────────────────────────────
from fastapi.responses import JSONResponse
from groq import AuthenticationError, GroqError

limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour"])

# ── FastAPI app ───────────────────────────────────────────────
app = FastAPI(
    title="Agentic RAG API",
    version="3.0",
    description="Enterprise Self-Correcting RAG with CoT, ToT, and full observability.",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(AuthenticationError)
async def groq_auth_error_handler(request: Request, exc: AuthenticationError):
    logger.error(f"Groq AuthenticationError: {exc}")
    return JSONResponse(
        status_code=401,
        content={"detail": "Groq API key authentication failed. Please update GROQ_API_KEY in your .env file with a valid key from https://console.groq.com/keys."},
    )

@app.exception_handler(GroqError)
async def groq_generic_error_handler(request: Request, exc: GroqError):
    logger.error(f"Groq API error: {exc}")
    return JSONResponse(
        status_code=502,
        content={"detail": f"Groq LLM service error: {str(exc)}"},
    )

app.add_middleware(ObservabilityMiddleware)

# ── CORS (restrict in production) ────────────────────────────
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(observability_router)

# ── JWT Auth (replaces shared API key) ────────────────────────
from auth import COOKIE_NAME, authenticate_user, create_access_token, get_current_user

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

if DEMO_MODE:
    logger.warning("⚠️ DEMO_MODE is ENABLED — JWT auth verification is bypassed for development.")


@app.post("/auth/token", tags=["Auth"], summary="Obtain JWT access token via httpOnly cookie")
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Authenticate with username + password and receive a JWT stored in an httpOnly cookie.
    Also returns access_token in body for headless API clients.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user["username"]})

    # Set httpOnly cookie (XSS protected)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in HTTPS production environments
        max_age=8 * 3600,
        path="/",
    )
    logger.info(f"JWT issued for user: {user['username']}")
    return {"username": user["username"], "access_token": token, "token_type": "bearer"}


@app.post("/auth/logout", tags=["Auth"], summary="Clear authentication cookie")
async def logout(response: Response):
    """Clear the httpOnly authentication cookie."""
    response.delete_cookie(key=COOKIE_NAME, httponly=True, samesite="lax", path="/")
    return {"message": "Logged out successfully"}


@app.get("/auth/me", tags=["Auth"], summary="Get current logged in user")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return user info for the currently authenticated session."""
    return {"username": current_user["username"], "role": current_user.get("role", "user")}


# ── File / Query constants ────────────────────────────────────
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_QUERY_LENGTH = 2000
UPLOAD_DIR = "data/uploads"
INDEX_DIR = "data/indexes"
DEBUG_RUNS_DIR = "data/debug_runs"
REGISTRY_PATH = os.path.join(INDEX_DIR, "registry.json")

for d in [UPLOAD_DIR, INDEX_DIR, DEBUG_RUNS_DIR]:
    os.makedirs(d, exist_ok=True)

# ── Global models (singletons with thread safety) ─────────────
embedding_model = EmbeddingModel()
loaded_vector_stores: dict[str, FaissVectorStore] = {}
_vs_lock = threading.Lock()  # Thread-safe vector store cache
_registry_lock = threading.Lock()  # Thread-safe registry access


# ── Registry helpers (atomic writes) ─────────────────────────
def load_registry() -> dict:
    with _registry_lock:
        if not os.path.exists(REGISTRY_PATH):
            return {}
        try:
            with open(REGISTRY_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            return {}


def save_registry(registry: dict):
    """Atomic write using a temp file + os.replace to prevent corruption."""
    with _registry_lock:
        try:
            tmp_path = REGISTRY_PATH + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=2)
            os.replace(tmp_path, REGISTRY_PATH)
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")


def get_doc_metadata(doc_id: str) -> dict:
    registry = load_registry()
    if doc_id not in registry:
        raise HTTPException(status_code=404, detail=f"Document ID '{doc_id}' not found.")
    return registry[doc_id]


def get_vector_store_for_doc(doc_id: str) -> VectorStore:
    registry = load_registry()
    if doc_id not in registry:
        raise HTTPException(status_code=404, detail=f"Document ID '{doc_id}' not found.")

    with _vs_lock:
        if doc_id in loaded_vector_stores:
            return loaded_vector_stores[doc_id]

    meta = registry[doc_id]
    index_path = meta["index_path"]
    chunks_path = meta["chunks_path"]

    if not os.path.exists(index_path) or not os.path.exists(chunks_path):
        raise HTTPException(status_code=404, detail=f"Index files missing for doc '{doc_id}'.")

    try:
        vs = create_vector_store(os.getenv("VECTOR_BACKEND", "faiss"))
        vs.load(index_path, chunks_path)
        with _vs_lock:
            loaded_vector_stores[doc_id] = vs
        logger.info(f"Loaded and cached VectorStore for doc_id: {doc_id}")
        return vs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load vector store: {e!s}")


# ── Sanitize filename ─────────────────────────────────────────
def safe_filename(filename: str) -> str:
    """Strip directory traversal and enforce safe characters."""
    basename = os.path.basename(filename)
    # Keep only alphanumeric, dash, underscore, dot
    safe = "".join(c for c in basename if c.isalnum() or c in "-_.")
    return safe or "upload"


# ── Helpers ───────────────────────────────────────────────────
def validate_query(query: str):
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    if len(query) > MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Query too long ({len(query)} chars). Maximum is {MAX_QUERY_LENGTH}.",
        )


# ── Routes ────────────────────────────────────────────────────


@app.get("/", tags=["Health"])
def read_root():
    return {"message": "Enterprise Agentic RAG API v3.0", "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "ok",
        "version": "3.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "features": ["standard", "cot", "tot", "observability", "streaming"],
    }


# ── Upload ────────────────────────────────────────────────────
@app.post("/upload-doc", response_model=UploadDocResponse, tags=["Documents"])
@limiter.limit("20/hour")
async def upload_doc(
    request: Request,
    file: UploadFile = File(...),
    _key: dict = Depends(get_current_user),
):
    filename = file.filename or "upload"
    filename = safe_filename(filename)

    if not filename.lower().endswith((".docx", ".pdf")):
        raise HTTPException(status_code=400, detail="Only .pdf and .docx files are supported.")

    content = await file.read()

    # File size guard
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(content) // 1024 // 1024}MB). Maximum is {MAX_FILE_SIZE_MB}MB.",
        )

    # Magic bytes validation
    if filename.lower().endswith(".pdf") and not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400, detail="File claims to be PDF but magic bytes are invalid."
        )

    doc_id = uuid.uuid4().hex[:8]
    unique_name = f"{doc_id}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e!s}")

    # Extract text
    try:
        text = load_document(file_path)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {e!s}")

    if not text.strip():
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail="Document has no readable text. If it is a scanned PDF, enable OCR mode.",
        )

    chunk_size = 6
    overlap = 2
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="No text chunks could be extracted.")

    try:
        embeddings = embedding_model.embed_texts(chunks)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e!s}")

    try:
        vs = VectorStore()
        vs.build_index(embeddings, chunks)
        index_path = os.path.join(INDEX_DIR, f"{doc_id}.index")
        chunks_path = os.path.join(INDEX_DIR, f"{doc_id}_chunks.pkl")
        vs.save(index_path, chunks_path)
        with _vs_lock:
            loaded_vector_stores[doc_id] = vs
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Index build failed: {e!s}")

    registry = load_registry()
    registry[doc_id] = {
        "doc_id": doc_id,
        "file_name": filename,
        "uploaded_at": datetime.utcnow().isoformat() + "Z",
        "num_chunks": len(chunks),
        "upload_path": file_path,
        "index_path": index_path,
        "chunks_path": chunks_path,
        "chunk_size": chunk_size,
        "overlap": overlap,
        "embedding_model": "all-MiniLM-L6-v2",
    }
    save_registry(registry)

    logger.info(f"Indexed '{filename}' → doc_id={doc_id}, chunks={len(chunks)}")
    return {
        "message": "Document indexed successfully",
        "doc_id": doc_id,
        "file_name": filename,
        "num_chunks": len(chunks),
    }


# ── Ask (Agentic) ─────────────────────────────────────────────
@app.post("/ask", response_model=AskResponse, tags=["RAG"])
@limiter.limit("30/minute")
def ask_question(
    request: Request,
    body: QueryRequest,
    _key: dict = Depends(get_current_user),
):
    validate_query(body.query)
    vs = get_vector_store_for_doc(body.doc_id)
    try:
        result = agentic_rag(
            query=body.query,
            embedding_model=embedding_model,
            vector_store=vs,
            top_k=body.top_k,
            reasoning_mode=body.reasoning_mode or "standard",
        )
        if body.response_mode == "compact" and not body.include_trace:
            result["trace"] = None
            result["final_context"] = None
        return result
    except Exception as e:
        logger.exception(f"Agentic RAG failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e!s}")


# ── Ask (Vanilla) ─────────────────────────────────────────────
@app.post("/vanilla-ask", response_model=VanillaAskResponse, tags=["RAG"])
@limiter.limit("30/minute")
def vanilla_question(
    request: Request,
    body: QueryRequest,
    _key: dict = Depends(get_current_user),
):
    validate_query(body.query)
    vs = get_vector_store_for_doc(body.doc_id)
    try:
        result = vanilla_rag(
            query=body.query, embedding_model=embedding_model, vector_store=vs, top_k=body.top_k
        )
        return result
    except Exception as e:
        logger.exception(f"Vanilla RAG failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e!s}")


# ── Ask Debug ─────────────────────────────────────────────────
@app.post("/ask-debug", response_model=AskDebugResponse, tags=["RAG"])
@limiter.limit("20/minute")
def ask_debug_question(
    request: Request,
    body: QueryRequest,
    _key: dict = Depends(get_current_user),
):
    validate_query(body.query)
    vs = get_vector_store_for_doc(body.doc_id)
    try:
        result = agentic_rag(
            query=body.query,
            embedding_model=embedding_model,
            vector_store=vs,
            top_k=body.top_k,
            reasoning_mode=body.reasoning_mode or "standard",
        )
        response_data = {
            "query": result["query"],
            "answer": result["answer"],
            "iterations": result["iterations"],
            "context_sufficient": result["context_sufficient"],
            "missing_information": result["missing_information"],
            "citations": result["citations"],
            "trace": result["trace"],
            "final_context": result["final_context"],
            "fallback_used": result.get("fallback_used", False),
            "session_id": result.get("session_id"),
        }
        # Save debug run log
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(DEBUG_RUNS_DIR, f"{ts}_{body.doc_id}.json")
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(response_data, f, indent=2, default=str)
        except Exception as log_err:
            logger.error(f"Failed to write debug log: {log_err}")
        return response_data
    except Exception as e:
        logger.exception(f"Debug RAG failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e!s}")


# ── Streaming Ask (SSE) ───────────────────────────────────────
@app.post("/stream-ask", tags=["RAG"])
@limiter.limit("20/minute")
async def stream_ask(
    request: Request,
    body: QueryRequest,
    _key: dict = Depends(get_current_user),
):
    """
    Server-Sent Events endpoint.
    Emits: stage_update, result, error events.
    """
    validate_query(body.query)
    vs = get_vector_store_for_doc(body.doc_id)

    async def event_generator():
        import asyncio

        executor = ThreadPoolExecutor(max_workers=1)

        def run_pipeline():
            return agentic_rag(
                query=body.query,
                embedding_model=embedding_model,
                vector_store=vs,
                top_k=body.top_k,
                reasoning_mode=body.reasoning_mode or "standard",
            )

        try:
            # Send stage updates
            stages = [
                "Planning sub-queries...",
                "Rewriting queries for dense retrieval...",
                "Running FAISS fanout search...",
                "Auditing context sufficiency...",
                "Synthesizing final answer...",
            ]
            for i, stage in enumerate(stages):
                yield {
                    "event": "stage",
                    "data": json.dumps({"stage": stage, "step": i + 1, "total": len(stages)}),
                }
                await asyncio.sleep(0.3)

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(executor, run_pipeline)

            yield {
                "event": "result",
                "data": json.dumps(
                    {
                        "answer": result["answer"],
                        "iterations": result["iterations"],
                        "context_sufficient": result["context_sufficient"],
                        "evidence_type": result.get("trace", [{}])[-1]
                        .get("sufficient_context_result", {})
                        .get("evidence_type")
                        if result.get("trace")
                        else None,
                        "citations": result["citations"],
                        "session_id": result.get("session_id"),
                        "trace": result.get("trace", []),
                        "fallback_used": result.get("fallback_used", False),
                    },
                    default=str,
                ),
            }
            yield {"event": "done", "data": "complete"}

        except Exception as e:
            logger.exception(f"Streaming pipeline error: {e}")
            yield {"event": "error", "data": json.dumps({"message": str(e)})}

    return EventSourceResponse(event_generator())


# ── Document Management ───────────────────────────────────────
@app.get("/documents", response_model=list[DocumentInfoResponse], tags=["Documents"])
def list_documents():
    registry = load_registry()
    docs = list(registry.values())
    docs.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
    return docs


@app.get("/documents/{doc_id}", response_model=DocumentInfoResponse, tags=["Documents"])
def get_document(doc_id: str):
    return get_doc_metadata(doc_id)


@app.delete("/documents/{doc_id}", tags=["Documents"])
def delete_document(
    doc_id: str,
    _key: dict = Depends(get_current_user),
):
    registry = load_registry()
    if doc_id not in registry:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    meta = registry[doc_id]
    for path in [meta.get("upload_path"), meta.get("index_path"), meta.get("chunks_path")]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                logger.error(f"Failed to delete {path}: {e}")
    del registry[doc_id]
    save_registry(registry)
    with _vs_lock:
        loaded_vector_stores.pop(doc_id, None)
    logger.info(f"Deleted document doc_id={doc_id}")
    return {"message": f"Document '{doc_id}' deleted successfully."}


# ── Agent Inspection Endpoints ────────────────────────────────
@app.post("/retrieve-only", response_model=RetrieveOnlyResponse, tags=["Agents"])
@limiter.limit("30/minute")
def retrieve_only_endpoint(
    request: Request,
    body: RetrieveOnlyRequest,
    _key: dict = Depends(get_current_user),
):
    validate_query(body.query)
    vs = get_vector_store_for_doc(body.doc_id)
    try:
        rewritten = query_rewriter(body.query)
        retrieved = retrieve(rewritten, embedding_model, vs, top_k=body.top_k)
        return {
            "original_query": body.query,
            "rewritten_query": rewritten,
            "retrieved_chunks": [
                {"chunk": r["chunk"], "score": r["score"], "index": r["index"]} for r in retrieved
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/plan", response_model=PlanResponse, tags=["Agents"])
@limiter.limit("30/minute")
def plan_query(
    request: Request,
    body: PlanRequest,
    _key: dict = Depends(get_current_user),
):
    validate_query(body.query)
    try:
        return {"query": body.query, "sub_queries": planner_agent(body.query)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rewrite", response_model=RewriteResponse, tags=["Agents"])
@limiter.limit("30/minute")
def rewrite_query_endpoint(
    request: Request,
    body: RewriteRequest,
    _key: dict = Depends(get_current_user),
):
    validate_query(body.query)
    try:
        return {"query": body.query, "rewritten_query": query_rewriter(body.query)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Reasoning Telemetry ───────────────────────────────────────
from observability.storage.db import get_reasoning_chain_details, get_reasoning_tree_details


@app.get("/reasoning/cot/{session_id}", tags=["Reasoning"])
def get_reasoning_cot(session_id: str):
    return get_reasoning_chain_details(session_id)


@app.get("/reasoning/chain/{session_id}", tags=["Reasoning"])
def get_reasoning_chain(session_id: str):
    return get_reasoning_chain_details(session_id)


@app.get("/reasoning/tot/{session_id}", tags=["Reasoning"])
def get_reasoning_tot(session_id: str):
    return get_reasoning_tree_details(session_id)


@app.get("/reasoning/tree/{session_id}", tags=["Reasoning"])
def get_reasoning_tree(session_id: str):
    return get_reasoning_tree_details(session_id)


# ── OCR Upload Endpoint ───────────────────────────────────────
@app.post("/upload-doc-ocr", response_model=UploadDocResponse, tags=["Documents"])
@limiter.limit("10/hour")
async def upload_doc_ocr(
    request: Request,
    file: UploadFile = File(...),
    _key: dict = Depends(get_current_user),
):
    """Upload a scanned PDF — uses OCR (Tesseract/Unstructured) to extract text."""
    filename = safe_filename(file.filename or "scan.pdf")
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="OCR mode only supports PDF files.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413, detail=f"File too large. Maximum is {MAX_FILE_SIZE_MB}MB."
        )

    doc_id = uuid.uuid4().hex[:8]
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{filename}")
    with open(file_path, "wb") as f:
        f.write(content)

    # Try OCR extraction
    try:
        from rag.ingestion import load_pdf_with_ocr

        text = load_pdf_with_ocr(file_path)
    except ImportError:
        text = ""
        logger.warning("OCR dependencies not installed. Falling back to pypdf.")
        try:
            from rag.ingestion import load_pdf

            text = load_pdf(file_path)
        except Exception as e:
            os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Failed to extract text: {e!s}")
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"OCR extraction failed: {e!s}")

    if not text.strip():
        os.remove(file_path)
        raise HTTPException(
            status_code=400, detail="OCR produced no readable text. Is this a valid scanned PDF?"
        )

    chunk_size, overlap = 6, 2
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    embeddings = embedding_model.embed_texts(chunks)

    vs = VectorStore()
    vs.build_index(embeddings, chunks)
    index_path = os.path.join(INDEX_DIR, f"{doc_id}.index")
    chunks_path = os.path.join(INDEX_DIR, f"{doc_id}_chunks.pkl")
    vs.save(index_path, chunks_path)
    with _vs_lock:
        loaded_vector_stores[doc_id] = vs

    registry = load_registry()
    registry[doc_id] = {
        "doc_id": doc_id,
        "file_name": filename,
        "uploaded_at": datetime.utcnow().isoformat() + "Z",
        "num_chunks": len(chunks),
        "upload_path": file_path,
        "index_path": index_path,
        "chunks_path": chunks_path,
        "chunk_size": chunk_size,
        "overlap": overlap,
        "embedding_model": "all-MiniLM-L6-v2",
        "ocr_used": True,
    }
    save_registry(registry)

    logger.info(f"OCR-indexed '{filename}' → doc_id={doc_id}, chunks={len(chunks)}")
    return {
        "message": "OCR document indexed successfully",
        "doc_id": doc_id,
        "file_name": filename,
        "num_chunks": len(chunks),
    }
