# data.gov.in Licence — Browser Verification (GODL-India)

Recorded 2026-10-24 by the lead agent, using a real Chromium session (Playwright) on the live portal,
because two automated passes had failed to read a per-resource licence field and concluded
"NEEDS_REVIEW". **Those passes were looking in the wrong place: the licence is declared portal-wide
in the footer, not in per-resource metadata.**

## What was observed (VERIFIED)

On `https://www.data.gov.in/resource/year-wise-aicte-approved-government-engineering-institutes-ug-pg-2019-20-2021-22`
and again on `https://www.data.gov.in/resource/institute-wise-details-higher-educational-institutions-heis-numbers-registered-and`,
the rendered footer reads:

> "Content is owned by the respective Ministries/Departments/Organizations and licensed under the
> **Government Open Data License-India**. © 2012-2015 GOVERNMENT OF INDIA All rights reserved except
> published datasets/resources and metadata."

Resource metadata observed on the AISHE resource: **Published On 26/07/2023**, *Updated On 26/07/2023*,
catalog *"Answers Data of Rajya Sabha Questions for Session 259"*, **file size 321 bytes**, granularity
Quarterly, reference URL pointing at `sansad.in` (a parliamentary question, not a survey extract).

## What this changes

| Before | After |
|---|---|
| SRC-043 (OGD / data.gov.in AISHE catalogue) = **NEEDS_REVIEW**, "no licence field found" | **APPROVED_WITH_LIMITATIONS** — GODL-India is declared by the portal operator, and the licensor is the publishing ministry, not an intermediary |
| Government aggregates treated as unusable | Ministry-published **aggregate** tables on data.gov.in are reusable, subject to GODL conditions |

GODL-India is a government licence built for reuse; it permits commercial use and redistribution
with attribution, and it excludes personal data and certain restricted categories. That exclusion
matters here: AISHE tables that break out individuals must not be ingested.

## What it does **not** change

The portal's education holdings are **aggregate counts**, not an institution directory. The closest
"institute-wise" hit is a 321-byte parliamentary answer. There is no OGD resource found in this pass
that provides thousands of institution rows with AICTE/UGC codes. So:

- **An institution directory from OGD: BLOCKED (data availability, not licence).**
- **Aggregate education statistics from a ministry-published OGD resource: APPROVED_WITH_LIMITATIONS**
  (attribution, no personal data, cite resource id + publisher + retrieval date).

## Conditions attached to any future import from this source

1. The resource must name a **ministry/department as publisher**; a catalogue of parliamentary
   answers is a secondary compilation and should be preferred only if the primary is unavailable.
2. Record `resource_id`, publisher, dataset name, retrieval date and the GODL attribution string on
   every row (the import pipeline already requires `source_url` and `retrieved_at`).
3. Reject any resource whose fields identify individuals (AISHE has student/faculty-level tables).
4. Do not present an aggregate as a per-institution fact. A state-level count is not a college's
   placement figure.

## Status

- Licence text: **VERIFIED** (quoted above, live page, 2026-10-24).
- An institution-level OGD dataset: **NOT FOUND** (searched "AICTE" and "AISHE"; top results are
  aggregates and parliamentary answers).
- Import performed: **NONE** — no institution directory exists here to import, and aggregates are not
  what the pilot needs.

## Honest correction

`SOURCE_RIGHTS_EVIDENCE.md` and two research agents concluded "no licence field" for this portal.
The correct statement is: **the portal declares GODL-India in its footer for all published
datasets/resources and metadata**; what is missing is per-resource metadata enrichment, not the
grant. This document supersedes those passages for SRC-043.
