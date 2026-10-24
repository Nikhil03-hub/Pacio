# Release Readiness

Separates four things that are easy to confuse: what was verified locally, what was
verified against a real database, what depends on external services, and what cannot be
verified without the owner's production access.

**Verdict: not production-ready, not commercially ready.** The local product is now
substantially safer and more honest than the hackathon build, and the core Track 5B
workflow works against a real MongoDB. Notification delivery, production configuration,
rights and demand remain unproven.

Environment for every result below: Windows 11, Python 3.12 (repo `.venv`), Node 22.21,
MongoDB 8.2.1 on `127.0.0.1:27017`, no third-party API credentials.

## 1. Verified locally (reproducible)

| Check | Command | Result |
| --- | --- | --- |
| Security/authorisation regressions | `pytest backend/tests/test_hardening.py -q` | **32 passed**, ~93 s |
| DSA specification harness | `pytest backend/tests/test_dsa_specs.py -q` | **44 passed** |
| DSA grading honesty | `pytest backend/tests/test_dsa_grading_honesty.py -q` | **6 passed** |
| Data import pipeline | `pytest backend/tests/test_data_import.py -q` | **18 passed** |
| Job feed adapters | `pytest backend/tests/test_job_feeds.py -q` | **16 passed** |
| Total | 32 + 20 + 44 + 6 + 18 + 16 + 3 + 73 | **212 passed, every suite exit 0** (final run 2026-10-25) |
| Multi-tenant role matrix (Tenant A vs synthetic Tenant B) | `pytest backend/tests/test_tenant_isolation.py -q` | **20 passed**, ~102 s |
| Real-MongoDB integration | `PACIO_TEST_MONGO_URL=mongodb://127.0.0.1:27017 pytest backend/tests/test_mongo_integration.py -q` | **3 passed**, ~18 s |
| Legacy feature suites | `bash scripts/release_gate.sh` against a Mongo-backed server with `RATE_LIMIT_ENABLED=false` | **73 passed** (7 m 01 s), exit 0 |
| Frontend production build | `cd frontend && REACT_APP_BACKEND_URL= CI=false npm run build` | compiled, exit 0; 885 kB gzipped JS |
| Certificate verification page | served build, `/verify/ST-CRT-RC2026` | renders VALID with holder/program/institution; screenshot captured |
| Login page (served build) | `http://127.0.0.1:8073/login` | renders; no stray markup in the top-left corner; screenshot captured |
| No local backend URL in the bundle | grep of `build/static/js/main.*.js` | 0 occurrences of `localhost` or `127.0.0.1` |
| Stray `"/>` in the old certificate screenshot | source + build + commit check | **not present**: source clean, built HTML clean, fix shipped in commit `58d6dc5`. The screenshot was taken before that commit, from an earlier build. |

Covered by the two new suites specifically: tenant scoping on rosters, peer records,
resumes, MOUs, payouts, analytics, exports and comm logs; students blocked from staff
exports; pending accounts blocked from all data routes while still able to read their own
identity and submit onboarding; super-admin global access; session revocation; rate
limiting (429 + `Retry-After`); fail-closed production startup.

### Release-candidate checks added in this pass

- Backup and restore drill: see [DATABASE_RECOVERY.md](DATABASE_RECOVERY.md) (VERIFIED).
- Credential posture and provider steps: see [CREDENTIAL_REMEDIATION.md](CREDENTIAL_REMEDIATION.md).
- DSA catalogue replaced with an original curriculum; orphan progress rows fixed; **0** orphans remain.
- Jooble now returns an empty feed with a warning when unconfigured (no fabricated listings).
- Full diff review: no dependency or database-target changes, deletions intentional, no secrets
  in the current tree, backup directory git-ignored.

## 2. Verified against a real MongoDB (local instance, fresh database)

The full seeding path was exercised on a brand-new database (`pacio_dev_verify`), then the
database was dropped after use.

| Check | Result |
| --- | --- |
| Startup connects to Mongo | log: "MONGO_URL configured"; `/api/health` 200 |
| Full seed (after fixing the Mongo-path gaps) | 57 institutions, 5,450 students, 1,565 jobs, 979 applications, **108 DSA questions over 12 topics**, 61,200 topic-progress rows, 345,795 question-progress rows, 282 aptitude questions, 4,920 aptitude scores, 858 placement records, 56 MOUs, 165 revenue records |
| Index creation on Mongo | unique `users.email`, unique `user_sessions.jwt_id`, TTL `password_reset_tokens.expires_at`, unique `rate_limits.key`, unique `certificates.cert_id`, plus roster/query indexes |
| Health backfill | 57/57 institutions have a computed `health_score` |
| Backup / restore drill | `scripts/mongo_backup_restore.py`: 41 collections / 597,821 documents backed up (16.4 MB); restored into a separate database; every collection count matched; the API ran against the restored database (login + roster + indexes verified); the disposable database was dropped |
| Restart duplication | Counts identical before and after restart (no repeated seeding) |
| DSA migration integrity | Orphan progress rows: **0**; demo student has 27 attempted / 9 solved after the rebuild |
| Jooble without a key | Returns `source: "unconfigured"`, `jobs: []`, warning — no invented listings |
| Persistence across a real process restart | session token still valid (200), certificate still verifies, jobs endpoint 200 |
| Logout revocation | same token after logout → 401 |
| Rate limiting across instances | 10×401 then 429 with `Retry-After`; counters stored in Mongo (`rate_limits`) |
| Fail-closed production guard | `APP_ENV=production MONGO_URL=` → exit code 3, `RuntimeError: MONGO_URL is not configured but APP_ENV=production…` |

### Defects this revealed (now fixed)
1. The Mongo startup path seeded only six collections. **Jobs were empty and the entire DSA
   catalog (474 questions / 340k progress rows at the time; now the 108-problem original curriculum) was missing**, which silently broke the jobs
   board and 30% of the readiness score on any real deployment while the in-memory demo
   looked complete.
2. Aptitude progress and resume versions were backfilled only on the in-memory path, so ATS
   history and the aptitude tracker were empty on Mongo.
3. Health scores were never computed on the Mongo path.
4. Cold start rebuilt ~340k seed rows in memory on every boot even when the database was
   already populated (minutes of latency); it now probes first and only seeds an empty
   deployment. Populated-database startup measured at ~35 s.
5. An interrupted frontend build left `frontend/build/` empty, and the unconditional
   `StaticFiles` mount crashed the whole API at import. Mounting is now guarded.

## 2b. Data discovery (research complete, no import)

48 sources were investigated across public repositories, official portals and job APIs.
Findings and licensing verdicts: `docs/data/DATA_SOURCE_DISCOVERY_REPORT.md` and
`docs/data/DATA_SOURCE_REGISTER.csv`. Headline: no openly licensed multi-college,
company-level placement dataset exists; KMIT publishes per-company figures only through
2023-24; AISHE/AICTE data is readable but redistribution needs written consent; OGD is the
cleanest licensed route; Adzuna is the best India job feed but requires a paid licence.

## 3. Depends on external services — NOT verified

| Integration | Status | How to prove it |
| --- | --- | --- |
| SendGrid email | **simulated** in every run (no key) | set `SENDGRID_API_KEY` + verified `SENDER_EMAIL`, trigger an invite, confirm provider message id and inbox arrival |
| Telegram | **simulated** (no token/chat id) | set `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`, trigger an alert, confirm receipt |
| Google OAuth | **not exercised** (no client credentials) | configure the OAuth client, complete a real sign-in, confirm pending → approval → workspace |
| Jooble job feed | **not exercised**; key must be rotated | rotate, set env, confirm listings plus graceful empty state when the key is absent |
| LLM feedback | deterministic fallback only | set the key, compare output quality, confirm cost per call |
| QR rendering (`api.qrserver.com`) | not exercised; certificate id is disclosed to a third party | replace with a local encoder before relying on it |
| LiveAvatar interview embed | not exercised | confirm the iframe loads and degrades if the vendor is down |

## 4. Production configuration — NOT inspected

The deployed site `https://pacio-two.vercel.app` responds 200 with `X-CareerOS-Release: v3`,
but it is serving the **pre-audit build**: this work is committed locally and was not
pushed, so production cannot contain it. Whether the live deployment has `MONGO_URL`,
`JWT_SECRET`, `PUBLIC_BASE_URL`, `ALLOWED_ORIGINS` and Google credentials set could not be
determined from this machine. Treat these as owner checks:

1. `MONGO_URL` set and reachable (otherwise the new build will **refuse to start**, by design).
2. `JWT_SECRET` set to a long random value.
3. `PUBLIC_BASE_URL` and `ALLOWED_ORIGINS` set to the real domain.
4. Google OAuth client + redirect URI configured.
5. Any demo accounts remaining in Atlas removed, and the exposed password rotated.

## 5. Commercial blockers (unchanged unless stated)

| Blocker | Status |
| --- | --- |
| Exposed credentials in public git history | **OPEN** — rotate at providers; decide history rewrite vs private repo |
| DSA curriculum rights + validation | **PARTIAL (2026-10-24)** — 108 curated canonical problems under an in-house 12-topic taxonomy. **36/108 now have machine-validated gradable specs** (reference passes, mutant caught, harness-stamped; see `docs/data/DSA_VALIDATION_REPORT.md`); 72 remain prose drafts. All twelve topics have at least one grader, including graphs, heaps, backtracking and two Hard problems. Originality measured: 91/108 titles are standard industry names, prompt overlap 1/1,283 6-grams, and the word "original" was removed from the marketing copy. Depth is still thin: 78 drafts, only two Hard problems, and the in-app runner does not execute learner code. The catalogue must not be advertised as auto-gradable |
| Brand collision (`careeros.com`) | **OPEN** — owner naming decision |
| Seeded data names real colleges with invented partnerships/payouts | **OPEN** — fictionalise or obtain permission |
| No customer, pilot, LOI, tender or willingness-to-pay evidence | **OPEN** — the only sourced price in the category is one competitor's list price (₹25k–55k/month) |
| Single Vercel function constraints (300 s, 4.5 MB payload, WebSockets beta) | **OPEN** — split the backend before paying tenants |

## 6. What would move this to "release candidate"

1. Push to a preview deployment with the production variables set, then re-run the local
   suites against that URL.
2. Prove one real email and one real Telegram message with provider ids.
3. Rehearse an Atlas backup/restore and record the restored counts.
4. Resolve or isolate the rights blockers above.
5. Add CI so the 212 tests run on every change, and a browser-level journey suite.
