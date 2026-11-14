"""Generate the synthetic finance and access dataset.

Northgate Regional Agency is fictional. Every person, vendor, account and
transaction below is invented by this script; none is drawn from or modelled
on a real organisation.

The data is built in two steps:
  1. a "clean" population that follows the agency's (fictional) controls;
  2. a small number of planted exceptions, each recorded in
     tests/answer_key.csv, so every audit test can be checked against a
     known answer.

Run:  python -m src.generate_data
The random seed is fixed: every run produces identical files.
"""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

SEED = 20261024
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ANSWER_KEY = ROOT / "tests" / "answer_key.csv"

FY_START = date(2025, 10, 1)
FY_END = date(2026, 9, 30)
PO_THRESHOLD = 10_000.00  # POs above this need Manager approval or higher

APPROVAL_LIMITS = {
    "Clerk": 0, "Procurement Officer": 10_000, "Finance Officer": 10_000,
    "Accountant": 0, "Finance Manager": 50_000, "Director": 250_000,
    "Administrator": 0,
}

FIRST = ["Amara", "Daniel", "Grace", "Samuel", "Fatima", "Joseph", "Esther", "Michael", "Ruth",
         "David", "Hannah", "Peter", "Zainab", "John", "Mary", "Ibrahim", "Sarah", "Paul",
         "Halima", "James", "Comfort", "Victor", "Joy", "Emmanuel", "Lydia", "Isaac", "Naomi",
         "Musa", "Rebecca", "Thomas"]
LAST = ["Adeyemi", "Okafor", "Bello", "Mensah", "Danjuma", "Eze", "Usman", "Ogunleye", "Abubakar",
        "Nwosu", "Okon", "Garba", "Balogun", "Ike", "Sani", "Afolabi", "Yakubu", "Chukwu", "Lawal",
        "Ndukwe", "Aliyu", "Ojo", "Bassey", "Akpan", "Musa"]
STREETS = ["Harbour Road", "Station Street", "Market Lane", "Hill View", "Riverside Avenue",
           "Mill Close", "Church Street", "Park Way", "Canal Road", "Orchard Drive",
           "Bridge Street", "Kingsway", "Garden Row", "Ridge Road", "Lake Crescent"]
TOWNS = ["Northgate", "Eastbrook", "Westfield", "Southmoor", "Highcliff"]
VENDOR_WORDS = ["Apex", "Bluebird", "Cedar", "Delta", "Evergreen", "Falcon", "Granite", "Horizon",
                "Ivory", "Juniper", "Keystone", "Lighthouse", "Meridian", "Northstar", "Oakfield",
                "Pinnacle", "Quartz", "Redwood", "Summit", "Trident", "Unity", "Vertex", "Willow",
                "Zenith"]
VENDOR_TRADES = [("IT Supplies", "IT equipment"), ("Office Solutions", "Office supplies"),
                 ("Facilities Services", "Facilities maintenance"), ("Consulting", "Advisory services"),
                 ("Print & Media", "Printing"), ("Logistics", "Courier and transport"),
                 ("Catering", "Catering"), ("Security Services", "Guarding services"),
                 ("Networks", "Network services"), ("Training", "Staff training")]
DEPARTMENTS = ["Finance", "Procurement", "ICT", "Human Resources", "Operations", "Communications",
               "Legal", "Planning"]
GL_ACCOUNTS = ["Accruals", "Prepayments", "Payroll control", "Depreciation", "Bank charges",
               "Suspense", "Inter-unit transfers", "Provision for doubtful debts"]


class Gen:
    def __init__(self, seed: int = SEED):
        self.rng = np.random.default_rng(seed)
        self.key: list[dict] = []

    # ---------------------------------------------------------------- helpers
    def choice(self, seq):
        return seq[int(self.rng.integers(len(seq)))]

    def amount(self, median: float = 2_500, sigma: float = 1.15, cap: float = 240_000) -> float:
        """Log-normal amounts spanning several orders of magnitude (Benford-like)."""
        while True:
            a = float(self.rng.lognormal(np.log(median), sigma))
            if 25 <= a <= cap:
                a = round(a, 2)
                if a % 1000 == 0 or a % 100 == 0:  # keep clean data free of round sums
                    a += 0.37
                return a

    def workday(self, start: date = FY_START, end: date = FY_END) -> date:
        span = (end - start).days
        while True:
            d = start + timedelta(days=int(self.rng.integers(span + 1)))
            if d.weekday() < 5:
                return d

    def office_time(self, d: date) -> datetime:
        minutes = int(self.rng.integers(8 * 60 + 15, 17 * 60 + 45))
        return datetime.combine(d, datetime.min.time()) + timedelta(minutes=minutes)

    def bank(self) -> str:
        return "".join(str(int(x)) for x in self.rng.integers(0, 10, 10))

    def plant(self, phase: int, test: str, table: str, record_id: str, note: str) -> None:
        self.key.append({"phase": phase, "test": test, "table": table,
                         "record_id": record_id, "note": note})


def build(seed: int = SEED) -> tuple[dict[str, list[dict]], list[dict]]:
    g = Gen(seed)
    used_banks: set[str] = set()
    used_addr: set[str] = set()

    def unique_bank() -> str:
        while True:
            b = g.bank()
            if b not in used_banks:
                used_banks.add(b)
                return b

    def unique_addr() -> str:
        while True:
            a = f"{int(g.rng.integers(1, 200))} {g.choice(STREETS)}, {g.choice(TOWNS)}"
            if a not in used_addr:
                used_addr.add(a)
                return a

    # ------------------------------------------------------------ employees
    employees = []
    names = set()
    for i in range(1, 121):
        while True:
            n = f"{g.choice(FIRST)} {g.choice(LAST)}"
            if n not in names:
                names.add(n)
                break
        hire = date(2010, 1, 1) + timedelta(days=int(g.rng.integers(0, 5300)))
        employees.append({
            "employee_id": f"E{i:03d}", "full_name": n, "department": g.choice(DEPARTMENTS),
            "job_title": "Staff", "bank_account": unique_bank(), "address": unique_addr(),
            "hire_date": hire.isoformat(), "leave_date": "",
        })

    # --------------------------------------------------------------- users
    # Finance and procurement system users, mapped to employees.
    roles = (["Clerk"] * 10 + ["Procurement Officer"] * 8 + ["Finance Officer"] * 8 +
             ["Accountant"] * 6 + ["Finance Manager"] * 5 + ["Director"] * 2)
    users = []
    for i, role in enumerate(roles, start=1):
        emp = employees[i - 1]
        emp["job_title"] = role
        emp["department"] = "Procurement" if role in ("Procurement Officer", "Clerk") and i % 2 else "Finance"
        users.append({"user_id": f"U{i:03d}", "employee_id": emp["employee_id"],
                      "username": emp["full_name"].lower().replace(" ", "."), "role": role,
                      "is_privileged": 0, "created_date": "2024-01-15", "disabled_date": ""})
    # Two administrator accounts and one shared/generic account
    n = len(users)
    admin_emp = employees[n]
    admin_emp["job_title"], admin_emp["department"] = "Systems Administrator", "ICT"
    users.append({"user_id": f"U{n + 1:03d}", "employee_id": admin_emp["employee_id"],
                  "username": "sysadmin1", "role": "Administrator", "is_privileged": 1,
                  "created_date": "2024-01-15", "disabled_date": ""})
    users.append({"user_id": f"U{n + 2:03d}", "employee_id": "", "username": "fin_batch",
                  "role": "Administrator", "is_privileged": 1, "created_date": "2024-01-15",
                  "disabled_date": ""})
    # Two leavers: accounts disabled during the year
    leavers = {"U030": date(2026, 3, 31), "U022": date(2026, 6, 30)}
    for u in users:
        if u["user_id"] in leavers:
            u["disabled_date"] = leavers[u["user_id"]].isoformat()
            emp = next(e for e in employees if e["employee_id"] == u["employee_id"])
            emp["leave_date"] = leavers[u["user_id"]].isoformat()

    by_role = {r: [u for u in users if u["role"] == r] for r in APPROVAL_LIMITS}

    def active(us: list[dict], on: date) -> list[dict]:
        return [u for u in us if not u["disabled_date"] or date.fromisoformat(u["disabled_date"]) > on]

    def approver_for(amount: float, on: date, exclude: set[str]) -> dict:
        pool = [u for r, lim in APPROVAL_LIMITS.items() if lim >= amount for u in by_role[r]]
        pool = [u for u in active(pool, on) if u["user_id"] not in exclude]
        return g.choice(pool)

    # -------------------------------------------------------------- vendors
    vendors = []
    vnames = set()
    creators = by_role["Procurement Officer"]
    for i in range(1, 81):
        while True:
            word, (trade, _) = g.choice(VENDOR_WORDS), g.choice(VENDOR_TRADES)
            name = f"{word} {trade} Ltd"
            if name not in vnames:
                vnames.add(name)
                break
        vendors.append({
            "vendor_id": f"V{i:03d}", "vendor_name": name,
            "tax_id": f"TIN{int(g.rng.integers(10_000_000, 99_999_999))}",
            "bank_account": unique_bank(), "address": unique_addr(),
            "status": "Active", "approved": 1,
            "created_by": g.choice(creators)["user_id"],
            "created_date": (date(2022, 1, 1) + timedelta(days=int(g.rng.integers(0, 1300)))).isoformat(),
        })
    for v in vendors[70:]:  # last ten: inactive, used only in earlier years
        v["status"] = "Inactive"
    active_vendors = [v for v in vendors if v["status"] == "Active"]

    # ------------------------------------- purchase orders, invoices, payments
    pos, invoices, payments = [], [], []
    raisers = by_role["Procurement Officer"] + by_role["Clerk"]
    releasers = by_role["Finance Officer"]
    last_po: dict[tuple[str, str], date] = {}
    po_n = inv_n = pay_n = 0

    def new_payment(inv: dict, vendor: dict, amount: float, pay_date: date, excl: set[str]) -> dict:
        nonlocal pay_n
        pay_n += 1
        appr = approver_for(max(amount, 10_000.01), pay_date, excl | {vendor["created_by"]})
        rel = g.choice([u for u in active(releasers, pay_date) if u["user_id"] != appr["user_id"]])
        p = {"payment_id": f"PAY{pay_n:05d}", "invoice_id": inv["invoice_id"],
             "vendor_id": vendor["vendor_id"], "payment_date": pay_date.isoformat(),
             "amount": f"{amount:.2f}", "approved_by": appr["user_id"],
             "released_by": rel["user_id"],
             "posted_at": g.office_time(pay_date).isoformat(sep=" ")}
        payments.append(p)
        return p

    while po_n < 900:
        vendor = g.choice(active_vendors)
        d = g.workday(FY_START, date(2026, 8, 31))
        raiser = g.choice(active(raisers, d))
        k = (raiser["user_id"], vendor["vendor_id"])
        if k in last_po and abs((d - last_po[k]).days) < 10:
            continue  # clean data: no repeat PO from same raiser to same vendor within 10 days
        amt = g.amount()
        if 8_000 <= amt <= PO_THRESHOLD:  # keep the band just under the threshold clean
            continue
        last_po[k] = d
        po_n += 1
        trade = next(t for w, t in VENDOR_TRADES if w in vendor["vendor_name"])
        appr = approver_for(amt, d, {raiser["user_id"]})
        po = {"po_id": f"PO{po_n:05d}", "vendor_id": vendor["vendor_id"],
              "department": g.choice(DEPARTMENTS), "po_date": d.isoformat(),
              "description": trade, "amount": f"{amt:.2f}",
              "raised_by": raiser["user_id"], "approved_by": appr["user_id"]}
        pos.append(po)
        inv_d = d + timedelta(days=int(g.rng.integers(3, 25)))
        inv_amt = amt if g.rng.random() < 0.85 else round(amt * float(g.rng.uniform(0.9, 1.0)), 2)
        if inv_amt % 100 == 0:
            inv_amt += 0.13
        inv_n += 1
        clerk = g.choice(active(by_role["Clerk"], inv_d))
        inv = {"invoice_id": f"INV{inv_n:05d}", "vendor_id": vendor["vendor_id"], "po_id": po["po_id"],
               "invoice_number": f"{vendor['vendor_id'][1:]}-{inv_n:05d}",
               "invoice_date": inv_d.isoformat(), "amount": f"{inv_amt:.2f}",
               "entered_by": clerk["user_id"]}
        invoices.append(inv)
        pay_d = inv_d + timedelta(days=int(g.rng.integers(14, 45)))
        while pay_d.weekday() >= 5:
            pay_d += timedelta(days=1)
        if pay_d <= FY_END:
            new_payment(inv, vendor, inv_amt, pay_d, {raiser["user_id"], clerk["user_id"]})

    # Non-PO invoices (utilities, subscriptions): small, recurring
    for _ in range(300):
        vendor = g.choice(active_vendors)
        d = g.workday(FY_START, date(2026, 8, 31))
        amt = g.amount(median=600, sigma=0.9, cap=7_500)
        inv_n += 1
        clerk = g.choice(active(by_role["Clerk"], d))
        inv = {"invoice_id": f"INV{inv_n:05d}", "vendor_id": vendor["vendor_id"], "po_id": "",
               "invoice_number": f"{vendor['vendor_id'][1:]}-{inv_n:05d}",
               "invoice_date": d.isoformat(), "amount": f"{amt:.2f}", "entered_by": clerk["user_id"]}
        invoices.append(inv)
        pay_d = d + timedelta(days=int(g.rng.integers(10, 35)))
        while pay_d.weekday() >= 5:
            pay_d += timedelta(days=1)
        if pay_d <= FY_END:
            new_payment(inv, vendor, amt, pay_d, {clerk["user_id"]})

    # ------------------------------------------------------ journal entries
    journals = []
    accountants = by_role["Accountant"]
    for i in range(1, 1201):
        d = g.workday()
        creator = g.choice(active(accountants, d))
        amt = g.amount(median=8_000, sigma=1.3)
        appr = approver_for(amt, d, {creator["user_id"]})
        journals.append({"je_id": f"JE{i:05d}", "posted_at": g.office_time(d).isoformat(sep=" "),
                         "account": g.choice(GL_ACCOUNTS),
                         "description": f"{g.choice(GL_ACCOUNTS)} adjustment",
                         "amount": f"{amt:.2f}", "created_by": creator["user_id"],
                         "approved_by": appr["user_id"]})

    plant_exceptions(g, vendors, users, employees, pos, invoices, payments, journals, new_payment)
    gl_postings = build_gl_postings(g, payments, seed)

    limits = [{"role": r, "max_approval": f"{v:.2f}"} for r, v in APPROVAL_LIMITS.items()]
    tables = {"employees": employees, "users": users, "approval_limits": limits, "vendors": vendors,
              "purchase_orders": pos, "invoices": invoices, "payments": payments,
              "journal_entries": journals, "gl_postings": gl_postings}
    # Control totals as the source system would report them at extract time
    controls = []
    for name, rows in tables.items():
        total = ""
        if rows and "amount" in rows[0]:
            total = f"{sum(round(float(r['amount']) * 100) for r in rows) / 100:.2f}"
        controls.append({"table_name": name, "record_count": len(rows), "amount_total": total})
    tables["extract_control_totals"] = controls
    return tables, g.key


def build_gl_postings(g, payments, seed):
    """General-ledger lines posted from the payables subledger: one per payment,
    same date and amount, plus planted breaks for the subledger-to-GL test.

    Uses its own random stream so adding this table leaves every other table
    exactly as it was."""
    rng = np.random.default_rng(seed + 4_000)
    planted = {r["record_id"] for r in g.key}
    clean = [p for p in payments if p["payment_id"] not in planted]

    def pick(cands, n):
        idx = rng.choice(len(cands), size=n, replace=False)
        return [cands[i] for i in sorted(idx)]

    # Breaks: never posted; posted in the next month (cut-off); posted at a
    # different amount (two digits swapped when keying, a classic slip).
    late_cands = [p for p in clean if int(p["payment_date"][8:10]) >= 27
                  and p["payment_date"][:7] < "2026-09"]
    late = pick(late_cands, 2)
    rest = [p for p in clean if p not in late]
    missing = pick(rest, 3)
    rest = [p for p in rest if p not in missing]
    swap_cands = [p for p in rest if p["amount"].split(".")[0][-2] != p["amount"].split(".")[0][-1]
                  and float(p["amount"]) >= 1000]
    swapped = pick(swap_cands, 2)
    missing_ids = {p["payment_id"] for p in missing}
    late_ids = {p["payment_id"] for p in late}
    swap_ids = {p["payment_id"] for p in swapped}

    lines = []
    for p in sorted(payments, key=lambda r: (r["payment_date"], r["payment_id"])):
        pid = p["payment_id"]
        if pid in missing_ids:
            g.plant(4, "GL_NOT_POSTED", "payments", pid, "payment never posted to the GL")
            continue
        posting_date, amount = p["payment_date"], p["amount"]
        if pid in late_ids:
            d = date.fromisoformat(p["payment_date"])
            first_next = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
            posted = first_next + timedelta(days=int(rng.integers(0, 3)))
            while posted.weekday() >= 5:          # GL postings happen on working days
                posted += timedelta(days=1)
            posting_date = posted.isoformat()
            g.plant(4, "GL_WRONG_PERIOD", "payments", pid, f"paid {p['payment_date']}, posted {posting_date}")
        if pid in swap_ids:
            whole, cents = amount.split(".")
            amount = f"{whole[:-2]}{whole[-1]}{whole[-2]}.{cents}"
            g.plant(4, "GL_AMOUNT_DIFFERENCE", "payments", pid, f"paid {p['amount']}, posted {amount}")
        lines.append({"gl_line_id": f"GL{len(lines) + 1:05d}", "posting_date": posting_date,
                      "account": "Accounts payable", "source_module": "AP",
                      "source_doc": pid, "amount": amount})
    return lines


def plant_exceptions(g, vendors, users, employees, pos, invoices, payments, journals, new_payment):
    """Insert the exceptions each phase's tests must find. Recorded in the answer key."""
    vend = {v["vendor_id"]: v for v in vendors}
    nxt = {"po": len(pos), "inv": len(invoices), "je": len(journals)}

    def add_invoice(vendor, amount, inv_no, d, po_id=""):
        nxt["inv"] += 1
        inv = {"invoice_id": f"INV{nxt['inv']:05d}", "vendor_id": vendor["vendor_id"], "po_id": po_id,
               "invoice_number": inv_no, "invoice_date": d.isoformat(), "amount": f"{amount:.2f}",
               "entered_by": "U002"}
        invoices.append(inv)
        return inv

    # ---------------- Phase 1: data integrity (orphans in the extract)
    for pid, missing, amt in (("PAY90001", "INV99901", "1840.55"), ("PAY90002", "INV99902", "2215.80")):
        payments.append({"payment_id": pid, "invoice_id": missing, "vendor_id": "V012",
                         "payment_date": "2026-02-17", "amount": amt, "approved_by": "U033",
                         "released_by": "U020", "posted_at": "2026-02-17 10:42:00"})
        g.plant(1, "ORPHAN_PAYMENT", "payments", pid, f"invoice {missing} not in invoices extract")
    orphan = add_invoice({"vendor_id": "V099"}, 2310.40, "099-77812", date(2026, 4, 9))
    g.plant(1, "ORPHAN_INVOICE", "invoices", orphan["invoice_id"], "vendor V099 not in vendor master")
    pos[40]["approved_by"] = "U999"
    g.plant(1, "UNKNOWN_APPROVER", "purchase_orders", pos[40]["po_id"], "approver U999 not in users")

    # ---------------- Phase 2: payments
    # Exact duplicates: same invoice paid twice
    for idx in (55, 210, 480, 760):
        p = payments[idx]
        inv = next(i for i in invoices if i["invoice_id"] == p["invoice_id"])
        d = date.fromisoformat(p["payment_date"]) + timedelta(days=9)
        while d.weekday() >= 5:
            d += timedelta(days=1)
        dup = new_payment(inv, vend[p["vendor_id"]], float(p["amount"]), d, set())
        g.plant(2, "DUPLICATE_PAYMENT_EXACT", "payments", dup["payment_id"],
                f"second payment of invoice {inv['invoice_id']} (first {p['payment_id']})")
    # Near duplicates: same vendor and amount, invoice number re-keyed with different format
    for idx in (120, 330, 640):
        p = payments[idx]
        orig = next(i for i in invoices if i["invoice_id"] == p["invoice_id"])
        d = date.fromisoformat(orig["invoice_date"]) + timedelta(days=4)
        inv2 = add_invoice(vend[p["vendor_id"]], float(orig["amount"]),
                           orig["invoice_number"].replace("-", ""), d)
        pd_ = date.fromisoformat(p["payment_date"]) + timedelta(days=6)
        while pd_.weekday() >= 5:
            pd_ += timedelta(days=1)
        dup = new_payment(inv2, vend[p["vendor_id"]], float(orig["amount"]), pd_, set())
        g.plant(2, "DUPLICATE_PAYMENT_NEAR", "payments", dup["payment_id"],
                f"invoice {orig['invoice_number']} re-entered as {inv2['invoice_number']}")
    # Split purchases: one raiser, one vendor, several POs just under the threshold within 3 days
    for vid, raiser, start, amounts in (("V007", "U012", date(2026, 1, 13), (9_850.00, 9_720.50, 9_910.25)),
                                        ("V031", "U015", date(2026, 5, 5), (9_600.00, 9_995.00)),
                                        ("V052", "U011", date(2026, 7, 20), (9_480.75, 9_350.20, 9_999.00))):
        for k, amt in enumerate(amounts):
            nxt["po"] += 1
            po = {"po_id": f"PO{nxt['po']:05d}", "vendor_id": vid, "department": "Operations",
                  "po_date": (start + timedelta(days=k)).isoformat(),
                  "description": "Equipment", "amount": f"{amt:.2f}", "raised_by": raiser,
                  "approved_by": "U019"}  # Finance Officer, limit 10,000
            pos.append(po)
            g.plant(2, "SPLIT_PURCHASE", "purchase_orders", po["po_id"],
                    f"{len(amounts)} POs to {vid} by {raiser} within 3 days, total over threshold")
    # Payments to inactive or unapproved vendors
    # V073 is one of the inactive vendors; V081 is a new vendor that never
    # completed due diligence (approved = 0).
    new_v = {"vendor_id": "V081", "vendor_name": "Swiftline Supplies Ltd", "tax_id": "TIN58201447",
             "bank_account": "4417730921", "address": "7 Quarry Lane, Eastbrook", "status": "Active",
             "approved": 0, "created_by": "U013", "created_date": "2026-03-30"}
    vendors.append(new_v)
    vend["V081"] = new_v
    for vid, amt, d in (("V073", 6_420.18, date(2026, 3, 10)), ("V073", 3_115.60, date(2026, 6, 2)),
                        ("V081", 12_870.44, date(2026, 4, 21)), ("V081", 4_402.09, date(2026, 8, 12))):
        inv = add_invoice(vend[vid], amt, f"{vid[1:]}-X{int(amt)}", d - timedelta(days=12))
        pay = new_payment(inv, vend[vid], amt, d, set())
        test = "PAYMENT_INACTIVE_VENDOR" if vid == "V073" else "PAYMENT_UNAPPROVED_VENDOR"
        g.plant(2, test, "payments", pay["payment_id"], f"vendor {vid}")
    # Round-sum payments
    for vid, amt, d in (("V003", 25_000.00, date(2025, 12, 18)), ("V018", 15_000.00, date(2026, 2, 26)),
                        ("V027", 50_000.00, date(2026, 3, 30)), ("V060", 8_000.00, date(2026, 6, 24)),
                        ("V066", 40_000.00, date(2026, 9, 11))):
        inv = add_invoice(vend[vid], amt, f"{vid[1:]}-R{int(amt)}", d - timedelta(days=15))
        pay = new_payment(inv, vend[vid], amt, d, set())
        g.plant(2, "ROUND_SUM_PAYMENT", "payments", pay["payment_id"], f"{amt:,.0f} to {vid}")

    # ---------------- Phase 3: vendor-employee links, Benford, timing
    emp = {e["employee_id"]: e for e in employees}
    vendors[22]["bank_account"] = emp["E090"]["bank_account"]
    g.plant(3, "VENDOR_EMPLOYEE_BANK", "vendors", vendors[22]["vendor_id"], "bank account matches E090")
    vendors[58]["bank_account"] = emp["E047"]["bank_account"]
    g.plant(3, "VENDOR_EMPLOYEE_BANK", "vendors", vendors[58]["vendor_id"], "bank account matches E047")
    vendors[9]["address"] = emp["E101"]["address"]
    g.plant(3, "VENDOR_EMPLOYEE_ADDRESS", "vendors", vendors[9]["vendor_id"], "address matches E101")
    vendors[36]["address"] = emp["E015"]["address"]
    g.plant(3, "VENDOR_EMPLOYEE_ADDRESS", "vendors", vendors[36]["vendor_id"], "address matches E015")
    # Benford: one vendor's invoices cluster just under the 10,000 threshold (first digit 9)
    for k in range(18):
        d = g.workday(date(2025, 11, 1), date(2026, 8, 31))
        amt = round(float(g.rng.uniform(9_100, 9_990)), 2)
        inv = add_invoice(vend["V041"], amt, f"041-B{k:03d}", d)
        g.plant(3, "BENFORD_OUTLIER_VENDOR", "invoices", inv["invoice_id"], "V041 first-digit-9 cluster")
    # Out-of-hours and weekend journal postings
    for d, t in ((date(2026, 1, 10), "22:47"), (date(2026, 3, 1), "11:05"), (date(2026, 3, 28), "09:30"),
                 (date(2026, 6, 16), "23:58"), (date(2026, 8, 29), "14:12"), (date(2026, 9, 29), "05:40")):
        nxt["je"] += 1
        je = {"je_id": f"JE{nxt['je']:05d}", "posted_at": f"{d.isoformat()} {t}:00",
              "account": "Suspense", "description": "Manual adjustment",
              "amount": f"{float(g.rng.uniform(15_000, 48_000)):.2f}", "created_by": "U028",
              "approved_by": "U034"}
        journals.append(je)
        g.plant(3, "JOURNAL_OUT_OF_HOURS", "journal_entries", je["je_id"],
                f"{d:%a} {t}")

    # ---------------- Phase 4: access and segregation of duties
    # Vendor creator also approves payments to that vendor
    for vid in ("V014", "V063"):
        # The manager who approves this vendor's payments is recorded as having
        # also created the vendor in the master file.
        first = next(p for p in payments if p["vendor_id"] == vid)
        creator = first["approved_by"]
        vend[vid]["created_by"] = creator
        for p in payments:
            if p["vendor_id"] == vid and p["approved_by"] == creator:
                g.plant(4, "SOD_VENDOR_CREATOR_APPROVES_PAYMENT", "payments", p["payment_id"],
                        f"{creator} created {vid} and approved this payment")
    # Journal created and approved by the same person
    for idx in (101, 505, 909):
        journals[idx]["approved_by"] = journals[idx]["created_by"]
        g.plant(4, "SOD_JOURNAL_SELF_APPROVED", "journal_entries", journals[idx]["je_id"],
                f"created and approved by {journals[idx]['created_by']}")
    # Activity by leavers after their account was disabled
    for uid, je_date in (("U030", date(2026, 7, 14)), ("U030", date(2026, 8, 3))):
        nxt["je"] += 1
        je = {"je_id": f"JE{nxt['je']:05d}", "posted_at": f"{je_date.isoformat()} 10:15:00",
              "account": "Accruals", "description": "Accrual reversal",
              "amount": f"{float(g.rng.uniform(2_000, 9_000)):.2f}", "created_by": uid,
              "approved_by": "U034"}
        journals.append(je)
        g.plant(4, "ACTIVITY_AFTER_LEAVING", "journal_entries", je["je_id"], f"{uid} disabled 2026-03-31")
    p = next(p for p in payments if date.fromisoformat(p["payment_date"]) > date(2026, 7, 20)
             and p["approved_by"] != "U022" and p["payment_id"] < "PAY9")
    p["released_by"] = "U022"
    g.plant(4, "ACTIVITY_AFTER_LEAVING", "payments", p["payment_id"], "U022 disabled 2026-06-30")
    # Postings by privileged (administrator) accounts
    for uid, d in (("U040", date(2026, 2, 9)), ("U041", date(2026, 5, 18))):
        nxt["je"] += 1
        je = {"je_id": f"JE{nxt['je']:05d}", "posted_at": f"{d.isoformat()} 16:20:00",
              "account": "Inter-unit transfers", "description": "System correction",
              "amount": f"{float(g.rng.uniform(5_000, 30_000)):.2f}", "created_by": uid,
              "approved_by": "U035"}
        journals.append(je)
        g.plant(4, "PRIVILEGED_ACCOUNT_POSTING", "journal_entries", je["je_id"], f"posted by {uid}")


def write(tables: dict[str, list[dict]], key: list[dict]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        with open(DATA / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"wrote data/{name}.csv ({len(rows)} rows)")
    with open(ANSWER_KEY, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["phase", "test", "table", "record_id", "note"])
        w.writeheader()
        w.writerows(key)
    print(f"wrote tests/answer_key.csv ({len(key)} planted exceptions)")


def main() -> None:
    tables, key = build()
    write(tables, key)


if __name__ == "__main__":
    main()
