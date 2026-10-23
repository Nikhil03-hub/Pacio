# Pacio — Campus Intelligence

Multi-tenant placement-intelligence platform for Indian colleges. Six role workspaces
(platform admin, institution admin, TPO, faculty, student, recruiter) over one shared
readiness model, with MOU/partnership management, FDP scheduling, revenue-share tracking,
board-grade reports and automated notifications.

Built as the **SummerSaaS Hackathon Track 5B** submission ("Skill Tank: College/TPO Partner
Dashboard") and subsequently hardened. Deployed at `https://pacio-two.vercel.app`.
The product is internally branded "CareerOS" while the repository and deployment are
"Pacio" — see [brand status](#brand-and-rights-status) before shipping or selling.

## Stack

React 18 (CRA) + Tailwind · FastAPI (Python 3.12) · MongoDB via Motor, with an in-memory
Mongo-compatible fallback for zero-dependency demos · JWT + HttpOnly cookie sessions and
Google OAuth · Vercel (single Python serverless function serving API and SPA).

## Run it

```bash
cp .env.example backend/.env      # git-ignored; JWT_SECRET is mandatory to boot
.venv/Scripts/python.exe -m uvicorn server:app --app-dir backend --port 8000
cd frontend && npm install && npm start
```

Full setup, test, backup and deployment notes: [docs/SETUP_AND_RECOVERY.md](docs/SETUP_AND_RECOVERY.md).
Demo account handling: [docs/DEMO_ACCESS.md](docs/DEMO_ACCESS.md).

## Verify it

```bash
.venv/Scripts/python.exe -m pytest backend/tests/test_hardening.py -q            # 32
.venv/Scripts/python.exe -m pytest backend/tests/test_tenant_isolation.py -q     # 20
PACIO_TEST_MONGO_URL=mongodb://127.0.0.1:27017   .venv/Scripts/python.exe -m pytest backend/tests/test_mongo_integration.py -q  # 3
# legacy suites need a running server with RATE_LIMIT_ENABLED=false (see docs)
cd frontend && REACT_APP_BACKEND_URL= CI=false npm run build
```

Last full run (2026-10-23): **128 automated tests passed** (32 hardening + 20 tenant +
3 real-MongoDB + 73 legacy), frontend compiled clean. Details and exact commands:
[docs/SETUP_AND_RECOVERY.md](docs/SETUP_AND_RECOVERY.md) and
[docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md).

## What is real and what is sample

- **Sample data.** Every institution, student, recruiter, MOU, payout and placement row in
  a fresh deployment is generated demonstration data so the product can be evaluated end to
  end. Some rows reuse real Indian college names; the commercial terms attached to them are
  invented. Read [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) before showing it externally.
- **No customers.** Marketing copy that implied customer logos, testimonials or ratings has
  been relabelled as demonstration/illustrative content.
- **Notifications are simulated** unless `SENDGRID_API_KEY` and Telegram credentials are
  configured; delivery status is recorded in `notification_log` either way.
- **Certificates verify.** `POST /api/certificates/issue` persists an issued certificate and
  the QR on the printed document resolves to `/verify/<id>` on this deployment.

## Documentation

| Document | Contents |
| --- | --- |
| [docs/audit/PACIO_AUDIT.md](docs/audit/PACIO_AUDIT.md) | Requirements traceability to the Track 5B brief, findings by severity, doc-vs-code conflicts |
| [docs/audit/PACIO_BACKLOG.md](docs/audit/PACIO_BACKLOG.md) | 30 prioritised items with acceptance criteria |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Actual system shape, authorization path, data model |
| [docs/SECURITY_AND_PRIVACY.md](docs/SECURITY_AND_PRIVACY.md) | Threat model, controls, residual risks, privacy obligations |
| [docs/COMMERCIAL_READINESS.md](docs/COMMERCIAL_READINESS.md) | Scorecard, competitor and pricing evidence, operating costs |
| [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) | Third-party services, env var names, failure behaviour |
| [docs/PACIO_HANDOFF.md](docs/PACIO_HANDOFF.md) | Current status, blockers, owner decisions |
| [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md) | Verified local / real-DB / unverified external / commercial blockers |
| [docs/DATABASE_RECOVERY.md](docs/DATABASE_RECOVERY.md) | Backup, restore drill, migration integrity, fail-closed guard |
| [docs/CREDENTIAL_REMEDIATION.md](docs/CREDENTIAL_REMEDIATION.md) | Exposed-credential status and provider rotation steps |
| [docs/GIT_REPORT.md](docs/GIT_REPORT.md) | Commit inventory for both repositories |
| [FINAL_PROJECT_DOCUMENTATION.md](FINAL_PROJECT_DOCUMENTATION.md) | Original hackathon build documentation |

## Known limitations

- One Vercel function serves every route: 300 s default duration, 4.5 MB payload ceiling,
  WebSockets in beta, single region. Fine for a demo, not yet right for paying tenants.
- Without `MONGO_URL` the app runs in memory and **loses all data on cold start**.
- No rate limiting, no MFA, no CI, no browser tests, no error monitoring.
- Initial JS bundle is 884 kB gzipped; accessibility and mobile tables need work.
- The DSA curriculum is now an original 12-topic / 108-problem pattern set written for this
  product (the earlier third-party-derived catalogue was replaced on 2026-10-23).

## Brand and rights status

`careeros.com` is an unrelated operating product in the same category and `careeros.app`
redirects there, so the in-product name is not currently safe to ship. All references to
that domain have been removed; the rename decision is open. This repository is public and
carries a proprietary licence notice ([LICENSE](LICENSE)); rotate anything that appeared in
its history.
