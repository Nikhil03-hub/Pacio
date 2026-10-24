# Browser Smoke Report

Phase 3, release-confidence evidence. Run 2026-10-24 against the **production build** served by the
local API at `http://127.0.0.1:8073` (FastAPI mounting `frontend/build`), Playwright driving Chromium.

## Journeys exercised (anonymous only)

| Route | Result | Evidence |
|---|---|---|
| `/login` | **PASS** — page renders, "Sign in with email" reveals a form with Email and Password fields | DOM assertions: `hasEmail: true`, `hasPassword: true`, labels `["Email","Password"]` |
| `/verify/ST-CRT-RC2026` | **PASS** — public certificate verification returns a valid record: certificate id, holder, program, department, institution, issue date, "CHECKED 24/10/2026" | rendered text captured |
| `/` (landing) | **PASS** — renders; demo content is labelled "ILLUSTRATIVE · NOT A CUSTOMER REVIEW" and "What the demonstration dataset contains"; 0 `<img>` elements, so no fake customer logos | rendered text captured |

Console on every route: 2 errors, both expected `401 Unauthorized` from `/api/auth/me` and
`/api/auth/refresh` for an anonymous visitor. No JavaScript exceptions, no failed static assets.

## Regression found by this smoke, and fixed

The first build of this session ran `CI=false npm run build` **without** overriding
`REACT_APP_BACKEND_URL`. CRA then baked the gitignored `frontend/.env.local` value
(`http://localhost:8000`) into the bundle, so the served login page issued
`net::ERR_CONNECTION_REFUSED` to `localhost:8000`.

Two fixes, both shipped:

1. **Build step** — rebuild with `REACT_APP_BACKEND_URL=` (empty), as
   `scripts/release_gate.sh` and the new CI job already specify. Verified: **0** occurrences of
   `localhost:8000` in `build/static/js/main.*.js`.
2. **Runtime guard** in `frontend/src/lib/api.js` — if the baked base URL is a loopback address and
   the page is *not* served from loopback, the client falls back to same-origin. A developer who
   builds locally and uploads the folder to Vercel therefore still gets a working app instead of a
   dead one. The CI job additionally fails the build if `localhost`/`127.0.0.1` appears in the
   bundle, so the guard and the check are independent.

Re-run after the fix: same three journeys pass, and the API calls now go to the serving origin.

## Not run, and why

| Journey | Status | Reason |
|---|---|---|
| Student DSA list, problem page, submit + static-review panel | **BLOCKED** | Requires a demo login. The demo password lives in `backend/.env`; typing it into a browser-automation tool call would expose it in logs, which the mandate forbids. Verify manually in a browser, or add a dedicated read-only demo account for automation. |
| TPO / faculty / institution / recruiter dashboards | **BLOCKED** | Same credential constraint. |
| Mobile layouts, keyboard-only navigation, contrast | **NOT RUN** | No automated a11y tooling wired in this repo yet; the axe/Playwright a11y job is proposed in the CI backlog, not implemented. |
| Certificate issue flow (staff) | **NOT RUN** | Requires staff login. |

The authenticated half of Workstream E's UI checklist therefore remains **PARTIAL**: the code and
the honest copy are in place and build cleanly, but the rendering has not been verified behind a
login in this pass.

## How to reproduce

```
RATE_LIMIT_ENABLED=false .venv/Scripts/python.exe -m uvicorn server:app --app-dir backend --host 127.0.0.1 --port 8073
cd frontend && REACT_APP_BACKEND_URL= CI=false npm run build
# then Playwright: goto /login → click "Sign in with email" → assert Email + Password inputs
#                  goto /verify/ST-CRT-RC2026 → assert "Certificate is valid"
#                  goto / → assert "ILLUSTRATIVE" label present
```
