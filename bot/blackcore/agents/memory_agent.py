import sqlite3
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parents[2]
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "blackcore_memory.db"


def init_memory_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS intelligence_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            target_type TEXT,
            risk_score INTEGER,
            report_text TEXT,
            findings_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def save_intelligence_report(query, target_type, risk_score, report_text, findings_count=0):
    init_memory_db()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO intelligence_reports
        (query, target_type, risk_score, report_text, findings_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            query,
            target_type,
            risk_score,
            report_text,
            findings_count,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
    )

    conn.commit()
    conn.close()


def list_recent_reports(limit=10):
    init_memory_db()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, query, target_type, risk_score, findings_count, created_at
        FROM intelligence_reports
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = cur.fetchall()
    conn.close()

    return rows


def get_report_by_id(report_id):
    init_memory_db()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, query, target_type, risk_score, findings_count, report_text, created_at
        FROM intelligence_reports
        WHERE id = ?
        """,
        (report_id,)
    )

    row = cur.fetchone()
    conn.close()

    return row