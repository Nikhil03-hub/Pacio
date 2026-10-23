# Database Recovery, Backup and Restore

Evidence for the development database used in this work. **No production database was
touched, and the original hackathon database was not recovered** — its credentials are
unavailable and no export exists. Everything here is reconstructed demo data.

## Which database this is

| | |
| --- | --- |
| Host | `mongodb://127.0.0.1:27017` (local MongoDB 8.2.1, this machine only) |
| Database | `pacio_dev_verify` — created in this work for local verification |
| Contents | Reconstituted demo data from the repository's seed logic, plus one synthetic second tenant used by the tests |
| Production target | **No.** Production is the Atlas cluster configured by the owner's `MONGO_URL`; it was never contacted or modified |
| Other local databases | The machine also hosts unrelated databases (`careeros`, `studentkmit`, `ecommerceDB`, …). None were read, written or dropped |

The similarly named `careeros` database on this local server pre-dates this work and was
left untouched.

## Backup

Tool: `scripts/mongo_backup_restore.py` (no `mongodump` is installed on this machine).
Format: gzipped JSON Lines in Extended JSON, one metadata line per collection (including
index definitions) followed by one document per line, so ObjectIds and dates round-trip.
GridFS collections are included because they are ordinary collections.

```bash
.venv/Scripts/python.exe scripts/mongo_backup_restore.py backup \
  --uri mongodb://127.0.0.1:27017 --db pacio_dev_verify \
  --out backups/pacio_dev_verify.jsonl.gz
```

Result (VERIFIED): **41 collections, 597,821 documents, 16.4 MB**.
The backup directory is git-ignored because it contains personal-format demo records and
password hashes.

## Restore into a separate database

```bash
.venv/Scripts/python.exe scripts/mongo_backup_restore.py restore \
  --uri mongodb://127.0.0.1:27017 --file backups/pacio_dev_verify.jsonl.gz \
  --db pacio_restore_verify --force
```

Result (VERIFIED): **39 collections / 597,821 documents restored in 55 seconds** into a
fresh database. The restore tool refuses to write into a non-empty database without
`--force` and refuses to target the source database's name.

### Verification

```bash
# backup vs restored database
scripts/mongo_backup_restore.py verify --db pacio_restore_verify --file backups/pacio_dev_verify.jsonl.gz
# backup vs source database
scripts/mongo_backup_restore.py verify --db pacio_dev_verify --file backups/pacio_dev_verify.jsonl.gz
```

Both comparisons reported **every collection matched** (VERIFIED).

### The restored database can run the product (VERIFIED)

Started the API against `pacio_restore_verify`:

- `GET /api/health` → 200.
- `POST /api/auth/login` (demo TPO) → 200 with a session token.
- `GET /api/students?limit=2` → scoped to `inst_kmit`.
- Indexes present and correct:
  - `users.email` unique,
  - `user_sessions.jwt_id` unique,
  - `password_reset_tokens.expires_at` **TTL**,
  - `resume_versions.download_token` **partial unique** (`partialFilterExpression: string`),
  - `rate_limits.key` unique + TTL.
- 7 users had usable password hashes; a sample student record was intact.

The disposable restore database was then dropped; `pacio_dev_verify` was left in place.

## Restart does not duplicate data (VERIFIED)

Counts before and after restarting the API against the same database:

```
users 9 · students 5450 · dsa_questions 474→108 · institutions 57 · jobs 1565
dsa_progress 22140→14760→61200 (see migration below) · dsa_question_progress 340932→…
```

The restart produced identical counts — startup only inserts into empty collections.
(After the DSA curriculum migration, counts changed because the catalogue changed; the
restart itself added nothing.)

## Fail-closed production guard (VERIFIED)

```bash
APP_ENV=production MONGO_URL= JWT_SECRET=probe uvicorn server:app --app-dir backend --port 8098
```

Exit code **3** with `RuntimeError: MONGO_URL is not configured but APP_ENV=production.
Refusing to start on the in-memory fallback…`. A production or Vercel deployment cannot
silently run on ephemeral storage.

## Test cleanup safety (VERIFIED)

- `test_hardening.py` and `test_tenant_isolation.py` force `MONGO_URL=""` before importing
  the app, so they can only ever use the in-memory store.
- `test_mongo_integration.py` creates a database named `pacio_it_<random>` and asserts
  `DB_NAME.startswith("pacio_it_")` before dropping it.
- The migration and rebuild scripts refuse databases that do not start with `pacio_` unless
  `--force-any` is passed.

## DSA curriculum migration and the orphan-row defect

Replacing the catalogue is a data migration, not only a code change. The first attempt
exposed a real integrity bug:

1. `scripts/migrate_dsa_curriculum.py` backed up and dropped the three DSA collections.
2. Startup reseeded them from `seed_payload()`, which invents new student IDs. Because the
   `students` collection already existed, the new progress rows referenced **student IDs
   that do not exist** — 1,230 phantom students. The demo student had no progress and the
   leaderboard resolved to missing names.

Fixes applied:

- Startup and the admin reseed now insert student-derived collections **only into a fresh
  database**; existing deployments never receive rows built from generated IDs.
- `scripts/rebuild_dsa_progress.py` rebuilds progress from **existing** students,
  deterministically per student, and removes orphan rows first.
- Completeness is judged by question-level rows; a student with stale topic rows but no
  question rows is rebuilt (this was exactly the demo account).

Result on `pacio_dev_verify` (VERIFIED):

| Metric | Value |
| --- | --- |
| Questions | 108 (12 topics) |
| Students with progress | 5,099 of 5,100 engineering students |
| Topic rows | 61,200 |
| Question-progress rows | 345,795 |
| Orphaned progress rows | **0** |
| Demo student (`student@kmit.in`) | 27 attempted / 9 solved |

## What was not recovered

- The original classmate-hosted MongoDB: **NOT RECOVERED** (no credentials, no export).
- Any genuine user, partnership, MOU, payout or uploaded document: **NOT AVAILABLE**.
- The earlier 474-question catalogue: replaced by the original 108-problem curriculum;
  the pre-migration arrays were backed up locally to `backups/` before deletion.

No claim is made that this database is, or is equivalent to, the original production data.
