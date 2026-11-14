"""Phase 1 tests: the dataset loads and the data-validation queries find
exactly the planted problems, on SQLite and (when DATABASE_URL is set) on
PostgreSQL. Run with `python -m pytest` or `python -m unittest`.
"""

import csv
import os
import unittest
from pathlib import Path

from src.db import ROOT, Database

Q = ROOT / "sql" / "01_data_validation"
KEY = ROOT / "tests" / "answer_key.csv"


def answer_key(phase: int) -> list[dict]:
    with open(KEY, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if int(r["phase"]) == phase]


class Phase1Mixin:
    engine = "sqlite"

    @classmethod
    def setUpClass(cls):
        cls.db = Database(cls.engine)
        cls.db.load()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def run_q(self, name: str) -> list[dict]:
        return self.db.run_file(Q / name)

    def test_control_totals_reconcile(self):
        rows = self.run_q("01_reconcile_control_totals.sql")
        self.assertEqual(len(rows), 9)
        self.assertEqual({r["status"] for r in rows}, {"MATCH"})

    def test_integrity_finds_exactly_the_planted_orphans(self):
        found = {r["record_id"] for r in self.run_q("02_referential_integrity.sql")}
        expected = {r["record_id"] for r in answer_key(1)}
        self.assertEqual(found, expected)

    def test_key_fields_complete(self):
        rows = self.run_q("03_completeness.sql")
        self.assertTrue(rows)
        self.assertTrue(all(int(r["blank_count"]) == 0 for r in rows))

    def test_twelve_months_all_in_period(self):
        rows = self.run_q("04_period_coverage.sql")
        self.assertEqual([r["month"] for r in rows][0], "2025-10")
        self.assertEqual(len(rows), 12)
        self.assertEqual({r["period_status"] for r in rows}, {"IN PERIOD"})


class SQLitePhase1(Phase1Mixin, unittest.TestCase):
    engine = "sqlite"


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "set DATABASE_URL to test PostgreSQL")
class PostgresPhase1(Phase1Mixin, unittest.TestCase):
    engine = "postgres"


class DatasetIsReproducible(unittest.TestCase):
    def test_same_seed_same_data(self):
        from src import generate_data as g
        t1, k1 = g.build()
        t2, k2 = g.build()
        self.assertEqual(t1, t2)
        self.assertEqual(k1, k2)

    def test_committed_data_matches_generator(self):
        """The CSVs in data/ are exactly what the generator produces."""
        from src import generate_data as g
        tables, _ = g.build()
        for name, rows in tables.items():
            with open(ROOT / "data" / f"{name}.csv", newline="", encoding="utf-8") as f:
                on_disk = list(csv.DictReader(f))
            self.assertEqual(len(on_disk), len(rows), name)
            self.assertEqual(on_disk[0], {k: str(v) for k, v in rows[0].items()}, name)


if __name__ == "__main__":
    unittest.main()
