# DSA Coverage and Validation

Audit date 2026-10-23. Catalogue version `2026.10-pattern-v1` (12 topics, 108 problems).
Source: `backend/dsa_catalog.py`. Findings below are machine-verified from that file.

## 1. Coverage

Difficulty mix: **23 Easy / 75 Medium / 10 Hard** (21% / 69% / 9%).

| Topic | Count | E/M/H | Gaps |
| --- | --- | --- | --- |
| Arrays & Hashing | 12 | 5/7/0 | No Hard; hashing is only 2 of 12; matrix problems parked here |
| Two Pointers & Sliding Window | 10 | 1/7/2 | Two families merged; only 5 sliding-window; no prefix-sum family |
| Binary Search | 8 | 2/5/1 | Thin "search on the answer" (2) |
| Stacks | 8 | 1/6/1 | No queue/deque; no data-structure design (LRU/LFU) |
| Linked Lists | 8 | 3/5/0 | No Hard; K-way merge lives under Heaps |
| Trees & BSTs | 12 | 6/5/1 | Strongest; no tree DP beyond diameter; no iterator |
| Heaps & Top-K | 6 | 0/4/2 | No Easy on-ramp |
| Graphs | 10 | 0/9/1 | No Easy; union-find only implicit; one Dijkstra, no Bellman-Ford/Floyd |
| Backtracking | 8 | 0/7/1 | No Easy; no duplicate-pruning family |
| Dynamic Programming | 12 | 1/10/1 | No interval/tree/digit DP |
| Greedy & Intervals | 8 | 0/8/0 | No Easy, no Hard |
| Bits & Maths | 6 | 4/2/0 | No Hard; no bitmask enumeration |

**Missing canonical topics:** sorting (merge/quick/quickselect/comparator), tries, strings as a
first-class topic, queues/deques, data-structure design, number theory (sieve/gcd/modular).

**Near-duplicates:** 9 clusters, ~19 problems (cycle I/II, house robber I/II, jump game I/II,
course schedule I/II, islands vs max area, merge array vs merge list, two-sum variants,
level-order vs right-side view, kth-largest vs top-k). No identical titles.

**Dead code:** `seen_subtopics` in `build_dsa_question_bank()` is computed and never used.

## 2. Testability — the critical gap

**0 of 108 problems are executable or auto-gradable.**

- 0 include examples; 0 specify input/output format; 4 contain any digit; 3 mention bounds.
- Median prompt length is 10 words, e.g. "Find the contiguous subarray with the largest
  sum." — no return specification.
- "Two Sum" omits the usual exactly-one-solution guarantee, so even a correct implementation
  could legitimately differ.

This means the tracker records *self-reported or seeded* completion; it cannot grade. That is
acceptable for a demo, not for a paid feature that claims to measure readiness.

## 3. Proposed problem schema

```json
{
  "id": "dsa_arrays_001",
  "topic": "ARRAYS",
  "pattern": "hash_map",
  "difficulty": "easy",
  "statement": "Given an array of integers and a target, return the indices of the two values that add up to the target. Exactly one solution exists and an element may not be used twice.",
  "signature": {"lang": "python", "name": "two_sum",
                "params": [["nums", "list[int]"], ["target", "int"]], "returns": "list[int]"},
  "constraints": ["2 <= len(nums) <= 10^4",
                  "-10^9 <= nums[i], target <= 10^9",
                  "exactly one valid pair exists"],
  "examples": [{"in": {"nums": [2, 7, 11, 15], "target": 9}, "out": [0, 1]}],
  "hidden_tests": [
    {"in": {"nums": [3, 3], "target": 6}, "out": [0, 1]},
    {"in": {"nums": [-1, -2, -3, -4, -5], "target": -8}, "out": [2, 4]}
  ],
  "checker": "unordered",
  "expected_complexity": {"time": "O(n)", "space": "O(n)"},
  "authoring": {"author": "", "date": "", "method": "original", "reviewer": ""},
  "company_evidence": []
}
```

Process for every problem:

1. Author the statement, constraints, examples and hidden tests.
2. Schema-lint the record.
3. A reference solution must pass every hidden test.
4. **Negative mutants** — a deliberately wrong solution must fail; this catches weak tests.
5. Ambiguity review by a second person; bump `spec_version` on any change.
6. Complexity checked by input-scaling (a smoke signal, not proof).

**Never execute learner code in CI.** CI validates only trusted artefacts (schema, reference
solutions, mutants) in a locked container. Learner submissions belong in a separate
ephemeral sandbox (gVisor/Firecracker/nsjail, seccomp, no network, wall-clock and output
caps) with no repository credentials. Today there is no CI workflow and no test references
the catalogue — **NOT RUN**.

## 4. Licensing findings

| Source | Terms | Commercial verdict |
| --- | --- | --- |
| CSES Problem Set | No licence found on the site | **BLOCKED** (default copyright) |
| Project Euler | CC BY-NC-SA 4.0 | **BLOCKED** (non-commercial) |
| LeetCode | Proprietary; scraping forbidden | **BLOCKED** — link out only |
| GeeksforGeeks | Bans compiling collections/databases without permission | **BLOCKED** |
| HackerRank | Bans copying/derivatives | **BLOCKED** |
| Codeforces | No reciprocal licence to third parties | **BLOCKED** |
| Kaggle "LeetCode" mirrors (CC0 label) | Uploader cannot license third-party text | **REJECTED** (licence laundering) |
| DeepMind CodeContests (HuggingFace) | CC BY 4.0, but underlying Codeforces content is separately restricted | **PARTIAL** — calibration only |
| jwasham/coding-interview-university | CC BY-SA 4.0 | Study plan only; ShareAlike affects adaptations |
| TheAlgorithms/Python | MIT | Oracle/reference code only |

**What this means for Pacio:** the 108 prompts are original wording, but several titles are
canonical (short titles are not protectable) and the selection/ordering still resembles
common commercial curricula. Compilation originality is **PARTIAL** and should get legal
review before a sale. Do not import text from any blocked source.

## 5. Company-claim evidence standard

Only display a company association when it is backed by:

`PACIO_INTERNAL` (own mock/placement data, with n and window) or `OFFICIAL` (the company's
own page) or **≥3 independent `DATED_REPORT`s** within 24 months, with role/level and URL.

`COMMUNITY_ANECDOTE` and `UNVERIFIED` may never appear as "asked at X". Never show
frequencies without a denominator and sampling method, never imply endorsement, and do not
use company logos as badges.

## 6. Recommended next steps

1. **Freeze the catalogue** and add specs/tests before expanding it (BL-32).
2. Add SORTING (8), TRIES (5), STRINGS (6), DESIGN (4); rebalance to ≥30% Easy (BL-33).
3. Add a per-problem authoring log plus no-copy attestation.
4. Build the company-evidence ledger before any "asked at" label (BL-34).
5. Remove the dead `seen_subtopics` code and update `DATA_SOURCES` when the above is done.

Status: coverage and licence quotes **VERIFIED**; executable validation **NOT RUN**;
compilation legal review **BLOCKED** (needs counsel).
