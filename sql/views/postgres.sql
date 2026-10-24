-- Helper views: PostgreSQL version.
-- The ONLY place engine-specific SQL is allowed. sql/views/sqlite.sql
-- defines the same views with the same columns and the same values, so
-- every audit query can use them and stay identical on both engines.
--
-- day numbers: whole days since 1 Jan 2000, so "within N days" becomes
-- simple integer arithmetic (b.day - a.day <= N) on both engines.
-- (In PostgreSQL, subtracting two DATEs gives an integer number of days.)

DROP VIEW IF EXISTS v_payments;
CREATE VIEW v_payments AS
SELECT p.*,
       (p.payment_date - DATE '2000-01-01') AS pay_day
FROM payments p;

DROP VIEW IF EXISTS v_purchase_orders;
CREATE VIEW v_purchase_orders AS
SELECT po.*,
       (po.po_date - DATE '2000-01-01') AS po_day
FROM purchase_orders po;
