-- 1.4 Period coverage
-- Purpose : confirm the extract covers the whole financial year
--           (1 Oct 2025 - 30 Sep 2026) with no missing months and nothing
--           outside the period.
-- Criteria: every month has activity; no transactions outside the year.
-- Output  : one row per month with payment and journal counts and values.
-- Note    : month keys are built with SUBSTR on the ISO date text, which
--           behaves the same in SQLite and PostgreSQL (dates cast to text).

WITH p AS (
    SELECT SUBSTR(CAST(payment_date AS VARCHAR(30)), 1, 7) AS month, amount FROM payments
),
j AS (
    SELECT SUBSTR(CAST(posted_at AS VARCHAR(30)), 1, 7) AS month, amount FROM journal_entries
),
months AS (
    SELECT month FROM p UNION SELECT month FROM j
)
SELECT
    m.month,
    (SELECT COUNT(*) FROM p WHERE p.month = m.month)                    AS payments,
    (SELECT ROUND(SUM(amount), 2) FROM p WHERE p.month = m.month)       AS payments_value,
    (SELECT COUNT(*) FROM j WHERE j.month = m.month)                    AS journals,
    (SELECT ROUND(SUM(amount), 2) FROM j WHERE j.month = m.month)       AS journals_value,
    CASE WHEN m.month < '2025-10' OR m.month > '2026-09' THEN 'OUTSIDE PERIOD' ELSE 'IN PERIOD' END
                                                                        AS period_status
FROM months m
ORDER BY m.month;
