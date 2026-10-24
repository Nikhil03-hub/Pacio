# Job Feed Pilot Report

Phase 2, Workstream D deliverable #5. Run 2026-10-24.

```
.venv/Scripts/python.exe scripts/job_feed_pilot.py
.venv/Scripts/python.exe scripts/job_feed_pilot.py --mongo-url mongodb://127.0.0.1:27017 --db-name pacio_dryrun_jobs
```

Exit code 0 for both. Full machine-readable evidence: `docs/data/job_feed_pilot_raw.json` and
`docs/data/job_feed_pilot_raw_mongo.json`. Behaviour was **identical** on the in-memory store and on
real MongoDB (`totals`, `location_relevance`, `per_board_stored` compared field by field).

Everything written went into a disposable database and was rolled back
(`stored_after_rollback: 0`, `cleanup: dropped`). The application database and the synthetic demo
tenant were not touched.

## An honest disclosure first

The **first** pilot run pre-dated robots.txt enforcement and polled all three boards, including
`api.ashbyhq.com`, collecting 796 OpenAI postings. When the rights research pass (Workstream C)
returned, `https://api.ashbyhq.com/robots.txt` was found to answer **HTTP 401**, i.e. the host
publishes no permissive crawl policy and its terms were unreachable. That first run therefore
polled a feed whose crawl policy we had not read. Mitigation, in order: every row from that run was
already rolled back (nothing persisted anywhere), the code now refuses a feed before making the
data request, and the pilot was re-run under the gate. Recorded here rather than quietly re-run.
Status: VERIFIED breach, VERIFIED remediation.

## Machines built

- `backend/job_feeds.py` — provider adapters (Greenhouse, Lever, Ashby), robots gate, dedupe,
  liveness reconciliation, import through the approval gate.
- `scripts/job_feed_pilot.py` — live poll of a named board list into a disposable database.
- `backend/tests/test_job_feeds.py` — 16 tests, fixtures only, no network.

## What the pilot observed (real data, second run, under the gate)

| Board | Provider | robots.txt | Crawl-delay | HTTP | Poll result |
|---|---|---|---|---|---|
| Groww | Greenhouse | `published`, allowed (`Disallow: /embed/` does not cover `/v1/…`) | none | 200 | 10 postings, 10 new |
| CRED | Lever | `published`, `Allow: /` | 1s (we waited 1.5s) | 200 | 8 postings, 8 new |
| OpenAI | Ashby | **`unreadable` — HTTP 401** | — | not requested | **refused before the request** |

Second poll of the two permitted boards: `{new: 0, updated: 0, unchanged: 10}` and
`{new: 0, updated: 0, unchanged: 8}`. Real, repeated network data re-importing as no-op is the
strongest idempotency proof available without inventing fixtures.

Totals across both polls: 6 requests, 4 successful, **2 refused by policy**, 18 unique postings,
18 duplicate observations collapsed, **144 posting-body fields received and discarded**.

Sample of what was stored (all employer-published, all attributed):

| Company | Title | Location as the employer wrote it | Posted | Apply link host |
|---|---|---|---|---|
| CRED | accounts payable manager | hyderabad | 2026-09-28 | jobs.lever.co |
| CRED | area collections manager, pune (recoveries) | mumbai | 2026-08-21 | jobs.lever.co |
| CRED | business development & partnerships | bengaluru | 2026-05-25 | jobs.lever.co |
| Groww | Assistant Manager - Internal Audit | Bengaluru-VTP, India | 2026-09-14 | job-boards.eu.greenhouse.io |
| Groww | Creative Illustrator | Bengaluru-VTP, India | 2026-10-08 | job-boards.eu.greenhouse.io |

Rows are drawn from the full evidence JSON (`polls[].records`); the report's own
`sample_stored_rows` block holds the first eight sorted by company, so CRED fills it.

## Verified against the mandate's checklist

| Requirement | Result | Evidence |
|---|---|---|
| Applicable terms and permitted fields | PARTIAL | robots.txt read and enforced per host. Provider **ToS** is not cleared: Lever's ToS bars competitor/benchmarking access, Greenhouse's ToS page 404'd, Ashby's product terms were unreachable. See `SOURCE_RIGHTS_EVIDENCE.md`. |
| Stable external IDs and deduplication | VERIFIED | `SRC-ATS-PILOT:<board>:<provider id>`; 36 observations → 18 unique, 18 collapsed. |
| Canonical employer application links | VERIFIED | 18/18 `https`, 18/18 hosted on the provider's own domain (`greenhouse.io` / `lever.co`); an off-provider host is flagged for human review by `check_links()`. |
| Location and role accuracy | PARTIAL | Locations are the employer's own strings, unnormalised. Six distinct values across two cities: `bengaluru`, `Bengaluru, India`, `Bengaluru-VTP, India`, `hyderabad`, `mumbai`, `India`. A placement cell filtering on "Bengaluru" would silently miss three of them. |
| First-seen / last-seen / expiry | VERIFIED (logic) | `reconcile_visibility()` marks absent postings, expires them after a 14-day grace, and un-expires them if the employer relists. Proven by `test_visibility_lifecycle_absent_then_expired_then_reappeared`. **Not** proven live — no employer withdrew a posting mid-pilot, so that half rests on fixtures, not on network evidence. |
| Honest handling of unavailable feeds | VERIFIED | A failed poll leaves the last-known state untouched and never mass-expires: `visibility: skipped, feed unavailable`. The Ashby refusal is the live demonstration. |
| Attribution | VERIFIED | Every row carries `attribution` and `careers_url`; stored in the JSON evidence. |
| Rate limiting | VERIFIED | Sequential, 1.5s floor, raised to the host's `Crawl-delay` when larger. One request per board per poll; robots probe cached per origin. |
| No redistribution of full job descriptions | VERIFIED | 144 body fields received, 0 stored. `FORBIDDEN_KEYS` is enforced inside `_clean()` and asserted by `test_no_provider_body_text_survives_any_adapter`, so a future edit cannot quietly start storing employer text. |
| No broad crawler, no restricted-site scraping | VERIFIED | Three named boards in a code constant; no link-following, no sitemap use, no `--all-boards` mode. Jooble was not called and its quota untouched. |

## What this means for the product

**The employer-hosted lane works mechanically and is the only live-data lane that is close to
clearance — but it is not yet commercially cleared, and 1 of 3 attempted boards is already refused by
policy.** The India relevance of an arbitrary board list is poor: 10 of 18 stored postings were
India-located only because Groww and CRED happen to be Indian; OpenAI would have contributed 796
non-Indian rows. So board selection is a *curation* problem, not a volume problem — the placement
cell needs a named, reviewed list of companies that actually recruit on campus.

## Next actions, in order

1. Read Greenhouse's and Ashby's actual terms (their ToS URLs 404'd); keep both lanes **off** in the
   product until then. Lever is the only affirmative `Allow: /` and even it has a ToS restriction.
2. Decide the permitted-field list with counsel or by written consent, then record it in
   `SOURCE_APPROVAL_DECISIONS.md` before any board is enabled in the application database.
3. Add a location normaliser (city → state → "eligible region") before surfacing jobs to students.
4. Run one board on a schedule (daily) against staging and measure real churn: how many postings
   appear, disappear and reappear per week. Until that is measured, the expiry threshold is a guess.
5. Only then expand the board list — as a curated, per-company allowlist, never as a crawler.

**GO/NO-GO for this milestone: GO as a prototype. NO-GO for shipping live jobs to customers.**
The ingestion mechanism, dedupe, link canonicalisation and refusal-on-unknown-policy are proven on
real networks. The commercial permission to hold and show this data is not.
