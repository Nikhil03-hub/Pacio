# Dataset Integration Plan

Status: **proposal — not executed.** No external dataset has been imported into Pacio. This
plan defines how a vetted source becomes product data without corrupting the existing
synthetic demo or implying partnerships that do not exist.

## Principles

1. **Separate layers.** Verified public facts, published statistics, live job feeds and
   synthetic demo records live in different collections with an explicit
   `data_status` field. Nothing is silently overwritten.
2. **No identity without provenance.** Every imported record carries `source_id`,
   `source_url`, `retrieved_at`, `verification_status` and, where applicable,
   `published_on` and `definition`.
3. **No partnership inference.** An institution appearing in a public directory or having
   published a placement report does **not** imply an MOU, payout, onboarding or endorsement.
   Those remain synthetic operational records and must stay labelled as such.
4. **Staging first.** Imports run against a dedicated staging database with a pre-import
   backup. Production is a separate, approved step.
5. **Definitions before numbers.** Offers ≠ unique students; median ≠ highest package;
   historical ≠ current. Each statistic stores its metric name and definition.

## Target collections

| Collection | Replaces | Key fields |
| --- | --- | --- |
| `institutions_public` | nothing (new, alongside `institutions`) | `aishe_code`, `name`, `short_name`, `type`, `management`, `state`, `district`, `affiliated_university`, `source_id`, `source_url`, `retrieved_at`, `published_on`, `verification_status`, `data_status` |
| `placement_stats` | nothing (new; `placements` stays synthetic) | `institution_id`, `academic_year`, `metric` (`offers`, `unique_students_placed`, `median_ctc_lpa`, `average_ctc_lpa`, `highest_ctc_lpa`, `companies_count`), `value`, `definition`, `source_url`, `published_on`, `retrieved_at`, `verification_status`, `data_status` |
| `source_registry` | nothing (new) | `source_id`, `name`, `canonical_url`, `licence`, `commercial_use`, `attribution_text`, `refresh_policy`, `enabled`, `notes` |
| `employer_boards` | nothing (new) | `source_id`, `board_token`, `company_name`, `company_domain`, `country_focus`, `verified_at`, `enabled` |
| `job_postings` | `/api/jobs/discover` response only | `source_id`, `board_id`, `external_id`, `dedupe_key`, `title`, `company`, `city`, `country`, `remote`, `employment_type`, `posted_at`, `first_seen`, `last_seen`, `expires_at`, `listing_url`, `apply_url`, `attribution`, `status` |
| `dsa_questions` | existing catalogue (enhanced) | adds `statement`, `signature`, `constraints`, `examples`, `hidden_tests`, `checker`, `expected_complexity`, `spec_version`, `authoring`, `company_evidence` |

The existing `institutions`, `students`, `placements`, `mous`, `revenue_share` collections
remain the **synthetic demo tenant**. Adding a `data_status: "synthetic"` marker to seeded
records is the first, non-destructive migration (BL-27).

## Source decisions (from discovery)

| Domain | Preferred source | Decision |
| --- | --- | --- |
| Institution directory | AISHE / Government OGD (subject to licence verification) | Pending the official-source review; import only the fields the source actually publishes |
| Placement statistics | Institution-published reports (aggregates only) | Manual, one institution at a time, with URL/date/definition; never invent per-company tuples |
| Companies hiring historically | Institution placement reports | Only where the report names companies; otherwise omit |
| Live jobs | Greenhouse / Lever / Ashby public boards for named employers; Adzuna if licensed; Jooble as a legacy bridge | Metadata + canonical apply URL only; no full-description redistribution without permission |
| DSA | Internal curriculum + executable specs | Expand only with original or licensed content; validation before display |
| Benchmarks | Computed across tenants with data | Exclude synthetic institutions from any public/peer claim unless labelled |

## Pipeline

```
fetch (authorised source, rate-limited)
  -> normalise to the target schema
  -> validate (schema, required provenance, no PII, definitions present)
  -> deduplicate (stable source key + cross-source key)
  -> stage into <collection>_staging with import_batch_id
  -> dry-run diff (new / changed / conflicting counts; human review)
  -> approve
  -> transactional-ish import into the target collection (upsert by stable key)
  -> rebuild derived aggregates only from documented definitions
  -> integrity checks + regression tests
  -> record the batch in `import_runs`
```

Every batch stores `import_batch_id`, source, operator, counts, failures and the backup path.

## Field-level rules

- **Institutions:** use the official identifier as the stable key; never reuse a synthetic
  `institution_id` for a real institution.
- **Placement metrics:** one document per (institution, year, metric). Reject a document
  without a definition or source.
- **Jobs:** `apply_url` must be the employer's canonical URL; aggregator URLs are secondary.
  A listing missing from two consecutive successful polls becomes `closed` (soft delete).
- **DSA:** a problem without tests is `draft` and is not shown as gradable.
- **Personal data:** no student-level real data is imported. Institution and job data only.

## UI changes required before display

1. A `data_status` badge: "Published statistic" vs "Demonstration data".
2. Benchmarking must exclude or label synthetic peers.
3. Jobs empty state must state the reason and last sync time.
4. Any company association in the DSA UI must follow the evidence ledger.

## Approval gates

- Legal/licensing review per source (register status `APPROVED`).
- Product sign-off on the metric definitions.
- Staging import + integrity report.
- Acceptance checklist re-run.
- Only then a production migration plan with backup and rollback.
