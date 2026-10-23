# Pacio — Audit and Requirements Traceability

**Audit date:** 2026-10-23 · **Auditor:** Qoder agent (read-only audit, then implementation)
**Repository audited:** `Pacio-Merged` — remote `https://github.com/Nikhil03-hub/pacio-intelligence` (**public**, no licence file before this work)
**Baseline before changes:** branch `main`, HEAD `6aa0f44`, working tree clean except untracked `pacio-audit-findings.md`
**Live deployment checked:** `https://pacio-two.vercel.app` — HTTP 200, `X-CareerOS-Release: v3` (read-only checks; no login attempted against production)

---

## 1. What this product actually is

Internally named **CareerOS — Campus Intelligence**, deployed as **Pacio**. A multi-tenant
B2B SaaS dashboard for Indian college placement cells, built to satisfy **SummerSaaS
Hackathon Finale, Track 5B — "Skill Tank: College/TPO Partner Dashboard"**.

Stack: React 18 (CRA) + Tailwind SPA · FastAPI monolith (`backend/server.py`, 7,183 lines,
151 routes) · MongoDB via Motor with a hand-written in-memory Mongo-compatible fallback
(`memory_db.py`) · deployed on Vercel as a single Python serverless function
(`api/index.py` → `server.app`) that also serves the built SPA.

`skill-tank-partner-platform` (Next.js + Supabase) is the **sub-product / predecessor**
that Pacio-Merged absorbed features from. It is a separate git repository
(`Nikhil03-hub/CareerOS-Partner-Intelligence`) and is assessed separately.

### Historical leads from the handoff — verified

| Lead | Verdict |
| --- | --- |
| "Pacio-Merged had only a collaborator's remote" | **No longer true.** Origin is now the owner's own account `Nikhil03-hub/pacio-intelligence`. History still shows the earlier submission repo `Manju10092006/Pacio` (clone source, per `pacio merged cmd.txt`). |
| "CareerOS AI is a separate project" | Confirmed. The workspace root `README.md` describes a different app (after-10th stream guidance). Not touched. |
| "There may be uncommitted local changes" | Confirmed in the **sub-product** (24 modified + 2 untracked paths, uncommitted). Pacio-Merged itself was clean. |
| "Module 3 final / winning module" | The recovered brief is the SummerSaaS Track 5B problem statement (15 must-haves, 10 good-to-haves) plus 13 general rules. No judging rubric or score sheet was found in the repository or in `~/Downloads`. |

---

## 2. Requirements traceability — Track 5B must-haves

Status vocabulary: **verified** (code path read and exercised), **partial**, **broken**,
**missing**, **unverified** (present in code but not provable from here).

| # | Requirement | Where it lives | Status | Evidence / gap |
| --- | --- | --- | --- | --- |
| 1 | TPO signup + admin approval before activation | `POST /api/auth/register`, `POST /api/signup`, `GET /api/admin/pending-signups`, `POST /api/admin/approve/{id}`, `pages/Register.jsx`, `pages/OnboardingPending.jsx` | **verified** | Approval now also assigns role (`ApproveUserBody.role`). Re-inviting a pending user re-scopes instead of 409. |
| 2 | College profile: university, departments, partnership type | `pages/CollegeProfile.jsx`, `/api/institutions`, `/api/institutions/{id}/departments` | **verified** | |
| 3 | Student roster view/add | `/api/students` GET/POST, `pages/StudentRoster.jsx` | **verified** | POST gated to staff; students can now read only their own row. |
| 4 | Program/cohort tracking with enrolment status | `/api/cohorts`, `pages/Cohorts.jsx`, `enrollments` | **verified** | |
| 5 | Placement outcomes dashboard | `/api/placements/overview`, `pages/PlacementIntelligence.jsx` | **verified** | |
| 6 | Training completion per student | `/api/training/completion`, `pages/Training.jsx` | **verified** | |
| 7 | MOU upload/store/view + term and renewal | `/api/mou`, `/api/mou/upload`, `/api/mou/download`, `/api/mou/renew`, GridFS | **verified (fixed)** | Was open to students and accepted any file type; now role-gated with type/size checks. |
| 8 | FDP scheduling + attendance | `/api/fdp/schedule`, `/api/fdp/attendance`, `pages/FDPManagement.jsx` | **verified** | |
| 9 | Downloadable PDF/CSV reports | `backend/reports.py`, `/api/reports/*.pdf`, `/api/reports/*.csv`, `pages/Reports.jsx` | **verified** | |
| 10 | Revenue-share and payout visibility | `/api/revenue/me`, `/api/revenue/share`, `/api/revenue/approve-payout`, `pages/Revenue.jsx` | **verified (fixed)** | TPO could read but not write (403); body-supplied `institution_id` allowed writing to another tenant. Both fixed. |
| 11 | Communication log with account manager | `/api/comm-log` CRUD, `pages/CommLog.jsx` | **verified** | |
| 12 | Multi-user access per college with permission scoping | `/api/invite`, `/api/institution/users`, `pages/TeamInvites.jsx`, `require_roles` | **verified (changed)** | Invitations no longer issue a shared password; activation happens on first Google sign-in. |
| 13 | Renewal/expiry alerts before MOU end | `/api/notifications/generate-alerts`, `days_until_renewal` in `/api/mou` | **verified** | Alert generation is on-demand; **no scheduler is configured** (see BACKLOG BL-11). |
| 14 | Automated Email + WhatsApp/Telegram triggers | `backend/notification_service.py` | **partial — live delivery unverified** | Code fans out to SendGrid + Telegram and always logs to `notification_log`. No API keys exist locally, so every message was `simulated`. Whether real delivery works in production cannot be verified from here (needs the Vercel env and a test inbox). |
| 15 | Central admin panel that can act on all data | `pages/PlatformControl.jsx`, `pages/AdminPanel.jsx`, `/api/admin/*` | **verified** | |

### Good-to-haves (10)

| Requirement | Status |
| --- | --- |
| Anonymised peer benchmarking | **verified** — `/api/benchmarking/partner` (self, averages, top band, leaderboard, percentile) |
| TPO ↔ account-manager chat | **verified** — `/api/chat/room`, `/api/chat/messages`, `/ws/live` (token-authenticated, institution-scoped rooms) |
| Workshop / event request flow | **verified** — `/api/workshops`, status PATCH |
| Student-level drill-down | **partial** — data is reachable per student, but there is no unified "Student 360" admin page (the parity audit already flagged this) |
| Co-branded certificates | **verified (fixed)** — certificates were browser-only and their QR encoded `https://careeros.app/verify/<id>`, a domain the project does not own, for a route that did not exist. Now persisted via `POST /api/certificates/issue` and verified at `/verify/:certId`. |
| Automated digest report | **verified** — `POST /api/digest/send` |
| Companies that hired from this college | **verified** — placement intelligence |
| College leaderboard for admin | **verified** — benchmarking leaderboard |
| MOU e-signature | **partial** — `/api/mou/esign` records a signed state; there is no real signature provider integration |
| Budget / seat tracking | **partial** — seats live inside MOU/revenue records; no first-class seat-allocation page |

### General hackathon rules worth flagging

- **Rule 3 "real, working database"**: satisfied when `MONGO_URL` is set. If it is not, the
  app silently runs on `MemoryDB`, and on Vercel **every cold start erases all users,
  sessions, uploads and reset tokens**. This is the single largest operational risk.
- **Rule 5 "seeded data on every screen"**: satisfied — startup seeds 56 institutions,
  5,450 students, 1,565 jobs, 979 applications and 22,140 DSA rows. Note this contradicts
  `memory/PRD.md`, which claims 6 institutions / 470 students; the docs are stale.
- **Rule 12 "no broken links / placeholders"**: the landing page previously carried
  fabricated customer logos, "real results from real customers" and five-star reviews. Fixed.

---

## 3. Findings and severity (what was wrong, ranked)

### Critical — fixed in this work

| ID | Finding | Fix |
| --- | --- | --- |
| F-1 | 19 routes resolved the tenant as `user.get("institution_id") or "inst_kmit"`, so any account without an attached institution read **and wrote** another college's roster, MOUs and reports. | Centralised in `_scope_institution()`; non-admins pinned to their own tenant, refused when none. |
| F-2 | A correctly signed JWT authenticated even after its session row was deleted → logout and password reset never revoked bearer tokens. | `get_session_user` requires a live session row. |
| F-3 | Password reset stored a raw UUID token, answered 404 for unknown emails, accepted any password length, and left old sessions alive. | Digest-stored, single-use, min length, sessions purged; enumeration removed from login/register/forgot. |
| F-4 | Google OAuth state was only checked **if** the `oauth_state` cookie existed → CSRF exposure when the cookie was blocked. | Fail-closed with constant-time comparison. |
| F-5 | Every invited user got the same published `DEFAULT_DEMO_PASSWORD`, emailed in plaintext and returned in the API response. | Password-less invitations activated on first Google sign-in; no secret in the response. |
| F-6 | `_public_origin()` trusted the `Host`/`X-Forwarded-Host` header when building password-reset links → reset-link hijacking. | Derived from `PUBLIC_BASE_URL` or the allowlisted origins only. |
| F-7 | Startup created **no indexes at all** on the MongoDB path (they lived only in the in-memory branch): no unique email index, no reset-token TTL. | `_ensure_indexes()` + expired-session purge run on connect. |
| F-8 | Seven demo accounts, including a super_admin with a password published in the repo's own docs, were auto-seeded into any environment. | Admin bootstraps from env; demo accounts are opt-in (`SEED_DEMO_USERS`, default false). Tracked credential docs deleted. |
| F-9 | Legacy Emergent `/api/auth/session` trusted a third-party endpoint's email and could mint a super_admin. | Disabled by default (410) behind `EMERGENT_AUTH_ENABLED`. |

### Critical — found only by running against a real MongoDB (fixed)

| ID | Finding | Fix |
| --- | --- | --- |
| F-10 | The MongoDB startup path seeded only six hand-picked collections. Jobs, the DSA catalog (474 questions / 340,931 progress rows *at that time; since replaced by the 108-problem original curriculum*), placements, training and announcements were empty on a real database, silently breaking the jobs board and 30% of the readiness score. The in-memory demo looked complete, which is why no earlier test caught it. | Both paths seed the full payload; aptitude progress, resume versions and health scores are backfilled on Mongo too. Verified by count on a fresh database. |
| F-11 | Institution-wide PDF/CSV exports and cohort rosters accepted any authenticated user, so a student could download the whole roster. | Staff-only via `require_roles`. |
| F-12 | Pending (unapproved) accounts could reach data routes that only depended on `get_session_user`. | Central approval gate: pending accounts get 403 on data routes, but can still read `/auth/me` and submit `/signup`. |
| F-13 | No rate limiting on login, reset, registration or invitations; an in-process counter would not work across serverless instances. | Fixed-window limiter backed by the shared datastore (Mongo or the memory store), applied to the abuse-prone entry points. |

### Reliability — found while verifying the production path (fixed)

| ID | Finding | Fix |
| --- | --- | --- |
| F-14 | `seed_payload()` rebuilds ~340k demo rows **on every startup**, even when the database is already populated, so a cold start spent minutes generating data it then discarded. | Startup probes a few collections first; the payload is only generated when the deployment is genuinely empty. Cold start against a populated Mongo dropped to ~35 s. |
| F-15 | An interrupted frontend build leaves `frontend/build/` in place but empty, and the unguarded `StaticFiles` mount then raised **at import time**, taking the entire API down. | Mount only when `build/static` exists; the SPA fallback already returns a clear 404 when `index.html` is missing. |
| F-16 | The in-memory fallback is pathologically slow for analytics: `/api/placements/overview` computes readiness for up to 1,000 students and each per-student query scans ~340k rows in pure Python, blocking the event loop long enough to time out other requests. | Not "fixed" — the fallback is demo-only by design and production now refuses to start without Mongo. Documented as a hard operational constraint. |

### Data integrity (fixed in the release-candidate pass)

| ID | Finding | Fix |
| --- | --- | --- |
| F-17 | Partial reseeding regenerated `students` with new random IDs while the collection already existed. Dependent rows (`dsa_progress`, `dsa_question_progress`, applications, …) were then inserted against IDs that do not exist. A curriculum migration exposed it as 1,230 phantom students, a demo account with no DSA progress, and a leaderboard of missing names. | Startup and the admin reseed now insert student-derived collections only into a genuinely fresh database; `scripts/rebuild_dsa_progress.py` rebuilds from live students and deletes orphan rows. Verified: 0 orphans, demo student 27 attempted / 9 solved. |
| F-18 | The Jooble integration fabricated six job listings from named companies whenever the key was missing or the provider failed, flagged only by a `warning` field the UI ignored. | Missing key and provider errors now return an empty list with an explicit warning; no invented postings. |
| F-19 | The DSA catalogue reproduced a third-party sheet's structure and titles, whose terms prohibit commercial use without consent. | Replaced with an original 12-topic / 108-problem pattern curriculum (original prompts, rationale and ordering). Rights blocker BL-26 closed. |

### High — fixed

- MOU upload/download open to students and faculty; no file-type, size or filename validation; `Content-Disposition` replayed client-controlled names/types.
- Students could enumerate the whole cohort roster and open any peer's full record (applications, resumes, interview reports).
- `resume_versions` download checked ownership only for students.
- Regex injection / ReDoS through `q` on roster and global search; unbounded `limit`.
- `/api/health/deep` published tenant counts anonymously.
- Design system: `ink`/`bone` had no `DEFAULT`, so ~375 class usages — including the shared primary button's background and every modal scrim — resolved to nothing.
- AnalyticsWorkbench displayed a hardcoded comparison table and cited a non-existent "National Placement Census · 2026".
- Landing page asserted Google/Amazon/Microsoft/Adobe/Deloitte as customers and showed fabricated five-star reviews.
- Certificates were never persisted, so their printed verification code pointed at a third-party domain and a route that did not exist.
- Login had exactly one path (Google); with no OAuth credentials a fresh clone cannot sign in at all.

### Still open (see `PACIO_BACKLOG.md`)

Unverified production environment variables; the Jooble key and demo password remain in
public git history; no rate limiting anywhere; bearer token in `localStorage`; single
monolithic FastAPI function on Vercel with a 4.5 MB payload ceiling; no CI; no e2e tests;
`MemoryDB` data-loss default; brand collision with `careeros.com`; takeUforward DSA
licensing; 884 kB gzipped JS bundle.

---

## 4. Conflicts between documentation and code

| Document claim | Reality |
| --- | --- |
| `memory/PRD.md`: 6 institutions, 470 students, ~70 jobs, ~880 applications | Startup log: **56 institutions, 5,450 students, 1,565 jobs, 979 applications** |
| `memory/PRD.md`: "password login + Emergent Google OAuth" | Login UI is Google-only; password login exists in the API only (now surfaced as an explicit, capability-gated option) |
| `FEATURE_GUIDE_FOR_JUDGES.md`: Anomaly Detective and What-If Simulator as shipping features | Both components existed but were **never mounted**; now wired into the workspace overview |
| `PACIO_MERGED_AUDIT_AND_ROADMAP.md` (June): "submission repo is `Manju10092006/Pacio`" | Superseded; origin is now `Nikhil03-hub/pacio-intelligence` |
| `pacio-audit-findings.md` (Sept): CORS wildcard, `/api/test/reset-pending`, doubled `/api/api/` calls, hardcoded secret fallbacks | All four were fixed by commits `b170ab0`, `a69348c`, `6aa0f44` after that audit was written |
| `RUN_ON_WINDOWS.md` / `auth_testing.md`: demo password in plain text | Sanitised to env-var references; `auth_testing.md` removed |

---

## 5. What was preserved deliberately

The winning product concept was not diluted. Kept intact: the six role workspaces and
their routing; the composite readiness model; the editorial ink/bone/accent visual system
(now actually rendering); the intelligence layer (executive summary, voice narration,
6-factor health, high-risk list, copilot, anomaly detection, what-if); the MOU/FDP/revenue/
comm-log partner workflows; and the in-memory fallback that makes the app runnable with
zero external dependencies for demos.

No feature was added that the brief or the evidence did not justify.
