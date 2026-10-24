"""Phase 2 tests: each payment test finds exactly its planted exceptions
(nothing missed, no false positives) on SQLite and, when DATABASE_URL is
set, on PostgreSQL.
"""

import csv
import os
import unittest

from src.db import ROOT, Database

Q = ROOT / "sql" / "02_payment_tests"
KEY = ROOT / "tests" / "answer_key.csv"

# query file -> (answer-key test codes it must find, id column in its output)
EXPECTED = {
    "01_duplicate_payments_exact.sql": ({"DUPLICATE_PAYMENT_EXACT"}, "payment_id"),
    "02_duplicate_payments_near.sql": ({"DUPLICATE_PAYMENT_NEAR"}, "payment_id"),
    "03_split_purchases.sql": ({"SPLIT_PURCHASE"}, "po_id"),
    "04_payments_to_unapproved_vendors.sql": (
        {"PAYMENT_INACTIVE_VENDOR", "PAYMENT_UNAPPROVED_VENDOR"}, "payment_id"),
    "05_round_sum_payments.sql": ({"ROUND_SUM_PAYMENT"}, "payment_id"),
}


def planted(codes: set[str]) -> set[str]:
    with open(KEY, newline="", encoding="utf-8") as f:
        return {r["record_id"] for r in csv.DictReader(f) if r["test"] in codes}


class Phase2Mixin:
    engine = "sqlite"

    @classmethod
    def setUpClass(cls):
        cls.db = Database(cls.engine)
        cls.db.load()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def found(self, name: str) -> tuple[list[dict], set[str]]:
        codes, id_col = EXPECTED[name]
        rows = self.db.run_file(Q / name)
        return rows, {r[id_col] for r in rows}

    def check(self, name: str) -> list[dict]:
        rows, ids = self.found(name)
        self.assertEqual(ids, planted(EXPECTED[name][0]))
        self.assertEqual(len(rows), len(ids), "each exception should appear once")
        return rows

    def test_exact_duplicates(self):
        rows = self.check("01_duplicate_payments_exact.sql")
        for r in rows:  # the original payment is referenced, never flagged itself
            self.assertNotEqual(r["first_payment_id"], r["payment_id"])

    def test_near_duplicates(self):
        rows = self.check("02_duplicate_payments_near.sql")
        self.assertEqual({r["match_basis"] for r in rows},
                         {"Same invoice number once punctuation is removed"})

    def test_split_purchases(self):
        rows = self.check("03_split_purchases.sql")
        for r in rows:
            self.assertGreaterEqual(int(r["pos_in_cluster"]), 2)
            self.assertGreater(float(r["cluster_total"]), 10_000)
            self.assertLessEqual(float(r["amount"]), 10_000)

    def test_unapproved_and_inactive_vendors(self):
        rows = self.check("04_payments_to_unapproved_vendors.sql")
        reasons = {r["vendor_id"]: r["reason"] for r in rows}
        self.assertEqual(reasons["V073"], "Vendor status: Inactive")
        self.assertEqual(reasons["V081"], "Vendor not approved (due diligence incomplete)")

    def test_round_sums(self):
        rows = self.check("05_round_sum_payments.sql")
        self.assertTrue(all(float(r["amount"]) % 1000 == 0 for r in rows))

    def test_no_false_positives_across_phase2(self):
        """Everything Phase 2 flags is in the answer key, and vice versa."""
        all_ids = set()
        for name in EXPECTED:
            all_ids |= self.found(name)[1]
        phase2 = set().union(*(codes for codes, _ in EXPECTED.values()))
        self.assertEqual(all_ids, planted(phase2))


class SQLitePhase2(Phase2Mixin, unittest.TestCase):
    engine = "sqlite"


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "set DATABASE_URL to test PostgreSQL")
class PostgresPhase2(Phase2Mixin, unittest.TestCase):
    engine = "postgres"


if __name__ == "__main__":
    unittest.main()
