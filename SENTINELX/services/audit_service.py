"""Audit log: a permanent record of who did what."""
from database.db import utc_now_iso


def record(db, action: str, target: str = "", details: str = "", actor: str = "local-analyst"):
    db.execute(
        "INSERT INTO audit_log (timestamp, actor, action, target, details) VALUES (?,?,?,?,?)",
        (utc_now_iso(), actor, action, target, details[:500]),
    )
