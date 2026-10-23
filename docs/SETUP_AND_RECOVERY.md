# Setup, Operation and Recovery

Verified on 2026-10-23 on Windows 11 with the repository's own `.venv` (Python 3.12 per
`.python-version`) and Node 22.21 / npm 11.6.

## 1. Prerequisites

| Tool | Version used | Notes |
| --- | --- | --- |
| Python | 3.12 | `.venv` in the repo root is already provisioned; recreate with `python -m venv .venv` |
| Node | 22.x | CRA (`react-scripts 5`) works on 22; Node 24+ can hit OpenSSL hashing errors on older CRA |
| MongoDB | Atlas or local | Optional locally (in-memory fallback), mandatory for any real use |

## 2. Backend

```bash
cd Pacio-Merged
.venv/Scripts/python.exe -m pip install -r backend/requirements.txt   # see BL-16: manifests conflict
cp .env.example backend/.env                                           # backend/.env is git-ignored
.venv/Scripts/python.exe -m uvicorn server:app --app-dir backend --host 127.0.0.1 --port 8000
```

- `backend/.env` is loaded automatically (`load_dotenv(Path(__file__).parent / ".env")`).
- **`JWT_SECRET` is required** - startup raises `RuntimeError` without it rather than
  running an authentication layer that cannot sign sessions.
- Without `MONGO_URL` the app boots on the in-memory demo layer in about 80 seconds
  (seeding 56 institutions / 5,450 students / 22,140 DSA rows) and **forgets everything on
  restart**. That is a demo mode, not a database.
- Health: `GET /api/health` is public and minimal. `GET /api/health/deep` requires a
  super_admin session and reports which data layer is live.
- Sign-in on a fresh clone: set `SEED_DEMO_USERS=true` plus `DEFAULT_DEMO_PASSWORD` and
  `ADMIN_EMAIL`/`ADMIN_PASSWORD`, then use "Sign in with email" on `/login`. Google-only
  sign-in is unusable until OAuth credentials exist (BL-25 covers the brand rename).

## 3. Frontend

```bash
cd Pacio-Merged/frontend
npm install
npm start                                            # dev server on :3000, proxies via REACT_APP_BACKEND_URL
REACT_APP_BACKEND_URL= CI=false npm run build        # production build: same-origin /api
```

**Do not ship a build made while `frontend/.env.local` sets a localhost backend.** That
file is git-ignored but is baked into `build/` at compile time, so a locally built artifact
silently points every visitor's browser at `localhost:8000`. Production must build with
`REACT_APP_BACKEND_URL` empty so the SPA calls the same origin that serves it.

## 4. Tests

```bash
cd Pacio-Merged
.venv/Scripts/python.exe -m pip install pytest
.venv/Scripts/python.exe -m pytest backend/tests/test_hardening.py -q
```

| Suite | Command | Result on 2026-10-23 |
| --- | --- | --- |
| Hardening (new) | `pytest backend/tests/test_hardening.py` | **30 passed** in ~28 s; runs in-process with `TestClient`, no server needed |
| Legacy v2 + v21 | `REACT_APP_BACKEND_URL=http://127.0.0.1:8000 pytest backend/tests/test_careeros_v2.py backend/tests/test_careeros_v21.py` | **73 passed** in ~6 min; needs a running server and reaches external services, which is why it is slow |
| Frontend build | `cd frontend && CI=false npm run build` | **Compiled successfully**; 884 kB gzipped JS (BL-20) |

Total: **103 automated tests passing** on 2026-10-23.

There is no CI yet (BL-18) and no browser test (BL-19).

## 5. Database

- Driver: Motor; collections are declared in `CORE_COLLECTIONS` in `backend/server.py`.
- Name: `DB_NAME`, default `careeros`. **Deliberately unchanged** - the deployed Atlas
  database already uses it, and a new default would silently point every tenant at an empty
  database. Rename only with a migration.
- Indexes are created on connect by `_ensure_indexes()`: unique on `users.email`,
  `user_sessions.jwt_id`, `dsa_questions.question_id`, `aptitude_questions.question_id`,
  `password_reset_tokens.token_hash`, `saved_jobs(user_id, job_id)`, plus a TTL on
  `password_reset_tokens.expires_at`. Expired sessions are purged at startup.
- MOU and resume bytes live in GridFS bucket `mou_files`.
- Seed is additive: `seed_payload()` only inserts into collections that are empty, and
  `POST /api/admin/reseed-demo` (super_admin) re-runs it without deleting anything.

## 6. Backup and restore

Not yet automated (BL-10). Manual procedure that works today with Atlas:

1. **Backup:** Atlas -> Actions -> Backup -> Restore to a new cluster (or `mongodump`
   against the deployment's `MONGO_URL` with a restricted user).
2. **Restore drill:** restore into a throwaway cluster, point a staging deployment's
   `MONGO_URL` at it, then confirm `/api/health/deep` reports `database: "mongo"` with
   non-zero students, and that an existing user can still sign in.
3. **Uploads:** GridFS collections (`mou_files.files`, `mou_files.chunks`) are included in
   a normal dump; verify by downloading one MOU after restore.
4. Record the date and the person who performed it. An untested backup is not a backup.

## 7. Deployment

```jsonc
// vercel.json - build the CRA app, then route everything through the Python entrypoint
{ "buildCommand": "cd frontend && npm install --no-package-lock && CI=false npm run build",
  "rewrites": [{ "source": "/(.*)", "destination": "/api/index.py" }] }
```

Required Vercel environment variables: `JWT_SECRET`, `MONGO_URL`, `DB_NAME`,
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `PUBLIC_BASE_URL`,
`ALLOWED_ORIGINS`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, plus `SENDGRID_API_KEY`,
`SENDER_EMAIL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` for real notifications.
Leave `SEED_DEMO_USERS` unset in production.

**These values could not be inspected from this environment.** Confirm them in the Vercel
dashboard before trusting a production login flow: a missing `JWT_SECRET` now fails loudly
at startup instead of running with an unsigned session, and a missing `MONGO_URL` means
data loss on every cold start.

## 8. Known operational limits

- One Python function serves every route: 300 s default duration, 4.5 MB payload, 500 MB
  bundle, single region, WebSockets in beta (BL-17).
- Cold starts re-run seeding when the database is empty; the first request after idle can
  be slow.
- No error reporting, uptime monitoring or alerting is wired in.
