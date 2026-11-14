-- 4.5 Subledger to general ledger: did every payment reach the GL?
-- Risk     : the payables subledger and the general ledger disagree. A
--            payment that never posts understates expenditure; one posted
--            in the wrong month misstates both months; a mistyped amount
--            leaves the accounts wrong by the difference. The financial
--            statements are built from the GL, not the subledger.
-- Criteria : every payment in the AP subledger is posted to the GL once,
--            in the same month, for the same amount.
-- Method   : add up GL lines by source document (a payment can post in
--            more than one line), then LEFT JOIN from the payments so that
--            a payment with no GL lines still appears, with NULLs. A CASE
--            names the break. Months are compared as 'YYYY-MM' text, which
--            works the same on both engines.
-- Output   : one row per payment with a break, with what the GL shows.
-- Limits   : tests one direction only (subledger -> GL). The other
--            direction, GL lines with no payment behind them, is an
--            existence test. A difference that is a multiple of 9 (here
--            6,205.64 vs 6,250.64 = 45.00) usually means two digits were
--            swapped when keying.
-- Credit   : added after a reader's suggestion on LinkedIn.

WITH gl AS (
    SELECT source_doc,
           COUNT(*)                                        AS gl_lines,
           ROUND(SUM(amount), 2)                           AS gl_amount,
           MIN(SUBSTR(CAST(posting_date AS VARCHAR(30)), 1, 7)) AS gl_month,
           MIN(posting_date)                               AS gl_posting_date
    FROM gl_postings
    WHERE source_module = 'AP'
    GROUP BY source_doc
)
SELECT
    p.payment_id,
    p.payment_date,
    p.amount            AS payment_amount,
    gl.gl_posting_date,
    gl.gl_amount,
    ROUND(p.amount - COALESCE(gl.gl_amount, 0), 2) AS difference,
    CASE
        WHEN gl.source_doc IS NULL
            THEN 'Not posted to the GL'
        WHEN gl.gl_month <> SUBSTR(CAST(p.payment_date AS VARCHAR(30)), 1, 7)
            THEN 'Posted to the GL in a different month'
        ELSE 'Posted to the GL at a different amount'
    END AS break_type
FROM payments p
LEFT JOIN gl ON gl.source_doc = p.payment_id
WHERE gl.source_doc IS NULL
   OR gl.gl_month <> SUBSTR(CAST(p.payment_date AS VARCHAR(30)), 1, 7)
   OR ABS(p.amount - gl.gl_amount) >= 0.01
ORDER BY break_type, p.payment_date, p.payment_id;
