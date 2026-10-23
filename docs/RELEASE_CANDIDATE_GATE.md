# Release-Candidate Gate

Date: 2026-10-23. **Verdict: NO-GO for deployment.** The local checkpoint is verified and
safe to preserve; credentials, staging configuration and external delivery remain open.

## 1. Repository state

| | Pacio-Merged | skill-tank-partner-platform |
| --- | --- | --- |
| Path | `.../Career Guidance/Pacio-Merged` | `.../Career Guidance/skill-tank-partner-platform` |
| Branch | `main` | `main` (no upstream) |
| HEAD | `39f7137` | `83ed1cb` |
| Status | clean working tree | clean working tree |
| Commits vs remote | local commits, **not pushed** | 1 recovery commit, **not pushed** |
| Remote | `Nikhil03-hub/pacio-intelligence` | `Nikhil03-hub/CareerOS-Partner-Intelligence` |

CareerOS AI (workspace root) remains untouched — verified by modification-time scan and by
the absence of any shared files, datasets or remotes.

## 2. Checkpoint integrity evidence

| Check | Result |
| --- | --- |
| Backup file exists and is readable | **VERIFIED** — `backups/pacio_dev_verify.jsonl.gz`, gzip integrity OK, 41 collection headers, 597,821 documents |
| Backup excluded from Git | **VERIFIED** — `.gitignore` `backups/` and `*.jsonl.gz`; `git check-ignore` confirms |
| DSA catalogue | **VERIFIED** — 108 questions, 12 topics, version `2026.10-pattern-v1`, prompts present |
| DSA progress integrity | **VERIFIED** — 61,200 topic rows, 345,796 question rows, **0 orphan** student IDs |
| Demo student data | **VERIFIED** — 27 attempted / 9 solved |
| Diff review | 10 commits: 26 added, 41 modified, 5 deleted. No dependency or database-target changes. No secrets added. The only `drop_database` in the diff is the integration test, guarded by a `pacio_it_` name assertion. Deletions are the two dead pages, the legacy auth callback, and the credential documents. |
| Ignored sensitive files | `backend/.env` ignored; backup ignored |

## 3. Test evidence (this checkpoint)

Command: `bash scripts/release_gate.sh` (runs each suite separately and prints exit codes).

| Suite | Result | Exit |
| --- | --- | --- |
| Hardening | 32 passed | 0 |
| Tenant isolation | 20 passed | 0 |
| Real MongoDB integration | 3 passed | 0 |
| Legacy v2 + v21 | **73 passed** (10 m 09 s) | 0 |

**Total: 128 tests passed, all four suites exit 0** in one clean run
(`/tmp/release_gate_final.log`, HEAD `39f7137`). An earlier run reported 72/73 because of a
stale catalogue-title assertion; it was corrected before this run. A prior gate attempt was
invalidated by an environment bug in the runner script (the legacy demo password was
exported globally, so the hermetic suites seeded a different password than they used to log
in); the script was fixed and re-run from scratch. Both incidents are recorded rather than
hidden because they show why a single clean run matters.

Known environmental limitation: on the in-memory fallback, `/api/placements/overview`
computes readiness for up to 1,000 students and blocks the event loop; the legacy suite is
therefore run against **MongoDB**, which is the production path (BL-31).

## 4. Build and served pages

| Check | Result |
| --- | --- |
| Production build | **VERIFIED** — compiled; 2.8 MB raw JS; no `localhost`/`127.0.0.1` baked into the bundle |
| Stray markup (`"/>`) | **VERIFIED absent** — source, build and served login page |
| Login page desktop | **VERIFIED** — screenshot |
| Login page mobile (390×844) | **VERIFIED** — single column, no overflow, screenshot |
| Certificate verification | **VERIFIED** — `/verify/ST-CRT-RC2026` renders holder/program/institution/date |

## 5. Open gates (must clear before preview)

1. **P0 credentials** — rotate the Jooble key and demo password; remove surviving demo
   accounts. Code no longer contains literals; history still does.
   See `CREDENTIAL_REMEDIATION.md`.
2. **P1 staging database** — create/choose an Atlas cluster and a least-privilege user; do
   not point production or preview at the local synthetic database. See `STAGING_ENV.md`.
3. **P1 production configuration** — set `JWT_SECRET`, `MONGO_URL`, `PUBLIC_BASE_URL`,
   `ALLOWED_ORIGINS`, Google OAuth credentials. A missing `MONGO_URL` now refuses to boot.
4. **P1 external delivery** — real email and Telegram messages have never been observed;
   everything is `simulated`. Google OAuth has not completed a real round trip.
5. **P2 browser acceptance on a deployed preview** — authenticated journeys were not
   clickable in this environment; see `ACCEPTANCE_CHECKLIST.md`.

## 6. Go / no-go

**NO-GO** for production or a public preview promotion. The local artifact is reproducible,
tested and honest about its data; it is blocked on owner-controlled credentials,
staging configuration and external-integration proof. The correct next milestone is a
**preview deployment with staging-only settings**, then re-run the acceptance checklist
against that URL.
