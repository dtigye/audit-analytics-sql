"""Load the data and run every audit query, saving the results as CSV.

Usage:
    python -m src.run_sql                    # SQLite (default)
    python -m src.run_sql --engine postgres  # needs DATABASE_URL and psql

Results are written to results/<engine>/<folder>__<query>.csv and a
one-line summary per query is printed.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.db import ROOT, SQL, Database

RESULTS = ROOT / "results"


def query_files() -> list[Path]:
    """All numbered query folders (01_..., 02_...) in order."""
    return sorted(p for p in SQL.glob("[0-9][0-9]_*/*.sql"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine", choices=["sqlite", "postgres"], default="sqlite")
    args = ap.parse_args()

    db = Database(args.engine)
    db.load()
    out_dir = RESULTS / args.engine
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Loaded data into {args.engine}. Running {len(query_files())} queries:\n")
    for f in query_files():
        rows = db.run_file(f)
        name = f"{f.parent.name}__{f.stem}.csv"
        with open(out_dir / name, "w", newline="", encoding="utf-8") as fh:
            if rows:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
        print(f"  {f.parent.name}/{f.name:<38} {len(rows):>4} rows")
    db.close()
    print(f"\nResults written to results/{args.engine}/")


if __name__ == "__main__":
    main()
