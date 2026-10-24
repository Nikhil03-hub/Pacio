"""DSA interview curriculum for Pacio Campus Intelligence, authored in-house.

Honest description of provenance (verified 2026-10-24, see docs/data/DSA_ORIGINALITY_CHECK.md):
the *problems* are canonical interview questions whose names appear in every public list of the
subject - 91 of 108 titles match a public list verbatim, which is expected for standard names and
is not a protectable expression. What is in-house is the 12-topic pattern taxonomy, the ordering,
the selection weighting, and every prompt and rationale string (6-gram overlap with public sources:
1 of 1,283 distinct 6-grams). No third-party sheet's section structure or ordering is reproduced.
The pattern coverage follows widely reported interview practice (arrays/hashing, two
pointers, sliding window, binary search, stacks, linked lists, trees, heaps, graphs,
backtracking, dynamic programming, greedy/intervals, bits and maths); see
docs/DATA_SOURCES.md (DS-4) for the sources that informed coverage.

Each topic carries a `problems` count so seeding code can size per-student progress
without importing the catalogue twice.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

CURRICULUM_VERSION = "2026.10-pattern-v1"

TOPICS = [
    {"code": "ARRAYS", "name": "Arrays & Hashing", "order": 1,
     "focus": "Indexing, prefix products, in-place transforms and hash-map lookups."},
    {"code": "POINTERS", "name": "Two Pointers & Sliding Window", "order": 2,
     "focus": "Monotonic scans, window invariants and converging pointers."},
    {"code": "BINSEARCH", "name": "Binary Search & Search Space", "order": 3,
     "focus": "Boundary conditions, rotated arrays and searching on the answer."},
    {"code": "STACK", "name": "Stacks & Monotonic Structures", "order": 4,
     "focus": "Parsing, next-greater patterns and histogram-style spans."},
    {"code": "LINKED", "name": "Linked Lists", "order": 5,
     "focus": "Pointer rewiring, cycles and constant-space traversal."},
    {"code": "TREES", "name": "Trees & BSTs", "order": 6,
     "focus": "Recursive shapes, traversal orders and BST invariants."},
    {"code": "HEAPS", "name": "Heaps & Top-K", "order": 7,
     "focus": "Priority queues, streaming order statistics and k-way merges."},
    {"code": "GRAPHS", "name": "Graphs & Grids", "order": 8,
     "focus": "Traversal, connectivity, topological order and shortest paths."},
    {"code": "BACKTRACK", "name": "Recursion & Backtracking", "order": 9,
     "focus": "Decision trees, pruning and generating combinations."},
    {"code": "DP", "name": "Dynamic Programming", "order": 10,
     "focus": "State definition, transition and rolling-array optimisation."},
    {"code": "GREEDY", "name": "Greedy & Intervals", "order": 11,
     "focus": "Exchange arguments, scheduling and interval sweeps."},
    {"code": "BITS", "name": "Bit Manipulation & Maths", "order": 12,
     "focus": "XOR identities, bit counting and fast arithmetic."},
]

# (title, pattern, difficulty, prompt, why it matters)
PROBLEMS: dict[str, list[tuple[str, str, str, str, str]]] = {
    "ARRAYS": [
        ("Two Sum", "Hash map lookup", "Easy",
         "Return the indices of the two numbers in an array that add up to a given target.",
         "The first hash-map trade-off candidates must be able to explain."),
        ("Contains Duplicate", "Set membership", "Easy",
         "Decide whether any value appears at least twice in an array.",
         "Warm-up for set-based deduplication and early exit."),
        ("Best Time to Buy and Sell Stock", "Running minimum", "Easy",
         "Given daily prices, find the maximum profit from one buy followed by one sell.",
         "Single-pass state tracking instead of trying every pair."),
        ("Product of Array Except Self", "Prefix and suffix products", "Medium",
         "Return an array where each position holds the product of every other element, without division.",
         "Prefix/suffix accumulation is reused in many counting problems."),
        ("Maximum Subarray", "Kadane scan", "Medium",
         "Find the contiguous subarray with the largest sum.",
         "The cleanest example of a running-state DP reduced to O(1) space."),
        ("Maximum Product Subarray", "Signed running state", "Medium",
         "Find the contiguous subarray with the largest product.",
         "Forces candidates to track both extremes when signs flip."),
        ("Rotate Array", "Reversal trick", "Medium",
         "Rotate an array to the right by k steps in place.",
         "In-place transformation with O(1) extra space."),
        ("Move Zeroes", "Stable compaction", "Easy",
         "Move all zeroes to the end while preserving the order of non-zero values.",
         "Two-pointer compaction that appears inside many streaming problems."),
        ("Merge Sorted Array", "Backward two pointers", "Easy",
         "Merge two sorted arrays into the first one, which has enough trailing space.",
         "Writing from the end avoids an extra buffer."),
        ("Find All Duplicates in an Array", "Index marking", "Medium",
         "Return every value that appears twice in an array whose values lie in 1..n.",
         "Cyclic placement and sign marking unlock O(1)-space counting."),
        ("Set Matrix Zeroes", "In-place marking", "Medium",
         "If a cell is zero, set its entire row and column to zero using constant extra space.",
         "Marker reuse inside the input is a common matrix interview trick."),
        ("Spiral Matrix", "Boundary simulation", "Medium",
         "Return all elements of a matrix in spiral order.",
         "Tests careful index bookkeeping and boundary updates."),
    ],
    "POINTERS": [
        ("Valid Palindrome", "Converging pointers", "Easy",
         "Decide whether a string reads the same forwards and backwards, ignoring non-alphanumeric characters.",
         "Pointer movement rules with a filtering predicate."),
        ("Two Sum II (Sorted Input)", "Converging pointers", "Medium",
         "Find two values in a sorted array that add up to a target.",
         "Shows why sorted order converts a search into a linear scan."),
        ("3Sum", "Sort plus two pointers", "Medium",
         "Return all unique triplets that sum to zero.",
         "Deduplication logic is where most candidates lose points."),
        ("Container With Most Water", "Greedy pointer movement", "Medium",
         "Choose two lines that, with the x-axis, hold the most water.",
         "The exchange argument for moving the shorter side."),
        ("Trapping Rain Water", "Two-pointer water levels", "Hard",
         "Compute how much rainwater is trapped between bars of varying height.",
         "Combines prefix maxima with a streaming pointer proof."),
        ("Longest Substring Without Repeating Characters", "Sliding window", "Medium",
         "Find the length of the longest substring with all distinct characters.",
         "The canonical variable-size window with a last-seen index."),
        ("Longest Repeating Character Replacement", "Window with budget", "Medium",
         "Find the longest substring that can be made uniform with at most k replacements.",
         "Windows whose validity depends on a frequency budget."),
        ("Minimum Window Substring", "Window with required counts", "Hard",
         "Find the smallest window in a string containing every character of another string.",
         "The reference problem for matched-count windows."),
        ("Find All Anagrams in a String", "Fixed-size window", "Medium",
         "Return every start index of substrings that are anagrams of a pattern.",
         "Frequency arrays with a fixed window size."),
        ("Permutation in String", "Fixed-size window comparison", "Medium",
         "Decide whether one string contains a permutation of another.",
         "Same window mechanics as anagram search, with an early exit."),
    ],
    "BINSEARCH": [
        ("Binary Search", "Classic bounds", "Easy",
         "Return the index of a target in a sorted array, or -1.",
         "Half-open interval discipline prevents infinite loops."),
        ("Search Insert Position", "Lower bound", "Easy",
         "Return the index where a value should be inserted in a sorted array.",
         "The lower-bound template reused everywhere."),
        ("First and Last Position of a Target", "Boundary search", "Medium",
         "Return the first and last indices of a target in a sorted array.",
         "Two bound searches instead of one fuzzy search."),
        ("Search in Rotated Sorted Array", "Pivot logic", "Medium",
         "Find a target in a sorted array that has been rotated.",
         "Deciding which half is sorted is a frequent twist."),
        ("Find Minimum in Rotated Sorted Array", "Pivot detection", "Medium",
         "Find the smallest element in a rotated sorted array.",
         "Comparing the midpoint with the right edge."),
        ("Koko Eating Bananas", "Binary search on the answer", "Medium",
         "Find the minimum eating speed that clears all piles within h hours.",
         "The key skill of searching a monotone feasibility function."),
        ("Capacity to Ship Packages Within D Days", "Search on capacity", "Medium",
         "Find the smallest ship capacity that delivers all packages within the given days.",
         "Same template as Koko with a different feasibility check."),
        ("Median of Two Sorted Arrays", "Partition search", "Hard",
         "Find the median of two sorted arrays in logarithmic time.",
         "Partition arithmetic and edge sentinels under pressure."),
    ],
    "STACK": [
        ("Valid Parentheses", "Stack matching", "Easy",
         "Decide whether a string of brackets is correctly nested and closed.",
         "The entry point to stack-based parsing."),
        ("Min Stack", "Auxiliary state stack", "Medium",
         "Design a stack that returns its minimum element in constant time.",
         "State design rather than algorithm choice."),
        ("Evaluate Reverse Polish Notation", "Operand stack", "Medium",
         "Evaluate an arithmetic expression written in postfix notation.",
         "Stack evaluation used by interpreters and calculators."),
        ("Daily Temperatures", "Monotonic stack", "Medium",
         "For each day, find how many days until a warmer temperature.",
         "The canonical next-greater-element pattern."),
        ("Next Greater Element", "Monotonic stack", "Medium",
         "For each element, find the next element to its right that is larger.",
         "Index bookkeeping inside a decreasing stack."),
        ("Largest Rectangle in Histogram", "Monotonic stack spans", "Hard",
         "Find the largest rectangle that fits inside a histogram.",
         "Left and right span boundaries in one pass."),
        ("Asteroid Collision", "Stack simulation", "Medium",
         "Simulate collisions between asteroids moving left and right.",
         "Careful case analysis with a stack."),
        ("Decode String", "Nested stack parsing", "Medium",
         "Decode a string with nested repeat counts such as 3[a2[c]].",
         "Two coordinated stacks for counts and fragments."),
    ],
    "LINKED": [
        ("Reverse Linked List", "Pointer rewiring", "Easy",
         "Reverse a singly linked list in place.",
         "The three-pointer pattern every linked-list question builds on."),
        ("Merge Two Sorted Lists", "Dummy-head merge", "Easy",
         "Merge two sorted linked lists into one sorted list.",
         "Dummy nodes remove most edge cases."),
        ("Reorder List", "Split, reverse, merge", "Medium",
         "Reorder a list as first, last, second, second-last, and so on.",
         "Combines three primitives in one problem."),
        ("Remove Nth Node From End", "Gap pointers", "Medium",
         "Remove the nth node from the end of a list in one pass.",
         "Two pointers separated by a fixed gap."),
        ("Linked List Cycle", "Fast and slow pointers", "Easy",
         "Decide whether a linked list contains a cycle.",
         "Floyd's algorithm and why it terminates."),
        ("Linked List Cycle II", "Cycle entry detection", "Medium",
         "Return the node where a cycle begins.",
         "Requires reasoning about pointer distances."),
        ("Add Two Numbers", "Digit-wise carry", "Medium",
         "Add two numbers stored as reversed linked-list digits.",
         "Carry propagation across list boundaries."),
        ("Copy List with Random Pointer", "Hash map cloning", "Medium",
         "Deep-copy a list whose nodes also have random pointers.",
         "Identity mapping between original and cloned nodes."),
    ],
    "TREES": [
        ("Maximum Depth of Binary Tree", "Post-order recursion", "Easy",
         "Return the number of nodes on the longest root-to-leaf path.",
         "The base case for most tree recursion."),
        ("Invert Binary Tree", "Recursive swap", "Easy",
         "Mirror a binary tree by swapping left and right children.",
         "Traversal plus mutation."),
        ("Diameter of Binary Tree", "Height with global best", "Easy",
         "Find the longest path between any two nodes.",
         "Returning one value while tracking another."),
        ("Balanced Binary Tree", "Height with early exit", "Easy",
         "Decide whether every node's subtrees differ in height by at most one.",
         "Bottom-up validation instead of repeated height calls."),
        ("Same Tree", "Parallel recursion", "Easy",
         "Decide whether two binary trees are structurally identical with equal values.",
         "Two-pointer recursion over two structures."),
        ("Binary Tree Level Order Traversal", "BFS by level", "Medium",
         "Return node values grouped by depth.",
         "Queue processing with a per-level size snapshot."),
        ("Binary Tree Right Side View", "Level order projection", "Medium",
         "Return the rightmost node value at each depth.",
         "Level boundaries in BFS."),
        ("Lowest Common Ancestor of a BST", "BST navigation", "Easy",
         "Find the lowest common ancestor of two nodes in a BST.",
         "Using the ordering invariant instead of searching both subtrees."),
        ("Validate Binary Search Tree", "Range propagation", "Medium",
         "Decide whether a tree satisfies the BST ordering invariant.",
         "Bounds must be inherited, not only compared with immediate parents."),
        ("Kth Smallest Element in a BST", "In-order traversal", "Medium",
         "Return the kth smallest value in a BST.",
         "In-order traversal as sorted iteration."),
        ("Construct Binary Tree from Preorder and Inorder", "Index mapping", "Medium",
         "Rebuild a tree from its preorder and inorder traversals.",
         "Root splitting and hash-map index lookup."),
        ("Serialize and Deserialize Binary Tree", "Preorder encoding", "Hard",
         "Design an encoding that round-trips an arbitrary binary tree.",
         "Null markers and stateful parsing."),
    ],
    "HEAPS": [
        ("Kth Largest Element in an Array", "Bounded min-heap", "Medium",
         "Return the kth largest value without fully sorting.",
         "Why the opposite heap keeps memory at O(k)."),
        ("Top K Frequent Elements", "Frequency plus heap", "Medium",
         "Return the k most frequent values in an array.",
         "Counting then selecting."),
        ("K Closest Points to Origin", "Bounded max-heap", "Medium",
         "Return the k points closest to the origin.",
         "Distance ordering without computing square roots."),
        ("Merge K Sorted Lists", "K-way merge", "Hard",
         "Merge k sorted linked lists into one sorted list.",
         "Priority queues across multiple streams."),
        ("Find Median from Data Stream", "Two heaps", "Hard",
         "Support inserting numbers and querying the running median.",
         "Balanced heaps and invariant maintenance."),
        ("Task Scheduler", "Frequency scheduling", "Medium",
         "Find the minimum time to run tasks with a cooldown between identical tasks.",
         "Counting and idle-slot arithmetic."),
    ],
    "GRAPHS": [
        ("Number of Islands", "Connected components", "Medium",
         "Count connected regions of land in a grid.",
         "The canonical grid traversal."),
        ("Clone Graph", "Graph copy with map", "Medium",
         "Deep-copy a connected undirected graph.",
         "Identity mapping and cycle handling."),
        ("Max Area of Island", "Component accumulation", "Medium",
         "Return the size of the largest connected land region.",
         "Traversal returning an aggregate."),
        ("Rotting Oranges", "Multi-source BFS", "Medium",
         "Find the minutes until all reachable oranges rot.",
         "Multi-source BFS and unreachable detection."),
        ("Pacific Atlantic Water Flow", "Reverse reachability", "Medium",
         "Find cells from which water can reach both oceans.",
         "Reversing the direction of a search."),
        ("Course Schedule", "Cycle detection", "Medium",
         "Decide whether all courses can be finished given prerequisites.",
         "Topological sorting or DFS colouring."),
        ("Course Schedule II", "Topological order", "Medium",
         "Return a valid order to finish all courses.",
         "Kahn's algorithm and output construction."),
        ("Number of Connected Components", "Union-find", "Medium",
         "Count connected components in an undirected graph.",
         "Disjoint sets with path compression."),
        ("Word Ladder", "Implicit graph BFS", "Hard",
         "Find the shortest transformation sequence between two words.",
         "Building a graph on the fly."),
        ("Network Delay Time", "Dijkstra", "Medium",
         "Find how long a signal takes to reach every node.",
         "Weighted shortest paths with a priority queue."),
    ],
    "BACKTRACK": [
        ("Subsets", "Include or exclude", "Medium",
         "Return every subset of a distinct integer array.",
         "The smallest decision-tree template."),
        ("Combination Sum", "Reuse with pruning", "Medium",
         "Find all combinations that sum to a target, reusing values.",
         "Start-index control and pruning."),
        ("Permutations", "Used-set exploration", "Medium",
         "Return every permutation of distinct integers.",
         "State restoration and ordering."),
        ("Word Search", "Grid backtracking", "Medium",
         "Decide whether a word can be traced through adjacent grid cells.",
         "Visited marking inside a mutable grid."),
        ("Palindrome Partitioning", "Cut enumeration", "Medium",
         "Partition a string so every part is a palindrome.",
         "Palindrome checks inside a decision tree."),
        ("N-Queens", "Constraint propagation", "Hard",
         "Place n queens so that none attack each other.",
         "Column and diagonal bookkeeping."),
        ("Letter Combinations of a Phone Number", "Cartesian recursion", "Medium",
         "Return all letter sequences a digit string could represent.",
         "Breadth of combinations with a fixed depth."),
        ("Generate Parentheses", "Count-constrained backtracking", "Medium",
         "Generate all well-formed bracket sequences of n pairs.",
         "Pruning by remaining counts."),
    ],
    "DP": [
        ("Climbing Stairs", "1D recurrence", "Easy",
         "Count the ways to reach the top when you may climb one or two steps.",
         "The Fibonacci-shaped introduction to DP."),
        ("House Robber", "Take or skip", "Medium",
         "Maximise the sum robbed from non-adjacent houses.",
         "The classic local choice recurrence."),
        ("House Robber II", "Circular DP", "Medium",
         "Solve the same problem when houses form a circle.",
         "Handling a circular constraint by splitting cases."),
        ("Coin Change", "Unbounded knapsack", "Medium",
         "Find the fewest coins that make an amount.",
         "Bottom-up minimisation with unreachable states."),
        ("Longest Increasing Subsequence", "Sequence DP", "Medium",
         "Find the length of the longest strictly increasing subsequence.",
         "The O(n^2) formulation and the patience-sorting improvement."),
        ("Word Break", "Prefix segmentation", "Medium",
         "Decide whether a string can be segmented into dictionary words.",
         "A reachable-index DP that reappears in parsing problems."),
        ("Longest Common Subsequence", "2D DP", "Medium",
         "Find the length of the longest common subsequence of two strings.",
         "The foundation for diffing and edit distance."),
        ("Edit Distance", "2D edit operations", "Hard",
         "Find the minimum insert, delete and replace operations between two strings.",
         "A three-way transition with clear base cases."),
        ("Partition Equal Subset Sum", "Subset sum", "Medium",
         "Decide whether an array can be split into two equal-sum halves.",
         "Boolean knapsack with rolling arrays."),
        ("Unique Paths", "Grid DP", "Medium",
         "Count monotone paths through a grid with obstacles absent.",
         "Grid state compression."),
        ("Decode Ways", "Prefix counting", "Medium",
         "Count the ways a digit string can be decoded into letters.",
         "Validity checks inside a recurrence."),
        ("Target Sum", "Signed subset sum", "Medium",
         "Count ways to assign plus or minus signs to reach a target.",
         "A DP reformulation of a combinatorics question."),
    ],
    "GREEDY": [
        ("Merge Intervals", "Sort and sweep", "Medium",
         "Merge all overlapping intervals.",
         "The default first move for interval problems."),
        ("Insert Interval", "Linear merge", "Medium",
         "Insert a new interval into a sorted list and merge overlaps.",
         "Three-phase scanning."),
        ("Non-overlapping Intervals", "Earliest finish", "Medium",
         "Remove the fewest intervals so the rest do not overlap.",
         "The exchange argument behind earliest-finish sorting."),
        ("Meeting Rooms II", "Sweep line", "Medium",
         "Find the minimum number of rooms needed for all meetings.",
         "Event ordering versus heap-based allocation."),
        ("Jump Game", "Farthest reach", "Medium",
         "Decide whether the last index is reachable from the first.",
         "Maintaining a reachable frontier."),
        ("Jump Game II", "Frontier expansion", "Medium",
         "Find the minimum jumps to reach the last index.",
         "Implicit BFS over reachable ranges."),
        ("Gas Station", "Circular surplus", "Medium",
         "Find the starting station that lets you complete a circuit.",
         "Why a single pass suffices."),
        ("Partition Labels", "Last occurrence sweep", "Medium",
         "Split a string into parts so each letter appears in at most one part.",
         "Greedy boundary expansion."),
    ],
    "BITS": [
        ("Single Number", "XOR cancellation", "Easy",
         "Find the element that appears once when every other element appears twice.",
         "The XOR identity that underpins many bit tricks."),
        ("Number of 1 Bits", "Bit counting", "Easy",
         "Count the set bits in an unsigned integer.",
         "Brian Kernighan's loop."),
        ("Counting Bits", "DP over bits", "Easy",
         "Return the set-bit count for every number up to n.",
         "Reusing a smaller result with an offset."),
        ("Missing Number", "Index XOR", "Easy",
         "Find the missing value in a sequence from 0 to n.",
         "Sum or XOR without extra memory."),
        ("Pow(x, n)", "Fast exponentiation", "Medium",
         "Compute x raised to an integer power efficiently.",
         "Binary exponentiation and negative powers."),
        ("Reverse Integer", "Overflow-safe arithmetic", "Medium",
         "Reverse the digits of an integer, returning zero on overflow.",
         "Boundary handling in fixed-width arithmetic."),
    ],
}

DSA_TOPICS = [{**topic, "problems": len(PROBLEMS[topic["code"]])} for topic in TOPICS]
DSA_TOTAL = sum(topic["problems"] for topic in DSA_TOPICS)

assert len(DSA_TOPICS) == 12, f"Expected 12 topics, got {len(DSA_TOPICS)}"
assert DSA_TOTAL == 108, f"Curriculum drift: expected 108 problems, got {DSA_TOTAL}"


# Bumped whenever the harness changes what "proven gradable" means, so an old stamp cannot
# keep advertising a problem as auto-gradable after the proof rule has moved.
DSA_HARNESS_VERSION = "2026.10-harness-v1"


def _spec_states(path: Path | None = None) -> dict[str, str]:
    """Question id -> validated | specified_unverified.

    Having an entry in the spec file is not proof of gradability; the harness stamp is. A missing
    file is a legitimate fresh checkout, so it yields no states. A corrupt file would silently
    demote the entire curriculum to draft, so it is allowed to raise.
    """
    path = path or Path(__file__).with_name("dsa_specs.json")
    if not path.exists():
        return {}
    states = {}
    for spec in json.loads(path.read_text(encoding="utf-8")):
        stamp = spec.get("verification") or {}
        proven = (stamp.get("result") == "pass"
                  and stamp.get("harness") == DSA_HARNESS_VERSION)
        states[spec["question_id"]] = "validated" if proven else "specified_unverified"
    return states


SPEC_STATES = _spec_states()
VALIDATED_SPEC_IDS = {qid for qid, state in SPEC_STATES.items() if state == "validated"}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def build_dsa_question_bank(now: datetime | None = None) -> list[dict]:
    """Return the stable curriculum as question rows."""
    now = now or datetime.now(timezone.utc)
    rows: list[dict] = []
    global_order = 0
    for topic in DSA_TOPICS:
        seen_subtopics: dict[str, int] = {}
        for index, (title, pattern, difficulty, prompt, why) in enumerate(PROBLEMS[topic["code"]], start=1):
            global_order += 1
            slug = _slug(title)
            # 48 keeps every title in the current catalogue whole; the longest slug is 47.
            # The trailing-hyphen strip stops a cut slug from ending on a dangling separator.
            question_id = f"dsa_{topic['code'].lower()}_{index:03d}_{slug[:48].rstrip('-')}"
            state = SPEC_STATES.get(question_id, "draft")
            validated = state == "validated"
            sub_code = _slug(pattern)[:40]
            seen_subtopics[sub_code] = seen_subtopics.get(sub_code, 0) + 1
            rows.append({
                "question_id": question_id,
                "spec_status": state,
                "gradable": validated,
                "sheet": "pacio_curriculum",
                "topic_code": topic["code"],
                "topic_name": topic["name"],
                "topic_order": topic["order"],
                "subtopic_code": sub_code,
                "subtopic_name": pattern,
                "title": title,
                "pattern": pattern,
                "prompt": prompt,
                "why_it_matters": why,
                "difficulty": difficulty,
                "order": index,
                "global_order": global_order,
                "source": "internal_curriculum",
                "curriculum_version": CURRICULUM_VERSION,
                "created_at": now.isoformat(),
            })
    assert len(rows) == DSA_TOTAL, f"Expected {DSA_TOTAL} DSA questions, got {len(rows)}"
    return rows


def question_bank_by_topic(now: datetime | None = None) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for question in build_dsa_question_bank(now):
        grouped.setdefault(question["topic_code"], []).append(question)
    return grouped
