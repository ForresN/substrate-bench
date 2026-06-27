"""Trusted deterministic reference for the exact-computation tasks.

Plain integer arithmetic and a tiny constraint-satisfaction enumerator. No
models, no floating point for the exact tasks.
"""

from __future__ import annotations

from itertools import permutations
from typing import Mapping


def widget_remainder(params: Mapping[str, int]) -> int:
    """exact-001: containers * per_container - shipped."""
    return params["containers"] * params["per_container"] - params["shipped"]


def count_valid_schedules(params: Mapping) -> int:
    """exact-002: count assignments of the named meetings to the given slots
    that satisfy `before` (a < b) and `not_in` constraints.

    params = {
        "meetings": ["A", "B", "C"],
        "slots": [9, 10, 11],
        "before": [["A", "B"]],          # A's slot < B's slot
        "not_in": {"C": [9]}             # C may not occupy slot 9
    }
    """
    meetings = list(params["meetings"])
    slots = list(params["slots"])
    before = [tuple(p) for p in params.get("before", [])]
    not_in = {k: set(v) for k, v in params.get("not_in", {}).items()}

    count = 0
    for perm in permutations(slots, len(meetings)):
        assign = dict(zip(meetings, perm))
        if any(assign[a] >= assign[b] for a, b in before):
            continue
        if any(assign.get(m) in bad for m, bad in not_in.items()):
            continue
        count += 1
    return count


def handshakes(params: Mapping[str, int]) -> int:
    """meta-001: complete-graph handshake count C(n, 2) = n*(n-1)/2."""
    n = int(params["guests"])
    return n * (n - 1) // 2
