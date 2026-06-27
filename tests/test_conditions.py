"""The offline mock run must reproduce the substrate-asymmetry the spec is built
to expose. These expectations lock the demonstration in place."""

import pytest

from conftest import TASKS_V0
from substrate_bench.runner import run_all
from substrate_bench.schema import load_tasks
from substrate_bench.scoring import summarize

TASKS = load_tasks(TASKS_V0)
RES = run_all(TASKS)
M = summarize(RES)


def _by_task(condition):
    return {r.task_id: r for r in RES[condition]}


def test_task_accuracy_matrix():
    assert M["A"]["task_accuracy"] == pytest.approx(0.10)
    assert M["B"]["task_accuracy"] == pytest.approx(0.20)
    assert M["C"]["task_accuracy"] == pytest.approx(0.50)
    assert M["D"]["task_accuracy"] == pytest.approx(0.90)
    assert M["E"]["task_accuracy"] == pytest.approx(1.00)


def test_substrate_selection_matrix():
    assert M["A"]["substrate_selection_accuracy"] == pytest.approx(0.20)
    assert M["B"]["substrate_selection_accuracy"] == pytest.approx(0.20)
    assert M["C"]["substrate_selection_accuracy"] == pytest.approx(0.50)
    assert M["D"]["substrate_selection_accuracy"] == pytest.approx(0.90)
    assert M["E"]["substrate_selection_accuracy"] == pytest.approx(1.00)


def test_composite_ordering_demonstrates_thesis():
    comp = {c: M[c]["composite"] for c in "ABCDE"}
    # selective routing (D, E) beats indiscriminate code (C) beats no tools (A, B)
    assert comp["E"] > comp["D"] > comp["C"] > comp["B"] >= comp["A"]


def test_indiscriminate_code_loses_on_language_tasks():
    """The core asymmetry: condition C routing to code is WRONG on lang/social."""
    c = _by_task("C")
    for tid in ("lang-001", "social-001"):
        assert not c[tid].substrate_correct
        assert not c[tid].answer_correct
        assert c[tid].failure_mode == "wrong_substrate"
    # while a router (D) gets them right
    d = _by_task("D")
    for tid in ("lang-001", "social-001"):
        assert d[tid].answer_correct and d[tid].substrate_correct


def test_drag_needs_simulation_not_code():
    """sim-001 has no closed form: C's code reflex fails, D's simulation works."""
    assert not _by_task("C")["sim-001"].answer_correct
    assert _by_task("D")["sim-001"].answer_correct
    assert _by_task("D")["sim-001"].chosen_substrate == "simulation"


def test_cot_rescues_theory_of_mind_without_changing_substrate():
    """A (no CoT) gets the right substrate but bad execution on social-001;
    B (CoT) fixes the execution."""
    a = _by_task("A")["social-001"]
    b = _by_task("B")["social-001"]
    assert a.substrate_correct and not a.answer_correct
    assert a.failure_mode == "right_substrate_bad_execution"
    assert b.answer_correct


def test_meta_switch_is_unique_to_verifier_condition():
    """meta-001 is the switch task: only E detects the bad language route and
    re-routes to code; D fails it; C wins it only by always coding."""
    assert _by_task("E")["meta-001"].self_corrected is True
    assert _by_task("E")["meta-001"].answer_correct is True
    assert _by_task("E")["meta-001"].chosen_substrate == "code"
    assert _by_task("D")["meta-001"].self_corrected is False
    assert _by_task("D")["meta-001"].answer_correct is False
    assert M["E"]["switch_rate"] == pytest.approx(1.0)
    assert M["D"]["switch_rate"] == pytest.approx(0.0)


def test_only_E_verifies_everything():
    assert M["E"]["verified_rate"] == pytest.approx(1.0)
    assert M["A"]["verified_rate"] == pytest.approx(0.0)


def test_cost_ordering_tools_cost_more_than_nothing():
    # A (no tools, no CoT) is the cheapest; E (route+verify+switch) costs more.
    assert M["A"]["mean_cost"] < M["E"]["mean_cost"]
