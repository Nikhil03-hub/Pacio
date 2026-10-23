# Release-Candidate Acceptance Checklist

Scope: what has actually been exercised on this checkpoint (HEAD `39f7137`, 2026-10-23),
not what the product intends to support. Status vocabulary is strict: **VERIFIED** (the
exact flow ran and the result was observed), **PARTIAL** (the API/behaviour is tested but
the full browser flow was not), **BLOCKED** (needs credentials/access this environment does
not have), **NOT RUN**.

Browser automation can navigate and screenshot public pages in this environment, but
scripted credential entry and clicking through authenticated flows were blocked by the
execution harness. Authenticated behaviour below is therefore evidenced by the automated
API suites, not by a recorded UI session.

| Area | Check | Status | Evidence |
| --- | --- | --- | --- |
| Login | Page renders on desktop and at 390 px; no artifacts; no demo credentials shown | **VERIFIED** | screenshots `login_final.png` (desktop), `mobile_login.png` (390×844); built bundle clean |
| Login | Email sign-in form appears only when `/api/auth/config` reports it enabled | **VERIFIED** | live `/api/auth/config` → `password_enabled: true`, `google_enabled: false`; rendered button present |
| Login | Google OAuth round trip | **BLOCKED** | no Google client credentials in this environment |
| Login | Pending account can read its identity but is blocked from data routes | **VERIFIED** | tenant suite: `/auth/me` 200, `/students` `/dsa/intelligence` `/mou` `/reports/students.csv` → 403 |
| Session | Logout/password reset revokes existing bearer tokens | **VERIFIED** | hardening + live check (reuse after logout → 401) |
| Registration | Institution self-registration persists and does not confirm duplicate emails | **PARTIAL** | hardening tests (API); browser form not submitted |
| Admin | Approve/reject pending users, assign role/institution | **PARTIAL** | legacy approval tests; no recorded UI session |
| Tenancy | Cross-tenant read/write boundaries (rosters, students, resumes, MOUs, payouts, analytics, exports, comm logs) | **VERIFIED** | 20-test Tenant A vs Tenant B matrix |
| Dashboards | Role payloads load with real scoped data | **PARTIAL** | API calls for TPO/student/institution verified; authenticated UI not clicked |
| DSA | Catalogue 12 topics / 108 problems; progress and leaderboard resolve to real students; 0 orphan rows | **VERIFIED** | API + Mongo counts; rebuild report |
| DSA | Student UI interactions (solve, filters, code editor) | **PARTIAL** | API/seed verified; UI session not recorded |
| Jobs | Missing `JOOBLE_API_KEY` shows no fabricated listings | **VERIFIED** | live `/api/jobs/discover` → empty + warning |
| Jobs | Live provider results | **BLOCKED** | no Jooble key (exposed key must be rotated first) |
| MOU | Staff-only access; upload validation; download scoping | **VERIFIED** | hardening tests (415/400/403, sanitised name) |
| Resume | Built-resume download is owner-only | **VERIFIED** | hardening test (cross-user → 404) |
| Resume | Full browser upload → build → download | **PARTIAL** | API-level owner checks only |
| Certificates | Issue, public verification page, idempotency, cross-tenant rejection | **VERIFIED** | API tests + `/verify/ST-CRT-RC2026` screenshot |
| Reports | PDF/CSV exports gated to staff; manifest/board packet | **PARTIAL** | gating tests pass; report content not re-inspected in this pass |
| Limits | Login/reset/invite/certificate throttling | **VERIFIED** | 429 + `Retry-After`; counters in Mongo |
| Persistence | Data survives API restart; no duplicate seeding | **VERIFIED** | identical counts before/after restart |
| Recovery | Backup → restore into a separate DB → API runs on it | **VERIFIED** | 41 collections / 597,821 docs; counts matched; disposable DB dropped |
| Fail-closed | Production without `MONGO_URL` refuses to start | **VERIFIED** | exit code 3 + RuntimeError |
| Mobile | Login at 390 px | **VERIFIED** | screenshot |
| Mobile | Authenticated dashboards at mobile widths | **NOT RUN** | requires an authenticated browser session |
| Accessibility | Keyboard/focus/contrast audit of authenticated pages | **NOT RUN** | prior code audit only; not part of this gate |
| External delivery | Real email/Telegram messages | **BLOCKED** | no provider keys; everything is logged as `simulated` |

## What must be true before a preview deployment

1. Vercel environment variables set per `docs/STAGING_ENV.md`, with `MONGO_URL` pointing at
   a **dedicated staging database**.
2. Exposed credentials rotated (Jooble, demo password) — `docs/CREDENTIAL_REMEDIATION.md`.
3. Preview URL added to `ALLOWED_ORIGINS`; `PUBLIC_BASE_URL` set to that origin.
4. Google OAuth redirect URI registered for the preview domain.
5. Re-run this checklist against the deployed URL, including one authenticated browser
   session per role and one real email/Telegram delivery if keys are configured.
