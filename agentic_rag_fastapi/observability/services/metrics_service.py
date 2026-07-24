from typing import Any

from observability.storage.db import get_db_connection


def get_performance_metrics() -> dict[str, Any]:
    """
    Computes performance metrics by querying the SQLite database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    metrics = {
        "total_requests": 0,
        "avg_latency": 0.0,
        "avg_tokens": 0.0,
        "avg_retrieval_time": 0.0,
        "avg_planner_time": 0.0,
        "avg_rewrite_time": 0.0,
        "avg_context_eval_time": 0.0,
        "avg_synthesis_time": 0.0,
        "avg_iterations": 0.0,
        "success_rate": 0.0,
        "failure_rate": 0.0,
        "retry_count": 0,
    }

    try:
        # 1. Session aggregates
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(total_latency) as avg_lat,
                AVG(total_tokens) as avg_tok,
                AVG(iterations_count) as avg_iter,
                SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failure
            FROM sessions
        """)
        row = cursor.fetchone()
        if row and row["total"] > 0:
            total = row["total"]
            metrics["total_requests"] = total
            metrics["avg_latency"] = round(row["avg_lat"] or 0.0, 3)
            metrics["avg_tokens"] = round(row["avg_tok"] or 0.0, 1)
            metrics["avg_iterations"] = round(row["avg_iter"] or 0.0, 2)
            metrics["success_rate"] = round((row["success"] or 0) * 100.0 / total, 2)
            metrics["failure_rate"] = round((row["failure"] or 0) * 100.0 / total, 2)

        # 2. Span average latencies per agent
        cursor.execute("SELECT AVG(latency) FROM spans WHERE name = 'retriever'")
        metrics["avg_retrieval_time"] = round(cursor.fetchone()[0] or 0.0, 3)

        cursor.execute("SELECT AVG(latency) FROM spans WHERE name = 'planner'")
        metrics["avg_planner_time"] = round(cursor.fetchone()[0] or 0.0, 3)

        cursor.execute("SELECT AVG(latency) FROM spans WHERE name = 'rewriter'")
        metrics["avg_rewrite_time"] = round(cursor.fetchone()[0] or 0.0, 3)

        cursor.execute("SELECT AVG(latency) FROM spans WHERE name = 'sufficient_context'")
        metrics["avg_context_eval_time"] = round(cursor.fetchone()[0] or 0.0, 3)

        cursor.execute("SELECT AVG(latency) FROM spans WHERE name = 'synthesis'")
        metrics["avg_synthesis_time"] = round(cursor.fetchone()[0] or 0.0, 3)

        # 3. Retry counts (errors that mention retry, or total errors if they occur)
        cursor.execute(
            "SELECT COUNT(*) FROM errors WHERE message LIKE '%retry%' OR error_type = 'Retry'"
        )
        metrics["retry_count"] = cursor.fetchone()[0] or 0

    except Exception as e:
        import logging

        logging.getLogger("observability.metrics").error(f"Error compiling metrics: {e}")
    finally:
        conn.close()

    return metrics
