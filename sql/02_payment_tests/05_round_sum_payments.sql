-- 2.5 Round-sum payments
-- Risk     : genuine invoices rarely total an exact round figure. Large
--            payments of exactly 15,000.00 or 50,000.00 can indicate
--            estimates, advances, or invented invoices.
-- Criteria : payments of 5,000 or more that are an exact multiple of 1,000.
-- Method   : amount = ROUND(amount / 1000.0, 0) * 1000 is true only for
--            whole thousands. (The % operator is NOT used: SQLite turns
--            both sides into integers first, so 25000.37 % 1000 = 0 and
--            every amount with cents would be wrongly flagged.)
-- Output   : one row per round-sum payment.
-- Limits   : a round amount is a prompt to look at the invoice, not proof
--            of a problem; deposits and fixed-fee contracts are often round.

WITH params AS (
    SELECT 5000.00 AS min_amount, 1000.00 AS round_unit
)
SELECT
    p.payment_id,
    p.payment_date,
    p.vendor_id,
    v.vendor_name,
    p.amount,
    p.approved_by
FROM payments p
LEFT JOIN vendors v ON v.vendor_id = p.vendor_id
CROSS JOIN params
WHERE p.amount >= params.min_amount
  AND p.amount = ROUND(p.amount / params.round_unit, 0) * params.round_unit
ORDER BY p.amount DESC, p.payment_id;
