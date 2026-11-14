-- 4.1 Segregation of duties: the person who set up a vendor approves its payments
-- Risk     : one person can create a vendor (including its bank account)
--            and then approve payments to it. That is everything needed
--            to pay a fictitious vendor, with nobody else involved.
-- Criteria : the user who created a vendor in the vendor master never
--            approves payments to that vendor.
-- Method   : join payments to the vendor master and keep payments whose
--            approver is the vendor's creator. Join users to show who it
--            is and their role.
-- Output   : one row per payment.
-- Limits   : shows that the conflict happened, not that anything was
--            wrong with the payments. The next step is to check that each
--            vendor is real (registration, tax ID, bank details) and that
--            the goods or services were received.

SELECT
    p.payment_id,
    p.payment_date,
    p.amount,
    v.vendor_id,
    v.vendor_name,
    v.created_date AS vendor_created_date,
    v.created_by   AS vendor_created_by,
    p.approved_by  AS payment_approved_by,
    u.username,
    u.role
FROM payments p
JOIN vendors v    ON v.vendor_id = p.vendor_id
LEFT JOIN users u ON u.user_id = p.approved_by
WHERE p.approved_by = v.created_by
ORDER BY v.vendor_id, p.payment_date, p.payment_id;
