# Audit Analytics in SQL

[![tests](https://github.com/dtigye/audit-analytics-sql/actions/workflows/tests.yml/badge.svg)](https://github.com/dtigye/audit-analytics-sql/actions/workflows/tests.yml)

Data analytics tests an auditor runs over a public body's finance and access
records: duplicate payments, split purchases, payments to unapproved vendors,
vendor–employee conflicts, Benford's law, out-of-hours postings and
segregation-of-duties breaches. Every test is plain SQL that runs unchanged on
**SQLite and PostgreSQL**.

> **All data is synthetic.** "Northgate Regional Agency" is fictional, the same
> organisation used in [ict-risk-register-and-kpi-dashboard](https://github.com/dtigye/ict-risk-register-and-kpi-dashboard).
> Nothing here comes from a real organisation.

## Roadmap

The project is being built in phases. Each phase is complete and tested on its own.

| Phase | Content | Status |
|---|---|---|
| 1 | Dataset, schema, and data validation before testing | ✅ Complete |
| 2 | Payment tests: duplicates, split purchases, unapproved/inactive vendors, round sums | Planned |
| 3 | Vendor and timing tests: vendor–employee matches, Benford's law, out-of-hours postings | Planned |
| 4 | Access tests: segregation of duties, leavers' activity, privileged accounts | Planned |
| 5 | Reporting: exceptions summary and findings written as audit working papers | Planned |

## Phase 1: Validate the data before testing it

Audit analytics is only as good as the extract it runs on. Before any
exception test, an auditor confirms the data is **complete**, **internally
consistent** and **covers the right period**. Phase 1 does exactly that.

| Query | What it checks | Result on the sample |
|---|---|---|
| [`01_reconcile_control_totals`](sql/01_data_validation/01_reconcile_control_totals.sql) | Record counts and amount totals equal the source system's control totals | ✅ All 8 tables match |
| [`02_referential_integrity`](sql/01_data_validation/02_referential_integrity.sql) | Every payment, invoice, PO and user reference points to a real record | ⚠️ 4 broken references |
| [`03_completeness`](sql/01_data_validation/03_completeness.sql) | Fields later tests depend on (bank accounts, addresses, approvers) are populated | ✅ No blanks |
| [`04_period_coverage`](sql/01_data_validation/04_period_coverage.sql) | Activity in all 12 months of FY 2025/26, nothing outside the year | ✅ 12 months, all in period |

**The four integrity exceptions** are the kind found in real extracts:

| Record | Problem | Why it matters |
|---|---|---|
| `PAY90001`, `PAY90002` | Payments reference invoices that are not in the invoice extract | Either the extract is incomplete or payments were made without an invoice. Must be resolved with management before relying on the payment tests. |
| `INV01201` | Invoice from vendor `V099`, which is not in the vendor master | Possible payment route to an unregistered vendor |
| `PO00041` | Purchase order approved by user `U999`, unknown to the system | Approval cannot be attributed to an authorised person |

Full outputs: [`results/sqlite/`](results/sqlite).

## The data

One financial year (1 Oct 2025 – 30 Sep 2026) for a fictional agency.

```mermaid
erDiagram
    EMPLOYEES ||--o| USERS : "has account"
    USERS }o--|| APPROVAL_LIMITS : "role"
    VENDORS ||--o{ PURCHASE_ORDERS : ""
    VENDORS ||--o{ INVOICES : ""
    PURCHASE_ORDERS ||--o{ INVOICES : "billed by"
    INVOICES ||--o{ PAYMENTS : "settled by"
    USERS ||--o{ PURCHASE_ORDERS : "raises / approves"
    USERS ||--o{ PAYMENTS : "approves / releases"
    USERS ||--o{ JOURNAL_ENTRIES : "creates / approves"
    USERS ||--o{ VENDORS : "creates"
```

| Table | Rows | Contents |
|---|---|---|
| `employees` | 120 | Staff with bank account and address (used for vendor–employee matching) |
| `users` | 41 | System accounts, roles, privileged flag, disabled date for leavers |
| `approval_limits` | 7 | Maximum amount each role may approve |
| `vendors` | 81 | Vendor master: bank account, address, status, due-diligence flag |
| `purchase_orders` | 908 | POs with raiser and approver |
| `invoices` | ~1,230 | PO and non-PO invoices |
| `payments` | ~1,200 | Payments with approver, releaser and posting time |
| `journal_entries` | ~1,200 | Manual journals with creator, approver and posting time |
| `extract_control_totals` | 8 | Counts and totals reported by the source system |

Column definitions: [`docs/data_dictionary.md`](docs/data_dictionary.md).

**How the data is built.** [`src/generate_data.py`](src/generate_data.py) creates a
clean population that follows the agency's controls, then plants a known set
of exceptions for every phase. Each planted record is listed in
[`tests/answer_key.csv`](tests/answer_key.csv), and the tests check that
each query finds **exactly** those records: nothing missed, no false positives.

## Run it

**SQLite** (nothing to install beyond Python 3.10+):

```bash
pip install -r requirements.txt
python -m src.run_sql          # loads data, runs all queries, writes results/sqlite/
python -m pytest               # or: python -m unittest
```

**PostgreSQL** (uses the `psql` client):

```bash
createdb audit
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/audit
python -m src.run_sql --engine postgres
python -m pytest               # now also runs the PostgreSQL tests
```

Or run any `.sql` file directly in DBeaver, pgAdmin or the `sqlite3` shell
after loading the data.

**Portability rules used throughout:** no engine-specific functions; flags
stored as 0/1; dates compared as ISO text where needed; `NULL` columns in
`UNION`s cast explicitly (PostgreSQL requires it, SQLite does not). CI runs
every test on both engines.

## Repository layout

```
data/                    synthetic CSV extract (regenerated by src/generate_data.py)
sql/schema.sql           portable DDL
sql/01_data_validation/  Phase 1 queries (one test per file, documented in its header)
src/                     data generator, loader/runner for both engines
tests/                   answer key and tests for each phase
results/sqlite/          query outputs from the last run
docs/data_dictionary.md  table and column definitions
```

## Author

**Dominic Igye**: ICT operations, cybersecurity and IT governance ·
CBAP · E|CIH · [LinkedIn](https://www.linkedin.com/in/dominicti)

Licensed under the [MIT Licence](LICENSE).
