"""Phase 5: turn the test results into an exceptions summary and audit
working papers.

Usage:
    python -m src.report                    # SQLite (default)
    python -m src.report --engine postgres  # needs DATABASE_URL and psql

Writes:
    reports/exceptions_summary.csv   one row per test: exceptions and value
    reports/exceptions_summary.md    the same, as a readable table
    reports/working_papers.md        one working paper per finding

How it works: every exception query is run again, and each flagged record
is valued from its own table (payments, invoices, POs and journals at their
amount; a vendor at the total paid to it). The criteria in each working
paper are read from the query's own header, so the paper and the SQL can't
drift apart. Condition and value come from the data. Possible causes, effect
and recommendation are the auditor's judgement, written in FINDINGS below.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path

from src.db import ROOT, SQL, Database

REPORTS = ROOT / "reports"


@dataclass(frozen=True)
class Finding:
    ref: str            # working-paper reference
    query: str          # path under sql/
    title: str
    id_col: str         # column holding the flagged record's ID
    rating: str         # High / Medium / Low: auditor's judgement
    causes: str         # possible causes, to confirm with management
    effect: str
    recommendation: str


FINDINGS = [
    Finding("WP-1.2", "01_data_validation/02_referential_integrity.sql",
            "Broken references in the extract", "record_id", "Medium",
            "Extract taken before all records were posted; records deleted after payment; "
            "vendor or user master incomplete.",
            "Payments and approvals that cannot be traced to a valid invoice, vendor or user; "
            "later tests may be incomplete until resolved.",
            "Obtain the missing records or a written explanation from the system owner before "
            "relying on the payment tests; add referential checks to the extract process."),
    Finding("WP-2.1", "02_payment_tests/01_duplicate_payments_exact.sql",
            "Invoices paid more than once", "payment_id", "High",
            "Payment run re-processed; invoice re-submitted by the vendor; no system block on "
            "paying an already-paid invoice.",
            "Money paid out twice for the same goods or services.",
            "Recover the duplicate amounts from the vendors; configure the system to block "
            "payment of an invoice already marked paid."),
    Finding("WP-2.2", "02_payment_tests/02_duplicate_payments_near.sql",
            "Same bill paid twice under a re-keyed invoice number", "payment_id", "High",
            "Invoice number re-typed without punctuation, so the duplicate-invoice check "
            "treated it as new.",
            "Duplicate payments that the system's own control does not detect.",
            "Recover the amounts; normalise invoice numbers (case and punctuation) before the "
            "duplicate check runs."),
    Finding("WP-2.3", "02_payment_tests/03_split_purchases.sql",
            "Purchases split to stay within an approval limit", "po_id", "High",
            "Requesters avoiding the higher approval level; approver not seeing related POs "
            "together.",
            "Purchases above 10,000 approved without the required authority.",
            "Review each cluster with the budget holder; flag same-vendor POs by one raiser "
            "within a few days whose total exceeds the limit."),
    Finding("WP-2.4", "02_payment_tests/04_payments_to_unapproved_vendors.sql",
            "Payments to inactive or unapproved vendors", "payment_id", "High",
            "Vendor status not checked at payment; due diligence not completed before first use.",
            "Money paid to vendors the agency has not verified or has stopped using.",
            "Confirm the vendors and the goods received; block payment to vendors that are "
            "not Active and approved."),
    Finding("WP-2.5", "02_payment_tests/05_round_sum_payments.sql",
            "Large round-sum payments", "payment_id", "Medium",
            "Advances, deposits or fixed fees (legitimate); estimates or invented invoices "
            "(not).",
            "Higher risk that the amount is not supported by an actual invoice.",
            "Inspect supporting invoices and contracts; document the basis for each round sum."),
    Finding("WP-3.1", "03_vendor_and_timing_tests/01_vendor_employee_matches.sql",
            "Vendors sharing a bank account or address with staff", "vendor_id", "High",
            "Undeclared conflict of interest; employee-controlled vendor.",
            "Public money may be paid to staff or their associates.",
            "Check the conflict-of-interest register and who set up each vendor; require "
            "independent vendor set-up and periodic staff-vendor matching."),
    Finding("WP-3.3", "03_vendor_and_timing_tests/03_benford_vendor_outliers.sql",
            "One vendor's invoices cluster just under the approval limit", "invoice_id", "High",
            "Invoices sized to avoid the higher approval level; inflated or invented invoices.",
            "Purchases that should have needed senior approval avoided it.",
            "Inspect the invoices and goods received; review the vendor's contract and pricing; "
            "add the vendor to targeted monitoring."),
    Finding("WP-3.4", "03_vendor_and_timing_tests/04_out_of_hours_journals.sql",
            "Manual journals posted at weekends or at night", "je_id", "Medium",
            "Year-end or catch-up work (legitimate); postings timed to avoid review (not).",
            "Higher risk of management override of controls through manual journals.",
            "Obtain the business reason and support for each journal; require prior approval "
            "for out-of-hours manual journals."),
    Finding("WP-4.1", "04_access_and_completeness_tests/01_vendor_creator_approves_payment.sql",
            "Vendor creator approves payments to the same vendor", "payment_id", "High",
            "Vendor set-up and payment approval rights held by the same role.",
            "One person can create a vendor and approve paying it, with no one else involved.",
            "Confirm the vendors are genuine; separate vendor-master maintenance from payment "
            "approval in the role design."),
    Finding("WP-4.2", "04_access_and_completeness_tests/02_same_person_both_steps.sql",
            "Journals approved by the person who created them", "record_id", "High",
            "System allows self-approval of journals.",
            "The second-person check did not happen.",
            "Review the journals; configure the system to reject approval by the creator."),
    Finding("WP-4.3", "04_access_and_completeness_tests/03_activity_after_leaving.sql",
            "Accounts used after they were disabled", "record_id", "High",
            "Account re-enabled or shared; disabled status not enforced in the finance system.",
            "Transactions attributed to people who had left; accountability lost.",
            "Find out who used the accounts; reconcile the leavers list with system access "
            "every month; investigate how a disabled account could post."),
    Finding("WP-4.4", "04_access_and_completeness_tests/04_privileged_account_activity.sql",
            "Administrator accounts used to post transactions", "record_id", "Medium",
            "Admin accounts used for convenience; generic batch account without an owner.",
            "One account can change the system and post transactions; generic accounts hide "
            "who acted.",
            "Stop business postings from privileged accounts; give every account a named owner."),
    Finding("WP-4.5", "04_access_and_completeness_tests/05_subledger_to_gl_completeness.sql",
            "Payments that do not agree with the general ledger", "payment_id", "High",
            "Interface failures; manual GL entry with keying errors; month-end cut-off errors.",
            "Expenditure misstated in the accounts by month and in total.",
            "Post the missing items and correct the others before close; reconcile the AP "
            "subledger to the GL every month."),
]

# Which table each kind of record ID lives in, and its amount column.
_VALUE_SQL = {
    "PAY": "SELECT payment_id AS id, amount FROM payments",
    "INV": "SELECT invoice_id AS id, amount FROM invoices",
    "PO": "SELECT po_id AS id, amount FROM purchase_orders",
    "JE": "SELECT je_id AS id, amount FROM journal_entries",
    "V": "SELECT vendor_id AS id, SUM(amount) AS amount FROM payments GROUP BY vendor_id",
}


def criteria(query: str) -> str:
    """The text of the '-- Criteria' block in a query's header."""
    lines = (SQL / query).read_text(encoding="utf-8").splitlines()
    out, inside = [], False
    for line in lines:
        if not line.startswith("--"):
            break
        body = line[2:]
        m = re.match(r"\s*(\w+)\s*:\s*(.*)", body)
        if m:
            inside = m.group(1) == "Criteria"
            if inside:
                out.append(m.group(2).strip())
        elif inside and body.strip():
            out.append(body.strip())
    return " ".join(out)


def _prefix(record_id: str) -> str:
    return re.match(r"[A-Z]+", record_id).group(0)


def build(db: Database) -> list[dict]:
    """Run every finding's query and value its records."""
    values: dict[str, float] = {}
    for sql in _VALUE_SQL.values():
        values.update({r["id"]: float(r["amount"]) for r in db.query(sql + ";")})
    results = []
    for f in FINDINGS:
        rows = db.run_file(SQL / f.query)
        ids = sorted({r[f.id_col] for r in rows})
        results.append({
            "finding": f, "rows": rows, "ids": ids,
            "value": round(sum(values.get(i, 0.0) for i in ids), 2),
        })
    return results


def _money(x: float) -> str:
    return f"{x:,.2f}"


def write_summary(results: list[dict], out: Path) -> None:
    with open(out / "exceptions_summary.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ref", "finding", "rating", "exceptions", "value"])
        for r in results:
            f = r["finding"]
            w.writerow([f.ref, f.title, f.rating, len(r["ids"]), f"{r['value']:.2f}"])
    total_n = sum(len(r["ids"]) for r in results)
    total_v = sum(r["value"] for r in results)
    lines = [
        "# Exceptions summary",
        "",
        "Generated by `python -m src.report` from the synthetic dataset. Each record is valued "
        "from its own table (a vendor at the total paid to it). No record appears in more than "
        "one test, so the totals add up.",
        "",
        "**Value is the amount of the flagged records: what an auditor would examine, not an "
        "estimate of loss.** A flagged vendor's value includes payments that may be genuine, a "
        "round sum may be a legitimate deposit, and a GL break counts the whole payment, not "
        "just the misstatement.",
        "",
        "| Ref | Finding | Rating | Exceptions | Value |",
        "|---|---|---|---:|---:|",
    ]
    for r in results:
        f = r["finding"]
        lines.append(f"| [{f.ref}](working_papers.md#{f.ref.lower().replace('.', '')}) | "
                     f"{f.title} | {f.rating} | {len(r['ids'])} | {_money(r['value'])} |")
    lines += [f"| | **Total** | | **{total_n}** | **{_money(total_v)}** |", ""]
    (out / "exceptions_summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_working_papers(results: list[dict], out: Path) -> None:
    lines = [
        "# Audit working papers",
        "",
        "Northgate Regional Agency (fictional), financial year 2025/26. **Synthetic data.**",
        "",
        "One paper per finding, in the condition / criteria / cause / effect / recommendation "
        "format. Condition and value come from the data; criteria are taken from the query "
        "header. Possible causes, effect and recommendation are the auditor's judgement and "
        "would be confirmed with management before reporting.",
        "",
    ]
    for r in results:
        f = r["finding"]
        sample = ", ".join(r["ids"][:8]) + (" …" if len(r["ids"]) > 8 else "")
        lines += [
            f"## {f.ref}",
            "",
            f"**{f.title}** · Rating: {f.rating} · Status: draft, management response pending",
            "",
            f"- **Test:** [`{f.query}`](../sql/{f.query})",
            f"- **Condition:** {len(r['ids'])} exception(s), value {_money(r['value'])}. "
            f"Records: {sample}",
            f"- **Criteria:** {criteria(f.query)}",
            f"- **Possible causes (to confirm):** {f.causes}",
            f"- **Effect:** {f.effect}",
            f"- **Recommendation:** {f.recommendation}",
            "",
        ]
    (out / "working_papers.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine", choices=["sqlite", "postgres"], default="sqlite")
    args = ap.parse_args()
    db = Database(args.engine)
    db.load()
    results = build(db)
    db.close()
    REPORTS.mkdir(exist_ok=True)
    write_summary(results, REPORTS)
    write_working_papers(results, REPORTS)
    total = sum(len(r["ids"]) for r in results)
    print(f"{len(results)} findings, {total} exceptions. Written to reports/")


if __name__ == "__main__":
    main()
