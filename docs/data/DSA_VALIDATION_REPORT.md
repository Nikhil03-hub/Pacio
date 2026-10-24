# DSA Validation Report

Phase 2/3, Workstream A deliverable #2. Written 2026-10-24; updated 2026-10-25 after batch 4
(trees and bit manipulation).

```
.venv/Scripts/python.exe scripts/validate_dsa_specs.py
  -> specs supplied: 36 | COMPLETE: 36 | INVALID: 0 | DRAFT: 72        exit 0
.venv/Scripts/python.exe -m pytest backend/tests/test_dsa_specs.py -q
  -> 44 passed
.venv/Scripts/python.exe -m pytest backend/tests/test_dsa_grading_honesty.py -q
  -> 6 passed
.venv/Scripts/python.exe -c "…build_dsa_question_bank()…"
  -> rows 108 | validated 36 | draft 72 | gradable 36
```

Machine-readable per-problem state: `DSA_SPECIFICATION_COMPLETION.csv`.
Catalogue quality audit by a separate agent: `DSA_CATALOGUE_AUDIT.md` (48 findings).
External originality measurement: `DSA_ORIGINALITY_CHECK.md`.

## Where it started and where it is

At the end of Phase 1 the honest figure was **0 of 108 gradable** — the catalogue was prose only.
Four batches later it is **36 of 108**, every one machine-verified, with all twelve topics covered
and trees and bit manipulation now substantially validated. The count rose only by making problems
genuinely testable; nothing was re-labelled to look better.

## What "validated" means, and what changed under it

Early in this phase `gradable` meant *"this id has an entry in dsa_specs.json"* — presence as
proof. That was a defect: a corrupt spec file was caught by a bare `except` and silently returned
an empty set, demoting the entire curriculum to draft with no error anywhere.

Gradability is now keyed to a **harness stamp**
(`verification: {harness: "2026.10-harness-v1", result: "pass", validated_at, cases}`), written only
by `validate_dsa_specs.py --stamp`:

| state | meaning |
|---|---|
| `validated` | the harness passed it under the current version → `gradable: true` |
| `specified_unverified` | a spec exists but the current harness has not passed it |
| `draft` | no spec at all |

A missing file is a legitimate fresh checkout (all draft). A corrupt file **raises** instead of
quietly demoting the bank. Bumping `DSA_HARNESS_VERSION` invalidates old stamps on purpose. The API
overlays this state on every question payload (`_with_gradability`), so a database seeded before
the harness existed cannot keep advertising drafts as gradable.

Per spec the harness requires all 11 fields, the reference solution passing every example **and**
every hidden test, and a deliberately wrong mutant **failing at least one** case. A spec whose
mutant accidentally passes is INVALID — the tests must have teeth.

## Coverage: all twelve topics now have a grader

| Topic | Validated | Total | Gap |
|---|---|---|---|
| LINKED | 7 | 8 | 1 |
| TREES | 7 | 12 | 5 |
| **GRAPHS** | **4** | 10 | 6 |
| **BACKTRACK** | **3** | 8 | 5 |
| **HEAPS** | **2** | 6 | 4 |
| DP | 2 | 12 | 10 |
| ARRAYS | 2 | 12 | 10 |
| POINTERS | 2 | 10 | 8 |
| BINSEARCH | 1 | 8 | 7 |
| STACK | 1 | 8 | 7 |
| GREEDY | 1 | 8 | 7 |
| BITS | 4 | 6 | 2 |
| **Total** | **36** | 108 | 72 |

Batch 4 (6 specs — invert / same-tree / balanced binary tree, number-of-1-bits, counting-bits,
missing-number) deepened the two topics a student meets first. Batch 3 (10 specs, all lead-reviewed)
closed the exact gap the audit called a blocker:
`kth-largest-element`, `top-k-frequent-elements` (HEAPS); `course-schedule`,
`number-of-connected-components`, `network-delay-time`, `word-ladder` (GRAPHS);
`subsets`, `generate-parentheses`, `palindrome-partitioning` (BACKTRACK); `edit-distance` (DP).

**Review independence is uneven.** 26 of the 36 specs were authored by a subagent and reviewed by the lead (author ≠ reviewer). The first 10 were authored and reviewed by the same agent and still carry `reviewer: "pending"` — they are machine-validated but not independently reviewed, and that is recorded rather than papered over.

Difficulty of the 36: **16 Easy, 18 Medium, 2 Hard** (`word-ladder`, `edit-distance`). The bank is
no longer Hard-free, though two is still thin for a "crack a product company" claim.

Hidden tests per spec: 4 (9), 5 (8), 6 (8), 7 (9), 8 (2). Examples: 2 for 26 specs, 1 for the first 10. Edge cases ≥3 everywhere.

Checkers: `exact` 32, `unordered` 3, `nested_unordered` 1. The previously untested checker paths are
now both exercised by real content **and** unit-tested (`test_every_shipped_checker_is_exercised`).

## Defects found and fixed (all with tests)

1. **`unordered` accepted a string in place of a list.** `sorted("ab") == sorted(["a","b"])` is
   `True`, so answering `["a","b"]` with `"ab"` graded correct. Both unordered checkers now require
   list/tuple shapes.
2. **Presence-as-proof gradability** — replaced by the stamp; the API now overlays it on read.
3. **Silent corruption fallback** in `_validated_spec_ids` — removed; it raises.
4. **Two question ids were truncated mid-phrase**, one ending on a dangling hyphen. Slug cap raised
   to 48 (longest real slug is 47) with trailing-hyphen stripping.
5. **One garbled statement** in the batch-1 BST spec rewritten before merge.

Defect 4 also proved the drift detector: after the cap change the validator immediately reported
`INVALID dsa_pointers_006_…: question_id not in catalogue`, because ids derive from title slugs.
That coupling is a live hazard — re-wording a title orphans its spec and stored attempts — and it
was caught by a test rather than in production. Freeze ids in a manifest before any re-wording.

## Security boundary: measured, not assumed

| probe inside `load_function` | result |
|---|---|
| `().__class__.__bases__[0].__subclasses__()` | **ESCAPED** — returned 245 classes |
| `import os` | **blocked** — `ImportError` from the allowlist |

The restricted `exec` is an **authoring guardrail, not a sandbox**. It is safe for trusted,
committed artefacts and must never be pointed at a learner submission.
`test_restricted_exec_is_a_guardrail_not_a_sandbox` pins both halves, including the escape, so if a
future Python closes it the documentation gets re-checked instead of silently going stale.

**Open, deliberately not half-fixed:** no per-case wall-clock budget. A looping reference hangs the
validator. A correct cross-platform fix is a subprocess worker; `signal.SIGALRM` does not exist on
Windows, and shipping a timeout that no-ops on this platform would be worse than the documented gap.

## The in-app judge was fabricated, and is gone

Separate from the authoring harness: `/api/me/dsa/submissions/{run,submit}` used
`_simulated_code_result`, which invented "Accepted", fake "Sample 1 / Sample 2 / Hidden edge" pass
flags and runtime/memory numbers from a **token count**, and a submission therefore set
`solved: true` and `mastery: 88`. A student could earn credit by writing code containing `def ` and
`for`.

It now returns `_static_code_review`: `executed: false`, `graded: false`, a list of labelled static
signals, and a note that nothing was run. `submit_my_dsa_code` keeps `solved`, `mastery`,
`best_submission_id` and `last_solved_at` at their previous values and records only
`attempted: true`. The UI no longer promises that "passing the test suite updates your placement
metrics", and the fake test-case chips are gone. Pinned by 6 tests in
`backend/tests/test_dsa_grading_honesty.py`.

## Originality: the claim was too strong, so it was corrected

Measured against three public lists (`DSA_ORIGINALITY_CHECK.md`):

- **91 of 108 titles match a public canonical list verbatim**; 95/108 match at least one source;
  0/108 are invented names.
- Difficulty agrees with the public list on 90 of 91 comparable titles.
- **Expression overlap: 1 of 1,283 distinct 6-grams** across all `prompt` + `why` text, and that one
  is a stock sentence.
- Topic structure matches no source (order concordance 15%/19%).

Verdict: **generic-naming coincidence, moderate confidence** — what standard problem names do. But
"original problems" is not a defensible phrase, so the wording was corrected in seven files. The
accurate claim: **canonical interview problems under an in-house 12-topic taxonomy, with prompts and
rationale written here.** The moat is the workflow, the tenant data and the verification — not the
problem list.

## One candidate rejected rather than faked

`dsa_linked_008_copy_list_with_random_pointer` is **excluded**. A correct deep copy serialises
byte-identically to its input, so "return the input unchanged" passes every test; the real skill
(fresh node objects with remapped pointers) is unobservable through the JSON in/out harness. It
would have made the count 31 and the claim false.

## What may be said about DSA today

Allowed: "108 curated canonical problems across 12 patterns; **36 are auto-gradable and machine
verified**, including graphs, heaps, backtracking and two Hard problems; the rest are practice
prompts with solutions and rationale."

Not allowed: "108 auto-gradable problems", "an original problem bank", any grading claim about the
78 drafts, or any company-wise "most asked DSA" statistic — no verified source for those exists.

## Next batch, in priority order

1. **TREES → 4 more** (traversal variants, LCA): the largest remaining gap in a high-frequency topic.
2. **DP → 3 more**, including one 2-D grid DP: DP is thin and only one Hard exists.
3. **GRAPHS → 2 more** (BFS on a grid, topological order output): grids are the common interview
   framing.
4. **BITS → 2 more** (count set bits, single number): the topic with the least coverage relative to
   frequency in written rounds.
5. Add a **third Hard** in BACKTRACK to balance the difficulty mix.

Each must arrive with a reference that passes, a mutant that fails, and a stamp — never a title.

## GO / NO-GO for Workstream A

**GO for the 36 validated problems** as genuinely gradable, evidence-backed, and reviewed under a
harness whose own boundary has been measured. Coverage is now broad enough to demo every topic.

**NO-GO for marketing the bank as auto-gradable end to end**, and NO-GO for claiming interview
readiness equal to a commercial platform: 78 drafts remain, Hard coverage is two problems, and the
in-app runner still cannot execute learner code.
