-- 2.4 Payments to inactive or unapproved vendors
-- Risk     : money is paid to a vendor that has been deactivated, or that
--            never passed due diligence (identity, tax and bank checks).
--            Classic route for fictitious-vendor fraud.
-- Criteria : payments go only to vendors with status 'Active' and
--            approved = 1 in the vendor master.
-- Method   : join payments to the vendor master and keep rows that break
--            either condition; CASE explains which one.
-- Output   : one row per payment, with the vendor's status and the reason.
-- Limits   : uses the vendor's status as at the extract date. A vendor
--            deactivated after a legitimate payment would need its status
--            history to clear it.

SELECT
    p.payment_id,
    p.payment_date,
    p.amount,
    p.approved_by,
    v.vendor_id,
    v.vendor_name,
    v.status,
    v.approved,
    v.created_date AS vendor_created_date,
    CASE
        WHEN v.status <> 'Active' AND v.approved = 0 THEN 'Vendor not active and not approved'
        WHEN v.status <> 'Active'                    THEN 'Vendor status: ' || v.status
        ELSE 'Vendor not approved (due diligence incomplete)'
    END AS reason
FROM payments p
JOIN vendors v ON v.vendor_id = p.vendor_id
WHERE v.status <> 'Active'
   OR v.approved = 0
ORDER BY p.payment_date, p.payment_id;
