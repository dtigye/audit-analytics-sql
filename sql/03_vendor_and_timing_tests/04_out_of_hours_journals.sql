-- 3.4 Manual journals posted at weekends or out of hours
-- Risk     : journals posted when nobody is around to notice: to hide a
--            misstatement or a theft, or using someone else's login.
-- Criteria : manual journals are posted on working days (Monday to
--            Friday) between 07:00 and 20:00.
-- Method   : use the helper view v_journal_entries, which adds the day of
--            the week and the hour (the only engine-specific part, see
--            sql/views/), and keep entries outside those hours. A CASE
--            gives the reason in plain words.
-- Output   : one row per journal, with when it was posted and why it is
--            flagged.
-- Limits   : year-end close and system batch jobs legitimately run late;
--            exclude known batch users or agreed close dates before
--            reporting. Public holidays are not in the calendar here.

WITH params AS (
    SELECT 7 AS day_start_hour, 20 AS day_end_hour
)
SELECT
    je.je_id,
    je.posted_at,
    CASE je.posted_dow
        WHEN 0 THEN 'Sun' WHEN 1 THEN 'Mon' WHEN 2 THEN 'Tue' WHEN 3 THEN 'Wed'
        WHEN 4 THEN 'Thu' WHEN 5 THEN 'Fri' ELSE 'Sat'
    END AS posted_day,
    je.account,
    je.description,
    je.amount,
    je.created_by,
    je.approved_by,
    CASE
        WHEN je.posted_dow IN (0, 6) THEN 'Posted at the weekend'
        ELSE 'Posted outside working hours'
    END AS reason
FROM v_journal_entries je
CROSS JOIN params
WHERE je.posted_dow IN (0, 6)
   OR je.posted_hour <  params.day_start_hour
   OR je.posted_hour >= params.day_end_hour
ORDER BY je.posted_at, je.je_id;
