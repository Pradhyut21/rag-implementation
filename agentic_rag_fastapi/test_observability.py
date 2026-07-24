import json

from fastapi.testclient import TestClient

# Make sure we don't start the real uvicorn server, just run tests in-process
from app import app

client = TestClient(app)


def test_observability_flow():
    print("\n==============================================")
    print("RUNNING AI OBSERVABILITY LAYER VERIFICATION")
    print("==============================================")

    # 1. Verify health check
    print("\n[Step 1] Checking backend health...")
    r = client.get("/health")
    print("GET /health status:", r.status_code)
    assert r.status_code == 200

    # 2. List documents to find a valid doc_id to query
    print("\n[Step 2] Fetching indexed documents...")
    r = client.get("/documents")
    print("GET /documents status:", r.status_code)
    assert r.status_code == 200
    docs = r.json()
    print("Available documents count:", len(docs))

    if not docs:
        print("WARNING: No documents uploaded. Skipping queries. Please upload a document first.")
        return

    doc_id = docs[0]["doc_id"]
    print(f"Using document doc_id: '{doc_id}' for query testing.")

    # 3. Perform a RAG query
    print("\n[Step 3] Executing Vanilla RAG query with tracing middleware...")
    headers = {
        "X-API-Key": "demo-rag-2026",
        "X-Correlation-ID": "test-correlation-123",
        "X-Session-ID": "test-session-456",
    }
    payload = {"query": "What is the Sufficient Context Agent role?", "doc_id": doc_id, "top_k": 3}

    # Run the query
    r = client.post("/vanilla-ask", json=payload, headers=headers)
    print("POST /vanilla-ask status:", r.status_code)
    assert r.status_code == 200

    # Verify response headers are set by ObservabilityMiddleware
    print("Outbound Response headers:")
    print("  - X-Request-ID:", r.headers.get("X-Request-ID"))
    print("  - X-Session-ID:", r.headers.get("X-Session-ID"))
    print("  - X-Correlation-ID:", r.headers.get("X-Correlation-ID"))
    print("  - X-Workflow-ID:", r.headers.get("X-Workflow-ID"))

    assert "X-Request-ID" in r.headers
    assert r.headers.get("X-Session-ID") == "test-session-456"
    assert r.headers.get("X-Correlation-ID") == "test-correlation-123"
    assert "X-Workflow-ID" in r.headers

    # 4. Check Observability Sessions list
    print("\n[Step 4] Querying /observability/sessions...")
    r_sessions = client.get("/observability/sessions")
    print("GET /observability/sessions status:", r_sessions.status_code)
    assert r_sessions.status_code == 200
    sessions_data = r_sessions.json()
    assert "sessions" in sessions_data
    print("Total recorded sessions in DB:", len(sessions_data["sessions"]))

    session_id = None
    for s in sessions_data["sessions"]:
        if s["session_id"] == "test-session-456":
            session_id = s["session_id"]
            print("Found our test session record in the SQLite database!")
            print("  - Query:", s["query"])
            print("  - Answer (preview):", (s["answer"][:100] + "...") if s["answer"] else "None")
            print("  - Tokens:", s["total_tokens"])
            print("  - Cost:", s["estimated_cost"])
            break

    assert session_id is not None, "Test session was not written to DB"

    # 5. Check Trace Spans list
    print("\n[Step 5] Querying /observability/traces...")
    r_traces = client.get("/observability/traces")
    print("GET /observability/traces status:", r_traces.status_code)
    assert r_traces.status_code == 200
    traces_data = r_traces.json()
    assert "traces" in traces_data
    print(f"Total spans recorded in DB: {len(traces_data['traces'])}")

    # 6. Check Metrics Endpoint
    print("\n[Step 6] Querying /observability/metrics...")
    r_metrics = client.get("/observability/metrics")
    print("GET /observability/metrics status:", r_metrics.status_code)
    assert r_metrics.status_code == 200
    metrics_data = r_metrics.json()
    print("Performance Metrics Payload:")
    print(json.dumps(metrics_data, indent=2))

    # 7. Check Dashboard Summary
    print("\n[Step 7] Querying /observability/dashboard...")
    r_dash = client.get("/observability/dashboard")
    print("GET /observability/dashboard status:", r_dash.status_code)
    assert r_dash.status_code == 200
    dash_data = r_dash.json()
    assert "metrics" in dash_data
    assert "analytics" in dash_data
    print("Dashboard data successfully loaded.")

    # 8. Check Replay Endpoint
    print(f"\n[Step 8] Querying /observability/replay/{session_id}...")
    r_replay = client.get(f"/observability/replay/{session_id}")
    print("GET /observability/replay status:", r_replay.status_code)
    assert r_replay.status_code == 200
    replay_data = r_replay.json()
    assert "session" in replay_data
    assert "spans" in replay_data
    print(f"Replay data retrieved. Chronological spans in trace: {len(replay_data['spans'])}")
    for span in replay_data["spans"]:
        print(
            f"  -> Span: name='{span['name']}' status='{span['status']}' latency={span['latency']:.3f}s"
        )

    print("\n==============================================")
    print("SUCCESS: ALL OBSERVABILITY CHECKS PASSED!")
    print("==============================================")


if __name__ == "__main__":
    test_observability_flow()
