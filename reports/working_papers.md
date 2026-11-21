# Audit working papers

Northgate Regional Agency (fictional), financial year 2025/26. **Synthetic data.**

One paper per finding, in the condition / criteria / cause / effect / recommendation format. Condition and value come from the data; criteria are taken from the query header. Possible causes, effect and recommendation are the auditor's judgement and would be confirmed with management before reporting.

## WP-1.2

**Broken references in the extract** · Rating: Medium · Status: draft, management response pending

- **Test:** [`01_data_validation/02_referential_integrity.sql`](../sql/01_data_validation/02_referential_integrity.sql)
- **Condition:** 4 exception(s), value 11,213.06. Records: INV01201, PAY90001, PAY90002, PO00041
- **Criteria:** every reference resolves to an existing record.
- **Possible causes (to confirm):** Extract taken before all records were posted; records deleted after payment; vendor or user master incomplete.
- **Effect:** Payments and approvals that cannot be traced to a valid invoice, vendor or user; later tests may be incomplete until resolved.
- **Recommendation:** Obtain the missing records or a written explanation from the system owner before relying on the payment tests; add referential checks to the extract process.

## WP-2.1

**Invoices paid more than once** · Rating: High · Status: draft, management response pending

- **Test:** [`02_payment_tests/01_duplicate_payments_exact.sql`](../sql/02_payment_tests/01_duplicate_payments_exact.sql)
- **Condition:** 4 exception(s), value 7,314.07. Records: PAY01182, PAY01183, PAY01184, PAY01185
- **Criteria:** each invoice is paid once. Any second or later payment of the same invoice_id is an exception.
- **Possible causes (to confirm):** Payment run re-processed; invoice re-submitted by the vendor; no system block on paying an already-paid invoice.
- **Effect:** Money paid out twice for the same goods or services.
- **Recommendation:** Recover the duplicate amounts from the vendors; configure the system to block payment of an invoice already marked paid.

## WP-2.2

**Same bill paid twice under a re-keyed invoice number** · Rating: High · Status: draft, management response pending

- **Test:** [`02_payment_tests/02_duplicate_payments_near.sql`](../sql/02_payment_tests/02_duplicate_payments_near.sql)
- **Condition:** 3 exception(s), value 12,885.52. Records: PAY01186, PAY01187, PAY01188
- **Criteria:** two payments to the same vendor for exactly the same amount within 30 days, against different invoice records, need explaining. Matching invoice numbers once punctuation is removed make a duplicate very likely.
- **Possible causes (to confirm):** Invoice number re-typed without punctuation, so the duplicate-invoice check treated it as new.
- **Effect:** Duplicate payments that the system's own control does not detect.
- **Recommendation:** Recover the amounts; normalise invoice numbers (case and punctuation) before the duplicate check runs.

## WP-2.3

**Purchases split to stay within an approval limit** · Rating: High · Status: draft, management response pending

- **Test:** [`02_payment_tests/03_split_purchases.sql`](../sql/02_payment_tests/03_split_purchases.sql)
- **Condition:** 8 exception(s), value 77,905.70. Records: PO00901, PO00902, PO00903, PO00904, PO00905, PO00906, PO00907, PO00908
- **Criteria:** two or more POs by the same person to the same vendor within 3 days, each at or below the 10,000 threshold, whose combined value is above it.
- **Possible causes (to confirm):** Requesters avoiding the higher approval level; approver not seeing related POs together.
- **Effect:** Purchases above 10,000 approved without the required authority.
- **Recommendation:** Review each cluster with the budget holder; flag same-vendor POs by one raiser within a few days whose total exceeds the limit.

## WP-2.4

**Payments to inactive or unapproved vendors** · Rating: High · Status: draft, management response pending

- **Test:** [`02_payment_tests/04_payments_to_unapproved_vendors.sql`](../sql/02_payment_tests/04_payments_to_unapproved_vendors.sql)
- **Condition:** 4 exception(s), value 26,808.31. Records: PAY01189, PAY01190, PAY01191, PAY01192
- **Criteria:** payments go only to vendors with status 'Active' and approved = 1 in the vendor master.
- **Possible causes (to confirm):** Vendor status not checked at payment; due diligence not completed before first use.
- **Effect:** Money paid to vendors the agency has not verified or has stopped using.
- **Recommendation:** Confirm the vendors and the goods received; block payment to vendors that are not Active and approved.

## WP-2.5

**Large round-sum payments** · Rating: Medium · Status: draft, management response pending

- **Test:** [`02_payment_tests/05_round_sum_payments.sql`](../sql/02_payment_tests/05_round_sum_payments.sql)
- **Condition:** 5 exception(s), value 138,000.00. Records: PAY01193, PAY01194, PAY01195, PAY01196, PAY01197
- **Criteria:** payments of 5,000 or more that are an exact multiple of 1,000.
- **Possible causes (to confirm):** Advances, deposits or fixed fees (legitimate); estimates or invented invoices (not).
- **Effect:** Higher risk that the amount is not supported by an actual invoice.
- **Recommendation:** Inspect supporting invoices and contracts; document the basis for each round sum.

## WP-3.1

**Vendors sharing a bank account or address with staff** · Rating: High · Status: draft, management response pending

- **Test:** [`03_vendor_and_timing_tests/01_vendor_employee_matches.sql`](../sql/03_vendor_and_timing_tests/01_vendor_employee_matches.sql)
- **Condition:** 4 exception(s), value 199,521.89. Records: V010, V023, V037, V059
- **Criteria:** no vendor shares a bank account or a postal address with a member of staff, unless the conflict has been declared.
- **Possible causes (to confirm):** Undeclared conflict of interest; employee-controlled vendor.
- **Effect:** Public money may be paid to staff or their associates.
- **Recommendation:** Check the conflict-of-interest register and who set up each vendor; require independent vendor set-up and periodic staff-vendor matching.

## WP-3.3

**One vendor's invoices cluster just under the approval limit** · Rating: High · Status: draft, management response pending

- **Test:** [`03_vendor_and_timing_tests/03_benford_vendor_outliers.sql`](../sql/03_vendor_and_timing_tests/03_benford_vendor_outliers.sql)
- **Condition:** 18 exception(s), value 171,074.84. Records: INV01214, INV01215, INV01216, INV01217, INV01218, INV01219, INV01220, INV01221 …
- **Criteria:** for a vendor with enough invoices, no first digit should appear far more often than Benford predicts.
- **Possible causes (to confirm):** Invoices sized to avoid the higher approval level; inflated or invented invoices.
- **Effect:** Purchases that should have needed senior approval avoided it.
- **Recommendation:** Inspect the invoices and goods received; review the vendor's contract and pricing; add the vendor to targeted monitoring.

## WP-3.4

**Manual journals posted at weekends or at night** · Rating: Medium · Status: draft, management response pending

- **Test:** [`03_vendor_and_timing_tests/04_out_of_hours_journals.sql`](../sql/03_vendor_and_timing_tests/04_out_of_hours_journals.sql)
- **Condition:** 6 exception(s), value 180,484.48. Records: JE01201, JE01202, JE01203, JE01204, JE01205, JE01206
- **Criteria:** manual journals are posted on working days (Monday to Friday) between 07:00 and 20:00.
- **Possible causes (to confirm):** Year-end or catch-up work (legitimate); postings timed to avoid review (not).
- **Effect:** Higher risk of management override of controls through manual journals.
- **Recommendation:** Obtain the business reason and support for each journal; require prior approval for out-of-hours manual journals.

## WP-4.1

**Vendor creator approves payments to the same vendor** · Rating: High · Status: draft, management response pending

- **Test:** [`04_access_and_completeness_tests/01_vendor_creator_approves_payment.sql`](../sql/04_access_and_completeness_tests/01_vendor_creator_approves_payment.sql)
- **Condition:** 9 exception(s), value 33,520.07. Records: PAY00015, PAY00057, PAY00073, PAY00156, PAY00311, PAY00711, PAY00868, PAY01084 …
- **Criteria:** the user who created a vendor in the vendor master never approves payments to that vendor.
- **Possible causes (to confirm):** Vendor set-up and payment approval rights held by the same role.
- **Effect:** One person can create a vendor and approve paying it, with no one else involved.
- **Recommendation:** Confirm the vendors are genuine; separate vendor-master maintenance from payment approval in the role design.

## WP-4.2

**Journals approved by the person who created them** · Rating: High · Status: draft, management response pending

- **Test:** [`04_access_and_completeness_tests/02_same_person_both_steps.sql`](../sql/04_access_and_completeness_tests/02_same_person_both_steps.sql)
- **Condition:** 3 exception(s), value 17,522.08. Records: JE00102, JE00506, JE00910
- **Criteria:** for every purchase order, payment and manual journal, the two steps are done by two different users.
- **Possible causes (to confirm):** System allows self-approval of journals.
- **Effect:** The second-person check did not happen.
- **Recommendation:** Review the journals; configure the system to reject approval by the creator.

## WP-4.3

**Accounts used after they were disabled** · Rating: High · Status: draft, management response pending

- **Test:** [`04_access_and_completeness_tests/03_activity_after_leaving.sql`](../sql/04_access_and_completeness_tests/03_activity_after_leaving.sql)
- **Condition:** 3 exception(s), value 9,369.78. Records: JE01207, JE01208, PAY00002
- **Criteria:** no transaction is created, approved or released by a user after that user's account was disabled.
- **Possible causes (to confirm):** Account re-enabled or shared; disabled status not enforced in the finance system.
- **Effect:** Transactions attributed to people who had left; accountability lost.
- **Recommendation:** Find out who used the accounts; reconcile the leavers list with system access every month; investigate how a disabled account could post.

## WP-4.4

**Administrator accounts used to post transactions** · Rating: Medium · Status: draft, management response pending

- **Test:** [`04_access_and_completeness_tests/04_privileged_account_activity.sql`](../sql/04_access_and_completeness_tests/04_privileged_account_activity.sql)
- **Condition:** 2 exception(s), value 38,482.05. Records: JE01209, JE01210
- **Criteria:** privileged accounts are used only for system administration. They do not create, approve or release business transactions.
- **Possible causes (to confirm):** Admin accounts used for convenience; generic batch account without an owner.
- **Effect:** One account can change the system and post transactions; generic accounts hide who acted.
- **Recommendation:** Stop business postings from privileged accounts; give every account a named owner.

## WP-4.5

**Payments that do not agree with the general ledger** · Rating: High · Status: draft, management response pending

- **Test:** [`04_access_and_completeness_tests/05_subledger_to_gl_completeness.sql`](../sql/04_access_and_completeness_tests/05_subledger_to_gl_completeness.sql)
- **Condition:** 7 exception(s), value 12,586.95. Records: PAY00185, PAY00260, PAY00422, PAY00505, PAY00713, PAY01029, PAY01074
- **Criteria:** every payment in the AP subledger is posted to the GL once, in the same month, for the same amount.
- **Possible causes (to confirm):** Interface failures; manual GL entry with keying errors; month-end cut-off errors.
- **Effect:** Expenditure misstated in the accounts by month and in total.
- **Recommendation:** Post the missing items and correct the others before close; reconcile the AP subledger to the GL every month.
