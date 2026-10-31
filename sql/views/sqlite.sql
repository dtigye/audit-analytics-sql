-- Helper views: SQLite version.
-- The ONLY place engine-specific SQL is allowed. sql/views/postgres.sql
-- defines the same views with the same columns and the same values, so
-- every audit query can use them and stay identical on both engines.
--
-- day numbers: whole days since 1 Jan 2000, so "within N days" becomes
-- simple integer arithmetic (b.day - a.day <= N) on both engines.

DROP VIEW IF EXISTS v_payments;
CREATE VIEW v_payments AS
SELECT p.*,
       CAST(julianday(p.payment_date) - julianday('2000-01-01') AS INTEGER) AS pay_day
FROM payments p;

DROP VIEW IF EXISTS v_purchase_orders;
CREATE VIEW v_purchase_orders AS
SELECT po.*,
       CAST(julianday(po.po_date) - julianday('2000-01-01') AS INTEGER) AS po_day
FROM purchase_orders po;

-- posted_dow: day of week, 0 = Sunday ... 6 = Saturday.
-- posted_hour: hour of the day, 0-23.
DROP VIEW IF EXISTS v_journal_entries;
CREATE VIEW v_journal_entries AS
SELECT je.*,
       CAST(strftime('%w', je.posted_at) AS INTEGER) AS posted_dow,
       CAST(strftime('%H', je.posted_at) AS INTEGER) AS posted_hour
FROM journal_entries je;
