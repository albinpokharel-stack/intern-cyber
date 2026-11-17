"""Run from the project folder:  python -m unittest discover -s tests -v"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from database import db as database
from detection.engine import run_detection
from services import alert_service, event_service


def failed(db, ip, n, synthetic=False):
    for _ in range(n):
        event_service.add_event(db, source="Test", event_type="login", status="failed",
                                source_ip=ip, username="admin", is_synthetic=synthetic)


class DetectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        config.DATA_DIR = Path(self.tmp.name)
        config.DB_PATH = Path(self.tmp.name) / "test.db"
        database.initialize_database()

    def tearDown(self):
        self.tmp.cleanup()

    def alerts(self, db):
        return db.execute("SELECT * FROM alerts").fetchall()

    def test_below_threshold_no_alert(self):
        with database.db_session() as db:
            failed(db, "10.0.0.5", 4)
            self.assertEqual(run_detection(db), [])

    def test_threshold_creates_alert_with_evidence(self):
        with database.db_session() as db:
            failed(db, "10.0.0.5", 5)
            run_detection(db)
            rows = self.alerts(db)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["rule_id"], "SX-001")
            self.assertIn("why", rows[0]["evidence"])

    def test_deduplication(self):
        with database.db_session() as db:
            failed(db, "10.0.0.5", 6)
            run_detection(db)
            run_detection(db)
            self.assertEqual(len(self.alerts(db)), 1)

    def test_success_after_failures(self):
        with database.db_session() as db:
            failed(db, "10.0.0.9", 5)
            event_service.add_event(db, source="Test", event_type="login", status="success",
                                    source_ip="10.0.0.9", username="admin")
            run_detection(db)
            self.assertEqual({a["rule_id"] for a in self.alerts(db)}, {"SX-001", "SX-002"})

    def test_synthetic_flag_carries_to_alert(self):
        with database.db_session() as db:
            failed(db, "203.0.113.7", 5, synthetic=True)
            run_detection(db)
            self.assertEqual(self.alerts(db)[0]["is_synthetic"], 1)

    def test_resolved_alert_can_fire_again(self):
        with database.db_session() as db:
            failed(db, "10.0.0.5", 5)
            run_detection(db)
            db.execute("UPDATE alerts SET status='resolved'")
            self.assertEqual(len(run_detection(db)), 1)

    def test_rejects_invalid_ip(self):
        with database.db_session() as db:
            with self.assertRaises(ValueError):
                event_service.add_event(db, source="T", event_type="login",
                                        status="failed", source_ip="not-an-ip")

    def test_duplicate_event_uid_ignored(self):
        with database.db_session() as db:
            a = event_service.add_event(db, source="T", event_type="x", status="ok", event_uid="abc")
            b = event_service.add_event(db, source="T", event_type="x", status="ok", event_uid="abc")
            self.assertIsNotNone(a)
            self.assertIsNone(b)


if __name__ == "__main__":
    unittest.main()
