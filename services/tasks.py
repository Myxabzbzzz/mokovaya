import random as random_module
from dataclasses import dataclass
from typing import List

# Every entry is a specific, real task (verified via a live fetch of each
# source, not guessed from memory) — not a category/catalog link.


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
    Task("Count lowercase letters in a string", "easy", "Codewars", "https://www.codewars.com/kata/56a946cd7bd95ccab2000055"),
    Task("Return the day", "easy", "Codewars", "https://www.codewars.com/kata/59dd3ccdded72fc78b000b25"),
    Task("How old will I be in 2099?", "easy", "Codewars", "https://www.codewars.com/kata/5761a717780f8950ce001473"),
    Task("MakeUpperCase", "easy", "Codewars", "https://www.codewars.com/kata/57a0556c7cb1f31ab3000ad7"),
    Task("Twice as old", "easy", "Codewars", "https://www.codewars.com/kata/5b853229cfde412a470000d0"),
    Task("Calculate BMI", "easy", "Codewars", "https://www.codewars.com/kata/57a429e253ba3381850000fb"),
    Task("Who ate the cookie?", "easy", "Codewars", "https://www.codewars.com/kata/55a996e0e8520afab9000055"),
    Task("Средний элемент", "easy", "CodeRun", "https://coderun.yandex.ru/problem/median-out-of-three"),
    Task("Вывести маршрут максимальной стоимости", "easy", "CodeRun", "https://coderun.yandex.ru/problem/print-the-route-of-the-maximum-cost"),
    Task("Ход конём", "easy", "CodeRun", "https://coderun.yandex.ru/problem/knight-move"),
    Task("Длина кратчайшего пути", "easy", "CodeRun", "https://coderun.yandex.ru/problem/shortest-path-length"),
    Task("Блохи", "easy", "CodeRun", "https://coderun.yandex.ru/problem/fleas"),
    Task("Путь спелеолога", "easy", "CodeRun", "https://coderun.yandex.ru/problem/speleologist-way"),
]

MEDIUM_TASKS: List[Task] = [
    Task("Add Two Numbers", "medium", "LeetCode", "https://leetcode.com/problems/add-two-numbers/"),
    Task("Longest Substring Without Repeating Characters", "medium", "LeetCode", "https://leetcode.com/problems/longest-substring-without-repeating-characters/"),
    Task("3Sum", "medium", "LeetCode", "https://leetcode.com/problems/3sum/"),
    Task("Group Anagrams", "medium", "LeetCode", "https://leetcode.com/problems/group-anagrams/"),
    Task("Product of Array Except Self", "medium", "LeetCode", "https://leetcode.com/problems/product-of-array-except-self/"),
    Task("Multiples of 3 or 5", "medium", "Codewars", "https://www.codewars.com/kata/514b92a657cdc65150000006"),
    Task("Convert string to camel case", "medium", "Codewars", "https://www.codewars.com/kata/517abf86da9663f1d2000003"),
    Task("Classify a floating point number", "medium", "Codewars", "https://www.codewars.com/kata/5f1ab7bd5af35f000f4ff875"),
    Task("FizzBuzz++", "medium", "Codewars", "https://www.codewars.com/kata/596925532f709fccf3000077"),
    Task("Sum The Tree", "medium", "Codewars", "https://www.codewars.com/kata/5800580f8f7ddaea13000025"),
    Task("Cantor's pairing function", "medium", "Codewars", "https://www.codewars.com/kata/543b9113def6343e43000875"),
    Task("Самый дешевый путь", "medium", "CodeRun", "https://coderun.yandex.ru/problem/cheapest-way"),
    Task("Поиск в глубину", "medium", "CodeRun", "https://coderun.yandex.ru/problem/search-in-depth"),
    Task("Компоненты связности", "medium", "CodeRun", "https://coderun.yandex.ru/problem/connectivity-components"),
    Task("Топологическая сортировка", "medium", "CodeRun", "https://coderun.yandex.ru/problem/topological-sorting"),
    Task("Поиск цикла", "medium", "CodeRun", "https://coderun.yandex.ru/problem/cycle-search"),
    Task("Путь в графе", "medium", "CodeRun", "https://coderun.yandex.ru/problem/the-path-in-the-graph"),
    Task("Пересадки", "medium", "CodeRun", "https://coderun.yandex.ru/problem/metro-2"),
    Task("Конвейер", "medium", "CodeRun", "https://coderun.yandex.ru/problem/conveyor"),
]

EASY_PROBABILITY = 0.9


def pick_random_task(rng: random_module.Random = random_module) -> Task:
    pool = EASY_TASKS if rng.random() < EASY_PROBABILITY else MEDIUM_TASKS
    return rng.choice(pool)
