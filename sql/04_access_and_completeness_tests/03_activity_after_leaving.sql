-- 4.3 Accounts used after the user left
-- Risk     : a leaver's account is still being used, by the leaver or by
--            someone who knows the password. Every action it records is
--            attributed to a person who was no longer there.
-- Criteria : no transaction is created, approved or released by a user
--            after that user's account was disabled.
-- Method   : build one activity list ("who did what, and when") from every
--            table that records a user: vendors created, POs raised and
--            approved, invoices entered, payments approved and released,
--            journals created and approved. UNION ALL turns those eight
--            user columns into rows. Then join to users and keep actions
--            dated after the disabled date.
-- Output   : one row per action, with the date the account was disabled.
-- Limits   : the extract only records the disabled date, not the actual
--            leaving date; if the account was disabled late, actions
--            between leaving and disabling are missed. Payments are
--            dated by payment date. Activity on the disabled date itself
--            is allowed (handover day).

WITH activity AS (
    SELECT created_by  AS user_id, 'Created vendor'    AS action, vendor_id  AS record_id, created_date AS action_date FROM vendors
    UNION ALL
    SELECT raised_by,   'Raised PO',          po_id,      po_date      FROM purchase_orders
    UNION ALL
    SELECT approved_by, 'Approved PO',        po_id,      po_date      FROM purchase_orders
    UNION ALL
    SELECT entered_by,  'Entered invoice',    invoice_id, invoice_date FROM invoices
    UNION ALL
    SELECT approved_by, 'Approved payment',   payment_id, payment_date FROM payments
    UNION ALL
    SELECT released_by, 'Released payment',   payment_id, payment_date FROM payments
    UNION ALL
    SELECT created_by,  'Created journal',    je_id,      posted_date  FROM v_journal_entries
    UNION ALL
    SELECT approved_by, 'Approved journal',   je_id,      posted_date  FROM v_journal_entries
)
SELECT
    a.record_id,
    a.action,
    a.action_date,
    a.user_id,
    u.username,
    u.role,
    u.disabled_date
FROM activity a
JOIN users u ON u.user_id = a.user_id
WHERE u.disabled_date IS NOT NULL
  AND a.action_date > u.disabled_date
ORDER BY a.action_date, a.record_id;
