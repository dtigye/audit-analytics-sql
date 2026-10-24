# Audit Analytics in SQL

[![tests](https://github.com/dtigye/audit-analytics-sql/actions/workflows/tests.yml/badge.svg)](https://github.com/dtigye/audit-analytics-sql/actions/workflows/tests.yml)

Data analytics tests an auditor runs over a public body's finance and access
records: duplicate payments, split purchases, payments to unapproved vendors,
vendor–employee conflicts, Benford's law, out-of-hours postings and
segregation-of-duties breaches. Every test is plain SQL that runs unchanged on
**SQLite and PostgreSQL**, and is checked against a known answer key.

> **All data is synthetic.** "Northgate Regional Agency" is fictional, the same
> organisation used in [ict-risk-register-and-kpi-dashboard](https://github.com/dtigye/ict-risk-register-and-kpi-dashboard).
> Nothing here comes from a real organisation.

## Roadmap

The project is being built in phases. Each phase is complete and tested on its own.

| Phase | Content | Status |
|---|---|---|
| 1 | Dataset, schema, and data validation before testing | ✅ Complete |
| 2 | Payment tests: duplicates, split purchases, unapproved/inactive vendors, round sums | ✅ Complete |
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

## Phase 2: Payment tests

Five tests over the year's 1,199 payments and 908 purchase orders. Each SQL
file starts with a header stating the **risk**, the **criteria** (what
"correct" looks like), the **method** and the **limits** of the test.

| Test | Risk it addresses | Exceptions | Value |
|---|---|---|---|
| [`01_duplicate_payments_exact`](sql/02_payment_tests/01_duplicate_payments_exact.sql) | The same invoice paid twice | 4 payments | 7,314.07 |
| [`02_duplicate_payments_near`](sql/02_payment_tests/02_duplicate_payments_near.sql) | A bill re-keyed under a slightly different invoice number (`046-00124` → `04600124`) and paid again | 3 payments | 12,885.52 |
| [`03_split_purchases`](sql/02_payment_tests/03_split_purchases.sql) | Orders split to stay under the 10,000 approval limit | 3 clusters, 8 POs | 77,905.70 |
| [`04_payments_to_unapproved_vendors`](sql/02_payment_tests/04_payments_to_unapproved_vendors.sql) | Payments to an inactive vendor, or one that never passed due diligence | 4 payments | 26,808.31 |
| [`05_round_sum_payments`](sql/02_payment_tests/05_round_sum_payments.sql) | Large exact round amounts that may not be backed by a real invoice | 5 payments | 138,000.00 |

**What the results say (sample data):**

- **20,199.59 was paid twice.** Seven duplicate payments, each 6 to 10 days after the original. The near-duplicates
  slipped past because the invoice number was re-typed without its hyphen, which is why the test normalises
  invoice numbers before comparing them. *Next step:* confirm with the vendors and recover the overpayments.
- **Three officers split orders** worth 19,595 to 29,481 into two or three POs of just under 10,000 each,
  over consecutive days, all approved by an officer whose own limit is 10,000. *Next step:* establish whether
  each cluster was one requirement and, if so, why Manager approval was avoided.
- **26,808.31 went to vendors that should not have been paid:** an inactive vendor (`V073`) and a new
  vendor that never completed due diligence (`V081`), one payment of which was over 10,000.
- **Five round-sum payments** totalling 138,000 need their invoices checked. A round figure is a prompt to
  look, not proof of a problem.

**SQL techniques used:** window functions (`ROW_NUMBER`, `FIRST_VALUE`), self-joins with a date window,
`GROUP BY … HAVING`, text normalisation with `UPPER`/`REPLACE`, and parameters held in a `params` CTE so
thresholds are set in one place.

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

**Portability rules used throughout:**
- Engine differences live in **one place**: [`sql/views/`](sql/views) has a SQLite and a PostgreSQL version
  of the same helper views (for example, a day number for date arithmetic). Every audit query uses the
  views and is identical on both engines.
- Flags stored as 0/1; `NULL` columns in `UNION`s cast explicitly (PostgreSQL requires it, SQLite does not).
- No `%` for "is this a round number": SQLite converts both sides to integers first, so
  `25000.37 % 1000` is `0` in SQLite but `0.37` in PostgreSQL.
- CI runs every test on both engines.

## Repository layout

```
data/                    synthetic CSV extract (regenerated by src/generate_data.py)
sql/schema.sql           portable DDL
sql/views/               helper views, one file per engine (the only engine-specific SQL)
sql/01_data_validation/  Phase 1 queries (one test per file, documented in its header)
sql/02_payment_tests/    Phase 2 queries
src/                     data generator, loader/runner for both engines
tests/                   answer key and tests for each phase
results/sqlite/          query outputs from the last run
docs/data_dictionary.md  table and column definitions
```

## Author

**Dominic Igye**: ICT operations, cybersecurity and IT governance ·
CBAP · E|CIH · [LinkedIn](https://www.linkedin.com/in/dominicti)

Licensed under the [MIT Licence](LICENSE).
