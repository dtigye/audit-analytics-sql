"""Phase 5 tests: the exceptions summary and working papers agree with the
answer key, on SQLite and, when DATABASE_URL is set, on PostgreSQL.
"""

import csv
import os
import unittest

from src.db import ROOT, SQL, Database
from src.report import FINDINGS, build, criteria

KEY = ROOT / "tests" / "answer_key.csv"


def answer_key() -> list[dict]:
    with open(KEY, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class Phase5Mixin:
    engine = "sqlite"

    @classmethod
    def setUpClass(cls):
        cls.db = Database(cls.engine)
        cls.db.load()
        cls.results = build(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_every_planted_exception_is_reported_once(self):
        reported = [i for r in self.results for i in r["ids"]]
        self.assertEqual(len(reported), len(set(reported)), "a record is in two findings")
        self.assertEqual(set(reported), {r["record_id"] for r in answer_key()})

    def test_values_match_known_figures(self):
        """Spot-check values against figures published in the README."""
        value = {r["finding"].ref: r["value"] for r in self.results}
        self.assertAlmostEqual(value["WP-2.1"], 7314.07, places=2)
        self.assertAlmostEqual(value["WP-3.3"], 171074.84, places=2)
        self.assertAlmostEqual(value["WP-4.1"], 33520.07, places=2)

    def test_every_finding_has_criteria_from_its_query(self):
        for f in FINDINGS:
            self.assertTrue((SQL / f.query).exists(), f.query)
            self.assertGreater(len(criteria(f.query)), 20, f.ref)

    def test_every_finding_has_all_five_elements(self):
        for f in FINDINGS:
            for field in ("causes", "effect", "recommendation"):
                self.assertTrue(getattr(f, field).strip(), f"{f.ref} has no {field}")
            self.assertIn(f.rating, {"High", "Medium", "Low"})


class SQLitePhase5(Phase5Mixin, unittest.TestCase):
    engine = "sqlite"


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "set DATABASE_URL to test PostgreSQL")
class PostgresPhase5(Phase5Mixin, unittest.TestCase):
    engine = "postgres"


if __name__ == "__main__":
    unittest.main()
