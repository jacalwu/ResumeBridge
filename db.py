"""
SQLite database layer for persisting analysis history.
Sensitive fields (jd_text, cv_text, result) are encrypted at rest.
"""

import sqlite3
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from privacy import encrypt, safe_decrypt

DB_PATH = "analysis_history.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create the analysis_history table if it doesn't exist."""
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                role       TEXT    NOT NULL,
                mode       TEXT,
                jd_text    TEXT    NOT NULL,
                cv_text    TEXT    NOT NULL,
                result     TEXT    NOT NULL,
                created_at TEXT    NOT NULL
            )
            """
        )


def save_analysis(
    role: str,
    jd_text: str,
    cv_text: str,
    result: str,
    mode: Optional[str] = None,
) -> int:
    """Persist one analysis record. Sensitive fields are encrypted. Returns the new row id."""
    created_at = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO analysis_history (role, mode, jd_text, cv_text, result, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                role,
                mode,
                encrypt(jd_text),
                encrypt(cv_text),
                encrypt(result),
                created_at,
            ),
        )
        return cur.lastrowid


def load_history(limit: int = 20) -> List[dict]:
    """Return the most recent analyses (newest first). Sensitive fields are decrypted on read."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM analysis_history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["jd_text"] = safe_decrypt(d["jd_text"])
            d["cv_text"] = safe_decrypt(d["cv_text"])
            d["result"] = safe_decrypt(d["result"])
            result.append(d)
        return result


def delete_record(record_id: int) -> None:
    """Delete one record by id."""
    with get_conn() as conn:
        conn.execute("DELETE FROM analysis_history WHERE id = ?", (record_id,))


def purge_old_records(retention_days: int) -> int:
    """Delete records older than retention_days. Returns count of deleted rows."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM analysis_history WHERE created_at < ?",
            (cutoff,),
        )
        conn.commit()
        return cur.rowcount
