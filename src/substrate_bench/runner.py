"""Execute conditions over tasks and turn solver behaviour into scored Results.

The runner is the only place that joins the three concerns: a condition produces
behaviour (a SolverOutput), the checker judges the answer, and the scoring
module classifies the failure. No model is consulted here.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from .checkers import run_checker
from .conditions import CONDITION_ORDER, CONDITIONS, Pricing
from .model import Model, StubModel
from .schema import Result, SolverOutput, Task
from .scoring import classify_failure


def score_output(task: Task, condition: str, out: SolverOutput) -> Result:
    """Judge one SolverOutput against the task's checker and gold substrate."""
    answer_correct = run_checker(task, out.answer)
    substrate_correct = out.chosen_substrate in task.gold_substrate
    failure_mode = classify_failure(
        answer=out.answer,
        answer_correct=answer_correct,
        substrate_correct=substrate_correct,
        verified=out.verified,
        needs_verify=task.needs_verify(),
    )
    return Result(
        task_id=task.id,
        category=task.category,
        condition=condition,
        chosen_substrate=out.chosen_substrate,
        gold_substrate=list(task.gold_substrate),
        answer=out.answer,
        answer_correct=answer_correct,
        substrate_correct=substrate_correct,
        cost=out.cost,
        latency_s=out.latency_s,
        verified=out.verified,
        self_corrected=out.self_corrected,
        failure_mode=failure_mode,
        difficulty=task.difficulty,
    )


def run_condition(
    condition: str,
    tasks: Sequence[Task],
    model: Optional[Model] = None,
    pricing: Optional[Pricing] = None,
) -> List[Result]:
    """Run a single condition (e.g. 'D') over the task set."""
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition {condition!r}; expected one of {CONDITION_ORDER}")
    model = model or StubModel()
    pricing = pricing or Pricing()
    solve = CONDITIONS[condition]
    return [score_output(t, condition, solve(t, model, pricing)) for t in tasks]


def run_all(
    tasks: Sequence[Task],
    conditions: Sequence[str] = CONDITION_ORDER,
    model: Optional[Model] = None,
    pricing: Optional[Pricing] = None,
) -> Dict[str, List[Result]]:
    """Run every requested condition over every task. Returns {condition: [Result]}."""
    model = model or StubModel()
    pricing = pricing or Pricing()
    return {c: run_condition(c, tasks, model, pricing) for c in conditions}
