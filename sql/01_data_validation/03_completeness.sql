-- 1.3 Completeness of key fields
-- Purpose : confirm the fields the audit tests rely on are populated.
-- Criteria: no blank values in fields used later (bank accounts, addresses,
--           amounts, dates, user fields).
-- Output  : one row per field checked with the count of blank values.

SELECT 'vendors' AS table_name, 'bank_account' AS field,
       SUM(CASE WHEN bank_account IS NULL OR bank_account = '' THEN 1 ELSE 0 END) AS blank_count,
       COUNT(*) AS total_records
FROM vendors
UNION ALL
SELECT 'vendors', 'address',
       SUM(CASE WHEN address IS NULL OR address = '' THEN 1 ELSE 0 END), COUNT(*) FROM vendors
UNION ALL
SELECT 'vendors', 'tax_id',
       SUM(CASE WHEN tax_id IS NULL OR tax_id = '' THEN 1 ELSE 0 END), COUNT(*) FROM vendors
UNION ALL
SELECT 'employees', 'bank_account',
       SUM(CASE WHEN bank_account IS NULL OR bank_account = '' THEN 1 ELSE 0 END), COUNT(*) FROM employees
UNION ALL
SELECT 'employees', 'address',
       SUM(CASE WHEN address IS NULL OR address = '' THEN 1 ELSE 0 END), COUNT(*) FROM employees
UNION ALL
SELECT 'invoices', 'invoice_number',
       SUM(CASE WHEN invoice_number IS NULL OR invoice_number = '' THEN 1 ELSE 0 END), COUNT(*) FROM invoices
UNION ALL
SELECT 'payments', 'amount',
       SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END), COUNT(*) FROM payments
UNION ALL
SELECT 'journal_entries', 'approved_by',
       SUM(CASE WHEN approved_by IS NULL OR approved_by = '' THEN 1 ELSE 0 END), COUNT(*) FROM journal_entries
ORDER BY table_name, field;
