"""Everything that reads or writes the `events` table."""
import ipaddress
from datetime import datetime, timedelta, timezone

from database.db import utc_now_iso


def _clean_ip(value):
    """Return a valid IP string or None. Rejects anything that is not an IP."""
    if not value:
        return None
    return str(ipaddress.ip_address(str(value).strip()))  # raises ValueError if bad


def add_event(db, *, source, event_type, status, source_ip=None, username=None,
              details="", severity="info", is_synthetic=False,
              timestamp=None, event_uid=None):
    """Insert one event. Returns its id, or None if event_uid already existed."""
    cur = db.execute(
        """INSERT OR IGNORE INTO events
           (timestamp, source, source_ip, username, event_type, status,
            severity, details, is_synthetic, event_uid)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (timestamp or utc_now_iso(), str(source)[:60], _clean_ip(source_ip),
         (username or "")[:80], str(event_type)[:40], str(status)[:20],
         severity, (details or "")[:500], 1 if is_synthetic else 0, event_uid),
    )
    return cur.lastrowid if cur.rowcount else None


def seed_samples(db):
    """Fill an EMPTY database with clearly-labelled synthetic demo events."""
    if db.execute("SELECT COUNT(*) FROM events").fetchone()[0]:
        return
    now = datetime.now(timezone.utc)

    def ts(minutes_ago, extra_seconds=0):
        return (now - timedelta(minutes=minutes_ago, seconds=-extra_seconds)).isoformat(timespec="seconds")

    for i in range(5):  # 5 failed logins, then a success from the SAME ip
        add_event(db, source="Linux", source_ip="192.168.1.25", username="admin",
                  event_type="login", status="failed", details="Incorrect password",
                  is_synthetic=True, timestamp=ts(10, i * 20))
    add_event(db, source="Linux", source_ip="192.168.1.25", username="admin",
              event_type="login", status="success", details="Successful login",
              is_synthetic=True, timestamp=ts(5))
    add_event(db, source="Windows", source_ip="192.168.1.40", username="user1",
              event_type="login", status="success", details="Successful login",
              is_synthetic=True, timestamp=ts(3))
    add_event(db, source="Firewall", source_ip="10.0.0.15", username="unknown",
              event_type="connection", status="blocked", details="Connection blocked",
              is_synthetic=True, timestamp=ts(2))
    add_event(db, source="Linux", source_ip="192.168.1.30", username="analyst",
              event_type="login", status="success", details="Successful login",
              is_synthetic=True, timestamp=ts(1))


def generate_failed_login_burst(db, ip="203.0.113.50", count=6):
    """Synthetic test data (203.0.113.x is a reserved documentation range)."""
    now = datetime.now(timezone.utc)
    for i in range(count):
        add_event(db, source="Linux", source_ip=ip, username="testuser",
                  event_type="login", status="failed",
                  details="Synthetic failed login test", is_synthetic=True,
                  timestamp=(now - timedelta(seconds=count - i)).isoformat(timespec="seconds"))


# ---- Read-only queries for the dashboard -----------------------------------
def overview(db) -> dict:
    row = db.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN event_type='login' AND status='failed' THEN 1 ELSE 0 END) AS failed,
               COUNT(DISTINCT source) AS sources,
               SUM(is_synthetic) AS synthetic,
               MAX(timestamp) AS last_event
        FROM events""").fetchone()
    total = row["total"] or 0
    synthetic = row["synthetic"] or 0
    return {"total": total, "failed_logins": row["failed"] or 0,
            "sources": row["sources"] or 0, "synthetic": synthetic,
            "real": total - synthetic, "last_event": row["last_event"]}


def by_source(db):
    return db.execute("""SELECT source AS label, COUNT(*) AS n FROM events
                         GROUP BY source ORDER BY n DESC LIMIT 8""").fetchall()


def by_status(db):
    return db.execute("""SELECT status AS label, COUNT(*) AS n FROM events
                         GROUP BY status ORDER BY n DESC""").fetchall()


def top_ips(db, limit=6):
    return db.execute("""SELECT source_ip AS label, COUNT(*) AS n FROM events
                         WHERE source_ip IS NOT NULL AND source_ip != ''
                         GROUP BY source_ip ORDER BY n DESC LIMIT ?""", (limit,)).fetchall()


def hourly_timeline(db, hours=24):
    """Return [(hour_label, count)] for the last `hours` hours (UTC), oldest first."""
    now = datetime.now(timezone.utc)
    buckets = [(now - timedelta(hours=h)).strftime("%Y-%m-%dT%H") for h in range(hours - 1, -1, -1)]
    rows = db.execute("""SELECT substr(timestamp,1,13) AS hr, COUNT(*) AS n FROM events
                         WHERE timestamp >= ? GROUP BY hr""", (buckets[0],)).fetchall()
    counts = {r["hr"]: r["n"] for r in rows}
    return [(b[-2:], counts.get(b, 0)) for b in buckets]


def recent(db, limit=15, query=""):
    query = (query or "").strip()[:100]
    if query:
        like = f"%{query}%"
        return db.execute("""SELECT * FROM events
                             WHERE source LIKE ? OR source_ip LIKE ? OR username LIKE ?
                                OR event_type LIKE ? OR status LIKE ? OR details LIKE ?
                             ORDER BY id DESC LIMIT ?""",
                          (like,) * 6 + (limit,)).fetchall()
    return db.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()


def all_events(db):
    return db.execute("SELECT * FROM events ORDER BY id DESC").fetchall()
