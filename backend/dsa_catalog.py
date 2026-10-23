"""DSA curriculum catalog used by Campus Intelligence DSA Intelligence.

The topic sequence mirrors a widely used public DSA preparation sheet (474 problems
across 18 sections) so that student progress is comparable with material students
already follow. That publisher's terms prohibit commercial redistribution without
written consent - see docs/DATA_SOURCES.md, item DS-4, before this dataset ships in
a paid product.

Question records drive readiness: attempts, revision, mastery and faculty feedback
are computed from these rows.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable


STRIVER_TOPICS = [
    {"code": "BASICS", "name": "Learn the basics", "problems": 54, "order": 1},
    {"code": "SORTING", "name": "Learn Important Sorting Techniques", "problems": 7, "order": 2},
    {"code": "ARRAYS", "name": "Solve Problems on Arrays [Easy -> Medium -> Hard]", "problems": 40, "order": 3},
    {"code": "BIN_SEARCH", "name": "Binary Search [1D, 2D Arrays, Search Space]", "problems": 32, "order": 4},
    {"code": "STR_BASIC", "name": "Strings [Basic and Medium]", "problems": 15, "order": 5},
    {"code": "LL", "name": "Learn LinkedList [Single LL, Double LL, Medium, Hard Problems]", "problems": 31, "order": 6},
    {"code": "RECURSION", "name": "Recursion [PatternWise]", "problems": 25, "order": 7},
    {"code": "BIT_MANIP", "name": "Bit Manipulation [Concepts & Problems]", "problems": 18, "order": 8},
    {"code": "STACK", "name": "Stack and Queues [Learning, Prefix/Infix/Postfix, Monotonic Stack]", "problems": 30, "order": 9},
    {"code": "SLIDING", "name": "Sliding Window & Two Pointer Combined Problems", "problems": 12, "order": 10},
    {"code": "HEAP", "name": "Heaps [Learning, Medium, Hard Problems]", "problems": 17, "order": 11},
    {"code": "GREEDY", "name": "Greedy Algorithms [Easy, Medium/Hard]", "problems": 15, "order": 12},
    {"code": "TREE", "name": "Binary Trees [Traversals, Medium and Hard Problems]", "problems": 38, "order": 13},
    {"code": "BST", "name": "Binary Search Trees [Concept and Problems]", "problems": 16, "order": 14},
    {"code": "GRAPH", "name": "Graphs [Concepts & Problems]", "problems": 53, "order": 15},
    {"code": "DP", "name": "Dynamic Programming [Patterns and Problems]", "problems": 55, "order": 16},
    {"code": "TRIES", "name": "Tries", "problems": 7, "order": 17},
    {"code": "STR_ADV", "name": "Strings", "problems": 9, "order": 18},
]

DSA_TOTAL = sum(topic["problems"] for topic in STRIVER_TOPICS)
assert DSA_TOTAL == 474, f"DSA curriculum total drift: {DSA_TOTAL}"


SUBTOPIC_PATTERNS = {
    "BASICS": [
        ("basics", "Programming foundation"),
        ("patterns", "Pattern printing"),
        ("math", "Basic maths"),
        ("recursion", "Basic recursion"),
        ("hashing", "Basic hashing"),
    ],
    "SORTING": [("selection", "Selection sort"), ("bubble", "Bubble sort"), ("merge", "Merge sort"), ("quick", "Quick sort")],
    "ARRAYS": [("easy", "Easy arrays"), ("medium", "Medium arrays"), ("hard", "Hard arrays")],
    "BIN_SEARCH": [("one_d", "1D arrays"), ("search_space", "Search space"), ("two_d", "2D arrays")],
    "STR_BASIC": [("easy", "String basics"), ("medium", "Medium strings")],
    "LL": [("single", "Singly linked list"), ("double", "Doubly linked list"), ("medium", "Medium linked list"), ("hard", "Hard linked list")],
    "RECURSION": [("basics", "Recursion basics"), ("subsequence", "Subsequence pattern"), ("backtracking", "Backtracking")],
    "BIT_MANIP": [("concepts", "Bit concepts"), ("medium", "Bit problems")],
    "STACK": [("learning", "Stack and queue learning"), ("conversion", "Prefix/Infix/Postfix"), ("monotonic", "Monotonic stack"), ("implementation", "Advanced implementation")],
    "SLIDING": [("window", "Sliding window"), ("two_pointer", "Two pointer")],
    "HEAP": [("learning", "Heap learning"), ("medium", "Heap medium"), ("hard", "Heap hard")],
    "GREEDY": [("easy", "Easy greedy"), ("medium_hard", "Medium and hard greedy")],
    "TREE": [("traversal", "Tree traversals"), ("medium", "Medium trees"), ("hard", "Hard trees")],
    "BST": [("concept", "BST concepts"), ("problems", "BST problems")],
    "GRAPH": [("learning", "Graph learning"), ("traversal", "Traversal"), ("topo", "Topological sorting"), ("shortest_path", "Shortest paths"), ("mst_dsu", "MST and DSU"), ("advanced", "Advanced graphs")],
    "DP": [("one_d", "1D DP"), ("two_d", "2D/3D DP"), ("subsequence", "Subsequence DP"), ("strings", "String DP"), ("stocks", "Stock DP"), ("lis", "LIS DP"), ("partition", "Partition DP")],
    "TRIES": [("learning", "Trie learning"), ("xor", "Trie XOR")],
    "STR_ADV": [("patterns", "Pattern matching"), ("advanced", "Advanced strings")],
}


QUESTION_TITLES = {
    "BASICS": [
        "Input Output Basics", "Data Types", "If Else Statements", "Switch Statement", "Loops",
        "Functions", "Time Complexity", "Space Complexity", "Pattern 1 Rectangular Star Pattern",
        "Pattern 2 Right-Angled Triangle", "Pattern 3 Number Triangle", "Pattern 4 Repeated Number Triangle",
        "Pattern 5 Inverted Star Triangle", "Pattern 6 Inverted Number Triangle", "Pattern 7 Star Pyramid",
        "Pattern 8 Inverted Star Pyramid", "Pattern 9 Diamond Star Pattern", "Pattern 10 Half Diamond",
        "Pattern 11 Binary Number Triangle", "Pattern 12 Number Crown", "Pattern 13 Increasing Number Triangle",
        "Pattern 14 Increasing Letter Triangle", "Pattern 15 Reverse Letter Triangle", "Pattern 16 Alpha Ramp",
        "Pattern 17 Alpha Hill", "Pattern 18 Alpha Triangle", "Pattern 19 Symmetric Void Pattern",
        "Pattern 20 Symmetric Butterfly", "Pattern 21 Hollow Rectangle", "Pattern 22 Number Pattern",
        "Count Digits", "Reverse Number", "Check Palindrome Number", "GCD Or HCF", "Armstrong Number",
        "Print All Divisors", "Check Prime", "Print Name N Times", "Print 1 To N", "Print N To 1",
        "Sum Of First N Numbers", "Factorial Of N", "Reverse An Array", "Check String Palindrome",
        "Fibonacci Number", "Hashing Theory", "Count Frequencies Of Array Elements", "Find Highest And Lowest Frequency",
    ],
    "SORTING": [
        "Selection Sort", "Bubble Sort", "Insertion Sort", "Merge Sort", "Recursive Bubble Sort",
        "Recursive Insertion Sort", "Quick Sort",
    ],
    "ARRAYS": [
        "Largest Element in an Array", "Second Largest Element in an Array", "Check if the Array is Sorted",
        "Remove Duplicates from Sorted Array", "Left Rotate an Array by One Place", "Left Rotate an Array by D Places",
        "Move Zeroes to End", "Linear Search", "Union of Two Sorted Arrays", "Find Missing Number",
        "Maximum Consecutive Ones", "Find the Number That Appears Once", "Longest Subarray with Sum K - Positives",
        "Longest Subarray with Sum K - Positives and Negatives", "Two Sum", "Sort an Array of 0s, 1s and 2s",
        "Majority Element", "Kadane's Algorithm", "Print Subarray with Maximum Sum", "Stock Buy and Sell",
        "Rearrange Array Elements by Sign", "Next Permutation", "Leaders in an Array", "Longest Consecutive Sequence",
        "Set Matrix Zeroes", "Rotate Matrix", "Spiral Matrix", "Count Subarrays with Given Sum",
        "Pascal's Triangle", "Majority Element II", "3 Sum", "4 Sum", "Largest Subarray with Zero Sum",
        "Count Subarrays with XOR K", "Merge Intervals", "Merge Two Sorted Arrays Without Extra Space",
        "Find Missing and Repeating Numbers", "Count Inversions", "Reverse Pairs", "Maximum Product Subarray",
    ],
    "BIN_SEARCH": [
        "Binary Search to Find X in Sorted Array", "Implement Lower Bound", "Implement Upper Bound",
        "Search Insert Position", "Floor and Ceil in Sorted Array", "First and Last Occurrence",
        "Count Occurrences in Sorted Array", "Search in Rotated Sorted Array I", "Search in Rotated Sorted Array II",
        "Find Minimum in Rotated Sorted Array", "Find How Many Times Array Is Rotated", "Single Element in Sorted Array",
        "Find Peak Element", "Find Square Root of a Number", "Find Nth Root of M", "Koko Eating Bananas",
        "Minimum Days to Make Bouquets", "Smallest Divisor Given a Threshold", "Capacity to Ship Packages",
        "Kth Missing Positive Number", "Aggressive Cows", "Allocate Books", "Split Array Largest Sum",
        "Painter's Partition", "Minimize Maximum Distance to Gas Station", "Median of Two Sorted Arrays",
        "Kth Element of Two Sorted Arrays", "Row with Maximum Ones", "Search a 2D Matrix",
        "Search a 2D Matrix II", "Find Peak Element in 2D Matrix", "Median in Row-Wise Sorted Matrix",
    ],
    "STR_BASIC": [
        "Remove Outermost Parentheses", "Reverse Words in a String", "Largest Odd Number in a String",
        "Longest Common Prefix", "Isomorphic Strings", "Rotate String", "Valid Anagram",
        "Sort Characters by Frequency", "Maximum Nesting Depth of Parentheses", "Roman to Integer",
        "String to Integer Atoi", "Count Number of Substrings", "Longest Palindromic Substring",
        "Sum of Beauty of All Substrings", "Reverse Every Word in a String",
    ],
    "LL": [
        "Introduction to Linked List", "Inserting a Node in Linked List", "Deleting a Node in Linked List",
        "Length of Linked List", "Search in Linked List", "Introduction to Doubly Linked List",
        "Delete a Node in Doubly Linked List", "Insert a Node in Doubly Linked List", "Reverse a Doubly Linked List",
        "Middle of Linked List", "Reverse a Linked List", "Detect Loop in Linked List", "Find Starting Point of Loop",
        "Length of Loop in Linked List", "Check if Linked List is Palindrome", "Segregate Odd and Even Nodes",
        "Remove Nth Node from End", "Delete Middle Node of Linked List", "Sort Linked List",
        "Sort Linked List of 0s, 1s and 2s", "Find Intersection Point of Two Linked Lists",
        "Add 1 to a Number Represented by Linked List", "Add Two Numbers in Linked List",
        "Reverse Nodes in K Group", "Rotate Linked List", "Flattening a Linked List",
        "Clone Linked List with Random Pointer",
    ],
    "RECURSION": [
        "Recursive Implementation of Atoi", "Pow(x, n)", "Count Good Numbers", "Sort a Stack Using Recursion",
        "Reverse a Stack Using Recursion", "Generate All Binary Strings", "Generate Parentheses",
        "Print All Subsequences", "Subsequence Sum Equals K", "Print One Subsequence with Sum K",
        "Count Subsequences with Sum K", "Combination Sum", "Combination Sum II", "Subset Sum I",
        "Subset Sum II", "Combination Sum III", "Letter Combinations of a Phone Number", "Palindrome Partitioning",
        "Word Search", "Rat in a Maze", "N Queens", "Sudoku Solver", "M Coloring Problem", "Kth Permutation Sequence",
    ],
    "BIT_MANIP": [
        "Introduction to Bit Manipulation", "Check if the ith Bit is Set", "Check Odd or Even",
        "Check if Number is Power of Two", "Count Set Bits", "Set the Rightmost Unset Bit",
        "Swap Two Numbers", "Divide Two Integers Without Multiplication", "Minimum Bit Flips",
        "Power Set", "Single Number", "Single Number II", "Single Number III",
        "XOR of Numbers in a Range", "Find Two Odd Occurring Numbers", "Prime Factors Using Sieve",
    ],
    "STACK": [
        "Implement Stack Using Arrays", "Implement Queue Using Arrays", "Implement Stack Using Queue",
        "Implement Queue Using Stack", "Valid Parentheses", "Min Stack", "Infix to Postfix",
        "Prefix to Infix", "Prefix to Postfix", "Postfix to Prefix", "Postfix to Infix",
        "Infix to Prefix", "Next Greater Element I", "Next Greater Element II", "Next Smaller Element",
        "Number of Next Greater Elements", "Trapping Rain Water", "Sum of Subarray Minimums",
        "Asteroid Collision", "Sum of Subarray Ranges", "Remove K Digits", "Largest Rectangle in Histogram",
        "Maximal Rectangle", "Sliding Window Maximum", "Online Stock Span", "The Celebrity Problem",
        "LRU Cache", "LFU Cache",
    ],
    "SLIDING": [
        "Maximum Points from Cards", "Longest Substring Without Repeating Characters", "Max Consecutive Ones III",
        "Fruit Into Baskets", "Longest Repeating Character Replacement", "Binary Subarrays with Sum",
        "Count Number of Nice Subarrays", "Subarrays with K Different Integers", "Minimum Window Substring",
        "Minimum Window Subsequence", "Count Substrings Containing All Three Characters",
        "Longest Substring with At Most K Distinct Characters",
    ],
    "HEAP": [
        "Introduction to Priority Queue", "Min Heap and Max Heap Implementation", "Check if Array Represents Min Heap",
        "Convert Min Heap to Max Heap", "Kth Largest Element", "Kth Smallest Element",
        "Sort a K Sorted Array", "Merge K Sorted Lists", "Replace Each Array Element by Its Rank",
        "Task Scheduler", "Hands of Straights", "Top K Frequent Elements", "Kth Largest Element in a Stream",
        "Connect N Ropes with Minimum Cost", "K Closest Points to Origin", "Find Median from Data Stream",
        "Sliding Window Median",
    ],
    "GREEDY": [
        "Assign Cookies", "Fractional Knapsack", "Lemonade Change", "Valid Parenthesis String",
        "N Meetings in One Room", "Jump Game", "Jump Game II", "Minimum Platforms",
        "Job Sequencing Problem", "Candy", "Insert Interval", "Non-Overlapping Intervals",
        "Minimum Number of Arrows to Burst Balloons", "Minimum Coins", "Gas Station",
    ],
    "TREE": [
        "Binary Tree Representation", "Preorder Traversal", "Inorder Traversal", "Postorder Traversal",
        "Level Order Traversal", "Iterative Preorder Traversal", "Iterative Inorder Traversal",
        "Postorder Traversal Using Two Stacks", "Postorder Traversal Using One Stack", "Height of Binary Tree",
        "Check if Binary Tree is Balanced", "Diameter of Binary Tree", "Maximum Path Sum",
        "Check if Two Trees are Identical", "Zig Zag Traversal", "Boundary Traversal", "Vertical Order Traversal",
        "Top View of Binary Tree", "Bottom View of Binary Tree", "Right and Left View of Binary Tree",
        "Symmetric Binary Tree", "Root to Node Path", "Lowest Common Ancestor", "Maximum Width of Binary Tree",
        "Children Sum Property", "Nodes at Distance K", "Minimum Time to Burn Binary Tree",
        "Count Nodes in Complete Binary Tree", "Construct Tree from Preorder and Inorder",
        "Construct Tree from Postorder and Inorder", "Serialize and Deserialize Binary Tree",
        "Morris Inorder Traversal", "Morris Preorder Traversal", "Flatten Binary Tree to Linked List",
    ],
    "BST": [
        "Search in a Binary Search Tree", "Ceil in BST", "Floor in BST", "Insert a Node in BST",
        "Delete a Node in BST", "Kth Smallest Element in BST", "Kth Largest Element in BST",
        "Validate Binary Search Tree", "Lowest Common Ancestor in BST", "Construct BST from Preorder",
        "Inorder Successor and Predecessor in BST", "BST Iterator", "Two Sum in BST",
        "Recover BST", "Largest BST in Binary Tree",
    ],
    "GRAPH": [
        "Graph Representation", "BFS Traversal", "DFS Traversal", "Number of Provinces",
        "Connected Components", "Rotten Oranges", "Flood Fill", "Cycle Detection in Undirected Graph BFS",
        "Cycle Detection in Undirected Graph DFS", "0/1 Matrix", "Surrounded Regions", "Number of Enclaves",
        "Number of Distinct Islands", "Bipartite Graph BFS", "Bipartite Graph DFS", "Cycle Detection in Directed Graph",
        "Topological Sort DFS", "Topological Sort Kahn Algorithm", "Course Schedule I", "Course Schedule II",
        "Find Eventual Safe States", "Alien Dictionary", "Shortest Path in DAG",
        "Shortest Path in Undirected Graph with Unit Weights", "Word Ladder I", "Word Ladder II",
        "Dijkstra Algorithm Using Priority Queue", "Shortest Path in Binary Maze", "Path with Minimum Effort",
        "Cheapest Flights Within K Stops", "Network Delay Time", "Number of Ways to Arrive at Destination",
        "Minimum Multiplications to Reach End", "Bellman Ford Algorithm", "Floyd Warshall Algorithm",
        "Find City with Smallest Number of Neighbours", "Minimum Spanning Tree", "Prim's Algorithm",
        "Disjoint Set Union", "Kruskal's Algorithm", "Number of Provinces Using DSU",
        "Number of Operations to Make Network Connected", "Accounts Merge", "Most Stones Removed",
        "Number of Islands II", "Making a Large Island", "Swim in Rising Water", "Bridges in Graph",
        "Articulation Points", "Kosaraju Algorithm", "Tarjan Strongly Connected Components",
    ],
    "DP": [
        "Introduction to Dynamic Programming", "Fibonacci Number", "Climbing Stairs", "Frog Jump",
        "Frog Jump with K Distance", "Maximum Sum of Non-Adjacent Elements", "House Robber II", "Ninja Training",
        "Grid Unique Paths", "Grid Unique Paths II", "Minimum Path Sum in Grid", "Minimum Path Sum in Triangle",
        "Minimum Falling Path Sum", "Cherry Pickup II", "Subset Sum Equals Target", "Partition Equal Subset Sum",
        "Minimum Absolute Sum Difference", "Count Subsets with Sum K", "Count Partitions with Given Difference",
        "0/1 Knapsack", "Minimum Coins", "Target Sum", "Coin Change II", "Unbounded Knapsack",
        "Rod Cutting", "Longest Common Subsequence", "Print Longest Common Subsequence",
        "Longest Common Substring", "Longest Palindromic Subsequence", "Minimum Insertions to Make Palindrome",
        "Minimum Insertions or Deletions to Convert String", "Shortest Common Supersequence", "Distinct Subsequences",
        "Edit Distance", "Wildcard Matching", "Best Time to Buy and Sell Stock", "Stock Buy and Sell II",
        "Stock Buy and Sell III", "Stock Buy and Sell IV", "Stock with Cooldown", "Stock with Transaction Fee",
        "Longest Increasing Subsequence", "Print Longest Increasing Subsequence", "LIS Using Binary Search",
        "Largest Divisible Subset", "Longest String Chain", "Longest Bitonic Subsequence", "Number of LIS",
        "Matrix Chain Multiplication", "Minimum Cost to Cut Stick", "Burst Balloons", "Boolean Expression Evaluation",
        "Palindrome Partitioning II", "Partition Array for Maximum Sum", "Maximum Rectangle Area with All 1s",
        "Count Square Submatrices with All Ones",
    ],
    "TRIES": [
        "Implement Trie I", "Implement Trie II", "Longest Word with All Prefixes",
        "Number of Distinct Substrings", "Maximum XOR of Two Numbers", "Maximum XOR with an Element from Array",
        "Complete String",
    ],
    "STR_ADV": [
        "KMP Algorithm", "Rabin Karp Algorithm", "Z Function", "Shortest Palindrome",
        "Longest Happy Prefix", "Count Distinct Substrings", "Longest Repeated Substring",
        "Aho-Corasick Algorithm", "Minimum Characters Needed to Make String Palindrome",
    ],
}


DIFFICULTY_BY_TOPIC = {
    "BASICS": (44, 10, 0),
    "SORTING": (4, 3, 0),
    "ARRAYS": (14, 14, 12),
    "BIN_SEARCH": (13, 15, 4),
    "STR_BASIC": (8, 7, 0),
    "LL": (11, 14, 6),
    "RECURSION": (7, 10, 8),
    "BIT_MANIP": (7, 8, 3),
    "STACK": (8, 13, 9),
    "SLIDING": (3, 7, 2),
    "HEAP": (4, 9, 4),
    "GREEDY": (5, 7, 3),
    "TREE": (12, 16, 10),
    "BST": (7, 7, 2),
    "GRAPH": (13, 23, 17),
    "DP": (10, 24, 21),
    "TRIES": (3, 3, 1),
    "STR_ADV": (1, 5, 3),
}


def _slug(value: str) -> str:
    keep = []
    for char in value.lower():
        if char.isalnum():
            keep.append(char)
        elif keep and keep[-1] != "_":
            keep.append("_")
    return "".join(keep).strip("_")


def _difficulty(topic_code: str, index: int) -> str:
    easy, medium, _hard = DIFFICULTY_BY_TOPIC[topic_code]
    if index <= easy:
        return "Easy"
    if index <= easy + medium:
        return "Medium"
    return "Hard"


def _subtopic(topic_code: str, index: int, total: int) -> tuple[str, str]:
    patterns = SUBTOPIC_PATTERNS[topic_code]
    bucket_size = max(1, (total + len(patterns) - 1) // len(patterns))
    bucket = min(len(patterns) - 1, (index - 1) // bucket_size)
    return patterns[bucket]


def _titles(topic_code: str, total: int) -> Iterable[str]:
    provided = QUESTION_TITLES.get(topic_code, [])
    for title in provided[:total]:
        yield title
    topic_name = next(topic["name"] for topic in STRIVER_TOPICS if topic["code"] == topic_code)
    for index in range(len(provided) + 1, total + 1):
        yield f"{topic_name} Practice {index}"


def build_dsa_question_bank(now: datetime | None = None) -> list[dict]:
    """Return the stable 474-row DSA question catalog."""
    now = now or datetime.now(timezone.utc)
    rows: list[dict] = []
    global_order = 0
    for topic in STRIVER_TOPICS:
        topic_total = int(topic["problems"])
        for index, title in enumerate(_titles(topic["code"], topic_total), start=1):
            global_order += 1
            sub_code, sub_name = _subtopic(topic["code"], index, topic_total)
            question_slug = _slug(title)
            rows.append({
                "question_id": f"a2z_{topic['code'].lower()}_{index:03d}_{question_slug[:44]}",
                "sheet": "campus_dsa_curriculum",
                "topic_code": topic["code"],
                "topic_name": topic["name"],
                "topic_order": topic["order"],
                "subtopic_code": sub_code,
                "subtopic_name": sub_name,
                "title": title,
                "difficulty": _difficulty(topic["code"], index),
                "order": index,
                "global_order": global_order,
                "source": "internal_curriculum",
                "created_at": now.isoformat(),
            })
    assert len(rows) == DSA_TOTAL, f"Expected {DSA_TOTAL} DSA questions, got {len(rows)}"
    return rows


def question_bank_by_topic(now: datetime | None = None) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for question in build_dsa_question_bank(now):
        grouped.setdefault(question["topic_code"], []).append(question)
    return grouped
