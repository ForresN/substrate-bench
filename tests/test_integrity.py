"""Integrity guarantees that matter MORE on contamination-prone frontier data:
the prompt-only view, and the planted-wrong-gold (no-leak) test."""

import json
from dataclasses import replace

from conftest import TASKS_SMOKE
from substrate_bench.model import CallableModel
from substrate_bench.runner import run_condition, score_output
from substrate_bench.conditions import condition_D
from substrate_bench.conditions import Pricing
from substrate_bench.schema import load_tasks, prompt_view

TASKS = {t.id: t for t in load_tasks(TASKS_SMOKE)}


# --- prompt-only view ----------------------------------------------------- #
def test_prompt_view_hides_gold_category_and_substrate():
    t = TASKS["meta-001"]  # numeric_exact, gold 15, gold_substrate exact_computation
    pv = prompt_view(t)
    blob = json.dumps(pv.answer_format) + " " + pv.prompt + " " + pv.id
    assert "gold_substrate" not in pv.__dict__
    assert not hasattr(pv, "category")
    assert "answer" not in pv.answer_format            # gold value never exposed
    assert set(pv.answer_format) <= {"type", "labels"}
    assert str(t.checker["answer"]) not in pv.answer_format.get("type", "")


def test_prompt_view_keeps_public_option_labels_only():
    t = TASKS["lang-001"]  # exact_label with public labels
    pv = prompt_view(t)
    assert pv.answer_format["labels"] == t.checker["labels"]  # public option set is a format hint
    assert "answer" not in pv.answer_format


# --- planted-wrong-gold (no leak) ----------------------------------------- #
def _truth_solver(true_answer):
    """A prompt-only solver that emits the TRUE answer, independent of any gold."""
    def complete(prompt, cot):
        obj = {"strategy": "exact_computation", "executes_code": True,
               "rationale": "computed", "answer": true_answer}
        return json.dumps(obj), 50, 20
    return CallableModel(complete, name="truth")


def test_planted_wrong_gold_is_scored_incorrect():
    t = TASKS["meta-001"]
    true_answer = t.checker["answer"]            # 15
    model = _truth_solver(true_answer)

    # sanity: against the REAL gold the solver is correct
    real = score_output(t, "D", condition_D(t, model, Pricing()))
    assert real.answer_correct is True

    # plant a deliberately WRONG gold; a gold-blind solver still answers 15,
    # so it must now be scored INCORRECT (proves no gold leaks into the solver).
    planted = replace(t, checker={**t.checker, "answer": true_answer + 1})
    bad = score_output(planted, "D", condition_D(planted, model, Pricing()))
    assert bad.answer_correct is False


def test_solver_answer_independent_of_planted_gold():
    t = TASKS["meta-001"]
    model = _truth_solver(t.checker["answer"])
    planted = replace(t, checker={**t.checker, "answer": 9999})
    out = condition_D(planted, model, Pricing())
    assert out.answer == t.checker["answer"]  # not 9999 -> the solver never saw the gold
