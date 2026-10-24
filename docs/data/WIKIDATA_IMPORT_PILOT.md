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
