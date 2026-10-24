# Pacio Handoff

Current state, what changed, what is blocked, and how to verify it yourself.

## Status at a glance

| | |
| --- | --- |
| Repository | `Pacio-Merged`, remote `Nikhil03-hub/pacio-intelligence` (**public**) |
| Branch | `main`; **eight local commits** added in this work, **not pushed** |
| Baseline before this work | HEAD `6aa0f44`, clean tree except one untracked audit file |
| Tests | **212 passed in one clean gate run** (32 hardening + 20 tenant-boundary + 44 DSA harness + 6 DSA grading honesty + 18 data import + 16 job feeds + 3 real-MongoDB + 73 legacy; every suite exit 0, final 2026-10-25 run) |
| Frontend build | Compiles clean; 884 kB gzipped JS |
| Live site | `https://pacio-two.vercel.app` reachable; **not modified** by this work |
| Sub-product | `../skill-tank-partner-platform` - Next.js/Supabase, has **uncommitted** work |

## What changed here

**Commit 1 - backend security and tenancy.** Tenant resolution centralised (19 routes had
an `or "inst_kmit"` fallback); bearer-token session revocation; password reset hardened
(digest storage, single use, minimum length, sessions purged, no enumeration); OAuth state
check made fail-closed; invitations stopped issuing a shared published password; reset
links no longer trust the Host header; MOU documents role-gated with upload validation;
students restricted to their own records; regex and limit abuse closed; anonymous
telemetry removed; MongoDB index creation actually runs on the production path; demo
accounts made opt-in with the admin bootstrapped from env; legacy Emergent auth disabled;
`JWT_SECRET` now required to boot.

**Commit 2 - UI, design system and truthfulness.** `ink`/`bone` gained `DEFAULT` shades so
~375 previously dead class usages take effect (the shared primary button had no background
and modal scrims were transparent); `num-mono` defined with tabular figures; disabled button
styling; flat hover states fixed; muted label contrast raised from 2.8:1 to 4.5:1;
pinch-zoom re-enabled; two never-mounted intelligence components wired in; dead pages
deleted; the fabricated benchmark table and invented "National Placement Census" citation
replaced with the real partner-benchmarking endpoint; landing-page customer logos, "real
customers" claims and five-star reviews relabelled as demonstration/illustrative;
certificates now persist and verify at `/verify/:certId`; login gained a capability check
and an email path so a fresh clone is usable.

**Then:** credential documents removed from tracking and sanitised, `.env.example`, a
proprietary `LICENSE`, third-party branding stripped from the DSA catalog identifiers, and
the documentation set.

**Then (data + release-candidate pass):** replaced the third-party DSA catalogue with an
original 12-topic / 108-problem curriculum (original prompts and rationale), migrated the
dev database, and fixed a seeding bug that had created 1,230 orphan progress rows when a
partial reseed regenerated student IDs. Added `scripts/mongo_backup_restore.py`,
`scripts/migrate_dsa_curriculum.py`, `scripts/rebuild_dsa_progress.py`, removed the
fabricated Jooble fallback jobs, and documented [CREDENTIAL_REMEDIATION.md](CREDENTIAL_REMEDIATION.md)
and [DATABASE_RECOVERY.md](DATABASE_RECOVERY.md). A backup/restore drill passed and the
restored database ran the API.

**Then (real-database pass):** running against a fresh local MongoDB exposed that the Mongo
startup path seeded only six collections, leaving jobs, the entire DSA catalog, placements,
training and announcements empty on any real deployment — while the in-memory demo looked
complete. Fixed, along with missing aptitude/resume backfills and health scores. Added
fail-closed production startup, shared-store rate limiting, a central approval gate, and
staff-only exports. New suites: a Tenant-A-vs-Tenant-B matrix (20), real-MongoDB integration
(3), and fail-closed/rate-limit regressions. Evidence:
`docs/RELEASE_READINESS.md`, provenance: `docs/DATA_PROVENANCE.csv`, git:
`docs/GIT_REPORT.md`.

## Where to look

| Need | Path |
| --- | --- |
| Findings and requirement traceability | `docs/audit/PACIO_AUDIT.md` |
| Open work with acceptance criteria | `docs/audit/PACIO_BACKLOG.md` |
| How to run, test, back up | `docs/SETUP_AND_RECOVERY.md` |
| System shape | `docs/ARCHITECTURE.md` |
| Data provenance and rights | `docs/DATA_SOURCES.md` |
| Third-party services | `docs/INTEGRATIONS.md` |
| Security posture | `docs/SECURITY_AND_PRIVACY.md` |
| Market and cost evidence | `docs/COMMERCIAL_READINESS.md` |
| Demo accounts without leaking secrets | `docs/DEMO_ACCESS.md` |
| Prior audit (Sept 2026, partly superseded) | `pacio-audit-findings.md` |

## Commands

```bash
# backend tests (no server needed)
.venv/Scripts/python.exe -m pytest backend/tests/test_hardening.py -q

# legacy suites (needs a running backend)
.venv/Scripts/python.exe -m uvicorn server:app --app-dir backend --port 8000
REACT_APP_BACKEND_URL=http://127.0.0.1:8000 .venv/Scripts/python.exe -m pytest backend/tests/test_careeros_v2.py backend/tests/test_careeros_v21.py -q

# frontend
cd frontend && npm run build
```

## Blocked / needs a decision from the owner

1. **Rotate and contain exposed credentials.** The demo password and a Jooble key are in
   public git history. Decide: rotate only, rewrite history (`git filter-repo`, force push),
   or make the repository private. None was done unilaterally because each is destructive
   or externally visible.
2. **Vercel environment variables could not be inspected from here.** Confirm `JWT_SECRET`,
   `MONGO_URL`, `PUBLIC_BASE_URL`, `ALLOWED_ORIGINS` and the Google OAuth pair. A missing
   `MONGO_URL` now makes a production build **refuse to start** (it used to lose data on
   every cold start), so set it before deploying these commits.
3. **Production demo accounts.** New deployments no longer create them, but rows already in
   Atlas remain. Mutating a live database was not attempted.
4. **Brand.** `careeros.com` is an operating product in the same category and
   `careeros.app` belongs to someone else. Renaming to Pacio is a business decision.
5. **DSA curriculum rights.** takeUforward's terms prohibit commercial use without written
   consent. Licence it or replace the catalog before selling.
6. **Seed data names real colleges** with invented MOUs, payouts and offers.
7. **Accent colour contrast** fails AA for small text; changing it alters the brand, so it
   was left for design sign-off (BL-23).
8. **Pushing.** Two commits are local only. Nothing was pushed, published or deployed.

## Sub-product note (`skill-tank-partner-platform`)

Uncommitted work exists there: 24 modified files plus untracked `src/components/ui/` and
`src/app/globals.css`. **The tracked edits import the untracked components**, so
`git clean -fd` or a bare checkout would break the build (`tsc --noEmit` passes as it
stands). It is a half-applied UI migration: the new palette file is imported by nothing and
one new primitive is unused. Committing or discarding someone's in-progress work is a
decision for the owner; the recommended handling is recorded in the backlog.
