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
