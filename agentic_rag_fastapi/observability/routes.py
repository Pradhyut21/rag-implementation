import json

from fastapi import APIRouter, HTTPException, Query

from observability.services.analytics_service import get_analytics
from observability.services.metrics_service import get_performance_metrics
from observability.services.replay_service import get_session_replay_data
from observability.storage.db import get_db_connection

router = APIRouter(prefix="/observability", tags=["Observability"])


@router.get("/sessions")
def get_sessions(
    limit: int = Query(50, ge=1), offset: int = Query(0, ge=0), status: str | None = None
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if status:
            cursor.execute(
                """
                SELECT * FROM sessions 
                WHERE status = ? 
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            """,
                (status, limit, offset),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM sessions 
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            """,
                (limit, offset),
            )

        sessions = [dict(row) for row in cursor.fetchall()]
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/session/{session_id}")
def get_session_details(session_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        session = cursor.fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get spans
        cursor.execute(
            "SELECT * FROM spans WHERE session_id = ? ORDER BY timestamp ASC", (session_id,)
        )
        spans = []
        for r in cursor.fetchall():
            span = dict(r)
            try:
                span["inputs"] = json.loads(span["inputs"]) if span["inputs"] else {}
                span["outputs"] = json.loads(span["outputs"]) if span["outputs"] else {}
                span["extra_data"] = json.loads(span["extra_data"]) if span["extra_data"] else {}
            except Exception:
                pass
            spans.append(span)

        # Get events
        cursor.execute(
            "SELECT * FROM events WHERE session_id = ? ORDER BY timestamp ASC", (session_id,)
        )
        events = []
        for r in cursor.fetchall():
            ev = dict(r)
            try:
                ev["extra_data"] = json.loads(ev["extra_data"]) if ev["extra_data"] else {}
            except Exception:
                pass
            events.append(ev)

        # Get errors
        cursor.execute(
            "SELECT * FROM errors WHERE session_id = ? ORDER BY timestamp ASC", (session_id,)
        )
        errors = [dict(row) for row in cursor.fetchall()]

        return {"session": dict(session), "spans": spans, "events": events, "errors": errors}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/traces")
def get_traces(limit: int = 50, offset: int = 0):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT * FROM spans 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        """,
            (limit, offset),
        )
        spans = []
        for r in cursor.fetchall():
            span = dict(r)
            try:
                span["inputs"] = json.loads(span["inputs"]) if span["inputs"] else {}
                span["outputs"] = json.loads(span["outputs"]) if span["outputs"] else {}
                span["extra_data"] = json.loads(span["extra_data"]) if span["extra_data"] else {}
            except Exception:
                pass
            spans.append(span)
        return {"traces": spans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/events")
def get_events(limit: int = 100, offset: int = 0):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT * FROM events 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        """,
            (limit, offset),
        )
        events = []
        for r in cursor.fetchall():
            ev = dict(r)
            try:
                ev["extra_data"] = json.loads(ev["extra_data"]) if ev["extra_data"] else {}
            except Exception:
                pass
            events.append(ev)
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/errors")
def get_errors(limit: int = 50, offset: int = 0):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT * FROM errors 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        """,
            (limit, offset),
        )
        errors = [dict(row) for row in cursor.fetchall()]
        return {"errors": errors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/metrics")
def get_metrics():
    try:
        return get_performance_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tokens")
def get_tokens():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                SUM(prompt_tokens) as prompt,
                SUM(completion_tokens) as completion,
                SUM(total_tokens) as total,
                SUM(estimated_cost) as cost
            FROM sessions
        """)
        totals = dict(cursor.fetchone())

        # Token usage by sessions
        cursor.execute("""
            SELECT session_id, query, timestamp, total_tokens, estimated_cost
            FROM sessions
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        sessions = [dict(row) for row in cursor.fetchall()]

        return {
            "totals": {
                "prompt_tokens": totals.get("prompt") or 0,
                "completion_tokens": totals.get("completion") or 0,
                "total_tokens": totals.get("total") or 0,
                "estimated_cost": round(totals.get("cost") or 0.0, 5),
            },
            "recent_sessions": sessions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/latency")
def get_latency_breakdown():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Averages per step
        cursor.execute("SELECT AVG(latency) FROM spans WHERE name = 'planner'")
        avg_planner = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT AVG(latency) FROM spans WHERE name = 'rewriter'")
        avg_rewriter = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT AVG(latency) FROM spans WHERE name = 'retriever'")
        avg_retriever = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT AVG(latency) FROM spans WHERE name = 'sufficient_context'")
        avg_context = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT AVG(latency) FROM spans WHERE name = 'synthesis'")
        avg_synthesis = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT AVG(total_latency) FROM sessions")
        avg_workflow = cursor.fetchone()[0] or 0.0

        # Recent 30 runs latency distribution
        cursor.execute("""
            SELECT session_id, query, total_latency, timestamp
            FROM sessions
            ORDER BY timestamp DESC
            LIMIT 30
        """)
        recent_latencies = [dict(row) for row in cursor.fetchall()]

        return {
            "breakdown": {
                "planner": round(avg_planner, 3),
                "rewriter": round(avg_rewriter, 3),
                "retriever": round(avg_retriever, 3),
                "context_eval": round(avg_context, 3),
                "synthesis": round(avg_synthesis, 3),
                "total_workflow": round(avg_workflow, 3),
            },
            "recent_latencies": recent_latencies,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/replay/{session_id}")
def get_session_replay(session_id: str):
    data = get_session_replay_data(session_id)
    if not data["session"]:
        raise HTTPException(status_code=404, detail="Session not found")
    return data


@router.get("/dashboard")
def get_dashboard_summary():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Recent 5 sessions
        cursor.execute("""
            SELECT session_id, query, answer, status, total_latency, total_tokens, timestamp
            FROM sessions
            ORDER BY timestamp DESC
            LIMIT 5
        """)
        recent_sessions = [dict(row) for row in cursor.fetchall()]

        # Recent 5 errors
        cursor.execute("""
            SELECT * FROM errors
            ORDER BY timestamp DESC
            LIMIT 5
        """)
        recent_errors = [dict(row) for row in cursor.fetchall()]

        conn.close()

        metrics = get_performance_metrics()
        analytics = get_analytics()

        return {
            "metrics": metrics,
            "analytics": analytics,
            "recent_sessions": recent_sessions,
            "recent_errors": recent_errors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
