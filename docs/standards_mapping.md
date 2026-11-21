# Standards mapping

How each part of this project lines up with the standards and frameworks a
public-sector auditor works to. The mapping is indicative, at the level of
whole standards: check the current text of each standard before relying on it
for a specific requirement.

## Public-sector audit (INTOSAI)

| Standard | What it covers | Where it shows up here |
|---|---|---|
| ISSAI 100 | Fundamental principles of public-sector auditing | The whole approach: evidence-based findings, documented criteria, reporting to those responsible |
| ISSAI 200 | Financial audit principles | Phases 1–4 test the reliability of financial records (payments, journals, the general ledger) |
| ISSAI 400 | Compliance audit principles | Tests against stated rules: approval limits, vendor approval, segregation of duties |

INTOSAI's financial audit standards are based on the International Standards on
Auditing (ISAs), so the ISA mapping below applies to public-sector financial
audit too.

## Financial audit (ISA)

| Standard | What it covers | Where it shows up here |
|---|---|---|
| ISA 500 Audit evidence | Information produced by the entity must be reliable enough (complete and accurate) for the auditor's purpose | Phase 1: control totals, referential integrity, completeness and period checks before any test |
| ISA 240 Fraud | Risk of fraud, including management override of controls; testing journal entries | Phase 2 payment red flags; Phase 3 out-of-hours journals; Phase 4 self-approved and leaver journals |
| ISA 315 (Revised 2019) Risk assessment | Understanding the entity, its internal control and IT, including general IT controls such as access | Phase 4 access tests: segregation of duties, leavers, privileged accounts |
| ISA 520 Analytical procedures | Comparing data with expectations to find unusual items | Phase 3 Benford tests (expected first-digit pattern) |
| ISA 530 Audit sampling | When and how to sample | Not needed here: every test covers 100% of the records, which is the main advantage of data analytics over sampling |
| ISA 230 Audit documentation | What working papers must record | Phase 5 working papers: test, condition, criteria, cause, effect, recommendation |
| ISA 265 Deficiencies in internal control | Communicating control weaknesses to management and those charged with governance | Phase 5 recommendations, rated High / Medium |

## Control frameworks

| Framework | Relevant part | Where it shows up here |
|---|---|---|
| COSO Internal Control – Integrated Framework (2013) | Control activities, including general controls over technology | Approval limits, duplicate-payment checks, segregation of duties, subledger-to-GL reconciliation |
| COBIT 2019 | DSS05 Managed security services (identity and access) | Phase 4 leavers and privileged accounts |
| COBIT 2019 | DSS06 Managed business process controls | Phase 2 payment controls; Phase 4 completeness of postings to the general ledger |

## The working-paper format

Each finding in [`reports/working_papers.md`](../reports/working_papers.md)
uses the five elements common to public-sector audit reporting:

- **Condition:** what was found (from the data)
- **Criteria:** what should be (from the query header: the rule being tested)
- **Cause:** why it happened (possible causes, confirmed with management before reporting)
- **Effect:** why it matters
- **Recommendation:** what should change
