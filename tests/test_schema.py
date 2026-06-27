import json

import pytest

from conftest import TASKS_V0
from substrate_bench.schema import TaskValidationError, load_tasks, validate_task


def _base():
    return {
        "id": "t",
        "category": "exact_computation",
        "prompt": "p",
        "gold_substrate": ["code"],
        "checker": {"type": "numeric_exact", "answer": 1},
        "difficulty": 2,
    }


def test_loads_all_ten_v0_tasks():
    tasks = load_tasks(TASKS_V0)
    assert len(tasks) == 10
    ids = {t.id for t in tasks}
    assert ids == {
        "lang-001", "exact-001", "exact-002", "sim-001", "sim-002",
        "search-001", "search-002", "rule-001", "social-001", "meta-001",
    }


def test_v0_tasks_are_valid_json_and_schema():
    for p in TASKS_V0.glob("*.json"):
        validate_task(json.loads(p.read_text(encoding="utf-8")))


def test_needs_verify_flag():
    tasks = {t.id: t for t in load_tasks(TASKS_V0)}
    assert tasks["exact-002"].needs_verify() is True
    assert tasks["exact-001"].needs_verify() is False


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


def test_rejects_missing_field():
    obj = _base()
    del obj["prompt"]
    with pytest.raises(TaskValidationError):
        validate_task(obj)
