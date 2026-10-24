# Permitted Dataset Scan — New Candidates Only

**Retrieval date:** 2026-10-24 (UTC 15:40–16:15).
**Scope:** new candidates only. The 48 previously screened sources are excluded, and the
following are taken as settled and were **not** revisited: KMIT (blocked), `Ash310u/All-India-Institutions-Data`
(needs review), AICTE/AISHE official (blocked — consent), data.gov.in AISHE catalogue
(needs review — no licence field), NIRF (blocked), Adzuna / Jooble / Workable / NCS /
Skill India (blocked).

**Method:** GitHub REST search API (10 repository queries, unauthenticated), direct
`raw.githubusercontent.com` fetches, Wikidata Query Service, and direct HTTP to
`data.gov.in` and `data.telangana.gov.in` with a desktop User-Agent. No API keys used, no
database touched, no app code changed. One 24.9 MB JSON was downloaded to count rows
(noted below; it was not stored in the repo). Every licence below was read from the
primary surface named in the "licence seen" column on the retrieval date.

**Verdict vocabulary:** APPROVED / CONDITIONED / NEEDS_REVIEW / REJECTED / NONE FOUND.

---

## 1. Verdict table

| # | Source | URL | Licence seen | Licence authority | Rows | Fields | Verdict |
|---|--------|-----|--------------|-------------------|------|--------|---------|
| N-01 | `anburocky3/indian-colleges-data` | https://github.com/anburocky3/indian-colleges-data | MIT (repo `LICENSE`, 1,077 B, via GitHub licence API) | Uploader — **code only**; README states data is AICTE's | **13,089** institutions (counted) | `aicte_id, institute_name, address, district, state, institution_type, university, women, minority, other_id, programmes[]` | **NEEDS_REVIEW** — AICTE data under an MIT wrapper |
| N-02 | `MustansirZia/institutions-api` | https://github.com/MustansirZia/institutions-api | MIT (repo) | Uploader — code only; India data provenance unstated | Not counted | Name/type list only; India JSON bundled in `data/json/*.json`, schema not inspected | **NEEDS_REVIEW** — no provenance, no useful fields |
| N-03 | `mratanusarkar/Dataset-Indian-Companies` | https://github.com/mratanusarkar/Dataset-Indian-Companies | **None** (GitHub API `license: null`) | n/a | Not counted | Company names scraped from AmbitionBox | **REJECTED** — no licence + admitted third-party scrape |
| N-04 | Wikidata — Indian colleges | https://www.wikidata.org/ | **CC0** (structured data) | Wikimedia / Wikidata licensing policy | **23,173** direct `P31=college`, **1,204** `P31=university`; **14,165** colleges with a website | Label, instance-of, located-in (city/district/state), country, official website, coordinates | **CONDITIONED** — clean licence, weak fitness |
| N-05 | data.gov.in (any resource) | https://www.data.gov.in/ | **GODL-India at portal level only**; no per-resource licence retrievable | MeitY / NIC (portal policy) | n/a | n/a | **NEEDS_REVIEW** — portal presence ≠ per-resource licence |
| N-06 | Telangana Open Data Portal | https://data.telangana.gov.in/ | None visible (JS app shell; CKAN API 404) | State government | n/a | n/a | **UNVERIFIED** — no licence evidence obtainable |
| N-07 | Placement-statistics lane (GitHub sweep) | — | — | — | **0 qualifying** | — | **NONE FOUND** |

Kerala (`data.kerala.gov.in`, `opendata.kerala.gov.in`) and Odisha (`data.odisha.gov.in`)
did not resolve from this network (DNS failure) — recorded as **unreachable**, not as
"no licence".

---

## 2. Per-candidate detail

### N-01 `anburocky3/indian-colleges-data` — the best-structured Indian college dataset found, and still not licensable

**What it is.** A Next.js API plus a bulk JSON export of AICTE institutions with
programme-level rows. The export is genuinely richer than the previously screened
`Ash310u` mirror: institutions and their approved programmes are nested, and the AICTE
institution identifier is carried in the row.

**Licence actually seen.** `LICENSE` present (1,077 bytes); GitHub's licence API reports
`MIT`. That is a real MIT grant — over the wrapper code and the uploader's own schema
choices.

**Why the licence does not travel with the data.** The README says, verbatim:

> "This api contains 1278 colleges data, like names, district, address, etc., including private, government, autonomous, and affiliated institutions across India. The data is sourced from the All India Council for Technical Education (AICTE) website."

The uploader is therefore a redistributor, not an author. The MIT grant cannot bind
AICTE's database. This is the same defect as `SRC-001` in
`DATA_SOURCE_REGISTER.csv`, reached independently — the finding is confirmed, not new.

**Format and count.** Single file
`data/institutions-with-programmes.json`, a JSON array, **24,896,526 bytes** (24.9 MB —
marginally over the 20 MB counting budget; counted once, not retained). Parsed:
**13,089** institution records.

Note the metadata contradiction: the README says 1,278 colleges, the repository
description says 39,268, and the file contains 13,089. None of the three agrees. Treat any
"row count" claimed in the repo metadata as unreliable.

**Fields and missingness (13,089 rows):**

| Field | Missing |
|---|---|
| `aicte_id` | 0 |
| `institute_name` | 0 |
| `address` | 0 |
| `district` | 0 |
| `state` | 0 |
| `institution_type` | 0 |
| `university` | 0 |
| `women` | 4 |
| `minority` | 4 |
| `other_id` | 0 |
| `programmes[]` (nested: `programme, level, course, course_type, shift`) | 0 |

Completeness is high. That is exactly what an automated export from an approval database
looks like.

**Machine-generated or scraped?** Machine-generated from AICTE's own records. Evidence:
identifiers in AICTE's format (`"aicte_id": "1-44638801317"`, plus a parallel
`other_id`), ALL-CAPS institution names, and approval-style programme codes
(`"course_type": "Course Institute-1"`, `"shift": "1st Shift"`). This is not a
hand-curated list and it is not a scrape of rendered HTML — it is a dump of the
regulator's database.

**Verdict: NEEDS_REVIEW.** Structurally the best candidate encountered, legally
indistinguishable from the already-demoted mirror.

### N-02 `MustansirZia/institutions-api` — MIT, but nobody says where the India rows came from

README describes an `InstitutionProvider` architecture and states the data is "lazily
loaded ... via JSON files located in `data/json/*.json`". It names **no upstream source**
for the Indian college file. A name-only list with no city/state/code guarantees, no
placements, and no provenance fails both tests that matter: authority and fitness. Killed
without further inspection.

**Verdict: NEEDS_REVIEW** (would become REJECTED on any attempt to rely on it — the
uploader has not demonstrated ownership).

### N-03 `mratanusarkar/Dataset-Indian-Companies` — rejected on sight

GitHub API returns `license: null`. Repository description: *"Web Scraping 'List of
companies in India' from AmbitionBox Website using Python and Beautiful Soup."* No
licence and an admitted scrape of a commercial site. This is the exact pattern the
standing rules prohibit.

**Verdict: REJECTED.**

### N-04 Wikidata — a clean CC0 grant, and the only licence in this pass that needs no interpretation

**Licence actually seen.** `https://www.wikidata.org/wiki/Wikidata:Licensing`, retrieved
2026-10-24:

> "All structured data (i.e. the main, Property, Lexeme, and EntitySchema namespaces) is released into the public domain under Creative Commons Zero."

The same page adds: *"All data in Wikidata has a CC0 license. Wikidata avoids hosting data
that lacks a CC0 license."* CC0 permits commercial use, redistribution and modification
with no attribution condition. The licensor is the Wikimedia movement's own policy, and
the data is the community's own compilation — this is the one candidate whose licence
authority is not in question.

**Counts (Wikidata Query Service, 2026-10-24):**

- `P31 = Q189004` (college) **and** `P17 = Q668` (India): **23,173**
- `P31 = Q3918` (university) and `P17 = Q668`: **1,204**
- of the 23,173 colleges, those with `P856` (official website): **14,165**

These are direct `instance-of` counts. A broader `P31/P279*` (subclass) count timed out at
60 s and is not reported. `Q1662221` returned 0, i.e. that QID is not "institute of
technology" — the type taxonomy needs mapping before any import.

**Fields available:** label, instance-of, located-in (`P131`, city/district/state),
country, official website, coordinates. **Not available:** AICTE or UGC institution
codes, affiliation, intake, accreditation, placement data. Coverage skews to universities
and notable colleges; AICTE-approved polytechnics are likely thin (unmeasured — no join
against a known list was run).

**Quality.** Community-entered, so values look human, not generated. A 5-row sample
returned the same institution multiple times because it carries two website values — any
import must deduplicate on QID and collapse multi-valued properties.

**Verdict: CONDITIONED.** Rights are clean; fitness is limited to a name/city/website seed
list. Not a placement source, and not a substitute for an AICTE directory.

### N-05 data.gov.in — GODL exists, but not where it is needed

The portal footer links "GODL", and the licence instrument itself is reachable:
`https://data.gov.in/sites/default/files/Gazette_Notification_OGDL.pdf` returns HTTP 200,
`application/pdf`, 1,179,227 bytes on 2026-10-24. The Government Open Data License is a
real, gazette-notified licence that permits commercial use.

What could **not** be verified is the per-resource licence. `data.gov.in` is a
single-page app: the AISHE catalogue URL
(`/catalog/all-india-survey-higher-education`) and a deliberately invalid resource slug
(`/resource/this-slug-does-not-exist-xyz`) both returned the **identical 1,115,580-byte
shell** with `<title>Open Government Data (OGD) Platform India</title>`. No dataset title,
no resource id and no licence field is server-rendered. `WebFetch` of `/search` returned
**HTTP 403**. There is no way, without executing JavaScript or presenting an API key, to
read the metadata field the task requires.

That is consistent with the earlier pass's finding on the AISHE catalogue. Under the
standing rule — a resource that merely sits on data.gov.in is not enough — the verdict is
unchanged.

**Verdict: NEEDS_REVIEW.** This lane is not exhausted; it is blocked by tooling, not by
the absence of a licence. It needs one human browser session, not more bot passes.

### N-06 Telangana Open Data Portal — no evidence obtainable

`https://data.telangana.gov.in/` returns a 2,455-byte shell whose entire body is
"You need to enable JavaScript to run this app." No licence string appears in the HTML.
The standard CKAN discovery endpoint
(`/api/3/action/package_search?q=college`) returns **404**, so it is not a stock CKAN
portal and there is no documented API to query. Kerala and Odisha portals were
unreachable (DNS).

**Verdict: UNVERIFIED — dropped.** No licence evidence, no dataset evidence.

### N-07 Placement statistics — nothing new qualifies

Ten GitHub repository searches (`placement data`, `placement report`, `campus placement
dataset`, `placement india license:mit`, `placement statistics india`, …) surfaced only:

- Kaggle-derived academic CSVs of individual student records (no licence, and personal
  data at row level);
- explicitly synthetic sets (e.g. a 50,000-row "logically connected" student file) —
  fabricated, therefore worthless as published statistics;
- single-college student projects with no licence and no stated source year;
- the previously screened `anxkhn/placement-data-2025` (GPL-3.0 with the author
  disclaiming ownership — already RESEARCH_ONLY).

**Zero** new datasets met both conditions: an explicit licence **and** a stated source
year for the statistics.

**Verdict: NONE FOUND.** Company/recruiter directories fared no better — every hit was
either a scrape (AmbitionBox, IndiaMART) or a stock-ticker list, neither of which is a
placement-cell recruiter directory.

---

## 3. What would have to be true for any of these to be importable

1. **AICTE-derived sets (N-01, and by extension SRC-001).** AICTE must publish an explicit
   reuse licence, or grant written consent, or the same fields must be obtained from a
   data.gov.in resource published by AICTE/MoE whose rendered metadata shows a named
   licence. An MIT/Apache grant from a mirror uploader satisfies none of these. Until
   then the only lawful use of these files is internal reconciliation against a licensed
   source — not shipping the rows.

2. **Wikidata (N-04).** No rights precondition remains; the conditions are all fitness
   conditions: (a) map the type taxonomy and restrict to `P17=Q668` plus the agreed
   `P31` set; (b) deduplicate on QID and collapse multi-valued `P131`/`P856`; (c) measure
   coverage against ~200 known AICTE colleges before committing — expected gap is large
   for polytechnics; (d) treat every field as a suggestion that must be confirmed against
   the institution's own site, because the community does not enforce freshness.

3. **data.gov.in (N-05).** A named resource id must be observed, in a browser, showing an
   explicit licence line ("License: GODL-India" or equivalent) in its rendered metadata.
   Then: capture the provider, year, dataset name, repository, retrieval date and link in
   the attribution string GODL requires, and re-check the resource's own exclusions
   (personal data, restricted datasets) before import.

4. **Placements (N-07).** The publisher must be the college/placement cell itself (with a
   licence and a stated year), or an aggregator that grants redistribution. No such
   publisher was found. Any future candidate needs: named publisher, explicit licence,
   stated reporting year, and company-level or aggregate figures — never student-level
   rows.

5. **Standing rule for all of the above.** "Repo is MIT" is not "data may be
   redistributed". Three of the six candidates opened here failed on exactly that
   distinction, and only one (Wikidata) passed the licence-authority test.

---

## 4. Recommendation

**None.** No new source found in this pass is approved for import.

The single best-structured Indian college file encountered (N-01, 13,089 institutions with
AICTE ids and nested programmes) is an AICTE database dump under a wrapper's MIT licence
and inherits the same upstream defect that already demoted `SRC-001`. Recommending it
would simply re-open a settled question.

If a pilot is needed to exercise the import pipeline rather than to ship data, the only
defensible one is **Wikidata CC0 (N-04), restricted to name / city / state / official
website** — a supplementary seed list, explicitly *not* a placement dataset and not a
replacement for an AICTE directory. That is a pipeline test, not a data acquisition.

The highest-value next action is not another repository sweep. It is one human browser
session on data.gov.in to read the per-resource licence field on AICTE/MoE-published
resources — the one route where a government licensor, not a scraper, would be granting
the rights.
