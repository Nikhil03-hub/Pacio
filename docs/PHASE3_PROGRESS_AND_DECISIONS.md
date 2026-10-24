# Phase 3 — Progress and Decisions

Living document. Started 2026-10-24 from the Phase 2 checkpoint. Status labels: VERIFIED / PARTIAL /
BLOCKED / NOT RUN.

## 1. Baseline at Phase 3 start

| Item | Value |
|---|---|
| Branch / HEAD | `main` @ `1be1eb0` (Phase 2 final), clean tree at start |
| Remote | `origin` = `https://github.com/Nikhil03-hub/pacio-intelligence.git`, upstream `origin/main` — **nothing pushed in this phase** |
| Tests at start | 206 passed across 8 suites, frontend build clean |
| DSA at start | 30 of 108 gradable (all twelve topics covered), 78 drafts, 2 Hard. **Now 36/108 after batch 4.** |
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
| A | Batch 4 (3 trees + 3 bit problems) | VERIFIED | 36/108 gradable; 44 spec tests; validator `COMPLETE: 36 / INVALID: 0` |
| B | Wikidata CC0 licence + fitness measured | VERIFIED | `WIKIDATA_FEASIBILITY.md` (2/8 spot-check pass, 57% links live) |
| B | New dataset candidates scanned | VERIFIED (negative) | `PERMITTED_DATASET_SCAN.md` — no approved AICTE/AISHE/placement source |
| B | OGD licence corrected in a browser | VERIFIED | `OGD_LICENCE_BROWSER_VERIFICATION.md` — GODL-India in the portal footer |
| C | Pipeline exercised on real third-party data | VERIFIED | `WIKIDATA_IMPORT_PILOT.md` — 28 rows imported, idempotent, rolled back to 0 on disposable MongoDB |
| D | Real-data pilot | VERIFIED (twice) | Round 1: 28 institutions from a generic sample (9.3% yield). Round 2 with a targeted engineering query: **193 distinct institutions, 87% filter pass, 74% live websites, 48% AISHE-coded**, imported and rolled back on disposable MongoDB |
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
| **Gate result now** | **212 passed, 0 failed**, every suite exit 0 (final run 2026-10-25) |
| Commits added this phase | 6 (UI + API URL guard, CI + security design, data rights + Wikidata pilot, progress/coverage docs, truthfulness addenda, batch 4 + round 2 pilot) |
| Gradable DSA problems | 36 of 108 (batch 4 merged: 3 trees + 3 bit problems) |
| Validated specs with independent reviewer | 26 of 36 (the 10 earliest are self-reviewed and marked `pending`) |
| Real external rows ever imported into the application DB | **0** |
| Rows imported into disposable pilot DBs, then rolled back | **221 institutions** (28 + 193, Wikidata) and 18 job postings (Lever/Groww) |
| Approved external sources | Wikidata (CC0, limited), Lever boards (conditional), three OSS curriculum repos (MIT/CC BY) |
| Blocked sources | AICTE official + mirrors, AISHE counts, NIRF, KMIT, NASSCOM, NCS, Adzuna, Jooble, Ashby, Workable |

## 5. Open items and exact continuation point

1. **Batch 4 — DONE** (36/108). A first agent produced nothing in two hours; a reduced-scope agent
   delivered 6 specs, all hand-checked before merge. The next batch is DP (10 drafts) then the 8
   remaining Hard problems.
2. **`DSA_COVERAGE_AND_DIFFICULTY.md`** — written from the post-batch-4 data, with the 72 remaining
   draft ids listed exactly.
3. **Authenticated browser journeys** — blocked on credentials. Options: add a read-only demo
   account whose password is safe to use in automation, or accept manual verification.
4. **CI has never executed on GitHub** — every job was validated locally (YAML parse, the same
   commands). Enabling it requires a push, which is out of scope until the owner decides.
5. **Wikidata — targeted query DONE** (193 rows, 87% yield). Next: resolve state, paginate to the
   full 1,403, and only then surface it read-only with `unverified` labelling.
6. **Label synthetic demo progress.** The seeded demo tenant carries `solved`/mastery rows that the
   UI does not mark as synthetic, so a reviewer could read them as student work. Needs a seed flag
   (`is_demo` / `data_status`) plus a UI treatment — a seed-data change with migration impact, so it
   is deliberately not done in passing.
7. **Owner actions unchanged** — rotate the Jooble key and demo password; decide the staging
   database; decide whether public repo history needs rewriting after rotation.

## 5b. Workstream E — product truthfulness audit (code-level, 2026-10-25)

Checked by reading the shipped components, not by assuming:

| Surface | Requirement | Finding |
|---|---|---|
| `landing/WallOfLove.jsx` | no fake testimonials | **PASS** — renders "Written from the product team as role walkthroughs — these are illustrative, not customer testimonials" |
| `landing/CustomerStories.jsx` | no placement claims | **PASS** — heading is "What the demonstration dataset contains" |
| `landing/TrustGrid.jsx` | no fake customer logos | **PASS** — "This deployment runs on a seeded demonstration dataset", each row labelled "sample record in the demo dataset" |
| `pages/Jobs.jsx` | empty feed must not show fake listings | **PASS** — state starts empty, API failures are caught, and an explicit empty state renders (`discoveryJobs.length === 0`) |
| `pages/StudentDSA*.jsx` | drafts must differ from gradable | **PASS (code)** — `VALIDATED SPEC` / `DRAFT SPEC` badges and a description that states submissions are not executed; **visual check blocked** behind login |
| Landing hero / metrics | no invented benchmarks | **PARTIAL** — copy is honest, but the demo dataset still contains synthetic `solved`/mastery progress that is not labelled per-row in the UI |

The last row is the one real remaining truthfulness gap: a reviewer could mistake seeded demo
progress for student work. Fixing it needs a seed-labelling decision (see §5, item 7).

## 5c. Workstream F — measured deployment constraints (2026-10-25)

Numbers below were measured on this machine, not estimated. They are the evidence for whether the
monolith should be split — and the answer is "not yet, but two specific things are already broken".

| Measurement | Value | Consequence |
|---|---|---|
| `import server` cold, in-memory | **12.06 s** | Exceeds a default Vercel function timeout. A cold start can fail before the first response. VERIFIED locally. |
| Time to `GET /api/health` = 200 after launch, with MongoDB | ~45 s observed across restarts | Cold-start cost is dominated by module import plus startup seeding/index work, not the DB round trip. |
| `vercel.json` | single rewrite `/(.*) → /api/index.py`; **no `maxDuration`, no function config** | The whole app is one function on the default budget. |
| `vercel.json` build | `npm install --no-package-lock` while `frontend/package-lock.json` exists | Builds are non-reproducible: CI and Vercel can resolve different dependency versions. |
| `/ws/live` WebSocket endpoint (`server.py:5866`) | exists and is used by the live dashboard | **Cannot work** in a single serverless function; needs a persistent process or a different transport. |
| Frontend bundle | 885 kB gzipped `main.js` | Flagged by the build itself; a code-splitting task, not a blocker. |

Recommendation, deliberately conservative: **do not rewrite the monolith this phase.** Two targeted
changes fix real defects with no architectural risk — add an explicit `maxDuration` (and move to
`npm ci` for reproducibility), and decide whether `/ws/live` is a feature the hosted product ships or
drops. Splitting the API from the SPA is worth doing only when a measured cold-start or timeout
incident justifies it, and that evidence is now recorded.

## 6. What must not be claimed

- That Pacio has a real institution directory, placement dataset, or live jobs feed.
- That any DSA submission is executed or graded.
- That the catalogue's problem list is original (measured: 91/108 titles are standard names).
- That CI passes on GitHub (it has only been validated locally).
