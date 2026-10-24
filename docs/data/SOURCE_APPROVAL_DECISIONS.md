# Source Approval Decisions

Phase 2, Workstream C deliverable #3. Written 2026-10-24 by the lead agent.

This document **records the engineering gate**, not a legal opinion. I can read a licence and I can
refuse a source; I cannot grant Pacio a legal right it does not have. Every verdict below is either
"the licence says we may, under these conditions" or "we do not have permission yet". Anything the
owner must sign off on is called out in section 6.

Input: `SOURCE_RIGHTS_EVIDENCE.md` (the rights dossier, 82KB, per-source quotations with retrieval
dates). Where the dossier's claim was load-bearing I re-verified it myself rather than trusting it —
those are marked **LEAD-VERIFIED** below, and two places where the dossier overstated the case are
corrected.

## 1. The rule this applies

Publicly accessible ≠ licensed for reuse. A permissive licence on a scraper's repository does not
license the data it scraped. A college publishing a placement table on its website does not thereby
grant a commercial product the right to redistribute it. Citation is an etiquette, not a licence.

## 2. Verdicts (old → new)

| ID | Source | Was | Now | Basis |
|---|---|---|---|---|
| SRC-033 | tech-interview-handbook | APPROVED | **APPROVED** | MIT, © 2017–Present Yangshun Tay. **LEAD-VERIFIED** via GitHub licence API. Ship the notice. |
| SRC-038 | TheAlgorithms/Python | APPROVED | **APPROVED** | MIT, © 2016–2022 TheAlgorithms and contributors. **LEAD-VERIFIED**. Reference code only, never learner-facing text. |
| SRC-035 | system-design-primer | APPROVED | **APPROVED_WITH_LIMITATIONS** | `LICENSE.txt` grants CC BY 4.0 — **LEAD-VERIFIED by reading the file**. GitHub scores it `NOASSERTION` because the file is non-standard, so a licence scanner will not see it. CC BY 4.0 has no share-alike, but s.3(a) attribution has a **required form**: credit, copyright notice, licence link, source URL, and indication of changes. |
| SRC-021 | Lever boards | APPROVED_WITH_LIMITATIONS | **APPROVED_WITH_LIMITATIONS** | `api.lever.co/robots.txt`: `Allow: /`, `Crawl-delay: 1` — **LEAD-VERIFIED**. Limitation: ToS bars competitor access and benchmarking use; we store metadata + the employer's canonical link only. |
| SRC-020 | Greenhouse boards | APPROVED_WITH_LIMITATIONS | **NEEDS_REVIEW** | **LEAD-VERIFIED and corrected against the dossier**: `boards-api.greenhouse.io/robots.txt` disallows only `/embed/`, so our `/v1/boards/…` path is *not* excluded — the dossier's "the recommended lane is disallowed" overstated it. What is unresolved is the provider **ToS**, which 404'd on every candidate URL. |
| SRC-022 | Ashby API | APPROVED_WITH_LIMITATIONS | **BLOCKED (licence)** | **LEAD-VERIFIED**: `api.ashbyhq.com/robots.txt` → **HTTP 401**; `jobs.ashbyhq.com/robots.txt` → `Disallow: /api/`; product terms unreachable. Unknown policy is treated as refusal. |
| SRC-043 | OGD / data.gov.in AISHE | APPROVED_WITH_LIMITATIONS | **APPROVED_WITH_LIMITATIONS (aggregates only)** — *reversed 2026-10-24* | **LEAD-VERIFIED IN A BROWSER**: the portal footer states that published datasets and metadata are "licensed under the Government Open Data License-India", i.e. the grant exists and the licensor is the publishing ministry — the earlier "no licence field" finding looked at per-resource metadata only. Limit: the portal's education holdings are aggregate counts, not an institution directory (the closest "institute-wise" hit is a 321-byte parliamentary answer). See `OGD_LICENCE_BROWSER_VERIFICATION.md`. |
| SRC-001 | AICTE mirror (Apache-2.0) | APPROVED_WITH_LIMITATIONS | **NEEDS_REVIEW** | Apache-2.0 from a non-owner cannot license AICTE's data. Upstream AICTE terms unreachable (site in maintenance). |
| SRC-041 | AISHE counts | BLOCKED (redistribution) | **BLOCKED (consent)** | Counts endpoint now 404. Stale record, no licence statement. |
| SRC-044 | AICTE institutes API | BLOCKED (consent) | **BLOCKED (consent)** | Endpoint returns `null`; terms page 404. |
| SRC-047 | KMIT placement page | APPROVED_WITH_LIMITATIONS (cite) | **BLOCKED (licence)** | **LEAD-VERIFIED**: the page carries a `Copyright 2026` notice and no reuse licence. Two factual corrections to the register, also **LEAD-VERIFIED**: company-wise tabs now run **2017-18 → 2025-26** (nine years, not "through 2023-24"), and the page **does** publish aggregates — 148 companies, 712 offers, average 8.75 LPA plus a salary band histogram (the register claimed those were absent). Only *median* is genuinely unpublished. |
| SRC-048 | CBIT / BITS Hyderabad / PES | RESEARCH_ONLY | **NEEDS_REVIEW** | Same all-rights-reserved posture is likely; not re-read per institution this pass. |
| SRC-046 | NIRF rankings | RESEARCH_ONLY | **BLOCKED (licence)** | No licence, no API, `robots.txt` 403; footer names INFLIBNET rather than MoE, so the rights-holder itself is unidentified. Methodology proves institute-level placement % (Np) and median salary (GMS) exist but are unpublished — **must never be imputed from a rank band**. |
| SRC-011/013 | NIRF / AICTE official | BLOCKED | BLOCKED | confirmed |
| SRC-015/016/023/024/05c | Jooble / Adzuna / Workable / NCS / Skill India | BLOCKED | BLOCKED (licence or consent) | Adzuna needs a written agreement and a mandated 116×23 badge, and excludes resale/lead-gen; Jooble docs 403 and **its API was not called and its key not used**; NCS terms are liability disclaimers, not a licence. |

Register changed: **11 verdicts moved**, new column `rights_review_2026_10_24` added to all 48 rows.

## 3. What Pacio may do today

**Cleared, with obligations attached**
1. Build the DSA/system-design curriculum content from the three MIT/CC-BY repositories, respecting
   each licence: ship an `THIRD_PARTY_NOTICES` file, and for system-design-primer use the CC BY 4.0
   s.3(a) attribution form (not just a mention). Pacio's own statements must say "inspired by /
   organised with reference to", not "derived from", unless a specific derivation exists.
2. Operate the **Lever** board lane only: metadata + canonical apply link, ≥1s between hits,
   per-row attribution. Greenhouse is built and works but stays off until its ToS is read.
3. Publish *Pacio's own* synthetic demo tenant and *Pacio's own* original content — that was never
   in question.

**Not cleared**
- Any institution directory built from AICTE/AISHE/OGD until written consent or an explicit licence.
- Any per-company placement figures, averages, medians, offer counts, MOUs or partnerships from
  college web pages. KMIT's real numbers are the specific temptation here: they exist, they are
  published, and we may not copy them into a paid product without permission.
- Any Kaggle/scraped placement dataset (already REJECTED; unchanged).
- Ashby, Workable, Adzuna, Jooble, NCS, Skill India.

## 4. Permission requests: drafted, **not sent**

`SOURCE_RIGHTS_EVIDENCE.md` contains drafted request text for AICTE, AISHE/OGD, KMIT and NIRF (Np and
GMS specifically). No request has been sent and no permission has been granted. Sending them is an
owner action; the drafts are labelled "draft, not sent" so nothing can be misread later.

## 5. What I corrected in the dossier rather than accepted

- Greenhouse robots: the dossier treated `Disallow: /embed/` as blocking our endpoint. It does not —
  our path is `/v1/boards/<slug>/jobs`. The real gap is the ToS, not robots.
- Ashby: the dossier cited `Disallow: /api/`; the decisive fact I confirmed is that the API host
  returns **401 for robots.txt itself**, and the jobs host disallows `/api/`. Two independent
  signals, same verdict.
- The pilot breach: my first job-feed run polled Ashby before the robots gate existed (796
  postings, all later rolled back). Disclosed in `JOB_FEED_PILOT_REPORT.md`, remediated in code,
  re-run under enforcement.

## 6. Decisions only the owner can make

| Question | Options | Cost of the wrong choice |
|---|---|---|
| Institution directory | (a) wait for AICTE/OGD consent, (b) licence a commercial dataset, (c) have students/colleges submit their own verified data | (c) is the only lane with no rights problem and it is also the moat; (a) has an unbounded timeline |
| Placement stats | (a) written permission per college, (b) college-entered data only, (c) drop the metric from the pitch | selling a dashboard whose numbers cannot be defended is the commercial risk the mentor flagged |
| Live jobs | (a) Lever-curated Indian boards only, (b) obtain Greenhouse/Ashby terms in writing, (c) paid aggregator licence | (a) is shippable now; (c) is the fastest path to breadth |
| Budget | Adzuna/licensed feeds cost money; consent requests cost time | If neither, the honest product claim is "curriculum + tenant workflow + your data" |

## 7. Gate status

**NO-GO on bulk data import.** Not one external dataset is currently cleared for import into the
application database. The pipeline is built, tested, rolled back, and waiting; the only records it
has ever held are labelled `synthetic` fixtures and pilot rows in a disposable database that was
then emptied.

**GO on the mechanism, GO on the three open-source curriculum sources (with notices), GO on the
Lever-only jobs lane as a prototype.**

**GO/NO-GO for Workstream C: PARTIAL.** The rights picture is now evidence-backed instead of
assumed, four sources were demoted, two dossier claims were corrected, and the register no longer
contradicts the evidence. Remaining blockers are external: unreadable provider ToS, an offline AICTE
site, and four unsent permission letters.
