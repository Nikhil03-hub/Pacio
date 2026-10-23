# Data Sources and Provenance

All dates are access/verification dates. Nothing here was invented; where a source could
not be established, the data is marked **unverified** rather than given a plausible origin.

| ID | Dataset | Where it is used | Origin and status | Rights / commercial use |
| --- | --- | --- | --- | --- |
| DS-1 | Institution, student, recruiter, job, application, MOU, revenue, cohort and communication records | `backend/seed_data.py` -> `seed_payload()`; seeded at startup into every empty collection | **Generated sample data**, produced for the hackathon. Verified 2026-10-23 by reading the generator: names, CGPAs, offers and payouts are synthesised. | Safe to ship **except** for the real institution names it borrows (DS-2). |
| DS-2 | Real Indian college names used as tenants: KMIT, Vasavi, MREC, MRCET, MRITS, CBIT, VNRVJIET, BVRIT, LIM, SPMP, GMC, SMDC, GPT-MT | `seed_data.py` `INSTITUTIONS`; landing copy | **Real institutions.** Their partnership records, MOU terms, payouts and outcomes in the seed are **invented**. | Not cleared. Presenting invented commercial terms against a named real college is a reputational and legal risk. Replace with fictional names or obtain written permission before any external demo or sale. Backlog BL-27. |
| DS-3 | KMIT placement records 2017-18 to 2025-26 (company, selects, CTC) | `seed_data.py` `KMIT_PLACEMENT_RECORDS`, `YEAR_AGGREGATES`; landing stats; placement intelligence | KMIT (Keshav Memorial Institute of Technology, Hyderabad) publishes **aggregate** figures only - e.g. 148 companies, 712 offers, ~8.75 LPA average for 2025-26 per https://kmit.in/placements/placement.php (accessed 2026-10-23). The **year-by-year company x CTC x selects tuples in this repository could not be traced to any published source** and are treated as modelled, not verified. | Facts a college publishes are generally reusable, but the granular rows are unsourced. Rebuild them from published reports or label them as sample data. Backlog BL-28. |
| DS-4 | DSA curriculum: 18 topics, 474 problems, subtopic buckets and titles | `backend/dsa_catalog.py` -> `build_dsa_question_bank()`; DSA pages and the 30% readiness weight | Structure follows the publicly used takeUforward "A2Z" sheet. Verified 2026-10-23 against https://takeuforward.org/terms-and-conditions: "You may not copy, record, redistribute, sell, modify, or commercially exploit any Platform content without our prior written consent... non-commercial". | **Blocking for a commercial product.** Third-party branding was removed from identifiers and UI copy in this work, which does not create a right to the content. Obtain written consent or replace with an independently defined curriculum. Backlog BL-26. |
| DS-5 | Aptitude sections and topic lists (quant, reasoning, verbal, DI, technical MCQs) | `backend/server.py` `APTITUDE_PREP_SECTIONS`, `seed_data.py` | Generic competitive-exam syllabus topics, standard across the domain; no single proprietary source identified. | Low risk - factual categories. |
| DS-6 | Recruiter and company names (Amazon, Google, Adobe, DE Shaw, Deloitte, Goldman) | seed data, landing page, one seeded announcement | Real companies appearing as (a) sample placement recruiters and (b) formerly as **customers** on the landing page. | The customer claim was removed on 2026-10-23 (`TrustGrid.jsx`, `CustomerStories.jsx`). Remaining use as sample placement data is descriptive and must never be presented as a partnership or endorsement. |
| DS-7 | Testimonials and star ratings on the marketing page | `frontend/src/mock.js` (`featuredTestimonials`, `wallOfLove`, `heroQuote`, `duoQuote`, `cabifyQuote`) | **Fabricated by the product team.** No customer quotes exist. | Now labelled "illustrative role walkthrough - not customer testimonials / not a customer review" in `WallOfLove.jsx`, `CustomerStories.jsx`, `DuoSection.jsx`, `Hero.jsx`, `FinalCTA.jsx`. Delete once real quotes exist. |
| DS-8 | Blog entries "Placement intelligence playbooks" | `mock.js` `blogPosts`, landing Blog section | Fictional article stubs with 2026 dates and no destinations. | Still presents as product content. Backlog BL-24. |
| DS-9 | Fonts: Cabinet Grotesk and Satoshi (Fontshare); Fraunces, Inter Tight, JetBrains Mono (Google Fonts) | `frontend/public/index.html` CDN links; `tailwind.config.js` | Loaded at runtime from public CDNs; verified 2026-10-23 by reading the stylesheet URLs. | Fontshare and Google Fonts licences permit this use. Self-host for a commercial product to drop the third-party runtime dependency and tighten CSP. |
| DS-10 | QR codes on issued certificates | `frontend/src/lib/certificateRenderer.js` | Rendered by calling `https://api.qrserver.com/v1/create-qr-code/?...&data=<verify url>`. | Third-party dependency: the certificate id is disclosed to that service, and if it is unreachable the renderer draws a **decorative fake QR**. Replace with a local QR encoder. |
| DS-11 | Live job listings | `backend/server.py` Jooble integration (`JOOBLE_API_KEY`) | External aggregator API. Not exercised in this audit (no key configured). | Subject to Jooble's terms. A key was previously hardcoded and is now read only from the environment; rotate it (BL-09). |

## Secrets and history

- `memory/test_credentials.md` and `auth_testing.md` published the demo password in a
  **public** repository. Both are removed; remaining docs reference
  `${DEFAULT_DEMO_PASSWORD}` instead of a value.
- Removal is forward-only: the values remain in git history (`git log -p`). Rotate and
  decide about a history rewrite or making the repository private. See BL-08.
- No high-confidence secret patterns (private keys, `sk-`, `ghp_`, `AIza`, Slack tokens)
  were found in the current tracked tree on 2026-10-23.

## Reproducibility

The seed is deterministic enough to re-run: `SEED_DEMO_DATA=true` plus
`POST /api/admin/reseed-demo` restores missing collections without deleting existing rows.
Startup seeding observed on 2026-10-23 produced 56 institutions, 5,450 students,
1,565 jobs, 979 applications and 22,140 DSA rows - which is why `memory/PRD.md`'s claim of
6 institutions and 470 students was corrected rather than trusted.
