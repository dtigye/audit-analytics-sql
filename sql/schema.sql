-- Audit analytics sample database: Northgate Regional Agency (fictional).
-- Portable DDL: runs unchanged on SQLite 3.35+ and PostgreSQL 13+.
--
-- Primary keys are declared. Foreign keys are deliberately NOT enforced:
-- audit work usually starts from system extracts where referential
-- integrity cannot be assumed, so integrity is tested by queries
-- (sql/01_data_validation) instead of guaranteed by the schema.
-- Flags are stored as SMALLINT 0/1 so the same SQL works on both engines.
-- All amounts are in US dollars.

-- Helper views (sql/views/) depend on these tables; PostgreSQL will not
-- drop a table while a view uses it, so the views are dropped first.
DROP VIEW IF EXISTS v_payments;
DROP VIEW IF EXISTS v_purchase_orders;
DROP VIEW IF EXISTS v_journal_entries;

DROP TABLE IF EXISTS extract_control_totals;
DROP TABLE IF EXISTS gl_postings;
DROP TABLE IF EXISTS journal_entries;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS purchase_orders;
DROP TABLE IF EXISTS vendors;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS approval_limits;

CREATE TABLE employees (
    employee_id   VARCHAR(10)  PRIMARY KEY,
    full_name     VARCHAR(80)  NOT NULL,
    department    VARCHAR(40)  NOT NULL,
    job_title     VARCHAR(60)  NOT NULL,
    bank_account  VARCHAR(20),
    address       VARCHAR(120),
    hire_date     DATE         NOT NULL,
    leave_date    DATE
);

CREATE TABLE users (
    user_id        VARCHAR(10) PRIMARY KEY,
    employee_id    VARCHAR(10),            -- NULL for generic/system accounts
    username       VARCHAR(30) NOT NULL,
    role           VARCHAR(30) NOT NULL,   -- see approval_limits
    is_privileged  SMALLINT    NOT NULL,   -- 1 = administrator account
    created_date   DATE        NOT NULL,
    disabled_date  DATE
);

CREATE TABLE approval_limits (
    role            VARCHAR(30)    PRIMARY KEY,
    max_approval    NUMERIC(14, 2) NOT NULL  -- largest PO/payment this role may approve
);

CREATE TABLE vendors (
    vendor_id     VARCHAR(10)  PRIMARY KEY,
    vendor_name   VARCHAR(80)  NOT NULL,
    tax_id        VARCHAR(15),
    bank_account  VARCHAR(20),
    address       VARCHAR(120),
    status        VARCHAR(10)  NOT NULL,   -- Active / Inactive / Blocked
    approved      SMALLINT     NOT NULL,   -- 1 = passed vendor due diligence
    created_by    VARCHAR(10)  NOT NULL,   -- users.user_id
    created_date  DATE         NOT NULL
);

CREATE TABLE purchase_orders (
    po_id        VARCHAR(12)    PRIMARY KEY,
    vendor_id    VARCHAR(10)    NOT NULL,
    department   VARCHAR(40)    NOT NULL,
    po_date      DATE           NOT NULL,
    description  VARCHAR(120)   NOT NULL,
    amount       NUMERIC(14, 2) NOT NULL,
    raised_by    VARCHAR(10)    NOT NULL,  -- users.user_id
    approved_by  VARCHAR(10)    NOT NULL   -- users.user_id
);

CREATE TABLE invoices (
    invoice_id      VARCHAR(12)    PRIMARY KEY,
    vendor_id       VARCHAR(10)    NOT NULL,
    po_id           VARCHAR(12),             -- NULL for non-PO invoices
    invoice_number  VARCHAR(20)    NOT NULL, -- as printed by the vendor
    invoice_date    DATE           NOT NULL,
    amount          NUMERIC(14, 2) NOT NULL,
    entered_by      VARCHAR(10)    NOT NULL
);

CREATE TABLE payments (
    payment_id    VARCHAR(12)    PRIMARY KEY,
    invoice_id    VARCHAR(12)    NOT NULL,
    vendor_id     VARCHAR(10)    NOT NULL,
    payment_date  DATE           NOT NULL,
    amount        NUMERIC(14, 2) NOT NULL,
    approved_by   VARCHAR(10)    NOT NULL,
    released_by   VARCHAR(10)    NOT NULL,
    posted_at     TIMESTAMP      NOT NULL
);

CREATE TABLE journal_entries (
    je_id        VARCHAR(12)    PRIMARY KEY,
    posted_at    TIMESTAMP      NOT NULL,
    account      VARCHAR(40)    NOT NULL,
    description  VARCHAR(120)   NOT NULL,
    amount       NUMERIC(14, 2) NOT NULL,
    created_by   VARCHAR(10)    NOT NULL,
    approved_by  VARCHAR(10)    NOT NULL
);

-- Record counts and amount totals reported by the source system when the
-- extract was taken. Used to confirm the extract is complete before testing.
-- General-ledger lines posted from the payables (AP) subledger:
-- one line per payment, carrying the payment ID as its source document.
CREATE TABLE gl_postings (
    gl_line_id     VARCHAR(12)    PRIMARY KEY,
    posting_date   DATE           NOT NULL,
    account        VARCHAR(40)    NOT NULL,
    source_module  VARCHAR(10)    NOT NULL,   -- AP = accounts payable subledger
    source_doc     VARCHAR(12)    NOT NULL,   -- payments.payment_id
    amount         NUMERIC(14, 2) NOT NULL
);

CREATE TABLE extract_control_totals (
    table_name    VARCHAR(30)    PRIMARY KEY,
    record_count  INTEGER        NOT NULL,
    amount_total  NUMERIC(16, 2)            -- NULL where the table has no amount
);
