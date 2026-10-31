-- 3.2 Benford's law: first-digit profile of all invoices
-- Risk     : invented or manipulated amounts. People making up numbers
--            spread first digits evenly, or cluster them just under a
--            limit; genuine financial amounts do not.
-- Criteria : in many natural financial datasets the first digit d appears
--            with probability log10(1 + 1/d): about 30.1% are 1s and
--            only 4.6% are 9s (Benford's law).
-- Method   : take the first character of each amount (as text), count by
--            digit and compare with the Benford percentage. The expected
--            percentages are typed in a VALUES list because SQLite builds
--            do not always include log10().
--            All invoices are included. Cutting off small amounts would
--            itself distort the profile: Benford's law only holds when
--            amounts are free to start at any size.
-- Output   : nine rows, one per digit, with actual and expected counts.
--            This is a profile, not an exception list: test 3.3 drills
--            down to vendors.
-- Limits   : Benford suits large populations of amounts that span several
--            orders of magnitude. It does not suit assigned numbers, fixed
--            prices or amounts with a built-in minimum or maximum.

WITH benford (digit, expected_pct) AS (
    VALUES (1, 30.10), (2, 17.61), (3, 12.49), (4, 9.69), (5, 7.92),
           (6, 6.69), (7, 5.80), (8, 5.12), (9, 4.58)
),
population AS (
    SELECT CAST(SUBSTR(CAST(i.amount AS TEXT), 1, 1) AS INTEGER) AS digit
    FROM invoices i
    WHERE i.amount >= 1    -- the first character must be a digit 1-9
),
totals AS (
    SELECT COUNT(*) AS n FROM population
)
SELECT
    b.digit,
    COUNT(p.digit)                                    AS actual_count,
    ROUND(100.0 * COUNT(p.digit) / t.n, 2)            AS actual_pct,
    b.expected_pct,
    ROUND(t.n * b.expected_pct / 100.0, 1)            AS expected_count,
    ROUND(100.0 * COUNT(p.digit) / t.n - b.expected_pct, 2) AS difference_pct
FROM benford b
CROSS JOIN totals t
LEFT JOIN population p ON p.digit = b.digit
GROUP BY b.digit, b.expected_pct, t.n
ORDER BY b.digit;
