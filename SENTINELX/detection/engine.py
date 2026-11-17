"""The detection engine: runs every enabled rule and stores new alerts."""
import logging

import config
from detection.rules import RULES
from services import alert_service

log = logging.getLogger("sentinelx.detection")


def run_detection(db) -> list:
    """Run all enabled rules. Returns the ids of alerts created in this run."""
    created = []
    for rule_id, (title, fn) in RULES.items():
        cfg = config.DETECTION_RULES.get(rule_id, {})
        if not cfg.get("enabled", False):
            continue
        try:
            for finding in fn(db, cfg):
                alert_id = alert_service.create_alert_if_new(db, finding)
                if alert_id:
                    created.append(alert_id)
        except Exception:
            # One broken rule must never stop the others.
            log.exception("Rule %s failed", rule_id)
    return created
