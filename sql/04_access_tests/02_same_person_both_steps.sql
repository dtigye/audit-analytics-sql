-- 4.2 Segregation of duties: one person at both steps of a transaction
-- Risk     : a second person is the control. If the same user raises and
--            approves a purchase order, approves and releases a payment,
--            or creates and approves a journal, the second check never
--            happened.
-- Criteria : for every purchase order, payment and manual journal, the two
--            steps are done by two different users.
-- Method   : one SELECT per table, each keeping rows where the two user
--            columns are equal, combined with UNION ALL into one list.
--            Each half returns the same columns, in the same order.
-- Output   : one row per transaction, with which two steps were combined.
-- Limits   : catches the same user ID only. Two IDs used by one person
--            (a shared password, or a second account) look like two
--            people; test 4.4 and the user list help with that.

SELECT 'Purchase order' AS record_type, po.po_id AS record_id, po.po_date AS record_date,
       po.amount, po.raised_by AS user_id, 'Raised and approved' AS steps_combined
FROM purchase_orders po
WHERE po.raised_by = po.approved_by
UNION ALL
SELECT 'Payment', p.payment_id, p.payment_date,
       p.amount, p.approved_by, 'Approved and released'
FROM payments p
WHERE p.approved_by = p.released_by
UNION ALL
SELECT 'Journal', je.je_id, je.posted_date,
       je.amount, je.created_by, 'Created and approved'
FROM v_journal_entries je
WHERE je.created_by = je.approved_by
ORDER BY record_type, record_date, record_id;
