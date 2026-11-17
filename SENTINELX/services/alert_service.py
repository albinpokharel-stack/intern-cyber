"""Everything that reads or writes the `alerts` table."""
import json
import logging

log = logging.getLogger("sentinelx.alerts")

ACTIVE = ("open", "investigating")


def create_alert_if_new(db, finding: dict):
    """Insert an alert unless an ACTIVE alert with the same dedup_key exists.

    Returns the new alert id, or None if it was a duplicate.
    """
    exists = db.execute(
        "SELECT id FROM alerts WHERE dedup_key = ? AND status IN ('open','investigating')",
        (finding["dedup_key"],)).fetchone()
    if exists:
        return None
    cur = db.execute(
        """INSERT INTO alerts (rule_id, title, severity, description, source_ip,
                               trigger_timestamp, evidence, related_event_ids,
                               dedup_key, is_synthetic)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (finding["rule_id"], finding["title"], finding["severity"],
         finding["description"], finding.get("source_ip"),
         finding["trigger_timestamp"], json.dumps(finding["evidence"]),
         json.dumps(finding["related_event_ids"]), finding["dedup_key"],
         1 if finding.get("is_synthetic") else 0))
    log.warning("ALERT %s %s: %s", finding["rule_id"], finding["severity"], finding["description"])
    return cur.lastrowid


def counts_by_severity(db) -> dict:
    rows = db.execute("""SELECT severity, COUNT(*) AS n FROM alerts
                         WHERE status IN ('open','investigating') GROUP BY severity""").fetchall()
    return {r["severity"]: r["n"] for r in rows}


def unresolved_count(db) -> int:
    return db.execute("""SELECT COUNT(*) FROM alerts
                         WHERE status IN ('open','investigating')""").fetchone()[0]


def by_rule(db):
    return db.execute("""SELECT rule_id || ' · ' || title AS label, COUNT(*) AS n
                         FROM alerts GROUP BY rule_id, title ORDER BY n DESC""").fetchall()


def latest(db, limit=8):
    return db.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()


def collectors(db):
    return db.execute("SELECT * FROM collector_status ORDER BY name").fetchall()
