"""The offline mock run must reproduce the substrate asymmetry AND the v0.1
answer/substrate decoupling. These expectations lock the demonstration."""

import pytest

from conftest import TASKS_V0
from substrate_bench.runner import run_all
from substrate_bench.schema import load_tasks
from substrate_bench.scoring import summarize

TASKS = load_tasks(TASKS_V0)
N = len(TASKS)
RES = run_all(TASKS)
M = summarize(RES)


def _by_task(condition):
    return {r.task_id: r for r in RES[condition]}


def test_task_accuracy_matrix():
    assert M["A"]["task_accuracy"] == pytest.approx(5 / N)
    assert M["B"]["task_accuracy"] == pytest.approx(15 / N)   # all linguistic via CoT
    assert M["C"]["task_accuracy"] == pytest.approx(12 / N)
    assert M["D"]["task_accuracy"] == pytest.approx(45 / N)   # all but the meta trap
    assert M["E"]["task_accuracy"] == pytest.approx(1.0)


def test_substrate_selection_matrix():
    assert M["A"]["substrate_selection_accuracy"] == pytest.approx(7 / N)
    assert M["B"]["substrate_selection_accuracy"] == pytest.approx(7 / N)
    assert M["C"]["substrate_selection_accuracy"] == pytest.approx(12 / N)
    assert M["D"]["substrate_selection_accuracy"] == pytest.approx(45 / N)
    assert M["E"]["substrate_selection_accuracy"] == pytest.approx(1.0)


def test_composite_ordering_demonstrates_thesis():
    comp = {c: M[c]["composite"] for c in "ABCDE"}
    assert comp["E"] > comp["D"] > comp["C"] > comp["B"] > comp["A"]


def test_answer_and_substrate_decouple():
    """v0.1's point: the two metrics move independently."""
    # B answers a social task correctly but with the WRONG declared strategy
    # (it says 'language', gold is 'social').
    b = _by_task("B")["social-101"]
    assert b.answer_correct and not b.substrate_correct
    # A on a hard language task: right strategy, wrong answer (no CoT).
    a = _by_task("A")["lang-105"]
    assert a.substrate_correct and not a.answer_correct
    assert a.failure_mode == "right_substrate_bad_execution"


def test_indiscriminate_code_is_wrong_strategy_widely():
    """C declares exact_computation everywhere; at scale that is the wrong
    strategy for most tasks (language/social/simulation/search/verify)."""
    c = _by_task("C")
    for tid in ("lang-101", "social-101", "search-101", "verify-101", "sim-001"):
        assert not c[tid].substrate_correct
        assert c[tid].failure_mode == "wrong_substrate"
    # C is right only where exact_computation IS the strategy
    assert c["exact-001"].substrate_correct and c["exact-001"].answer_correct


def test_router_emits_strategy_and_is_right_except_meta():
    d = _by_task("D")
    assert d["sim-001"].declared_strategy == "simulation"
    assert d["search-101"].declared_strategy == "search"
    assert d["verify-101"].declared_strategy == "verify"
    assert d["social-101"].declared_strategy == "social"
    assert d["meta-001"].declared_strategy == "language"  # the trap
    assert not d["meta-001"].answer_correct


def test_meta_switch_is_unique_to_verifier_condition():
    e_meta = _by_task("E")["meta-001"]
    assert e_meta.self_corrected and e_meta.answer_correct
    assert e_meta.declared_strategy == "exact_computation"
    assert _by_task("D")["meta-001"].self_corrected is False
    assert M["E"]["switch_rate"] == pytest.approx(1.0)
    assert M["D"]["switch_rate"] == pytest.approx(0.0)


def test_audit_passes_for_the_honest_stub():
    for c in "ABCDE":
        assert M[c]["audit_pass_rate"] == pytest.approx(1.0)


def test_executes_code_flag_tracks_strategy():
    # C declares it runs code; A/B declare prose.
    assert _by_task("C")["lang-101"].executes_code is True
    assert _by_task("A")["lang-101"].executes_code is False
    # D's declaration for a search task runs code; for a social task it does not.
    assert _by_task("D")["search-101"].executes_code is True
    assert _by_task("D")["social-101"].executes_code is False
