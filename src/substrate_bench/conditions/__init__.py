"""The five baseline conditions A-E (spec section 4).

Each condition is a uniform solver: `solve(task, model, pricing) -> SolverOutput`.
They share one `execute(...)` seam that runs a chosen substrate -- `language`
goes through the model, the computational substrates go through the trusted
references. Cost and latency are deterministic synthetic estimates so runs are
reproducible (the gate's reproducibility clause depends on this).

    A  Direct          implicit substrate = language, no CoT
    B  CoT             implicit substrate = language, with CoT
    C  Code-always     implicit substrate = code, indiscriminately (the trap)
    D  Router          selects one substrate by category, then executes
    E  Router+Verify   D, plus a verifier that can refute and re-route
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Tuple

from ..checkers import is_verifiable, run_checker
from ..model import Model, estimate_tokens
from ..references import gold
from ..schema import SolverOutput, Task
from ..substrates import COMPUTATIONAL_SUBSTRATES, route

CONDITION_ORDER = ("A", "B", "C", "D", "E")
CONDITION_INFO: Dict[str, Tuple[str, str]] = {
    "A": ("Direct", "Direct LLM answer (floor: pure next-token)"),
    "B": ("CoT", "LLM + chain-of-thought"),
    "C": ("Code-always", "LLM with code tool always on (indiscriminate)"),
    "D": ("Router", "Router that selects one substrate"),
    "E": ("Router+Verify", "Router + verifier (verify before commit)"),
}


@dataclass
class Pricing:
    """Flat, deterministic price/latency model (spec section 5: cost = tokens x
    price, plus tool/compute time priced flat)."""

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


def execute(
    substrate: str, task: Task, model: Model, *, cot: bool
) -> Tuple[Any, str, int, int, int]:
    """Run one substrate. Returns (answer, used_substrate, in_tok, out_tok, n_tools).

    `language` is answered by the model. A computational substrate succeeds iff
    it is appropriate for the task (in `gold_substrate`); otherwise it returns a
    deterministic wrong answer -- e.g. reaching for closed-form `code` on the
    drag task yields the vacuum range.
    """
    if substrate == "language":
        r = model.answer(task, cot=cot)
        return r.answer, "language", r.input_tokens, r.output_tokens, 0
    if substrate in COMPUTATIONAL_SUBSTRATES:
        in_tok = estimate_tokens(task.prompt)
        out_tok = 30  # framing / emitting the tool result
        ans = gold.gold_answer(task) if substrate in task.gold_substrate else gold.wrong_answer(task)
        return ans, substrate, in_tok, out_tok, 1
    raise ValueError(f"{substrate!r} is not a primary execution substrate in v0")


def _alternative_substrate(task: Task, chosen: str) -> str:
    """Pick a better substrate to switch to after a verifier refutation."""
    for s in task.gold_substrate:
        if s in COMPUTATIONAL_SUBSTRATES and s != chosen:
            return s
    return task.gold_substrate[0]


# --------------------------------------------------------------------------- #
# The conditions
# --------------------------------------------------------------------------- #
def condition_A(task: Task, model: Model, pricing: Pricing) -> SolverOutput:
    ans, sub, it, ot, nt = execute("language", task, model, cot=False)
    cost, lat = _account(pricing, it, ot, nt)
    return SolverOutput(ans, sub, verified=False, self_corrected=False, cost=cost, latency_s=lat, raw="A:direct")


def condition_B(task: Task, model: Model, pricing: Pricing) -> SolverOutput:
    ans, sub, it, ot, nt = execute("language", task, model, cot=True)
    cost, lat = _account(pricing, it, ot, nt)
    return SolverOutput(ans, sub, verified=False, self_corrected=False, cost=cost, latency_s=lat, raw="B:cot")


def condition_C(task: Task, model: Model, pricing: Pricing) -> SolverOutput:
    # Always reach for code, regardless of whether it is the right substrate.
    ans, sub, it, ot, nt = execute("code", task, model, cot=False)
    cost, lat = _account(pricing, it, ot, nt)
    return SolverOutput(ans, sub, verified=False, self_corrected=False, cost=cost, latency_s=lat, raw="C:code-always")


def condition_D(task: Task, model: Model, pricing: Pricing) -> SolverOutput:
    chosen = route(task.category)
    ans, sub, it, ot, nt = execute(chosen, task, model, cot=True)
    cost, lat = _account(pricing, it, ot, nt)
    return SolverOutput(ans, sub, verified=False, self_corrected=False, cost=cost, latency_s=lat, raw=f"D:route->{chosen}")


def condition_E(task: Task, model: Model, pricing: Pricing) -> SolverOutput:
    chosen = route(task.category)
    ans, sub, it, ot, nt = execute(chosen, task, model, cot=True)

    # Verify pass: a small extra call plus (for verifiable tasks) a check tool.
    it += estimate_tokens(task.prompt) // 2
    ot += 20
    self_corrected = False
    if is_verifiable(task):
        nt += 1  # the verification check itself
        if not run_checker(task, ans):
            # Refuted: re-route to an appropriate substrate and re-execute.
            alt = _alternative_substrate(task, chosen)
            ans, sub, it2, ot2, nt2 = execute(alt, task, model, cot=True)
            it += it2
            ot += ot2
            nt += nt2
            self_corrected = True

    cost, lat = _account(pricing, it, ot, nt)
    return SolverOutput(
        ans, sub, verified=True, self_corrected=self_corrected, cost=cost, latency_s=lat,
        raw=f"E:route->{route(task.category)}" + (f"=>switch->{sub}" if self_corrected else ""),
    )


CONDITIONS: Dict[str, Callable[[Task, Model, Pricing], SolverOutput]] = {
    "A": condition_A,
    "B": condition_B,
    "C": condition_C,
    "D": condition_D,
    "E": condition_E,
}
