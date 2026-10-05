import sqlite3
import json
import shutil
from datetime import datetime, date
from .config import CACHE_DIR, DB_PATH, ARCHIVE_DIR


def _migrate_db_if_needed():
    old_db = CACHE_DIR / "state.db"
    if old_db.exists() and not DB_PATH.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(old_db), str(DB_PATH))


def get_conn():
    _migrate_db_if_needed()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _init_schema(conn)
    return conn


def _init_schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            event_type TEXT NOT NULL,
            summary TEXT,
            details TEXT,
            count INTEGER DEFAULT 0,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS morning_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date DATE UNIQUE,
            raw_data TEXT,
            llm_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS state (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)


def get_last_seen(key):
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None


def set_last_seen(key, value):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
            (key, str(value)),
        )


def save_report(raw_data, llm_summary=""):
    today = date.today().isoformat()
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO morning_reports
               (report_date, raw_data, llm_summary)
               VALUES (?, ?, ?)""",
            (today, json.dumps(raw_data, default=str), llm_summary),
        )
    archive_path = ARCHIVE_DIR / f"report-{today}.json"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(json.dumps(raw_data, indent=2, default=str))


def get_latest_report():
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM morning_reports ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            return {
                "report_date": row["report_date"],
                "raw_data": json.loads(row["raw_data"]),
                "llm_summary": row["llm_summary"],
                "created_at": row["created_at"],
            }
        return None


def save_collapse_state(key: str, expanded: bool):
    set_last_seen(f"collapse_{key}", "1" if expanded else "0")


def load_collapse_state(key: str) -> bool:
    val = get_last_seen(f"collapse_{key}")
    if val is None:
        return True
    return val == "1"
