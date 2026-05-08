import sqlite3
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parents[2]
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "blackcore_memory.db"


def init_watch_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS watch_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT NOT NULL UNIQUE,
            target_type TEXT,
            last_risk_score INTEGER DEFAULT 0,
            last_findings_count INTEGER DEFAULT 0,
            last_report_id INTEGER,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def add_watch_target(target, target_type="unknown"):
    init_watch_db()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO watch_targets
            (target, target_type, status, created_at, updated_at)
            VALUES (?, ?, 'active', ?, ?)
            """,
            (target, target_type, now, now)
        )

        conn.commit()

        return {
            "ok": True,
            "message": "Alvo adicionado ao monitoramento.",
        }

    except sqlite3.IntegrityError:
        return {
            "ok": False,
            "message": "Este alvo já está sendo monitorado.",
        }

    finally:
        conn.close()


def list_watch_targets(include_inactive=True):
    init_watch_db()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if include_inactive:
        cur.execute(
            """
            SELECT id, target, target_type, last_risk_score, last_findings_count,
                   last_report_id, status, created_at, updated_at
            FROM watch_targets
            ORDER BY id DESC
            """
        )
    else:
        cur.execute(
            """
            SELECT id, target, target_type, last_risk_score, last_findings_count,
                   last_report_id, status, created_at, updated_at
            FROM watch_targets
            WHERE status = 'active'
            ORDER BY id DESC
            """
        )

    rows = cur.fetchall()
    conn.close()

    return rows


def remove_watch_target(target_id):
    init_watch_db()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE watch_targets
        SET status = 'inactive', updated_at = ?
        WHERE id = ?
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            target_id,
        )
    )

    conn.commit()
    affected = cur.rowcount
    conn.close()

    return affected > 0


def update_watch_snapshot(target, risk_score, findings_count, report_id=None):
    init_watch_db()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE watch_targets
        SET last_risk_score = ?,
            last_findings_count = ?,
            last_report_id = ?,
            updated_at = ?
        WHERE target = ?
        """,
        (
            risk_score,
            findings_count,
            report_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            target,
        )
    )

    conn.commit()
    conn.close()


def get_last_report_id_by_query(query):
    init_watch_db()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id
        FROM intelligence_reports
        WHERE query = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (query,)
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return row[0]