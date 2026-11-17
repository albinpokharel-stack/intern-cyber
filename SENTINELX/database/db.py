"""Database helpers: connections, setup, backups, health."""
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import config

log = logging.getLogger("sentinelx.db")

SCHEMA_VERSION = 1
SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def utc_now_iso() -> str:
    """Current time in UTC, e.g. 2026-11-17T10:30:00+00:00 (sorts correctly as text)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def db_session():
    """Open a connection, commit on success, roll back on error, always close."""
    conn = sqlite3.connect(config.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database() -> None:
    config.DATA_DIR.mkdir(exist_ok=True)
    config.LOG_DIR.mkdir(exist_ok=True)
    with db_session() as db:
        db.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
        if db.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0] == 0:
            db.execute("INSERT INTO schema_version VALUES (?, ?)",
                       (SCHEMA_VERSION, utc_now_iso()))
        # The Windows collector is built in Milestone 2; register it now.
        db.execute("""INSERT OR IGNORE INTO collector_status (name, status)
                      VALUES ('Windows Event Log', 'not_configured')""")
    log.info("Database ready at %s", config.DB_PATH)


def backup_database():
    """Copy the database using SQLite's safe backup API. Keeps the newest few."""
    if not config.DB_PATH.exists():
        return None
    config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = config.BACKUP_DIR / f"sentinelx_{stamp}.db"
    src = sqlite3.connect(config.DB_PATH)
    dst = sqlite3.connect(target)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    for old in sorted(config.BACKUP_DIR.glob("sentinelx_*.db"))[:-config.BACKUPS_TO_KEEP]:
        old.unlink()
    log.info("Backup created: %s", target.name)
    return target


def health_info() -> dict:
    """Small health report for the dashboard and /health endpoint."""
    info = {"db_ok": False, "db_size_kb": 0, "last_backup": None,
            "schema_version": None}
    try:
        with db_session() as db:
            info["db_ok"] = db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
            info["schema_version"] = db.execute(
                "SELECT MAX(version) FROM schema_version").fetchone()[0]
        info["db_size_kb"] = round(config.DB_PATH.stat().st_size / 1024, 1)
        backups = sorted(config.BACKUP_DIR.glob("sentinelx_*.db"))
        if backups:
            info["last_backup"] = datetime.fromtimestamp(
                backups[-1].stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
    except Exception:
        log.exception("Health check failed")
    return info
