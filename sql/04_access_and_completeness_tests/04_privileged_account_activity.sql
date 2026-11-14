-- 4.4 Administrator accounts used for business transactions
-- Risk     : administrator (privileged) accounts can change data, settings
--            and other users' access. If they are also used to post
--            transactions, one account can both change the system and
--            move money, and a generic account hides who did it.
-- Criteria : privileged accounts are used only for system administration.
--            They do not create, approve or release business
--            transactions.
-- Method   : the same activity list as test 4.3 (every user column in
--            every table, turned into rows with UNION ALL), joined to
--            users and filtered to is_privileged = 1. A CASE shows when
--            the account has no named person behind it.
-- Output   : one row per action by a privileged account.
-- Limits   : covers the transactions in this extract only. System logs
--            (configuration changes, user-access changes) are outside it
--            and need a separate review.

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
    CASE WHEN u.employee_id IS NULL
         THEN 'Generic account: no named person'
         ELSE 'Named administrator: ' || u.employee_id
    END AS account_owner
FROM activity a
JOIN users u ON u.user_id = a.user_id
WHERE u.is_privileged = 1
ORDER BY a.action_date, a.record_id;
