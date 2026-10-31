-- 3.3 Benford by vendor: vendors whose amounts break the pattern
-- Risk     : one vendor's invoices are invented or inflated, for example
--            kept just under an approval limit. Across the whole
--            population the effect is diluted and invisible (test 3.2);
--            vendor by vendor it stands out.
-- Criteria : for a vendor with enough invoices, no first digit should
--            appear far more often than Benford predicts.
-- Method   : count each vendor's invoices by first digit and compare with
--            the Benford expectation for that vendor's invoice count. A
--            vendor-digit is flagged when the actual count is at least
--            3 times the expected count AND at least 5 invoices above it,
--            for vendors with 20+ invoices. The statistics use all of the
--            vendor's invoices; the invoices behind a flagged vendor-digit
--            are then listed for inspection if they are at or above the
--            materiality floor.
-- Output   : one row per invoice in a flagged vendor-digit group.
-- Limits   : the thresholds are judgement, documented in params. The
--            floor applies to the listing only (cutting small amounts out
--            of the statistics would distort Benford): a 943 invoice is
--            not the same risk as a 9,430 one. Benford flags where to
--            look; the invoices themselves decide whether there is a
--            problem.

WITH params AS (
    SELECT 1000.00 AS materiality_floor,
           20      AS min_invoices,
           3.0     AS ratio,
           5       AS min_excess
),
benford (digit, expected_pct) AS (
    VALUES (1, 30.10), (2, 17.61), (3, 12.49), (4, 9.69), (5, 7.92),
           (6, 6.69), (7, 5.80), (8, 5.12), (9, 4.58)
),
inv AS (
    SELECT i.invoice_id, i.vendor_id, i.invoice_date, i.amount,
           CAST(SUBSTR(CAST(i.amount AS TEXT), 1, 1) AS INTEGER) AS digit
    FROM invoices i
    WHERE i.amount >= 1    -- the first character must be a digit 1-9
),
vendor_totals AS (
    SELECT vendor_id, COUNT(*) AS n FROM inv GROUP BY vendor_id
),
vendor_digits AS (
    SELECT inv.vendor_id, inv.digit, COUNT(*) AS actual_count,
           vt.n * b.expected_pct / 100.0 AS expected_count, vt.n AS vendor_invoices
    FROM inv
    JOIN vendor_totals vt ON vt.vendor_id = inv.vendor_id
    JOIN benford b        ON b.digit = inv.digit
    GROUP BY inv.vendor_id, inv.digit, vt.n, b.expected_pct
),
flagged AS (
    SELECT vd.*
    FROM vendor_digits vd
    CROSS JOIN params
    WHERE vd.vendor_invoices >= params.min_invoices
      AND vd.actual_count >= params.ratio * vd.expected_count
      AND vd.actual_count - vd.expected_count >= params.min_excess
)
SELECT
    inv.invoice_id,
    inv.vendor_id,
    v.vendor_name,
    inv.invoice_date,
    inv.amount,
    inv.digit                       AS first_digit,
    f.actual_count                  AS vendor_digit_count,
    ROUND(f.expected_count, 1)      AS vendor_digit_expected,
    f.vendor_invoices
FROM flagged f
JOIN inv          ON inv.vendor_id = f.vendor_id AND inv.digit = f.digit
LEFT JOIN vendors v ON v.vendor_id = inv.vendor_id
CROSS JOIN params
WHERE inv.amount >= params.materiality_floor
ORDER BY inv.vendor_id, inv.invoice_date, inv.invoice_id;
