"""The five declarative checker types (spec section 3).

Every checker is deterministic and model-free. `run_checker(task, answer)`
dispatches on `task.checker['type']` and returns a bool. Checkers are defensive:
a malformed or wrong-typed candidate answer scores False rather than raising.
"""

from __future__ import annotations

from typing import Any

from ..references import search_ref
from ..schema import Task


def _as_grid(value: Any):
    if not isinstance(value, (list, tuple)):
        return None
    grid = []
    for row in value:
        if not isinstance(row, (list, tuple)):
            return None
        grid.append([c for c in row])
    return grid


def check_exact_label(task: Task, answer: Any) -> bool:
    if not isinstance(answer, str):
        return False
    gold = str(task.checker["answer"]).strip().lower()
    return answer.strip().lower() == gold


def check_numeric_exact(task: Task, answer: Any) -> bool:
    if isinstance(answer, bool) or not isinstance(answer, (int, float)):
        return False
    return answer == task.checker["answer"]


def check_numeric_tol(task: Task, answer: Any) -> bool:
    if isinstance(answer, bool) or not isinstance(answer, (int, float)):
        return False
    return abs(float(answer) - float(task.checker["reference"])) <= float(task.checker["tol"])


def check_sequence_valid(task: Task, answer: Any) -> bool:
    c = task.checker
    if not isinstance(answer, (list, tuple)):
        return False
    require_optimal = bool(c.get("require_optimal", True))
    if c["problem"] == "hanoi":
        return search_ref.hanoi_validate(
            c["n"], answer, c["source"], c["target"], c["aux"], require_optimal
        )
    if c["problem"] == "gridworld":
        return search_ref.gridworld_validate(
            c["grid"], c["start"], c["goal"], answer, require_optimal
        )
    return False


def check_grid_match(task: Task, answer: Any) -> bool:
    cand = _as_grid(answer)
    gold = _as_grid(task.checker["answer"])
    return cand is not None and cand == gold


_DISPATCH = {
    "exact_label": check_exact_label,
    "numeric_exact": check_numeric_exact,
    "numeric_tol": check_numeric_tol,
    "sequence_valid": check_sequence_valid,
    "grid_match": check_grid_match,
}


def run_checker(task: Task, answer: Any) -> bool:
    """Return whether `answer` passes the task's declared checker."""
    fn = _DISPATCH.get(task.checker["type"])
    if fn is None:
        raise ValueError(f"unknown checker type {task.checker['type']!r}")
    return fn(task, answer)


def is_verifiable(task: Task) -> bool:
    """Can a `verify` substrate independently refute a candidate answer?

    Computational checks can be re-run against constraints/tests; a purely
    linguistic answer (e.g. sentiment) cannot be formally verified, so the
    verifier must trust it.
    """
    return task.checker["type"] != "exact_label" and "language" not in task.gold_substrate
