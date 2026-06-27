"""Trusted deterministic validators for the `verify`-strategy tasks.

A verify task presents a *candidate* (a claimed solution or property) and asks
whether it holds. The gold label is computed here, never by a solver. `label_for`
dispatches on the checker's `verify_impl` and returns the positive/negative label.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from . import search_ref


def is_prime(n: int) -> bool:
    n = int(n)
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def balanced_parens(s: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in ")]}":
            if not stack or stack[-1] != pairs[ch]:
                return False
            stack.pop()
    return not stack


def nqueens_valid(positions: Sequence[int], n: int) -> bool:
    """positions[r] = column of the queen in row r; must be a legal n-queens board."""
    if len(positions) != n:
        return False
    if any(not (0 <= c < n) for c in positions):
        return False
    if len(set(positions)) != n:
        return False
    for r1 in range(n):
        for r2 in range(r1 + 1, n):
            if abs(positions[r1] - positions[r2]) == abs(r1 - r2):
                return False
    return True


def latin_square_valid(grid: Sequence[Sequence[int]]) -> bool:
    n = len(grid)
    target = list(range(1, n + 1))
    if any(len(row) != n for row in grid):
        return False
    for row in grid:
        if sorted(row) != target:
            return False
    for c in range(n):
        if sorted(grid[r][c] for r in range(n)) != target:
            return False
    return True


def schedule_valid(constraints: Mapping, assignment: Mapping) -> bool:
    """Does a concrete meeting->slot assignment satisfy the constraints?"""
    slots = list(constraints["slots"])
    meetings = list(constraints["meetings"])
    a = {k: int(v) for k, v in assignment.items()}
    if sorted(a.keys()) != sorted(meetings):
        return False
    if any(v not in slots for v in a.values()):
        return False
    if len(set(a.values())) != len(a):  # distinct slots
        return False
    for x, y in constraints.get("before", []):
        if a[x] >= a[y]:
            return False
    for m, bad in constraints.get("not_in", {}).items():
        if a.get(m) in set(bad):
            return False
    return True


def evaluate(impl: str, candidate: Mapping) -> bool:
    """Run a validator on a candidate, returning True iff it holds."""
    if impl == "hanoi":
        return search_ref.hanoi_validate(
            candidate["n"], candidate["moves"],
            candidate.get("source", "A"), candidate.get("target", "C"), candidate.get("aux", "B"),
            require_optimal=candidate.get("require_optimal", False),
        )
    if impl == "gridworld":
        return search_ref.gridworld_validate(
            candidate["grid"], candidate["start"], candidate["goal"], candidate["moves"],
            require_optimal=candidate.get("require_optimal", False),
        )
    if impl == "waterjug":
        return search_ref.waterjug_validate(
            candidate["cap_a"], candidate["cap_b"], candidate["target"], candidate["actions"],
            require_optimal=candidate.get("require_optimal", False),
        )
    if impl == "prime":
        return is_prime(candidate["n"])
    if impl == "balanced":
        return balanced_parens(candidate["s"])
    if impl == "nqueens":
        return nqueens_valid(candidate["positions"], candidate["n"])
    if impl == "latin":
        return latin_square_valid(candidate["grid"])
    if impl == "schedule":
        return schedule_valid(candidate["constraints"], candidate["assignment"])
    raise ValueError(f"unknown verify_impl {impl!r}")


def label_for(checker: Mapping) -> str:
    """Compute the gold label for a verify task. labels[0]=positive, labels[1]=negative."""
    labels = checker["labels"]
    ok = evaluate(checker["verify_impl"], checker["candidate"])
    return labels[0] if ok else labels[1]
