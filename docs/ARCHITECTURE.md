# Architecture

Describes the system as it actually is on 2026-10-23, not as planned.

## Shape

```
Browser (React 18 SPA, CRA)
   |  same-origin /api  (axios client, HttpOnly cookie + optional Bearer)
   v
Vercel edge  ->  api/index.py  ->  backend/server.py  (FastAPI, 151 routes, ~7,200 lines)
   |                                      |
   | serves frontend/build                +--> Motor -> MongoDB Atlas  (or MemoryDB fallback)
   |                                      +--> GridFS "mou_files"       (or MemoryGridFS)
   +--> /ws/live WebSocket (in-process room manager, institution-scoped)
                                          +--> reports.py  (ReportLab PDF, CSV, ICS)
                                          +--> notification_service.py -> SendGrid + Telegram
                                          +--> ai_service.py -> optional LLM, deterministic fallback
                                          +--> intelligence_engine.py -> readiness scoring
```

Everything runs in one deployable unit. The SPA and the API share an origin in production,
which is why CORS is mostly a non-issue there but must still be an explicit allowlist for
local development and any preview URL.

## Backend layout

| File | Role | Size |
| --- | --- | --- |
| `backend/server.py` | App factory, models, all routes, startup seeding, SPA serving | ~7,300 lines |
| `backend/auth.py` | bcrypt, JWT issue/decode, `get_session_user`, `require_roles`, `require_same_institution` | 130 lines |
| `backend/memory_db.py` | Mongo-compatible in-memory store (`$or`, `$in`, `$gte`, `$regex`, aggregation) | 231 lines |
| `backend/seed_data.py` | Deterministic sample data generator | 1,278 lines |
| `backend/dsa_catalog.py` | In-house DSA curriculum: canonical problems, own taxonomy and prompts (12 topics, 108 problems) | 450 lines |
| `backend/intelligence_engine.py` | Readiness weights and per-student scoring | 345 lines |
| `backend/reports.py` | PDF/CSV/ICS generation | 270 lines |
| `backend/notification_service.py` | SendGrid + Telegram fan-out with always-on logging | 102 lines |
| `backend/ai_service.py` | Interview feedback and ATS scoring, optional LLM | 173 lines |
| `backend/ws_manager.py` | In-process WebSocket rooms | 57 lines |
| `api/index.py` | Vercel entrypoint; adds `backend/` to `sys.path` and re-exports `app` | 11 lines |

`server.py` is the main maintainability debt: route definitions, business logic and
seeding live in one file, and the same demo-user seeding was duplicated three times
(consolidated into `_demo_account_specs()` in this work). Splitting into routers is
backlog BL-16/BL-17 territory.

## Request path and authorization

1. `production_headers` middleware adds `X-Content-Type-Options`, `X-Frame-Options: DENY`,
   `Referrer-Policy`, `Permissions-Policy` and response timing.
2. Route dependencies decide access:
   - nothing -> public (health, auth start/callback, static SPA, certificate verify)
   - `get_session_user` -> any signed-in user
   - `require_roles(...)` -> role plus `approved` check
   - `require_same_institution()` / `_scope_institution()` -> tenant boundary
3. `_scope_institution(user, requested)` is now the single tenant resolver: non-admins are
   pinned to their own `institution_id` and refused when they have none; only super_admin
   may name a tenant, defaulting to `DEFAULT_INSTITUTION_ID`.

## Sessions

`create_access_token()` issues a JWT (`iss`, `sub`, `jti`, `role`, `institution_id`,
`approved`, `iat`, `exp`) and a matching `user_sessions` row stores the `jti` and expiry.
Resolution requires **both** a valid signature and a live session row, so logout, password
reset and admin deactivation actually take effect. Cookies are HttpOnly, `Secure` when the
request came over HTTPS (checked via `x-forwarded-proto`), and `SameSite=None` only in that
secure case.

## Data model (Mongo collections)

Core: `users`, `user_sessions`, `institutions`, `programs`, `cohorts`, `enrollments`,
`students`, `recruiters`, `jobs`, `applications`, `placements`, `placement_records`,
`year_summaries`, `mous`, `fdp_sessions`, `revenue_share`, `payouts`, `comm_log`,
`announcements`, `notifications`, `notification_log`, `audit_logs`, `certificates`.
Intelligence: `dsa_questions`, `dsa_question_progress`, `dsa_code_submissions`,
`dsa_progress`, `aptitude_questions`, `aptitude_question_progress`, `aptitude_test_sessions`,
`aptitude_test_attempts`, `aptitude_scores`, `ats_reports`, `resume_versions`,
`mock_interview_sessions`, `interview_reports`, `recruiter_shortlists`,
`recruiter_saved_filters`, `saved_jobs`, `password_reset_tokens`, `college_health_history`,
`chat_rooms`, `chat_messages`, `workshops`.

There are no foreign keys (document store); integrity is enforced in code plus the unique
indexes listed in `SETUP_AND_RECOVERY.md`.

## Frontend layout

- `App.js` - one router with six role trees (`/platform`, `/institution`, `/tpo`,
  `/faculty`, `/student`, `/recruiter`), `Protected` role gating, and an `AuthProvider`
  that caches the user and refreshes via `/auth/me`.
- `layouts/RoleLayout.jsx` + `roleConfig.js` - the single authenticated shell for all six
  roles, including the mobile drawer and the command palette.
- `pages/*` - 47 page components; `components/*` - shared widgets plus `landing/*` for the
  marketing page.
- `lib/api.js` - axios instance with a 401 refresh queue; `lib/utils.js` - formatting.

Design tokens live in `tailwind.config.js` (ink/bone/accent/rust/moss/ochre, four font
families) and `src/index.css` (`.editorial`, `.pill`, `.btn`, `.grain`, `.tnum`,
`.num-mono`). `design_guidelines.json` at the repo root is **stale** relative to the code
(colours, status tokens and container padding all differ) - treat the config and CSS as
authoritative.

## Known architectural risks

1. Single serverless function for all routes and payload limits (BL-17).
2. In-memory fallback silently becomes the database when `MONGO_URL` is missing (BL-10).
3. WebSocket state is per-instance, so realtime rooms do not scale horizontally.
4. No background worker: alert generation and digests are request-driven.
5. 884 kB gzipped initial JS with no route splitting (BL-20).
