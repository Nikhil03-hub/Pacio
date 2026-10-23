# Data Quality Report

Two different things are measured here: the integrity of the **existing local database**,
and the quality of **candidate external sources**. No external dataset has been imported, so
external validation rates are marked NOT RUN rather than estimated.

## 1. Existing database integrity (local `pacio_dev_verify`) — VERIFIED

| Check | Result |
| --- | --- |
| Collections / documents | 41 / 597,821 |
| Backup integrity | gzip OK, parsed 41 headers and 597,821 documents |
| Restore integrity | restored into a separate DB; every collection count matched; API ran on it |
| DSA catalogue | 108 questions, 12 topics, version `2026.10-pattern-v1` |
| DSA topic progress | 61,200 rows |
| DSA question progress | 345,796 rows |
| Orphan progress (student_id not in `students`) | **0** |
| Demo student | 27 attempted / 9 solved |
| Leaderboard | resolves to existing student names |
| Restart duplication | none (identical counts before/after) |
| Duplicate email index | unique, present |
| Reset-token / rate-limit TTLs | present |
| Resume token index | partial unique (string tokens only) |

Residual data-quality issues in the **seed** itself:

- Real institution names are paired with invented MOUs, payouts and outcomes. Labelled
  synthetic in `DATA_PROVENANCE.csv`; must not be shown as genuine (BL-27).
- KMIT year-by-year tuples are not sourced. Only aggregates are published by the college.
- 5,450 synthetic student profiles; no real student data is imported (deliberate).
- DSA prompts are original but untestable (0/108 with examples or tests) — see
  `DSA_COVERAGE_AND_VALIDATION.md`.

## 2. Candidate sources — what was actually inspected

| Source | Records | Quality findings | External validation |
| --- | --- | --- | --- |
| AICTE institution mirror (`Ash310u`) | 39,268 institutions | Clean identifier field (`aicte_id`), district/type present; **no NAAC, no affiliation**; includes polytechnics; upstream terms unverified | Structure VERIFIED; duplication and field-completeness rates **NOT RUN** (not imported) |
| `placement-data-2025` | 779 placements + 293 internships | 609 distinct companies; **217 blank Role**; name variants (e.g. misspellings); **no college, year or selects**; author disclaims validation; GPL-3.0 | Sample VERIFIED; duplicate rate and accuracy **NOT RUN**; unsuited as shipped data |
| Kaggle “India colleges” | 1,203 colleges | Implausible values (same average package across different IITs); no stated source | **REJECTED on accuracy grounds** |
| Kaggle campus recruitment | 215 | Pseudonymous individual records; academic survey | **REJECTED on privacy/relevance** |
| Kaggle internships (Internshala scrape) | 8,483 | Uploader cannot license the source listings | **REJECTED on rights** |
| Kaggle tech jobs (synthetic) | 5,000 | Calibrated simulation | Demo fixtures only |
| Lever / Ashby / Greenhouse boards | Board-dependent (CRED 8, Atlan 6) | Required fields present: id, title, company, location, canonical URL, timestamps | Endpoint VERIFIED; schema VERIFIED; freshness/duplicate behaviour **NOT RUN** at scale |
| Adzuna | 500k+ India ads claimed | Cannot test without a key | **BLOCKED** |
| Jooble | n/a | Docs 403 to bots; 500 requests per key lifetime | **BLOCKED/PARTIAL** |
| NIRF / AISHE / data.gov.in | n/a | Automated access blocked (403/503) | **BLOCKED** |

## 3. Quality gates for any future import

A record may enter the product only if:

1. **Provenance** — `source_id`, canonical `source_url`, `retrieved_at`; `published_on` for
   statistics; `definition` for any metric.
2. **Stable key** — official identifier (`aicte_id`), ATS `dedupe_key`, or
   `(institution_id, academic_year, metric)`; no random IDs for existing entities.
3. **No PII** — no student names, emails, phone numbers or contact data in public
   collections.
4. **Duplicate policy** — exact-key duplicates are impossible (unique index); cross-source
   duplicates resolved by preferring the authoritative source (employer ATS > aggregator;
   official directory > mirror).
5. **Metric semantics** — offers ≠ unique students; median ≠ highest package; never mix.
6. **Freshness** — jobs expire after two missed polls or 72 h; placement statistics carry
   the academic year and publication date; stale sources are disabled.
7. **Labelling** — `data_status` in every document and a visible badge in the UI.
8. **Rollback** — every import batch has an ID, a dry-run diff and a pre-import backup.

## 4. Known quality risks if ignored

- **False authority:** importing the Kaggle college list would inject wrong fees/packages
  into dashboards and benchmarks.
- **Silent partnership claims:** an institution in a directory is not a customer; mixing
  the two is the highest reputational risk in this product.
- **Metric conflation:** “highest package” headlines and “offers vs students” confusion are
  common in Indian placement reporting; the product must store definitions, not just values.
- **Stale jobs:** a job board without expiry logic shows closed roles and destroys trust.

Status: existing DB integrity **VERIFIED**; external dataset quality beyond sampled files
**NOT RUN** by design (research phase, no imports).
