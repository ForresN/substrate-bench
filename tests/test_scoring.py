"""Scoring math: composite, aggregate, failure taxonomy, switch rate, gate."""

import math

import pytest

from substrate_bench.schema import Result
from substrate_bench.scoring import (
    aggregate,
    classify_failure,
    composite_score,
    discrimination,
    evaluate_gate,
)


def _result(**kw):
    base = dict(
        task_id="t", category="exact_computation", condition="X",
        declared_strategy="exact_computation", executes_code=True, code_executed=True,
        gold_substrate=["exact_computation"], answer=1,
        answer_correct=True, substrate_correct=True, audit_passed=True, audit_detail="ok",
        cost=0.01, latency_s=0.5, verified=False, self_corrected=False,
        failure_mode="none", difficulty=2,
    )
    base.update(kw)
    return Result(**base)


# --- composite ------------------------------------------------------------- #
def test_composite_weights():
    assert composite_score(1.0, 1.0) == 1.0
    assert composite_score(1.0, 0.0) == pytest.approx(0.6)
    assert composite_score(0.0, 1.0) == pytest.approx(0.4)
    assert composite_score(0.9, 0.9) == pytest.approx(0.9)


# --- failure taxonomy: every branch --------------------------------------- #
def test_classify_failure_none():
    assert classify_failure(answer=1, answer_correct=True, substrate_correct=True,
                            verified=True, needs_verify=False) == "none"


def test_classify_failure_wrong_substrate():
    assert classify_failure(answer=1, answer_correct=False, substrate_correct=False,
                            verified=False, needs_verify=False) == "wrong_substrate"


def test_classify_failure_no_verification():
    assert classify_failure(answer=1, answer_correct=False, substrate_correct=True,
                            verified=False, needs_verify=True) == "no_verification"


def test_classify_failure_bad_execution():
    assert classify_failure(answer=1, answer_correct=False, substrate_correct=True,
                            verified=True, needs_verify=True) == "right_substrate_bad_execution"
    # also when verification isn't required
    assert classify_failure(answer=1, answer_correct=False, substrate_correct=True,
                            verified=False, needs_verify=False) == "right_substrate_bad_execution"


def test_classify_failure_gave_up():
    assert classify_failure(answer=None, answer_correct=False, substrate_correct=False,
                            verified=False, needs_verify=False) == "gave_up"


# --- aggregate ------------------------------------------------------------- #
def test_aggregate_basic_metrics():
    results = [
        _result(answer_correct=True, substrate_correct=True, cost=0.02),
        _result(answer_correct=False, substrate_correct=True, cost=0.02, failure_mode="right_substrate_bad_execution"),
        _result(answer_correct=True, substrate_correct=False, cost=0.04, failure_mode="none"),
        _result(answer_correct=False, substrate_correct=False, cost=0.04, failure_mode="wrong_substrate"),
    ]
    m = aggregate(results)
    assert m["n"] == 4
    assert m["task_accuracy"] == pytest.approx(0.5)
    assert m["substrate_selection_accuracy"] == pytest.approx(0.5)
    assert m["composite"] == pytest.approx(0.5)
    assert m["mean_cost"] == pytest.approx(0.03)
    assert m["cost_adjusted_accuracy"] == pytest.approx(0.5 / 0.03)
    assert m["failure_modes"]["wrong_substrate"] == 1
    assert m["failure_modes"]["right_substrate_bad_execution"] == 1


def test_aggregate_audit_pass_rate():
    results = [
        _result(audit_passed=True),
        _result(audit_passed=False),
        _result(audit_passed=True),
        _result(audit_passed=True),
    ]
    assert aggregate(results)["audit_pass_rate"] == pytest.approx(0.75)


def test_aggregate_switch_rate_meta_only():
    # one meta task, first attempt wrong, self-corrected -> switch_rate 1.0
    res = [
        _result(category="meta_cognition", answer_correct=True, self_corrected=True),
        _result(category="exact_computation", answer_correct=False),  # ignored by switch rate
    ]
    assert aggregate(res)["switch_rate"] == pytest.approx(1.0)

    # meta first attempt wrong, NOT corrected -> 0.0
    res2 = [_result(category="meta_cognition", answer_correct=False, self_corrected=False)]
    assert aggregate(res2)["switch_rate"] == pytest.approx(0.0)

    # meta solved on first try (not corrected, correct) -> excluded -> None
    res3 = [_result(category="meta_cognition", answer_correct=True, self_corrected=False)]
    assert aggregate(res3)["switch_rate"] is None

    # no meta tasks at all -> None
    res4 = [_result(category="exact_computation")]
    assert aggregate(res4)["switch_rate"] is None


# --- the gate -------------------------------------------------------------- #
def _metrics(composite, mean_cost):
    return {"composite": composite, "mean_cost": mean_cost}


def test_gate_accepts_improvement_within_budget():
    g = evaluate_gate(_metrics(0.80, 0.10), _metrics(0.90, 0.11), reproducible=True)
    assert g.accepted
    assert g.composite_delta == pytest.approx(0.10)
    assert g.cost_ratio == pytest.approx(1.1)


def test_gate_rejects_no_composite_improvement():
    g = evaluate_gate(_metrics(0.90, 0.10), _metrics(0.90, 0.10), reproducible=True)
    assert not g.accepted
    assert any("composite" in r for r in g.reasons)


def test_gate_rejects_cost_regression_over_15pct():
    g = evaluate_gate(_metrics(0.80, 0.10), _metrics(0.95, 0.12), reproducible=True)
    assert not g.accepted
    assert any("cost regression" in r for r in g.reasons)


def test_gate_rejects_non_reproducible():
    g = evaluate_gate(_metrics(0.80, 0.10), _metrics(0.95, 0.10), reproducible=False)
    assert not g.accepted
    assert any("reproducible" in r for r in g.reasons)


def test_gate_cost_boundary_exactly_15pct_ok():
    g = evaluate_gate(_metrics(0.80, 0.10), _metrics(0.90, 0.115), reproducible=True)
    assert g.accepted  # +15.0% exactly is within budget


# --- discrimination signal ------------------------------------------------ #
def test_discrimination_spread_and_router_gap():
    metrics = {
        "A": {"substrate_selection_accuracy": 0.2, "task_accuracy": 0.1},
        "B": {"substrate_selection_accuracy": 0.2, "task_accuracy": 0.3},
        "C": {"substrate_selection_accuracy": 0.25, "task_accuracy": 0.25},
        "D": {"substrate_selection_accuracy": 0.9, "task_accuracy": 0.9},
        "E": {"substrate_selection_accuracy": 1.0, "task_accuracy": 1.0},
    }
    d = discrimination(metrics)
    assert d["substrate_discrimination_spread"] == pytest.approx(0.8)   # 1.0 - 0.2
    assert d["router_vs_codealways_gap"] == pytest.approx(0.75)         # best(D,E)=1.0 - C=0.25
    assert d["best_router_substrate_acc"] == pytest.approx(1.0)


def test_discrimination_handles_missing_conditions():
    d = discrimination({"A": {"substrate_selection_accuracy": 0.3, "task_accuracy": 0.3}})
    assert d["router_vs_codealways_gap"] is None  # no D/E or C present
