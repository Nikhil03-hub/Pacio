# Data Import Dry-Run Report

Phase 2, Workstream B deliverable #4. Generated 2026-10-24.

Command (run twice, once per engine):

```
.venv/Scripts/python.exe scripts/import_dry_run.py
.venv/Scripts/python.exe scripts/import_dry_run.py --mongo-url mongodb://127.0.0.1:27017 --db-name pacio_dryrun_import
```

Exit code: `0` for both runs. Raw JSON captured in `scripts/import_dry_run.py` stdout; the two runs
produced byte-identical behavioural results (`engine` and `ran_at` apart).

## What this proves and what it does not

**No real dataset was imported.** Every record in the run is a synthetic fixture whose
`data_status` is `synthetic` and whose `source_url` is `https://example.org/...`. The registered
source is `SRC-FIXTURE — "Pipeline fixture (not a real source)"`.

The purpose is to prove the *mechanism* — approval gating, provenance enforcement, PII refusal,
dry-run purity, idempotency, and reversible rollback — before any approved dataset is loaded.
Mechanism VERIFIED. Real-data import NOT RUN (blocked on `SOURCE_APPROVAL_DECISIONS.md`).

Both runs used a disposable store. The MongoDB run created database `pacio_dryrun_import`, used it,
and dropped it (`"cleanup": "dropped"`). The application development database and the synthetic demo
tenant were not touched. `--db-name` refuses any name not starting with `pacio_dryrun_`, so the
script cannot be pointed at a real database by accident.

## Evidence

| Check | Expected | Observed | Status |
|---|---|---|---|
| Dry-run writes nothing | 0 documents after `dry_run` | `dry_run_wrote_documents: 0` | VERIFIED |
| Unregistered source refused | `PermissionError` | covered by `test_unregistered_source_is_refused` | VERIFIED |
| Non-approved source refused | `PermissionError` | `rejected_source_blocked: true` | VERIFIED |
| PII field refused | invalid record reported | `pii_rejected: true` | VERIFIED |
| First import inserts | `new: 3` | `first_import: {new:3, updated:0, unchanged:0}` | VERIFIED |
| Re-import is idempotent | no writes | `second_import: {new:0, updated:0, unchanged:3}` | VERIFIED |
| Changed record updates | `updated: 1` | `changed_import: {new:0, updated:1, unchanged:2}` | VERIFIED |
| Rollback refuses a dirty batch | no deletions | `status: blocked_conflict`, `deleted: 0`, `restored: 0` | VERIFIED |
| Rollback of an update restores the old value | value reverts | `name_after_restore: "Fixture Institute Two"` | VERIFIED |
| Rollback of a clean batch removes its inserts | all gone | `deleted: 3`, `stored_after_rollback: 0`, `remaining_keys: []` | VERIFIED |
| Audit trail written | runs + undo items recorded | `import_runs: 3`, `undo_items: 4`, `sources_registered: 2` | VERIFIED |

## The defect this run found, and the fix

The first version of `rollback_batch` deleted every document carrying the batch's
`import_batch_id`. Two ways that is wrong:

1. **A record only *updated* by a batch was deleted outright**, destroying data that existed before
   the batch and had nothing to do with it.
2. **A later batch re-stamped the same record**, so rolling back the *earlier* batch silently
   skipped the record it had actually created — the leftover `SRC-FIXTURE:AICTE-FIXTURE-2` in the
   first run of this script was exactly that leak.

`backend/data_import.py` now writes a per-document undo item (`import_batch_items`: `seq`, `action`,
`before` pre-image, `after_hash`) for every write, keeps `first_import_batch_id` stable across
updates, and rolls back newest-first from the pre-images. If a live record no longer matches what
the batch wrote, the rollback **refuses and changes nothing** unless the operator passes
`force=True`, because overwriting another batch's work is worse than an aborted rollback.
Regression coverage: `backend/tests/test_data_import.py` — 18 tests pass, including
`test_rollback_of_update_restores_pre_image`, `test_rollback_refuses_when_a_later_batch_modified_the_record`,
`test_forced_rollback_overrides_conflict`, `test_rollback_is_idempotent`.

## Domain contracts now enforced

`institutions` → `institutions_public`, key `source:official_id`.
`placement_stats` → `placement_stats`, key `source:institution:year:metric`, requires a written
`definition` and a `published_on` date.
`jobs` → `job_postings`, key `source:board:external_id`, requires an `http(s)` `apply_url`.

All three require `source_url`, `retrieved_at` and an explicit `data_status` from
`published | synthetic | unverified | draft`. Any key in `PII_KEYS` (name, email, phone, mobile,
contact) aborts the record. A batch containing one invalid record imports **nothing** — the failure
is raised before the first write.

## Known limitations (not yet solved)

- `import_batch_items` is read into memory in full before a rollback. Fine at fixture scale, needs
  cursoring before a six-figure batch. PARTIAL.
- Rollback restores field content but the store mints a new `_id`; nothing in the pipeline reads
  `_id`, and `stable_key` is the identity — documented in the code. PARTIAL.
- No row-level merge: an out-of-band UI edit inside a batched field is a conflict, and the operator
  must decide. Deliberate, not a bug.
- Concurrency: two imports of the same source running at once can interleave. Needs a per-source
  advisory lock before any scheduled ingestion. NOT RUN.

## GO / NO-GO for this milestone

**GO on the mechanism. NO-GO on loading any real dataset.** The pipeline is safe to keep behind an
approval gate; the gate currently has no approved real source to let through. The next action is not
more pipeline code — it is the verdicts in `SOURCE_APPROVAL_DECISIONS.md` and a small first import
from whichever source survives them.
