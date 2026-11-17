"""
Detection rules.

A rule is a small function:   rule(db, cfg) -> list of "findings"
A finding is a dict describing a possible threat AND the evidence for it.
To add a rule: write a function, decorate it with @rule(...), add its settings
to config.DETECTION_RULES. The engine picks it up automatically.
"""
import json
from datetime import datetime, timedelta, timezone

RULES = {}  # rule_id -> (title, function)


def rule(rule_id: str, title: str):
    def decorator(fn):
        RULES[rule_id] = (title, fn)
        return fn
    return decorator


def _cutoff(cfg) -> str:
    moment = datetime.now(timezone.utc) - timedelta(minutes=cfg["window_minutes"])
    return moment.isoformat(timespec="seconds")


def _failed_login_groups(db, cfg):
    """IPs with >= threshold failed logins inside the time window."""
    return db.execute("""
        SELECT source_ip,
               COUNT(*)                         AS attempts,
               MIN(timestamp)                   AS first_seen,
               MAX(timestamp)                   AS last_seen,
               GROUP_CONCAT(id)                 AS ids,
               GROUP_CONCAT(DISTINCT username)  AS users,
               MIN(is_synthetic)                AS all_synthetic
        FROM events
        WHERE event_type = 'login' AND status = 'failed'
          AND source_ip IS NOT NULL AND source_ip != ''
          AND timestamp >= ?
        GROUP BY source_ip
        HAVING COUNT(*) >= ?""", (_cutoff(cfg), cfg["threshold"])).fetchall()


@rule("SX-001", "Repeated Failed Logins")
def repeated_failed_logins(db, cfg):
    findings = []
    for g in _failed_login_groups(db, cfg):
        ids = [int(i) for i in g["ids"].split(",")][:50]
        findings.append({
            "rule_id": "SX-001",
            "title": "Repeated Failed Logins",
            "severity": cfg["severity"],
            "source_ip": g["source_ip"],
            "trigger_timestamp": g["last_seen"],
            "description": (f"{g['attempts']} failed logins from {g['source_ip']} "
                            f"within {cfg['window_minutes']} minutes"),
            "evidence": {
                "why": (f"The rule fires when {cfg['threshold']} or more failed logins "
                        f"come from one IP within {cfg['window_minutes']} minutes. "
                        f"This IP produced {g['attempts']}."),
                "attempts": g["attempts"], "threshold": cfg["threshold"],
                "window_minutes": cfg["window_minutes"],
                "first_seen": g["first_seen"], "last_seen": g["last_seen"],
                "usernames_tried": (g["users"] or "").split(","),
                "note": "Could be a mistyped password or a script. Verify before concluding.",
            },
            "related_event_ids": ids,
            "dedup_key": f"SX-001:{g['source_ip']}",
            "is_synthetic": bool(g["all_synthetic"]),
        })
    return findings


@rule("SX-002", "Successful Login After Failures")
def success_after_failures(db, cfg):
    findings = []
    for g in _failed_login_groups(db, cfg):
        win = db.execute("""
            SELECT id, timestamp, username, is_synthetic FROM events
            WHERE event_type='login' AND status='success' AND source_ip = ?
              AND timestamp >= ? ORDER BY timestamp LIMIT 1""",
            (g["source_ip"], g["last_seen"])).fetchone()
        if not win:
            continue
        ids = [int(i) for i in g["ids"].split(",")][:50] + [win["id"]]
        findings.append({
            "rule_id": "SX-002",
            "title": "Successful Login After Failures",
            "severity": cfg["severity"],
            "source_ip": g["source_ip"],
            "trigger_timestamp": win["timestamp"],
            "description": (f"{g['source_ip']} logged in as '{win['username']}' right after "
                            f"{g['attempts']} failed attempts"),
            "evidence": {
                "why": ("A successful login from the same IP followed a burst of failed "
                        "logins. This pattern can mean a guessed password."),
                "failed_attempts": g["attempts"], "threshold": cfg["threshold"],
                "failures_last_seen": g["last_seen"],
                "success_event_id": win["id"], "success_time": win["timestamp"],
                "success_username": win["username"],
                "note": "Confirm with the account owner whether this login was expected.",
            },
            "related_event_ids": ids,
            "dedup_key": f"SX-002:{g['source_ip']}",
            "is_synthetic": bool(g["all_synthetic"] and win["is_synthetic"]),
        })
    return findings
