# CareerOS · Campus Intelligence — PRD (v2.1)

## Original problem statement
The operating system for placement intelligence — multi-role B2B SaaS with 13 modules.
Real KMIT placement data (2017-18 → 2025-26) + 5 additional institutions.
Light editorial design. GSAP cinematic landing. Each role lands in its own workspace.

## What's been implemented

### v1 (2026-01-18)
First 7 must-have features + central admin + Emergent Google OAuth + SendGrid + Telegram fan-out.

### v2 (2026-01-18 later)
- 6 distinct role-based workspaces (super_admin, institution_admin, tpo, faculty, student, recruiter)
- Email + bcrypt password login + Emergent Google OAuth
- 13 modules wired with real data: Student Intelligence, DSA (Striver A2Z 19 topics · 455 problems), Aptitude (4 sections), Resume ATS, Interview AI, Application Pipeline, Placement Intelligence, Recruiter Intelligence, Training, MOU, Announcements, Reports, Platform Control
- 6 institutions seeded across streams (Engineering / Management / Pharmacy / Medical / Degree / Diploma)
- 470 students with full profiles, 22 recruiters, ~70 jobs, ~880 applications

### v2.1 (2026-01-18 today)
- **PDF reports** via reportlab: Placement Report · Training Report · Department Report (boardroom-ready, editorial monochrome styled, footer with timestamp & page number)
- **CSV exports**: Students · Applications · Placements
- **Interview scheduling** with `.ics` calendar invite attached to SendGrid email + Telegram nudge — auto-advances linked Application to "Interview" stage
- **Multi-user invites** under each institution (TPO / Institution Admin / Super Admin can add team members with role + department; welcome email with temp password sent)
- **GridFS persistence** for MOU uploads + `/api/mou/download` streams original bytes
- **Faculty-scoped DSA view** — Faculty sees ONLY their department's progress with `FACULTY SCOPE · {dept}` badge
- **Mobile drawer polish** — slide-in animation, body-scroll lock, route-change auto-close, overlay-click + X close
- **SendGrid API key wired** — emails will go live once you verify a sender identity in your SendGrid dashboard (until then, notification_log shows `status='failed'` from the SDK — this is expected)

## Testing
- `/app/test_reports/iteration_3.json` — Backend 22/22 v2.1 pytest PASS; Frontend ~98%
- Backend 1094 lines; tests at `/app/backend/tests/test_careeros_v21.py`

## Demo accounts (password `${DEFAULT_DEMO_PASSWORD}`)
| Email | Role | Lands on |
| --- | --- | --- |
| admin@careeros.app | super_admin | /platform |
| institution@kmit.in | institution_admin | /institution |
| tpo@kmit.in | tpo | /tpo |
| faculty@kmit.in (CSE) | faculty | /faculty (DSA scoped to CSE) |
| student@kmit.in (Aarav Reddy · CSE) | student | /student |
| recruiter@amazon.com | recruiter | /recruiter |
| tpo@vasavi.ac.in | tpo (pending) | /pending |

## Backlog
### P1
- Verify SendGrid sender identity to flip emails from `failed` → `sent`
- Wire real Telegram bot token + chat id to flip Telegram from `simulated` → `sent`
- Real-time WebSocket updates for application pipeline + interview schedule
- AI-generated mock interview feedback (LLM integration)
- Resume upload + actual ATS scoring (currently seeded scores)
- Split server.py into routers/ modules (>1000 lines)
- Push notify() to BackgroundTasks for sub-100ms request latency

### P2
- Co-branded report templates with institution logo
- MOU e-signature flow
- Anonymized cross-institution benchmarking
- Weekly digest email cron
- Direct chat between TPO ↔ Skill Tank AM
- College leaderboard for super admin
- LinkedIn / Github profile sync per student
- Stripe sandbox payment for institution onboarding fees
