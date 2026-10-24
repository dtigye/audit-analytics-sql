-- 2.2 Near-duplicate payments: same vendor, same amount, different invoice
-- Risk     : the same bill is entered twice under a slightly different
--            invoice number ("INV-1023" and "INV1023"), so the system's
--            duplicate-invoice control does not stop it and it is paid twice.
-- Criteria : two payments to the same vendor for exactly the same amount
--            within 30 days, against different invoice records, need
--            explaining. Matching invoice numbers once punctuation is
--            removed make a duplicate very likely.
-- Method   : self-join: the payments table is joined to itself so each
--            payment ("later") can be compared with every earlier payment
--            ("earlier") to the same vendor. Invoice numbers are normalised
--            with UPPER() and REPLACE() to strip '-', '/', '.' and spaces.
-- Output   : one row per later payment of a matching pair, with the basis
--            of the match.
-- Limits   : exact-amount match only; a duplicate with a small difference
--            (e.g. VAT added) needs a tolerance band. Recurring fixed fees
--            (rent, subscriptions) can match legitimately and are cleared
--            by checking the invoices.

WITH params AS (
    SELECT 30 AS window_days
),
p AS (
    SELECT
        vp.payment_id, vp.vendor_id, vp.invoice_id, vp.amount, vp.payment_date, vp.pay_day,
        i.invoice_number,
        UPPER(REPLACE(REPLACE(REPLACE(REPLACE(i.invoice_number, '-', ''), '/', ''), '.', ''), ' ', ''))
            AS invoice_number_normalised
    FROM v_payments vp
    JOIN invoices i ON i.invoice_id = vp.invoice_id
)
SELECT
    later.payment_id,
    later.vendor_id,
    later.amount,
    later.payment_date,
    later.invoice_number,
    earlier.payment_id     AS earlier_payment_id,
    earlier.payment_date   AS earlier_payment_date,
    earlier.invoice_number AS earlier_invoice_number,
    later.pay_day - earlier.pay_day AS days_apart,
    CASE
        WHEN later.invoice_number_normalised = earlier.invoice_number_normalised
            THEN 'Same invoice number once punctuation is removed'
        ELSE 'Same vendor and amount only'
    END AS match_basis
FROM p later
JOIN p earlier
  ON  earlier.vendor_id  = later.vendor_id
  AND earlier.amount     = later.amount
  AND earlier.invoice_id <> later.invoice_id
  AND (earlier.pay_day < later.pay_day
       OR (earlier.pay_day = later.pay_day AND earlier.payment_id < later.payment_id))
CROSS JOIN params
WHERE later.pay_day - earlier.pay_day <= params.window_days
ORDER BY later.payment_id;
