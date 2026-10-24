"""Tests for the database wrapper itself (src/db.py).

Issue #1: Database.query() promises to return the rows of the LAST SELECT.
SQLite always did; the PostgreSQL path printed every result set and parsed
them as one malformed CSV. These tests run the same multi-statement SQL on
both engines and expect identical, correct results.
"""

import os
import unittest

from src.db import Database

# Three statements: drop, create a temporary view, then SELECT from it.
# The view only exists inside one session, so this also proves that all
# statements run in the same database session on both engines.
MULTI = """
DROP VIEW IF EXISTS tmp_issue1;
CREATE TEMP VIEW tmp_issue1 AS SELECT 5 AS n, 'x' AS label;
SELECT n * 2 AS doubled, label FROM tmp_issue1;
"""

TWO_SELECTS = "SELECT 1 AS first_result; SELECT 2 AS second_result, 'b' AS tag;"

# A semicolon inside a string or a comment must not split the statement.
TRICKY = """
-- comment with a semicolon; that must be ignored
SELECT 'a;b' AS text_with_semicolon;
"""


class DbMixin:
    engine = "sqlite"

    @classmethod
    def setUpClass(cls):
        cls.db = Database(cls.engine)
        cls.db.load()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    @staticmethod
    def as_text(rows):
        return [{k: str(v) for k, v in r.items()} for r in rows]

    def test_returns_only_the_last_select(self):
        self.assertEqual(self.as_text(self.db.query(TWO_SELECTS)),
                         [{"second_result": "2", "tag": "b"}])

    def test_statements_share_one_session(self):
        self.assertEqual(self.as_text(self.db.query(MULTI)), [{"doubled": "10", "label": "x"}])

    def test_semicolons_in_strings_and_comments(self):
        self.assertEqual(self.as_text(self.db.query(TRICKY)), [{"text_with_semicolon": "a;b"}])

    def test_select_with_no_rows_returns_empty_list(self):
        self.assertEqual(self.db.query("SELECT vendor_id FROM vendors WHERE 1 = 0;"), [])


class SQLiteDb(DbMixin, unittest.TestCase):
    engine = "sqlite"


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "set DATABASE_URL to test PostgreSQL")
class PostgresDb(DbMixin, unittest.TestCase):
    engine = "postgres"


if __name__ == "__main__":
    unittest.main()
