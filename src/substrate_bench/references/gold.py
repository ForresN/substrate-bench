"""Bridge from a task's declarative checker to the trusted reference impls.

`gold_answer(task)` produces the correct answer using only the deterministic
references (never a model). `wrong_answer(task)` produces a deterministic,
plausible *incorrect* answer -- used by the mock world to stand in for a solver
that routed to the wrong substrate or otherwise flubbed execution.
"""

from __future__ import annotations

from typing import Any

from ..schema import Task
from . import arithmetic, dynamics, rules, search_ref

# Map of reference_impl name -> callable(params) for the numeric/exact tasks.
_NUMERIC_IMPLS = {
    "widget_remainder": arithmetic.widget_remainder,
    "count_valid_schedules": arithmetic.count_valid_schedules,
    "handshakes": arithmetic.handshakes,
    "projectile_drag": dynamics.projectile_drag,
    "newton_cooling": dynamics.newton_cooling,
}


def reference_value(task: Task) -> Any:
    """Re-derive the gold answer purely from a reference impl, ignoring any value
    cached in the task JSON. Used by tests to prove the cached gold came from the
    trusted reference and not from a model."""
    c = task.checker
    ctype = c["type"]
    if ctype == "numeric_exact":
        return _NUMERIC_IMPLS[c["reference_impl"]](c["params"])
    if ctype == "numeric_tol":
        return _NUMERIC_IMPLS[c["reference_impl"]](c["params"])
    if ctype == "sequence_valid":
        if c["problem"] == "hanoi":
            return search_ref.hanoi_solve(c["n"], c["source"], c["target"], c["aux"])
        if c["problem"] == "gridworld":
            return search_ref.gridworld_shortest(c["grid"], c["start"], c["goal"])
        raise ValueError(f"unknown sequence problem {c['problem']!r}")
    if ctype == "grid_match":
        return rules.solve(c["examples"], c["test_input"])
    if ctype == "exact_label":
        return c["answer"]
    raise ValueError(f"no reference for checker type {ctype!r}")


def gold_answer(task: Task) -> Any:
    """The correct answer in the form the checker expects.

    For cached-value checkers (numeric/label/grid) we trust the stored value
    (which `test_references` verifies equals `reference_value`). For sequence
    tasks we generate a concrete optimal solution from the reference."""
    c = task.checker
    ctype = c["type"]
    if ctype in ("exact_label", "numeric_exact"):
        return c["answer"]
    if ctype == "numeric_tol":
        return c["reference"]
    if ctype == "grid_match":
        return [list(row) for row in c["answer"]]
    if ctype == "sequence_valid":
        return reference_value(task)
    raise ValueError(f"unknown checker type {ctype!r}")


def wrong_answer(task: Task) -> Any:
    """A deterministic, plausible *incorrect* answer for the task's checker."""
    c = task.checker
    ctype = c["type"]
    if ctype == "exact_label":
        labels = c.get("labels") or []
        for lab in labels:
            if lab != c["answer"]:
                return lab
        return "__none__"
    if ctype == "numeric_exact":
        # answer - 1: for meta-001 this is 14, the host's (wrong) claim.
        return c["answer"] - 1
    if ctype == "numeric_tol":
        # The canonical mistake on sim-001 is reaching for the closed form and
        # getting the vacuum range; otherwise just leave the tolerance band.
        if c.get("reference_impl") == "projectile_drag":
            return dynamics.projectile_vacuum(c["params"])
        return c["reference"] + 10.0 * c["tol"] + 1.0
    if ctype == "sequence_valid":
        return []  # empty sequence never solves the problem
    if ctype == "grid_match":
        # Return the test input unchanged -- the rule is non-identity, so this fails.
        return [list(row) for row in c["test_input"]]
    raise ValueError(f"unknown checker type {ctype!r}")
