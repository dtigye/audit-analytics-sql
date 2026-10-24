-- 2.1 Duplicate payments: same invoice paid more than once
-- Risk     : an invoice is settled twice (keying error, resubmitted payment
--            run, or deliberate fraud). Money leaves the agency with no
--            goods or services in return.
-- Criteria : each invoice is paid once. Any second or later payment of the
--            same invoice_id is an exception.
-- Method   : ROW_NUMBER() numbers the payments of each invoice in date
--            order; payment_seq > 1 means "not the first payment".
--            FIRST_VALUE() picks up the original payment for reference.
-- Output   : one row per duplicate payment, with the original it repeats.
-- Limits   : only catches re-use of the same invoice record. An invoice keyed
--            in twice under a different number is caught by 2.2.

WITH ranked AS (
    SELECT
        payment_id,
        invoice_id,
        vendor_id,
        amount,
        payment_date,
        pay_day,
        ROW_NUMBER()  OVER (PARTITION BY invoice_id ORDER BY pay_day, payment_id) AS payment_seq,
        FIRST_VALUE(payment_id)   OVER (PARTITION BY invoice_id ORDER BY pay_day, payment_id) AS first_payment_id,
        FIRST_VALUE(payment_date) OVER (PARTITION BY invoice_id ORDER BY pay_day, payment_id) AS first_payment_date,
        FIRST_VALUE(pay_day)      OVER (PARTITION BY invoice_id ORDER BY pay_day, payment_id) AS first_pay_day
    FROM v_payments
)
SELECT
    payment_id,
    invoice_id,
    vendor_id,
    amount,
    payment_date,
    first_payment_id,
    first_payment_date,
    pay_day - first_pay_day AS days_after_first
FROM ranked
WHERE payment_seq > 1
ORDER BY payment_id;
