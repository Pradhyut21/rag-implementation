import json
from typing import Dict, Any, List
from observability.storage.db import get_db_connection

def get_session_replay_data(session_id: str) -> Dict[str, Any]:
    """
    Retrieves all records associated with a session ID to drive step-by-step replays.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    replay_data = {
        "session": None,
        "spans": [],
        "events": [],
        "errors": []
    }
    
    try:
        # 1. Fetch Session Metadata
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        session_row = cursor.fetchone()
        if not session_row:
            return replay_data
            
        replay_data["session"] = dict(session_row)
        
        # 2. Fetch Spans (sorted by timestamp/span_id)
        cursor.execute("""
            SELECT * FROM spans 
            WHERE session_id = ? 
            ORDER BY timestamp ASC, span_id ASC
        """, (session_id,))
        
        for r in cursor.fetchall():
            span = dict(r)
            # Parse JSON serialized values
            try:
                span["inputs"] = json.loads(span["inputs"]) if span["inputs"] else {}
                span["outputs"] = json.loads(span["outputs"]) if span["outputs"] else {}
                span["extra_data"] = json.loads(span["extra_data"]) if span["extra_data"] else {}
            except Exception:
                pass
            replay_data["spans"].append(span)
            
        # 3. Fetch Events
        cursor.execute("SELECT * FROM events WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
        for r in cursor.fetchall():
            ev = dict(r)
            try:
                ev["extra_data"] = json.loads(ev["extra_data"]) if ev["extra_data"] else {}
            except Exception:
                pass
            replay_data["events"].append(ev)
            
        # 4. Fetch Errors
        cursor.execute("SELECT * FROM errors WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
        for r in cursor.fetchall():
            err = dict(r)
            replay_data["errors"].append(err)
            
    except Exception as e:
        import logging
        logging.getLogger("observability.replay").error(f"Error fetching replay data: {e}")
    finally:
        conn.close()
        
    return replay_data
