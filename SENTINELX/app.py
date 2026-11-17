"""
SentinelX entry point.  Run with:   python app.py
It starts a local web server (127.0.0.1 only) and routes URLs to the right code.
"""
import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging.handlers import RotatingFileHandler
from urllib.parse import parse_qs, urlparse

import config
from database.db import backup_database, db_session, health_info, initialize_database
from detection.engine import run_detection
from routes.dashboard import render_dashboard
from routes.events import export_events_csv
from routes.security import csrf_valid
from services import audit_service, event_service

log = logging.getLogger("sentinelx")
STATIC_TYPES = {".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8"}


def setup_logging():
    config.LOG_DIR.mkdir(exist_ok=True)
    handler = RotatingFileHandler(config.LOG_DIR / "sentinelx.log", maxBytes=1_000_000,
                                  backupCount=3, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(fmt)
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logging.basicConfig(level=logging.INFO, handlers=[handler, console])


class Handler(BaseHTTPRequestHandler):
    server_version = "SentinelX"
    sys_version = ""

    # ---- helpers ----
    def _send(self, status, body: bytes, ctype="text/html; charset=utf-8", extra=None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; script-src 'none'; style-src 'self' 'unsafe-inline'; "
                         "img-src 'self' data:; frame-ancestors 'none'; form-action 'self'")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _allowed_hosts(self):
        return {f"127.0.0.1:{config.PORT}", f"localhost:{config.PORT}"}

    def _host_ok(self):  # blocks DNS-rebinding style attacks
        return self.headers.get("Host", "") in self._allowed_hosts()

    # ---- routes ----
    def do_GET(self):
        try:
            if not self._host_ok():
                return self._send(403, f"Forbidden: open http://127.0.0.1:{config.PORT} in your browser".encode(), "text/plain")
            parsed = urlparse(self.path)
            if parsed.path == "/":
                q = parse_qs(parsed.query).get("q", [""])[0]
                return self._send(200, render_dashboard(q).encode("utf-8"))
            if parsed.path == "/export":
                with db_session() as db:
                    data = export_events_csv(db)
                    audit_service.record(db, "export_events_csv")
                return self._send(200, data, "text/csv; charset=utf-8", {
                    "Content-Disposition": 'attachment; filename="sentinelx_events.csv"'})
            if parsed.path == "/health":
                return self._send(200, json.dumps(health_info()).encode(), "application/json")
            if parsed.path.startswith("/static/"):
                return self._serve_static(parsed.path[len("/static/"):])
            return self._send(404, b"Not found", "text/plain")
        except Exception:
            log.exception("GET %s failed", self.path)
            self._send(500, b"Internal error (see logs/sentinelx.log)", "text/plain")

    def do_POST(self):
        try:
            if not self._host_ok():
                log.warning("POST blocked: bad Host header %r", self.headers.get("Host"))
                return self._send(403, f"Forbidden: Host header {self.headers.get('Host')!r} is not allowed. "
                                       f"Open http://127.0.0.1:{config.PORT}".encode(), "text/plain")
            length = min(int(self.headers.get("Content-Length") or 0), 2048)
            form = parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
            if not csrf_valid(form.get("csrf", [""])[0]):
                log.warning("POST blocked: missing or wrong CSRF token")
                return self._send(403, b"Forbidden: security token missing or expired. "
                                       b"Go back, refresh the page (CTRL+F5) and try again.", "text/plain")
            if self.path == "/simulate":
                with db_session() as db:
                    event_service.generate_failed_login_burst(db)
                    created = run_detection(db)
                    audit_service.record(db, "simulate_failed_logins", details=f"alerts_created={len(created)}")
                self.send_response(303)
                self.send_header("Location", "/")
                self.end_headers()
                return
            self._send(404, b"Not found", "text/plain")
        except Exception:
            log.exception("POST %s failed", self.path)
            self._send(500, b"Internal error (see logs/sentinelx.log)", "text/plain")

    def _serve_static(self, rel):
        target = (config.STATIC_DIR / rel).resolve()
        if (not target.is_relative_to(config.STATIC_DIR.resolve()) or not target.is_file()
                or target.suffix not in STATIC_TYPES):
            return self._send(404, b"Not found", "text/plain")
        self._send(200, target.read_bytes(), STATIC_TYPES[target.suffix])

    def log_message(self, fmt, *args):
        log.info("%s %s", self.address_string(), fmt % args)


def main():
    if sys.version_info < (3, 9):
        sys.exit("SentinelX needs Python 3.9 or newer.")
    setup_logging()
    backup_database()          # copy the old DB first, if one exists
    initialize_database()
    with db_session() as db:
        event_service.seed_samples(db)
        run_detection(db)
    server = ThreadingHTTPServer((config.HOST, config.PORT), Handler)
    print("=" * 44)
    print("        SENTINELX SECURITY CENTER")
    print("=" * 44)
    print(f"Dashboard : http://{config.HOST}:{config.PORT}")
    print("Press CTRL+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SentinelX...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
