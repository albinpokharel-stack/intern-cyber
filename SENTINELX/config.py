"""
SentinelX configuration.

Everything you may want to tune lives in this one file.
Detection thresholds are here so you can change them WITHOUT touching code.
"""
from pathlib import Path

# ---- Paths -----------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
BACKUP_DIR = DATA_DIR / "backups"
STATIC_DIR = BASE_DIR / "static"
DB_PATH = DATA_DIR / "sentinelx.db"

# ---- Web server ------------------------------------------------------------
# 127.0.0.1 = reachable ONLY from this computer. Do not change this until
# authentication has been added and reviewed.
HOST = "127.0.0.1"
PORT = 8080

APP_NAME = "SentinelX"
APP_VERSION = "0.4.1"
BACKUPS_TO_KEEP = 7

# ---- Detection rules -------------------------------------------------------
DETECTION_RULES = {
    # SX-001: many failed logins from one IP inside a time window
    "SX-001": {
        "enabled": True,
        "threshold": 5,
        "window_minutes": 15,
        "severity": "High",
    },
    # SX-002: many failed logins from one IP, THEN a success from that same IP
    "SX-002": {
        "enabled": True,
        "threshold": 5,
        "window_minutes": 15,
        "severity": "Critical",
    },
}
