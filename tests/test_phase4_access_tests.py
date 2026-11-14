"""Phase 4 tests: access and segregation-of-duties tests find exactly their
planted exceptions (nothing missed, no false positives) on SQLite and, when
DATABASE_URL is set, on PostgreSQL.
"""

import csv
import os
import unittest

from src.db import ROOT, Database

Q = ROOT / "sql" / "04_access_tests"
KEY = ROOT / "tests" / "answer_key.csv"

# query file -> (answer-key test codes it must find, id column in its output)
EXPECTED = {
    "01_vendor_creator_approves_payment.sql": (
        {"SOD_VENDOR_CREATOR_APPROVES_PAYMENT"}, "payment_id"),
    "02_same_person_both_steps.sql": ({"SOD_JOURNAL_SELF_APPROVED"}, "record_id"),
    "03_activity_after_leaving.sql": ({"ACTIVITY_AFTER_LEAVING"}, "record_id"),
    "04_privileged_account_activity.sql": ({"PRIVILEGED_ACCOUNT_POSTING"}, "record_id"),
}


def key_rows(codes: set[str]) -> list[dict]:
    with open(KEY, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["test"] in codes]


def planted(codes: set[str]) -> set[str]:
    return {r["record_id"] for r in key_rows(codes)}


class Phase4Mixin:
    engine = "sqlite"

    @classmethod
    def setUpClass(cls):
        cls.db = Database(cls.engine)
        cls.db.load()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def run_query(self, name: str) -> list[dict]:
        return self.db.run_file(Q / name)

    def check(self, name: str) -> list[dict]:
        codes, id_col = EXPECTED[name]
        rows = self.run_query(name)
        self.assertEqual({r[id_col] for r in rows}, planted(codes))
        return rows

    def test_vendor_creator_approves_payment(self):
        rows = self.check("01_vendor_creator_approves_payment.sql")
        # The answer key note names the user and vendor, e.g. "U033 created V014 ..."
        notes = {r["record_id"]: r["note"].split()[:3]
                 for r in key_rows({"SOD_VENDOR_CREATOR_APPROVES_PAYMENT"})}
        for r in rows:
            user, _, vendor = notes[r["payment_id"]]
            self.assertEqual((r["payment_approved_by"], r["vendor_id"]), (user, vendor))
            self.assertEqual(r["vendor_created_by"], r["payment_approved_by"])

    def test_same_person_both_steps(self):
        rows = self.check("02_same_person_both_steps.sql")
        self.assertEqual({r["steps_combined"] for r in rows}, {"Created and approved"})

    def test_activity_after_leaving(self):
        rows = self.check("03_activity_after_leaving.sql")
        for r in rows:
            self.assertGreater(str(r["action_date"]), str(r["disabled_date"]))
        self.assertEqual({r["user_id"] for r in rows}, {"U022", "U030"})

    def test_privileged_account_activity(self):
        rows = self.check("04_privileged_account_activity.sql")
        owners = {r["user_id"]: r["account_owner"] for r in rows}
        self.assertEqual(owners["U041"], "Generic account: no named person")
        self.assertTrue(owners["U040"].startswith("Named administrator"))

    def test_helper_view_posted_date(self):
        rows = self.db.query("SELECT posted_date FROM v_journal_entries WHERE je_id = 'JE01207';")
        self.assertEqual(str(rows[0]["posted_date"]), "2026-07-14")

    def test_no_false_positives_across_phase4(self):
        """Everything Phase 4 flags is in the answer key, and vice versa."""
        found = set()
        for name, (_, id_col) in EXPECTED.items():
            found |= {r[id_col] for r in self.run_query(name)}
        phase4 = set().union(*(codes for codes, _ in EXPECTED.values()))
        self.assertEqual(found, planted(phase4))


class SQLitePhase4(Phase4Mixin, unittest.TestCase):
    engine = "sqlite"


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "set DATABASE_URL to test PostgreSQL")
class PostgresPhase4(Phase4Mixin, unittest.TestCase):
    engine = "postgres"


if __name__ == "__main__":
    unittest.main()
