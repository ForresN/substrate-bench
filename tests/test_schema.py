import json

import pytest

from conftest import TASKS_SMOKE
from substrate_bench.schema import TaskValidationError, load_tasks, validate_task

ORIGINAL_TEN = {
    "lang-001", "exact-001", "exact-002", "sim-001", "sim-002",
    "search-001", "search-002", "rule-001", "social-001", "meta-001",
}


def _base():
    return {
        "id": "t",
        "category": "exact_computation",
        "prompt": "p",
        "gold_substrate": ["exact_computation"],
        "checker": {"type": "numeric_exact", "answer": 1},
        "difficulty": 2,
    }


def test_loads_the_grown_v0_set():
    tasks = load_tasks(TASKS_SMOKE)
    assert len(tasks) >= 46
    ids = {t.id for t in tasks}
    assert ORIGINAL_TEN <= ids
    assert {"verify-101", "sim-106", "social-107", "lang-106"} <= ids


def test_v0_tasks_are_valid_json_and_schema():
    for p in TASKS_SMOKE.glob("*.json"):
        validate_task(json.loads(p.read_text(encoding="utf-8")))


def test_remapped_golds():
    tasks = {t.id: t for t in load_tasks(TASKS_SMOKE)}
    assert tasks["exact-001"].gold_substrate == ["exact_computation"]
    assert tasks["social-001"].gold_substrate == ["social"]
    assert tasks["rule-001"].gold_substrate == ["search"]
    assert tasks["sim-002"].gold_substrate == ["simulation", "exact_computation"]
    assert tasks["meta-001"].gold_substrate == ["exact_computation"]


def test_no_task_uses_the_removed_code_strategy():
    for t in load_tasks(TASKS_SMOKE):
        assert "code" not in t.gold_substrate


def test_provenance_split():
    tasks = {t.id: t for t in load_tasks(TASKS_SMOKE)}
    assert tasks["sim-101"].provenance == "reference"
    assert tasks["lang-101"].provenance == "human_review"
    assert tasks["social-101"].provenance == "human_review"


def test_needs_verify_flag():
    tasks = {t.id: t for t in load_tasks(TASKS_SMOKE)}
    assert tasks["exact-002"].needs_verify() is True
    assert tasks["exact-001"].needs_verify() is False


def test_rejects_code_strategy():
    obj = _base()
    obj["gold_substrate"] = ["code"]
    with pytest.raises(TaskValidationError):
        validate_task(obj)


def test_rejects_unknown_substrate():
    obj = _base()
    obj["gold_substrate"] = ["telepathy"]
    with pytest.raises(TaskValidationError):
        validate_task(obj)


def test_rejects_empty_gold():
    obj = _base()
    obj["gold_substrate"] = []
    with pytest.raises(TaskValidationError):
        validate_task(obj)


def test_rejects_unknown_checker_type():
    obj = _base()
    obj["checker"] = {"type": "vibes"}
    with pytest.raises(TaskValidationError):
        validate_task(obj)


def test_rejects_bad_difficulty():
    obj = _base()
    obj["difficulty"] = 5
    with pytest.raises(TaskValidationError):
        validate_task(obj)


def test_rejects_bad_provenance():
    obj = _base()
    obj["provenance"] = "from_a_solver"
    with pytest.raises(TaskValidationError):
        validate_task(obj)


def test_rejects_missing_field():
    obj = _base()
    del obj["prompt"]
    with pytest.raises(TaskValidationError):
        validate_task(obj)
