-- 1.1 Reconcile the extract to the source system's control totals
-- Purpose : confirm the data is complete and unaltered before any testing.
-- Criteria: record counts and amount totals in the extract equal the totals
--           reported by the source system when the extract was taken.
-- Output  : one row per table; status = 'MATCH' or 'DIFFERENCE'.

WITH extract_totals AS (
    SELECT 'employees' AS table_name, COUNT(*) AS record_count, CAST(NULL AS NUMERIC(16, 2)) AS amount_total FROM employees
    UNION ALL SELECT 'users', COUNT(*), CAST(NULL AS NUMERIC(16, 2)) FROM users
    UNION ALL SELECT 'approval_limits', COUNT(*), CAST(NULL AS NUMERIC(16, 2)) FROM approval_limits
    UNION ALL SELECT 'vendors', COUNT(*), CAST(NULL AS NUMERIC(16, 2)) FROM vendors
    UNION ALL SELECT 'purchase_orders', COUNT(*), ROUND(SUM(amount), 2) FROM purchase_orders
    UNION ALL SELECT 'invoices', COUNT(*), ROUND(SUM(amount), 2) FROM invoices
    UNION ALL SELECT 'payments', COUNT(*), ROUND(SUM(amount), 2) FROM payments
    UNION ALL SELECT 'journal_entries', COUNT(*), ROUND(SUM(amount), 2) FROM journal_entries
)
SELECT
    c.table_name,
    c.record_count                      AS reported_count,
    e.record_count                      AS extract_count,
    c.amount_total                      AS reported_total,
    e.amount_total                      AS extract_total,
    CASE
        WHEN e.record_count IS NULL OR c.record_count <> e.record_count THEN 'DIFFERENCE'
        WHEN c.amount_total IS NOT NULL
             AND ABS(c.amount_total - e.amount_total) >= 0.01 THEN 'DIFFERENCE'
        ELSE 'MATCH'
    END                                 AS status
FROM extract_control_totals c
LEFT JOIN extract_totals e ON e.table_name = c.table_name
ORDER BY c.table_name;
