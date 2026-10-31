-- 3.1 Vendors that share a bank account or address with an employee
-- Risk     : an employee sets up a vendor they control (a "ghost" or
--            conflicted vendor) and pays it. The bank account or address
--            in the vendor master is often the employee's own.
-- Criteria : no vendor shares a bank account or a postal address with a
--            member of staff, unless the conflict has been declared.
-- Method   : join vendors to employees twice, once on bank account and
--            once on address, and combine the results with UNION ALL.
--            Addresses are compared after UPPER() and removing commas,
--            full stops and spaces, so "117 Mill Close, Northgate" and
--            "117 mill close northgate" still match.
-- Output   : one row per vendor-employee match, with what matched.
-- Limits   : exact matches only. A different flat number or a misspelt
--            street needs fuzzy matching. A shared address can be
--            innocent (relatives, shared buildings) and is cleared by
--            checking the conflict-of-interest register.

WITH v AS (
    SELECT vendor_id, vendor_name, bank_account, address, status, created_by,
           UPPER(REPLACE(REPLACE(REPLACE(address, ',', ''), '.', ''), ' ', '')) AS address_key
    FROM vendors
),
e AS (
    SELECT employee_id, full_name, department, bank_account, address, leave_date,
           UPPER(REPLACE(REPLACE(REPLACE(address, ',', ''), '.', ''), ' ', '')) AS address_key
    FROM employees
)
SELECT v.vendor_id, v.vendor_name, v.status, v.created_by,
       e.employee_id, e.full_name, e.department,
       'Bank account' AS match_basis,
       v.bank_account AS matched_value
FROM v
JOIN e ON e.bank_account = v.bank_account
UNION ALL
SELECT v.vendor_id, v.vendor_name, v.status, v.created_by,
       e.employee_id, e.full_name, e.department,
       'Address' AS match_basis,
       v.address AS matched_value
FROM v
JOIN e ON e.address_key = v.address_key
ORDER BY match_basis, vendor_id;
