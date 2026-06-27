"""substrate-bench: a measurement instrument for substrate-selection accuracy.

Most benchmarks ask whether an agent got the right answer. substrate-bench asks
the prior question: did it route to the right computational substrate (language,
code, simulation, search, memory, verify)? The headline number is
substrate-selection accuracy, scored independently of answer accuracy.
"""

from __future__ import annotations

from .conditions import CONDITION_INFO, CONDITION_ORDER, CONDITIONS, Pricing
from .model import CallableModel, Model, ModelResponse, StubModel, parse_answer
from .runner import run_all, run_condition, score_output
from .schema import Result, SolverOutput, Task, load_task, load_tasks
from .scoring import aggregate, composite_score, evaluate_gate, summarize
from .substrates import SUBSTRATES

__version__ = "0.1.0"

__all__ = [
    "Task",
    "Result",
    "SolverOutput",
    "load_task",
    "load_tasks",
    "Model",
    "ModelResponse",
    "StubModel",
    "CallableModel",
    "parse_answer",
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
    "SUBSTRATES",
    "__version__",
]
