# Phase 2 Decision — What Is Cleared, What Is Not

One page for the owner. Evidence lives in `docs/data/`; every figure below is reproducible from the
commands in `IMPLEMENTATION_DIFF_REPORT.md`. Written 2026-10-24. Nothing was pushed or deployed.

## The gate

**196 tests pass, every suite exit 0. Frontend builds clean. DSA validator: 20 complete, 0 invalid,
88 drafts.** Base was 128 tests; this phase added 68 and two new suites.

## Workstream verdicts

| Workstream | Verdict | What that means in practice |
|---|---|---|
| A — DSA gradability | **PARTIAL** | 20/108 problems are genuinely auto-gradable and harness-stamped; 88 are prose. Graphs, heaps and backtracking have **zero** validated problems, so "interview ready" is not yet a defensible claim. A fabricated grading path was removed from the student product. |
| B — Import infrastructure | **GO** | Registry, approval gate, provenance, PII refusal, dry-run, idempotency, per-document undo, rollback with conflict detection, audit trail — all proven on memory **and** real MongoDB against disposable databases that were then dropped. |
| C — Source rights | **PARTIAL / mostly NO-GO** | 11 register verdicts corrected. Three open-source curriculum sources are cleared with attribution. **No institution or placement dataset is cleared for import.** KMIT is © All Rights Reserved; AICTE/AISHE need written consent; OGD's licence is not evidenced. |
| D — Live jobs | **GO as prototype, NO-GO to ship** | Real ingestion works: 18 Indian postings from Groww and CRED, 100% canonical employer links, 144 body fields received and deliberately discarded, second poll a pure no-op. Ashby is refused by the robots gate (HTTP 401 on its own policy file), Greenhouse waits on an unreadable ToS, only Lever is conditionally allowed. |
| E — Independent review | **GO** | Findings from three separate agents were independently re-verified; two dossier claims were corrected (Greenhouse robots, KMIT's published metrics); one honest breach was disclosed (the first job-feed run polled Ashby before the robots gate existed and was fully rolled back). |

## The three things this phase actually changed about the product

1. **The DSA "judge" was fake and is gone.** It invented "Accepted", fake test-case pass flags and
   runtime/memory numbers from a token count, and a submission could set `solved` and mastery 88.
   It now returns a labelled static review that cannot mark anything solved. That was the single
   most dangerous thing in the product: a placement cell could have made decisions on it.
2. **Data import is now reversible and gated.** Nothing enters the database without an approved
   source, provenance, and a batch that can be undone record-by-record.
3. **"108 original problems" is no longer claimed.** 91 of the 108 titles are standard industry
   names; the taxonomy and all prompts are in-house. The honest claim is now in the docs.

## What the owner must do, in order

1. **Rotate the exposed Jooble key and the demo password** (unchanged from Phase 1 — still the only
   strictly security-critical action).
2. **Create the staging MongoDB** when a preview deployment is actually wanted; the code asks for
   the URI at that point and never prints it.
3. **Decide the data strategy** — this is the real blocker, and it is a business decision, not an
   engineering one:
   - institution directory: wait for AICTE/OGD consent, licence a commercial set, or collect
     college-submitted data (only the third has no rights problem);
   - placement metrics: written permission per college, or college-entered data only;
   - live jobs: Lever-only curated boards now, or pay for a licensed aggregator.
4. **Send the four drafted permission requests** if option "wait for consent" is chosen. They are
   written and labelled "draft, not sent" in `SOURCE_RIGHTS_EVIDENCE.md`.
5. **Re-run `scripts/rebuild_dsa_progress.py`** against the dev database before any demo, because a
   question id changed when the slug cap was fixed.

## Overall decision

**GO to keep building on this codebase; NO-GO to sell it as a data product today.**

The engineering is now honest and verifiable: the pipeline is gated and reversible, the curriculum's
gradability is evidence-backed rather than asserted, the UI no longer promises grading it cannot do,
and every limitation is written down where the next engineer will find it. What is missing is not
more code — it is permission to use the data that would make the product valuable, and enough
validated problems in graphs, heaps and backtracking to walk into a placement cell and demo it.
