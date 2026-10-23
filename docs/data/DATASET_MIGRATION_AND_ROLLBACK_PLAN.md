# Dataset Migration and Rollback Plan

Status: **proposal — not executed.** It describes how to move from synthetic demo data to a
mixed dataset safely, and how to undo every step. Production is out of scope until the
release gate passes.

## Preconditions

1. Staging database exists and is **not** production or the local `pacio_dev_verify`.
2. `JWT_SECRET`, `MONGO_URL`, `PUBLIC_BASE_URL`, `ALLOWED_ORIGINS` set for staging.
3. Source register marks every source `APPROVED` or `APPROVED_WITH_LIMITATIONS`.
4. Fresh backup taken **after** the last code deployment and **before** the first import.
5. Freeze window: no other writers during import.

## Step 0 — Freeze and snapshot

```bash
# Backup the staging database (records the file outside Git)
.venv/Scripts/python.exe scripts/mongo_backup_restore.py backup \
  --uri "$STAGING_MONGO_URI" --db "$STAGING_DB" \
  --out backups/staging-preimport-$(date +%Y%m%dT%H%M%SZ).jsonl.gz

# Record baseline counts
mongosh "$STAGING_MONGO_URI/$STAGING_DB" --eval '
  ["institutions","students","jobs","placements","mous","revenue_share","dsa_questions"]
    .forEach(c => print(c + "=" + db.getCollection(c).countDocuments()))'
```

Expected synthetic baseline (local demo): institutions 57, students 5,450, jobs 1,565,
placements 858, MOUs 56, revenue 165, DSA 108.

## Step 1 — Label synthetic data (non-destructive)

Add `data_status: "synthetic"` to demo records so no future import can be confused with
them. This is a `$set` on documents that lack the field; nothing is deleted.

```javascript
db.students.updateMany({data_status: {$exists: false}}, {$set: {data_status: "synthetic"}})
db.institutions.updateMany({data_status: {$exists: false}}, {$set: {data_status: "synthetic"}})
db.jobs.updateMany({data_status: {$exists: false}}, {$set: {data_status: "synthetic"}})
db.placements.updateMany({data_status: {$exists: false}}, {$set: {data_status: "synthetic"}})
db.mous.updateMany({data_status: {$exists: false}}, {$set: {data_status: "synthetic"}})
db.revenue_share.updateMany({data_status: {$exists: false}}, {$set: {data_status: "synthetic"}})
```

Rollback: `$unset` the field where `data_status: "synthetic"` (or restore the backup).

## Step 2 — Create new collections, do not overwrite

`source_registry`, `institutions_public`, `placement_stats`, `employer_boards`,
`job_postings`, `import_runs` are new. The synthetic `institutions` / `placements` remain
available to the demo tenant.

Every imported document carries:

```json
{
  "import_batch_id": "imp_20261023T1900Z_aishe_01",
  "source_id": "SRC-AISHE",
  "source_url": "https://...",
  "retrieved_at": "2026-10-23T19:00:00Z",
  "published_on": "2024",
  "verification_status": "verified_public",
  "data_status": "published"
}
```

Jobs additionally store `dedupe_key`, `first_seen`, `last_seen`, `expires_at`, `status`.
Placement statistics additionally store `metric` and `definition`.

## Step 3 — Import and verify

For each batch:

1. Stage into `<collection>_staging` and compute a dry-run diff (new/changed/conflict).
2. Review the diff; abort on unexpected deletes.
3. Upsert into the target collection by the stable key (`aishe_code`, `dedupe_key`,
   `(institution_id, academic_year, metric)`).
4. Rebuild derived aggregates only from documented definitions.
5. Run integrity checks:
   - no duplicate stable keys,
   - every document has `source_id`, `source_url`, `retrieved_at`,
   - every placement metric has a `definition`,
   - no orphan `institution_id`,
   - no student PII in public collections.
6. Run `pytest backend/tests/test_hardening.py backend/tests/test_tenant_isolation.py` and
   the legacy suite, and `scripts/mongo_backup_restore.py verify` for the new backup.

## Step 4 — Application switch

The app keeps reading the synthetic collections until a feature flag is added. Planned flag:
`DATA_MODE=demo|staging|production`, controlling which collections back the dashboards.
**Not implemented yet**; until then, importing new collections changes no UI.

## Rollback

| Failure | Action |
| --- | --- |
| Bad import batch | Delete documents with that `import_batch_id` from the target and staging collections; the synthetic data is untouched |
| Bad schema change | Restore the pre-import backup with `scripts/mongo_backup_restore.py restore --db <new_db>`, verify, then repoint staging `MONGO_URL` |
| App regression after switch | Set `DATA_MODE=demo` (once implemented) or roll back the deployment; data remains intact |
| Accidental overwrite of synthetic rows | Restore the pre-import backup into a fresh database and compare counts before switching back |

Never "fix" a bad import by dropping a database. Never regenerate IDs for existing entities.

## Explicit prohibitions

- No import into production during this gate.
- No bulk scraping of sources whose terms prohibit it.
- No importing real student records or contact data.
- No presenting synthetic partnerships, payouts or outcomes as genuine.
- No silent replacement of records that existing foreign keys reference.

## What must exist before execution

1. `DATA_MODE` feature flag and UI data-status badges.
2. Import tooling with batch IDs and dry-run output (not built).
3. Licensed/approved sources in `source_registry`.
4. A staging deployment to test against.
