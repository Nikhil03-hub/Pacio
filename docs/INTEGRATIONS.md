# Integrations

Credential **variable names only**. No secret value appears in this repository. Anything
that was ever hardcoded is treated as compromised and needs rotation at the provider.

| Service | Purpose | Variables | Failure behaviour | Verified in this audit |
| --- | --- | --- | --- | --- |
| MongoDB Atlas | Primary datastore via Motor | `MONGO_URL`, `DB_NAME` | If unset, the app starts on the in-memory fallback and **loses all data on cold start**. If set but unreachable, startup raises after a 10 s server-selection timeout. | Local run used the fallback (no Atlas credentials here). Atlas path verified by code reading only. |
| Google Identity | Sign-in | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` | `/api/auth/google/start` returns 503 when unconfigured. `/api/auth/config` now reports `google_enabled` so the login screen can hide the button instead of offering a dead end. | Config endpoint tested; real OAuth round-trip not possible without credentials. |
| Emergent platform auth | Legacy demo login | `EMERGENT_AUTH_URL`, `EMERGENT_AUTH_ENABLED` | Endpoint returns **410 Gone** unless explicitly enabled, because it trusted a third party's email claim and could mint a super_admin. | Disabled path tested (410). |
| SendGrid | Transactional email | `SENDGRID_API_KEY`, `SENDER_EMAIL` | Without a key the send is skipped and `notification_log` records `status: "simulated"` with the reason. No exception reaches the user. | Simulated path exercised. **Live delivery unverified** (BL-12). |
| Telegram Bot API | Second mandatory channel | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Missing either one logs `simulated`. Rate limits are about 1 message/sec per chat and 20/min per group. | Simulated path only. |
| Jooble | Live job listings | `JOOBLE_API_KEY` | Previously had a hardcoded fallback in source; now read from the environment only, so the feature degrades instead of using a leaked key. | Not exercised. **Key must be rotated** - it sits in public git history (BL-09). |
| Emergent LLM / Claude | Optional AI text | `EMERGENT_LLM_KEY` | `ai_service.py` falls back to deterministic, template-based scoring and feedback, so every AI surface still works with no key. | Fallback path exercised locally; live LLM not called. |
| api.qrserver.com | Certificate QR rendering | none | If unreachable, the renderer draws a decorative placeholder QR that scans to nothing - a silent failure on a printed document. | Not exercised. Replace with a local encoder (DS-10). |
| LiveAvatar | Mock interview video | embed URL in `RoleLayout.jsx` | Third-party iframe inside the authenticated shell; no fallback if the vendor is down. | Not exercised. |
| Google Fonts / Fontshare | Typography | none (CDN links in `index.html`) | Fonts fail to load and the SPA falls back to system fonts; no functional impact. | Confirmed present in the served HTML. |

## Scheduled and background work

There is **no scheduler in the repository**. These are request-driven endpoints that an
external cron must call:

| Endpoint | Should run | Why |
| --- | --- | --- |
| `POST /api/notifications/generate-alerts` | daily | MOU expiry, high-risk students, payout and workshop alerts (Track 5B must-have 13) |
| `POST /api/digest/send` | weekly/monthly | TPO digest email (good-to-have 6) |
| `POST /api/admin/recompute-health` | after bulk data changes | College health scores |

Vercel Cron can call the first two; note that a cron request still executes inside the
single serverless function and its duration limit (BL-11, BL-17).

## Webhook and callback inventory

- `GET /api/auth/google/callback` - browser redirect, requires `state` match and
  `email_verified`, and validates `aud` against the client id.
- `GET /api/auth/session` - legacy POST from the Emergent flow (disabled by default).
- No inbound payment webhooks exist; revenue-share payouts are an internal approval
  workflow, not a money movement integration.

## Data sent to third parties

Currently: student and institution names in notification emails and Telegram messages;
certificate ids to the QR rendering service; resume text to the optional LLM. Nothing
should be sent to an external model provider until a data-processing position with the
institution exists (see `SECURITY_AND_PRIVACY.md`).
