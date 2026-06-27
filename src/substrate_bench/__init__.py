"""substrate-bench: a measurement instrument for substrate-selection accuracy.

Most benchmarks ask whether an agent got the right answer. substrate-bench asks
the prior question: did it recognise what kind of thinking the task required and
route to the right cognitive strategy? v0.1 splits *strategy* (the scored axis)
from *execution medium* (`executes_code`), requires a structured route
declaration, scores declaration and answer independently, and audits their
consistency. The headline number is substrate-selection accuracy.
"""

from __future__ import annotations

from .audit import RouteAudit, audit_consistency
from .conditions import CONDITION_INFO, CONDITION_ORDER, CONDITIONS, Pricing
from .model import (
    CallableModel,
    Model,
    RouteDeclarationError,
    SolverResponse,
    StubModel,
    parse_answer,
    parse_declaration,
)
from .registry import PromotionDenied, promote_baseline, show_baseline
from .runner import run_all, run_condition, score_output
from .schema import (
    Result,
    RouteDeclaration,
    SolverOutput,
    Task,
    load_task,
    load_tasks,
)
from .scoring import aggregate, composite_score, evaluate_gate, summarize
from .substrates import STRATEGIES, TASK_BEARING_STRATEGIES, default_executes_code

__version__ = "0.1.0"

__all__ = [
    "Task",
    "Result",
    "RouteDeclaration",
    "SolverOutput",
    "SolverResponse",
    "load_task",
    "load_tasks",
    "Model",
    "StubModel",
    "CallableModel",
    "parse_answer",
    "parse_declaration",
    "RouteDeclarationError",
    "RouteAudit",
    "audit_consistency",
    "Pricing",
    "CONDITIONS",
    "CONDITION_ORDER",
    "CONDITION_INFO",
    "run_all",
    "run_condition",
    "score_output",
    "aggregate",
    "summarize",
    "composite_score",
    "evaluate_gate",
    "show_baseline",
    "promote_baseline",
    "PromotionDenied",
    "STRATEGIES",
    "TASK_BEARING_STRATEGIES",
    "default_executes_code",
    "__version__",
]
