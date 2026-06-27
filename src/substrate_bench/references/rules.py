"""Trusted deterministic reference for the ARC-flavoured hidden-rule task.

The v0 rule is a horizontal mirror (reverse every row). The reference both
*induces* the rule from worked examples (by checking candidate rules against all
example pairs) and *applies* it. This is a toy, not an ARC-AGI solver.
"""

from __future__ import annotations

from typing import Callable, List, Sequence

Grid = List[List[int]]

# The small library of candidate transforms the inducer searches over.
_CANDIDATES: dict[str, Callable[[Grid], Grid]] = {
    "mirror_horizontal": lambda g: [list(reversed(row)) for row in g],
    "mirror_vertical": lambda g: [list(row) for row in reversed(g)],
    "transpose": lambda g: [list(col) for col in zip(*g)],
    "rotate_180": lambda g: [list(reversed(row)) for row in reversed(g)],
    "identity": lambda g: [list(row) for row in g],
}


def _as_grid(g: Sequence[Sequence[int]]) -> Grid:
    return [list(row) for row in g]


def induce_rule(examples: Sequence[dict]) -> str:
    """Return the name of the unique candidate transform consistent with every
    (input -> output) example. Raises if zero or more than one fit."""
    fits = []
    for name, fn in _CANDIDATES.items():
        if all(fn(_as_grid(ex["input"])) == _as_grid(ex["output"]) for ex in examples):
            fits.append(name)
    if len(fits) != 1:
        raise ValueError(f"rule not uniquely determined: {fits}")
    return fits[0]


def apply_rule(rule: str, grid: Sequence[Sequence[int]]) -> Grid:
    return _CANDIDATES[rule](_as_grid(grid))


def solve(examples: Sequence[dict], test_input: Sequence[Sequence[int]]) -> Grid:
    """Induce the rule from examples and apply it to the test input."""
    return apply_rule(induce_rule(examples), test_input)
