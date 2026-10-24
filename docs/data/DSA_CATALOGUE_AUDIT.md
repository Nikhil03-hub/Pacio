# DSA Catalogue Quality Audit

Scope: the 108-problem Pacio DSA curriculum in `backend/dsa_catalog.py`.
Status: complete — 48 findings (8 BLOCKER / 28 MAJOR / 12 MINOR), tallied in the Summary.
Evidence labels per section are in the Summary table; the audit boundary is in Section 0.

## 0. Method And Evidence Boundary

- `backend/dsa_catalog.py` read once, in full (474 lines). Counts below come from
  `build_dsa_question_bank()` and `c.PROBLEMS`, executed with
  `./.venv/Scripts/python.exe` — VERIFIED.
- `backend/dsa_specs.json` was NOT read in full. Only aggregate field values were printed
  (`checker`, `provenance`, `authoring`) — VERIFIED for those fields.
- `backend/tests/test_dsa_specs.py` was read (assertions inspected). **pytest was not run**,
  so "the 20 specs pass their reference and reject a mutant" is NOT CHECKED in this audit.
- LeetCode / GeeksforGeeks / NeetCode title and difficulty comparisons were made from
  memory. **No third-party site was fetched.** Every originality claim in Section 4 is
  therefore INFERRED, not VERIFIED, and must be confirmed by a human before it is acted on.
- Indian campus-hiring frequency judgements (Sections 1 and 6) are INFERRED practitioner
  opinion, not measured from Pacio data — no attempt logs were analysed.

## 1. Topic Coverage

`n` = problems in topic; `E/M/H` = difficulty labels as they appear in code; `Graded` =
specs present in `dsa_specs.json`. All counts VERIFIED.

| # | Topic | n | E/M/H | Graded | Missing for Indian campus hiring | Over-weighted vs real frequency | Severity |
|---|---|---|---|---|---|---|---|
| 1 | ARRAYS | 12 | 5/7/0 | 2 | Group Anagrams, Valid Anagram, Majority Element (Boyer-Moore), Longest Consecutive Sequence, Rotate Image, Valid Sudoku | 3 simulation/index-marker items (Spiral, Set Matrix Zeroes, Find All Duplicates) that are rare in a 45-min campus round | MAJOR |
| 2 | POINTERS | 10 | 1/7/2 | 2 | Sort Colors (Dutch national flag — a standard TCS/Infosys written question), Squares of a Sorted Array, 4Sum, trapping-water variants | 5 of 10 items are the same sliding-window frequency mechanic (006-010); window is over-served, two-pointer compaction under-served | MAJOR |
| 3 | BINSEARCH | 8 | 2/5/1 | 1 | Search a 2D Matrix, Kth Missing Positive, aggressive-cows/magician-style answer search, rotated-with-duplicates | Koko + Capacity-to-Ship are one template counted twice (see D4); Median of Two Sorted Arrays is near-zero frequency on campus | MINOR |
| 4 | STACK | 8 | 1/6/1 | 1 | Sliding-window maximum (monotonic **deque**), Next Greater Element II (cyclic), Implement Queue using Stacks, Simplify Path, Valid Parentheses with wildcards | 2 next-greater items (D3) + Histogram is Hard-tier and rarely asked cold | MAJOR |
| 5 | LINKED | 8 | 3/5/0 | 7 | Find the Duplicate Number (Floyd on an array), Remove Duplicates from a Sorted List, Palindrome Linked List, Partition a List, LRU/LFU design | None. This is the best-balanced topic and the only one with 7/8 gradable | — |
| 6 | TREES | 12 | 6/5/1 | 4 | Path Sum / Path Sum II, Zigzag + Boundary + Diagonal traversal (these three are *routine* in Indian written rounds), Sorted Array to BST, Same-tree-merging, Tree from In+Post | 6 Easy "check a structural property" recursions (Depth, Invert, Diameter, Balanced, Same, LCA-BST) = half the topic | MAJOR |
| 7 | HEAPS | 6 | 0/4/2 | **0** | Last Stone Weight (the standard Easy heap entry), Reorganize String, Kth Smallest in a Sorted Matrix, Sliding-window median, Merge K *arrays* | No Easy at all, so the topic has no entry point; K-selection is repeated 3x (D12) | MAJOR |
| 8 | GRAPHS | 10 | 0/9/1 | **0** | MST (Kruskal/Prim), Bellman-Ford and 0-1 BFS, Cheapest Flights Within K Stops, bipartite check, Number of Provinces, Alien Dictionary, Keys and Rooms, Flood-fill with area+perimeter | Only 1 weighted-path item (Network Delay) against 9 unweighted BFS/DFS items; Course Schedule I+II and Islands I+II each counted twice (D6, D7) | BLOCKER |
| 9 | BACKTRACK | 8 | 0/7/1 | **0** | Combination Sum II, Subsets II (duplicate handling), Sudoku Solver, Expression Add Operators, K-th symbol; no Easy at all | N-Queens (Hard) and Palindrome Partitioning are discussion problems, not campus coding-round problems | MAJOR |
| 10 | DP | 12 | 1/10/1 | 1 | 0/1 Knapsack as its own item, Minimum Path Sum / Triangle / Maximal Square (2-D grid DP), Longest Palindromic Subsequence, Buy-Sell with cooldown, DP on trees, bitmask DP, LCS-adjacent diff | 10 of 12 states are 1-D or 2-D *string* tables; only Unique Paths touches a grid and it has no obstacles. Subset-sum appears 3x (D5) | MAJOR |
| 11 | GREEDY | 8 | 0/8/0 | 1 | Arrows to Burst Balloons, Minimum Platforms (vs Meeting Rooms II), Assign Cookies, Fractional Knapsack, Queue Reconstruction | The interval sweep is 4 of 8 items (Merge/Insert/Non-overlapping/Meeting Rooms II); Jump Game I+II is one trick twice (D10). No Easy, no Hard | MAJOR |
| 12 | BITS | 6 | 4/2/0 | 1 | **All number theory**: GCD/LCM, prime sieve, primality, modular arithmetic and `nCr mod p`, power-of-two test, Sum of Two Integers, Bitwise AND of Numbers Range, Single Number II, Reverse Bits; no Hard | The topic is named "Bit Manipulation **& Maths**" and its focus promises "fast arithmetic", yet it contains zero maths problems | BLOCKER |

### Coverage findings

- **C1 — BLOCKER.** BITS is labelled "Bit Manipulation & Maths" but carries no arithmetic:
  no GCD/LCM, no sieve, no primality, no modular exponentiation, no combinatorics. For
  Indian campus hiring this is the *highest-volume* question family (TCS NQT, Infosys,
  Wipro, Capgemini round-1 are maths-heavy), and it is the one family the syllabus of every
  Indian CS curriculum guarantees. Fix: rename the topic to `BITS`, and add a 13th topic
  `MATHS` (GCD/LCM, count primes up to n, `nCr mod p`, power-of-two, digit-sum, modular
  exponentiation) with 8 problems; update the `DSA_TOTAL == 108` assert in the same commit.
- **C2 — BLOCKER.** GRAPHS (10), HEAPS (6), BACKTRACK (8) = 24 curated problems, 0 gradable
  specs — and those are three of the four topics Indian interviewers treat as the pass/fail
  line (BFS/DFS, priority queue, recursion). Progress claims built on "108 problems" rest on
  84 gradable-free problems concentrated exactly where signal matters. See Section 6.
- **C3 — MAJOR.** 4 of 12 topics contain **zero Easy problems** (HEAPS, GRAPHS, BACKTRACK,
  GREEDY). Overall mix is 23 Easy / 75 Medium / 10 Hard (21% / 69% / 9%) — VERIFIED by
  arithmetic (the per-topic E+M+H sums equal every topic length, so no fourth label exists).
  A first-round campus funnel wants roughly 40% Easy. Fix: insert 1-2 Easy entry problems per
  no-Easy topic before adding any new Medium.
- **C4 — MAJOR.** Weighted graphs are thin (1 item) and MST is absent (0 items), while
  Dijkstra, Bellman-Ford, Prim and Kruskal are syllabus items in Indian CS degrees and appear
  in product-company campus rounds. Fix: add Cheapest-Flights-style bounded shortest path,
  one Kruskal/MST and one bipartite/colouring problem to GRAPHS.
- **C5 — MAJOR.** String hashing canon is missing at the top of the funnel: Group Anagrams
  and Valid Anagram do not appear anywhere, while the two *anagram-window* problems (009, 010)
  do. This inverts real frequency — hash-key grouping is among the three most-asked campus
  string questions. Fix: add Group Anagrams and Valid Anagram to ARRAYS; de-duplicate per D2.
- **C6 — MAJOR.** DP is 1-D/2-D-string heavy: only `Unique Paths` is a grid, and it is
  deliberately obstacle-free, so no grid-with-obstacles or min-cost-grid DP exists anywhere.
  Fix: replace Unique Paths with Minimum Path Sum and add Maximal Square.
- **C7 — MINOR.** No design/data-structure-implementation item except Min Stack: LRU Cache,
  Trie, and a time-keyed map are all absent, and Trie absence also leaves Word Search II and
  autocomplete-style follow-ups unreachable. Fix: add LRU Cache and Implement Trie to STACK
  or a new `DESIGN` topic.
- **C8 — MINOR.** Monotonic **deque** is absent despite the topic name "Stacks & Monotonic
  Structures"; Sliding Window Maximum is a frequent campus question and cannot be taught from
  this bank. Fix: add it to STACK.
- **C9 — MINOR.** Duplicate-input handling is tested once (3Sum). Subsets II / Combination
  Sum II / Find Duplicates-with-repeats are absent, so the "sort then skip equal neighbours"
  reflex — a common rejection reason — is untrained. Fix: add one duplicates-backtracking item.

## 2. Duplication Clusters

Method: grouped all 108 `(title, pattern)` pairs by the `pattern` string and by the trick the
prompt actually requires. "Same skill" = same data structure; "same trick" = same insight that
earns the marks. Ids and pattern strings VERIFIED from code; the *judgement* that two tricks
are identical is INFERRED.

| ID | Cluster (all ids) | Same skill? | Same trick? | Recommend | Reason | Severity |
|---|---|---|---|---|---|---|
| D1 | `dsa_binsearch_001_binary-search` / `dsa_binsearch_002_search-insert-position` / `dsa_binsearch_003_first-and-last-position-of-a-target` | yes | yes — lower bound, three times | **Keep 2** (002 lower-bound template + 003 the double-bound application); retire 001 from *progress* counting | 001 is "return the index or -1", which is 002 plus a equality check. Note 001 is already one of the 20 gradable specs, so it should be re-labelled a warm-up (`counts_toward_progress: false`) rather than deleted — deleting it orphans a shipped spec | MAJOR |
| D2 | `dsa_pointers_009_find-all-anagrams-in-a-string` / `dsa_pointers_010_permutation-in-string` | yes | yes — fixed-size window + frequency compare | **Keep one** (009) | The prompts say it themselves: "Frequency arrays with a fixed window size" vs "Same window mechanics as anagram search, with an early exit". Two items whose `why_it_matters` differ only by return type is the definition of catalogue padding | MAJOR |
| D3 | `dsa_stack_004_daily-temperatures` / `dsa_stack_005_next-greater-element` | yes | yes — decreasing stack, pop on a greater element | **Keep one** (004) | Daily Temperatures is Next Greater Element with `i - j` instead of the value; the pattern strings are literally both `Monotonic stack`. 004 is untested, 005 untested, so either can be dropped without orphaning a spec | MAJOR |
| D4 | `dsa_binsearch_006_koko-eating-bananas` / `dsa_binsearch_007_capacity-to-ship-packages-within-d-days` | yes | yes — binary search on a monotone feasibility predicate + a greedy checker | **Keep one** (007) | 006's own note concedes it: "Same template as Koko with a different feasibility check." Prefer 007 if the third-party scenario risk in O3 is being paid down anyway | MAJOR |
| D5 | `dsa_dp_009_partition-equal-subset-sum` / `dsa_dp_012_target-sum` | yes | yes — 0/1 subset-sum rolling boolean/integer table | **Keep one** (009) and repurpose 012 | `Target Sum` is subset-sum counting: `sum(positive) = (total+target)/2`. Repurpose slot 012 for the genuinely missing 0/1 Knapsack (max value under capacity), which kills a coverage gap and a duplicate in one edit | MAJOR |
| D6 | `dsa_graphs_001_number-of-islands` / `dsa_graphs_003_max-area-of-island` | yes | yes — same flood fill | **Keep both, merge scoring** | The only difference is the accumulator (counter vs size). Cheapest fix: one item, two required outputs, so the BFS infra is specced once. Both are draft, so no spec breakage | MINOR |
| D7 | `dsa_graphs_006_course-schedule` / `dsa_graphs_007-course-schedule-ii` | yes | yes — Kahn / DFS colouring | **Keep one** (007) | Returning an order subsumes the boolean: `feasible = (len(order) == n)`. 006 adds a "can it be done" framing that is worth one edge case, not a whole item | MINOR |
| D8 | `dsa_heaps_001_kth-largest-element-in-an-array` / `dsa_heaps_002_top-k-frequent-elements` / `dsa_heaps_003_k-closest-points-to-origin` | yes | yes — size-k bounded heap, evict on compare | **Keep two** (001 + 002) | 002 adds a counting stage (a real second skill); 003 adds nothing except a distance key. 003 is where to spend the freed slot (Last Stone Weight or Reorganize String) | MAJOR |
| D9 | `dsa_trees_001_maximum-depth` / `dsa_trees_003_diameter` / `dsa_trees_004_balanced-binary-tree` | yes | yes — height returned up the recursion | **Keep 003 + 004**; 001 stays only as warm-up | Three items on "compute height bottom-up, sometimes with a second accumulator". 001 and 003 are already gradable, so downgrade rather than delete (see O2 for why deletion is unsafe) | MINOR |
| D10 | `dsa_greedy_005-jump-game` / `dsa_greedy_006-jump-game-ii` | yes | yes — farthest reachable frontier | **Keep both** | Decision vs optimisation is a legitimate step-up, and the BFS-over-ranges reframing in 006 is a distinct insight. This is the model for how D2/D3/D4 *should* have been split | — (no action) |
| D11 | `dsa_linked_005_linked-list-cycle` / `dsa_linked_006_linked-list-cycle-ii` | yes | partly — Floyd detection, then a distance proof for entry | **Keep both** | Cycle II requires the `2(a+b) = a+b+nL` argument; that is a separate reasoning step, and both are already gradable so the pair is load-bearing for the 20 | — (no action) |
| D12 | `dsa_pointers_001_valid-palindrome` / `dsa_dp_003-house-robber-ii` — *cross-topic pattern reuse* | n/a | n/a | No action | Checked for accidental cross-topic collisions: `converging-pointers` never recurs outside POINTERS; the only repeated `subtopic_code` values inside one topic are D1/D3/D4/D8/D9 above plus `Monotonic stack`, `Sliding window`, `Converging pointers`, `1D/2D DP` families — VERIFIED by grouping `subtopic_code` per topic | — (info) |
| D13 | `dsa_arrays_005_maximum-subarray` / `dsa_arrays_006_maximum-product-subarray` | yes | no — sign-flip dual state is a new insight | **Keep both** | The product version fails for anyone who only knows Kadane; that is the point of asking it | — (no action) |
| D14 | `dsa_pointers_002_two-sum-ii-sorted-input` / `dsa_arrays_001_two-sum` | no | no — hash lookup vs sorted scan | **Keep both** | Deliberate contrast, and 001 is gradable. This pair is the counter-example that shows the catalogue is not indiscriminately padded | — (no action) |

**Net effect if D1-D8 are actioned:** 108 -> 102 curated problems with *higher* topic coverage,
because 6 freed slots map straight onto the C1-C9 gaps (MST, Dijkstra-with-stops, grid DP,
monotonic deque, Group Anagrams, number theory).

- **T1 — MAJOR.** 6 of the 8 duplicate clusters sit in the three topics that carry the most
  items per trick (POINTERS windows, BINSEARCH search-on-answer, TREES height recursion).
  Duplication is not spread evenly — it is a by-product of filling topics by "famous list"
  rather than by pattern budget. Fix: add a catalogue lint that asserts each
  `(topic_code, subtopic_code)` pair appears at most 2 times and publish the pattern budget
  next to `CURRICULUM_VERSION`.
- **T2 — MINOR.** Dead dedup machinery: `seen_subtopics` is built at line 433/442 of
  `backend/dsa_catalog.py` and never read — the per-topic uniqueness counter this audit
  needed was never wired into the row. Fix: emit it as `duplicate_pattern_rank` on the row,
  or delete the two lines. VERIFIED by reading the function.

## 3. Ambiguity In The Prose-Only Drafts

Draft population VERIFIED: `build_dsa_question_bank()` returns 108 rows, 20 with
`gradable: true`, 88 with `gradable: false` (`spec_status: "draft"`). Selection of the 12 below
is my judgement over those 88 prompts (INFERRED); the "sentence to add" is the minimum text that
makes a reference solution unambiguous.

| # | Draft id | Current prompt's gap | The one sentence the spec author must add | Severity |
|---|---|---|---|---|
| A1 | `dsa_pointers_002_two-sum-ii-sorted-input` | Index base unstated; a reference returning 0-based fails every Indian candidate who learned the 1-based version | "Return the two **1-based** positions and guarantee exactly one valid pair exists." | MAJOR |
| A2 | `dsa_stack_005_next-greater-element` | "Next Greater Element" is used for two different problems (single-array vs query-over-a-second-array, and linear vs cyclic) | "Single-array version: for each index return the first strictly larger value to its right, or -1 if none; the array may contain duplicates and is not cyclic." | MAJOR |
| A3 | `dsa_backtrack_005_palindrome-partitioning` | "Partition a string so every part is a palindrome" does not say whether to enumerate or minimise — the II-variant asks for cut count | "Return **every** valid partitioning (not the minimum number of cuts); each part must be a non-empty palindrome and parts concatenate to the input exactly." | MAJOR |
| A4 | `dsa_dp_011_decode-ways` | Zero handling unstated — this single rule decides the answer for `'30'`, `'06'`, `'10'`, `'100'` | "A decoding is a partition into segments each mapping to 1..26, so any segment with a leading zero is invalid and `'06'` contributes 0 ways; return the count as an int with `'0'` -> 0." | MAJOR |
| A5 | `dsa_bits_006_reverse-integer` | "returning zero on overflow" leaves the width and the sign convention unstated | "Assume a 32-bit signed environment: if the reversed value falls outside [-2^31, 2^31-1] return 0, sign is preserved (`-123` -> `-321`), and leading zeros vanish (`120` -> `21`)." | MAJOR |
| A6 | `dsa_graphs_009_word-ladder` | "shortest transformation sequence" is ambiguous between word count and edge count, and the no-path sentinel is unstated | "Return the number of **words** in the chain including `beginWord` and `endWord`, or 0 if `endWord` is not in the dictionary or is unreachable; each step changes exactly one character and every intermediate word must be in the dictionary." | MAJOR |
| A7 | `dsa_bits_005_pow-x-n` | Float answer graded by an `exact` checker (all 20 shipped specs use `checker: "exact"` — VERIFIED) cannot pass; negative `n` and `0^0` undefined | "Compare with relative tolerance 1e-6; `n` may be negative (return `1/x**-n`), `0^0` returns 1, and `|result|` is guaranteed to fit a double." | BLOCKER |
| A8 | `dsa_heaps_002_top-k-frequent-elements` | Tie-breaking unstated, and an order-insensitive comparison is required — which the current checker set does not provide | "Return the k most frequent values; ties in frequency may be broken either way, so any permutation of the correct set is accepted and grading must compare as a **set**." | BLOCKER |
| A9 | `dsa_trees_012_serialize-and-deserialize-binary-tree` | The prompt lets the candidate invent the format, so no external expected output can exist | "Grading is a round-trip, not a string: the submitted `serialize` and `deserialize` are executed as a pair and the test passes iff `deserialize(serialize(tree)) == tree` for every test tree, including the empty tree and single-child chains." | BLOCKER |
| A10 | `dsa_arrays_009_merge-sorted-array` | m/n ambiguity (initialised count vs total length) is *the* failure mode of this problem | "`nums1` has length `m + n`: `m` initialised elements followed by `n` zeros; `nums2` has length `n`; both sorted non-decreasing; mutate `nums1` in place and return nothing." | MAJOR |
| A11 | `dsa_dp_010_unique-paths` | "with obstacles absent" is a malformed constraint (it neither adds nor removes the obstacle case) and grid orientation is unstated | "`m` rows and `n` columns, moves restricted to one step down or one step right, no blocked cells, start `(0,0)` and end `(m-1,n-1)`; the exact count is required and fits 64-bit for `m, n <= 23`." | MAJOR |
| A12 | `dsa_backtrack_006_n-queens` | Count vs board enumeration, and the string rendering of a board, are both unspecified — the answer is not reproducible without them | "Return every distinct solution as `n` strings of length `n` built from `'Q'` and `'.'`, rows ordered top to bottom; the result is compared as a **set** of boards, and rotations or reflections count as separate solutions." | MAJOR |

### Second tier (one sentence each; fix before the topic is marketed)

`dsa_greedy_003_non-overlapping-intervals` (do intervals sharing an endpoint overlap? — say
"they do not, `[1,2]` and `[2,3]` can both be kept"), `dsa_greedy_004_meeting-rooms-ii` ("a
meeting ending at `t` does not conflict with one starting at `t`"),
`dsa_dp_005_longest-increasing-subsequence` ("strictly increasing, subsequence not substring,
return length only"), `dsa_dp_006_word-break` ("boolean only, not the sentence list; dictionary
words may be reused"), `dsa_dp_004_coin-change` ("unlimited quantity, `-1` when unreachable,
amount 0 -> 0"), `dsa_heaps_001_kth-largest-element-in-an-array` ("kth largest **including
duplicates**"), `dsa_graphs_004_rotting-oranges` ("-1 when any fresh orange is unreachable; one
rotten orange costs 0 minutes"), `dsa_graphs_010_network-delay-time` ("return the maximum
arrival time, or -1 if any node is unreachable"), `dsa_trees_004_balanced-binary-tree` (height
in nodes vs edges, and the empty tree is balanced),
`dsa_trees_010_kth-smallest-element-in-a-bst` (1-based k, distinct values),
`dsa_graphs_002_clone_graph` (labels 1..n, the clone must share no object with the original),
`dsa_stack_003_evaluate_reverse_polish_notation` (division truncates toward zero, `-7/2 = -3`).

- **A13 — BLOCKER.** A7, A8, A9 (and A12's set comparison) are not prose problems at all: they
  need grader *capability* the corpus does not currently use, since all 20 shipped specs are
  `checker: "exact"` (VERIFIED by aggregating the field). Whether `validate_dsa_specs.py`
  supports any other mode was **NOT CHECKED** — it was not executed in this audit. Fix: confirm
  or add `tolerance`, `set_equal` and `round_trip` checker modes before speccing anything in
  float-output, tie-broken, round-trip or enumeration territory, and record the decision in the
  next revision of this file.
- **A14 — MAJOR.** Across the 88 drafts the same three fields are systematically missing:
  input type/bounds, the output sentinel for "impossible" (`-1` vs `0` vs `[]` — all three
  appear in the bank, VERIFIED from the prompts), and the ordering/duplicate contract of list
  outputs. Fix: adopt a 4-field prompt template (`signature`, `constraints`, `output contract`,
  `impossible case`) and treat a draft as un-speccable until all four are present in prose.

## 4. Originality Risk

Pacio's position, restated so the findings are legible: **a problem idea is not protectable;
a specific expression of it is.** Titles of two to six words are generally not copyrightable,
but invented *scenarios* (a named character, a fruit, an ocean, a course catalogue) and the
sentence shape that carries them are expression. Severity here is product/legal exposure, not
code quality.

Everything in this section is **INFERRED**. I compared titles and prompts against my own memory
of the public problem canon; I fetched **no** third-party site and ran no similarity check, so
the "verbatim" counts below are an estimate a human must confirm. What I *did* verify is the
claim Pacio's own code makes about itself.

- **O1 — BLOCKER (self-inflicted, and the only originality finding I can prove).**
  `backend/dsa_catalog.py` lines 1-13 state: "an independently authored, pattern-based
  curriculum ... no third-party problem sheet, its section structure or its question list is
  reproduced." Rows additionally carry `source: "internal_curriculum"` and
  `sheet: "pacio_curriculum"`, and every shipped spec carries `provenance: "original"` or
  `origin: "original_pacio_authoring"` with `source_urls: []` (VERIFIED — 20/20 specs assert
  originality, 0 assert a source). My memory-based comparison says roughly 105 of 108 titles
  match a public LeetCode title string and about 105 carry that site's difficulty label
  (INFERRED — NOT machine-checked). A blanket "nothing is reproduced" assertion sitting next to
  a near one-to-one title/difficulty correspondence is the weakest possible posture: it is a
  claim the reader can falsify in thirty seconds, and it is *not* what the law cares about.
  **Fix:** replace the docstring assertion with the accurate one — "problem ideas follow the
  public canon; every statement, pattern label, ordering and `why_it_matters` note here is
  Pacio's own restatement; titles are retained because candidates search by them" — and add a
  per-problem `canonical_alias` / `inspired_by` field so provenance is recorded rather than
  asserted. This raises protection, it does not lower it.
- **O2 — BLOCKER (and it gates the fix in O3).** `question_id` is derived from the title:
  `f"dsa_{topic}_{index:03d}_{slug[:48].rstrip('-')}"` where `slug = _slug(title)` (VERIFIED,
  lines 436-439). Re-wording any title therefore mints a new id and **orphans the 20 validated
  specs plus every stored student attempt keyed on the old id**. The two safe moves: (a) break
  the coupling now — make `question_id` a stable `dsa_{topic}_{index:03d}` and keep the slug as
  display metadata — then re-word freely; (b) never re-word, only re-word the *statement*. Do
  (a) first; it is a one-line change plus a migration of 20 spec keys, and it must be scheduled
  before any copy edit in O3/O5.
- **O3 — MAJOR. Re-word these 12 (invented scenario or invented framing, not a generic
  problem name):**

  | Id | Current title | Why it reads as copied | Safe re-wording (keep the id) |
  |---|---|---|---|
  | `dsa_binsearch_006_koko-eating-bananas` | Koko Eating Bananas | A named character + bananas + piles + an hours bound is one site's fiction, and the prompt keeps all four elements | "Minimum Worker Rate" / "Deadline-Bounded Batch Consumption" |
  | `dsa_stack_007_asteroid-collision` | Asteroid Collision | Sign-encoded integer bodies moving left/right is an invented conceit, and the prompt leans on it | "Opposing Packet Sweep" |
  | `dsa_graphs_004_rotting-oranges` | Rotting Oranges | Fruit-rot minutes is an invented scenario; the multi-source BFS idea is free | "Infection Spread in a Grid" |
  | `dsa_graphs_005_pacific-atlantic-water-flow` | Pacific Atlantic Water Flow | Naming two specific oceans as the borders is the expression | "Two-Border Reachability" |
  | `dsa_graphs_006_course-schedule` + `dsa_graphs_007_course-schedule-ii` | Course Schedule I/II | A course-and-prerequisite catalogue with an `n`-course frame | "Prerequisite Feasibility" / "Prerequisite Order" |
  | `dsa_greedy_004_meeting-rooms-ii` | Meeting Rooms II | The `II` suffix is a third party's numbering scheme, which also implies a part I Pacio does not have | "Minimum Concurrent Resources" |
  | `dsa_heaps_006_task_scheduler` | Task Scheduler | Cooled identical tasks on a unit-time grid | "Cooled Job Dispatch" |
  | `dsa_binsearch_007_capacity-to-ship-packages-within-d-days` | (verbatim public title) | The whole title string, including the `D days` framing, is the other side's wording | "Batch Limit for Deadline Scheduling" |
  | `dsa_graphs_010_network-delay-time` | Network Delay Time | Invented signal-propagation framing; the prompt "how long a signal takes to reach every node" mirrors the source sentence | "Broadcast Completion Time" |
  | `dsa_linked_008_copy-list-with-random-pointer` | Copy List with Random Pointer | "Random pointer" is a coined node type from one catalogue | "Deep-Copy a List With an Extra Edge" |
  | `dsa_stack_008_decode-string` | Decode String | The title is generic, but the prompt embeds the literal example `3[a2[c]]`, which is a specific expression | Keep the title; replace the example with Pacio's own (e.g. `2[x3[y]]`) and write the sentence fresh |
  | `dsa_heaps_005_find-median-from-data-stream` | Find Median from Data Stream | The `class MedianFinder` design framing is one site's; the two-heap idea is free | "Running Median Queries" (and state the API in Pacio's own terms) |

- **O4 — MAJOR. Re-word the statement, not the title, for these 8 prompts whose sentence shape
  tracks a specific source:** `dsa_arrays_010_find-all-duplicates-in-an-array` ("values lie in
  1..n" is the source's distinctive constraint phrasing — and it is exactly the ambiguity A1
  family), `dsa_pointers_004_container-with-most-water` ("two lines that, with the x-axis, hold
  the most water"), `dsa_stack_004_daily-temperatures` ("how many days until a warmer
  temperature"), `dsa_trees_012_serialize-and-deserialize-binary-tree` ("an encoding that
  round-trips"), `dsa_dp_012_target-sum` ("assign plus or minus signs to reach a target"),
  `dsa_greedy_008_partition-labels` ("each letter appears in at most one part"),
  `dsa_backtrack_007_letter-combinations-of-a-phone-number` (title + keypad mapping framing),
  `dsa_dp_006_word-break` ("segmented into dictionary words"). Each is one rewrite, no id
  change, no spec breakage.
- **O5 — MINOR.** ~90 remaining titles are short, descriptive and individually unprotectable
  ("Reverse Linked List", "Two Sum", "Coin Change"). Retaining them is defensible **as search
  keys** — but only once O1's overreach is removed and O6's provenance field exists. The
  aggregate impression ("this is somebody's list") is diluted by the ordering, which is *not*
  the ordering of the two most circulated community lists (INFERRED — the sequence of ARRAYS
  001-012 does not follow the community grouping), so re-publishing a pattern-first topic order
  and the existing `why_it_matters` notes is the cheapest mitigation.
- **O6 — MAJOR.** Provenance is not machine-readable in the artefact that is supposed to carry
  it: `dsa_specs.json` mixes two shapes for the same fields — 10 specs use `provenance:
  "original"` (bare string) and 10 use a dict with `origin`/`source_urls`/`notes`; 10 use
  `authoring.reviewer: "pending"` and 10 use `"qoder-lead"` (VERIFIED by counting field
  values). Consequences: (a) a rights query cannot be answered from the file, (b) **no spec has
  a human reviewer** — "pending" or an agent role, never a named person, so nothing in the
  catalogue can honestly be called human-reviewed, (c) the same 10/10 split is also the
  spec-authoring batch boundary, i.e. the file is two schema generations glued together. Fix:
  one normalisation pass, make `provenance` and `reviewer` required in the validator, and never
  let `reviewer: "pending"` count as reviewed.
- **O7 — MINOR.** `CURRICULUM_VERSION = "2026.10-pattern-v1"` is a single global string; the
  `why_it_matters` field is the only per-item editorial voice that is unambiguously Pacio's.
  Fix: treat `why_it_matters` as the protectable layer and require it in every new spec — do not
  let a spec-automation pass genericise it.

## 5. Minimum Honest Claim Pacio Can Make Today

Numbers below are VERIFIED from `build_dsa_question_bank()` and from the field values of
`backend/dsa_specs.json`. The claim "each spec passes its reference solution and rejects a
mutant" is **asserted by `backend/tests/test_dsa_specs.py`, which I read but did not run** — so
in this audit it is NOT CHECKED, and Pacio may not repeat it externally until someone runs
`pytest backend/tests/test_dsa_specs.py` and records the output.

**Defensible today (say exactly this):**

> Pacio's DSA curriculum is a 108-problem pattern bank across 12 topics, authored as original
> prose statements with pattern, difficulty and rationale for every item. **20 of the 108 have a
> machine-executable specification** — an input signature, constraints, worked examples, 4 to 7
> hidden tests, a reference solution and a deliberate wrong solution used to prove the tests have
> teeth. The remaining **88 are curated problem statements a coach can assign and grade by hand,
> not auto-graded items.** We do not claim adaptive difficulty, a validated score, or coverage of
> the full bank by automated grading.

**What may NOT be said, and why:**

- **"108 auto-graded / machine-validated problems" or any progress bar implying it.** VERIFIED:
  `gradable` is `True` for 20 rows and `False` for 88. `test_dsa_specs.py` even encodes the
  guard ("the product must not imply the full bank is gradable while drafts exist").
- **"12 topics with validated coverage."** VERIFIED: HEAPS, GRAPHS and BACKTRACK have **0 of 24**
  gradable items, and DP has 1 of 12 — the three topics that decide a campus screen have no
  machine-graded entry at all. Any per-topic "coverage" or "readiness" score computed off the
  bank is currently measuring prose, not validation.
- **"Human-reviewed curriculum."** VERIFIED: 10 of 20 specs say `reviewer: "pending"`, the other
  10 say `reviewer: "qoder-lead"` (an agent role). No human review exists in the artefact. I also
  performed no human review in this audit and ran no tests.
- **"84% of the bank is ready to serve."** Wrong denominator — 20/108 is 18.5% gradable, and the
  per-topic split is 2/12, 2/10, 1/8, 1/8, 7/8, 4/12, 0/6, 0/10, 0/8, 1/12, 1/8, 1/6.
- **Any difficulty-based ranking or "MHRD-style" percentile.** Difficulty labels are one
  author's per-item opinion with no distribution control (VERIFIED that the labels are only the
  three strings Easy/Medium/Hard; no rubric for *why* an item is Hard exists anywhere in the file),
  and 4 topics contain zero Easy items (Section 1, C3).

**Two structural defects that make even the 20/108 claim fragile (both VERIFIED in code):**

- **H1 — MAJOR, fail-silent.** `_validated_spec_ids()` catches `OSError, ValueError, KeyError,
  TypeError` and returns `set()` (lines 413-417). A missing, truncated or malformed
  `dsa_specs.json` therefore does not raise — every problem silently flips to draft and the
  product degrades to a 0-gradable bank with no signal in logs or health checks. Worse, a
  partially-valid JSON that still parses but has dropped entries degrades silently too. Fix: let
  the load failure raise, or return `None` and have `build_dsa_question_bank()` assert that the
  spec count matches the last-known floor (e.g. `>= 20`) before serving.
- **H2 — MAJOR, gradable is presence, not proof.** The gradable flag is membership of a set of
  `question_id`s read from a JSON file; the *proof* that each spec is executable lives entirely
  in the test suite. So `gradable: true` in the database means "a file contained this id at
  import time", and `dsa_catalog.py` runs its `assert DSA_TOTAL == 108` at import. Fix: have the
  validator write a `spec_digest` (spec count + last green test run id) into the bank row and
  have the API expose it, so a claim about gradability is traceable to an executed test run
  rather than to file existence.
- **H3 — MINOR.** `assert DSA_TOTAL == 108` and `assert len(DSA_TOPICS) == 12` are hard-coded
  magic numbers at module scope (lines 405-406). Adding the 10 problems recommended in Section 6
  crashes every import of the backend until the constant is edited, which in practice means the
  bank and the assertion drift or a reviewer deletes a problem instead of adding one. Fix: derive
  the expected total from a `CATALOGUE_SIZE` constant declared next to `CURRICULUM_VERSION`, or
  assert only the invariant that matters (every topic non-empty, every id unique).
- **H4 — MINOR.** All 20 specs use `checker: "exact"` and 9 of them ship only 4 hidden tests
  (VERIFIED). A "machine-validated" label over 4 hand-written cases plus 1 hand-written mutant is
  thin — there is no differential/fuzz comparison against a brute-force reference. Fix: add a
  `random_small_cases` generator in `validate_dsa_specs.py` that cross-checks the reference
  against a brute-force solver for n <= 8; this converts 20 weak specs into 20 strong ones
  without writing 120 new cases by hand.

## 6. The Next 10 To Spec

Selection rule, in order: (1) unblock a topic sitting at 0 gradable items, (2) highest INFERRED
campus-hiring frequency, (3) scalar or deterministically-ordered output so today's
`checker: "exact"` works with no harness change (A13), (4) reuse of runner infrastructure that
already exists. This is a sequencing recommendation, not measured demand — no attempt data was
available to me.

| Rank | Id | Topic (graded now) | Reason | Grader cost | Prerequisite |
|---|---|---|---|---|---|
| 1 | `dsa_graphs_001_number-of-islands` | GRAPHS (0/10) | The single most-asked graph question in Indian campus rounds; takes GRAPHS off zero, which is the largest credibility gap in the bank (C2) | Low — `grid: list[str] -> int`, exact | None |
| 2 | `dsa_heaps_001_kth-largest-element-in-an-array` | HEAPS (0/6) | Takes HEAPS off zero; scalar int output; also the entry point the topic lacks (no Easy exists — C3). Spec it as `k, nums -> int`, duplicates included (A-heaps sentence) | Low | State "including duplicates" first |
| 3 | `dsa_backtrack_001_subsets` | BACKTRACK (0/8) | Takes the last zero-topic off zero. The template problem for the whole family, so one spec unlocks 002/003/007/008 later | Medium | **Must define output order** ("in the order produced by include-then-exclude DFS from index 0") so `exact` grading stays legal instead of waiting for a `set_equal` checker |
| 4 | `dsa_dp_004_coin-change` | DP (1/12) | DP carries 12 problems and one gradable warm-up (Climbing Stairs). Int output with a `-1` sentinel; unbounded-knapsack reference is 6 lines; mutant is natural (0/1 vs unbounded loop order) | Low | Fix the amount-0 and unreachable rules (Section 3 tier 2) |
| 5 | `dsa_stack_004_daily-temperatures` | STACK (1/8) | Canonical monotonic stack, array-of-int output. Spec it **instead of** `dsa_stack_005_next-greater-element`, so D3's duplicate is retired by the same commit | Low | D3 decision |
| 6 | `dsa_binsearch_004_search-in-rotated-sorted-array` | BINSEARCH (1/8) | Very high campus frequency and the best edge-case stress test in the bank (1-element, target at pivot, boundaries) — it hardens the runner for every later search problem | Low | None |
| 7 | `dsa_arrays_004_product-of-array-except-self` | ARRAYS (2/12) | Ubiquitous on Indian lists; the "without division" constraint is a natural mutant (`prefix` only, or division on a zero array) so the spec has real teeth | Low | State no-division enforcement vs output-only grading |
| 8 | `dsa_trees_010_kth-smallest-element-in-a-bst` | TREES (4/12) | Cheapest marginal cost in this list: 4 tree specs already exist, so the level-order-with-nulls encoding and the tree comparison helper are built — 1-based k, distinct values | **Lowest** (infra reuse) | None |
| 9 | `dsa_greedy_005_jump_game` | GREEDY (1/8) | Boolean output — the fastest spec to write and validate; lifts GREEDY and gives the topic an entry point once paired with a re-labelled Easy | Very low | Decide the n=1 rule |
| 10 | `dsa_dp_007_longest-common-subsequence` | DP (1/12) | Second DP item and the gateway to Edit Distance (008) and every 2-D table spec; int output; the O(nm) grid mutant space is broad, so tests with teeth are easy to prove | Medium | None |

**Deliberately not in the ten:** `dsa_bits_005_pow-x-n` (A7 — float output against an `exact`
checker), `dsa_heaps_002_top-k-frequent-elements` (A8 — tie sets),
`dsa_trees_012_serialize-and-deserialize-binary-tree` (A9 — self-defined format needs a
round-trip runner), `dsa_backtrack_006_n-queens` (A12 — board sets), `dsa_dp_008_edit_distance`
(Hard, and lower campus frequency than 007 at the same spec cost).

- **S1 — MAJOR.** Ranks 1-3 alone move gradable from 20/108 to 23/108 *and* change the honest
  sentence from "three of the deciding topics have zero validated items" to "none do". That
  narrative change is worth more than the raw percentage. Fix: ship 1-3 as one release with the
  Section 5 wording updated in the same commit.
- **S2 — MAJOR.** Four of the ten (ranks 5, 7 in particular, plus 2 and 9) should be written
  **after** the duplicate decisions in Section 2, or Pacio pays spec cost twice on items it
  intends to retire. Fix: resolve D3, D4, D5, D7 before starting rank 5.
- **S3 — MINOR.** Nothing in this list touches the two BLOCKER coverage gaps (number theory,
  weighted graphs/MST). The bank stays mis-shaped for Indian campus hiring even at 30/108
  gradable. Fix: schedule the C1 `MATHS` topic and the C4 MST/bounded-shortest-path items
  immediately after rank 10, and spec them straight away rather than drafting them.

## Summary

**48 findings: 8 BLOCKER, 28 MAJOR, 12 MINOR.**

| Section | BLOCKER | MAJOR | MINOR | Evidence label |
|---|---|---|---|---|
| 1 Coverage (C1-C9) | 2 | 4 | 3 | counts VERIFIED; frequency gaps INFERRED |
| 2 Duplication (D1-D9, T1-T2) | 0 | 7 | 4 | ids/pattern strings VERIFIED; "same trick" INFERRED |
| 3 Ambiguity (A1-A14) | 4 | 10 | 0 | draft set VERIFIED; selection and fixes are judgement |
| 4 Originality (O1-O7) | 2 | 3 | 2 | Pacio's own claims VERIFIED; third-party match INFERRED, NOT machine-checked |
| 5 Honest claim (H1-H4) | 0 | 2 | 2 | VERIFIED from code and spec fields |
| 6 Roadmap (S1-S3) | 0 | 2 | 1 | sequencing judgement |
| **Total** | **8** | **28** | **12** | |

**Top 5.**

1. **O1 + O2 (BLOCKER) — the provenance claim is the sharpest liability, and the schema blocks
   fixing it.** The module docstring asserts nothing third-party is reproduced and every spec
   declares `provenance: "original"` with `source_urls: []`, while ~105 of 108 titles (and
   almost all difficulty labels) coincide with a public catalogue (INFERRED — no site was
   fetched). Simultaneously `question_id` is derived from the title slug, so any re-wording
   silently orphans the 20 shipped specs and every stored attempt. Fix order matters: decouple id
   from title first, then re-word the 12 in O3 and the 8 statements in O4, then replace the
   docstring assertion with the accurate narrower one. Ideas are free; expression is not; an
   over-broad "we wrote it all" claim is worth less than a precise "canon ideas, our wording".
2. **C2 (BLOCKER) — the three topics that decide a campus screen have zero validated items.**
   HEAPS 0/6, GRAPHS 0/10, BACKTRACK 0/8 = 24 curated problems, 0 specs; DP is 1/12. Gradable
   coverage instead concentrates in LINKED (7/8), the topic with the most deterministic output.
   Any readiness or coverage score computed per topic today measures prose, not validation.
   Ranks 1-3 of Section 6 close this specific gap.
3. **C1 (BLOCKER) — BITS is named "Bit Manipulation & Maths" and contains no maths.** No GCD/LCM,
   sieve, primality, modular arithmetic or combinatorics — the highest-volume family in Indian
   campus written rounds and the one guaranteed by every Indian CS syllabus. Rename the topic,
   add a `MATHS` topic, and update the hard-coded `DSA_TOTAL == 108`.
4. **A13 + H2 (BLOCKER/MAJOR) — the grader, not the prose, caps the roadmap.** All 20 specs use
   `checker: "exact"` and 9 ship only 4 hidden tests; `gradable` means "an id existed in a JSON
   file at import time", with the actual proof living in a test suite that **I did not run**.
   Float-output, tie-broken, set-output and round-trip problems are therefore unspeccable today,
   and `_validated_spec_ids()` swallows load errors so a corrupt spec file silently degrades the
   whole bank to draft.
5. **C3 + C5 + C6 (MAJOR) — the shape is wrong as well as thin.** 21% Easy overall and **4 of 12
   topics with no Easy at all** (HEAPS, GRAPHS, BACKTRACK, GREEDY); 10 of 12 DP items are 1-D or
   string tables with a single obstacle-free grid; the string-hashing canon (Group Anagrams, Valid
   Anagram, Majority Element, Sort Colors) is absent while five near-identical window problems and
   six duplicate clusters (D1-D5, D8) pad the same topics. 108 -> 102 with 6 freed slots aimed at
   the C1-C9 gaps is a better bank than 108.

**Also note (MAJOR, O6):** no spec in the catalogue has a human reviewer — 10 of 20 say
`reviewer: "pending"`, 10 say `"qoder-lead"` (an agent role) — and `dsa_specs.json` carries two
different schemas for `provenance`/`authoring`, so rights evidence is not machine-readable.

**Honesty boundary of this audit.** Counts, ids, difficulty labels, spec field values, checker
modes, reviewer values, dead code and the silent-failure path were read from code or computed by
executing the two snippets in Section 0. **No test suite was run** (`pytest` was not executed),
**no human review was performed**, **no third-party problem site was fetched or diffed**, and no
Pacio attempt/usage data was consulted. Coverage-frequency and originality judgements are labelled
INFERRED throughout and need a human pass before any copy change ships. The only file created or
modified by this audit is `docs/data/DSA_CATALOGUE_AUDIT.md`.
