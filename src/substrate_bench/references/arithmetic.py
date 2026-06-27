"""Trusted deterministic reference for the exact-computation tasks.

Plain integer arithmetic and a tiny constraint-satisfaction enumerator. No
models, no floating point for the exact tasks.
"""

from __future__ import annotations

from math import comb, gcd as _gcd
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


def gcd(params: Mapping[str, int]) -> int:
    return _gcd(int(params["a"]), int(params["b"]))


def lcm(params: Mapping[str, int]) -> int:
    a, b = int(params["a"]), int(params["b"])
    return a * b // _gcd(a, b)


def arithmetic_series_sum(params: Mapping[str, int]) -> int:
    """Sum of n terms of an arithmetic series: first term a, common difference d."""
    a, d, n = int(params["a"]), int(params["d"]), int(params["n"])
    return n * (2 * a + (n - 1) * d) // 2


def modexp(params: Mapping[str, int]) -> int:
    """Modular exponentiation: base**exp mod m."""
    return pow(int(params["base"]), int(params["exp"]), int(params["mod"]))


def combinations(params: Mapping[str, int]) -> int:
    """C(n, k)."""
    return comb(int(params["n"]), int(params["k"]))


def total_seconds(params: Mapping[str, int]) -> int:
    """Multi-step unit arithmetic: days/hours/minutes/seconds -> seconds."""
    d = int(params.get("days", 0))
    h = int(params.get("hours", 0))
    m = int(params.get("minutes", 0))
    s = int(params.get("seconds", 0))
    return ((d * 24 + h) * 60 + m) * 60 + s
