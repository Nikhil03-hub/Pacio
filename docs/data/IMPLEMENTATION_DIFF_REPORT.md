# Implementation Diff Report

Phase 2 deliverable #6. Baseline commit `a2bb07b` (branch `main`). Recorded 2026-10-24.
No commit was pushed, nothing was deployed, no Git history was rewritten.

## 1. Verification of this change set

| Check | Command | Result |
|---|---|---|
| Full release gate | `bash scripts/release_gate.sh` (server against local MongoDB, `RATE_LIMIT_ENABLED=false`) | **195 passed, 0 failed**, every suite exit 0 |
| — hardening | `pytest backend/tests/test_hardening.py` | 32 passed, exit 0 |
| — tenant isolation | `pytest backend/tests/test_tenant_isolation.py` | 20 passed, exit 0 |
| — DSA spec harness | `pytest backend/tests/test_dsa_specs.py` | 28 passed, exit 0 |
| — DSA grading honesty | `pytest backend/tests/test_dsa_grading_honesty.py` | 5 passed, exit 0 |
| — data import | `pytest backend/tests/test_data_import.py` | 18 passed, exit 0 |
| — job feeds | `pytest backend/tests/test_job_feeds.py` | 16 passed, exit 0 |
| — real MongoDB | `pytest backend/tests/test_mongo_integration.py` | 3 passed, exit 0 |
| — legacy features | `pytest backend/tests/test_careeros_v2.py test_careeros_v21.py` | 73 passed, exit 0 |
| DSA validator | `python scripts/validate_dsa_specs.py --stamp` | 20 COMPLETE / 0 INVALID / 88 DRAFT, exit 0 |
| Import dry-run (memory) | `python scripts/import_dry_run.py` | exit 0 |
| Import dry-run (MongoDB) | `... --mongo-url mongodb://127.0.0.1:27017 --db-name pacio_dryrun_import` | exit 0, identical behaviour, disposable DB dropped |
| Job feed pilot (memory + MongoDB) | `python scripts/job_feed_pilot.py [...]` | exit 0 both engines, identical behaviour |
| Frontend production build | `cd frontend && CI=false npm run build` | **exit 0**, `main.js` 885.29 kB gzipped |

Baseline was 128 passing tests across four suites; this change set adds 67 tests and two new
suites, for 195.

## 2. Every changed file

### Modified (12)

| File | Why |
|---|---|
| `backend/server.py` | **Removed the fabricated DSA judge.** `_simulated_code_result` invented "Accepted", "Sample 1/2/Hidden edge" pass flags and runtime/memory numbers from a token count, and a submission could set `solved: true` and `mastery: 88`. Replaced by `_static_code_review` (`executed: false`, `graded: false`, honest signals + note). `submit_my_dsa_code` no longer writes `solved`/`mastery`/`best_submission_id`/`last_solved_at` from an unexecuted submission. |
| `backend/dsa_catalog.py` | Gradability now requires a harness stamp (`DSA_HARNESS_VERSION`), three-state `spec_status`, corrupt spec file raises instead of silently demoting the bank, slug cap 40 → 48 with trailing-hyphen strip, and the module docstring no longer claims the problem list is unreproduced. |
| `frontend/src/pages/StudentDSAProblem.jsx` | Removed the promise that "successfully passing the test suite … updates your placement metrics"; console panel now renders the static-review signals and the "not executed · not graded" label; fake test-case chips gone. |
| `frontend/src/pages/StudentDSA.jsx` | Same panel/label change in the inline runner. |
| `scripts/release_gate.sh` | Adds the DSA-harness, grading-honesty, data-import and job-feed suites; documents why the dry-run and pilot scripts are run by hand. |
| `docs/data/DATA_SOURCE_REGISTER.csv` | 11 verdicts reconciled with the evidence dossier; new `rights_review_2026_10_24` column on all 48 rows. KMIT demoted to BLOCKED and its year/metric facts corrected. |
| `docs/RELEASE_READINESS.md` | Gate table updated to 195 tests; DSA row rewritten to PARTIAL with the real 20/108 figure and the provenance measurement. |
| `README.md`, `docs/ARCHITECTURE.md`, `FEATURE_GUIDE_FOR_JUDGES.md`, `FINAL_PROJECT_DOCUMENTATION.md` | "Original 12-topic / 108-problem" re-worded to "curated canonical problems under an in-house taxonomy, prompts written here". |
| `docs/audit/PACIO_AUDIT.md` (F-19), `docs/audit/PACIO_BACKLOG.md` (BL-26) | Dated corrections appended, not silent rewrites. |

### Added (19)

| File | Purpose |
|---|---|
| `backend/data_import.py` | Source registry, approval gate, provenance + PII validation, stable keys, content hashes (with per-domain volatile-field exclusion), per-document undo pre-images, batch rollback with conflict detection, `import_runs` audit. |
| `backend/job_feeds.py` | Greenhouse/Lever/Ashby adapters, **robots.txt gate**, body-text exclusion, dedupe, `import_board_snapshot`, first-seen/last-seen/expiry reconciliation. |
| `backend/dsa_specs.json` | 20 complete specs, each with statement, signature, constraints, examples, ≥4 hidden tests, checker, reference, mutant, complexity, edge cases, authoring, provenance and a harness stamp. |
| `backend/tests/test_data_import.py` | 18 tests: approval, provenance, PII, dry-run purity, idempotency, update, rollback pre-image restore, conflict refusal, forced rollback, idempotent rollback, creation-batch provenance. |
| `backend/tests/test_job_feeds.py` | 16 tests: adapter mapping, body-text refusal, dedupe, robots parsing/longest-prefix/401 refusal, crawl-delay, no-fetch-when-refused, unchanged-poll idempotency, expiry lifecycle. |
| `backend/tests/test_dsa_specs.py` | 28 tests: every spec complete with teeth, stamp-gated gradability, missing vs corrupt file, all four checkers, sandbox-boundary pinning. |
| `backend/tests/test_dsa_grading_honesty.py` | 5 tests: review never claims execution/grading, empty submission, draft labelling, submit cannot mark solved or grant mastery, run records a run not a verdict. |
| `scripts/validate_dsa_specs.py` | Restricted-exec harness with `--stamp`, `--specs`, `--csv`; writes per-problem completion CSV. |
| `scripts/import_dry_run.py` | Runs the pipeline against memory or a disposable MongoDB (`--db-name` must start `pacio_dryrun_`); prints JSON evidence. |
| `scripts/job_feed_pilot.py` | Live, rate-limited, robots-aware poll of named boards into a disposable DB, then rollback. |
| `docs/data/DATA_IMPORT_DRY_RUN_REPORT.md` | Deliverable #4. |
| `docs/data/SOURCE_APPROVAL_DECISIONS.md` | Deliverable #3. |
| `docs/data/JOB_FEED_PILOT_REPORT.md` | Deliverable #5. |
| `docs/data/DSA_VALIDATION_REPORT.md` | Deliverable #2. |
| `docs/data/DSA_SPECIFICATION_COMPLETION.csv` | Machine-readable per-problem validation state (108 rows). |
| `docs/data/DSA_CATALOGUE_AUDIT.md` | Independent subagent audit, 48 findings (8 BLOCKER / 28 MAJOR / 12 MINOR). |
| `docs/data/DSA_ORIGINALITY_CHECK.md` | External originality measurement against three public lists. |
| `docs/data/SOURCE_RIGHTS_EVIDENCE.md` | Rights dossier: per-source quotations, URLs, retrieval dates, drafted-but-unsent permission requests. |
| `docs/data/job_feed_pilot_raw*.json` | Raw pilot evidence for both storage engines. |

Temporary artefacts removed: `backend/dsa_specs_draft_batch2.json` (merged into `dsa_specs.json`),
two stray directories created by a mistyped non-ASCII path (each held only the one file written to
it; the files were relocated, the trees deleted).

## 3. Data written, and where

- **Application/development database:** touched only by the release gate's existing suites, which
  are designed to run against it. No imported dataset was written there.
- **Disposable databases:** `pacio_dryrun_import` and `pacio_dryrun_jobs` on the local MongoDB —
  both dropped at the end of their runs (`cleanup: dropped`, `stored_after_rollback: 0`).
- **Production / staging:** untouched. No push, no deploy, no Vercel change.

## 4. Behaviour changes a user can notice

1. Submitting DSA code no longer produces "Accepted" or a pass count; it produces a static review
   and the explicit line "not executed · not graded". Students cannot gain `solved` or 88 mastery
   by submitting code.
2. The same rule applies on the inline runner in the DSA list page.
3. The DSA catalogue now reports `spec_status` of `validated` / `specified_unverified` / `draft`,
   and only the 20 stamped problems are `gradable`.
4. Marketing copy no longer calls the problem bank "original".

## 5. Known remaining defects (not fixed here, deliberately)

| Item | Why not fixed now |
|---|---|
| Seed/demo data still contains invented DSA attempt verdicts and runtimes | It belongs to the clearly-labelled synthetic demo tenant, not to a live grading path. Regenerating it is a seed-data change with migration impact. |
| `question_id` derived from the title slug | Re-wording a title orphans its spec and stored attempts. Today's slug-cap change renamed exactly one id (`dsa_pointers_006`) and the validator caught it — that is the detector working, not a fix. Freeze ids in a manifest before any re-wording campaign. `scripts/rebuild_dsa_progress.py` must be re-run against the dev DB to realign existing progress rows. |
| No per-case timeout in the spec harness | A looping reference hangs the validator; a Windows-safe fix is a subprocess worker. |
| Restricted `exec` is not a sandbox | Measured (`__mro__` escape returns 245 classes). Fine for trusted artefacts only; learner execution needs a real sandbox. |
| 88 problems remain drafts; graphs/heaps/backtracking have zero gradable items | Sequencing decision, documented in `DSA_VALIDATION_REPORT.md` §next-10. |
| Jobs lane not commercially cleared | External: provider ToS unreadable. Only Lever is conditionally allowed. |

## 6. Rollback

Everything here is additive except the twelve modified files:

```
git checkout -- backend/server.py backend/dsa_catalog.py \
  frontend/src/pages/StudentDSA.jsx frontend/src/pages/StudentDSAProblem.jsx \
  scripts/release_gate.sh docs/data/DATA_SOURCE_REGISTER.csv docs/RELEASE_READINESS.md \
  README.md docs/ARCHITECTURE.md FEATURE_GUIDE_FOR_JUDGES.md FINAL_PROJECT_DOCUMENTATION.md \
  docs/audit/PACIO_AUDIT.md docs/audit/PACIO_BACKLOG.md
```

Import batches are reversible individually with `data_import.rollback_batch(batch_id)`, which
restores pre-images and refuses when a later batch touched the same record.
