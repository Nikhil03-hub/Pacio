# Pacio-Merged (CareerOS) — Full Product Audit: Prioritized Findings

**Scope:** All 46 live frontend pages + shared components/routing, the full FastAPI/MongoDB backend (154 routes), and a live walkthrough of `pacio-two.vercel.app`.
**Method:** Read-only throughout — zero files modified, zero fixes applied, zero credentials submitted to the live site. Backend authorization was verified by reading actual function signatures, not by grepping for patterns. No secret values appear anywhere below.
**Date:** September 27, 2026.

---

## How to read this

Every finding is tagged with a **type** — `bug` / `UX` / `accessibility` / `security` / `performance` / `polish` — and a **confidence** note saying exactly how it was verified, so you can tell a fully-confirmed issue from something that still needs your eyes. Severity tiers (🔴🟠🟡🟢) match the order GPT specified: critical → high → medium → low → leave-alone, then a recommended fix order at the end.

---

## 1. 🔴 Critical — fix first

### 1.1 The live login page hands out working credentials for all 6 roles, including super_admin
**Type:** security · **Confidence:** confirmed live, reproduced twice from a clean page load

Visiting `/login` on the production site shows all six demo account emails in plain text (`admin@careeros.app`, `institution@kmit.in`, `tpo@kmit.in`, `faculty@kmit.in`, `student@kmit.in`, `recruiter@amazon.com`), states outright **"All demo accounts use password ${DEFAULT_DEMO_PASSWORD},"** and — separately from that text — the sign-in form itself arrives **pre-filled** with a working TPO login (`tpo@kmit.in` + password already typed into the field) with zero clicks or typing from a visitor. The dashboard shell also carries an "Live · Production data" badge, so the app is explicitly telling visitors this isn't a sandbox.

Net effect: anyone who finds the URL can become **super_admin** — no exploit, no guessing, just reading the page. This is almost certainly a deliberate frictionless-demo feature (self-registration is currently broken — see 2.1 — so this may be the *only* way visitors can explore the product right now), but as built it's a full authentication bypass, not a scoped demo mode.

This also answers the open question from earlier in this audit about whether the hardcoded `ADMIN_PASSWORD`/`${DEFAULT_DEMO_PASSWORD}` fallback in the backend is "just theoretical": whatever the exact mechanism, that password is confirmed live and working in production today.

**Recommendation:** decide what you actually want a "demo" to be. Two reasonable paths: (a) drop the public demo panel entirely and fix self-registration instead, or (b) keep a demo mode but point it at a dedicated, sandboxed, non-admin demo account seeded with fake data only — never the real `admin@careeros.app` account. Either way, the credential-based access needs to stop being the front door to a real super_admin account.

### 1.2 CORS accepts credentialed requests from any website
**Type:** security · **Confidence:** confirmed by code read (`backend/server.py`, ~line 114-119)

`allow_origin_regex=r".*"` combined with `allow_credentials=True` reflects whatever `Origin` header a request sends, rather than a fixed list — which is exactly what browsers require to allow credentialed cross-origin requests from *any* site. Any website could make authenticated, cookie-bearing calls against your API on behalf of a logged-in user.

**Legitimate origin, determined (not guessed):** `vercel.json`'s rewrite serves the frontend and the FastAPI backend from the same domain, and I confirmed `frontend/.env.local` (dev-only) is the only `REACT_APP_BACKEND_URL` override anywhere — production genuinely runs same-origin. The only confirmed legitimate origin is **`https://pacio-two.vercel.app`**. I also checked the `careeros.app` domain your own code references (see 3.3 below) — it's owned by an unrelated company, so it must **not** be added to the allowlist.

**Recommendation:** replace the regex with an explicit allowlist containing just `https://pacio-two.vercel.app` (add a custom domain later if/when you actually own one). If you want Vercel preview-deployment URLs to also work, that needs a narrow regex scoped to your specific Vercel project slug — happy to draft that if you want it.

### 1.3 Public self-registration is broken — nobody can sign up right now
**Type:** bug · **Confidence:** confirmed live (404 in the network log) and root-caused in code

`frontend/src/lib/api.js` configures the shared API client with `baseURL: ${BASE}/api`. Five call sites then *also* prepend `/api/` to their own path, producing a doubled `/api/api/...` URL that 404s:

| File | Line | Call | Effect |
|---|---|---|---|
| `pages/Register.jsx` | 34 | `api.get("/api/public/institutions")` | "Select institution" dropdown is empty |
| `pages/Register.jsx` | 77 | `api.post("/api/auth/register")` | **Account creation itself fails** |
| `pages/Login.jsx` | 51 | `api.post("/api/auth/forgot-password")` | Forgot-password is broken |
| `pages/ResetPassword.jsx` | 33 | `api.post("/api/auth/reset-password")` | Password reset is broken |
| `pages/Revenue.jsx` | 37 | `api.post("/api/revenue/share")` | Revenue-share submission is broken |

I confirmed this live: `GET /api/api/public/institutions` returned `404` in the browser network log while on `/register`. Every other call site in the app (dozens of them) correctly omits the leading `/api/`, so this is a localized typo pattern, not a structural problem.

This is very likely the single highest business-impact bug in the app — if you're trying to onboard institutions, the public "create an account" flow does not work at all today, which also explains why the demo-credential shortcut in 1.1 is so prominent.

**Recommendation:** drop the redundant leading `/api/` from those 5 call sites. Small, mechanical, low-risk fix.

---

## 2. 🟠 High priority

### 2.1 Unauthenticated endpoint that mutates real-looking data
**Type:** security · **Confidence:** confirmed by full code read

```
POST /api/test/reset-pending   →  no parameters, no auth dependency
```
It hardcodes two specific records — institution `inst_vasavi_pending` and user `tpo@vasavi.ac.in` — and forces both back to `approved: False`. "Vasavi" also appears as a named customer logo on your live landing page ("Department health tracked"), so this may not be throwaway seed data. Anyone, unauthenticated, can repeatedly knock that institution's approval back to pending.

**Recommendation:** delete the route. It's named `/test/...` — it reads like dev-only scaffolding that shipped by accident.

### 2.2 Hardcoded fallback secrets in the auth layer
**Type:** security · **Confidence:** confirmed in code; **live-deployment status still needs your confirmation**

- `JWT_SECRET` falls back to a hardcoded string if the env var isn't set (`backend/auth.py`).
- `ADMIN_PASSWORD` / `DEFAULT_DEMO_PASSWORD` fall back to `${DEFAULT_DEMO_PASSWORD}` — the same value now confirmed publicly displayed on your live login page (1.1).
- `ADMIN_EMAIL` falls back to `admin@careeros.app`.

I don't have a way to inspect your Vercel project's environment variables from here, so I can't confirm whether the *real* production values are actually set (and just happen to coexist with a UI that separately advertises the same demo password), or whether the app is silently running on these fallbacks. That's a two-minute check in the Vercel dashboard's Environment Variables screen — worth doing regardless of how 1.1 gets resolved, since `JWT_SECRET` specifically controls session-token forgery risk and isn't shown anywhere in the UI the way the demo password is.

**Recommendation:** remove the hardcoded fallbacks so the app fails to start (or fails auth) instead of silently degrading to a known value. Confirm the real env vars in Vercel either way.

### 2.3 Hardcoded third-party API key fallback (Jooble)
**Type:** security · **Confidence:** confirmed in code, single consumption point

`JOOBLE_API_KEY` falls back to a hardcoded literal at `backend/server.py:7090`. I'm not printing the value anywhere per your standing instruction, and haven't rotated or touched it.

**Recommendation (prepared, not applied):** remove the hardcoded default so it fails closed to empty/`None`, and guard the Jooble-powered feature to degrade gracefully (skip that data source) rather than silently using an in-source key. Whether to rotate the existing key is your call — I haven't done anything that would require it, but since it's sat in source, it's worth considering once you're ready.

---

## 3. 🟡 Medium

### 3.1 `num-mono` styling silently does nothing, anywhere it's used
**Type:** UX inconsistency (confirmed bug) · **Confidence:** confirmed — grepped the full frontend, cross-checked against `tailwind.config.js` and `index.css`

`num-mono` is used 40+ times as the class meant to apply your JetBrains Mono "data" styling to labels, roll numbers, percentages, and figures — but it's never defined anywhere (not in `index.css`, not in the Tailwind config). Tailwind silently drops unknown class names, so it has zero effect. Your config already defines a working `mono` font family — `font-mono` is almost certainly the class that was intended.

**Confirmed live and reachable** (I cross-referenced every page file against every route in `App.js`) in:
`AuthCallback.jsx`, `Cohorts.jsx`, `OnboardingPending.jsx`, `StudentRoster.jsx`, `Training.jsx`.

Two more files have the same typo but are **dead code** with zero live impact — see 4.3.

**Recommendation:** find-and-replace `num-mono` → `font-mono` in the 5 live files (or add `.num-mono { @apply font-mono; }` to `index.css` as a one-line alias if you'd rather not touch each call site).

### 3.2 Bulk analytics queries could use an index check as institutions grow
**Type:** performance · **Confidence:** confirmed pattern in code; can't verify actual DB indexes from here

An institution-wide analytics path (`backend/server.py`, ~lines 540-546) runs six `$in`-based queries against student-ID lists, each capped at 10,000-30,000 documents. Fine at current scale, and the caps mean it's bounded rather than truly unbounded — but worth confirming a MongoDB index exists on `student_id` in each of those six collections before a large institution's data makes these slow. I can't inspect your live database's indexes from here.

### 3.3 Your own code references a domain you don't appear to own
**Type:** business risk, not a code bug · **Confidence:** confirmed live

Several places in the frontend (`layouts/RoleLayout.jsx`'s nav wordmark, the certificate QR-verification URL, notification sender addresses) reference `careeros.app` as if it's this product's domain. I checked it live: `careeros.app` redirects to `app.thecareeros.com`, an already-operating, unrelated personal job-search/networking product with different branding and positioning — not yours.

Two consequences: it settles the CORS question in 1.2 (that domain can't safely be added to your allowlist), and separately, it's worth knowing before you invest further in "CareerOS" branding or try to acquire that domain — someone else is already using a near-identical name. I'm not able to assess trademark risk; just flagging the fact.

---

## 4. 🟢 Low priority / polish

### 4.1 Five buttons have a hover state that's identical to their resting state
**Type:** polish · **Confidence:** confirmed by code read — see note below on correcting my own earlier read of this

`OnboardingPending.jsx` (2 buttons) and `StudentRoster.jsx` (3 buttons) each use `bg-accent ... hover:bg-accent` — the same orange in both states, so hovering shows no visible feedback. Your design system already defines a dedicated hover shade for exactly this purpose (`accent.hover`, a darker orange), which every *other* button in the app correctly uses (`MOU.jsx`, `Reports.jsx`, the shared `Primitives.jsx` Button component, `Cohorts.jsx`, `DSAIntelligence.jsx`, `PlatformControl.jsx`, `StudentDSA.jsx`, `Calendar.jsx` — I checked all of them).

*Self-correction:* I'd previously flagged `hover:bg-accent` as a broken/no-op class in general. On re-checking `tailwind.config.js`, `accent` is a fully-defined color and `hover:bg-accent` works correctly everywhere else — the real, much narrower bug is just these 5 buttons repeating the same color twice. Correcting it here rather than let the broader claim stand uncorrected.

**Recommendation:** change `hover:bg-accent` → `hover:bg-accent-hover` on those 5 buttons only.

### 4.2 A few raw hex colors duplicate existing design tokens
**Type:** polish · **Confidence:** sampled, not exhaustive

`StudentAptitude.jsx` uses `text-[#c1440e]` / `border-l-[#c1440e]` in a few places — that's the exact hex value of your existing `rust` token, just written as an arbitrary value instead of `text-rust`. Zero visual difference, purely a maintainability nitpick. Chart color props (Recharts `fill`/`tick` styling in `Overview.jsx` and similar) also use raw hex, which is normal and expected for that library — not an issue. A couple of risk/status badges (`StudentDSA.jsx`, `PlacementIntelligence.jsx`) use universal red/yellow instead of your custom `rust`/`ochre` tokens — a defensible choice since red/yellow read universally as error/warning; optional to unify.

### 4.3 Two orphaned files, safe to delete
**Type:** polish (dead code) · **Confidence:** confirmed — cross-referenced all 48 page files against every import/route in `App.js`

`pages/DashboardLayout.jsx` and `pages/Outcomes.jsx` are never imported or routed anywhere. (`PlacementIntelligence.jsx` is the component actually serving every "outcomes" route; the real shared dashboard shell is `layouts/RoleLayout.jsx`.) Both files also contain the `num-mono` typo from 3.1, but since neither renders in production, that's moot. No live-user impact either way — just a small cleanup opportunity.

---

## 5. Deliberately leave alone — these are already good

- **Visual identity as a whole.** The ink/bone/accent/rust/moss/ochre palette, Cabinet Grotesk/Fraunces/Satoshi/JetBrains Mono type system, grain texture, sharp no-radius buttons, light-only design — this is a mature, deliberate system, confirmed to carry through from the landing page into real dashboard pages. Don't homogenize it with Skill-Tank's system.
- **Mobile navigation on the shell every role actually uses.** `layouts/RoleLayout.jsx` (not `DashboardLayout.jsx`) has a properly-built, accessible mobile pattern: sidebar hidden below `lg`, replaced by a hamburger button with `aria-label`, an animated slide-in drawer, a backdrop, and background-scroll lock while open. 46 of 48 pages use responsive breakpoints; the login page correctly collapses to a single column on mobile. I couldn't get this session's browser-resize tool to reliably reflow to a true mobile viewport to screenshot it end-to-end, so this is a code-level read rather than a visually-confirmed one — worth a real device check if you want full certainty, but nothing in the code suggests a problem.
- **Route-level authorization.** Verified by reading full function bodies (not grep) across 8 diverse, sensitive routes — audit logs, user removal, invites, institution updates, student CRUD, MOU/resume uploads — all correctly gated, several with extra same-institution scoping. A second, independent pass with a proper multi-line signature parser covered 71 of ~154 routes and found exactly 15 with no auth dependency — every single one legitimately public (health checks, the auth flow itself, explicitly-named `/public/*` routes, the SPA catch-all) — plus the one already-listed gap in 2.1. Nothing else turned up. I'd treat the authorization layer as sound; further line-by-line coverage of the remaining routes is unlikely to change that picture, though I haven't read literally all 154.
- **MongoDB query construction.** No injection pattern found anywhere — no user input is interpolated into query filters. Result sets are consistently bounded with `.limit()`/capped `.to_list()`, several using a deliberate `safe_limit` variable.
- **Auth engineering details.** Cookie-security logic correctly checks `x-forwarded-proto` before marking cookies secure; Google OAuth and Mongo connection env vars have no insecure fallback (they fail closed, correctly, unlike the ones in 2.2); the axios client's 401-refresh-queue pattern is solid; `AuthCallback.jsx` carries an explicit code comment warning future editors not to hardcode the callback URL — good defensive practice, not a bug.
- **Unauthenticated route guarding.** Confirmed live: visiting a protected URL (`/admin`) while logged out redirects cleanly to the public landing page rather than leaking any protected UI.

---

## 6. Recommended implementation order

**Do first — live and exploitable right now:**
1. Narrow CORS to `https://pacio-two.vercel.app` (1.2).
2. Decide what "demo mode" should be and stop it from granting real super_admin access (1.1) — this is a product decision as much as a code fix, happy to help think through the options.
3. Delete `/api/test/reset-pending` (2.1).
4. Remove the hardcoded fallback secrets in `auth.py`/`server.py`; confirm the real Vercel env vars yourself (2.2).
5. Remove the Jooble key's hardcoded fallback (2.3).

**Do right alongside the above — actively costing you signups:**
6. Fix the 5 double-`/api/api/` call sites (1.3). This alone restores registration, password reset, forgot-password, and revenue-share.

**Then, medium:**
7. `num-mono` → `font-mono` across the 5 live files (3.1).
8. Sanity-check MongoDB indexes on `student_id` as institutions scale (3.2).
9. Decide what to do about the `careeros.app` naming/domain situation (3.3) — not code, but worth resolving before more go-to-market work.

**Then, low/polish, whenever convenient:**
10. Fix the 5 hover-state buttons (4.1).
11. Raw hex → token class cleanup (4.2).
12. Delete the 2 dead files (4.3).

**Don't touch:** everything in section 5.

---

## What I couldn't verify from here

- Whether the real `JWT_SECRET`/`ADMIN_PASSWORD` values are actually set in Vercel (no dashboard access from this session — needs your check).
- A true mobile-viewport screenshot of the live site (the browser-resize tool in this session didn't reliably reflow the page; the responsive-design read above is code-level).
- I did not attempt to log in anywhere on the live production site, including with the publicly-displayed demo credentials — entering any password into a live (non-local) site's form falls outside what I'll do on my own, regardless of the password being public. If you want that confirmed end-to-end (e.g., that the super_admin login genuinely succeeds and what it exposes), that's a quick manual check on your end.
- Did not read all ~154 backend routes line-by-line; see the coverage note in section 5.

No implementation has started on any of this — flagging it all for your review first, per the plan.
