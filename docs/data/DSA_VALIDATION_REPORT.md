# DSA Validation Report

Phase 2, Workstream A deliverable #2. Written 2026-10-24 by the lead agent.

```
.venv/Scripts/python.exe scripts/validate_dsa_specs.py
  -> specs supplied: 20 | COMPLETE: 20 | INVALID: 0 | DRAFT: 88        exit 0
.venv/Scripts/python.exe -m pytest backend/tests/test_dsa_specs.py -q
  -> 28 passed in 0.64s
.venv/Scripts/python.exe -c "…build_dsa_question_bank()…"
  -> rows 108 | validated 20 | draft 88 | gradable 20
```

Machine-readable per-problem state: `DSA_SPECIFICATION_COMPLETION.csv`.
Catalogue quality audit by a separate agent: `DSA_CATALOGUE_AUDIT.md` (48 findings).
External originality measurement: `DSA_ORIGINALITY_CHECK.md`.

## Where it started and where it is

At the end of Phase 1 the honest figure was **0 of 108 gradable** — the catalogue was prose only.
This session took it to **20 of 108**, with every one of the 20 machine-verified. The count went up
only by making problems genuinely testable; nothing was re-labelled to look better.

## What "validated" means now, and what changed today

Previously `gradable` meant *"this id has an entry in dsa_specs.json"* — presence as proof. That was
a real defect: a corrupt spec file was caught by a bare `except` and silently returned an empty set,
degrading the entire curriculum to draft with no error anywhere.

Now gradability is keyed to a **harness stamp**
(`verification: {harness: "2026.10-harness-v1", result: "pass", validated_at, cases}`), written only
by `validate_dsa_specs.py --stamp`, and `spec_status` has three states:

| state | meaning |
|---|---|
| `validated` | harness passed under the current version → `gradable: true` |
| `specified_unverified` | a spec exists but the current harness has not passed it |
| `draft` | no spec at all |

A missing file is a legitimate fresh checkout (all draft). A corrupt file **raises** instead of
quietly demoting the bank. Bumping `DSA_HARNESS_VERSION` invalidates old stamps on purpose, so a
spec cannot keep advertising gradability after the proof rule moves. Pinned by
`test_gradability_needs_the_current_harness_stamp`, `test_missing_spec_file_is_drafts_not_a_crash`,
`test_corrupt_spec_file_fails_loudly_instead_of_demoting_the_bank`.

The harness itself requires, per spec: all 11 fields present, the reference solution passing every
example **and** every hidden test, and a deliberately wrong mutant **failing at least one** case. A
spec whose mutant accidentally passes is INVALID — the tests have to have teeth.

## Coverage: where the 20 actually are

| Topic | Validated | Total | Gap |
|---|---|---|---|
| LINKED | 7 | 8 | 1 |
| TREES | 4 | 12 | 8 |
| ARRAYS | 2 | 12 | 10 |
| POINTERS | 2 | 10 | 8 |
| DP | 1 | 12 | 11 |
| BINSEARCH | 1 | 8 | 7 |
| STACK | 1 | 8 | 7 |
| GREEDY | 1 | 8 | 7 |
| BITS | 1 | 6 | 5 |
| **GRAPHS** | **0** | 10 | 10 |
| **BACKTRACK** | **0** | 8 | 8 |
| **HEAPS** | **0** | 6 | 6 |
| **Total** | **20** | 108 | 88 |

Difficulty of the 20: 10 Easy, 10 Medium, **0 Hard**.

This table is the single most important line in the report, and it vindicates the instruction not to
inflate: gradable coverage clustered in LINKED (7/8) precisely because linked-list answers are
trivially comparable as arrays, while **the three topics that decide a campus screen — graphs,
heaps, backtracking — have zero validated problems**. An audit flagged this; I re-derived it from
the code and it is correct.

Per-spec depth: hidden tests 4 (9 specs), 5 (4), 6 (4), 7 (3); examples 2 (10 specs), 1 (10 — the
first batch); edge cases ≥3 everywhere; checkers **20/20 `exact`**, so
`unordered`/`nested_unordered`/`float` were shipped unexercised by any real spec.

## Defects found and fixed today (all with tests)

1. **`unordered` accepted a string in place of a list.** `sorted("ab") == sorted(["a","b"])` is
   `True`, so a learner answering `["a","b"]` with the bare string `"ab"` would have been graded
   correct. Both unordered checkers now require list/tuple shapes. Pinned by
   `test_every_shipped_checker_is_exercised`.
2. **Presence-as-proof gradability** — replaced by the stamp (above).
3. **Silent corruption fallback** in `_validated_spec_ids` — removed.
4. **Two question ids were truncated mid-phrase**, one ending on a dangling hyphen
   (`…construct-binary-tree-from-preorder-and-`). Slug cap raised to 48 (longest real slug is 47)
   plus trailing-hyphen stripping.
5. **One garbled statement** in the batch-1 BST spec rewritten before merge.

Defect 4 is also the empirical proof of the drift detector: after the cap change, the validator
immediately reported `INVALID dsa_pointers_006_…: question_id not in catalogue`, because ids are
derived from title slugs. That coupling is a live hazard — re-wording a title orphans its spec and
any stored attempts. It was caught by a test today rather than in production; the fix is to freeze
ids in a manifest before any re-wording campaign.

## Security boundary: measured, not assumed

I probed the harness rather than trusting its docstring:

| probe | result |
|---|---|
| `().__class__.__bases__[0].__subclasses__()` inside `load_function` | **ESCAPED** — returned 245 classes |
| `import os` | **blocked** — `ImportError` from the allowlist |

So the restricted `exec` is an **authoring guardrail, not a sandbox**. It is safe for trusted,
committed artefacts (reference and mutant solutions) and must never be pointed at a learner
submission. `test_restricted_exec_is_a_guardrail_not_a_sandbox` pins both halves of that sentence,
including the escape — if a future Python version closes it, the test tells us the documentation
needs re-checking instead of letting the file grow quietly safer than the doc claims.

**Open and deliberately not half-fixed:** the harness has no per-case wall-clock budget. A looping
reference hangs the validator. A correct cross-platform fix is a subprocess worker with a timeout;
`signal.SIGALRM` does not exist on Windows, and shipping a timeout that silently no-ops on the
platform this project runs on would be worse than the documented gap. NOT RUN; recommended next.

## Originality: the claim was too strong, so it was corrected

The catalogue was sold internally as "108 **original** problems". I measured it against three public
lists (`DSA_ORIGINALITY_CHECK.md`):

- **91 of 108 titles match a public canonical list verbatim**; 95/108 match at least one source;
  0/108 are invented names.
- Difficulty agrees with the public list on 90 of 91 comparable titles.
- **Expression overlap: 1 of 1,283 distinct 6-grams** across all `prompt` + `why` text — and that
  one is a stock sentence ("connected components in an undirected graph").
- Topic structure does not match any source (order concordance 15%/19%); no source's section
  structure or ordering is reproduced.

Verdict: **generic-naming coincidence, moderate confidence** — which is exactly what standard problem
names do. But "original problems" is not a defensible phrase, so the wording was corrected in seven
files (`dsa_catalog.py`, `README.md`, `docs/ARCHITECTURE.md`, `FEATURE_GUIDE_FOR_JUDGES.md`,
`FINAL_PROJECT_DOCUMENTATION.md`, `PACIO_AUDIT.md` F-19, `PACIO_BACKLOG.md` BL-26 — the last two as
dated corrections, not silent rewrites). The accurate claim: **canonical interview problems under an
in-house 12-topic taxonomy, with prompts and rationale written here.** Anyone selling Pacio's
curriculum as a proprietary content moat is overselling; the moat is the workflow, the tenant data
and the verification.

## One candidate rejected rather than faked

`dsa_linked_008_copy_list_with_random_pointer` was **excluded** from batch 2. A correct deep copy
serialises byte-identically to its input, so "return the input unchanged" passes every test — the
actual skill (fresh node objects with remapped random pointers) is unobservable through the JSON
in/out harness. Shipping a spec for it would have made the count 21 and the claim false. The honest
options are a structural checker that compares object identity graphs, or leaving it prose-only.

## Audit reconciliation (what I accepted, what I corrected)

Accepted and now fixed: stamp-gated gradability, checker shape hole, silent corruption path, slug
truncation. Accepted and **not** yet fixed, with reasons: zero graphs/heaps/backtracking coverage
(sequence below), 0 Hard specs, 10 specs with a single example, all-`exact` checkers (three checkers
now unit-tested but still unused by content), missing timeout. Corrected: the audit's headline
originality BLOCKER was asserted from memory with no source fetched — measured, the real position is
weaker than "copied" and stronger than "original", and the docs now say so. The audit's claim that
Greenhouse's robots excluded our endpoint was also wrong in a different workstream; verified
directly.

## What may be said about DSA today

Allowed: "108 curated canonical problems across 12 patterns; **20 are auto-gradable and machine
verified**; the rest are practice prompts with solutions and rationale."

Not allowed: "108 auto-gradable problems", "an original problem bank", or any grading claim about
the 88 drafts. The frontend must not present drafts as gradable, and nothing may advertise
company-wise "most asked DSA" statistics — no verified source for those exists.

## Next 10 to validate, in this order

1. `HEAPS` — merge k sorted lists, top-k / kth-largest via heap (2): topic has zero gradable items
   and heaps are a standard campus-screen discriminator.
2. `GRAPHS` — number of islands, course schedule / cycle detection, shortest path weighted (3):
   largest zero-coverage topic; needs the `unordered`/`nested_unordered` checkers, which are now
   at least unit-tested.
3. `BACKTRACK` — permutations/subsets and one N-Queens-style count (2): zero coverage, and a
   natural fit for `nested_unordered`.
4. `DP` — one 2-D grid DP and one Hard (2): DP is 1-D only today and the bank has no Hard at all,
   which undercuts a "interview ready" claim for top-tier placement cells.

Each must arrive with a reference that passes, a mutant that fails, and a stamp — not a title.

## GO / NO-GO for Workstream A

**GO for the 20 validated problems** as genuinely gradable, evidence-backed, and reviewed under a
harness whose own boundary has been measured.

**NO-GO for marketing the bank as auto-gradable**, and NO-GO for adding new problems before graphs,
heaps and backtracking have working graders. The catalogue is now honest before it is large; that is
the order the mentor asked for.
