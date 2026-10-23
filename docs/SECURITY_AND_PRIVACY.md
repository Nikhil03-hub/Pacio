# Security and Privacy

Scope: authentication, sessions, tenancy isolation, uploads, data exposure and privacy
obligations. Findings describe the state **after** this work unless marked residual.

## Trust boundaries

1. Browser -> Vercel edge -> one FastAPI function that serves both the SPA and the API.
2. Identity: Google OAuth (preferred) or email + password. Both end in a signed JWT stored
   as an HttpOnly `session_token` cookie and mirrored in a `user_sessions` row.
3. Tenant: every data query is scoped by `institution_id`; faculty additionally by
   `department`; students to their own `student_id`.

## Threat model and current controls

| Threat | Control | Where | Verified |
| --- | --- | --- | --- |
| Credential stuffing | bcrypt; one generic 401 for unknown user and wrong password | `backend/auth.py`, `/api/auth/login` | yes (test) |
| Account enumeration | Login, forgot-password and public registration return identical shapes whether or not the account exists | `/api/auth/forgot-password`, `/api/auth/register` | yes (tests) |
| Session that will not die | A deleted session row now ends access; previously a valid signature alone authenticated | `get_session_user()` | yes (test) |
| Reset-token theft from a DB read | SHA-256 digest storage, single use, 1-hour expiry, TTL index | `/api/auth/forgot-password`, `_ensure_indexes()` | yes (test) |
| Reset-link hijacking via Host header | Origin from `PUBLIC_BASE_URL` or the CORS allowlist only | `_public_origin()` | yes (code) |
| Login CSRF through OAuth | `state` mandatory, constant-time compare, absent cookie now fails | `/api/auth/google/callback` | yes (test) |
| Third-party identity forgery | Legacy Emergent session endpoint returns 410 unless explicitly enabled | `/api/auth/session` | yes (test) |
| Cross-tenant read and write | `_scope_institution()` replaced 19 `or "inst_kmit"` fallbacks; non-admins cannot name another tenant | `backend/server.py` | yes (tests) |
| Peer privacy inside a tenant | Students see only their own roster row and record; MOU documents are staff-only | `/api/students`, `/api/students/{id}`, `/api/mou*` | yes (tests) |
| Uploaded-file abuse | Extension allowlist, 10 MB cap, empty-file rejection, path components stripped, sanitised stored name, MIME replayed only from an allowlist, `Content-Disposition: attachment` | `_validate_upload()`, `/api/mou/upload` | yes (tests) |
| Regex injection and ReDoS | Search terms escaped and length-capped; roster `limit` clamped to 1000 | `/api/students`, `/api/search` | yes (tests) |
| Anonymous infrastructure disclosure | `/api/health` is liveness-only; tenant counts moved behind super_admin | `/api/health`, `/api/health/deep` | yes (tests) |
| Unauthenticated data mutation | Old `/api/test/reset-pending` deleted; replaced by admin-only `POST /api/admin/reset-pending-approval` | `backend/server.py` | yes |
| Realtime eavesdropping | WebSocket authenticates the token and refuses rooms outside the caller's institution | `/ws/live` | yes (code) |
| Cross-origin credential abuse | Explicit `ALLOWED_ORIGINS` list with credentials | CORS middleware | yes (code) |
| Booting with no signing key | Startup raises `RuntimeError` when `JWT_SECRET` is unset | `_startup()` | yes |
| Duplicate identities | Unique index on `users.email` and `user_sessions.jwt_id` created on connect | `_ensure_indexes()` | yes (test) |

## Residual risks (unfixed, ranked)

1. **No rate limiting anywhere.** Login, password reset, invitations, uploads and AI
   endpoints are unlimited. In-process counters do not work across serverless instances,
   so this needs platform-level protection.
2. **Bearer token in `localStorage`.** The HttpOnly cookie is undermined because the client
   also sends an `Authorization` header read from storage, which any XSS or malicious
   extension can exfiltrate.
3. **`approved` is not enforced centrally.** Only `require_roles` checks it, so routes that
   depend on `get_session_user` alone can still serve unapproved accounts.
4. **Weak password policy** - minimum 8 characters, no composition or breach-list check, no
   forced change on first use, no MFA.
5. **No session rotation on privilege change** (role assigned at approval).
6. **Google ID tokens are validated through the `tokeninfo` endpoint** rather than by
   verifying the signature against Google's JWKS locally. `aud` and `email_verified` are
   checked, which limits but does not remove the third-party dependency.
7. **The in-memory fallback is a data-loss default.** Without `MONGO_URL` in production,
   accounts, sessions, MOU bytes and reset tokens disappear on every cold start.
8. **Exposed history.** The demo password and a Jooble key sit in public git history.
9. **Google's OAuth access token is still written to the session row**
   (`external_session_token`). Remove it unless a feature actually needs it.

## Audit and logging hygiene

`_audit_log` records actor, role, institution, resource, outcome and IP for login,
approval, invitations, uploads, payouts, health recomputes and certificate issuance.
Password hashes are excluded from every projection that returns a user. Reset tokens are
never logged. Audit reads are super-admin only.

## Privacy obligations to settle before selling to Indian institutions

- A written data-processing position per institution: purpose limitation, retention,
  export and deletion on request, breach notification, and a sub-processor list (Vercel,
  MongoDB Atlas, SendGrid, Telegram, any LLM provider).
- India's Digital Personal Data Protection Act, 2023 and its rules impose consent, notice,
  retention and erasure duties. **Requires legal review** - this document does not claim
  compliance.
- None of that exists in code today: there is no consent record, retention policy, export
  endpoint or soft delete. Removing a student or institution is a hard delete with no
  record of what was removed.
- The schema holds real personal data once institutions onboard: names, emails, phone
  numbers, CGPA and placement status - which can include students in pre-university
  streams, raising additional consent considerations.
