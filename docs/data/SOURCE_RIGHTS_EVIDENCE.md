# Source Rights Evidence Dossier

Deep-dive on seven shortlisted sources. This document **supersedes** the licence and
verdict claims in `DATA_SOURCE_DISCOVERY_REPORT.md` and `DATA_SOURCE_REGISTER.csv` where
they conflict; every conflict is called out under **Corrections**.

Research date for all retrievals: **2026-10-24** (UTC 02:59–03:20; IST 08:29–08:50).
Method: direct HTTP retrieval of primary pages/endpoints with a desktop browser
User-Agent, plus `archive.org` and GitHub raw/API. No bulk dataset was downloaded into
this repo. No API key was used or spent. The Jooble API was **not called**. Nothing was
committed or pushed. No database was touched.

Evidence labels used throughout:

| Label | Meaning |
| --- | --- |
| VERIFIED | The exact sentence was read from the primary source at the cited URL on 2026-10-24 |
| PARTIAL | Source reached, but the operative wording came via an index snippet, a partial render, or could not be read in full |
| UNVERIFIED | Assertion carried forward that this pass could not confirm |

Verdict vocabulary is the same as `DATA_SOURCE_REGISTER.csv` (`commercial_verdict`).

Two standing principles applied, because they decide most of these cases:

1. **Public accessibility is not a licence.** A number visible in a browser confers no
   right to copy it into a paid product. Absence of a prohibition is not permission.
2. **A scraper's code licence does not licence the scraped data.** Apache-2.0/MIT granted
   by a third party binds only what that third party owns.

---

## 1. AISHE / Ministry of Education OGD

### What it is

All India Survey on Higher Education, run by the Statistics Division, Department of Higher
Education, Ministry of Education, hosted by NIC. Three distinct surfaces, which must not be
treated as one source:

- `https://aishe.gov.in/` — WordPress site: reports, policies, navigation.
- `https://dashboard.aishe.gov.in/hedirectory/` — Angular SPA "Higher Education Institution
  Directory" (redirect target of `https://dashboard.aishe.gov.in/`).
- `https://data.gov.in/` — OGD portal carrying MoE-published AISHE *derived tables*.

### Is there a downloadable institutional dataset?

**No verified bulk download. VERIFIED (absence), PARTIAL (what exists instead).**

- The site's own navigation exposes the directory only as a web app:
  `https://dashboard.aishe.gov.in/hedirectory/#/hedirectory`, and per-category views
  `.../hedirectory/universityDetails/C/ALL`, `/S/ALL`, `/U/ALL`. Retrieved 2026-10-24.
  These are SPA routes requiring AES-encrypted query parameters (per the earlier pass; that
  finding was not re-tested here — **UNVERIFIED**).
- Downloadable artefacts are **report tables, not institution rows**:
  `https://aishe.gov.in/aishe-final-report/`, `https://aishe.gov.in/other-reports/`,
  `https://aishe.gov.in/document/aishe-meta-data-2/` (Meta Data PDF, 397 KB, dated
  05/01/2026, at
  `https://cdnbbsr.s3waas.gov.in/s392049debbe566ca5782a3045cf300a3c/uploads/2025-06-202601051722360630.pdf`).
  **That PDF could not be retrieved: HTTP 504 Gateway Timeout on 2026-10-24 (twice).** Its
  field list is therefore UNVERIFIED.
- `https://he.nic.in/aishereport/#/report/2023-24` and `/2022-23` are link targets from the
  AISHE home page — report viewers, not data APIs.

**Source-stability finding (new):** the JSON endpoint the earlier pass recorded as VERIFIED
is now dead.
`https://pdf.aishe.nic.in/aisheinstitutemanagement/institutionDirectory/getInstitutionCount?surveyYear=2023-24`
returned **HTTP 404** on 2026-10-24 with body
`{"title":"Not Found","detail":"No static resource institutionDirectory/getInstitutionCount."}`.
Two alternate paths also 404. The counts 1,437 universities / 53,116 colleges / 17,039
standalone are therefore **UNVERIFIED as of today**, and `SRC-041`'s "VERIFIED (counts)"
status is stale.

### Exact terms found (quoted)

Primary page: `https://aishe.gov.in/website-policies/` — retrieved 2026-10-24, HTTP 200.
**VERIFIED.**

> **Copyright Policy**
> "Contents of this website may not be reproduced partially or fully, without due permission
> from Ministry of Education. If referred to as a part of another website, the source must be
> appropriately acknowledged. The contents of this website cannot be used in any misleading or
> objectionable context."

> **Privacy Policy** (yes — the reuse clause is under this heading, not the copyright one)
> "Material on this site is subject to copyright protection unless otherwise indicated. The
> material may be downloaded without requiring specific prior permission. **Any other proposed
> use of the material is subject to the approval of Department of Higher Education.**"

> **Terms of Use**
> "The documents and information displayed in this website are for reference purposes only and
> does not purport to be a legal document. AISHE does not warrant the accuracy or completeness
> of the information…"

Footer attribution/ownership statement (VERIFIED):
"Content owned and managed by Statistics Division, D/o Higher Education, Ministry of Education
Government of India". Page last updated markers seen: 27.02.2024 (policies page), 15.10.2026
(home page).

`robots.txt` at `https://dashboard.aishe.gov.in/robots.txt` → **HTTP 404** (no robots policy
published; absence of a signal, not permission).

### The distinction that matters

AISHE's own wording splits use into two tiers:

| Tier | AISHE says | Pacio consequence |
| --- | --- | --- |
| Download / view | permitted, "without requiring specific prior permission" | internal research OK |
| **Any other proposed use** | "subject to the approval of Department of Higher Education" | shipping AISHE-derived rows in a paid SaaS **is** "other use" → written approval required |
| Reproduction | "may not be reproduced partially or fully, without due permission from Ministry of Education" | redistribution blocked outright |
| Citation/reference | permitted, "the source must be appropriately acknowledged" | link + cite + attribute only |

The earlier report summarised only the Copyright Policy and concluded "BLOCKED for
redistribution". That is right but **understated**: the Privacy Policy clause independently
blocks *use*, not just reproduction.

### Required attribution

"the source must be appropriately acknowledged" (VERIFIED). Sufficient form: institution name
+ "Source: All India Survey on Higher Education (AISHE), Ministry of Education, Government of
India" + the specific page URL + survey year + retrieval date.

### Fields actually available

**No placement outcomes. VERIFIED.** From `https://aishe.gov.in/` home text (2026-10-24):

> "Data is being collected on several parameters such as teachers, student enrolment,
> programmes, examination results, education finance, infrastructure. Indicators of educational
> development such as Institution Dens[ity], student-teacher ratio, Gender Parity Index, Per
> Student Expenditure will also be calculated from the data collected through AISHE."

Enrolment, faculty, programmes, examination results, finance, infrastructure, GPI, GER, per-
student expenditure. **Nothing on companies, offers, packages, or placement percentage.** AISHE
cannot supply the core placement promise.

### The OGD / data.gov.in alternative — weaker than the register assumed

Catalogue reached without a key: `https://api.data.gov.in/lists?format=json&filters[title]=AISHE`
→ **HTTP 200, `total: 15`, 10 returned** (VERIFIED, 2026-10-24). Titles read back include:

- "Year-wise Total Expenditure under … AISHE from 2018-19 to 2022-23"
- "State/UT-wise Universities for Providing Higher Education … during 2019-20"
- "Institute-wise Details of Higher Educational Institutions (HEIs) **the Numbers Registered and
  Responded** in … AISHE"
- "District-wise Higher Education Institution in Uttar Pradesh No. of Institutions … 2015-16 and …"
- "Year-wise Gross Enrolment Ratio (GER) in higher education in Madhya Pradesh …"
- "Institution-wise Details of Fund Released to Higher Education Information System (HEIS) …"

Two consequences (both VERIFIED from the returned titles):

1. "Institute-wise" here means **counts of institutions by category**, not one row per
   institution. There is no institution directory in these 15 resources.
2. The `/lists` response carries **no `license` field**. So "GODL-India" is supported only by
   the portal-wide footer, not per-resource (see below) → `SRC-043`'s licence claim is **PARTIAL**,
   not VERIFIED.

Portal-wide footer at `https://data.gov.in/` (VERIFIED, 2026-10-24):

> "This is a **sandbox environment** created for testing and demonstration purposes only. The
> content, data, and functionality **may be incomplete or inaccurate**. Please avoid entering any
> real or sensitive information."
> "Designed, developed & hosted by National Informatics Centre (NIC), MeitY, **Content is owned
> by the respective Ministries/Departments/Organizations and licensed under the Government Open
> Data License-India**. © 2012-2015 GOVERNMENT OF INDIA All rights reserved except published
> datasets/resources and metadata."

**GODL-India itself could not be retrieved.** `https://data.gov.in/government-open-data-license-india`
renders "**Page Not Found**"; `/Godl` returns **403** to direct fetch;
`https://www.india.gov.in/my-government/government-open-data-license-india` → 404. The licence
text, its version, and its exact attribution mechanics are therefore **UNVERIFIED**. Do not cite
GODL-India as a permission until the licence deed is read and versioned.

### What Pacio may lawfully do today

- Read, download and analyse AISHE material for internal research — expressly permitted.
- **Cite** AISHE figures in the UI and in documentation, with acknowledgement, without
  redistributing the underlying rows.
- Ship AISHE-derived institutional rows in a commercial product? **No** — blocked by both the
  reproduction clause and the "any other proposed use" clause.
- Rely on OGD/GODL as the clean path? **Not yet** — licence deed unretrieved, resources are
  aggregate tables, and the portal declares itself a possibly-inaccurate sandbox.

### Verdict

- `SRC-041` / `SRC-042` (AISHE institutional data, dashboard, counts): **BLOCKED (consent)** —
  plus `SRC-041` is additionally **stale/unreachable** (404).
- `SRC-012` (AISHE official, general): **BLOCKED (consent)**.
- `SRC-043` (OGD AISHE catalogue): downgrade **APPROVED_WITH_LIMITATIONS → NEEDS_REVIEW**
  (licence text never read; sandbox banner; no institution-level rows).
- AISHE as a *placement* source: **REJECTED** (the field does not exist).

### Conditions / limitations

1. Written approval from the Department of Higher Education required before any AISHE content is
   reproduced or used commercially.
2. Attribution string on every AISHE-derived citation, with survey year and retrieval date.
3. Never present AISHE as a source of placement outcomes.
4. Re-verify every AISHE endpoint at import time; paths have already broken once.

### Draft permission request — **draft, not sent**

> **To:** The Secretary / Statistics Division, Department of Higher Education, Ministry of
> Education, New Delhi (copy: aishe-helpdesk[at]nic[dot]in; Web Information Manager)
> **Subject:** Request under the AISHE Website Policies for written permission to reproduce
> institutional-directory records in a commercial education product
>
> Respected Sir/Madam,
>
> 1. **Applicant.** Pacio is a B2B SaaS product provided to Training & Placement Offices of
>    Indian colleges. [Legal entity, CIN, registered address, Director.]
> 2. **Basis of request.** We read the AISHE Website Policies at
>    https://aishe.gov.in/website-policies/, which state that "Contents of this website may not
>    be reproduced partially or fully, without due permission from Ministry of Education", and
>    that "Any other proposed use of the material is subject to the approval of Department of
>    Higher Education". We seek that due permission and approval in writing. We do not assume it.
> 3. **Exactly what we would reproduce.** Only the following non-personal directory fields, for
>    institutions located in India: [list, e.g. AISHE institution ID, institution name, address,
>    district, State/UT, institution type, university affiliation, year of survey].
> 4. **Exactly what we would NOT reproduce.** No student records, no faculty records, no
>    individually identifiable data, no placement or salary figures (we note AISHE does not collect
>    placement outcomes).
> 5. **How it would be used.** Displayed inside Pacio to paying institutional customers, in a
>    read-only panel, alongside the attribution string proposed at clause 6.
> 6. **Attribution we commit to.** "Source: All India Survey on Higher Education (AISHE),
>    Statistics Division, Department of Higher Education, Ministry of Education, Government of
>    India; survey year YYYY; retrieved DD-MM-YYYY", shown adjacent to each AISHE-derived figure.
> 7. **Undertakings.** No misleading or objectionable context; no implied MoE endorsement; no
>    resale of the dataset as a standalone dataset; source-refresh at agreed intervals; prompt
>    takedown on notice; agreement to any MoE-standard licence or fee.
> 8. **Alternative we would accept.** If permission cannot be granted, we would equally accept
>    written confirmation of (a) whether any AISHE extract is published under the Government Open
>    Data Licence – India, and if so which version and where, and (b) a link to the authoritative
>    GODL-India deed, since https://data.gov.in/government-open-data-license-india currently
>    returns "Page Not Found".
> 9. **We also note** that
>    `https://pdf.aishe.nic.in/aisheinstitutemanagement/institutionDirectory/getInstitutionCount?surveyYear=2023-24`
>    returned HTTP 404 on 24-10-2026; please confirm the current endpoint, if one is public.
>
> We would be grateful for a written response. We will not publish AISHE content before receiving it.

---

## 2. AICTE data, and the Apache-2.0 mirror

This item requires two separate assessments; conflating them is the trap.

### (a) The mirror repository — `github.com/Ash310u/All-India-Institutions-Data`

**Licence claim VERIFIED.** GitHub API `GET /repos/Ash310u/All-India-Institutions-Data/license`
(2026-10-24) → `{"name":"LICENSE","path":"LICENSE","spdx_id":"Apache-2.0"}`. The file is the
verbatim Apache License 2.0 text (11,337 bytes) beginning "TERMS AND CONDITIONS FOR USE,
REPRODUCTION, AND DISTRIBUTION".

**What the repo actually is (CORRECTION to `SRC-001`).** As retrieved 2026-10-24 it is no longer
a bare data drop — it is an **HTTP API** ("Indian Colleges Institutions API", Express/Vercel)
serving files under `dataset/`, whose README states: "Data is served from files under `dataset/`
by default; **some routes can optionally fetch live from the AICTE upstream**."

Repo contents (GitHub API, 2026-10-24): `.gitignore`, `LICENSE`, `README.md`,
`package-lock.json`, `package.json`, `tsconfig.json`, `dataset/`, `src/`.

`dataset/` listing (VERIFIED):

| file | bytes |
| --- | --- |
| `all-institutions-with-programmes.json` | 24,896,566 |
| `all-institutions.json` | 12,558,752 |
| `metadata.json` | 68 |
| `states/` | dir |

`dataset/metadata.json` verbatim (VERIFIED):
`{"last_grabbed": "2025-10-30T10:17:21.273Z", "records": 39268}`
→ 39,268 records, grabbed 2025-10-30; repo `pushed_at` 2026-05-30. The register's "39,268" and
"refreshed Oct 2025" are **confirmed**.

**Critical gap: there is no `NOTICE`, no data-provenance file, and no upstream-rights reservation.**
Confirmed by directory listing above (no `NOTICE` present) and by reading the README top to bottom
(2026-10-24): the README documents routes and the institution object shape, and **never mentions
AICTE as the data owner, never cites a licence for the data, and never disclaims upstream rights.**
The repo description says only "REST API for AICTE-approved Indian colleges."

**Fields (CORRECTION to `SRC-001`).** The README's documented institution object is:

```
aicte_id, institute_name, address, district, institution_type, women, minority,
other_id, state, university, programmes[]
```

`SRC-001` lists only the first seven and asserts "no NAAC/affiliation data". **That is wrong on
affiliation** — `university` (the affiliating university) and `state` are present in the documented
schema, and `programmes[]` is embedded. NAAC is genuinely absent. The register's limitation cell
must be corrected.

**Legal effect of the Apache-2.0 grant.** Apache-2.0 §2 grants copyright patent and copyright
rights "to the Work", where §1 defines Work as "the work of authorship". Two independent limits:

1. **Nemo dat.** A contributor can license only rights they hold. If the underlying register is
   AICTE's, the mirror's Apache-2.0 cannot sublicense it — it can only cover the mirror's own
   selection, arrangement, code and any original expression. Facts (names, IDs, addresses,
   districts) are thinly protectable, so the transferable value is small.
2. **The grant is silent on the data.** No `NOTICE` file, no attribution-of-source, no upstream
   reservation → we cannot even identify what the author intended to license.

So: **the mirror's Apache-2.0 is real, and legally irrelevant to AICTE's rights position.**

### (b) Upstream AICTE rights position

**The AICTE public website is currently unavailable.** On 2026-10-24:
`https://www.aicte-india.org/` and `https://www.aicte.gov.in/` both return HTTP 200 but serve a
**maintenance interstitial** — visible text: "The site is currently down for maintenance / We
apologize for any inconvenience caused. We are almost done." Every sub-path attempted returns
**404**, including `https://www.aicte.gov.in/terms-conditions` (404), `/terms-conditions/` (404),
`/sitemap.xml` (404), `/disclaimer` (404). `https://facilities.aicte-india.org/dashboard/` →
**HTTP 403**. `https://facilities.aicte-india.org/` → 200, but only a link landing page
("AICTE Dashboard — A Statistical view of AICTE Approved Institutes in India" / "PMKVY Dashboard").

Search-engine index of `https://www.aicte.gov.in/terms-conditions` (retrieved 2026-10-24) returns
this snippet — **PARTIAL**, because the page could not be loaded to confirm scope or the surrounding
clauses:

> "No part of this site shall be reproduced in any form whether electronically or otherwise
> without the prior consent of **AICTE Ltd.** other than temporarily in the …"

Notes, all honest:
- The snippet says "**AICTE Ltd.**", which is not the statutory Council's usual name form
  ("All India Council for Technical Education"). Either the terms belong to a corporate entity
  operating the portal, or the index snippet is corrupted. **Flag for counsel; do not quote as
  AICTE's terms until the live page is read.**
- Wayback could not corroborate: `archive.org` returned "Internet Archive services are
  temporarily offline" and no snapshot exists for `aicte.gov.in/terms-conditions`
  (`/web/available` → `"archived_snapshots": {}`; CDX → `[]`).
- The earlier pass recorded portal-level wording "No part … reproduced … without prior consent of
  AICTE" against `facilities.aicte-india.org`. **This pass could not re-verify it** → `SRC-044` /
  `SRC-045` consent finding is **UNVERIFIED as of today**, though consistent with the snippet.
- `robots.txt` at `https://facilities.aicte-india.org/robots.txt` returned an **empty 200** — no
  crawl policy published.
- Data availability is now also shaky: the previously VERIFIED records endpoint
  `https://facilities.aicte-india.org/dashboard/pages/php/approvedinstituteserver.php?method=fetchdata&stateName=Telangana&year=2024-25`
  returned **HTTP 200 with body `null`** on 2026-10-24 (register said "Telangana 655"). Either the
  parameter contract changed or the year is not published. `SRC-044`'s "VERIFIED (data)" is stale.

### What Pacio may lawfully do today

- Use the mirror's **code** under Apache-2.0 (with the §4 NOTICE/attribution obligations).
- Use the mirror's **directory facts** only if Pacio is prepared to accept that the licensor may
  lack title — i.e. it is a **risk-accepted** use, not a licensed one. It is not defensible as
  "Apache-2.0, so cleared".
- Copy a state JSON into the shipped product and mark it Apache-2.0: **No.** That asserts a
  permission upstream has not granted.
- Present any AICTE-derived row as AICTE-verified/endorsed: **No.**
- Link to AICTE's own institute page instead of storing the row: **Yes**, and this is the honest
  default until consent is obtained.

### Verdict

- `SRC-001` (AICTE mirror, Apache-2.0): **NEEDS_REVIEW** — was
  APPROVED_WITH_LIMITATIONS. The permissive code licence does **not** clear the data; the repo
  carries no provenance or rights notice; and the upstream terms could not be read because the
  AICTE site is down. Do **not** ship mirror rows until (b) is resolved.
- `SRC-013` / `SRC-044` / `SRC-045` (AICTE official, approved-institutes API, course/intake):
  **BLOCKED (consent)** — retained, but the operative terms are **PARTIAL/UNVERIFIED today**;
  re-read `aicte.gov.in/terms-conditions` when the site is back before relying on it either way.
- Any AICTE *placement* use: **REJECTED on facts as well as rights** — the register itself records
  the placement field as "frequently empty", and `SRC-045` already says "never as placement stats".

### Conditions / limitations

1. Treat the Apache-2.0 mirror as an **index** to AICTE, not as licensed data.
2. If mirror rows are used for internal matching/dedup only (not shipped), record that decision
   and the `last_grabbed` (2025-10-30) and `records` (39,268) provenance values.
3. Keep `university`/`state`/`programmes[]` fields available internally, but confirm NAAC is absent
   so the UI never claims NAAC coverage.
4. Never relicense, rebrand or sublicense any AICTE-derived set.

### Draft permission request — **draft, not sent**

> **To:** Member Chair / Secretary, All India Council for Technical Education, Nelson Mandela
> Road, Handewala, New Delhi (copy: the portal's Web Information Manager)
> **Subject:** Written permission to reproduce AICTE approved-institution directory records in a
> commercial product, and clarification of the Terms & Conditions at aicte.gov.in
>
> Respected Sir/Madam,
>
> 1. **Applicant.** [Pacio legal entity, CIN, address, signatory.]
> 2. **Why we are writing rather than relying on access.** Our research found a third-party GitHub
>    repository (`Ash310u/All-India-Institutions-Data`) which publishes a copy of AICTE
>    approved-institution records under an Apache License 2.0 code licence, with a `dataset/`
>    directory containing 39,268 records last grabbed 2025-10-30. **We do not treat that repository's
>    code licence as a licence to AICTE's data**, because the repository grants no rights AICTE has
>    not itself granted, and it carries no provenance or upstream-rights notice. We therefore seek
>    permission from AICTE directly.
> 3. **Fields requested.** AICTE Permanent ID, institute name, address, district, State/UT,
>    institution type, women/minority flags, affiliating university, approved programme, level,
>    approved intake, and the survey/approval year.
> 4. **Explicitly not requested.** Any placement, employment-outcome or salary figure. We note the
>    placement field in AICTE course data is frequently unpopulated and we would not present it as a
>    placement statistic.
> 5. **Use.** Read-only display to paying institutional customers inside Pacio, with a "Source:
>    AICTE" attribution and retrieval date adjacent to each figure, and no redistribution of the
>    dataset as a standalone file.
> 6. **Terms clarification requested.** On 24-10-2026 we could not read
>    https://www.aicte.gov.in/terms-conditions: the AICTE website returned a maintenance page
>    ("The site is currently down for maintenance") and that path returned HTTP 404. An index copy of
>    the clause reads "No part of this site shall be reproduced in any form whether electronically or
>    otherwise without the prior consent of AICTE Ltd. other than temporarily in the …". Please
>    confirm (a) the current authoritative text, (b) whether "AICTE Ltd." is the correct rights-holder
>    name, and (c) whether any AICTE dataset is published under the Government Open Data Licence –
>    India.
> 7. **Endpoints that appear to have changed** — please confirm the current contract:
>    `.../dashboard/pages/php/approvedinstituteserver.php?method=fetchdata&stateName=Telangana&year=2024-25`
>    returned `null` on 24-10-2026, and `https://facilities.aicte-india.org/dashboard/` returned 403.
> 8. **Undertakings.** We accept any licence, fee, attribution, refresh-cadence and takedown terms
>    AICTE imposes, and we will publish nothing before receiving written consent.

---

## 3. KMIT and college-published placement reports

### What it is and where it actually lives

`https://kmit.in/placements/placement.php` — Keshav Memorial Institute of Technology, Hyderabad
("An Autonomous Institution - Accredited by NAAC with 'A' Grade"). Retrieved **HTTP 200, 822,565
bytes**, 2026-10-24. (`https://kmit.in/placement/` → 404; `https://www.kmit.in/` → 404. The
canonical URL is `kmit.in` without `www`.)

### Which academic years are available — **CORRECTION, and a large one**

From the page's own tab identifiers and nav labels (VERIFIED, 2026-10-24):

- **Campus Placements (company-wise) tabs:** `cp2017-18`, `cp2018-19`, `cp2019-20`, `cp2020-21`,
  `cp2021-22`, `cp2022-23`, `cp2023-24`, **`cp2024-25`, `cp2025-26`**
- **Student Placements (per-student) tabs:** `sp2013-14` … **`sp2024-25`**
- Also a `cseplacements` section.

`SRC-047` claims company-wise tables run "2017-18 to 2023-24" and that "2024-26 not published".
**That is now wrong.** Company-wise tables exist through **2025-26**, and per-student lists through
**2024-25**. (The seed's 2024-26 rows therefore cannot be dismissed as "modelled" on the grounds
that nothing is published — they must instead be checked against these tabs.)

### Fields actually published — **SECOND CORRECTION**

Table headers read on the page (VERIFIED): `S No`, `Name of the Company`, `Number of Selects`,
`Internship Per Month`, `CTC (LPA)`, plus `Name of the Student`, `Package` for the student tabs.

**`SRC-047` states "no average, median or total offers". That is wrong.** The page carries a
placement headline for the current batch:

> "KMIT has again created a record placement for **2025-2026 Batch**. **148 companies** have visited
> so far and **712 offers** were made with an **Average Salary of 8.75LPA**."

followed by a distribution: "09 Students … more than 40 Lakhs Per Annum", "17 … 20–40",
"20 … 15–20", "132 … 10–15", "88 … 08–10", "97 … 07–08".

So KMIT publishes: companies visited, total offers, **average salary**, and a salary-band histogram,
plus company-wise selects / internship stipend / CTC, plus a per-student package list. **Median is
still absent** (0 occurrences of "Median" — VERIFIED absence). Caveats that survive: "so far" makes
the 2025-26 figures partial-year; "712 offers" is offers, not distinct students.

### Is there a reuse/rights statement? — **THE DECISIVE FINDING**

**Yes, and it is unfavourable.** The page footer, read verbatim on 2026-10-24:

> **"© Copyright 2026 | KMIT |. All Rights Reserved"**

Elsewhere on the page: **0** occurrences of "reproduc", "consent", "permission" or "disclaim"
(VERIFIED absence). So there is no *permission* — only an express reservation of all rights.

`SRC-047` recorded "No stated terms; cite the source" and issued
**APPROVED_WITH_LIMITATIONS (cite; no aggregate)**. **That is an overstatement.** The source does
state terms — "All Rights Reserved" — and citing a source is not a copyright licence.

### *The number is publicly visible* vs *we may copy it into a paid product*

These are different questions and only the first is answered by the page:

| Question | Answer | Basis |
| --- | --- | --- |
| Can we see 8.75 LPA / 712 offers / Amazon 80 LPA, 1 select? | **Yes** | page reached, HTTP 200, values read |
| Can we state it in Pacio UI **with our own measurement, as a citation/critique**, pointing at the page? | Arguably yes, low risk, but not licensed | quotation of discrete facts with attribution and link-back; no reproduction of the tables |
| Can we **store the company-wise tables and ship them to paying customers**? | **No** | "All Rights Reserved"; no licence; no consent obtained |
| Can we republish the per-student `Name of the Student` + `Package` list? | **No**, twice over | copyright reservation **and** student personal data |

### Is there any Government/UGC/AICTE rule making published institutional data reusable?

**No such rule was found in this pass, and none is asserted here.** What exists instead:

- **RTI Act 2005 / proactive-disclosure duties** oblige public authorities (and, through UGC and
  AICTE conditions of approval, many institutions) to *publish* information. These are **access**
  obligations. Nothing read in this pass converts a duty to publish into a grant of copyright to
  third parties. **PARTIAL** — the specific instruments were not read end-to-end here.
- **GODL-India** does permit commercial reuse with attribution — but it binds only material its
  owner actually publishes under it. It cannot be stretched over a college's self-published page.
  And GODL's own deed could not be retrieved (section 1).
- **KMIT's "Mandatory Disclosure"** is in its own navigation. Mandatory disclosure is precisely the
  paradigm of *required publication* that does not carry a licence.
- KMIT's data is **self-published by a private institution**, not a Government work, so even a
  generous government-work doctrine would not reach it.
- **Not checked, must go to counsel:** whether any provision of the Copyright Act 1957 on
  government works, or any fair-dealing provision, could cover short extraction of factual figures.
  This dossier deliberately **does not** resolve that, and Pacio should not rely on it.

### What Pacio may lawfully do today

- Reference individual published figures in a *critique/comparison* with attribution and link-back.
- Display the figure **as KMIT's own claim**, with the academic-year label, the exact metric name,
  "so far"/partial-year caveats, and the retrieval date — i.e. reproduce a citation, not the dataset.
- Copy the company-wise tables, the per-student list, or the histogram into Pacio's shipped data.
  **No.**
- Ask KMIT for written permission (draft below) — and note the request must be sent by the lead,
  not assumed granted.

### Verdict

- `SRC-047` (KMIT): downgrade **APPROVED_WITH_LIMITATIONS → BLOCKED (licence)** for storing or
  shipping the published tables. A narrow **NEEDS_REVIEW** applies only to single-figure citation
  with attribution, pending counsel. With written college consent: would become
  APPROVED_WITH_LIMITATIONS.
- `SRC-048` (CBIT / BITS Hyderabad / PES counters): **NEEDS_REVIEW** retained as RESEARCH_ONLY-grade;
  same "all rights reserved" logic almost certainly applies and was not re-read for each institution.
- Generalise: **any** college-published placement table inherits its site's copyright reservation
  until proven otherwise. The earlier recommendation "replace KMIT's 2017-18→2023-24 tuples from its
  published table with URL/year citations" is **not cleared** and must not be implemented as written.

### Conditions / limitations

1. Default to **link + cite**, never **copy + store**, for institution-published placement data.
2. Any KMIT-derived figure must carry: institution, academic year, exact metric label as published,
  "as published by KMIT", source URL, retrieval date.
3. Never import `Name of the Student` / `Package` rows — personal data plus reserved copyright.
4. Keep "offers" and "distinct students" as separate fields; never average across them.
5. Label partial-year data ("so far") explicitly as provisional.

### Draft permission request — **draft, not sent**

> **To:** The Registrar / Director – Training & Placement, Keshav Memorial Institute of Technology,
> 3-5-1026, Narayanguda, Hyderabad – 500029 (copy: info@kmit.in)
> **Subject:** Request for written permission to reproduce KMIT's published placement statistics in
> Pacio, and a request to confirm the terms implied by "All Rights Reserved"
>
> Respected Sir/Madam,
>
> 1. **Applicant.** [Pacio legal entity, CIN, address, signatory.] Pacio is a B2B SaaS product
>    licensed to Training & Placement Offices of engineering colleges.
> 2. **What we found.** Your Placements page,
>    `https://kmit.in/placements/placement.php` (retrieved 24-10-2026), publishes company-wise
>    selection tables for academic years 2017-18 through **2025-26** (fields: S No, Name of the
>    Company, Number of Selects, Internship Per Month, CTC (LPA)), a per-student package list for
>    2013-14 through 2024-25, and an aggregate headline "148 companies have visited so far and 712
>    offers were made with an Average Salary of 8.75LPA" for the 2025-2026 batch. We are writing
>    because that page also states "© Copyright 2026 | KMIT |. All Rights Reserved", and we do **not**
>    treat public visibility of those figures as a licence to reproduce them.
> 3. **Permission sought.** A written, revocable, non-exclusive licence for Pacio to reproduce
>    **only** the following, in a read-only display panel: (i) the aggregate figures (companies
>    visited, total offers, average salary, salary-band counts); (ii) the company-wise table rows —
>    company name, number of selects, internship stipend, CTC band — for each academic year.
> 4. **What we will not reproduce.** We will **not** copy, store or display the `Name of the
>    Student` / `Package` list, or any individually identifiable student data. We do not seek it.
> 5. **Attribution we will apply.** "Source: KMIT Training & Placement Office, published placement
>    report, academic year YYYY-YY, https://kmit.in/placements/placement.php, retrieved DD-MM-YYYY",
>    shown adjacent to each figure, with a direct link.
> 6. **Accuracy safeguards we commit to.** We will label the 2025-26 figures as partial-year as
>    published ("so far"); we will present "offers" and "distinct students placed" as different
>    metrics and never conflate them; we will report the average only as KMIT's published average and
>    will not present it as a median; we will remove or correct any figure on written notice from KMIT.
> 7. **Limits we accept.** KMIT may revoke this permission at any time and Pacio will cease display
>    within the period KMIT specifies. Pacio will not resell the data as a dataset or license it
>    onward. No implied endorsement by KMIT of Pacio is asserted anywhere in the product.
> 8. **Alternative.** If a licence is not granted, we will instead limit ourselves to a link to your
>    page, and we would welcome your instruction on how you wish placement figures to be cited.
> 9. **Also asked, as a general matter.** If KMIT would be willing to grant a standing permission to
>    reputable placement-analytics products on standard terms, we would gladly help draft them.
>
> We will not publish KMIT figures before receiving your written response.

---

## 4. NIRF data / API

### What it is

National Institutional Ranking Framework, Ministry of Education; site operated by INFLIBNET Centre,
Gandhinagar. `https://www.nirfindia.org/` — retrieved **HTTP 200, 29,279 bytes**, 2026-10-24.

### Exact terms found

**There are none.** The complete set of navigation targets on the home page (VERIFIED, 2026-10-24)
is: `/Home/About`, `/Home/Advertisement`, `/Home/Archives`, `/Home/Contact`, `/Home/Documents`,
`/Home/Faqs`, `/Home/GalleryView`, `/Home/Index`, `/Home/Parameter`, `/Home/ScreenReader`,
`/Home/Sitemap`, `https://login.nirfindia.org/Grievance`, `https://webcast.gov.in/moe/`, and the
year ranking pages `/Rankings/2016…2025`.

**No Terms of Use, no Copyright Policy, no Website Policies, no Data Sharing policy, no licence.**
Confirmed by link enumeration (all hrefs matching
`polic|copyright|disclaim|term|api|data|download` → **none**) and by the footer text, verbatim
(VERIFIED):

> "Copyright © 2023 Website Managed and Maintained by **INFLIBNET CENTRE**, INFOCITY,
> GANDHINAGAR-382 007, GUJARAT, INDIA."

Note the footer names **INFLIBNET** as maintainer — it does **not** state who owns the data, and
`SRC-011`/`SRC-046`'s "© MoE/NIRF" attribution is an inference, not a quoted statement. Label:
**PARTIAL**.

`https://www.nirfindia.org/robots.txt` → **HTTP 403 Forbidden** (VERIFIED). NIRF actively blocks
robot access to the robots file itself; combined with `/Home/Documents` holding only methodology
PDFs, there is no indication any machine-readable reuse is contemplated.

### Is there an API? — No. VERIFIED

- No API endpoint, no developer page, no bulk download anywhere in the navigation (VERIFIED).
- `/Home/Documents` contains **only** the 15 discipline-wise methodology PDFs, e.g.
  `https://www.nirfindia.org/nirfpdfcdn/2025/framework/Engineering.pdf`. Retrieved and enumerated
  2026-10-24. **No dataset files.**
- The 2025 ranking pages are server-rendered HTML tables with jQuery DataTables. The rank table
  `https://www.nirfindia.org/Rankings/2025/EngineeringRanking.html` → **HTTP 200, 110,459 bytes,
  201 rows** (VERIFIED). `EngineeringRankingALL.html` → **HTTP 200, 533,098 bytes, 1,585 rows**
  but only 3 columns (VERIFIED).
- `https://www.nirfindia.org/Rankings/2025/EngineeringRankingALL.html` previously 403'd for the
  earlier pass; it is reachable with a browser UA. The 403 was a User-Agent effect, not a policy.

### Field granularity (VERIFIED from parsed table headers)

`EngineeringRanking.html` headers:

- Row table: **`Institute ID`, `Name`, `City`, `State`, `Score`, `Rank`**
- Expandable per-institute sub-table: **`TLR (100)`, `RPC (100)`, `GO (100)`, `OI (100)`,
  `PERCEPTION (100)`**
- Example row read back: `IR-E-U-0456`, IIT Madras, TLR 95.70, RPC 90.74, **GO 82.29**, OI 63.25,
  Perception 100.00.
- Per-institute radar images: `https://www.nirfindia.org/nirfpdfcdn/2025/graph/Engineering/<ID>.jpg`
- `EngineeringRankingALL.html` headers: **`Name`, `City`, `State`** only (participated-institute list).

**No placement percentage and no median salary appear on any published ranking page — the string
"plac" and "median" occur 0 times in `EngineeringRanking.html` (VERIFIED).** `SRC-046` is
**correct on the published surface.**

### The trap the earlier report missed — important

The **methodology** proves NIRF collects exactly the two fields Pacio most wants.
`https://www.nirfindia.org/nirfpdfcdn/2025/framework/Engineering.pdf` (HTTP 200, 437,944 bytes,
25 pages, retrieved and text-extracted 2026-10-24) states, verbatim:

> "**3. Graduation Outcomes (GO)** Ranking weight: 0.20 … A. **Combined metric for Placement and
> Higher Studies (GPH): 40 marks** B. Metric for University Examinations (GUE): 15 marks
> C. **Median Salary (GMS): 25 marks** D. Metric for Number of Ph.D. Students Graduated (GPHD):
> 20 marks"

> "A. Combined Metric for Placement and Higher Studies (GPH): 40 marks • **GPH = 40 × (Np/100 +
> Nhs/100)** • **Np = Percentage of graduating students (in UG/ PG programs) placed in the previous
> three years.** • Nhs = Percentage of graduating students … selected for higher studies …"

So NIRF holds institute-level **placement percentage (Np)** and **median salary (GMS)**, submitted by
institutions, and publishes only the blended **GO score out of 100**. Consequences:

1. **Do not reverse-engineer GO into a placement rate or a salary.** GPH, GUE, GMS and GPHD are
   summed; a GO of 82.29 licenses no inference about either. Label any such derivation **modelled**.
2. The right ask from NIRF is the **DCS/underlying metric values**, not the ranking table.
3. Institution-submitted NIRF self-reported data is **self-reported by the institution**; it is not
   audited, and Pacio must not present it as verified.

### What Pacio may lawfully do today

- Cite a rank, an institute ID, a score, or the fact of participation, attributed to NIRF with year
  and URL. **Yes** (citation of discrete facts).
- Store and ship the ranking table / per-institute parameter scores in a paid product. **No** —
  there is no licence at all, and the site blocks `robots.txt`.
- Derive placement % or median salary from GO. **No** — impossible in principle, and misleading.

### Verdict

- `SRC-046` / `SRC-011` (NIRF): **BLOCKED (licence)** — silence is not permission. Field content
  VERIFIED; absence of licence VERIFIED; rights-holder identity PARTIAL (INFLIBNET vs MoE unclear).
  (`SRC-011` was BLOCKED, `SRC-046` RESEARCH_ONLY; unify to **BLOCKED (licence)** with a citation
  carve-out, consistent with sections 1 and 3.)

### Conditions / limitations

1. Rank/score citations only, with `Institute ID`, discipline, year, URL, retrieval date.
2. Never present GO as a placement or salary metric; never impute one.
3. Keep NIRF-derived and institution-published placement figures in separate fields — do not let a
   NIRF score silently validate a college's self-published package claim.
4. Automated harvesting is not defensible here (`robots.txt` 403, no API, no terms). Any ingestion
   must wait for written permission.

### Draft permission request — **draft, not sent**

> **To:** The Project Director, India Rankings / NIRF Monitoring Cell, Ministry of Education,
> Shastri Bhawan, New Delhi (copy: INFLIBNET Centre, Gandhinagar — the site maintainer)
> **Subject:** Request for (a) written terms of reuse for India Rankings data and (b) release of the
> underlying Graduation Outcome metric values (Np, GMS)
>
> Respected Sir/Madam,
>
> 1. **Applicant.** [Pacio legal entity, CIN, address, signatory.] B2B SaaS for college Training &
>    Placement Offices in India.
> 2. **The gap we are trying to close.** We reviewed `https://www.nirfindia.org/` on 24-10-2026 and
>    could locate **no** Terms of Use, Copyright Policy, data-licence or API documentation — the site's
>    navigation offers only About/Parameters/Documents/Notifications/FAQS/Contact/Archives/Sitemap, and
>    the footer states only "Copyright © 2023 Website Managed and Maintained by INFLIBNET CENTRE".
>    `https://www.nirfindia.org/robots.txt` returns HTTP 403. `/Home/Documents` contains only
>    discipline-wise methodology PDFs. We therefore decline to infer permission from public
>    accessibility and ask for terms in writing.
> 3. **First request — a reuse licence.** Written permission for Pacio to reproduce, for institutional
>    customers, the published ranking records: `Institute ID`, institution name, city, state, discipline,
>    year, `Score`, `Rank`, and the five parameter scores TLR/RPC/GO/OI/PERCEPTION, with attribution
>    "Source: NIRF / Ministry of Education, India Rankings YYYY" plus URL and retrieval date, and no
>    implied MoE endorsement.
> 4. **Second, more valuable request — the constituent metrics.** The Engineering methodology
>    (`https://www.nirfindia.org/nirfpdfcdn/2025/framework/Engineering.pdf`) states that Graduation
>    Outcome is "GO = GPH(40) + GUE(15) + GMS(25) + GPHD(20)", where "**Np = Percentage of graduating
>    students (in UG/PG programs) placed in the previous three years**" and GMS is **Median Salary**.
>    Only the blended GO score is published. We request release of the **institution-level Np and GMS
>    values** (with the year and the definition used) under a written licence — or, if release is not
>    possible, confirmation of whether such values exist in a machine-readable form that any third
>    party may be licensed to use. This would be the single most useful public placement dataset in
>    India.
> 5. **Clarification requested — ownership.** Is the data owned by the Ministry of Education, by
>    INFLIBNET, or by the reporting institutions? Who signs a licence? Is any NIRF dataset published
>    under the Government Open Data Licence – India (and if so, which version)?
> 6. **Acknowledgement of limits.** We understand institutions self-report these values, and we will
>    label them as self-reported and un-audited wherever displayed. We will not present derived
>    placement figures as NIRF facts.
> 7. **We will publish nothing derived from NIRF beyond citation before receiving a written reply.**

---

## 5. NASSCOM / industry bodies, and Government labour-market portals

### 5a. NASSCOM

**What it is.** National Association of Software and Service Companies — an industry association,
**not** a Government source. `https://www.nasscom.in/` → HTTP 200, 108,516 bytes, 2026-10-24.

**Exact terms found (VERIFIED):** footer reads

> "© 2026 **National Association of Software and Service Companies. All Rights Reserved.**"

Site legal links enumerated (VERIFIED): `/privacy-policy`, `/refund-policy-and-tc`,
`/policy-advocacy`. `https://nasscom.in/knowledge-center/publications` → **HTTP 404** ("404 - Page
Not Found / Please reach out to us at webmaster@nasscom.in"). `/refund-policy-and-tc` is a refunds
policy and contains **no** data-reuse terms. **No open-data statement, no API, no bulk access, no
licence to reports' contents was found.**

**Bulk/programmatic access: not permitted and not offered.** No documented API exists; the
publications route 404s; and NASSCOM's revenue model includes paid/restricted research
(partly why a public publications path is gated). Absence of an explicit anti-scraping clause is
**not** permission. Note also: NASSCOM report figures (e.g. sector headcount, revenue, hiring
numbers) are **association estimates**, frequently behind paywalls or membership access; a
commercial product re-broadcasting them without licence is a straightforward rights problem, and
attributing "as reported by NASSCOM" does not cure redistribution.

**Verdict:** **BLOCKED (consent)** — copyright expressly reserved; no grant; bulk access not offered.
Individual headline statistics quoted *with attribution and a link* are a much narrower matter for
counsel, not cleared here.

**Draft permission request — **draft, not sent****

> **To:** The President / General Counsel, NASSCOM, Ambit IT Park, Tower B, 4th Floor,
>MG Road, Bengaluru (copy: the NASSCOM research/knowledge function)
> **Subject:** Request for a written licence to cite and reproduce selected statistics from
> NASSCOM industry research in Pacio
>
> Respected Sir/Madam,
> 1. **Applicant.** [Pacio legal entity, CIN, address, signatory.]
> 2. **Position found.** We reviewed https://www.nasscom.in/ on 24-10-2026 and note the footer
>    "© 2026 National Association of Software and Service Companies. All Rights Reserved." We found
>    no open-data licence and no API; https://nasscom.in/knowledge-center/publications currently
>    returns 404. We therefore seek written permission rather than inferring it.
> 3. **Permission sought.** A non-exclusive, revocable licence to (a) quote individual published
>    headline statistics (sector revenue, employee counts, hiring growth, technology-mix percentages)
>    with attribution and link-back, and (b) reproduce named report tables/figures for display to
>    paying institutional customers, if NASSCOM permits on its standard terms and fee.
> 4. **Attribution proposed.** "Source: NASSCOM, <exact report title>, <year>, <URL>, retrieved
>    DD-MM-YYYY", plus "NASSCOM figures are association estimates and are not Government data".
> 5. **Undertakings.** No redistribution of full reports as files; no resale as a dataset; no implied
>    NASSCOM endorsement or partnership; correction/takedown on notice; we will accept any licence fee.
> 6. **Also asked.** Whether a member or research-access subscription would grant the rights in (b),
>    and its current terms — we will not scrape, and would prefer to subscribe.

### 5b. National Career Service (Ministry of Labour & Employment)

**What it is.** `https://www.ncs.gov.in/` → 200 (redirects to `https://ncs.gov.in/`), 278,190 bytes,
2026-10-24. Operated by the Directorate General of Employment (DGE).

**Exact terms found (VERIFIED)** at `https://ncs.gov.in/terms&condition` (HTTP 200, last updated
28-09-26):

> "This official website of the Directorate General of Employment (DGE) has been developed to
> **disseminate information to the general public**. Though all efforts have been made to ensure the
> accuracy and correctness of the content on this website, **the same should not be construed as a
> statement of law or used for any legal purposes**."
> "In no event will Directorate General of Employment (DGE) be liable for any expense, loss or damage
> … arising from use, or loss of use, of data…"
> "In case of any variation between what has been produced on the website about Act, Rules,
> Regulations, Policy Statements etc. and that contained in the relevant Act, Rules, Regulations,
> Policy Statements etc. with the department **the latter shall prevail**."
> "These terms and conditions shall be governed by and construed in accordance with the Indian Laws.
> Any dispute arising under these terms and conditions shall be subject to the exclusive jurisdiction
> of the courts of India."

`https://ncs.gov.in/disclaimer` (HTTP 200, VERIFIED): "NCS is only a facilitator and the concerned
authority cannot be held liable for any misrepresentation of data or information provided herein."
Footer (VERIFIED): "National Career Service © 2026 **Website contents are managed by Ministry of
Labour & Employment, Government of India.**"

**Critical reading:** NCS terms are **liability disclaimers, not a licence**. Unlike AISHE, NCS does
**not** say "may not be reproduced" — but it also does **not** grant any use right. Two facts matter
commercially:
- "**disseminate information to the general public**" — a distribution purpose, not a reuse licence;
- "**NCS is only a facilitator**" + "misrepresentation of data" — employers post the listings, and
  NCS disclaims their accuracy. Redistributing employer postings collected here means redistributing
  **third-party content NCS does not own and disclaims**.

**Bulk/programmatic access: no documented public API.** The site nav (VERIFIED) exposes
`NCS Dashboard`, `NCS Meta Data`, `NESM Reports & Documents`, `EEx Statistics`, `RTI`, `Annual
Reports`, `Classified jobs`, `Sitemap` — reports and portals, not a feed. Nothing in the retrieved
terms authorises API or bulk access. (`api.ncs.gov.in` partner gateways are known to exist but were
**not** reached in this pass → UNVERIFIED.)

**Verdict:** **BLOCKED (licence)** for bulk/programmatic use — terms are silent, and silence favours
the rights-holder. Individual job postings remain the **employer's** content regardless of portal.
`SRC-024` recorded BLOCKED; retained, now with the "disseminate ≠ licence" and "facilitator ≠ owner"
reasoning attached, which is the real basis.

### 5c. Skill India

**Two different portals; both unusable as a data source.** VERIFIED, 2026-10-24:
- `https://www.skillindia.gov.in/` → **redirects to `https://admin.skillindiadigital.gov.in/`** and
  returns only **62 bytes** of visible text. It lands on an **admin** host — not a data portal.
- `https://skillindiadigital.gov.in/` → 200, 89,793 bytes, visible text **94 characters**: "Skill
  India Digital Hub (SIDH) - Upskilling, reskilling, career growth and lifelong learning". It is a
  full client-rendered SPA; **no** links matching `term|polic|api|data|download|copyright` were
  present in the served HTML.

So: no terms retrievable, no API documented, no bulk route. Any conclusion about SIDH's terms would
require rendering the SPA and logging in. **Verdict: BLOCKED (consent) / NEEDS_REVIEW** — do not
claim Skill India data. `SRC-025` (AICTE internship portal, login-gated) is unaffected and stays
BLOCKED.

### Conditions / limitations (whole of section 5)

1. NASSCOM figures: link + cite only, with exact report title and year, plus the
   "association estimate, not Government data" qualifier.
2. NCS: no bulk ingestion; note NCS explicitly disclaims accuracy and calls itself a facilitator, so
   it is not an authority on its own listings.
3. Skill India: treat as inaccessible until its terms are actually rendered and read.
4. For all three, absence of an API is not an invitation to scrape.

---

## 6. The three previously-approved open-source repositories

These are the only cleanly-cleared sources, and two of them carry obligations the register does not
yet record. All three LICENSE files were read from raw content and cross-checked against the GitHub
license API on 2026-10-24.

### 6a. `yangshun/tech-interview-handbook` — MIT

`https://raw.githubusercontent.com/yangshun/tech-interview-handbook/main/LICENSE` (VERIFIED, 1,077
bytes):

> "MIT License / **Copyright (c) 2017-Present Yangshun Tay** / Permission is hereby granted, free of
> charge, to any person obtaining a copy of this software and **associated documentation files** (the
> "Software"), to deal in the Software without restriction, including without limitation the rights
> to use, copy, **modify, merge, publish, distribute, sublicense, and/or sell** copies of the
> Software… **The above copyright notice and this permission notice shall be included in all copies
> or substantial portions of the Software.**"

GitHub license API: `LICENSE`, `main` branch, MIT. Note "**and/or sell**" — commercial use is
expressly granted, and "associated documentation files" reaches the Markdown prose, not just code.

**One nuance the register records correctly and this pass confirms.** `README.md` line 123
(VERIFIED): "I am providing **code** in the repository to you under an open source license. Because
this is my personal repository, the license you receive to my code is from me and not my employer
(Meta)." The README sentence is narrower than the LICENSE file ("code"); the LICENSE is the operative
instrument and covers documentation. MIT also does **not** convey any third party's rights: material
about LeetCode/HackerRank/GfG questions, or company-specific interview questions, remains subject to
those parties' terms. `SRC-033` APPROVED stands.

### 6b. `TheAlgorithms/Python` — MIT

`https://raw.githubusercontent.com/TheAlgorithms/Python/master/LICENSE.md` (VERIFIED, 1,095 bytes):

> "## MIT License / **Copyright (c) 2016-2022 TheAlgorithms and contributors** / Permission is hereby
> granted… to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
> Software… The above copyright notice and this permission notice shall be included in all copies or
> substantial portions of the Software."

Copyright ends at **2022** even though the project is active — a 400-contributor project with no CLA
means individual contributions are not centrally owned; the MIT grant still covers them, but there
is no single entity to warrant title. Use as **oracle/reference implementations**, as `SRC-038`
says. Quality varies and must not be presented as canonical solutions.

### 6c. `donnemartin/system-design-primer` — CC BY 4.0 (**register claim survives; the caveats are new**)

`https://raw.githubusercontent.com/donnemartin/system-design-primer/master/LICENSE.txt`
(VERIFIED, **365 bytes**, GitHub license API `name: LICENSE.txt`, `spdx_id: CC-BY-4.0`):

> "I am providing code and resources in this repository to you under an open source license. Because
> this is my personal repository, the license you receive to my code and resources is from me and not
> my employer (Facebook). / Copyright 2017 Donne Martin / **Creative Commons Attribution 4.0
> International License (CC BY 4.0)** / http://creativecommons.org/licenses/by/4.0/"

The README's License section repeats this verbatim (line 1833–1839). **No share-alike.** This pass
specifically tested whether the register's `SRC-035` "CC BY 4.0 (LICENSE verified)" was overstated —
**it is not**; it is accurate. (The 365-byte size was suspicious; it is a *pointer* to CC BY 4.0
rather than the deed, which is common. The deed at `creativecommons.org/licenses/by/4.0/` governs.)

Caveats to record:
- It covers "code **and resources**", i.e. prose and diagrams — the useful part for Pacio.
- **Not CC0:** attribution is mandatory and, per CC BY 4.0 §3(a), must include the licensee name,
  a link to the licence, an indication of changes, and any supplied copyright notice.
- **The repo itself credits third parties** (its "Credits" section) — e.g. material derived from
  *Designing Data-Intensive Applications*, HLD docs, and images hosted externally. CC BY 4.0 cannot
  relicense what Donne Martin does not own. Do not copy third-party-derived prose or the hosted
  images; use the topics.

### What Pacio must do to comply

| Repo | Must do | Must NOT do |
| --- | --- | --- |
| tech-interview-handbook (MIT) | Ship the copyright + permission notice verbatim in a distributed `THIRD-PARTY-NOTICES` file **and** in any redistributed copy of substantial portions | Present LeetCode/company-specific question content as Pacio's own; imply author endorsement |
| TheAlgorithms/Python (MIT) | Same notice obligation; keep `Copyright (c) 2016-2022 TheAlgorithms and contributors` intact | Market copied solutions as original or as validated answers |
| system-design-primer (**CC BY 4.0**) | Visible attribution satisfying §3(a): "Portions based on *System Design Primer* © 2017 Donne Martin, licensed CC BY 4.0" + hyperlink to repo + hyperlink to the licence + **"adapted from the original"** where modified + keep the third-party Credits section's notices | Copy third-party-derived prose/images the repo itself credits; apply a licence that removes attribution; imply authorship by Donnemartin |

- **No share-alike applies to any of these three.** `SRC-036` (`coding-interview-university`,
  CC BY-SA 4.0) and `SRC-037` (`cp-algorithms`, CC BY-SA 4.0) remain REJECTED for a closed product —
  correct, because share-alike would propagate to Pacio's derivative content.

### Does re-implementing their *topics* create a derivative work?

**No — if Pacio writes its own expression.** This is the key doctrinal point and should be recorded
in the product's engineering rules:

1. **Ideas, facts, methods and topic lists are not protected** — copyright does not extend to
   procedures, processes, systems or methods of operation. "Implement an LRU cache", "explain
   sharding", "two-pointer pattern" are unprotectable ideas; a curriculum *selection* of topics is
   not an appropriation of expression.
2. **Derivative work arises from recitation, translation or close paraphrase of protected text.**
   Copying structure-and-expression (the distinctive question→answer→trade-off prose of the Primer,
   or distinctive headings phrased identically) does create a derivative — which, for MIT, is fine
   *if the notice travels*, but for CC BY 4.0 additionally triggers attribution obligations.
3. **Therefore:** use the repos as **topic vocabularies and test oracles**, write all UI/explanation
   text independently, and forbid paste-through. Keep the attribution table above regardless, since
   it is cheap and it is the honest thing to do.
4. **Do not claim the topics as Pacio's innovation** in investor or customer material.
5. **Do not let the DSA catalogue inherit third-party problem text.** `DSA_COVERAGE_AND_VALIDATION.md`
   already flags every major problem-text source as blocked; an MIT reference implementation does
   **not** license the associated problem statement.

### Verdict

- `SRC-033`, `SRC-038`: **APPROVED** — conditions: MIT notice shipped; no third-party content laundered
  through them.
- `SRC-035`: **APPROVED_WITH_LIMITATIONS** — was APPROVED with only "Attribution required". CC BY 4.0
  attribution is not a courtesy; it has a required *form* (name, licence link, changes flag, source
  link), and third-party-derived material in the repo is outside the grant. Add the notice.

---

## 7. Employer-hosted job boards, and aggregators

### 7a. The robots.txt signals — the finding that changes the verdict

Retrieved with a desktop UA, 2026-10-24, bodies quoted verbatim:

| Endpoint | robots.txt | Reading |
| --- | --- | --- |
| `https://boards.greenhouse.io/robots.txt` (200) | `User-agent: *`<br>`Disallow: /embed/` | The **public Job Board API lives under `/embed/`** — Greenhouse explicitly disallows automated crawling of exactly that path |
| `https://api.lever.co/robots.txt` (200) | `User-agent: *`<br>`Allow: /`<br>`Crawl-delay: 1` | Lever **permits** automated access to the postings API for all agents, with a 1-second crawl delay |
| `https://jobs.ashbyhq.com/robots.txt` (200) | `User-Agent: *`<br>`Disallow: /meeting/`<br>`Disallow: /b/`<br>**`Disallow: /api/`** | Ashby **disallows** its `/api/` path — again the exact machine-readable surface |
| `https://developers.greenhouse.io/robots.txt` (200) | all directives commented out | Docs site crawlable (irrelevant to data) |

**This is the most consequential correction in this dossier.** The plan (Workstream 4) is to poll
these three public JSON endpoints for named Indian employers. Two of three providers disallow robots
on precisely the endpoints to be polled; one (Lever) expressly allows it with a crawl-delay.
`robots.txt` is not a copyright licence, but in a defensibility review it is dispositive evidence that
the provider did **not** contemplate third-party machine harvesting — "publicly available" ≠
"open for aggregation".

### 7b. Provider terms, as actually written

**Greenhouse.** `https://docs.greenhouse.io/job-board.html` (301 from
`developers.greenhouse.io/job-board.html`), VERIFIED quote:

> "**Job Board data is publicly available, so authentication is not required for any GET
> endpoints.**"

That sentence is about *authentication*, not permission, and it sits alongside `Disallow: /embed/`.
**The Greenhouse Terms of Service could not be read.** `https://www.greenhouse.com/legal` returns
200 but serves a JS shell whose visible text is navigation + footer only; `/legal/terms`,
`/terms-of-use`, `/terms_of_use` all → **404** (redirecting to greenhouse.com/legal). No clause on
automated access, reproduction, redistribution, third-party licence or job-posting ownership could be
retrieved. → **PARTIAL / UNVERIFIED on terms; a genuine gap, not a clean bill.**

**Lever.** `https://www.lever.co/legal/terms-of-service` (HTTP 200, 138,595 bytes; visible text
36,792 chars; VERIFIED, 2026-10-24):

> "**Lever's direct competitors are prohibited from accessing the software and/or services provided by
> Lever, except with Lever's prior express written consent.** In addition, the software and services
> may not be accessed for the exclusive purpose of monitoring performance, or functionality, or for
> any other benchmarking or competitive purposes. **These Terms of Service were last updated August
> 25, 2023.**"

> "Subject to all the terms and conditions of this Agreement, Lever will provide Customer with a
> non-exclusive, non-transferable, **non-sublicensable** right to access the generally available
> software services … **solely for Customer's internal use**"

Two observations the earlier report missed:
1. This is the **Customer (employer) agreement**. It does not address a third party reading a public
   postings feed at all — silence again.
2. **But** "the software and services may not be accessed …" plus the competitor bar is a live risk
   for any aggregator, because a public postings endpoint is plausibly within "the services". Pacio is
   not an ATS and so is probably not a "direct competitor", yet that is a judgement call, not a
   clearance. **Needs counsel / written confirmation.** `SRC-021`'s "ToS silent on aggregation" is
   true but incomplete — the ToS is not merely silent, it contains an access prohibition whose scope
   must be interpreted.

**Ashby.** `https://www.ashbyhq.com/resources/terms-and-policies` (HTTP 200) is a JS shell — 764
chars of visible text, listing: Terms of Service, Privacy Policy, SLA, GDPR, AI Terms, Referral
Qualifications Agreement, **Product Specific Terms**, Design Partner Terms, Modern Slavery Statement.
On retrieval, the operative Terms body was **truncated before any API/job-board clause**, and the page
**names a "Product Specific Terms" document which is the instrument most likely to govern the Public
Job Posting API — it was not reachable in this pass.** `https://www.ashbyhq.com/legal` → 404.
→ **UNVERIFIED on Ashby terms.** `SRC-022`'s "No explicit third-party grant found" is the honest
state, but its VERDICT must fall with the `Disallow: /api/` finding.

**Workable content-ownership rule, and the metadata/description split.** Where an ATS's own employer
agreement is the only instrument, the employer (Customer) is the content source; the platform's terms
bind the employer, not Pacio. So the defensible split is:

| Data | Nature | Pacio's position without written permission |
| --- | --- | --- |
| Title, company, location, posting date, external ID, canonical `applyUrl` | short factual metadata | store + link is the low-risk lane (Lever expressly); Greenhouse/Ashby blocked by robots signal |
| **Full job description text** | employer's copyrightable creative expression | **do not copy or store** — this is the redistribution that hurts, and the ATS ToS never grants it |
| Employer salary ranges / requirements | facts, but embedded in protected expression | restate only as Pacio's own structured fields, never verbatim prose |

Practical consequence: show a **headline + link out to the employer's own board**, not a mirrored
description. This also removes the "stale listing" trust problem: the employer page is authoritative.

### 7c. Verdicts on ATS boards

- `SRC-020` Greenhouse: **APPROVED_WITH_LIMITATIONS → NEEDS_REVIEW.** Reason: `Disallow: /embed/`
  targets the exact endpoint, and the ToS could not be read at all. Poll `/embed/.../jobs` only after
  written permission or counsel sign-off; cite the employer's own board otherwise.
- `SRC-021` Lever: **APPROVED_WITH_LIMITATIONS** (strongest of the three). `Allow: /` + `Crawl-delay: 1`
  is affirmative machine-readability consent. Conditions: honour `Crawl-delay: 1`; metadata + applyUrl
  only; do not reproduce description prose; keep the "not a direct competitor / not benchmarking"
  analysis documented, because the ToS bars competitor and benchmarking access.
- `SRC-022` Ashby: **NEEDS_REVIEW → BLOCKED (licence)** for automated polling: `Disallow: /api/` plus
  unreadable ToS plus an unreached "Product Specific Terms" document. Manual, per-employer links to
  `jobs.ashbyhq.com/<company>` pages remain fine (browsing, not scraping).
- `SRC-023` Workable: **BLOCKED (consent)** retained — undocumented widget endpoint, sub-licensing
  restricted; worse now, since an undocumented widget is by definition not offered as a feed.

### 7d. Aggregators — terms only, no key used, Jooble API not called

**Adzuna.** `https://developer.adzuna.com/docs/terms_of_service` (retrieved via index + fetch,
2026-10-24). Operative clauses read back (PARTIAL — retrieved through a content-extraction proxy
rather than a clean direct render; quotes are verbatim but the full deed was not read end-to-end):

> "**Any other use, including commercial analysis, resale of data, and sales prospecting or lead
> generation, requires our written agreement.**"
> "**After the trial period ends … a licence agreement is required.**"
> "**An API user shall label each displayed advert with the phrase 'Adzuna' at least 116 X 23 pixels
> in size…**"
> "**Upon termination … an API user shall immediately remove all insertion codes and data acquired
> from Adzuna.**"

Direct curl of `https://developer.adzuna.com/terms` → **redirects to `/`** (200, ~1 KB shell);
`https://www.adzuna.co.uk/Pages/ApiTermsAndConditions` → **HTTP 403**.

Interpretation for Pacio — **note the fit is worse than "just pay for it":**
1. Adzuna *contemplates* commercial use but only under **written agreement**. → purchase, don't scrape.
2. **Display-only with a mandated Adzuna logo badge (116×23 px) on every advert.** That is a
   *search-and-display* licence, not a data-licence.
3. "**resale of data … and sales prospecting or lead generation, requires our written agreement**" —
   a B2B product showing job inventory to placement cells to drive institutional sales sits close to
   both prohibited categories. Standard API terms likely do **not** cover Pacio's use case.
4. **Termination ⇒ immediate removal of "all … data acquired from Adzuna."** Pacio's schema must keep
   Adzuna-sourced rows separately identifiable, or it cannot honour a takedown. Add
   `source_id`-scoped purge support before signing anything.

Verdict: **BLOCKED (licence)** — as `SRC-016` said, and unchanged. Conditions: negotiated written
agreement, per-advert Adzuna badge, no data resale, purgeable provenance.

**Jooble.** **The API was not called and no key was used or spent, as instructed.**
`https://jooble.org/api/about` → **HTTP 403 to direct retrieval** (VERIFIED twice: curl and fetch).
No terms text was retrievable at all. What is known from the prior pass (500 requests per key
lifetime, key is country-specific, display-only) is therefore **UNVERIFIED** — and the 403 itself is
evidence the provider does not court programmatic clients. Verdict: **BLOCKED (licence)** — retained,
with the sharpened reason: *a provider whose documentation endpoint returns 403 cannot be relied on
for a display-only bridge in a commercial product.* Retire it rather than rotate the key, unless terms
are read in full and signed.

**Not India-relevant, unchanged:** `SRC-017` Arbeitnow (approved, wrong geography),
`SRC-018` Remotive (4 req/day, no redistribution), `SRC-019` RemoteOK (dofollow attribution link
required). Not re-tested this pass → **UNVERIFIED**, but all three are remote-only and cannot serve
placement cells.

---

## Consolidated verdict table

| # | Source | Prior verdict (register) | **This dossier's verdict** | Evidence label | Blocking reason / required condition |
|---|---|---|---|---|---|
| 1 | AISHE institutional directory / dashboard (SRC-012/042) | BLOCKED | **BLOCKED (consent)** | VERIFIED | "may not be reproduced … without due permission from Ministry of Education"; "any other proposed use … subject to the approval of Department of Higher Education" |
| 1b | AISHE counts endpoint (SRC-041) | BLOCKED, "VERIFIED (counts)" | **BLOCKED (consent)** — and **endpoint now 404** | VERIFIED (404) | Record is stale; re-verify before any use |
| 1c | AISHE as a *placement* source | — | **REJECTED** | VERIFIED | Collects enrolment/faculty/programmes/exam/finance/infrastructure. No placement field exists |
| 1d | OGD / data.gov.in AISHE resources (SRC-043) | APPROVED_WITH_LIMITATIONS | **NEEDS_REVIEW** ↓ | PARTIAL | Licence field absent from records; GODL deed unretrievable; portal self-declares a possibly-inaccurate **sandbox**; no institution rows |
| 2 | AICTE mirror `Ash310u` Apache-2.0 (SRC-001) | APPROVED_WITH_LIMITATIONS | **NEEDS_REVIEW** ↓ | VERIFIED (licence) / PARTIAL (upstream) | Apache-2.0 from a non-owner cannot license AICTE data; no NOTICE/provenance; upstream terms unreadable (site down) |
| 2b | AICTE official data / APIs (SRC-013/044/045) | BLOCKED / BLOCKED (consent) | **BLOCKED (consent)** | **PARTIAL** — terms quote came from a search index; site 404/maintenance; data endpoint returns `null` | Written AICTE consent required; re-read `aicte.gov.in/terms-conditions` when live; verify "AICTE Ltd." as rights-holder |
| 3 | KMIT placement page (SRC-047) | APPROVED_WITH_LIMITATIONS | **BLOCKED (licence)** ↓ | VERIFIED | Footer: "© Copyright 2026 \| KMIT \| All Rights Reserved"; no permission; per-student names also present |
| 3b | CBIT / BITS Hyd / PES (SRC-048) | RESEARCH_ONLY | **NEEDS_REVIEW** | PARTIAL | Same reservation likely; not re-read per institution |
| 4 | NIRF rankings / data (SRC-011/046) | BLOCKED / RESEARCH_ONLY | **BLOCKED (licence)** | VERIFIED | No terms of use, no licence, no API, `robots.txt` 403. Citation of ranks only |
| 4b | NIRF as placement-metric source | "no placement %, no median salary" | **NEEDS_REVIEW — request Np/GMS** | VERIFIED | GO = GPH(40)+GUE(15)+GMS(25)+GPHD(20); placement % (Np) and Median Salary (GMS) exist but are not published; must not be imputed |
| 5 | NASSCOM | (not in register) | **BLOCKED (consent)** | VERIFIED | "© 2026 National Association of Software and Service Companies. All Rights Reserved."; publications 404; no API |
| 5b | National Career Service (SRC-024) | BLOCKED | **BLOCKED (licence)** | VERIFIED | Terms are liability disclaimers, not a licence; NCS "only a facilitator", disclaims data accuracy; no public API |
| 5c | Skill India / SIDH | BLOCKED | **BLOCKED (consent)** | VERIFIED (unreachable) | Redirects to an admin host; SPA serves 94 chars; no terms retrievable |
| 6 | tech-interview-handbook (SRC-033) | APPROVED | **APPROVED** | VERIFIED | MIT (c. 2017-Present Yangshun Tay), "and/or sell"; ship the notice |
| 6b | TheAlgorithms/Python (SRC-038) | APPROVED | **APPROVED** | VERIFIED | MIT (c. 2016-2022 TheAlgorithms and contributors); reference code only |
| 6c | system-design-primer (SRC-035) | APPROVED | **APPROVED_WITH_LIMITATIONS** ↑ | VERIFIED | **CC BY 4.0 is correct** (no share-alike) — but §3(a) attribution has a required form, and the repo's own third-party credits are outside the grant |
| 7 | Greenhouse boards (SRC-020) | APPROVED_WITH_LIMITATIONS | **NEEDS_REVIEW** ↓ | VERIFIED (robots) / UNVERIFIED (ToS) | `Disallow: /embed/` on the exact endpoint; ToS not retrievable (404s) |
| 7b | Lever postings (SRC-021) | APPROVED_WITH_LIMITATIONS | **APPROVED_WITH_LIMITATIONS** (keep) | VERIFIED | `Allow: /`, `Crawl-delay: 1`; honour delay, metadata only; ToS bars competitor/benchmarking access — document the analysis |
| 7c | Ashby public API (SRC-022) | APPROVED_WITH_LIMITATIONS | **BLOCKED (licence)** ↓ | VERIFIED (robots) / UNVERIFIED (ToS) | `Disallow: /api/`; ToS truncated; "Product Specific Terms" unreached |
| 7d | Workable widget (SRC-023) | NEEDS_REVIEW | **BLOCKED (consent)** | PARTIAL | Undocumented widget, sub-licensing restricted |
| 7e | Adzuna (SRC-016) | BLOCKED (commercial) | **BLOCKED (licence)** | PARTIAL | Commercial use only under written agreement; display-only with mandated 116×23 "Adzuna" badge; "resale of data … lead generation" excluded; termination requires deleting all acquired data |
| 7f | Jooble (SRC-015) | BLOCKED | **BLOCKED (licence)** | VERIFIED (403) | Docs 403; terms unreadable; API not called, no key used |

Net: the shortlist yields **two clean approvals (MIT ×2)** and **one approval-with-real-obligations
(CC BY 4.0)**, plus **one conditional approval (Lever)**. Everything else is blocked, needs review,
or needs consent in writing.

---

## Corrections to `DATA_SOURCE_REGISTER.csv` / `DATA_SOURCE_DISCOVERY_REPORT.md`

| ID | Field | Register says | Evidence says | Severity |
|---|---|---|---|---|
| SRC-047 | years | "Company-wise 2017-18 to 2023-24"; "2024-26 not published" | Tabs `cp2017-18` … **`cp2025-26`** (9 years); student tabs `sp2013-14` … `sp2024-25` | **High** — inverts the recommendation |
| SRC-047 | metrics | "no average, median or total offers" | Publishes **companies visited (148), total offers (712), Average Salary 8.75 LPA**, and a 6-band salary histogram. Only **median** is truly absent | **High** |
| SRC-047 | licence/verdict | "No stated terms; cite the source" → APPROVED_WITH_LIMITATIONS | Footer **"© Copyright 2026 \| KMIT \| All Rights Reserved"** → BLOCKED (licence) | **Critical** — the report's #1 actionable recommendation ("replace KMIT tuples from its published table") is not cleared |
| SRC-041 | status | "VERIFIED (counts)" — 1,437/53,116/17,039 | Endpoint returns **404** "No static resource institutionDirectory/getInstitutionCount" | High — stale record |
| SRC-001 | schema | fields = 7, "no NAAC/affiliation" | Documented object also has **`other_id`, `state`, `university`, `programmes[]`** — affiliation **is** present; NAAC absent | Medium |
| SRC-001 | nature | "JSON per state plus a 24 MB programme file" | Now an **HTTP API** over `dataset/` (`all-institutions.json` 12,558,752 B; `all-institutions-with-programmes.json` 24,896,566 B), and "some routes can optionally fetch live from the AICTE upstream" — i.e. it can proxy AICTE live | Medium |
| SRC-043 | licence | "GODL-India; attribution required" → APPROVED_WITH_LIMITATIONS | `/lists` returns **no `license` field**; GODL deed **unretrievable** (404/403/404); footer says content is "owned by the respective Ministries…" and portal is a **"sandbox … may be incomplete or inaccurate"** | **Critical** — the "cleanest licensed route" is not evidenced |
| SRC-044 | data | "VERIFIED (data): Telangana 655 (2024-25)" | Same endpoint → **HTTP 200, body `null`**; terms page 404/maintenance | High |
| SRC-046 / NIRF | terms | "No explicit reuse licence; content © MoE/NIRF" | Confirmed no licence; but the footer names **INFLIBNET**, not MoE — rights-holder unidentified | Low–Medium |
| Workstream 4 | ATS boards | "ToS silent on third-party aggregation" → APPROVED_WITH_LIMITATIONS | Greenhouse `Disallow: /embed/`; Ashby `Disallow: /api/`; Lever `Allow: / Crawl-delay: 1`. Also **Lever's ToS prohibits competitor access and benchmarking use**, and Greenhouse/Ashby ToS are **unreadable** | **Critical** — the recommended ingestion lane is 2/3 disallowed |
| Workstream 2 | KMIT/CBIT etc. | "Distinguish clearly: visible vs copyable" was recommended | Implemented: KMIT fails the second test on its own stated terms | Medium |

---

## What is still unknown

1. **GODL-India's actual text and version.** The deed could not be retrieved from any of
   `data.gov.in/government-open-data-license-india` (404 shell), `data.gov.in/Godl` (403), or
   `india.gov.in` (404). Until read, no OGD-based redistribution can be claimed. **Highest-value gap.**
2. **Per-resource licence metadata on data.gov.in.** `/lists` omits `license`; needs a free key to
   inspect individual records. No key was used.
3. **AISHE institutional field list, definitively.** The 397 KB "AISHE Meta Data" PDF (dated
   05/01/2026) **504'd twice**. Today's field conclusion rests on the site's own parameter sentence;
   the authoritative schema is unread.
4. **Whether AISHE Plus / newer survey cycles added any graduate-outcome field.** Not established;
   the current site text says no placement data, and the metadata PDF is unread.
5. **AICTE's operative terms in full.** `aicte.gov.in/terms-conditions` is 404 behind a maintenance
   page; the sentence relied on came from a search index; Wayback is offline with no snapshot. Also
   unresolved: why the clause says "**AICTE Ltd.**" rather than the Council.
6. **Greenhouse Terms of Service content.** Four candidate URLs 404; `/legal` is a JS shell. No
   clause on scraping, aggregation, redistribution or posting ownership is known.
7. **Ashby "Product Specific Terms."** Named on `/resources/terms-and-policies` but never reached —
   it is the document most likely to govern the Public Job Posting API.
8. **Whether any ATS ToS affirmatively permits third-party aggregation.** Still no. Lever's
   robots `Allow: /` is a crawl signal, not a licence; and Lever's own ToS contains a competitor /
   benchmarking bar whose scope for Pacio needs legal reading.
9. **Adzuna pricing, and whether its standard API licence can cover a B2B product** whose use
   resembles the excluded "resale of data / lead generation" categories. No commercial enquiry made.
10. **Jooble's terms** — docs 403; nothing readable; API deliberately not called.
11. **NASSCOM report-level reuse wording.** Association-level "All Rights Reserved" is confirmed;
    the per-PDF copyright page was not read (publications path 404s).
12. **Whether any *other* Indian institution publishes company-level placement tables like KMIT.**
    Still none found. Also still no openly-licensed multi-institution placement dataset.
13. **Skill India Digital Hub terms/API** — requires rendering the SPA and possibly login.
14. **Whether NIRF will release institute-level `Np` (placement %) and `GMS` (median salary).**
    These exist in methodology but are not published; a written request is drafted. **This is the
    single highest-value open question for the product**, and the permission in item 4 of that draft
    is worth pursuing before anything else.
15. **Copyright Act 1957 analysis** of government works / fair dealing for short factual extraction —
    deliberately **not** performed here; needs counsel. No provision was relied upon in any verdict.

---

## Bottom line for shipping decisions

- **Ship today, clean:** MIT tech-interview-handbook + MIT TheAlgorithms/Python (notice file
  required), CC BY 4.0 system-design-primer (formal attribution required). Topics re-implemented in
  Pacio's own words create no derivative work.
- **Ship with conditions:** Lever public postings (metadata + applyUrl, `Crawl-delay: 1`, no
  description prose) — the **only** government-adjacent-adjacent/ATS lane with an affirmative
  machine-access signal.
- **Do not ship, despite being publicly readable:** KMIT tables, AICTE rows, AICTE mirror rows,
  AISHE anything, NIRF tables, NASSCOM figures, NCS listings, Adzuna/Jooble results, Ashby or
  Greenhouse JSON. Each has either an express reservation, an express consent requirement, an
  explicit robots disallow, or no terms at all.
- **Do not claim:** that any Indian Government source licenses commercial redistribution of placement
  outcomes; that AISHE contains placement data; that NIRF GO scores can be converted into placement
  rates or salaries; that the KMIT seed tuples are sourced; or that permission exists anywhere it was
  merely drafted.
