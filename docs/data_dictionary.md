# Data dictionary

Northgate Regional Agency (fictional) · financial year 1 Oct 2025 – 30 Sep 2026 · amounts in US dollars.
Primary keys are declared; foreign keys are not enforced (see `sql/schema.sql`) and are tested by `sql/01_data_validation/02_referential_integrity.sql`.

## employees
| Column | Type | Description |
|---|---|---|
| employee_id | VARCHAR(10) | Primary key (E001…) |
| full_name | VARCHAR(80) | Fictional name |
| department | VARCHAR(40) | Department |
| job_title | VARCHAR(60) | Role in the organisation |
| bank_account | VARCHAR(20) | Salary bank account (compared with vendor accounts in Phase 3) |
| address | VARCHAR(120) | Home address (compared with vendor addresses in Phase 3) |
| hire_date | DATE | Start date |
| leave_date | DATE | Leaving date; blank if still employed |

## users
| Column | Type | Description |
|---|---|---|
| user_id | VARCHAR(10) | Primary key (U001…) |
| employee_id | VARCHAR(10) | Linked employee; blank for generic/system accounts |
| username | VARCHAR(30) | Login name |
| role | VARCHAR(30) | Clerk, Procurement Officer, Finance Officer, Accountant, Finance Manager, Director, Administrator |
| is_privileged | SMALLINT | 1 = administrator account |
| created_date | DATE | Account created |
| disabled_date | DATE | Account disabled (leavers); blank if active |

## approval_limits
| Column | Type | Description |
|---|---|---|
| role | VARCHAR(30) | Primary key |
| max_approval | NUMERIC(14,2) | Largest PO or payment the role may approve (0 = may not approve) |

Policy: purchase orders above **10,000** require a Finance Manager or Director.

## vendors
| Column | Type | Description |
|---|---|---|
| vendor_id | VARCHAR(10) | Primary key (V001…) |
| vendor_name | VARCHAR(80) | Fictional company name |
| tax_id | VARCHAR(15) | Tax identification number |
| bank_account | VARCHAR(20) | Account payments are sent to |
| address | VARCHAR(120) | Registered address |
| status | VARCHAR(10) | Active / Inactive / Blocked |
| approved | SMALLINT | 1 = passed vendor due diligence |
| created_by | VARCHAR(10) | User who created the vendor record |
| created_date | DATE | Date created |

## purchase_orders
| Column | Type | Description |
|---|---|---|
| po_id | VARCHAR(12) | Primary key |
| vendor_id | VARCHAR(10) | Vendor |
| department | VARCHAR(40) | Requesting department |
| po_date | DATE | Date raised |
| description | VARCHAR(120) | Goods or service category |
| amount | NUMERIC(14,2) | PO value |
| raised_by | VARCHAR(10) | User who raised it |
| approved_by | VARCHAR(10) | User who approved it |

## invoices
| Column | Type | Description |
|---|---|---|
| invoice_id | VARCHAR(12) | Primary key (system reference) |
| vendor_id | VARCHAR(10) | Vendor |
| po_id | VARCHAR(12) | Related PO; blank for non-PO invoices (utilities, subscriptions) |
| invoice_number | VARCHAR(20) | Number as printed by the vendor |
| invoice_date | DATE | Invoice date |
| amount | NUMERIC(14,2) | Invoice value |
| entered_by | VARCHAR(10) | Clerk who entered it |

## payments
| Column | Type | Description |
|---|---|---|
| payment_id | VARCHAR(12) | Primary key |
| invoice_id | VARCHAR(12) | Invoice settled |
| vendor_id | VARCHAR(10) | Vendor paid |
| payment_date | DATE | Value date |
| amount | NUMERIC(14,2) | Amount paid |
| approved_by | VARCHAR(10) | User who authorised the payment |
| released_by | VARCHAR(10) | User who released it to the bank |
| posted_at | TIMESTAMP | System posting time |

## journal_entries
| Column | Type | Description |
|---|---|---|
| je_id | VARCHAR(12) | Primary key |
| posted_at | TIMESTAMP | System posting time |
| account | VARCHAR(40) | General ledger account |
| description | VARCHAR(120) | Narrative |
| amount | NUMERIC(14,2) | Value |
| created_by | VARCHAR(10) | User who prepared it |
| approved_by | VARCHAR(10) | User who approved it |

## extract_control_totals
| Column | Type | Description |
|---|---|---|
| table_name | VARCHAR(30) | Table the totals relate to |
| record_count | INTEGER | Records reported by the source system |
| amount_total | NUMERIC(16,2) | Sum of `amount`; blank where the table has none |
