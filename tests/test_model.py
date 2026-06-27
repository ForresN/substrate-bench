"""The provider seam: best-effort answer parsing + a non-stub Model adapter.

This proves the package is genuinely provider-agnostic -- a model that is not
the StubModel plugs in through `CallableModel` and produces checker-passing
answers, all offline.
"""

from conftest import TASKS_V0
from substrate_bench.checkers import run_checker
from substrate_bench.conditions import Pricing
from substrate_bench.model import CallableModel, Model, parse_answer
from substrate_bench.references import gold
from substrate_bench.runner import run_condition
from substrate_bench.schema import load_tasks

TASKS = {t.id: t for t in load_tasks(TASKS_V0)}


# --- parse_answer: one case per checker type ------------------------------- #
def test_parse_exact_label_from_prose():
    t = TASKS["lang-001"]
    assert parse_answer(t, "I think the tone is clearly positive.\nAnswer: positive") == "positive"


def test_parse_numeric_exact_ignores_grouping_and_prose():
    t = TASKS["meta-001"]
    assert parse_answer(t, "It is C(6,2). Answer: 15 handshakes total.") == 15


def test_parse_numeric_tol_float():
    t = TASKS["sim-001"]
    assert abs(parse_answer(t, "Answer: 99.3 metres") - 99.3) < 1e-9


def test_parse_sequence_json():
    t = TASKS["search-002"]
    ans = parse_answer(t, 'Here is the path.\nAnswer: ["D","D","R","R","D","D","R","R"]')
    assert ans == ["D", "D", "R", "R", "D", "D", "R", "R"]


def test_parse_grid_json():
    t = TASKS["rule-001"]
    ans = parse_answer(t, "Answer: [[2,1,9],[5,4,3],[8,7,6]]")
    assert run_checker(t, ans)


def test_parse_returns_none_on_garbage_numeric():
    t = TASKS["exact-001"]
    assert parse_answer(t, "no number here") is None


# --- CallableModel end-to-end --------------------------------------------- #
def _oracle_complete(canned):
    """A fake provider: returns a canned 'Answer: ...' line per task substring."""

    def complete(prompt, cot):
        for key, text in canned.items():
            if key in prompt:
                return text, 50, 20
        return "Answer: unknown", 50, 5

    return complete


def test_callable_model_satisfies_protocol():
    m = CallableModel(_oracle_complete({}))
    assert isinstance(m, Model)
    assert m.name == "callable"


def test_callable_model_produces_checker_passing_language_answers():
    # A provider that answers the linguistic tasks correctly via the parser.
    canned = {
        "sentiment": "Answer: positive",
        "Sally": "Answer: basket",
    }
    model = CallableModel(_oracle_complete(canned), name="oracle")
    # Condition A routes language tasks to the model; both should pass.
    results = {r.task_id: r for r in run_condition("A", list(TASKS.values()), model=model)}
    assert results["lang-001"].answer_correct
    assert results["social-001"].answer_correct


def test_callable_model_drives_router_condition_offline():
    """Condition D uses the model only for the language substrate; computational
    substrates go through references, so a tiny canned model still scores well."""
    canned = {"sentiment": "Answer: positive", "Sally": "Answer: basket"}
    model = CallableModel(_oracle_complete(canned), name="oracle")
    results = {r.task_id: r for r in run_condition("D", list(TASKS.values()), model=model)}
    # the computational tasks are answered by the references regardless of model
    assert results["sim-001"].answer_correct
    assert results["search-001"].answer_correct
    assert results["lang-001"].answer_correct
