"""Phase 3 tests: vendor and timing tests find exactly their planted
exceptions (nothing missed, no false positives) on SQLite and, when
DATABASE_URL is set, on PostgreSQL.
"""

import csv
import os
import unittest

from src.db import ROOT, Database

Q = ROOT / "sql" / "03_vendor_and_timing_tests"
KEY = ROOT / "tests" / "answer_key.csv"

# query file -> (answer-key test codes it must find, id column in its output)
EXPECTED = {
    "01_vendor_employee_matches.sql": (
        {"VENDOR_EMPLOYEE_BANK", "VENDOR_EMPLOYEE_ADDRESS"}, "vendor_id"),
    "03_benford_vendor_outliers.sql": ({"BENFORD_OUTLIER_VENDOR"}, "invoice_id"),
    "04_out_of_hours_journals.sql": ({"JOURNAL_OUT_OF_HOURS"}, "je_id"),
}

# Benford's law: P(first digit = d) = log10(1 + 1/d), as percentages.
BENFORD = {1: 30.10, 2: 17.61, 3: 12.49, 4: 9.69, 5: 7.92,
           6: 6.69, 7: 5.80, 8: 5.12, 9: 4.58}


def key_rows(codes: set[str]) -> list[dict]:
    with open(KEY, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["test"] in codes]


def planted(codes: set[str]) -> set[str]:
    return {r["record_id"] for r in key_rows(codes)}


class Phase3Mixin:
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
        ids = {r[id_col] for r in rows}
        self.assertEqual(ids, planted(codes))
        return rows

    def test_vendor_employee_matches(self):
        rows = self.check("01_vendor_employee_matches.sql")
        found = {(r["vendor_id"], r["employee_id"], r["match_basis"]) for r in rows}
        # The answer key's note says which employee each vendor matches.
        expected = set()
        for r in key_rows({"VENDOR_EMPLOYEE_BANK", "VENDOR_EMPLOYEE_ADDRESS"}):
            basis = "Bank account" if r["test"] == "VENDOR_EMPLOYEE_BANK" else "Address"
            expected.add((r["record_id"], r["note"].split()[-1], basis))
        self.assertEqual(found, expected)

    def test_benford_profile_is_complete(self):
        rows = self.run_query("02_benford_first_digit.sql")
        self.assertEqual([int(r["digit"]) for r in rows], list(range(1, 10)))
        self.assertAlmostEqual(sum(float(r["expected_pct"]) for r in rows), 100.0, delta=0.1)
        self.assertAlmostEqual(sum(float(r["actual_pct"]) for r in rows), 100.0, delta=0.1)
        for r in rows:
            self.assertEqual(float(r["expected_pct"]), BENFORD[int(r["digit"])])

    def test_benford_vendor_outliers(self):
        rows = self.check("03_benford_vendor_outliers.sql")
        self.assertEqual({r["vendor_id"] for r in rows}, {"V041"})
        self.assertEqual({int(r["first_digit"]) for r in rows}, {9})
        self.assertTrue(all(float(r["amount"]) >= 1000 for r in rows))

    def test_out_of_hours_journals(self):
        rows = self.check("04_out_of_hours_journals.sql")
        # The answer key notes give the day and time, e.g. "Sat 22:47".
        notes = {r["record_id"]: r["note"] for r in key_rows({"JOURNAL_OUT_OF_HOURS"})}
        for r in rows:
            day, hhmm = notes[r["je_id"]].split()
            self.assertEqual(r["posted_day"], day)
            self.assertIn(hhmm, str(r["posted_at"]))

    def test_helper_view_weekday_and_hour(self):
        """The two engines' helper views must agree, JE01201 was posted on Sat 10 Jan 2026 at 22:47."""
        rows = self.db.query("""
            SELECT posted_dow, posted_hour FROM v_journal_entries WHERE je_id = 'JE01201';""")
        self.assertEqual((int(rows[0]["posted_dow"]), int(rows[0]["posted_hour"])), (6, 22))

    def test_no_false_positives_across_phase3(self):
        """Everything Phase 3 flags is in the answer key, and vice versa."""
        found = set()
        for name, (_, id_col) in EXPECTED.items():
            found |= {r[id_col] for r in self.run_query(name)}
        phase3 = set().union(*(codes for codes, _ in EXPECTED.values()))
        self.assertEqual(found, planted(phase3))


class SQLitePhase3(Phase3Mixin, unittest.TestCase):
    engine = "sqlite"


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "set DATABASE_URL to test PostgreSQL")
class PostgresPhase3(Phase3Mixin, unittest.TestCase):
    engine = "postgres"


if __name__ == "__main__":
    unittest.main()
