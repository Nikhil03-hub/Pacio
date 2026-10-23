# CareerOS (Pacio) — Complete Feature Guide for Judges

**One line:** CareerOS is an AI-driven *operating system for campus placement intelligence* — it connects students, faculty, TPOs (Training & Placement Officers), recruiters, and institutions on one live command surface, turning raw preparation data (DSA, aptitude, resumes, interviews) into a single forward-looking **Placement Readiness Score** and an executive-grade decision layer.

**Why it matters:** Traditional placement cells run on spreadsheets and look *backwards* (placed vs. unplaced). CareerOS runs on *live signals* and looks *forwards* — predicting outcomes, flagging at-risk students before drives, and giving every stakeholder an AI co-pilot.

**Stack:** React 18 + Tailwind (SPA) · FastAPI (Python) · MongoDB with an in-memory fallback · JWT + Google OAuth auth · deployed on Vercel. Live at **pacio-two.vercel.app**.

---

## 1. Platform Foundation (the base every feature stands on)

- **Six role-based workspaces (multi-tenant RBAC).** super_admin, institution_admin, tpo, faculty, student, recruiter. Each login lands in a *different* workspace by design, scoped to exactly the data that role may see (institution-scoped, department-scoped, or global). *Why: judges care that a platform claiming "100+ colleges" actually enforces real multi-tenant access control — many student projects don't.*

- **Authentication & security.** Signed JWT sessions (HS256), bcrypt password hashing, Google OAuth sign-in, password reset tokens, and per-request route guards (`require_roles`). *How: every API call is gated by a FastAPI dependency that verifies the token, the role, and the institution scope.*

- **Composite Placement Readiness Score (0–100).** The core metric of the whole platform: a weighted blend of **DSA 30% · Aptitude 20% · ATS 15% · Interview 15% · CGPA 10% · Consistency 10%**, computed from each student's *real* activity (not a self-reported number). Everything else — risk flags, forecasts, recruiter ranking — is derived from this. *Why: it's the single number that makes the platform "intelligent."*

- **Audit trail.** Every sensitive action (login, user/student created, MOU uploaded, health recomputed, payout approved) is written to an audit log with actor, role, institution, IP, and timestamp. *Why: real SaaS accountability.*

- **Resilient data layer.** Runs on MongoDB in production, or a custom in-memory database that mirrors Mongo's query API — so the app runs anywhere, even with zero external dependencies (useful for demos and serverless).

---

## 2. Role Dashboards (one per persona)

- **TPO — "Placement Command."** Mission-control view: placement rate, offers, top recruiters, application pipeline, interview queue, readiness risks, and a live decision queue of priority actions. The TPO's daily cockpit.

- **Institution Admin — "Institution Console."** Institution-wide health, department comparison, recruiter pipeline, readiness, and board-report decisions.

- **Faculty — "Faculty Console."** Department-scoped: batch size, readiness average, weak-student detection, DSA/aptitude depth, and an intervention roster for the faculty's own department.

- **Student — "Your Workspace."** Personal placement OS: readiness score, DSA/ATS/aptitude progress, ranked next moves, open drives, and applications.

- **Recruiter — "Recruiter Console."** Hiring funnel: open drives, readiness-ranked talent pool, pipeline (Kanban), interview movement, and hiring analytics across partner institutions.

- **Super Admin — "Platform Control."** Global layer: institutions, recruiter network, pending onboarding, platform revenue proxy (MRR), audit activity, and broadcast control.

*How they work: each dashboard calls a single `/api/workspace/me` endpoint that returns a role-specific payload (headline, KPIs, priority actions, alerts, and data sections), so the front end stays thin and every number is computed server-side from live data.*

---

## 3. AI Intelligence Layer (the differentiator)

This is the layer that makes judges say *"AI platform, not a dashboard."* All of it is computed from real data — no feature depends on a paid LLM to function.

- **AI Executive Summary (live).** A board-ready narrative auto-written at the top of the TPO, Institution, Faculty, and Super Admin dashboards — e.g. *"Placement rate is 72%, 72 of 100 placed; 702 offers across 148 recruiters, averaging 8.3 LPA, peaking at 80 LPA from Amazon; 58 students need intervention. Recommended focus: run a readiness booster."* *How: it reads the live placement/readiness/alert data and composes the sentence; it recomputes per role and per institution. Why: leadership wants the story, not just the chart.*

- **Voice Narration.** A "Narrate" button reads the executive summary aloud using the browser's Speech API (zero cost, zero dependency). *Why: memorable in a live demo — the platform literally talks.*

- **College Health — 6-Factor Breakdown + AI Verdict.** Instead of a single "52," it shows the six drivers — Placement Rate (30%), Training Completion (25%), Communication (15%), MOU Status (15%), FDP Participation (10%), Revenue (5%) — each with score, weight, and a plain-English detail, plus an AI verdict naming the weakest factor.

- **AI Advisor — Next Actions.** Turns the weakest health factors into a ranked action list ("Begin MOU renewal," "Schedule an FDP session," "Run a CRT booster"). *Why: tells you what to *do*, not just what's wrong.*

- **High-Risk Students widget.** Surfaces the lowest-readiness students the engine already flags, with their top risk reason — turning the prediction model into a visible action list. Links to the roster.

- **AI Risk Radar (Super Admin).** Auto-ranks "colleges needing attention this month" by health score (e.g. *"VCE — Health 0 — Poor"*) plus pending-signup risk. *Why: an executive, portfolio-level view of where to intervene.*

- **Artha AI Copilot.** A natural-language analytics assistant embedded across dashboards: ask *"Which department is weakest?"* or *"What if training completion rises 10%?"* and it returns a board-ready answer, an auto-generated chart, anomaly cards, a what-if projection, and an executive report (Strengths / Weaknesses / Predictions / Recommendations). *Why: anyone can interrogate the data in plain English.*

- **What-If Simulator.** Interactive levers (training, resume, interview, DSA) that project expected placements, conversion, expected package, and risk reduction in real time (e.g. *"78 → 94 placements"*). *Why: the most memorable judging moment — leadership can model an intervention live.*

- **Anomaly Detective.** Scans real year-over-year and department data and surfaces **WINNER / ALERT / OPPORTUNITY** cards (e.g. *"Offers up 14% YoY," "ECE placement 48% — below benchmark," "58 students need intervention"*). "AI" via real variance detection, no LLM required.

- **Placement Forecasting.** Projects expected offers this cycle from the open-drive pipeline and historical conversion, with a confidence band (best / likely / worst).

- **Global Search / Command Palette (⌘K).** Press ⌘K to jump anywhere — pages *and* records: students, recruiters, colleges, and drives — all role-scoped. *Why: enterprise navigation across a large platform.*

---

## 4. Student Features

- **AI Analysis.** A personalized action plan that combines DSA, aptitude, ATS, interviews, consistency, CGPA, and applications into one readiness verdict with a predicted package band and risk level, plus the top three things to fix.

- **Readiness scoring.** The student's live 0–100 score with a six-component breakdown and band (Placement Ready → Needs Intervention).
- **DSA tracker + in-browser code editor.** Tracks question-level progress across a curated 12-topic / 108-problem interview curriculum (original prompts and rationale), with a Monaco (VS Code-style) editor to solve and submit problems.

- **Aptitude tracker.** Sectional aptitude performance (quant, reasoning, verbal, DI) with accuracy, speed, and mastery.
- **ATS analysis flow.** Upload a résumé to get an ATS score, keyword-gap analysis, format quality, recruiter-match, and version history. *Why: turns static PDFs into measurable, improvable signals.*

- **Resume builder.** Build a structured résumé (Classic / Modern / Technical templates) directly in-app.
- **AI Mock Interview.** A simulated interview experience (LiveAvatar embed) with feedback on communication, confidence, and technical rubric.

- **Skill gap analysis.** After ATS/career analysis, shows missing skills and recommended next steps.
- **Career recommendations.** AI-suggested career pathways (e.g. SDE, Data Engineer, DevOps) ranked by fit %, each with recommended actions.

- **Opportunities.** Open drives matched to the student's profile, "My applications" tracking, interview slots, and announcements.

---

## 5. TPO / Placement Cell Features (operational SaaS depth)

- **Student roster (full CRUD).** Add, search, filter, and act on every enrolled student, with department/status filters, CGPA, placement status, and CTC. *Why: this is the operational backbone — without it, the AI features are just demos.*

- **Cohorts & training.** Program/cohort tracking and CRT/training-completion monitoring.

- **Placement outcomes.** Year-over-year offers, top recruiters, average and top CTC, department breakdown.

- **Application pipeline (Kanban).** Drag candidates across Applied → Shortlisted → Assessment → Interview → Selected/Rejected.

- **Active drives & interview schedule.** Open recruitment drives and interview-slot coordination.

- **Recruiter network.** The recruiters engaging with the institution.

- **MOU management.** Upload, view, renew, and track partnership MOUs (with expiry countdowns and renewal alerts).

- **FDP program.** Faculty Development Program scheduling and attendance.

- **Revenue share.** Revenue tracking and payout approval against the partnership.

- **Reports & exports.** One-click board PDFs (placement, training, department) and CSV exports.

- **Comm log & Broadcasts.** Communication history and announcement broadcasting (Email/Telegram dispatch).

- **Workshop request workflow.** TPO requests a workshop → account-manager approval → status update → notification. *Why: a complete, multi-role business workflow with an audit trail — not "just CRUD."*

- **Benchmarking & Partner chat.** Compare against peer institutions and message the partner team.

- **Team & invites (RBAC).** Add users, assign roles, and grant the matching portal — real authentication, authorization, and multi-tenant access.

---

## 6. Recruiter Features

- **Active drives / open roles.** The recruiter's live open positions across partner institutions.

- **Talent pool (readiness-ranked).** Pre-evaluated candidates filtered by CGPA and ranked by readiness score — recruiters skip manual résumé screening. *Why: ~60% less time-to-hire is the recruiter value prop.*

- **Hiring pipeline (Kanban).** Move shortlisted candidates through the funnel.

- **Interview schedule & shortlists.** Coordinate interviews, save shortlists and filters.

- **Hiring intelligence / analytics.** Conversion rate, ready-talent count, average and top package, upcoming interviews.

---

## 7. Institution Admin Features

- **Institution profile & departments.** Manage the institution's profile and department structure.

- **Training programs.** The institution's training/CRT portfolio.

- **Analytics engine + full intelligence layer.** Department health comparison, placement intelligence, DSA/aptitude/ATS/interview intelligence, plus the AI Executive Summary, Health breakdown, and Copilot scoped to the institution.

---

## 8. Super Admin / Platform Features

- **Institution onboarding + approval queue.** Approve new institutions and review pending signups.

- **Recruiter network & platform stats.** Global recruiter directory and platform KPIs — active institutions, total students, open drives, applications, and an estimated MRR (revenue proxy).

- **MOU vault, FDP, Revenue share, Reports, Broadcasts.** Platform-wide partnership control.

- **Health recompute & Reseed.** Recompute every institution's health score on demand, and a one-click "Reseed demo data" safeguard.

- **AI Executive Summary + Voice + Risk Radar** at the platform level (see §3).

---

## 9. Workflow & Automation (what makes it a *product*, not a demo)

- **Workshop lifecycle** — request → approve → status → notify (multi-role, audited).

- **User lifecycle** — add user → role assignment → login → portal access (authentication + authorization + RBAC + multi-tenant scope).

- **MOU lifecycle** — upload → renew → expiry alerts → renewal recommendation.

- **Notifications engine** — MOU-expiry, high-risk-student, payout, and workshop-approval alerts, dispatched via Email/Telegram.

- **Approval flows** — institution signup approval and revenue-payout approval.

---

## 10. Certificate Generation

- **Bulk e-certificates.** Dynamically rendered, co-branded certificates generated on a Canvas and compiled to vector PDFs (via `@react-pdf/renderer`), with company logos. *Why: a real B2B credential feature — replaces hardcopy templates and manual sign-offs.*

---

## 11. Reports & Exports

- **Board PDF reports** — placement board report, training intervention report, department health report (audience-targeted, with a clear decision each answers).

- **CSV exports** — student intelligence export for downstream tooling.

---

## 12. Technical Highlights (for technical judges)

- **Architecture:** decoupled React SPA ↔ FastAPI via JSON REST + WebSockets; deployed as a Vercel Python serverless function wrapping the ASGI app.

- **Auth:** JWT (HS256) + Google OAuth + bcrypt; RBAC enforced via FastAPI dependencies; institution/department scoping on every query.

- **Data:** Motor/MongoDB with a custom in-memory fallback implementing Mongo's query operators ($or, $in, $gte, $regex, aggregate).

- **Intelligence engine:** a dedicated readiness engine computes the composite score from question-level DSA, aptitude, ATS, interview, CGPA, and consistency signals.

- **Front end:** Recharts (charts), Monaco (code editor), Framer Motion (animation), Tailwind (design system), Web Speech API (voice narration), Radix UI primitives.

---

## How to demo this in 90 seconds (suggested judge flow)

1. **Problem** — open the TPO dashboard: "152 colleges run placements on spreadsheets and find out students aren't ready *during* the drive."

2. **AI insight** — point at the **AI Executive Summary**, hit **Narrate**, show the **Health 6-factor** breakdown and **High-Risk Students**.

3. **Intervention** — open the **Copilot** / **What-If Simulator**: "if we lift training 10%, placements go 78 → 94."

4. **Outcome** — switch to **Recruiter**: pre-ranked talent pool; switch to **Student**: personalized AI action plan. "One platform, every stakeholder, one readiness score."

> Tip for the live demo: open each role's dashboard once a minute before presenting so the serverless backend is warm (first cold load can briefly show zeros). Setting a `MONGO_URL` (MongoDB Atlas) in Vercel removes this entirely.
