# DSA Originality Check — External Verification of the "108 ORIGINAL Problems" Claim

Scope: `backend/dsa_catalog.py` (`PROBLEMS`), 12 topics, 108 problems (VERIFIED by execution:
`N 108 TOPICS 12`).
Question under test: an internal audit asserted "~105 of 108 titles and difficulty labels
coincide with a public catalogue" **without fetching any external source**. This check
fetches real public catalogues and measures overlap in three separate dimensions.
Legal frame tested: problem *ideas* and *standard names* are not protectable; specific
*expression* is.
Evidence labels: **VERIFIED** = produced by fetched data or executed code. **INFERRED** =
depends on my own normalisation/judgement or on a source I did not fetch.

## 0. The claim as shipped (where it appears)

| Location | Wording |
|---|---|
| `backend/dsa_catalog.py:1` | "Original DSA interview curriculum for Pacio Campus Intelligence." |
| `README.md:82`, `docs/ARCHITECTURE.md:34` | original 12-topic / 108-problem curriculum |
| `FEATURE_GUIDE_FOR_JUDGES.md:76` | "curated 12-topic / 108-problem interview curriculum (original prompts and rationale)" |
| `docs/audit/PACIO_BACKLOG.md:37` (BL-26, DONE) | "DSA curriculum mirrored takeUforward's A2Z structure ... Replaced with an original ... curriculum. No third-party sheet content remains." |
| `docs/audit/PACIO_AUDIT.md:126` (F-19) | "reproduced a third-party sheet's structure **and titles**" → "original prompts, rationale and ordering" |
| `docs/GIT_REPORT.md:28` | commit `b5a4754` "Replace the third-party DSA sheet with the original ... curriculum" |

## 1. Sources attempted

| Source | URL | Retrievable? | Method | Date |
|---|---|---|---|---|
| Striver A2Z — canonical takeuforward page | `https://takeuforward.org/strivers-a2z-dsa-course/strivers-a2z-dsa-course-sheet-2-0/` | **NO** — HTTP 404 on that path; not retried (1 attempt). **takeuforward.org itself was never successfully read**, so all A2Z evidence below comes through a third-party mirror. | WebFetch | 2026-10-30 |
| Striver A2Z — third-party mirror, section-grouped | `https://devsunite.com/resources/dsa-sheets/striver-a2z` | **YES** — parsed 433 problem titles + 22 section boundaries in document order | WebFetch, then curl HTML (200, 2.04 MB) + regex parse | 2026-10-30 |
| NeetCode 150 — community machine-readable export of the official list | `https://raw.githubusercontent.com/krmanik/Anki-NeetCode/main/neetcode-150-list.json` | **YES** — 18 groups, 150 problems, includes difficulty labels | curl 200, 37 KB | 2026-10-30 |
| NeetCode 150 — official site | `https://neetcode.io/roadmap` | **NO** — client-rendered; fetch returned CSS only. Replaced by the export above (mirror, not official). | WebFetch | 2026-10-30 |
| Blind 75 — `seanprashad/leetcode-patterns` README | `https://raw.githubusercontent.com/seanprashad/leetcode-patterns/main/README.md` | **PARTIAL** — 200 but the README no longer contains the question list (prose + TOC only; 0 titles). | curl 200, 4.5 KB | 2026-10-30 |
| Blind 75 — same repo's data file | `https://raw.githubusercontent.com/seanprashad/leetcode-patterns/main/src/data/questions.json` | **YES** — 179 question objects with `title`, `difficulty`, `pattern[]` | curl 200, 162 KB | 2026-10-30 |
| LeetCode problem statements / GeeksforGeeks | — | **NOT ATTEMPTED** — would mean pulling full problem prose (large dataset), out of scope per task rules. This is the main limitation of §3(c). | — | — |

Repo-internal provenance grep (`striver|takeuforward|neetcode|blind 75|grokking|leetcode`)
over `backend/`: **no matches** — shipped code carries no third-party sheet constant and no
attribution string. The "Striver topic constant" mentioned in the brief is **not present** in
`backend/` any more (consistent with commit `b5a4754`).

## 2. (a) TOPIC-LEVEL overlap

Pacio's groups, in order (VERIFIED):
`1 ARRAYS(12) · 2 POINTERS(10) · 3 BINSEARCH(8) · 4 STACK(8) · 5 LINKED(8) · 6 TREES(12) ·
7 HEAPS(6) · 8 GRAPHS(10) · 9 BACKTRACK(8) · 10 DP(12) · 11 GREEDY(8) · 12 BITS(6)`

| Compared with | Result |
|---|---|
| NeetCode 150 (18 groups) | **11 of 12** Pacio topics map onto exactly one NeetCode group family; the exception is POINTERS (4 Two Pointers + 4 Sliding Window) and ARRAYS (spread over 5 groups). Pacio **merges** Sliding Window→POINTERS, Intervals→GREEDY, 1-D+2-D DP→DP, Trees+BST→TREES, and **drops** Tries, Advanced Graphs, Math & Geometry, Strings, Sorting, Recursion, LL-design. Not a copy of the 18-group structure. |
| Striver A2Z (22 sections) | A2Z's section order is Basics→Maths→Recursion→Hashing→STL→Logic→Sorting→**Arrays**→**Binary Search**→Strings→**LinkedList**→Bit→Adv Maths→**Stack**→Sliding Window→**Heaps**→Greedy→**Trees**→BST→**Graphs**→DP→Trie. Pacio interleaves differently (STACK before LINKED; GREEDY *after* DP; BITS last, whereas A2Z has Bit in the middle and DP last). |
| **Order concordance** (how many matched problems appear in the same relative order as the source — longest monotone subsequence over the matched titles, computed by script) | vs NeetCode 150: **14 of 91 matched titles (15%)**. vs A2Z: **5 of 26 (19%)**. |

**Topic-level verdict: the 12-group structure is Pacio's own regrouping, not a reproduction
of either catalogue's section list or sequence** (VERIFIED against both source structures;
the LIS score is INFERRED as a metric choice).

## 3. (b) TITLE-LEVEL overlap

Normalisation: lowercase, Unicode-fold, all non-alphanumerics to single spaces, bracketed
qualifiers stripped (e.g. `Two Sum II (Sorted Input)` → `two sum ii`). "Verbatim" below means
equal after this normalisation.

| Source | Titles matched (exact-normalised) | Label |
|---|---|---|
| NeetCode 150 (150) | **91 / 108** | VERIFIED |
| Blind 75 list (179 items) | **79 / 108** | INFERRED — required my `loose()` variant (see borderline note below) |
| Striver A2Z (433) | **35 / 108** | VERIFIED |
| **Any of the three** | **95 / 108** | VERIFIED (exact-normalised) |
| **In none of the three** | **13 / 108** | VERIFIED |
| Titles invented by Pacio | **0 / 108** | INFERRED (every title maps to a recognisable LeetCode problem) |

**Difficulty labels:** of the 91 NeetCode-matched titles, **90 agree and 1 differs** —
`Edit Distance` (Pacio `Hard`, NeetCode export `Medium`; LeetCode's own label is Hard, so
Pacio matches LeetCode rather than the export). VERIFIED against that export. This corroborates
the auditor's difficulty claim — but note *why* it agrees: both sides read the same canonical
LeetCode label, not because one copied the other.

**Generic-name classification.** Definition used: a title is a *generic industry-standard name*
if it appears verbatim in ≥1 fetched mainstream catalogue (all three catalogues themselves use
LeetCode-canonical titles, so a verbatim hit proves the name is not Pacio's coinage).
→ **91 of 108 (84%) are generic names used verbatim; the remaining 17 are still generic names
in shortened/re-phrased form, so effectively 108 of 108 are standard names.** 0 are proprietary
or idiosyncratic sheet phrasings.

The 13 titles matching **none** of the sources verbatim, and what they are (all are
LeetCode-canonical problems under a **compressed** name — evidence of deliberate renaming, not
of original problems):

| Pacio title | Canonical form it compresses | Classified as |
|---|---|---|
| Rotate Array | LeetCode 189 "Rotate Array" — absent from NeetCode150/A2Z lists as worded | generic, list-absent |
| Move Zeroes | LC 283 | generic, list-absent |
| Merge Sorted Array | LC 88 | generic, list-absent |
| Find All Duplicates in an Array | LC 442 | generic, list-absent |
| Two Sum II (Sorted Input) | LC 167 "Two Sum II - Input Array Is Sorted" | **INFERRED** shortening by me |
| Find All Anagrams in a String | LC 438 | generic, list-absent |
| First and Last Position of a Target | LC 34 "Find First and Last Position of Element in Sorted Array" | **INFERRED** shortening |
| Decode String | LC 394 | generic, list-absent |
| Remove Nth Node From End | LC 19 "Remove Nth Node From End of List" | **INFERRED** shortening |
| Linked List Cycle II | LC 142 (present in A2Z as "Find the starting point in LL") | naming-variant miss |
| Lowest Common Ancestor of a BST | LC 235 "...of a Binary Search Tree" | **INFERRED** shortening |
| Construct Binary Tree from Preorder and Inorder | LC 105 "...Inorder Traversal" | **INFERRED** shortening |
| Number of Connected Components | LC 323 | generic, list-absent |

Borderline handling, stated explicitly: (i) a *loose* normaliser that also strips connective
and data-structure words (`a`, `the`, `of`, `binary`, `tree`, `list`) was tried to catch
re-phrasings; it **under-counted A2Z (28 < 35)** because it collapses distinct names, so I
report it only as the Blind 75 method (79/108) and label those figures INFERRED rather than
treating them as a cleaner measure. (ii) Titles that exist in a source but under Striver's own
wording (`Stock Buy and Sell` vs `Best Time to Buy and Sell Stock`, `2Sum Problem` vs `Two Sum`,
`Reverse a LinkedList [Iterative]` vs `Reverse Linked List`, `Number of provinces` vs
`Number of Connected Components`) are counted as **non-matches** for A2Z — which is exactly why
A2Z scores 35 while NeetCode scores 91.

## 4. (c) PROMPT / EXPRESSION-LEVEL overlap

What was tested: the tuple fields `prompt` (index 3) and `why` (index 4) — the full strings.
Measured (VERIFIED): **max 162 chars, mean 106 chars** across all 108 — each is one task
sentence plus one one-sentence rationale. There is no tutorial prose in the catalogue.

Method: (1) print all 8 sampled strings in full; (2) mechanically, extract every distinct
**6-gram** from all 108 prompt+why strings (**1,283** of them) and search each verbatim
(punctuation-insensitive) through the fetched source text — 2 MB A2Z page text, the NeetCode
JSON, the Blind 75 README and the Blind 75 questions JSON.

**Result: 1 of 1,283 6-grams appears in any fetched source** —
`"connected components in an undirected graph"`.

| # | Topic / Title (title NOT generic-listed) | Full `prompt` | Full `why` | Phrases searched | Shared expression found? |
|---|---|---|---|---|---|
| 1 | ARRAYS / Rotate Array | "Rotate an array to the right by k steps in place." | "In-place transformation with O(1) extra space." | all 6-grams of both strings vs A2Z + NC150 + B75 | NONE |
| 2 | POINTERS / Two Sum II (Sorted Input) | "Find two values in a sorted array that add up to a target." | "Shows why sorted order converts a search into a linear scan." | idem | NONE |
| 3 | BINSEARCH / Search Insert Position | "Return the index where a value should be inserted in a sorted array." | "The lower-bound template reused everywhere." | idem | NONE |
| 4 | STACK / Next Greater Element | "For each element, find the next element to its right that is larger." | "Index bookkeeping inside a decreasing stack." | idem | NONE |
| 5 | LINKED / Remove Nth Node From End | "Remove the nth node from the end of a list in one pass." | "Two pointers separated by a fixed gap." | idem | NONE |
| 6 | TREES / Lowest Common Ancestor of a BST | "Find the lowest common ancestor of two nodes in a BST." | "Using the ordering invariant instead of searching both subtrees." | idem | NONE |
| 7 | GRAPHS / Number of Connected Components | "Count connected components in an undirected graph." | "Disjoint sets with path compression." | idem | **1 hit**: `connected components in an undirected graph` — present in A2Z text, NC export and B75 JSON. It is the stock problem-statement sentence for LC 323 (**INFERRED**: LeetCode page not fetched). Unprotectable scènes à faire / merger language, but it is the one string to re-word. |
| 8 | ARRAYS / Move Zeroes | "Move all zeroes to the end while preserving the order of non-zero values." | "Two-pointer compaction that appears inside many streaming problems." | idem | NONE |

**Power limitation, stated plainly:** every source retrieved here is a **title list**, so §4(c)
is a *negative* test against title-level and UI text only. Prompt-vs-prompt comparison against
the actual prose of the candidate parents (LeetCode problem statements, takeuforward's own
solution pages, GfG articles) was **not performed** and cannot be concluded from this run.
What the run *does* establish: Pacio's prompts are short original-compression sentences that
share no distinctive multi-word phrasing with any fetched sheet, and no sheet prose was copied.

## 5. Verdict

### GENERIC-NAMING COINCIDENCE ONLY

Why this and not another option:
- **Not "NO EVIDENCE OF COPYING"** — overlap is real and large at the level of titles and
  difficulty labels (91/108 verbatim, 90/91 difficulty agreement). Pretending otherwise would
  understate the measured facts.
- **Not "SUBSTANTIAL DERIVATION DETECTED"** — derivation would require copying protected
  *selection/structure* or *expression*. Structure is Pacio's own 12-group regrouping with
  15–19% order concordance (§2), and expression overlap is 1/1,283 6-grams of stock
  problem-statement language (§4). What overlaps — problem ideas and canonical names — is the
  unprotectable layer.
- The auditor's "~105 of 108 coincide with a public catalogue" is **directionally supported**
  (91 verbatim vs NeetCode 150; 95 vs any source) but **mis-attributed**: the catalogue Pacio
  coincides with is the **LeetCode canonical title set** (as mirrored by NeetCode 150 / Blind 75),
  **not takeUforward's A2Z**, which scores only 35/108 under the same method.

Confidence: **MODERATE**. Title/difficulty/structure findings are VERIFIED against two live
catalogues plus one mirror. Expression finding is VERIFIED but low-powered (title-list sources
only; takeuforward.org itself unreachable).

**Would RAISE confidence (toward "substantial derivation"):** a prose-level diff of the 108
prompts against LeetCode 323/189/283-class problem statements and takeuforward solution pages;
retrieving takeuforward.org's A2Z sheet directly (404 today) and re-running §3(b) on the
canonical sheet rather than a mirror; a git-history diff of commit `b5a4754` showing how far the
pre-replacement (474-question) catalogue was from the current one; the same test against
GfG / "Cracking the Coding Interview" / Grokking-style lists.
**Would LOWER confidence (toward "no evidence"):** a source-independent difficulty ground truth
(LeetCode's own labels) confirming the 90/91 agreement is convergence on one upstream table
rather than a shared copy; demonstrating that the 13 shortened titles were renamed for UX length
(evidence already in `dsa_specs.json` / audit notes would settle this).

## 6. Recommended action

1. **Do not sell "108 ORIGINAL problems" as a differentiator in its current wording.** The
   selection is not original (0/108 invented problems, 91/108 canonical titles). Re-word the
   claim — in `backend/dsa_catalog.py:1`, `README.md:82`, `docs/ARCHITECTURE.md:34`,
   `FEATURE_GUIDE_FOR_JUDGES.md:76` — to something the evidence supports:
   *"108 curated canonical interview problems, re-organised into a 12-topic pattern taxonomy,
   with prompts and rationale written in-house."* Originality should attach to **expression and
   structure**, which is where the evidence actually holds.
2. **Re-word exactly 1 prompt now** (#7, `Number of Connected Components`) — it is the only
   string sharing verbatim multi-word expression with the sources. Low cost, removes the single
   traceable string.
3. **Before any further re-wording, decouple `question_id` from the title.** VERIFIED:
   `backend/dsa_catalog.py:437-453` builds `question_id = f"dsa_{topic_code}_{index:03d}_{slug[:48]}"`
   from `_slug(title)`, and `SPEC_STATES` / attempt history key off it (`dsa_catalog.py:429`,
   `backend/tests/test_dsa_specs.py:19`). Renaming a title silently mints a new ID and orphans
   every stored attempt/spec. Introduce a stable surrogate ID first, then re-word.
4. **Add a provenance note** to `docs/DATA_SOURCES.md` / `DATA_PROVENANCE.csv`: titles and
   difficulty labels are LeetCode-canonical (unprotectable ideas/names); coverage was cross-checked
   against NeetCode 150, Blind 75 and Striver A2Z on 2026-10-30 with the numbers in this file;
   no third-party prose is reproduced. Also correct BL-26's wording — the residual overlap is
   with LeetCode naming, not with takeUforward content.
5. **Keep the claim that BL-26 actually made** ("no third-party sheet content remains"): nothing
   in this check contradicts it — A2Z-specific wording matches only 35/108, structure 19%,
   expression 0/8 sampled. The exposure to fix is the *marketing* word "original", not a rights
   breach.

## 7. What remains unknown

- Whether any Pacio prompt is derivative of **LeetCode/GfG/takeuforward problem prose** — not
  tested (title-only sources; problem-statement bulk pulls were out of scope).
- takeuforward.org's own A2Z sheet was never read (404 at the expected path, one attempt each);
  all A2Z figures rest on a third-party mirror that may drift from the original sheet.
- Whether the current 108 are *structurally* descended from the pre-`b5a4754` 474-question
  catalogue (git history not inspected — task rules forbade git).
- Blind 75 figures use my loose normaliser → INFERRED.
- `dsa_specs.json`'s 48 graded/prompt-level specs were not originality-tested here (only
  `PROBLEMS` tuples + their `prompt`/`why`).
