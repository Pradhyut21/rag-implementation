from typing import Dict, Any, List
from observability.storage.db import get_db_connection

def get_analytics() -> Dict[str, Any]:
    """
    Computes advanced analytics for the observability dashboard.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    analytics = {
        "most_active_agent": "None",
        "slowest_agent": "None",
        "most_frequent_errors": [],
        "highest_token_usage": [],
        "avg_workflow_duration": 0.0,
        "avg_retrieval_count": 0.0,
        "avg_iterations": 0.0,
        "longest_session": None
    }
    
    try:
        # 1. Most active agent (highest span count, ignoring llm_generate)
        cursor.execute("""
            SELECT name, COUNT(*) as cnt 
            FROM spans 
            WHERE name != 'llm_generate'
            GROUP BY name 
            ORDER BY cnt DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            analytics["most_active_agent"] = row["name"].replace("_", " ").title()
            
        # 2. Slowest agent (highest avg latency, ignoring llm_generate or workflow itself)
        cursor.execute("""
            SELECT name, AVG(latency) as avg_lat
            FROM spans
            WHERE name != 'llm_generate'
            GROUP BY name
            ORDER BY avg_lat DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            analytics["slowest_agent"] = row["name"].replace("_", " ").title()
            
        # 3. Most frequent errors
        cursor.execute("""
            SELECT error_type, message, COUNT(*) as cnt
            FROM errors
            GROUP BY error_type, message
            ORDER BY cnt DESC
            LIMIT 5
        """)
        analytics["most_frequent_errors"] = [
            {"type": r["error_type"], "message": r["message"], "count": r["cnt"]}
            for r in cursor.fetchall()
        ]
        
        # 4. Highest token usage sessions
        cursor.execute("""
            SELECT session_id, query, total_tokens, estimated_cost
            FROM sessions
            ORDER BY total_tokens DESC
            LIMIT 5
        """)
        analytics["highest_token_usage"] = [
            {
                "session_id": r["session_id"],
                "query": r["query"][:60] + "..." if len(r["query"]) > 60 else r["query"],
                "total_tokens": r["total_tokens"],
                "estimated_cost": round(r["estimated_cost"], 5)
            }
            for r in cursor.fetchall()
        ]
        
        # 5. Average workflow duration
        cursor.execute("SELECT AVG(total_latency) FROM sessions")
        analytics["avg_workflow_duration"] = round(cursor.fetchone()[0] or 0.0, 3)
        
        # 6. Average retrieval count (count retrievals per session)
        cursor.execute("""
            SELECT AVG(cnt) FROM (
                SELECT session_id, COUNT(*) as cnt
                FROM spans
                WHERE name = 'retriever'
                GROUP BY session_id
            )
        """)
        analytics["avg_retrieval_count"] = round(cursor.fetchone()[0] or 0.0, 2)
        
        # 7. Average iterations
        cursor.execute("SELECT AVG(iterations_count) FROM sessions")
        analytics["avg_iterations"] = round(cursor.fetchone()[0] or 0.0, 2)
        
        # 8. Longest session
        cursor.execute("""
            SELECT session_id, query, total_latency, timestamp
            FROM sessions
            ORDER BY total_latency DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            analytics["longest_session"] = {
                "session_id": row["session_id"],
                "query": row["query"][:60] + "..." if len(row["query"]) > 60 else row["query"],
                "latency": round(row["total_latency"], 3),
                "timestamp": row["timestamp"]
            }
            
    except Exception as e:
        import logging
        logging.getLogger("observability.analytics").error(f"Error compiling analytics: {e}")
    finally:
        conn.close()
        
    return analytics
