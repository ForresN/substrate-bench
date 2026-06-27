"""Prove the gold answers stored in the task JSON were produced by the trusted
deterministic references -- not by a model. Re-derive each and compare."""

import math

from conftest import TASKS_V0
from substrate_bench.checkers import run_checker
from substrate_bench.references import gold, search_ref
from substrate_bench.schema import load_tasks

TASKS = {t.id: t for t in load_tasks(TASKS_V0)}


def test_numeric_exact_golds_match_reference():
    for tid in ("exact-001", "exact-002", "meta-001"):
        t = TASKS[tid]
        assert gold.reference_value(t) == t.checker["answer"]


def test_numeric_tol_references_match_reference_impl():
    for tid in ("sim-001", "sim-002"):
        t = TASKS[tid]
        recomputed = gold.reference_value(t)
        assert math.isclose(recomputed, t.checker["reference"], abs_tol=1e-4)


def test_grid_match_gold_matches_reference():
    t = TASKS["rule-001"]
    assert gold.reference_value(t) == [list(r) for r in t.checker["answer"]]


def test_sequence_golds_are_valid_and_optimal():
    h = TASKS["search-001"]
    moves = gold.reference_value(h)
    assert len(moves) == h.checker["optimal_length"] == (2 ** h.checker["n"] - 1)
    assert run_checker(h, moves)

    g = TASKS["search-002"]
    path = gold.reference_value(g)
    assert len(path) == g.checker["optimal_length"]
    assert run_checker(g, path)


def test_drag_range_is_far_below_vacuum_range():
    """Sanity: the drag task must actually require simulation -- the closed-form
    (vacuum) answer should be badly outside tolerance."""
    from substrate_bench.references.dynamics import projectile_vacuum
    t = TASKS["sim-001"]
    vac = projectile_vacuum(t.checker["params"])
    assert vac > t.checker["reference"] + 10 * t.checker["tol"]


def test_gold_answer_passes_its_own_checker_for_all_tasks():
    for t in TASKS.values():
        assert run_checker(t, gold.gold_answer(t)), t.id


def test_wrong_answer_fails_its_own_checker_for_all_tasks():
    for t in TASKS.values():
        assert not run_checker(t, gold.wrong_answer(t)), t.id


def test_every_reference_task_gold_is_reference_derived():
    """Provenance proof: for every provenance=='reference' task, the stored gold
    equals what the trusted reference re-derives -- no solver in the loop."""
    for t in TASKS.values():
        if t.provenance != "reference":
            continue
        derived = gold.reference_value(t)
        ctype = t.checker["type"]
        if ctype == "numeric_exact":
            assert derived == t.checker["answer"], t.id
        elif ctype == "numeric_tol":
            assert math.isclose(derived, t.checker["reference"], abs_tol=1e-4), t.id
        elif ctype == "grid_match":
            assert derived == [list(r) for r in t.checker["answer"]], t.id
        elif ctype == "exact_label":  # verify tasks
            assert derived == t.checker["answer"], t.id
        elif ctype == "sequence_valid":
            assert run_checker(t, derived), t.id


def test_human_review_tasks_are_labelled_not_reference_derived():
    human = [t for t in TASKS.values() if t.provenance == "human_review"]
    assert human  # the language/social tasks exist
    for t in human:
        assert t.checker["type"] == "exact_label"
        assert "verify_impl" not in t.checker  # not a reference computation


def test_waterjug_reference_is_valid_and_optimal():
    from substrate_bench.references import search_ref
    sol = search_ref.waterjug_solve(5, 3, 4)
    assert search_ref.waterjug_validate(5, 3, 4, sol)
    # a shorter prefix is not a solution
    assert not search_ref.waterjug_validate(5, 3, 4, sol[:-1])


def test_verify_labels_match_validators():
    from substrate_bench.references import verify_ref
    assert verify_ref.is_prime(437) is False  # 19 * 23
    assert verify_ref.balanced_parens("([)]") is False
    assert verify_ref.nqueens_valid([0, 2, 4, 1, 3, 5], 6) is False
    assert verify_ref.latin_square_valid([[1, 2, 3, 4], [2, 1, 4, 3], [3, 4, 1, 2], [4, 3, 2, 1]]) is True
