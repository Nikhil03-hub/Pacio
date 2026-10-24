# DSA Coverage and Difficulty

Phase 3 deliverable. Generated 2026-10-24 from `backend/dsa_catalog.py` + `backend/dsa_specs.json`
(after batch 4, 2026-10-25). Every count below is reproducible with
`build_dsa_question_bank()` and is asserted in CI against the harness CSV.

## 1. Current gradable coverage

| Topic | Gradable / total | Easy | Medium | Hard |
|---|---|---|---|---|
| LINKED | 7 / 8 | 3 | 4 | 0 |
| TREES | 7 / 12 | 5 | 2 | 0 |
| GRAPHS | 4 / 10 | 0 | 4 | 0 |
| BACKTRACK | 3 / 8 | 0 | 3 | 0 |
| HEAPS | 2 / 6 | 0 | 2 | 0 |
| DP | 2 / 12 | 0 | 1 | 1 |
| ARRAYS | 2 / 12 | 0 | 2 | 0 |
| POINTERS | 2 / 10 | 0 | 2 | 0 |
| BINSEARCH | 1 / 8 | 0 | 0 | 1 |
| STACK | 1 / 8 | 1 | 0 | 0 |
| GREEDY | 1 / 8 | 0 | 1 | 0 |
| BITS | 4 / 6 | 4 | 0 | 0 |
| **Total** | **36 / 108** | **16** | **18** | **2** |

Difficulty of the whole bank: 23 Easy / 75 Medium / 10 Hard. Gradable coverage is now **heavily
weighted to Easy** — 16 of 23 Easy (70%) are gradable, against 18 of 75 Medium (24%) and 2 of 10 Hard
(20%). That is the right order for building a verified bank, but it means an advanced student still has
almost nothing to be graded on.

## 2. What that means for a placement cell

- A student can be auto-verified today on linked lists, trees, graphs, backtracking, heaps and a
  little DP — enough to demo every topic.
- **Depth is thin where interviews are hardest**: 2 of 10 Hard problems, and no Hard in graphs,
  heaps, backtracking, arrays or stack. The Hard problems that exist (`word-ladder`, `edit-distance`)
  are two of the most-searched interview questions, which helps, but does not cover e.g.
  `trapping-rain-water`, `median-from-data-stream` or `serialize-and-deserialize`.
- **Design-style questions are absent.** No LRU/LFU cache, no iterator, no rate limiter. These are
  common in product-company screens and are currently impossible to grade with the JSON in/out
  harness without a stateful sequence API.

## 3. Topic and pattern gaps (independent of validation)

| Gap | Detail |
|---|---|
| Tries | No trie topic at all in the 12. Prefix-search questions cannot be practised. |
| Strings as a topic | String problems are scattered through POINTERS; there is no string/hashing topic. |
| Matrix / grid | `spiral-matrix`, `set-matrix-zeroes`, `unique-paths`, `number-of-islands` exist but none are gradable yet — grids are the most common interview framing. |
| Union-find | `number-of-connected-components` is gradable via DFS; no problem forces a disjoint-set implementation. |
| Topological **output** | `course-schedule` (cycle detection) is gradable; `course-schedule-ii` (ordering) is not. |
| Bit manipulation | Now 4 of 6 gradable, including the three written-round classics; `pow(x,n)` and `reverse-integer` remain. |
| 2-D DP | No gradable 2-D DP. `unique-paths` and `longest-common-subsequence` are drafts. |
| Design / stateful | No LRU, LFU, min-stack or iterator — `min-stack` is a draft and would need an operation-sequence harness. |

## 4. The 72 remaining drafts, exactly

IDs are the stable catalogue ids; spec them in this order (see §5).

```
ARRAYS (10)
  dsa_arrays_002_contains-duplicate            E   dsa_arrays_008_move-zeroes                 E
  dsa_arrays_003_best-time-to-buy-and-sell-stock E dsa_arrays_009_merge-sorted-array          E
  dsa_arrays_004_product-of-array-except-self   M   dsa_arrays_010_find-all-duplicates-in-an-array M
  dsa_arrays_006_maximum-product-subarray      M   dsa_arrays_011_set-matrix-zeroes          M
  dsa_arrays_007_rotate-array                  M   dsa_arrays_012_spiral-matrix              M

POINTERS (8)
  dsa_pointers_001_valid-palindrome            E   dsa_pointers_007_longest-repeating-character-replacement M
  dsa_pointers_002_two-sum-ii-sorted-input     M   dsa_pointers_008_minimum-window-substring H
  dsa_pointers_003_3sum                        M   dsa_pointers_009_find-all-anagrams-in-a-string M
  dsa_pointers_005_trapping-rain-water         H   dsa_pointers_010_permutation-in-string   M

BINSEARCH (7)
  dsa_binsearch_002_search-insert-position     E   dsa_binsearch_006_koko-eating-bananas     M
  dsa_binsearch_003_first-and-last-position-of-a-target M dsa_binsearch_007_capacity-to-ship-packages-within-d-days M
  dsa_binsearch_004_search-in-rotated-sorted-array M dsa_binsearch_008_median-of-two-sorted-arrays H
  dsa_binsearch_005_find-minimum-in-rotated-sorted-array M

STACK (7)
  dsa_stack_002_min-stack                      M   dsa_stack_006_largest-rectangle-in-histogram H
  dsa_stack_003_evaluate-reverse-polish-notation M dsa_stack_007_asteroid-collision           M
  dsa_stack_004_daily-temperatures             M   dsa_stack_008_decode-string                M
  dsa_stack_005_next-greater-element           M

LINKED (1)
  dsa_linked_008_copy-list-with-random-pointer M   [BLOCKED - not gradable in this harness]

TREES (5)
  dsa_trees_007_binary-tree-right-side-view    M   dsa_trees_011_construct-binary-tree-from-preorder-and-inorder M
  dsa_trees_008_lowest-common-ancestor-of-a-bst E  dsa_trees_012_serialize-and-deserialize-binary-tree H
  dsa_trees_010_kth-smallest-element-in-a-bst  M

HEAPS (4)
  dsa_heaps_003_k-closest-points-to-origin     M   dsa_heaps_005_find-median-from-data-stream H
  dsa_heaps_004_merge-k-sorted-lists           H   dsa_heaps_006_task-scheduler               M

GRAPHS (6)
  dsa_graphs_001_number-of-islands             M   dsa_graphs_005_pacific-atlantic-water-flow M
  dsa_graphs_002_clone-graph                   M   dsa_graphs_007_course-schedule-ii          M
  dsa_graphs_003_max-area-of-island            M
  dsa_graphs_004_rotting-oranges               M

BACKTRACK (5)
  dsa_backtrack_002_combination-sum            M   dsa_backtrack_006_n-queens                  H
  dsa_backtrack_003_permutations               M   dsa_backtrack_007_letter-combinations-of-a-phone-number M
  dsa_backtrack_004_word-search                M

DP (10)
  dsa_dp_002_house-robber                      M   dsa_dp_008_edit-distance (validated)       H
  dsa_dp_003_house-robber-ii                   M   dsa_dp_009_partition-equal-subset-sum      M
  dsa_dp_004_coin-change                       M   dsa_dp_010_unique-paths                    M
  dsa_dp_005_longest-increasing-subsequence    M   dsa_dp_011_decode-ways                     M
  dsa_dp_006_word-break                       M   dsa_dp_012_target-sum                      M
  dsa_dp_007_longest-common-subsequence        M

GREEDY (7)
  dsa_greedy_002_insert-interval               M   dsa_greedy_006_jump-game-ii                M
  dsa_greedy_003_non-overlapping-intervals     M   dsa_greedy_007_gas-station                 M
  dsa_greedy_004_meeting-rooms-ii              M   dsa_greedy_008_partition-labels            M
  dsa_greedy_005_jump-game                     M

BITS (2)
  dsa_bits_005_pow-x-n                         M   dsa_bits_006_reverse-integer               M
```

(72 listed; `dsa_dp_008_edit-distance` is shown only to mark that DP already has one validated Hard.)

## 5. Recommended order for the next batches

Batch 4 (3 trees + 3 bits) is done. Next, in this order:

1. **DP (10)** — the largest remaining block and the weakest area for a serious candidate.
   `unique-paths` gives the bank its first gradable 2-D DP; `house-robber`, `coin-change` and
   `longest-common-subsequence` are the standard on-ramps.
2. **HARD problems (8 of the 10 remain)** — `trapping-rain-water`, `minimum-window-substring`,
   `largest-rectangle-in-histogram`, `merge-k-sorted-lists`, `find-median-from-data-stream`,
   `serialize-and-deserialize-binary-tree`, `n-queens`, `median-of-two-sorted-arrays`. Hard coverage is
   the biggest credibility gap for product-company screening.
3. **DP (10)** — `unique-paths` gives the bank its first gradable 2-D DP; `house-robber` and
   `coin-change` are the standard on-ramps.
4. **ARRAYS (10)** — Easy ones first; `spiral-matrix` and `set-matrix-zeroes` need explicit
   mutation semantics in the statement.
5. **GRAPHS (6)** — grid BFS (`rotting-oranges`, `number-of-islands`) is the common interview framing;
   `clone-graph` needs the same node-identity harness problem that blocked `copy-list-with-random-pointer`
   and may have to stay a draft.
6. STACK / BINSEARCH / POINTERS / GREEDY — validate as capacity allows; several are stateful design
   problems (`min-stack`, `median-from-data-stream`) that need a sequence-of-operations harness
   before they can be graded honestly.

**Rule for every batch:** reference passes all cases, a plausible mutant fails at least one, expected
values computed independently, and a lead review recorded. A problem that cannot be observed through
JSON in/out stays a draft and is named in this file rather than quietly dropped.
