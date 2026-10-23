# Staging and Production Environment Contract

Names only — never paste secret values into chat, prompts, documents or Git. Set them in
the provider dashboard or a local git-ignored file.

## Build time (frontend)

| Variable | Required | Notes |
| --- | --- | --- |
| `REACT_APP_BACKEND_URL` | **No — leave unset for deployments** | Setting it bakes an absolute API URL into the bundle. Production and preview must build with it empty so the SPA calls the same origin that serves it. Only local development uses it (e.g. `http://127.0.0.1:8000`). |

No other frontend variables are required. The verification gate greps the built bundle for
`localhost`/`127.0.0.1` and fails if one is present.

## Backend runtime

`REQUIRED` = the app cannot serve correctly without it. `OPTIONAL` = degraded/simulated
behaviour without it, documented in `INTEGRATIONS.md`.

| Variable | Staging | Production | Behaviour if missing |
| --- | --- | --- | --- |
| `JWT_SECRET` | **REQUIRED** | **REQUIRED** | Startup raises `RuntimeError`; no unsigned sessions. |
| `MONGO_URL` | **REQUIRED** | **REQUIRED** | In production (`APP_ENV=production` or any Vercel deployment) startup **refuses to boot**. Locally it falls back to in-memory storage, which loses all data on restart. |
| `DB_NAME` | REQUIRED (explicit) | REQUIRED (explicit) | Defaults to `careeros`. Keep the existing production name; a different value points at a different database. |
| `APP_ENV` | `staging` | `production` | Defaults to `production` on Vercel, otherwise `development`. Controls the fail-closed guard. |
| `ALLOWED_ORIGINS` | REQUIRED | REQUIRED | Comma-separated exact origins allowed to make credentialed calls. Defaults to `https://pacio-two.vercel.app`; set the real preview/production domains. |
| `PUBLIC_BASE_URL` | REQUIRED | REQUIRED | Canonical origin used in password-reset and invitation links. Never derived from a request Host header. |
| `ADMIN_EMAIL` + `ADMIN_PASSWORD` | Recommended | Recommended | Bootstraps the super-admin account. Without them, access must come from an existing account or Google + prior approval. |
| `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` | REQUIRED for Google sign-in | REQUIRED for Google sign-in | `/api/auth/config` reports `google_enabled: false`, and the login screen hides the Google button; email sign-in remains available if enabled. |
| `GOOGLE_REDIRECT_URI` | Recommended | Recommended | Must match the Google console exactly (e.g. `https://<domain>/api/auth/google/callback`). |
| `PASSWORD_AUTH_ENABLED` | `true` (staff fallback) | owner decision | Defaults to true. Disable only when every user can sign in with Google. |
| `RATE_LIMIT_ENABLED` | `true` | `true` | Fixed-window limiter in the shared datastore. |
| `SEED_DEMO_DATA` | `true` for demo staging | **`false`** | When true, an empty database is seeded with synthetic institutions/students/jobs. Never present this as real data. |
| `SEED_DEMO_USERS` | `false` | **unset/false** | Creates the six KMIT demo logins. Must stay off anywhere real institution data exists. |
| `DEFAULT_DEMO_PASSWORD` | only if demo users are on | **unset** | Shared demo password; rotate it if it was ever used. |
| `DEFAULT_INSTITUTION_ID` | optional | optional | Tenant used when a super-admin browses without naming one. Defaults to `inst_kmit`. |
| `EMERGENT_AUTH_ENABLED` | `false` | `false` | Legacy third-party login; disabled by default. |
| `SENDGRID_API_KEY` + `SENDER_EMAIL` | optional | for real email | Without them, email is logged as `simulated`; nothing is sent. |
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | optional | for real alerts | Without them, Telegram is `simulated`. |
| `JOOBLE_API_KEY` | optional | optional | Without it, `/api/jobs/discover` returns an honest empty list (no fabricated jobs). Use a rotated key if the old one was exposed. |
| `EMERGENT_LLM_KEY` | optional | optional | AI feedback falls back to deterministic templates. |
| `MAX_UPLOAD_BYTES` | optional | optional | Defaults to 10 MB. Vercel’s request limit is 4.5 MB, so keep well below it there. |
| `ALLOWED_UPLOAD_EXTENSIONS` | optional | optional | Defaults to pdf/doc/docx/png/jpg/jpeg. |

## Staging database rules

1. Use a **dedicated staging database**, not the local `pacio_dev_verify` and not the
   production database.
2. Create a least-privilege Atlas user (`readWrite` on that database only).
3. Restrict network access to the deployment provider’s egress where possible.
4. Take a backup before the first import and record its location outside Git.
5. Run `scripts/mongo_backup_restore.py verify` after any restore.

## Cautions

- Changing Vercel environment variables affects **new deployments**, not existing ones.
- Rotating `JWT_SECRET` invalidates all sessions.
- `SEED_DEMO_USERS=false` does not delete accounts that already exist; remove them in Atlas.
- Do not point production at the synthetic development database and treat it as genuine.
