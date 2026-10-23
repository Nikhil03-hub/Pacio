# Commercial Readiness

Three questions, deliberately not merged:

1. **Hackathon success** - was it the winning Module 3 / Track 5B submission? Yes, built
   against the SummerSaaS finale brief. That establishes the concept satisfied judges, not
   that anyone will pay for it.
2. **Product readiness** - does it run reliably, reproduce, deploy and hold data safely?
3. **Commercial readiness** - is there a buyer, a defensible difference, clean rights and a
   workable cost base?

## 1. Product readiness scorecard

| Category | Status | Evidence and next action |
| --- | --- | --- |
| Requirements fit (Track 5B) | **strong** | 15/15 must-haves implemented; must-have 14 (email + Telegram triggers) is simulated until live keys are proven |
| Core workflow completion | **needs work** | Signup -> approval -> roster -> outcomes -> reports works; invited-user activation depends on Google being configured; no scheduler for expiry alerts |
| Product usability | **needs work** | The design system now actually renders; accessibility and mobile tables remain weak (BL-22) |
| Technical reliability | **blocked on a decision** | One Vercel function: 300 s default duration, 4.5 MB payload ceiling, WebSockets in beta, `iad1` only; without `MONGO_URL` every cold start erases data |
| Security and privacy | **needs work** | P0 auth/tenancy defects fixed and regression-tested; no rate limiting, bearer token in localStorage, no MFA |
| Data quality and rights | **blocked** | DSA curriculum conflicts with the publisher's non-commercial terms; real college names carry invented commercial records; KMIT granular rows untraced |
| Deployment and reproducibility | **needs work** | Builds and runs from a clone, but three conflicting Python manifests and no lockfile leave the deployed dependency graph unpinned |
| Testing and observability | **partial** | 92 automated tests pass; no CI, no browser tests, no error reporting or uptime monitoring in the repo |
| Maintainability and handover | **needs work** | A single 7,200-line `server.py`; docs contradicted the code in several places (now corrected) |
| Customer and market evidence | **unverified** | No customer, pilot, LOI, tender or willingness-to-pay evidence exists anywhere in the project |
| Unit economics | **estimable, not proven** | Cost model below; no revenue data |
| IP and licence transfer readiness | **weak** | Public repository with no licence until this work (proprietary notice added); secrets in history; brand collides with an operating product |

## 2. Market evidence (all accessed 2026-10-23)

**The only published price found in this category:** PlacementPilot AI, "affordable
placement software for colleges" - Foundation INR 25,000/month (5 users, 500 candidates,
25 interviews, 10 AI reports) and Growth INR 55,000/month, with an enterprise tier and
"special pricing for government institutions" (https://placementpilot.ai/pricing). That is
one competitor's list price, not a market average and not evidence of sales.

Other real vendors addressing the same buyer, all quote-only: Orell placement management,
Edumarshal T&P (claims 550+ institutions - vendor claim), Creatrix Campus (states plainly
"priced around your institution, not a price list"), Vidyalaya LMS, vmedulife, Ken42,
MagoFOG, Reculta, Placecom, rbtechservices. Global equivalents for the same buyer:
Handshake, Symplicity CSM (including a career-readiness skills module), Interstride.
Institution-side pricing for Handshake and Symplicity was **not found** from official
sources.

Candidates checked and **discarded** as not being placement-cell software: Agnify, Avanti,
Aryane, JobHunt, iFound, FreshQuotient, Zinc, Taggd, Uniproducts - the last three are
employer-side ATS or marketplaces.

**Genuinely uncommon in Pacio** versus those feature lists: MOU/partnership document
management with renewal alerts, revenue-share and payout approval for the college
relationship, FDP scheduling with attendance, Telegram as a first-class channel, a
communication log with the vendor's own account manager, and a platform super-admin layer.
**However**, MOU/contract and FDP functions also sit inside college-ERP products (DigiPix,
Jupsoft), and no tender, RFP or buyer statement asking for MOU/revenue-share software was
found - so demand for the differentiated parts is **unproven**, and absence in competitor
feature lists is not evidence of a market.

**Free substitutes:** Excel/Google Sheets plus WhatsApp groups; the National Career Service
portal, free by policy (https://www.ncs.gov.in/); AISHE reporting colleges already complete
for the government (https://www.aishe.gov.in/); and colleges' own published placement
pages.

**Searched for and not found:** any tender or GeM award amount for this software class; any
AICTE/MEITY/NSDC/NEP scheme funding a placement-cell dashboard; independent (non-vendor)
evidence of TPO willingness to pay; a sourced total addressable market. Accordingly **no
valuation, revenue projection or "worth N lakhs" figure is offered here.**

## 3. Operating cost basis (official pages, 2026-10-23)

| Component | Plan | Price | Source |
| --- | --- | --- | --- |
| Vercel | Pro | USD 20/month incl. 1M requests and 1 TB egress; overage USD 2/M requests, 0.15/GB, 0.60/M invocations | https://vercel.com/pricing |
| MongoDB Atlas | M0 / M10 / M20 | USD 0 (512 MB) / ~58 (0.08/hr, 2 GB) / ~146 (0.20/hr, 4 GB) | https://www.mongodb.com/pricing |
| SendGrid | free trial / Essentials | USD 0 for 60 days at 100 emails/day / 19.95/month for 50k-100k emails | https://www.twilio.com/en-us/products/email-api/pricing |
| Telegram Bot API | - | Free; about 1 message/sec per chat, 20/min per group | https://core.telegram.org/bots/faq |
| LLM for copilot (optional) | Claude Haiku 4.5 / Sonnet 4.5 | USD 1/5 and 3/15 per million input/output tokens | https://claude.com/pricing |
| LLM alternative | gpt-4.1-mini / gpt-5-nano | USD 0.40/1.60 and 0.05/0.40 per million tokens | https://developers.openai.com/api/docs/pricing |

A single-tenant pilot therefore costs roughly **USD 80-180/month** in platform fees plus
LLM usage - well below one INR 25,000/month subscription. Infrastructure is not the margin
problem; **sales and support cost per institution** is, and nothing in this project
measures that yet.

**The caveat that dominates this section:** Vercel's limits documentation states that a
Python framework app "builds into a single Vercel Function", with 300 s default duration,
a 4.5 MB request/response payload cap, a 500 MB bundle limit, and WebSockets in public
beta (https://vercel.com/docs/functions/limitations, updated 2026-08-24). MOU uploads,
bulk roster imports, board-report generation and multi-step AI calls all live inside that
one function today. Adequate for a demo; not adequate for paying multi-college tenants
without splitting the backend.

## 4. Rights and transfer blockers

1. **DSA curriculum licence** (DS-4) - written consent or replacement. Blocks a clean sale.
2. **Real institution names with invented commercial data** (DS-2) - before any external demo.
3. **Brand collision** - `careeros.com` is an operating "career action platform" for
   universities, cohort boards and talent pools (Jobworx CareerOS SL, Barcelona), and
   `careeros.app` redirects there. Pacio would share name, category and buyer. Trademark
   conclusion **requires legal review**; the practical mitigation is a rename and domain
   acquisition.
4. **Secrets in public history** - rotate, then decide on a history rewrite or private repo.
5. **No licence file existed** while the repository was public; a proprietary notice was
   added on 2026-10-23. Replace it deliberately if open distribution is ever intended.

## 5. What would make this sellable, in order

1. Prove one institution's workflow end to end on real data with a real notification
   delivery log (BL-10, BL-12, BL-17).
2. Clear the rights blockers above.
3. Put it in front of five placement officers and record what they say, including price
   reactions. Until then the buyer is a hypothesis.
4. Add what a buyer asks for in due diligence: CI, backups with a rehearsed restore,
   uptime and error monitoring, an admin audit export, and a data-processing agreement
   template.
