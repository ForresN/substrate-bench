"""The five baseline conditions A-E (spec section 4, contract v0.1 §2).

Each condition is a uniform solver: `solve(task, model, pricing) -> SolverOutput`.
Conditions are model-agnostic policy wrappers over `Model.solve(...)`:

    A  Direct          fixed declaration: language, no code, no CoT
    B  CoT             fixed declaration: language, no code, with CoT
    C  Code-always     fixed declaration: exact_computation, code on (the trap)
    D  Router          model EMITS its strategy declaration
    E  Router+Verify   D, plus a verifier that can refute and re-route

Cost/latency are deterministic synthetic estimates so runs are reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Tuple

from ..checkers import is_verifiable, run_checker
from ..model import Model, estimate_tokens
from ..schema import SolverOutput, Task
from ..substrates import CODE_BEARING_STRATEGIES, default_executes_code

CONDITION_ORDER = ("A", "B", "C", "D", "E")
CONDITION_INFO: Dict[str, Tuple[str, str]] = {
    "A": ("Direct", "Direct LLM answer (floor: pure next-token)"),
    "B": ("CoT", "LLM + chain-of-thought"),
    "C": ("Code-always", "Always declares exact_computation + runs code (indiscriminate)"),
    "D": ("Router", "Model emits its own strategy declaration"),
    "E": ("Router+Verify", "Router + verifier (verify before commit, re-route on refute)"),
}


@dataclass
class Pricing:
    """Flat, deterministic price/latency model (spec section 5)."""

    in_per_1k: float = 0.003
    out_per_1k: float = 0.015
    tool_cost: float = 0.0005
    base_latency_s: float = 0.20
    token_latency_per_1k: float = 0.80
    tool_latency_s: float = 0.30


def _account(pricing: Pricing, in_tok: int, out_tok: int, n_tools: int) -> Tuple[float, float]:
    cost = (
        in_tok / 1000.0 * pricing.in_per_1k
        + out_tok / 1000.0 * pricing.out_per_1k
        + n_tools * pricing.tool_cost
    )
    latency = (
        pricing.base_latency_s
        + out_tok / 1000.0 * pricing.token_latency_per_1k
        + n_tools * pricing.tool_latency_s
    )
    return round(cost, 8), round(latency, 6)


def _alternative_strategy(task: Task, chosen: str) -> str:
    """Pick a better strategy to switch to after a verifier refutation."""
    for s in task.gold_substrate:
        if s in CODE_BEARING_STRATEGIES and s != chosen:
            return s
    return task.gold_substrate[0]


def _run(
    model: Model,
    task: Task,
    pricing: Pricing,
    *,
    force_strategy,
    force_code,
    cot: bool,
    verify: bool,
    label: str,
) -> SolverOutput:
    resp = model.solve(task, force_strategy=force_strategy, force_executes_code=force_code, cot=cot)
    in_tok, out_tok = resp.input_tokens, resp.output_tokens
    n_tools = 1 if resp.code_executed else 0
    final = resp
    self_corrected = False

    if verify:
        in_tok += estimate_tokens(task.prompt) // 2
        out_tok += 20
        if is_verifiable(task):
            n_tools += 1  # the verification check itself
            if not run_checker(task, resp.answer):
                alt = _alternative_strategy(task, resp.declaration.strategy)
                resp2 = model.solve(
                    task, force_strategy=alt, force_executes_code=default_executes_code(alt), cot=cot
                )
                final = resp2
                in_tok += resp2.input_tokens
                out_tok += resp2.output_tokens
                n_tools += 1 if resp2.code_executed else 0
                self_corrected = True

    cost, lat = _account(pricing, in_tok, out_tok, n_tools)
    return SolverOutput(
        declaration=final.declaration,
        answer=final.answer,
        code_executed=final.code_executed,
        verified=verify,
        self_corrected=self_corrected,
        cost=cost,
        latency_s=lat,
        raw=label,
    )


def condition_A(task: Task, model: Model, pricing: Pricing) -> SolverOutput:
    return _run(model, task, pricing, force_strategy="language", force_code=False, cot=False, verify=False, label="A:direct")


def condition_B(task: Task, model: Model, pricing: Pricing) -> SolverOutput:
    return _run(model, task, pricing, force_strategy="language", force_code=False, cot=True, verify=False, label="B:cot")


def condition_C(task: Task, model: Model, pricing: Pricing) -> SolverOutput:
    return _run(model, task, pricing, force_strategy="exact_computation", force_code=True, cot=False, verify=False, label="C:code-always")


def condition_D(task: Task, model: Model, pricing: Pricing) -> SolverOutput:
    return _run(model, task, pricing, force_strategy=None, force_code=None, cot=True, verify=False, label="D:route")


def condition_E(task: Task, model: Model, pricing: Pricing) -> SolverOutput:
    return _run(model, task, pricing, force_strategy=None, force_code=None, cot=True, verify=True, label="E:route+verify")


CONDITIONS: Dict[str, Callable[[Task, Model, Pricing], SolverOutput]] = {
    "A": condition_A,
    "B": condition_B,
    "C": condition_C,
    "D": condition_D,
    "E": condition_E,
}
