import os
import uuid
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

import nltk
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from rag.ingestion import load_document, chunk_text
from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore
from rag.retrieval import retrieve
from agents.agentic_loop import agentic_rag, vanilla_rag
from agents.planner import planner_agent
from agents.rewriter import query_rewriter
from schemas import (
    QueryRequest,
    AskResponse,
    VanillaAskResponse,
    UploadDocResponse,
    DocumentInfoResponse,
    PlanRequest,
    PlanResponse,
    RewriteRequest,
    RewriteResponse,
    RetrieveOnlyRequest,
    RetrieveOnlyResponse,
    AskDebugResponse
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("agentic_rag_api")

# Initialize AI Observability (monkey-patching)
from observability import setup_observability, ObservabilityMiddleware
from observability.routes import router as observability_router

setup_observability()

# Download punkt once
try:
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)
except Exception as e:
    logger.warning(f"NLTK download failed: {e}")

app = FastAPI(title="Agentic RAG API", version="2.0")

# Add Observability Middleware
app.add_middleware(ObservabilityMiddleware)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Observability Endpoints
app.include_router(observability_router)

UPLOAD_DIR = "data/uploads"
INDEX_DIR = "data/indexes"
DEBUG_RUNS_DIR = "data/debug_runs"
REGISTRY_PATH = os.path.join(INDEX_DIR, "registry.json")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(INDEX_DIR, exist_ok=True)
os.makedirs(DEBUG_RUNS_DIR, exist_ok=True)

# Global in-memory cache and models
embedding_model = EmbeddingModel()
loaded_vector_stores: Dict[str, VectorStore] = {}

# Registry Helper Functions
def load_registry() -> dict:
    if not os.path.exists(REGISTRY_PATH):
        return {}
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load registry: {e}")
        return {}

def save_registry(registry: dict):
    try:
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save registry: {e}")

def get_doc_metadata(doc_id: str) -> dict:
    registry = load_registry()
    if doc_id not in registry:
        logger.warning(f"Document ID {doc_id} not found in registry.")
        raise HTTPException(status_code=404, detail=f"Document ID {doc_id} not found in registry")
    return registry[doc_id]

def get_vector_store_for_doc(doc_id: str) -> VectorStore:
    # 1. check registry
    registry = load_registry()
    if doc_id not in registry:
        logger.warning(f"Lookup failed: Document ID {doc_id} not found.")
        raise HTTPException(status_code=404, detail=f"Document ID {doc_id} not found in registry")
    
    # 2. check cache
    if doc_id in loaded_vector_stores:
        return loaded_vector_stores[doc_id]
        
    # 3. load from disk
    meta = registry[doc_id]
    index_path = meta["index_path"]
    chunks_path = meta["chunks_path"]
    
    if not os.path.exists(index_path) or not os.path.exists(chunks_path):
        logger.error(f"Index or chunks files missing on disk for cached doc_id {doc_id}.")
        raise HTTPException(
            status_code=404, 
            detail=f"Index files for document ID {doc_id} not found on disk"
        )
        
    try:
        vs = VectorStore()
        vs.load(index_path, chunks_path)
        loaded_vector_stores[doc_id] = vs
        logger.info(f"Loaded and cached VectorStore for doc_id: {doc_id}")
        return vs
    except Exception as e:
        logger.error(f"Failed to load VectorStore for doc_id {doc_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to load vector store for doc_id {doc_id}: {str(e)}"
        )

# Core Endpoints
@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Enterprise Agentic RAG Platform API",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload-doc", response_model=UploadDocResponse)
async def upload_doc(file: UploadFile = File(...)):
    filename = file.filename
    if not filename.lower().endswith((".docx", ".pdf")):
        raise HTTPException(status_code=400, detail="Only .docx and .pdf files are supported")

    doc_id = uuid.uuid4().hex[:8]
    logger.info(f"Received file upload: '{filename}', assigning doc_id: '{doc_id}'")
    
    unique_name = f"{doc_id}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to save uploaded file to {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    # Load text
    try:
        text = load_document(file_path)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"Failed to extract text from {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load document: {str(e)}")

    if not text.strip():
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail="Uploaded document has no readable text")

    # Chunk
    chunk_size = 6
    overlap = 2
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail="No chunks could be created from the document")

    # Embed
    try:
        embeddings = embedding_model.embed_texts(chunks)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"Failed to generate embeddings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")

    # Build FAISS Index
    try:
        vs = VectorStore()
        vs.build_index(embeddings, chunks)
        
        index_path = os.path.join(INDEX_DIR, f"{doc_id}.index")
        chunks_path = os.path.join(INDEX_DIR, f"{doc_id}_chunks.pkl")
        vs.save(index_path, chunks_path)
        
        # Cache in memory
        loaded_vector_stores[doc_id] = vs
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"Failed to build/save FAISS index: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to build vector store index: {str(e)}")

    # Update Registry
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
        "embedding_model": "all-MiniLM-L6-v2"
    }
    save_registry(registry)

    logger.info(f"Indexed document successfully: '{filename}' ({len(chunks)} chunks), doc_id: '{doc_id}'")
    return {
        "message": "Document indexed successfully",
        "doc_id": doc_id,
        "file_name": filename,
        "num_chunks": len(chunks)
    }

@app.post("/ask", response_model=AskResponse)
def ask_question(request: QueryRequest):
    logger.info(f"Processing Agentic RAG request for doc_id: {request.doc_id}, query: '{request.query}', mode: '{request.response_mode}', reasoning_mode: '{request.reasoning_mode}'")
    vs = get_vector_store_for_doc(request.doc_id)
    
    try:
        result = agentic_rag(
            query=request.query,
            embedding_model=embedding_model,
            vector_store=vs,
            top_k=request.top_k,
            reasoning_mode=request.reasoning_mode
        )
        
        # Handle include_trace and response_mode logic
        if request.response_mode == "compact" and not request.include_trace:
            result["trace"] = None
            result["final_context"] = None
            
        return result
    except Exception as e:
        logger.exception(f"Agentic RAG failed for query: '{request.query}' on doc_id: {request.doc_id}")
        raise HTTPException(status_code=500, detail=f"Agentic RAG failed: {str(e)}")

@app.post("/vanilla-ask", response_model=VanillaAskResponse)
def vanilla_question(request: QueryRequest):
    logger.info(f"Processing Vanilla RAG request for doc_id: {request.doc_id}, query: '{request.query}'")
    vs = get_vector_store_for_doc(request.doc_id)
    
    try:
        result = vanilla_rag(
            query=request.query,
            embedding_model=embedding_model,
            vector_store=vs,
            top_k=request.top_k
        )
        return result
    except Exception as e:
        logger.exception(f"Vanilla RAG failed for query: '{request.query}' on doc_id: {request.doc_id}")
        raise HTTPException(status_code=500, detail=f"Vanilla RAG failed: {str(e)}")

# Document Management Endpoints
@app.get("/documents", response_model=List[DocumentInfoResponse])
def list_documents():
    logger.info("Retrieving all documents from registry.")
    registry = load_registry()
    return list(registry.values())

@app.get("/documents/{doc_id}", response_model=DocumentInfoResponse)
def get_document(doc_id: str):
    logger.info(f"Retrieving document details for doc_id: {doc_id}")
    return get_doc_metadata(doc_id)

@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    logger.info(f"Request to delete document doc_id: {doc_id}")
    registry = load_registry()
    if doc_id not in registry:
        logger.warning(f"Delete failed: doc_id {doc_id} not found in registry.")
        raise HTTPException(status_code=404, detail=f"Document ID {doc_id} not found in registry")
        
    meta = registry[doc_id]
    upload_path = meta.get("upload_path")
    index_path = meta.get("index_path")
    chunks_path = meta.get("chunks_path")
    
    # Delete file assets
    for path in [upload_path, index_path, chunks_path]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
                logger.info(f"Deleted file: {path}")
            except Exception as e:
                logger.error(f"Failed to delete file {path}: {e}")
                
    # Remove entry
    del registry[doc_id]
    save_registry(registry)
    
    # Clear cache
    if doc_id in loaded_vector_stores:
        del loaded_vector_stores[doc_id]
        logger.info(f"Evicted cache for doc_id: {doc_id}")
        
    logger.info(f"Document doc_id {doc_id} successfully deleted.")
    return {"message": f"Document {doc_id} deleted successfully"}

# Evaluation & Debugging Endpoints (Phase 4)
@app.post("/ask-debug", response_model=AskDebugResponse)
def ask_debug_question(request: QueryRequest):
    logger.info(f"Processing debug Agentic RAG request for doc_id: {request.doc_id}, query: '{request.query}', reasoning_mode: '{request.reasoning_mode}'")
    vs = get_vector_store_for_doc(request.doc_id)
    
    try:
        result = agentic_rag(
            query=request.query,
            embedding_model=embedding_model,
            vector_store=vs,
            top_k=request.top_k,
            reasoning_mode=request.reasoning_mode
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
            "session_id": result.get("session_id")
        }
        
        # Save exportable run log to disk (Phase 5)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{request.doc_id}.json"
        log_path = os.path.join(DEBUG_RUNS_DIR, filename)
        
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(response_data, f, indent=2)
            logger.info(f"Saved run debug log to: {log_path}")
        except Exception as log_err:
            logger.error(f"Failed to save run log to disk: {log_err}")
            
        return response_data
    except Exception as e:
        logger.exception(f"Debug Agentic RAG failed for query: '{request.query}' on doc_id: {request.doc_id}")
        raise HTTPException(status_code=500, detail=f"Agentic RAG failed: {str(e)}")

@app.post("/retrieve-only", response_model=RetrieveOnlyResponse)
def retrieve_only_endpoint(request: RetrieveOnlyRequest):
    logger.info(f"Processing Retrieve-Only request for doc_id: {request.doc_id}, query: '{request.query}'")
    vs = get_vector_store_for_doc(request.doc_id)
    
    try:
        # Run query rewriter
        rewritten = query_rewriter(request.query)
        logger.info(f"Rewritten query for retrieval: '{rewritten}'")
        
        # Retrieve chunks
        retrieved_results = retrieve(rewritten, embedding_model, vs, top_k=request.top_k)
        
        chunks_out = []
        for r in retrieved_results:
            chunks_out.append({
                "chunk": r["chunk"],
                "score": r["score"],
                "index": r["index"]
            })
            
        return {
            "original_query": request.query,
            "rewritten_query": rewritten,
            "retrieved_chunks": chunks_out
        }
    except Exception as e:
        logger.exception(f"Retrieve-Only failed for query: '{request.query}' on doc_id: {request.doc_id}")
        raise HTTPException(status_code=500, detail=f"Retrieve-Only failed: {str(e)}")

@app.post("/plan", response_model=PlanResponse)
def plan_query(request: PlanRequest):
    logger.info(f"Processing planner-only request for query: '{request.query}'")
    try:
        sub_queries = planner_agent(request.query)
        return {
            "query": request.query,
            "sub_queries": sub_queries
        }
    except Exception as e:
        logger.exception(f"Plan failed for query: '{request.query}'")
        raise HTTPException(status_code=500, detail=f"Planner failed: {str(e)}")

@app.post("/rewrite", response_model=RewriteResponse)
def rewrite_query_endpoint(request: RewriteRequest):
    logger.info(f"Processing rewriter-only request for query: '{request.query}'")
    try:
        rewritten = query_rewriter(request.query)
        return {
            "query": request.query,
            "rewritten_query": rewritten
        }
    except Exception as e:
        logger.exception(f"Rewrite failed for query: '{request.query}'")
        raise HTTPException(status_code=500, detail=f"Query rewriter failed: {str(e)}")

# Reasoning endpoints (CoT/ToT Telemetry retrieval)
from observability.storage.db import get_reasoning_chain_details, get_reasoning_tree_details

@app.get("/reasoning/cot/{session_id}")
def get_reasoning_cot(session_id: str):
    logger.info(f"Retrieving CoT details for session: {session_id}")
    return get_reasoning_chain_details(session_id)

@app.get("/reasoning/chain/{session_id}")
def get_reasoning_chain(session_id: str):
    logger.info(f"Retrieving CoT chain details for session: {session_id}")
    return get_reasoning_chain_details(session_id)

@app.get("/reasoning/tot/{session_id}")
def get_reasoning_tot(session_id: str):
    logger.info(f"Retrieving ToT details for session: {session_id}")
    return get_reasoning_tree_details(session_id)

@app.get("/reasoning/tree/{session_id}")
def get_reasoning_tree(session_id: str):
    logger.info(f"Retrieving ToT tree details for session: {session_id}")
    return get_reasoning_tree_details(session_id)
