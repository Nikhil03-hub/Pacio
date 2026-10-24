# Phase 3 — Progress and Decisions

Living document. Started 2026-10-24 from the Phase 2 checkpoint. Status labels: VERIFIED / PARTIAL /
BLOCKED / NOT RUN.

## 1. Baseline at Phase 3 start

| Item | Value |
|---|---|
| Branch / HEAD | `main` @ `1be1eb0` (Phase 2 final), clean tree at start |
| Remote | `origin` = `https://github.com/Nikhil03-hub/pacio-intelligence.git`, upstream `origin/main` — **nothing pushed in this phase** |
| Tests at start | 206 passed across 8 suites, frontend build clean |
| DSA at start | 30 of 108 gradable (all twelve topics covered), 78 drafts, 2 Hard |
| Batch 4 | **not started** at Phase 3 beginning; launched during this phase |
| Import pipeline | gated, undo pre-images, conflict-safe rollback; proven on memory + real MongoDB |
| Cleared external data | none — three research passes found no institution/placement dataset with a usable licence |

Reconciliation: the Phase 2 reports match the code at `1be1eb0`. The one number that moved during
Phase 2's own close-out was the honesty suite (5 → 6 tests), so the gate total is 206, not 195; both
`RELEASE_READINESS.md` and `PACIO_HANDOFF.md` were corrected.

## 2. What Phase 3 has delivered so far

| Workstream | Item | Status | Evidence |
|---|---|---|---|
| A | Grading-honesty guarantee kept and pinned | VERIFIED | `test_dsa_grading_honesty.py` (6 tests); `_static_code_review` cannot mark solved |
| A | Judge threat model + required controls | VERIFIED (design) | `DSA_GRADING_SECURITY_DESIGN.md`; implementation **NOT RUN** |
| A | Batch 4 (trees/DP/bits) | IN PROGRESS | agent authoring; validator run pending merge |
| B | Wikidata CC0 licence + fitness measured | VERIFIED | `WIKIDATA_FEASIBILITY.md` (2/8 spot-check pass, 57% links live) |
| B | New dataset candidates scanned | VERIFIED (negative) | `PERMITTED_DATASET_SCAN.md` — no approved AICTE/AISHE/placement source |
| B | OGD licence corrected in a browser | VERIFIED | `OGD_LICENCE_BROWSER_VERIFICATION.md` — GODL-India in the portal footer |
| C | Pipeline exercised on real third-party data | VERIFIED | `WIKIDATA_IMPORT_PILOT.md` — 28 rows imported, idempotent, rolled back to 0 on disposable MongoDB |
| D | Real-data pilot | PARTIAL | 28 community-sourced institutions, `unverified`, 9 states; **not** a shippable directory |
| E | DSA spec status shown in student UI | VERIFIED (build) / PARTIAL (visual) | `VALIDATED SPEC` / `DRAFT SPEC` badges + honest description; authenticated pages not browser-tested |
| E | Bundle no longer bakes a loopback URL | VERIFIED | `BROWSER_SMOKE_REPORT.md`; 0 occurrences after rebuild; runtime same-origin fallback added |
| F | CI for hermetic suites, spec integrity, Mongo, frontend | VERIFIED (local YAML + local runs) | `.github/workflows/ci.yml`; **NOT RUN on GitHub** — no push allowed |
| F | Browser smoke (anonymous) | VERIFIED | `/login`, `/verify/…`, `/` pass; authenticated journeys BLOCKED by credential policy |
| — | Security owner items | OPEN | Jooble key / demo password rotation still owner-controlled |

## 3. Decisions taken this phase

1. **Do not import AICTE-derived data from a mirror.** A second GitHub repository
   (`anburocky3/indian-colleges-data`, 13,089 rows, MIT) fails for the same reason SRC-001 did: a
   wrapper's licence cannot license AICTE's data. Recorded as SRC-049 NEEDS_REVIEW.
2. **Use Wikidata as the only rights-clean institution source**, with hard conditions: engineering
   scope filter, no K-12, dedupe on QID/AISHE/domain, link health check, `data_status:
   unverified`, `trust_level: community-maintained`, never presented as authoritative.
3. **Correct the OGD verdict from NEEDS_REVIEW to APPROVED_WITH_LIMITATIONS** for
   ministry-published *aggregates*, because the licence is declared portal-wide in the footer. The
   institution directory remains BLOCKED on availability, not on licence.
4. **No learner code execution.** The authoring harness is measured to be escapable; a real judge
   needs the isolation in `DSA_GRADING_SECURITY_DESIGN.md` before anything is enabled.
5. **Surface spec status, not grading status.** The UI says which problems have a validated spec
   and repeats that submissions are not executed.

## 4. Current numbers

| Metric | Value |
|---|---|
| Commits added this phase | 3 (UI/API-URL, CI/security design, data rights + Wikidata pilot) |
| Gradable DSA problems | 30 of 108 (+ batch 4 pending) |
| Validated specs with independent reviewer | 20 of 30 (10 earliest are self-reviewed and marked `pending`) |
| Real external rows ever imported into the application DB | **0** |
| Rows imported into disposable pilot DBs, then rolled back | 28 institutions (Wikidata), 18 job postings (Lever/Groww) |
| Approved external sources | Wikidata (CC0, limited), Lever boards (conditional), three OSS curriculum repos (MIT/CC BY) |
| Blocked sources | AICTE official + mirrors, AISHE counts, NIRF, KMIT, NASSCOM, NCS, Adzuna, Jooble, Ashby, Workable |

## 5. Open items and exact continuation point

1. **Batch 4 merge** — when `backend/dsa_specs_batch4.json` lands: validate, hand-check expected
   outputs, review mutants, merge into `dsa_specs.json`, `--stamp`, update pinned counts, re-run the
   gate, commit. Expected outcome 40/108.
2. **`DSA_COVERAGE_AND_DIFFICULTY.md`** — required deliverable; write from the post-merge data.
3. **Authenticated browser journeys** — blocked on credentials. Options: add a read-only demo
   account whose password is safe to use in automation, or accept manual verification.
4. **CI has never executed on GitHub** — every job was validated locally (YAML parse, the same
   commands). Enabling it requires a push, which is out of scope until the owner decides.
5. **Wikidata next step** — a targeted engineering query, not a bigger generic sample. Keep the link
   health check in the importer.
6. **Owner actions unchanged** — rotate the Jooble key and demo password; decide the staging
   database; decide whether public repo history needs rewriting after rotation.

## 6. What must not be claimed

- That Pacio has a real institution directory, placement dataset, or live jobs feed.
- That any DSA submission is executed or graded.
- That the catalogue's problem list is original (measured: 91/108 titles are standard names).
- That CI passes on GitHub (it has only been validated locally).
