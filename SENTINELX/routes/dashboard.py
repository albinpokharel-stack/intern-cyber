"""Builds the dashboard page (pure HTML, no JavaScript, no external libraries)."""
import html
from datetime import datetime, timezone

import config
from database.db import db_session, health_info
from routes.security import CSRF_TOKEN
from services import alert_service, event_service

SEV_COLORS = {"Critical": "#f43f5e", "High": "#f97316", "Medium": "#eab308", "Low": "#22c55e"}
STATUS_COLORS = {"success": "#22c55e", "failed": "#f43f5e", "blocked": "#eab308"}


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def fmt_ts(ts) -> str:
    return esc(str(ts).replace("T", " ")[:19]) if ts else "—"


def origin_badge(is_synthetic) -> str:
    return '<span class="pill test">TEST</span>' if is_synthetic else '<span class="pill real">REAL</span>'


def bars(rows, color="var(--accent)") -> str:
    if not rows:
        return '<p class="empty">No data yet</p>'
    top = max(r["n"] for r in rows) or 1
    return "".join(
        f'<div class="bar-row"><div class="bar-label" title="{esc(r["label"])}">{esc(r["label"])}</div>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{r["n"] / top * 100:.1f}%;background:{color}"></div></div>'
        f'<b>{r["n"]}</b></div>' for r in rows)


def donut(parts, colors, center) -> str:
    """parts: list of (label, count)."""
    total = sum(n for _, n in parts)
    if not total:
        return '<p class="empty">No data yet</p>'
    stops, legend, cur = [], [], 0.0
    for label, n in parts:
        end = cur + n / total * 100
        color = colors.get(label, "#38bdf8")
        stops.append(f"{color} {cur:.2f}% {end:.2f}%")
        legend.append(f'<div class="legend-item"><span style="background:{color}"></span>{esc(str(label).title())} <b>{n}</b></div>')
        cur = end
    return (f'<div class="donut-wrap"><div class="donut" style="background:conic-gradient({", ".join(stops)})">'
            f'<div class="donut-hole"><b>{esc(center)}</b></div></div><div>{"".join(legend)}</div></div>')


def timeline_svg(buckets) -> str:
    w, h, pad_l, pad_b = 720, 170, 28, 22
    plot_h = h - pad_b - 12
    top = max(c for _, c in buckets) or 1
    slot = (w - pad_l) / len(buckets)
    out = [f'<svg viewBox="0 0 {w} {h}" class="timeline" role="img" aria-label="Events per hour">']
    for frac in (0.5, 1):  # light grid lines
        y = 8 + plot_h * (1 - frac)
        out.append(f'<line x1="{pad_l}" x2="{w}" y1="{y:.1f}" y2="{y:.1f}" class="grid-line"/>')
    out.append(f'<text x="0" y="14" class="axis">{top}</text>')
    for i, (label, count) in enumerate(buckets):
        bh = count / top * plot_h
        x = pad_l + i * slot + slot * 0.15
        out.append(f'<rect x="{x:.1f}" y="{8 + plot_h - bh:.1f}" width="{slot * 0.7:.1f}" height="{max(bh, 1.5):.1f}" '
                   f'rx="3" class="{"tbar" if count else "tbar empty-bar"}"><title>{label}:00 UTC — {count} events</title></rect>')
        if i % 4 == 0:
            out.append(f'<text x="{x:.1f}" y="{h - 6}" class="axis">{label}h</text>')
    out.append("</svg>")
    return "".join(out)


PIPELINE = [
    ("Collect", "Windows logs", "next", "Milestone 2"),
    ("Normalize", "One clean format", "done", "Ready"),
    ("Store", "SQLite database", "done", "Ready"),
    ("Detect", "Rule engine", "done", "2 rules"),
    ("Alert", "Evidence + dedupe", "done", "Ready"),
    ("Investigate", "Explorer + incidents", "next", "Milestone 3-4"),
    ("Report", "Export & audit", "later", "Later"),
]


def pipeline() -> str:
    items = "".join(
        f'<div class="step {state}"><div class="step-dot">{i + 1}</div><b>{name}</b>'
        f'<span>{desc}</span><em>{tag}</em></div>'
        for i, (name, desc, state, tag) in enumerate(PIPELINE))
    return f'<div class="pipeline">{items}</div>'


def kpi(icon, label, value, tone, sub="") -> str:
    return (f'<div class="card {tone}"><div class="card-top"><span class="card-icon">{icon}</span>'
            f'<span class="card-label">{label}</span></div><div class="card-number">{value}</div>'
            f'<div class="card-sub">{sub}</div></div>')


def render_dashboard(query: str = "") -> str:
    with db_session() as db:
        ov = event_service.overview(db)
        sev = alert_service.counts_by_severity(db)
        unresolved = alert_service.unresolved_count(db)
        alerts = alert_service.latest(db)
        rules = alert_service.by_rule(db)
        collectors = alert_service.collectors(db)
        sources = event_service.by_source(db)
        statuses = event_service.by_status(db)
        ips = event_service.top_ips(db)
        timeline = event_service.hourly_timeline(db)
        events = event_service.recent(db, 12, query)
    health = health_info()

    cards = "".join([
        kpi("◈", "Total events", ov["total"], "blue", f'{ov["real"]} real · {ov["synthetic"]} test'),
        kpi("⛔", "Critical alerts", sev.get("Critical", 0), "rose", "active"),
        kpi("▲", "High alerts", sev.get("High", 0), "orange", "active"),
        kpi("●", "Medium alerts", sev.get("Medium", 0), "yellow", "active"),
        kpi("🔑", "Failed logins", ov["failed_logins"], "rose", "all time"),
        kpi("🚨", "Unresolved alerts", unresolved, "orange", "open + investigating"),
        kpi("▤", "Active log sources", ov["sources"], "green", "seen in events"),
    ])

    sev_parts = [(s, sev.get(s, 0)) for s in ("Critical", "High", "Medium", "Low") if sev.get(s, 0)]
    alert_rows = "".join(
        f'<tr><td>ALT-{a["id"]:04d}</td><td>{fmt_ts(a["trigger_timestamp"])}</td>'
        f'<td>{esc(a["rule_id"])} · {esc(a["title"])}</td>'
        f'<td><span class="sev" style="--c:{SEV_COLORS.get(a["severity"], "#38bdf8")}">{esc(a["severity"])}</span></td>'
        f'<td>{esc(a["source_ip"])}</td><td>{esc(a["status"])}</td><td>{origin_badge(a["is_synthetic"])}</td>'
        f'<td class="wide">{esc(a["description"])}</td></tr>' for a in alerts
    ) or '<tr><td colspan="8" class="empty">No alerts. Nothing suspicious detected.</td></tr>'

    event_rows = "".join(
        f'<tr><td>{e["id"]}</td><td>{fmt_ts(e["timestamp"])}</td><td>{esc(e["source"])}</td>'
        f'<td>{esc(e["source_ip"])}</td><td>{esc(e["username"])}</td><td>{esc(e["event_type"])}</td>'
        f'<td><span class="st {esc(e["status"])}">{esc(e["status"])}</span></td>'
        f'<td>{origin_badge(e["is_synthetic"])}</td><td class="wide">{esc(e["details"])}</td></tr>' for e in events
    ) or '<tr><td colspan="9" class="empty">No events found.</td></tr>'

    coll_rows = "".join(
        f'<div class="health-row"><span class="dot {"ok" if c["status"] == "ok" else "idle"}"></span>'
        f'<div><b>{esc(c["name"])}</b><small>{"Not configured yet (Milestone 2)" if c["status"] == "not_configured" else esc(c["status"])}'
        f' · last success: {fmt_ts(c["last_success"])} · {c["events_collected"]} events</small></div></div>'
        for c in collectors)

    ok = health["db_ok"]
    sys_rows = (
        f'<div class="health-row"><span class="dot {"ok" if ok else "bad"}"></span><div><b>Database</b>'
        f'<small>{"Integrity check passed" if ok else "PROBLEM DETECTED"} · {health["db_size_kb"]} KB · schema v{health["schema_version"]}</small></div></div>'
        f'<div class="health-row"><span class="dot ok"></span><div><b>Last backup</b><small>{fmt_ts(health["last_backup"])} UTC</small></div></div>'
        f'<div class="health-row"><span class="dot ok"></span><div><b>Last event ingested</b><small>{fmt_ts(ov["last_event"])} UTC</small></div></div>'
        f'<div class="health-row"><span class="dot ok"></span><div><b>Web server</b><small>Bound to {config.HOST}:{config.PORT} (this computer only)</small></div></div>')

    now = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M:%S UTC")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SentinelX | Security Operations Center</title>
<link rel="stylesheet" href="/static/css/style.css"></head>
<body>
<header><div class="brand"><div class="logo">🛡️</div><div><h1>SENTINELX</h1>
<p>Mini-SOC · Threat Detection &amp; Monitoring</p></div></div>
<div class="live"><span class="pulse"></span>LOCAL MONITORING ACTIVE</div></header>
<main>
<div class="heading"><div><h2>Security Overview</h2><div class="muted">Plain-English view of what is happening on your system</div></div>
<div class="muted">Updated {now}</div></div>

<section class="panel"><h3>How SentinelX works <small>(the SOC pipeline — green = built, blue = next)</small></h3>{pipeline()}</section>

<div class="cards">{cards}</div>

<div class="grid two">
<section class="panel"><h3>◷ Event timeline <small>events per hour, last 24h (UTC)</small></h3>{timeline_svg(timeline)}</section>
<section class="panel"><h3>⚠ Active alerts by severity</h3>{donut(sev_parts, SEV_COLORS, unresolved)}</section>
</div>

<div class="grid">
<section class="panel"><h3>▥ Events by source</h3>{bars(sources)}</section>
<section class="panel"><h3>◉ Events by status</h3>{donut([(r["label"], r["n"]) for r in statuses], STATUS_COLORS, ov["total"])}</section>
<section class="panel"><h3>⌖ Top source IPs</h3>{bars(ips, "linear-gradient(90deg,#8b5cf6,#38bdf8)")}</section>
<section class="panel"><h3>⚙ Detection rule activity</h3>{bars(rules, "linear-gradient(90deg,#f97316,#f43f5e)")}</section>
</div>

<div class="grid two">
<section class="panel"><h3>📡 Log collector health</h3>{coll_rows}</section>
<section class="panel"><h3>🩺 System health</h3>{sys_rows}</section>
</div>

<section class="panel"><h3>🚨 Latest alerts</h3><div class="scroll"><table>
<tr><th>ID</th><th>Time (UTC)</th><th>Rule</th><th>Severity</th><th>Source IP</th><th>Status</th><th>Data</th><th>Why it fired</th></tr>
{alert_rows}</table></div></section>

<section class="panel"><h3>⌕ Recent events</h3>
<form method="GET" action="/" class="toolbar"><input name="q" maxlength="100" placeholder="Search IP, user, source, status…" value="{esc(query)}">
<button type="submit">Search</button><a class="button ghost" href="/export">↓ Export CSV</a></form>
<div class="scroll"><table><tr><th>ID</th><th>Time (UTC)</th><th>Source</th><th>IP</th><th>User</th><th>Type</th><th>Status</th><th>Data</th><th>Details</th></tr>
{event_rows}</table></div></section>

<section class="panel"><h3>⚡ Test tools</h3>
<form method="POST" action="/simulate" class="toolbar"><input type="hidden" name="csrf" value="{CSRF_TOKEN}"><button type="submit">+ Generate failed-login burst (TEST data)</button></form>
<div class="muted">Adds 6 clearly-labelled synthetic failed logins so you can watch the detection engine create an alert. Safe and read-only.</div></section>
</main>
<footer>SENTINELX v{config.APP_VERSION} · Local defensive monitoring · Authorized, read-only</footer>
</body></html>"""
