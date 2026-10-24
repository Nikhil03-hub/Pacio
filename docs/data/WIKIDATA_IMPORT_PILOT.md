# Wikidata Institution Import — Pilot Report

Phase 3, Workstream D. Run 2026-10-24 against a disposable MongoDB database.

```
.venv/Scripts/python.exe scripts/wikidata_institution_pilot.py \
  --mongo-url mongodb://127.0.0.1:27017 --db-name pacio_dryrun_wikidata --check-links
```

Exit 0. Database `pacio_dryrun_wikidata` dropped afterwards (`cleanup: dropped`). The application
database was not touched.

## Why this source

Wikidata's structured data is **CC0** — the only candidate in three research passes whose licence
grants commercial reuse without interpretation. `WIKIDATA_FEASIBILITY.md` measured the quality risk;
`PERMITTED_DATASET_SCAN.md` found no AICTE/AISHE/placement dataset with a licence Pacio can rely on.
So this is a rights-clean slice with a known fitness problem, not a big dataset with a rights problem.

## What actually happened

| Stage | Count | Notes |
|---|---|---|
| Rows in the bounded sample | 300 | generic "college in India" query, not engineering-targeted |
| Excluded: outside engineering/technical scope | 203 | law, education, arts, nursing, medical colleges |
| Excluded: K-12 school | 54 | Wikidata's subclass graph admits schools |
| Excluded: no website and no education identifier | 13 | unverifiable even in principle |
| Excluded: department, not an institution | 1 | "Department of Physical Oceanography" |
| Excluded: not an educational institution | 1 | — |
| **Kept after filters** | **28** | **9.3% yield** |
| Duplicates removed | 0 | sample had no repeats after filtering |
| Imported (batch 1) | 28 new | via the approved-source gate |
| Re-import (batch 2) | 0 new, 0 updated, **28 unchanged** | idempotent on real data |
| Rollback | 28 deleted, 0 restored | disposable store empty afterwards |

Quality of what survived: **19/28 carry an AISHE code**, 24 have a website, and the 28 span 9 states.
Every stored row is `data_status: "unverified"` with `trust_level: "community-maintained"`.

Link health (checked live, one request per site, 1.5 s apart):

| Website state | Rows |
|---|---|
| `ok` (HTTP 2xx/3xx) | 16 |
| `dns_or_connection` failure | 7 |
| `http_404` | 1 |
| no website recorded | 4 |

**57% of the websites resolve.** That matches the 2-of-8 spot-check in the feasibility report and is
the single most important number here: the name/city/state fields are usable, the URL field is not.

## What this proves

- The gated pipeline works end to end on **real third-party data**, not fixtures: approval gate →
  provenance → dry-run → import → idempotent re-import → rollback to zero.
- The filters that make the data honest are expressible in code and testable (`classify()` returns a
  reason per row, so every exclusion is auditable).
- CC0 data can be stored with `unverified` status and a `trust_level`, so nothing downstream has to
  guess where a row came from.

## What this does **not** prove

- **That Pacio has an institution directory.** 28 rows is a demo slice. The generic query yields 9%;
  a targeted SPARQL query for engineering institutions is needed before any larger import, and even
  then the URL health problem remains.
- **That every surviving row is correct.** Only 2 of 8 spot-checked institutions were fully
  confirmed against their own website; one P856 was a hijacked domain serving gambling content. A
  row must never be presented as verified because it passed these filters.
- **Placement data.** Wikidata has none. This is a name/city/state/type seed list.

## Rules that must hold if this slice is ever surfaced in the product

1. Label it "community-sourced (Wikidata, CC0), not confirmed with the institution" — never
   "verified" and never next to a partnership claim.
2. Show the website only when `website_status == "ok"`; otherwise hide it or show "link unverified".
3. Never imply an institution is a Pacio customer because it appears in the directory.
4. Keep the collection separate (`institutions_public`), never merged into the synthetic demo tenant.

## Next action (in this order)

1. Re-run the collector with an **engineering-targeted** query (P31 engineering school / university
   of technology / institute of technology in India, plus AICTE-id-bearing rows) and expect a much
   higher yield than 9%.
2. Keep the link health check as part of the importer, not a separate report.
3. Only after those two: consider surfacing the directory read-only in the TPO/institution views.

**Verdict: GO as a pipeline proof and a labelled demo slice. NO-GO as a shippable, authoritative
institution directory.**


---

## Round 2 — the targeted engineering query (2026-10-25)

Round 1 used a generic "college in India" sample and yielded 9.3%. The recommendation was to query
for engineering institutions specifically. That was done, and the difference is the whole point.

Query (SPARQL, `https://query.wikidata.org/sparql`, 2026-10-25) — `?item wdt:P31/wdt:P279* wd:Q1663017`
("engineering school") and `wdt:P17 wd:Q668`, with P856 / P131 / P571 / P6392 / P6513 / P4897 optional:

> **Total matching institutions: 1,403.** First page fetched: 300 rows.

| Metric | Round 1 (generic) | Round 2 (targeted) |
|---|---|---|
| Rows fetched | 300 | 300 |
| Passed the filters | 28 (9.3%) | **260 (87%)** |
| Duplicates collapsed | 0 | 67 (same QID across multi-valued rows) |
| **Distinct institutions imported** | 28 | **193** |
| With a website | 24 | 188 |
| Websites that resolved live | 16 (67%) | **139 (74%)** |
| With an AISHE code | 19 | 93 (48%) |
| States resolved | 9 | **0 — the query did not fetch the state chain** |
| Re-import | 28 unchanged | **193 unchanged** |
| Rollback | 28 deleted, 0 left | **193 deleted, 0 left**, disposable DB dropped |

Link failures were classified rather than hidden: 25 DNS/connection failures, 10 connection refused,
5 HTTP 403, 5 HTTP 404, 1 HTTP 500, 1 HTTP 523, 2 unreachable, 5 with no URL at all.

### What this changes

`WIKIDATA_IMPORT_PILOT.md` round 1 concluded "a pipeline proof, not a directory". Round 2 shows the
limitation was the **query**, not the source: 193 named engineering colleges with 74% live websites,
48% carrying an AISHE code that can later be joined to official records, from a pool of 1,403.

### What is still required before this is shown to a customer

1. **Resolve state.** The round-2 query omitted the administrative parent chain, so no row has a
   state. A placement cell filters by state, so this is a blocker for UI use, not a cosmetic gap.
2. **Paginate past 300** to cover the 1,403, keeping the same filters.
3. **Keep the liveness check in the importer** — 26% of URLs are already dead or erroring.
4. **Label every row** `unverified / community-maintained`, and show a website only when
   `website_status == "ok"`.
5. Do not imply a relationship: appearing in this list means Wikidata has an article, nothing more.

**Revised verdict: GO as a real, importable institution seed list (193 rows today, ~1,400 available).
Still NO-GO as an authoritative or complete directory until state resolution and pagination are done.**


---

## Round 3 — the state-resolved population, audited on a deterministic sample (2026-10-25)

Round 2's blocker was that no row carried a state. The query was extended with the administrative
parent chain (`wdt:P131/wdt:P131*` restricted to `wd:Q12443800`, "state of India") and re-run with a
1,500-row page.

### Population

| Measure | Value |
|---|---|
| Rows returned | 1,500 |
| Passed the filters | 1,283 |
| Excluded: no website and no identifier | 181 |
| Excluded: department, not an institution | 20 |
| Excluded: K-12 | 11 |
| Excluded: outside scope / non-institution | 5 |
| Duplicate rows collapsed | 262 |
| **Distinct institutions available** | **1,021 across 27 states** |

### Audit of a deterministic 250-row sample (qid-ordered, so it is reproducible)

| Measure | Value |
|---|---|
| Rows imported | 250 |
| States represented | 21 |
| With an AISHE code | 111 (44%) |
| With a website | 240 |
| **Websites that resolved** | **163 (68%)** |
| Dead or refused | 76 — 41 DNS, 14 connection refused, 10 HTTP 404, 3 HTTP 403, 3 HTTP 503, 3 unreachable, 1 each 500/522/530 |
| Re-import | 0 new, 0 updated, **250 unchanged** |
| Rollback | **250 deleted, 0 remaining**, disposable DB dropped |

### What this settles

The directory is real: **1,021 named Indian engineering colleges across 27 states**, one licence
(CC0), one provenance chain per row (QID + retrieval timestamp + `unverified` status), and an import
path that is idempotent and reversible on production-grade data rather than fixtures.

Roughly **one third of the website links are dead**, which is the honest headline number and the
reason the importer keeps `website_status` per row: the UI must show a link only when it is `ok`.

### Still required before a customer sees it

1. Paginate the remaining rows (1,403 counted, 1,021 usable) — the current page cap is 1,500.
2. Re-check links on a schedule, not once at import.
3. Join the 44% with AISHE codes against the official registry to catch renamed or closed colleges.
4. The `unverified / community-maintained` label in the UI, and no implication of a relationship.

**Round 3 verdict: the slice is genuinely useful as a labelled seed directory. It is still not a
placement dataset, and it does not clear any institution to be shown as a Pacio customer.**
