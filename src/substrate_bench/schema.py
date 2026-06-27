"""Task / Result / SolverOutput dataclasses plus JSON load & validation.

A Task is declarative and seed-stable: the checker block carries everything the
deterministic scorer needs, so no model is ever consulted during scoring.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, List, Optional

from .substrates import SUBSTRATES

VALID_CHECKERS = frozenset(
    {"exact_label", "numeric_exact", "numeric_tol", "sequence_valid", "grid_match"}
)


class TaskValidationError(ValueError):
    """Raised when a task JSON violates the schema."""


@dataclass(frozen=True)
class Task:
    id: str
    category: str
    prompt: str
    gold_substrate: List[str]
    checker: dict
    difficulty: int
    rationale: str = ""

    def needs_verify(self) -> bool:
        return "verify" in self.gold_substrate


@dataclass
class SolverOutput:
    """What a condition harness returns for one task (behaviour, not judgement)."""

    answer: Any
    chosen_substrate: str
    verified: bool = False
    self_corrected: bool = False
    cost: float = 0.0
    latency_s: float = 0.0
    raw: str = ""


@dataclass
class Result:
    """A scored (task, condition) cell of the leaderboard."""

    task_id: str
    category: str
    condition: str
    chosen_substrate: str
    gold_substrate: List[str]
    answer: Any
    answer_correct: bool
    substrate_correct: bool
    cost: float
    latency_s: float
    verified: bool
    self_corrected: bool
    failure_mode: str
    difficulty: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Result":
        return cls(**d)


# --------------------------------------------------------------------------- #
# Loading & validation
# --------------------------------------------------------------------------- #
def validate_task(obj: dict) -> Task:
    required = {"id", "category", "prompt", "gold_substrate", "checker", "difficulty"}
    missing = required - obj.keys()
    if missing:
        raise TaskValidationError(f"task missing fields: {sorted(missing)}")

    gold = obj["gold_substrate"]
    if not isinstance(gold, list) or not gold:
        raise TaskValidationError(f"{obj['id']}: gold_substrate must be a non-empty list")
    bad = [s for s in gold if s not in SUBSTRATES]
    if bad:
        raise TaskValidationError(f"{obj['id']}: unknown substrate(s) {bad}")

    checker = obj["checker"]
    if not isinstance(checker, dict) or "type" not in checker:
        raise TaskValidationError(f"{obj['id']}: checker must be an object with a 'type'")
    if checker["type"] not in VALID_CHECKERS:
        raise TaskValidationError(f"{obj['id']}: unknown checker type {checker['type']!r}")

    diff = obj["difficulty"]
    if not isinstance(diff, int) or not (1 <= diff <= 3):
        raise TaskValidationError(f"{obj['id']}: difficulty must be an int in 1..3")

    return Task(
        id=obj["id"],
        category=obj["category"],
        prompt=obj["prompt"],
        gold_substrate=list(gold),
        checker=dict(checker),
        difficulty=diff,
        rationale=obj.get("rationale", ""),
    )


def load_task(path: str | Path) -> Task:
    with open(path, "r", encoding="utf-8") as fh:
        return validate_task(json.load(fh))


def load_tasks(directory: str | Path) -> List[Task]:
    """Load and validate every *.json task in `directory`, sorted by id."""
    d = Path(directory)
    if not d.is_dir():
        raise FileNotFoundError(f"task directory not found: {d}")
    tasks = [load_task(p) for p in sorted(d.glob("*.json"))]
    if not tasks:
        raise FileNotFoundError(f"no task JSON found in {d}")
    return sorted(tasks, key=lambda t: t.id)
