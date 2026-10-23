# Pacio — Prioritised Backlog

Companion to `PACIO_AUDIT.md`. Items marked **DONE** were implemented and verified in this
work; everything else is open with acceptance criteria so whoever picks it up can prove it.

Severity: `P0` data loss / security / legal · `P1` core workflow · `P2` production
readiness · `P3` evidence-backed product improvement · `P4` polish.

| ID | Sev | Finding and evidence | Affected paths | Status | Acceptance criteria / next action |
| --- | --- | --- | --- | --- | --- |
| BL-01 | P0 | 19 routes fell back to `inst_kmit` when the caller had no institution | `backend/server.py` | **DONE** | `_scope_institution()`; regression `test_account_without_an_institution_cannot_see_a_default_tenant` |
| BL-02 | P0 | Bearer tokens survived logout and password reset | `backend/auth.py` | **DONE** | `test_password_reset_rejects_weak_password_and_revokes_sessions` |
| BL-03 | P0 | Reset-link generation trusted the Host header | `backend/server.py` | **DONE** | `PUBLIC_BASE_URL` / allowlist only |
| BL-04 | P0 | OAuth state check was fail-open | `backend/server.py` | **DONE** | `test_google_callback_cannot_be_completed_without_state` |
| BL-05 | P0 | Invitations issued a shared published password | `backend/server.py`, `docs/DEMO_ACCESS.md` | **DONE** | no `temp_password` in API or email |
| BL-06 | P0 | Production MongoDB got no indexes (unique email, jti, token TTL) | `backend/server.py` | **DONE** | `test_startup_creates_indexes_on_the_real_database` |
| BL-07 | P0 | Demo accounts auto-seeded everywhere, incl. super_admin | `backend/server.py` | **DONE** | `SEED_DEMO_USERS` opt-in; admin from env |
| BL-08 | P0 | `memory/test_credentials.md` published the demo password in a public repo | repo root, `memory/` | **DONE (forward-only)** | Files removed and sanitised. **Still requires:** rotate the exposed password, delete surviving demo rows in Atlas, and decide whether to purge git history (`git filter-repo`) or make the repository private. Both are owner decisions with external visibility. |
| BL-09 | P0 | A Jooble API key was hardcoded in an earlier commit and is therefore in public history | git history | **OPEN** | Rotate the key at the provider. Confirm rotation before any sale or handover; do not reprint the value anywhere. |
| BL-10 | P0 | Without `MONGO_URL` the app runs on `MemoryDB` and loses all data on every cold start | `backend/memory_db.py`, `backend/server.py` | **OPEN (mitigated)** | Startup logs the mode and `/api/health/deep` reports it. **Needed:** refuse to start in a production profile when `MONGO_URL` is unset, plus a documented Atlas backup/restore drill. |
| BL-11 | P1 | MOU expiry alerts are on-demand only; no scheduler exists | `/api/notifications/generate-alerts` | **OPEN** | Wire a Vercel cron (or external scheduler) to call the endpoint daily; assert a notification row is created for an MOU expiring in <30 days. |
| BL-12 | P1 | Live email/Telegram delivery is unverified (hackathon rule 14) | `backend/notification_service.py` | **OPEN** | With real `SENDGRID_API_KEY` + verified sender and a Telegram bot token, send one message per channel and record the provider message id. Until then, treat rule 14 as **simulated**, which the brief scores lower. |
| BL-13 | P1 | No rate limiting on login, password reset, invites, uploads or AI endpoints | `backend/server.py` | **OPEN** | Add per-IP + per-account throttling at the edge or in middleware. Note that in-process counters do not work across serverless instances; prefer platform-level limits. |
| BL-14 | P1 | Bearer token and user object are kept in `localStorage` (XSS-theft surface) | `frontend/src/lib/api.js`, `App.js` | **OPEN** | Move to the HttpOnly cookie only; remove the token from storage and the request interceptor. Needs a re-test of the refresh queue. |
| BL-15 | P1 | Pending/unapproved accounts can reach routes that gate on `get_session_user` alone | `backend/auth.py` | **OPEN** | Decide policy: either enforce `approved` centrally (keeping `/auth/me` readable for the pending screen) or add an explicit `require_approved` dependency to every data route. |
| BL-16 | P1 | Three conflicting Python manifests (`backend/requirements.txt`, `api/requirements.txt`, `pyproject.toml`) and no lockfile | repo root | **OPEN** | Pick one source of truth, pin exact versions, commit a lockfile, and confirm which one Vercel installs. |
| BL-17 | P2 | Monolithic FastAPI app builds into **one** Vercel function: 300 s default duration, 4.5 MB request/response payload, WebSocket support in public beta, single region `iad1` | `vercel.json`, `api/index.py` | **OPEN** | Split upload/report/AI paths out of the monolith, or move to a container/VM host. Verify an MOU upload near 10 MB end to end. |
| BL-18 | P2 | No CI at all; the only automated checks are pytest suites | repo root | **OPEN** | Add a pipeline: `pytest backend/tests`, `npm run build`, and a secret scan. The legacy suites take ~8 min because they call external services — mark or isolate those. |
| BL-19 | P2 | No browser-level tests; UI regressions are invisible | `frontend/` | **OPEN** | Add Playwright journeys for: sign-in → workspace → roster add → report download → certificate verify. |
| BL-20 | P2 | JS bundle is 884 kB gzipped on first load | `frontend/` | **OPEN** | Route-level `React.lazy` for the six role trees, Monaco and Recharts; target < 400 kB initial. |
| BL-21 | P2 | `AnomalyDetective` and `WhatIfSimulator` each re-fetch `/api/placements/overview` | `frontend/src/pages/Overview.jsx` | **OPEN** | Hoist to one fetch in the page and pass data down. |
| BL-22 | P2 | Accessibility debt: 167 `<button>` vs 4 `aria-label`; five hand-rolled modals with no `role="dialog"`, focus trap or Escape; 45 CSS-grid "tables" with no table semantics; placeholder-as-label in ~60 inputs | `frontend/src/**` | **PARTIAL** | Escape/focus and `aria-label` work started (calendar nav, login form, verify page). Continue with a shared Modal built on the existing Radix primitives. |
| BL-23 | P2 | `accent` (#ff3b00) on white is 3.57:1 and on `bone` 3.4:1; small accent labels and accent-filled buttons fail AA for normal text | `frontend/tailwind.config.js` | **OPEN — needs design sign-off** | Either darken the accent used for text/buttons or restrict accent to large text and graphics. Deliberately not changed unilaterally because it alters the brand. |
| BL-24 | P2 | Landing page still presents fictional "Placement intelligence playbooks" blog entries and a `Customers`/`Pricing` nav with no destination | `frontend/src/mock.js`, `components/landing/Nav.jsx` | **OPEN** | Remove or clearly mark as sample content; wire or drop dead nav links. |
| BL-25 | P3 | Brand collision: user-facing name is CareerOS while `careeros.com` is an operating product for universities, cohort boards and talent pools; `careeros.app` redirects there | frontend strings, `package.json`, `start-careeros.bat`, `JWT_ISSUER` | **OPEN — owner decision** | Choose a name, then rename via a single brand module and secure the domain. Changing `JWT_ISSUER` invalidates live sessions, so schedule it. |
| BL-26 | P3 | DSA curriculum mirrors takeUforward's A2Z structure; their terms prohibit commercial exploitation without written consent | `backend/dsa_catalog.py` | **OPEN — legal blocker** | Obtain written permission **or** replace with an independently defined curriculum before selling. Attribution strings were removed; that does not resolve the underlying right. |
| BL-27 | P3 | Seeded data names real colleges (KMIT, Vasavi, MREC, CBIT…) and invents MOUs, payouts and offers for them | `backend/seed_data.py` | **OPEN** | Before any external demo, either obtain a placement report source per institution or switch the seed to clearly fictional institutions. |
| BL-28 | P3 | KMIT year-by-year placement tuples cannot be traced to a published source; only aggregate figures are published | `backend/seed_data.py` | **OPEN** | Document provenance in `DATA_SOURCES.md` (done) and mark the granular rows as modelled, or replace with published aggregates. |
| BL-29 | P4 | `num-mono`/`tnum` overlap; `index.css` re-declares `font-display/serif/mono` that Tailwind already emits | `frontend/src/index.css` | **PARTIAL** | `num-mono` now defined; dedupe the font utilities and pick one numeric class convention. |
| BL-30 | P4 | Currency and date formatting are hand-rolled in 26 places with mixed `en-US`/`en-IN` locales | `frontend/src/lib/utils.js` | **OPEN** | Route all formatting through `lib/utils.js` with a single `en-IN` locale policy. |

## Suggested order of work

1. **BL-08, BL-09, BL-26** — credential rotation, history exposure and the DSA licence are
   the only items that can block a sale outright.
2. **BL-10, BL-17** — decide where real tenant data will live and whether Vercel's
   serverless shape can hold it.
3. **BL-11 → BL-15** — finish the operational core (scheduling, delivery proof, abuse
   limits, session storage, approval policy).
4. **BL-16, BL-18, BL-19** — reproducibility and CI, so future changes are cheap to trust.
5. **BL-20 → BL-24** — performance and accessibility.
6. **BL-25, BL-27, BL-28** — brand and data decisions that need the owner, not the engineer.
