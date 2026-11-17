-- SentinelX database schema (version 1)
-- Every statement is "IF NOT EXISTS", so it is safe to run on every start.

CREATE TABLE IF NOT EXISTS schema_version (
    version    INTEGER NOT NULL,
    applied_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT    NOT NULL,              -- always UTC, ISO-8601
    source       TEXT    NOT NULL,              -- e.g. Windows-Security, Firewall
    source_ip    TEXT,
    username     TEXT,
    event_type   TEXT    NOT NULL,              -- e.g. login, connection
    status       TEXT    NOT NULL,              -- success / failed / blocked ...
    severity     TEXT    NOT NULL DEFAULT 'info',
    details      TEXT,
    is_synthetic INTEGER NOT NULL DEFAULT 0,    -- 1 = test data, 0 = real data
    event_uid    TEXT UNIQUE                    -- used later to stop duplicates
);
CREATE INDEX IF NOT EXISTS idx_events_time   ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_ip     ON events(source_ip);
CREATE INDEX IF NOT EXISTS idx_events_lookup ON events(event_type, status);

CREATE TABLE IF NOT EXISTS alerts (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id           TEXT NOT NULL,
    title             TEXT NOT NULL,
    severity          TEXT NOT NULL,
    description       TEXT NOT NULL,
    source_ip         TEXT,
    trigger_timestamp TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'open',  -- open/investigating/resolved/closed
    evidence          TEXT,                          -- JSON: WHY the rule fired
    related_event_ids TEXT,                          -- JSON list of event ids
    notes             TEXT NOT NULL DEFAULT '',
    dedup_key         TEXT NOT NULL,
    is_synthetic      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_alerts_dedup ON alerts(dedup_key, status);

CREATE TABLE IF NOT EXISTS collector_status (
    name             TEXT PRIMARY KEY,
    status           TEXT NOT NULL,
    last_attempt     TEXT,
    last_success     TEXT,
    last_error       TEXT,
    events_collected INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS audit_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    actor     TEXT NOT NULL,
    action    TEXT NOT NULL,
    target    TEXT,
    details   TEXT
);
