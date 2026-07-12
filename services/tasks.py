import random as random_module
from dataclasses import dataclass
from typing import List

# LeetCode entries link to specific, well-known problems (stable slugs).
# Codewars/CodeRun entries link to their difficulty-filtered catalog pages
# rather than a specific problem — individual kata/task IDs on those sites
# aren't reliably reproducible without looking them up live.


@dataclass(frozen=True)
class Task:
    title: str
    difficulty: str  # "easy" | "medium"
    source: str
    url: str


EASY_TASKS: List[Task] = [
    Task("Two Sum", "easy", "LeetCode", "https://leetcode.com/problems/two-sum/"),
    Task("Valid Parentheses", "easy", "LeetCode", "https://leetcode.com/problems/valid-parentheses/"),
    Task("Merge Two Sorted Lists", "easy", "LeetCode", "https://leetcode.com/problems/merge-two-sorted-lists/"),
    Task("Best Time to Buy and Sell Stock", "easy", "LeetCode", "https://leetcode.com/problems/best-time-to-buy-and-sell-stock/"),
    Task("Valid Anagram", "easy", "LeetCode", "https://leetcode.com/problems/valid-anagram/"),
    Task("Climbing Stairs", "easy", "LeetCode", "https://leetcode.com/problems/climbing-stairs/"),
    Task("Maximum Subarray", "easy", "LeetCode", "https://leetcode.com/problems/maximum-subarray/"),
    Task("Contains Duplicate", "easy", "LeetCode", "https://leetcode.com/problems/contains-duplicate/"),
    Task("Single Number", "easy", "LeetCode", "https://leetcode.com/problems/single-number/"),
    Task("Reverse Linked List", "easy", "LeetCode", "https://leetcode.com/problems/reverse-linked-list/"),
    Task("Случайная лёгкая kata (8 kyu)", "easy", "Codewars", "https://www.codewars.com/kata/search?q=&r%5B%5D=-8"),
    Task("Случайная лёгкая задача", "easy", "CodeRun", "https://coderun.yandex.ru/"),
]

MEDIUM_TASKS: List[Task] = [
    Task("Add Two Numbers", "medium", "LeetCode", "https://leetcode.com/problems/add-two-numbers/"),
    Task("Longest Substring Without Repeating Characters", "medium", "LeetCode", "https://leetcode.com/problems/longest-substring-without-repeating-characters/"),
    Task("3Sum", "medium", "LeetCode", "https://leetcode.com/problems/3sum/"),
    Task("Group Anagrams", "medium", "LeetCode", "https://leetcode.com/problems/group-anagrams/"),
    Task("Product of Array Except Self", "medium", "LeetCode", "https://leetcode.com/problems/product-of-array-except-self/"),
    Task("Случайная kata среднего уровня (5-6 kyu)", "medium", "Codewars", "https://www.codewars.com/kata/search?q=&r%5B%5D=-6"),
    Task("Случайная задача среднего уровня", "medium", "CodeRun", "https://coderun.yandex.ru/"),
]

EASY_PROBABILITY = 0.9


def pick_random_task(rng: random_module.Random = random_module) -> Task:
    pool = EASY_TASKS if rng.random() < EASY_PROBABILITY else MEDIUM_TASKS
    return rng.choice(pool)
