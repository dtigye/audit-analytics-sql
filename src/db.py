"""Load the dataset into SQLite or PostgreSQL and run SQL files against it.

SQLite needs nothing installed. PostgreSQL uses the `psql` command-line
client and a connection URL in the DATABASE_URL environment variable, e.g.
    DATABASE_URL=postgresql://postgres:postgres@localhost:5432/audit
"""

from __future__ import annotations

import csv
import io
import os
import shutil
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SQL = ROOT / "sql"
SCHEMA = SQL / "schema.sql"
SQLITE_PATH = ROOT / "audit.db"

TABLES = ["employees", "users", "approval_limits", "vendors", "purchase_orders",
          "invoices", "payments", "journal_entries", "extract_control_totals"]


def _rows(table: str) -> tuple[list[str], list[list]]:
    with open(DATA / f"{table}.csv", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        header = next(r)
        return header, [[v if v != "" else None for v in row] for row in r]


class Database:
    """Thin wrapper so the same calls work on both engines."""

    def __init__(self, engine: str):
        if engine not in ("sqlite", "postgres"):
            raise ValueError("engine must be 'sqlite' or 'postgres'")
        self.engine = engine
        if engine == "postgres":
            self.url = os.environ.get("DATABASE_URL")
            if not self.url:
                raise RuntimeError("Set DATABASE_URL to use PostgreSQL")
            if not shutil.which("psql"):
                raise RuntimeError("The psql client is required for PostgreSQL")
        else:
            self.conn: sqlite3.Connection | None = None

    # ------------------------------------------------------------------ load
    def load(self) -> None:
        if self.engine == "sqlite":
            if SQLITE_PATH.exists():
                SQLITE_PATH.unlink()
            self.conn = sqlite3.connect(SQLITE_PATH)
            self.conn.executescript(SCHEMA.read_text(encoding="utf-8"))
            for t in TABLES:
                header, rows = _rows(t)
                marks = ",".join("?" * len(header))
                self.conn.executemany(f"INSERT INTO {t} ({','.join(header)}) VALUES ({marks})", rows)
            self.conn.commit()
        else:
            script = [SCHEMA.read_text(encoding="utf-8")]
            for t in TABLES:
                header = _rows(t)[0]
                path = (DATA / f"{t}.csv").as_posix()
                script.append(f"\\copy {t} ({','.join(header)}) FROM '{path}' WITH (FORMAT csv, HEADER true)")
            self._psql("\n".join(script))

    # ----------------------------------------------------------------- query
    def query(self, sql: str) -> list[dict]:
        """Run SQL (one or more statements) in a single session; return the rows
        of the last statement as dicts. Behaves the same on both engines."""
        if self.engine == "sqlite":
            if self.conn is None:
                self.conn = sqlite3.connect(SQLITE_PATH)
            statements = [s for s in _split(sql) if s.strip()]
            cur = None
            for s in statements:
                cur = self.conn.execute(s)
            if cur is None or cur.description is None:
                return []
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        # PostgreSQL: psql prints every result set, so earlier statements'
        # output is redirected to the null device (\o) and only the last
        # statement is printed. One psql process = one session, so temporary
        # views or tables created earlier in the file are still visible.
        statements = [s.strip() for s in _split(sql) if s.strip()]
        if not statements:
            return []
        devnull = os.devnull.replace("\\", "/")
        script = ""
        if len(statements) > 1:
            script += f"\\o {devnull}\n" + ";\n".join(statements[:-1]) + ";\n\\o\n"
        script += statements[-1] + ";\n"
        out = self._psql(script, csv_out=True)
        return list(csv.DictReader(io.StringIO(out))) if out.strip() else []

    def run_file(self, path: Path) -> list[dict]:
        return self.query(path.read_text(encoding="utf-8"))

    def close(self) -> None:
        if self.engine == "sqlite" and self.conn is not None:
            self.conn.close()
            self.conn = None

    def _psql(self, script: str, csv_out: bool = False) -> str:
        cmd = ["psql", self.url, "-X", "-q", "-v", "ON_ERROR_STOP=1"]
        if csv_out:
            cmd.append("--csv")
        res = subprocess.run(cmd, input=script, capture_output=True, text=True, cwd=ROOT)
        if res.returncode != 0:
            raise RuntimeError(f"psql failed: {res.stderr.strip()}")
        return res.stdout


def _split(sql: str) -> list[str]:
    """Split on semicolons outside quotes and comments (enough for this project's SQL)."""
    out, buf, quote, i = [], [], False, 0
    while i < len(sql):
        c = sql[i]
        if not quote and sql.startswith("--", i):
            j = sql.find("\n", i)
            i = len(sql) if j == -1 else j
            continue
        if c == "'":
            quote = not quote
        if c == ";" and not quote:
            out.append("".join(buf))
            buf = []
        else:
            buf.append(c)
        i += 1
    out.append("".join(buf))
    return out
