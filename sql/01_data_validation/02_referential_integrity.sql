-- 1.2 Referential integrity
-- Purpose : find records that point to something missing from the extract.
--           The schema does not enforce foreign keys (extracts rarely do),
--           so each relationship is tested here.
-- Criteria: every reference resolves to an existing record.
-- Output  : one row per broken reference (no rows = pass).

SELECT 'payments' AS table_name, p.payment_id AS record_id, 'invoice_id' AS field,
       p.invoice_id AS missing_value
FROM payments p LEFT JOIN invoices i ON i.invoice_id = p.invoice_id
WHERE i.invoice_id IS NULL

UNION ALL
SELECT 'payments', p.payment_id, 'vendor_id', p.vendor_id
FROM payments p LEFT JOIN vendors v ON v.vendor_id = p.vendor_id
WHERE v.vendor_id IS NULL

UNION ALL
SELECT 'invoices', i.invoice_id, 'vendor_id', i.vendor_id
FROM invoices i LEFT JOIN vendors v ON v.vendor_id = i.vendor_id
WHERE v.vendor_id IS NULL

UNION ALL
SELECT 'invoices', i.invoice_id, 'po_id', i.po_id
FROM invoices i LEFT JOIN purchase_orders po ON po.po_id = i.po_id
WHERE i.po_id IS NOT NULL AND po.po_id IS NULL

UNION ALL
SELECT 'purchase_orders', po.po_id, 'vendor_id', po.vendor_id
FROM purchase_orders po LEFT JOIN vendors v ON v.vendor_id = po.vendor_id
WHERE v.vendor_id IS NULL

UNION ALL
SELECT x.table_name, x.record_id, x.field, x.user_id
FROM (
    SELECT 'purchase_orders' AS table_name, po_id AS record_id, 'raised_by' AS field, raised_by AS user_id FROM purchase_orders
    UNION ALL SELECT 'purchase_orders', po_id, 'approved_by', approved_by FROM purchase_orders
    UNION ALL SELECT 'invoices', invoice_id, 'entered_by', entered_by FROM invoices
    UNION ALL SELECT 'payments', payment_id, 'approved_by', approved_by FROM payments
    UNION ALL SELECT 'payments', payment_id, 'released_by', released_by FROM payments
    UNION ALL SELECT 'journal_entries', je_id, 'created_by', created_by FROM journal_entries
    UNION ALL SELECT 'journal_entries', je_id, 'approved_by', approved_by FROM journal_entries
    UNION ALL SELECT 'vendors', vendor_id, 'created_by', created_by FROM vendors
) x
LEFT JOIN users u ON u.user_id = x.user_id
WHERE u.user_id IS NULL

ORDER BY table_name, record_id;
