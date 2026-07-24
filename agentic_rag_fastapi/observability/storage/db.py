import json
import logging
import os
import sqlite3
from typing import Any

logger = logging.getLogger("observability.db")

DB_PATH = "data/observability.db"


def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initializes the SQLite tables for Observability.
    """
    logger.info("Initializing Observability SQLite database...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            correlation_id TEXT,
            workflow_id TEXT,
            query TEXT,
            answer TEXT,
            status TEXT,
            error_message TEXT,
            stack_trace TEXT,
            timestamp TEXT,
            total_latency REAL,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            estimated_cost REAL DEFAULT 0.0,
            iterations_count INTEGER DEFAULT 0,
            doc_id TEXT
        )
    """)

    # 2. Spans / Traces table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS spans (
            span_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            request_id TEXT NOT NULL,
            correlation_id TEXT,
            workflow_id TEXT,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            inputs TEXT,
            outputs TEXT,
            error TEXT,
            latency REAL,
            timestamp TEXT,
            iteration INTEGER DEFAULT 0,
            extra_data TEXT
        )
    """)

    # 3. Events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            session_id TEXT,
            request_id TEXT,
            name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            extra_data TEXT
        )
    """)

    # 4. Errors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS errors (
            error_id TEXT PRIMARY KEY,
            session_id TEXT,
            request_id TEXT,
            error_type TEXT NOT NULL,
            message TEXT NOT NULL,
            stack_trace TEXT,
            timestamp TEXT NOT NULL,
            retry_count INTEGER DEFAULT 0
        )
    """)

    # 5. Reasoning chains table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reasoning_chains (
            session_id TEXT PRIMARY KEY,
            query TEXT,
            timestamp TEXT
        )
    """)

    # 6. Reasoning stages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reasoning_stages (
            stage_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            stage_index INTEGER NOT NULL,
            stage_name TEXT NOT NULL,
            input_data TEXT,
            output_summary TEXT,
            execution_time REAL,
            status TEXT,
            timestamp TEXT
        )
    """)

    # 7. Reasoning trees table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reasoning_trees (
            session_id TEXT PRIMARY KEY,
            query TEXT,
            timestamp TEXT,
            decision_latency REAL
        )
    """)

    # 8. Reasoning branches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reasoning_branches (
            branch_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            branch_name TEXT,
            retrieval_query TEXT,
            rewritten_query TEXT,
            expected_evidence TEXT,
            status TEXT
        )
    """)

    # 9. Branch scores table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS branch_scores (
            branch_id TEXT PRIMARY KEY,
            retrieval_similarity REAL,
            coverage REAL,
            completeness REAL,
            evidence_quality REAL,
            confidence REAL,
            final_score REAL
        )
    """)

    # 10. Winning branch table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS winning_branches (
            session_id TEXT PRIMARY KEY,
            branch_id TEXT NOT NULL,
            score REAL
        )
    """)

    # 11. Branch evaluations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS branch_evaluations (
            branch_id TEXT PRIMARY KEY,
            evaluation_details TEXT,
            score REAL
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Observability database initialized successfully.")


def save_session(session_data: dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO sessions (
                session_id, request_id, correlation_id, workflow_id,
                query, answer, status, error_message, stack_trace,
                timestamp, total_latency, prompt_tokens, completion_tokens,
                total_tokens, estimated_cost, iterations_count, doc_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_data.get("session_id"),
                session_data.get("request_id"),
                session_data.get("correlation_id"),
                session_data.get("workflow_id"),
                session_data.get("query"),
                session_data.get("answer"),
                session_data.get("status"),
                session_data.get("error_message"),
                session_data.get("stack_trace"),
                session_data.get("timestamp"),
                session_data.get("total_latency"),
                session_data.get("prompt_tokens", 0),
                session_data.get("completion_tokens", 0),
                session_data.get("total_tokens", 0),
                session_data.get("estimated_cost", 0.0),
                session_data.get("iterations_count", 0),
                session_data.get("doc_id"),
            ),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to save session: {e}")
    finally:
        conn.close()


def save_span(span_data: dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO spans (
                span_id, session_id, request_id, correlation_id, workflow_id,
                name, status, inputs, outputs, error, latency, timestamp,
                iteration, extra_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                span_data.get("span_id"),
                span_data.get("session_id"),
                span_data.get("request_id"),
                span_data.get("correlation_id"),
                span_data.get("workflow_id"),
                span_data.get("name"),
                span_data.get("status"),
                json.dumps(span_data.get("inputs")),
                json.dumps(span_data.get("outputs")),
                span_data.get("error"),
                span_data.get("latency"),
                span_data.get("timestamp"),
                span_data.get("iteration", 0),
                json.dumps(span_data.get("extra_data", {})),
            ),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to save span: {e}")
    finally:
        conn.close()


def save_event(event_data: dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO events (
                event_id, session_id, request_id, name, timestamp, extra_data
            ) VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                event_data.get("event_id"),
                event_data.get("session_id"),
                event_data.get("request_id"),
                event_data.get("name"),
                event_data.get("timestamp"),
                json.dumps(event_data.get("extra_data", {})),
            ),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to save event: {e}")
    finally:
        conn.close()


def save_error(error_data: dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO errors (
                error_id, session_id, request_id, error_type, message,
                stack_trace, timestamp, retry_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                error_data.get("error_id"),
                error_data.get("session_id"),
                error_data.get("request_id"),
                error_data.get("error_type"),
                error_data.get("message"),
                error_data.get("stack_trace"),
                error_data.get("timestamp"),
                error_data.get("retry_count", 0),
            ),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to save error: {e}")
    finally:
        conn.close()


def save_reasoning_chain(session_id: str, query: str, timestamp: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO reasoning_chains (session_id, query, timestamp)
            VALUES (?, ?, ?)
        """,
            (session_id, query, timestamp),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to save reasoning chain: {e}")
    finally:
        conn.close()


def save_reasoning_stage(stage_data: dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO reasoning_stages (
                stage_id, session_id, stage_index, stage_name,
                input_data, output_summary, execution_time, status, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                stage_data.get("stage_id"),
                stage_data.get("session_id"),
                stage_data.get("stage_index"),
                stage_data.get("stage_name"),
                stage_data.get("input_data"),
                stage_data.get("output_summary"),
                stage_data.get("execution_time"),
                stage_data.get("status"),
                stage_data.get("timestamp"),
            ),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to save reasoning stage: {e}")
    finally:
        conn.close()


def save_reasoning_tree(session_id: str, query: str, timestamp: str, decision_latency: float):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO reasoning_trees (session_id, query, timestamp, decision_latency)
            VALUES (?, ?, ?, ?)
        """,
            (session_id, query, timestamp, decision_latency),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to save reasoning tree: {e}")
    finally:
        conn.close()


def save_reasoning_branch(branch_data: dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO reasoning_branches (
                branch_id, session_id, branch_name, retrieval_query,
                rewritten_query, expected_evidence, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                branch_data.get("branch_id"),
                branch_data.get("session_id"),
                branch_data.get("branch_name"),
                branch_data.get("retrieval_query"),
                branch_data.get("rewritten_query"),
                branch_data.get("expected_evidence"),
                branch_data.get("status"),
            ),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to save reasoning branch: {e}")
    finally:
        conn.close()


def save_branch_score(score_data: dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO branch_scores (
                branch_id, retrieval_similarity, coverage, completeness,
                evidence_quality, confidence, final_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                score_data.get("branch_id"),
                score_data.get("retrieval_similarity"),
                score_data.get("coverage"),
                score_data.get("completeness"),
                score_data.get("evidence_quality"),
                score_data.get("confidence"),
                score_data.get("final_score"),
            ),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to save branch score: {e}")
    finally:
        conn.close()


def save_winning_branch(session_id: str, branch_id: str, score: float):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO winning_branches (session_id, branch_id, score)
            VALUES (?, ?, ?)
        """,
            (session_id, branch_id, score),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to save winning branch: {e}")
    finally:
        conn.close()


def save_branch_evaluation(branch_id: str, evaluation_details: str, score: float):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO branch_evaluations (branch_id, evaluation_details, score)
            VALUES (?, ?, ?)
        """,
            (branch_id, evaluation_details, score),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to save branch evaluation: {e}")
    finally:
        conn.close()


def get_reasoning_chain_details(session_id: str) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM reasoning_chains WHERE session_id = ?", (session_id,))
        chain = cursor.fetchone()
        if not chain:
            return {"session_id": session_id, "stages": []}

        cursor.execute(
            """
            SELECT * FROM reasoning_stages 
            WHERE session_id = ? 
            ORDER BY stage_index ASC
        """,
            (session_id,),
        )
        stages = [dict(row) for row in cursor.fetchall()]

        return {
            "session_id": session_id,
            "query": chain["query"],
            "timestamp": chain["timestamp"],
            "stages": stages,
        }
    except Exception as e:
        logger.error(f"Failed to get reasoning chain: {e}")
        return {"session_id": session_id, "stages": []}
    finally:
        conn.close()


def get_reasoning_tree_details(session_id: str) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM reasoning_trees WHERE session_id = ?", (session_id,))
        tree = cursor.fetchone()
        if not tree:
            return {"session_id": session_id, "branches": [], "winning_branch": None}

        cursor.execute("SELECT * FROM reasoning_branches WHERE session_id = ?", (session_id,))
        branches = []
        for row in cursor.fetchall():
            branch = dict(row)
            b_id = branch["branch_id"]

            # get score
            cursor.execute("SELECT * FROM branch_scores WHERE branch_id = ?", (b_id,))
            score_row = cursor.fetchone()
            branch["score"] = dict(score_row) if score_row else None

            # get evaluation
            cursor.execute("SELECT * FROM branch_evaluations WHERE branch_id = ?", (b_id,))
            eval_row = cursor.fetchone()
            branch["evaluation"] = dict(eval_row) if eval_row else None

            branches.append(branch)

        cursor.execute("SELECT * FROM winning_branches WHERE session_id = ?", (session_id,))
        winning = cursor.fetchone()
        winning_branch = dict(winning) if winning else None

        return {
            "session_id": session_id,
            "query": tree["query"],
            "timestamp": tree["timestamp"],
            "decision_latency": tree["decision_latency"],
            "branches": branches,
            "winning_branch": winning_branch,
        }
    except Exception as e:
        logger.error(f"Failed to get reasoning tree: {e}")
        return {"session_id": session_id, "branches": [], "winning_branch": None}
    finally:
        conn.close()
