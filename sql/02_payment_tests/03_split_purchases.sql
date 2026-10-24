-- 2.3 Split purchases: one order broken into several to stay under a limit
-- Risk     : a purchase that needs Manager approval (over 10,000) is split
--            into smaller POs that an Officer can approve alone, bypassing
--            the approval control.
-- Criteria : two or more POs by the same person to the same vendor within
--            3 days, each at or below the 10,000 threshold, whose combined
--            value is above it.
-- Method   : self-join on raiser + vendor with a +/- 3 day window, then
--            GROUP BY each PO and HAVING to keep only clusters of 2+ POs
--            whose total exceeds the threshold. Every PO in a cluster is
--            listed so the whole pattern is visible.
-- Output   : one row per PO in a split cluster, with the cluster's size and
--            total, and the approver's own limit for comparison.
-- Limits   : splits across different raisers, or spread over more than
--            3 days, need a wider window or a vendor-only grouping.

WITH params AS (
    SELECT 10000.00 AS threshold, 3 AS window_days
),
small_pos AS (
    SELECT po.*
    FROM v_purchase_orders po
    CROSS JOIN params
    WHERE po.amount <= params.threshold
),
clusters AS (
    SELECT
        a.po_id,
        COUNT(*)      AS pos_in_cluster,
        SUM(b.amount) AS cluster_total
    FROM small_pos a
    JOIN small_pos b
      ON  b.raised_by = a.raised_by
      AND b.vendor_id = a.vendor_id
    CROSS JOIN params
    WHERE b.po_day BETWEEN a.po_day - params.window_days AND a.po_day + params.window_days
    GROUP BY a.po_id
    HAVING COUNT(*) >= 2
)
SELECT
    po.po_id,
    po.vendor_id,
    po.raised_by,
    po.approved_by,
    po.po_date,
    po.amount,
    c.pos_in_cluster,
    ROUND(c.cluster_total, 2) AS cluster_total,
    al.max_approval           AS approver_limit
FROM clusters c
JOIN purchase_orders po ON po.po_id = c.po_id
LEFT JOIN users u            ON u.user_id = po.approved_by
LEFT JOIN approval_limits al ON al.role = u.role
CROSS JOIN params
WHERE c.cluster_total > params.threshold
ORDER BY po.raised_by, po.vendor_id, po.po_date, po.po_id;
