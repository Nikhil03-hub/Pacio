# Wikidata Feasibility for a Pacio Institution Directory

Research date: **2026-10-24** (queries run approximately 16:30–17:35 UTC; 22:00–23:05 IST).
Scope: a bounded slice of Wikidata covering higher-education institutions located in India.
Artifacts: this report plus `docs/data/wikidata_institutions_sample.json` (raw sample + query metadata).

Nothing was imported, no database or code was touched, and no Wikidata dump was downloaded.
Only the SPARQL endpoint and the MediaWiki API were called, with an identifying User-Agent
(`PacioWikidataFeasibility/1.0 (research; contact data@pacio.example)`).

Evidence labels used throughout:

| Label | Meaning |
| --- | --- |
| VERIFIED | The exact text or number was obtained from the cited primary source on 2026-10-24 |
| PARTIAL | Source reached, but the claim depends on a derived step, a heuristic, or a small sample |
| NOT RUN | Not measured in this pass — no number is asserted |

---

## 1. Licence evidence

### 1.1 The data is CC0

**VERIFIED.** Primary page `https://www.wikidata.org/wiki/Wikidata:Licensing`, retrieved
2026-10-24, HTTP 200. Exact sentence:

> "All structured data (i.e. the main, Property, Lexeme, and EntitySchema namespaces) is
> released into the public domain under [Creative Commons Zero]."

**VERIFIED.** Official policy page `https://www.wikidata.org/wiki/Wikidata:Copyright`,
retrieved 2026-10-24. Exact sentence:

> "All structured data from the main, Property, Lexeme, and EntitySchema namespaces is
> available under the Creative Commons CC0 License; text in the other namespaces is
> available under the Creative Commons Attribution-ShareAlike License; additional terms
> may apply. By using this site, you agree to the Terms of Use and Privacy Policy."

**VERIFIED.** Data-access page `https://www.wikidata.org/wiki/Wikidata:Data_access`,
retrieved 2026-10-24. Exact sentences:

> "Wikidata offers a wide range of general data about everything under the sun. All that
> data is licensed CC0, "No rights reserved", for the public domain."

This is the page that governs programmatic access (including the Query Service described
later on the same page), so the CC0 statement covers **access via SPARQL**, not only
bulk dumps.

### 1.2 CC0 applies to the data, not the software

**VERIFIED.** The Licensing page scopes CC0 explicitly to "the main, Property, Lexeme, and
EntitySchema namespaces" — i.e. the statements returned by a SPARQL query. Two things sit
outside that scope:

- **Software.** Wikibase (the engine behind Wikidata and the Query Service) is distributed
  under the GNU GPL v2: `https://raw.githubusercontent.com/wikimedia/mediawiki-extensions-Wikibase/master/COPYING`
  contains the "GNU GENERAL PUBLIC LICENSE Version 2, June 1991" (retrieved 2026-10-24).
  Pacio is not linking or redistributing Wikibase, so this does not affect the import.
- **Prose pages.** Wikidata help/description pages are CC BY-SA, not CC0. Only the
  structured statements are public domain.

*Minor inconsistency noted:* `Wikidata:Licensing` says "Creative Commons
Attribution-ShareAlike 4.0" for other namespaces while `Wikidata:Copyright` still links the
3.0 text. Irrelevant to Pacio, which uses no prose.

### 1.3 What Wikimedia asks for even though CC0 does not require it

**VERIFIED.** `Wikidata:Data_access`, section on using the data:

> "We offer the data in Wikidata freely and with no requirement for attribution under
> CC-0. In return, we would greatly appreciate it if, in your project, you mention
> Wikidata as the origin of your data. In so doing you help ensure that Wikidata will
> stay around for a long time to provide up-to-date and high-quality data."

The same page offers acceptable wordings: "Powered by Wikidata", "Data from Wikidata",
"Source: Wikidata", "Including data from Wikidata". **Recommendation:** use
"Source: Wikidata (CC0)" with a link on every institution record and in the directory
footer. It costs nothing and matches the request exactly.

The page also sets access expectations, all of which were followed: send a descriptive
User-Agent, do not make many concurrent requests, respect HTTP 429 and stop on it, and
set the lowest sensible query timeout.

### 1.4 Residual legal risk — flag, not proven

**PARTIAL.** CC0 is granted by Wikidata contributors over *their contributions*. It cannot
by itself cure a rights claim held by an upstream compiler. This matters here because
**79.3% of the sample carries an AISHE code (P6392)**, which strongly suggests a bulk
import from the AISHE directory rather than piecemeal manual entry. No statement-level
provenance audit was run (**NOT RUN**), so the origin of those rows is unknown.

Practical reading: factual directory fields (name, city, website) are generally not
copyrightable, and Wikidata's position is that data is not eligible for copyright. But if
Pacio later ships a directory that is materially AISHE-derived, the safest course is a
short counsel review of this specific question before commercial launch. This does not
block a demo.

**Licence verdict: CC0 for the structured data — cleanest licence available to Pacio.
Attribution requested but not required. One narrow, auditable residual risk around AISHE
provenance.**

---

## 2. Coverage

### 2.1 Definition used

Population = items with `P17 (country) = Q668 (India)` that are `P31/P279*` one of the four
target classes. `P279*` is the transitive subclass path, which is what "instances of / subclasses
of" requires — and, as section 4 shows, is also where the data quality problem lives.

### 2.2 Class identification

**VERIFIED.** Class items were looked up rather than assumed:

- `Q3918` = university, "an institution of tertiary education and research which awards academic degrees in several academic disciplines"
- `Q189004` = college, "educational institution, varying in level from country to country"
- `Q1663017` = engineering school, "educational institution for the study of engineering"
- `Q1371037` = university of technology, "college or university for applied sciences"

Two negative findings:

- **There is no usable Wikidata class called "engineering college".** A search for the exact
  label returns only two Kerala electoral wards (`Q101186675`, `Q101197033`, both
  `P31 = ward`) and `Q17015796`, a defunct English schools programme with no `P31`. None
  models an institution. `Q1663017` (engineering school) is the nearest equivalent; it is
  used here and named as such, not silently re-labelled.
- **`Q11076398` "Institute of technology" is not usable as a class.** It has no `P31`, and
  its `P17` is Taiwan — it behaves like a specific institution, so including it would have
  injected a non-Indian entity into the population. Excluded.

### 2.3 Counts

**VERIFIED.** All counts run 2026-10-24 against `https://query.wikidata.org/sparql`.

| Target class | QID | Indian institutions |
| --- | --- | ---: |
| university | Q3918 | 2,128 |
| college | Q189004 | 26,234 |
| engineering school | Q1663017 | 1,403 |
| university of technology | Q1371037 | 168 |
| **Union, de-duplicated** | — | **29,509** |

Overlap: 406 items sit in more than one class (388 in exactly two, 18 in three). The naive
sum (29,933) therefore overstates the total by 424; only the union figure should be quoted.

The union query itself **failed twice** — see section 6 — so the union was computed from
four per-class QID listings rather than a single `COUNT`.

**P17 filter check (VERIFIED):** institutions reachable as "located in India" via `P131`
but missing `P17` were counted per class: university 1, college 1, engineering school 0,
university of technology 0. The `P17` filter therefore loses **2 items out of 29,509** —
negligible, and the counts above can be treated as complete for this definition.

### 2.4 What the counts mean, and what they do not

`college` at 26,234 is not 26,234 colleges. Section 4.2 documents a subclass error that
puts every Indian girls' school inside that number (2,449 items). Corrected college count:
**23,785** (derived, VERIFIED components).

Against reality: India has roughly 45,000+ colleges and ~3,000 AICTE-approved engineering
institutions (*external context, not measured in this pass*). Wikidata's 1,403 engineering
schools therefore capture a minority of the sector, and the 29,509 total is a partial,
unevenly built subset — not a registry.

---

## 3. Sample and field completeness

**VERIFIED.** 300 items drawn from the 29,509 union. Sampling was deterministic
pseudo-random: each QID was MD5-hashed and the list sorted by hex digest; the first 300
were taken. This is reproducible and uncorrelated with item quality — no "best of" selection.

Field extraction used the MediaWiki `wbgetentities` API (labels + claims), with deprecated
ranks dropped, followed by a level-by-level walk of `P131` to resolve the state name.
The aggregated SPARQL variant was abandoned after it timed out (section 6).

| Field | Wikidata property | Present | % | 95% CI (Wald) |
| --- | --- | ---: | ---: | --- |
| English label | rdfs:label @en | 300 | **100.0%** | — |
| Country | P17 | 300 | 100.0% | — |
| Located in admin unit (city/district) | P131 | 284 | **94.7%** | 92.2–97.2 |
| State (derived from P131 chain) | — | 277 | **92.3%** | 89.3–95.3 |
| Affiliation | P1416 | 240 | 80.0% | 75.5–84.5 |
| English description | schema:description | 239 | 79.7% | 75.2–84.2 |
| AISHE code | P6392 | 238 | **79.3%** | 74.8–83.9 |
| Inception | P571 | 219 | 73.0% | 68.1–77.9 |
| Official website | P856 | 174 | **58.0%** | 52.4–63.6 |
| Coordinate location | P625 | 87 | 29.0% | 23.9–34.1 |
| Street address | P6375 | 2 | 0.7% | — |
| AICTE Permanent ID | P6513 | 3 | 1.0% | — |
| AICTE application ID | P4897 | 3 | 1.0% | — |
| Official language | P37 | 0 | 0.0% | — |
| Political ideology | P1142 | 0 | 0.0% | — |

The four fields that matter most for a directory: **name 100%, state 92.3%, AISHE code
79.3%, website 58.0%.** Name and location are strong; the website is the weak link, and
section 5 shows that even the 58% is optimistic because many URLs are dead.

**Property correction — the brief contained an error.** The task described `P1142` as
affiliation. It is not. **P1142 is "political ideology"** (verified via the entity API:
"political ideology of an organization or person or of a work"). Affiliation is **P1416**
("organization that a person or organization is affiliated with"). Both were queried:
P1142 returned 0/300, P1416 returned 240/300. Any importer mapping P1142 → affiliation
would produce an empty column.

Other completeness notes:
- 126 of 300 (42.0%) have no website at all.
- 6 items list more than one P856 URL.
- 61 of 300 (20.3%) have no English description, which weakens keyword search.
- AISHE codes appear in the standard `C-39889` form and look structurally valid (not
  validated against the AISHE registry — **NOT RUN**).

---

## 4. Data quality

### 4.1 Duplicates — very low in the sample

**VERIFIED** on 300 records:

| Check | Result |
| --- | --- |
| Distinct website domains | 178 from 174 items |
| Domains shared by 2+ items | 2 groups, of which **1 genuine** duplicate pair |
| Same label + same city | 0 groups |

The genuine duplicate: `indoasianacademy.com` is listed for both `Q84800464` and
`Q84014390`. The second "collision" was one item (`Q7585630`) listing the same domain twice
with different schemes — a within-record duplicate, not a duplicate institution.

At 1 pair per 300, the sample duplicate rate is ~0.33%. Deduplication is cheap and still
necessary at full scale, but it is not the main problem.

### 4.2 Wrong entries — a real, explainable defect

**VERIFIED.** 28 of 300 records (**9.3%**) are K-12 schools, not higher-education
institutions. Examples:

- Q75182161 "Nabadwip Bakultala Balika Vidyalaya" — girls' school, higher secondary school
- Q73786360 "Boral Rr Girls High School" — girls' school, higher secondary school
- Q67465342 "Banga Balika Primary School" — girls' school, primary school
- Q75479866 "Milki Girls Jr High School" — upper primary school

Root cause, traced with SPARQL and **VERIFIED**:

> `Q22713629` ("girls' school") carries `P279` (subclass of) `Q189004` ("college").

That single edge pulls every Indian girls' school into the `college` subclass closure.
There are **2,449** Indian items with `P31 = girls' school`, and all of them necessarily sit
inside the 26,234 college count. This is a Wikidata modelling error, not a Pacio query
error — but a naive `P279*` import inherits it wholesale. None of the 28 had a website or an
AISHE code, so a "must have website or AISHE" rule removes them incidentally; relying on
that would be luck, not design.

Other confirmed type errors in the sample:

| QID | Label | Typed as | Actually |
| --- | --- | --- | --- |
| Q4860850 | Barjora College | university | a college (and its domain is now a betting site) |
| Q5248849 | Deccan College of Medical Sciences | open-access publisher | a medical college |

The problem is not confined to one item. Of the 20 sampled items typed `university`, **9 are
named "College" or "Institute"**, and at least 6 are plainly colleges — Barjora College,
St. Xavier's College Simdega, Ponjesly College of Engineering, Government Medical College
Kathua, NDMVP's College of Engineering, Index Medical College. (Two of the nine are
legitimate: IIIT Jabalpur is an Institute of National Importance and St. Peter's is a deemed
university.) Roughly a third of the `university` label in this slice is wrong.

Of the 300, only **14 (4.7%)** carry an explicitly engineering type
(`engineering school` / `university of technology`). Thirty-three (11.0%) mention
engineering, technology, polytechnic or technical in the label. The sample is dominated by
arts, commerce, education, nursing and law colleges — which is the true shape of Indian
higher education, but the opposite of what a placement-cell directory wants.

### 4.3 Distribution by state — skewed, and not in a way that reflects reality

**PARTIAL** (state derived by walking P131; 23 of 300 could not be resolved: 16 have no
P131 at all, 4 dead-end at "British Raj", 3 stop at "India" without naming a state). Chain
depth ranges from 0 to 5 hops, so deriving a state is not a mechanical one-step join.

| State | Items | Share |
| --- | ---: | ---: |
| Uttar Pradesh | 56 | 18.7% |
| Karnataka | 46 | 15.3% |
| Rajasthan | 34 | 11.3% |
| West Bengal | 29 | 9.7% |
| Andhra Pradesh | 20 | 6.7% |
| Madhya Pradesh | 18 | 6.0% |
| Maharashtra | 18 | 6.0% |
| Kerala | 16 | 5.3% |
| Gujarat | 9 | 3.0% |
| Haryana | 8 | 2.7% |
| Odisha | 7 | 2.3% |
| Tamil Nadu | 5 | 1.7% |
| Bihar, Nagaland | 2 each | 0.7% each |
| Goa, Punjab, Himachal Pradesh, Arunachal Pradesh, Delhi, Chhattisgarh, Jharkhand | 1 each | 0.3% each |
| Unresolved | 23 | 7.7% |

Maharashtra and Tamil Nadu — two of India's largest higher-education markets — are badly
under-represented, while Uttar Pradesh, Karnataka and Rajasthan are over-represented. The
pattern looks like the footprint of specific bulk-import campaigns (many rows share an
AISHE-style code and a terse "X College, Y" label), not a sample of the sector. A placement
cell in Chennai or Pune would immediately notice that well-known local colleges are absent.

---

## 5. Spot-check accuracy

Eight institutions were drawn at random with a fixed seed (20261024) from the 174 sampled
items that have a P856 URL — items without a website cannot be checked this way, so the
frame is stated rather than hidden. No item was swapped after inspection.

Method: fetch P856 (browser User-Agent, 25s timeout, follow redirects, retry https), compare
the landing page's title/footer text against the Wikidata name, the P131 city, the derived
state, and the P31 type. A site that would not load is recorded as UNKNOWN, not as a pass.

| # | QID | Wikidata label | P856 | What the site showed | Name | City/State | Type | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Q19458634 | Government Engineering College, Dahod | gecdahod.ac.in | HTTP 200; title "Government Engineering College Dahod"; Dahod, Gujarat, GTU, NBA, civil/mechanical | match | match | match | **PASS** |
| 2 | Q4860850 | Barjora College | barjoracollege.org | HTTP 200; title "Best Betting Apps in India (2026): IPL Live Scores" — domain hijacked | no | n/a | no | **FAIL** |
| 3 | Q91094481 | Jiet College of Nursing | jietjodhpur.ac.in | HTTP 200; "JIET Universe Jodhpur – Engineering, Medical, Management & Design College"; Jodhpur appears, nursing not identified as a distinct college | partial | match | partial | **PARTIAL** |
| 4 | Q84998745 | MQI Degree College | qidc.in | HTTP 530 (Cloudflare origin error) on both apex and www | — | — | — | **UNKNOWN** |
| 5 | Q91616360 | Ajitgarh College, Sikar | ajeetgarhpgcollege.in | DNS NXDOMAIN (apex and www) | — | — | — | **UNKNOWN** |
| 6 | Q88548534 | Dodhiwala Arts and Commerce College, Thangadh | dodhiwalacollege.webs.com | DNS NXDOMAIN; the host is a free website builder that no longer resolves | — | — | — | **UNKNOWN** |
| 7 | Q92178405 | Sri Venkateswara Institue of Technology and Sciences, Y.S.R. | svistkadapa.org | DNS NXDOMAIN (apex and www) | — | — | — | **UNKNOWN** |
| 8 | Q87421803 | S.P.B. Patel Engineering College (saffrony) | saffrony.ac.in | HTTP 200; footer "© 2026 S. P. B. Patel Engineering College (Saffrony)"; "District: Mehsana – 384435"; GTU | match | match | match | **PASS** |

**Score: 2 clean PASS out of 8 (25%).** One PARTIAL, one outright FAIL, four UNKNOWN.

Read honestly, this is worse than 2/8 for operational purposes:

- Of the four sites that loaded, **two confirmed the record, one was ambiguous, and one was
  a hijacked domain serving gambling content**. P856 is not merely incomplete — when it is
  wrong, it can be actively harmful to link.
- The four UNKNOWNs are link failures, not proven record errors. The institutions may be
  perfectly real; the URL simply no longer resolves. But from a user's point of view a dead
  "Website" button is a failure, and Pacio cannot distinguish the two cases without a
  liveness check.
- The sample includes no famous institution — none of the eight is an IIT, NIT or major
  university (the wider 300 does contain one IIIT) — so this is a fair picture of the long
  tail, which is exactly what a 500-row import would contain.

---

## 6. Endpoint behaviour (reported, not worked around silently)

The Query Service is rate-limited and kills long queries at roughly 60 seconds. Three query
shapes failed, and their exact errors are recorded here rather than replaced with guesses:

| Attempt | Result |
| --- | --- |
| Class inventory: all Indian items with `P31` under `educational institution`, grouped | `HTTP 504` — body `upstream request timeout`, 69.8s |
| Union count across 4 classes via `VALUES` + `P279*` | `HTTP 504` — body `upstream request timeout`, 67.9s |
| Aggregated detail query (14 `GROUP_CONCAT`s, label service) for 5 items | `HTTP 504` — body `upstream request timeout`, 70.3s |

Working substitutions, all successful: per-class `COUNT` queries (3–6s each), per-class
`SELECT DISTINCT ?item` listings (4–6s, the college listing returns 26,234 rows / 3.1 MB),
and field extraction via the MediaWiki API in batches of 50. Total load: ~22 SPARQL
queries and ~20 batched API calls over about 55 minutes, spaced ≥1.2s apart. No 429 was
received.

The aggressive-then-back-off pattern is itself a finding: a production importer should
expect to chunk by class and by QID list, not to run one large query.

---

## 7. Verdict

**GO — but only as a bounded, explicitly labelled demo slice. NO-GO as an authoritative
or complete institution directory, and NO-GO as a basis for outbound contact.**

The licence is the best Pacio will find: CC0, no attribution obligation, verified from
primary Wikimedia pages. The identity and geography data are good — 100% names, 92% states,
95% cities. AISHE codes at 79% give a credible join key to the official registry later.

The data is **noisy in three specific, measurable ways**, none of which is fatal if handled:

1. **9.3% are K-12 schools** admitted through one bad subclass edge.
2. **Roughly half of the P856 URLs are dead or hijacked** (4 of 8 checked).
3. **State coverage is skewed** toward a few import campaigns, so the directory will look
   incomplete to placement cells in under-represented states.

It is not "too noisy to use". It is too noisy to use *unfiltered and unlabelled*.

### 7.1 What must be filtered out before any row reaches a screen

| Filter | Rule | Removes |
| --- | --- | --- |
| K-12 contamination | exclude any item whose P31 set includes `girls' school`, `primary school`, `secondary school`, `higher secondary school`, `upper primary school`, `urban school`, `rural school` | ~9.3% |
| Label sanity | exclude labels matching `high school`, `higher secondary`, `primary school`, `vidyalaya`, `public school`, `convent` | ~4.7% |
| Non-institution types | exclude `open-access publisher`, person, company, disambiguation | small |
| Identifier floor | require at least one of P856 or P6392 | 41 rows (13.7%) |
| Link health | HTTP-check every P856 at import; drop 4xx/5xx/NXDOMAIN or park the URL as "unverified" | ~50% of URLs |
| Scope | keep only engineering-relevant rows for the placement-cell use case: P31 `engineering school`/`university of technology`, or label matches `engineering|technology|polytechnic|technical`, or an AICTE ID (P6513/P4897) is present | ~89% |

The percentages overlap (a K-12 school also fails scope) and must not be summed. Applied
together to the 300-row sample they leave a few dozen plausible rows.

### 7.2 What must be de-duplicated

Priority order, cheapest first:

1. **AISHE code (P6392), exact.** Primary key where present (79%). Two rows with the same
   code are the same institution.
2. **Registrable website domain.** Normalise scheme, `www`, trailing slash, path. Catches
   the `indoasianacademy.com` pair and group-site duplicates.
3. **Fuzzy label + city.** Token-set ratio ≥ 0.90 on the label, same P131. Needed for the
   21% without AISHE codes and for spelling variants ("Institue" already appears).

Observed duplicate rate is ~0.33%, so this is a cheap safeguard rather than a project.

### 7.3 What could mislead a placement cell

1. **A school in a college directory.** "Banga Balika Primary School" listed beside degree
   colleges destroys trust in one screenful.
2. **Hijacked links.** The Barjora College domain now serves betting-app spam. A placement
   portal that sends students there owns the reputational damage. Never render an
   unverified P856 as a plain outbound link.
3. **Implied approval.** Only 1% of rows carry an AICTE identifier. A row's presence must
   never be read as AICTE approval, UGC recognition or NAAC accreditation — Pacio has none
   of those facts. The UI needs an explicit "not an accreditation list" disclaimer.
4. **Stale affiliation.** P1416 is 80% populated but reflects whichever university the
   contributor recorded; affiliations change, and autonomous colleges may show a parent
   that no longer applies.
5. **False precision.** P571 is usually year-only (`+2003-01-01T00:00:00Z`). Render "est.
   2003", never "1 January 2003".
6. **Item-level type errors.** A college typed `university`, a medical college typed
   `open-access publisher`. Do not surface the raw P31 label to users.
7. **Skew read as national coverage.** A directory that is 19% Uttar Pradesh and 1.7% Tamil
   Nadu will be read as "Pacio only covers the north". Label it as a sample.

### 7.4 Recommended first import

- **Row cap: 500.** Rationale: engineering-relevant rows are ~11% of 29,509 (~3,250, 95% CI
  ~2,200–4,300), and rows that are engineering-named *and* have both an AISHE code and a
  website are only ~5.3% (~1,570). 500 sits comfortably inside the usable pool, survives a
  ~20% rejection rate during manual review, and is small enough to review 100% of rows by
  hand before the demo. Do not paginate past the cap in v1.
- **Hard filters:** section 7.1, applied in the importer, not in the UI.
- **Keep exactly these fields:**

  | Field | Source | Display rule |
  | --- | --- | --- |
  | `wikidata_qid` | item ID | internal key + deep link |
  | `name` | label @en | as-is, but strip trailing ", <city>" if city is shown separately |
  | `city` | P131 label | as-is |
  | `state` | derived P131 chain | required; drop row if unresolved |
  | `website` | P856 | show only with `link_status = verified`; otherwise omit the button |
  | `aishe_code` | P6392 | show as "AISHE code" — a join key, not a badge of approval |
  | `aicte_id` | P6513 / P4897 | show only when present (1%) |
  | `affiliation` | P1416 label | "Affiliated to …" with an "as recorded on Wikidata" caveat |
  | `established_year` | P571, year only | "est. YYYY" |
  | `source` | constant | "Source: Wikidata (CC0)" + link |

- **Drop entirely:** P6375 street address (0.7%), P37 official language (0%), P1142
  (wrong property), `admin_parent` (internal derivation), raw P31 labels, full precision
  dates and coordinates unless a map is actually built.
- **Labelling:** the directory page must say, in plain words, that it is a *sample of
  publicly documented institutions drawn from Wikidata*, that it is not an accreditation
  or approval list, and that details may be out of date. A "report an error" link is
  mandatory — the data will contain errors, and the correction path is part of the licence
  hygiene as much as the product.

### 7.5 If Pacio later wants full coverage

Wikidata will not get there. The 1,403 engineering schools against ~3,000 AICTE-approved
institutions (external reference), plus the state skew, mean the ceiling is roughly a third
of the sector. The route to a real directory is a licensed feed (AICTE/UGC with written
permission) or institution-supplied data — Wikidata is a demo seed and a join key, not the
destination.

---

## 8. What was not run

| Item | Status |
| --- | --- |
| Full Wikidata dump download | **NOT RUN** (explicitly avoided) |
| Statement-level provenance / revision history for AISHE-coded rows | **NOT RUN** |
| Validation of AISHE codes against the AISHE registry | **NOT RUN** |
| Website liveness across all 174 URLs (only 8 checked) | **NOT RUN** |
| Duplicate scan across all 29,509 items (sample only) | **NOT RUN** |
| UGC identifier property | **NOT RUN** — no such Wikidata property was found in a property search |
| Union as a single SPARQL `COUNT` | **NOT RUN** — HTTP 504 (section 6). The 29,509 in section 2.3 is the size of the de-duplicated QID set built from four per-class listings, not the output of one query |
| Coordinates/geo sanity check (e.g. points outside India) | **NOT RUN** |

## 9. Reproduction

All queries are recorded in the metadata block of
`docs/data/wikidata_institutions_sample.json`, including the exact per-class query, the
sampling method, the field map, and the licence quotes. The 300 selected QIDs can be
regenerated by hashing the union QIDs with MD5 and taking the first 300 in hex order.
