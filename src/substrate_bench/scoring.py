"""Metrics, the failure taxonomy, the composite score, and the acceptance gate.

All model-free. The composite and the gate are the load-bearing pieces: the
autonomous loop merges an experiment only if `evaluate_gate(...)` accepts it.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from statistics import mean
from typing import Any, Dict, List, Optional, Sequence

from .schema import Result

# Composite weights (spec section 6).
COMPOSITE_TASK_WEIGHT = 0.6
COMPOSITE_SUBSTRATE_WEIGHT = 0.4

FAILURE_MODES = (
    "none",
    "wrong_substrate",
    "right_substrate_bad_execution",
    "no_verification",
    "gave_up",
)


def classify_failure(
    *,
    answer: Any,
    answer_correct: bool,
    substrate_correct: bool,
    verified: bool,
    needs_verify: bool,
) -> str:
    """Single source of truth for the per-result failure taxonomy (section 5)."""
    if answer is None:
        return "gave_up"
    if answer_correct:
        return "none"
    if not substrate_correct:
        return "wrong_substrate"
    if needs_verify and not verified:
        return "no_verification"
    return "right_substrate_bad_execution"


def composite_score(task_accuracy: float, substrate_selection_accuracy: float) -> float:
    return (
        COMPOSITE_TASK_WEIGHT * task_accuracy
        + COMPOSITE_SUBSTRATE_WEIGHT * substrate_selection_accuracy
    )


def _switch_rate(results: Sequence[Result]) -> Optional[float]:
    """Self-correction rate on the meta-cognition subset, conditioned on the
    first attempt being wrong (spec section 5). None if the subset is empty."""
    subset = [r for r in results if r.category == "meta_cognition"]
    first_wrong = [r for r in subset if (r.self_corrected or not r.answer_correct)]
    if not first_wrong:
        return None
    return mean(1.0 if r.self_corrected else 0.0 for r in first_wrong)


def aggregate(results: Sequence[Result]) -> Dict[str, Any]:
    """Headline metrics for one condition's results (spec section 5)."""
    if not results:
        raise ValueError("cannot aggregate empty results")
    n = len(results)
    task_acc = mean(1.0 if r.answer_correct else 0.0 for r in results)
    sub_acc = mean(1.0 if r.substrate_correct else 0.0 for r in results)
    mean_cost = mean(r.cost for r in results)
    failure_counts = Counter(r.failure_mode for r in results)
    return {
        "n": n,
        "task_accuracy": task_acc,
        "substrate_selection_accuracy": sub_acc,
        "composite": composite_score(task_acc, sub_acc),
        "mean_cost": mean_cost,
        "total_cost": sum(r.cost for r in results),
        "mean_latency_s": mean(r.latency_s for r in results),
        "cost_adjusted_accuracy": (task_acc / mean_cost) if mean_cost > 0 else float("inf"),
        "verified_rate": mean(1.0 if r.verified else 0.0 for r in results),
        "audit_pass_rate": mean(1.0 if r.audit_passed else 0.0 for r in results),
        "code_execution_rate": mean(1.0 if r.code_executed else 0.0 for r in results),
        "switch_rate": _switch_rate(results),
        "failure_modes": {m: failure_counts.get(m, 0) for m in FAILURE_MODES},
    }


def summarize(results_by_condition: Dict[str, List[Result]]) -> Dict[str, Dict[str, Any]]:
    return {cond: aggregate(res) for cond, res in results_by_condition.items()}


def discrimination(metrics_by_condition: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """How well a task set discriminates routing ability across conditions.

    This is the 'discrimination spread' the reframe leans on: a good substrate
    benchmark separates selective routers (D/E) from the indiscriminate baselines
    (A/B/C) on substrate-selection accuracy.
    """
    if not metrics_by_condition:
        return {}
    sub = {c: m["substrate_selection_accuracy"] for c, m in metrics_by_condition.items()}
    acc = {c: m["task_accuracy"] for c, m in metrics_by_condition.items()}
    routers = [sub[c] for c in ("D", "E") if c in sub]
    best_router = max(routers) if routers else float("nan")
    code_always = sub.get("C")
    return {
        "substrate_discrimination_spread": max(sub.values()) - min(sub.values()),
        "task_accuracy_spread": max(acc.values()) - min(acc.values()),
        "router_vs_codealways_gap": (
            best_router - code_always if (routers and code_always is not None) else None
        ),
        "best_router_substrate_acc": best_router if routers else None,
        "codealways_substrate_acc": code_always,
    }


# --------------------------------------------------------------------------- #
# The acceptance gate (spec section 6)
# --------------------------------------------------------------------------- #
@dataclass
class GateResult:
    accepted: bool
    reasons: List[str] = field(default_factory=list)
    composite_delta: float = 0.0
    cost_ratio: float = 1.0


def evaluate_gate(
    baseline: Dict[str, Any],
    candidate: Dict[str, Any],
    *,
    reproducible: bool,
    max_cost_regression: float = 0.15,
) -> GateResult:
    """An experiment is accepted iff (1) it improves the composite, (2) the run
    is reproducible, and (3) it causes no cost regression beyond +15%."""
    reasons: List[str] = []

    improved = candidate["composite"] > baseline["composite"]
    if not improved:
        reasons.append(
            f"no composite improvement: {candidate['composite']:.4f} "
            f"<= baseline {baseline['composite']:.4f}"
        )

    base_cost = baseline["mean_cost"]
    cost_ratio = (candidate["mean_cost"] / base_cost) if base_cost > 0 else float("inf")
    cost_ok = cost_ratio <= (1.0 + max_cost_regression)
    if not cost_ok:
        reasons.append(
            f"cost regression {(cost_ratio - 1.0) * 100:.1f}% exceeds "
            f"+{max_cost_regression * 100:.0f}% budget"
        )

    if not reproducible:
        reasons.append("run not reproducible (need fixed task set, seeds, logged config + metrics)")

    accepted = improved and cost_ok and reproducible
    if accepted:
        reasons.append("accepted: composite improved, reproducible, within cost budget")
    return GateResult(
        accepted=accepted,
        reasons=reasons,
        composite_delta=candidate["composite"] - baseline["composite"],
        cost_ratio=cost_ratio,
    )
