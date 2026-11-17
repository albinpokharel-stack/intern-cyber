"""Event-related responses (CSV export)."""
import csv
import io

from services import event_service

COLUMNS = ["id", "timestamp", "source", "source_ip", "username", "event_type",
           "status", "severity", "details", "is_synthetic"]


def _safe_cell(value):
    """Stop spreadsheet formula injection: a cell starting with = + - @ gets a ' prefix."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


def export_events_csv(db) -> bytes:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([c.upper() for c in COLUMNS])
    for row in event_service.all_events(db):
        writer.writerow([_safe_cell(row[c]) for c in COLUMNS])
    return out.getvalue().encode("utf-8")
