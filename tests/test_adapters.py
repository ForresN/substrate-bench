"""BenchmarkAdapter ingest (offline, synthetic items — no network/fetch)."""

import pytest

from substrate_bench.adapters import available, get_adapter
from substrate_bench.adapters.arc_agi_2.adapter import ArcAgi2Adapter
from substrate_bench.adapters.base import BenchmarkAdapter, LabelRecord, RawItem, deterministic_order
from substrate_bench.adapters.gpqa_diamond.adapter import GpqaDiamondAdapter
from substrate_bench.checkers import run_checker
from substrate_bench.schema import prompt_view, validate_task


def test_registry_lists_both_adapters():
    assert set(available()) == {"arc-agi-2", "gpqa-diamond"}


def test_manifests_load_with_licence_and_provenance():
    for bid in available():
        m = get_adapter(bid).manifest
        assert m.licence and m.source_url and m.citation
    # GPQA must be flagged non-redistributable (gated + contamination-sensitive)
    assert get_adapter("gpqa-diamond").manifest.redistributable is False
    assert get_adapter("arc-agi-2").manifest.redistributable is True


def test_deterministic_order_is_stable_and_a_permutation():
    a = deterministic_order("item-x", 4)
    b = deterministic_order("item-x", 4)
    assert a == b and sorted(a) == [0, 1, 2, 3]
    assert deterministic_order("item-y", 4) == deterministic_order("item-y", 4)


# --- ARC ingest ----------------------------------------------------------- #
def test_arc_to_task_carries_benchmark_gold_and_search_label():
    raw = RawItem("abcd1234", {
        "train": [{"input": [[1, 2], [3, 4]], "output": [[4, 3], [2, 1]]}],
        "test": [{"input": [[5, 6], [7, 8]], "output": [[8, 7], [6, 5]]}],
    })
    label = LabelRecord("abcd1234", ["search"], 3, "rule induction", "rubric", "labelled")
    d = ArcAgi2Adapter().to_task_dict(raw, label)
    t = validate_task(d)  # must satisfy the schema
    assert t.gold_substrate == ["search"]
    assert t.checker["type"] == "grid_match"
    assert t.checker["answer"] == [[8, 7], [6, 5]]   # benchmark gold
    assert t.provenance == "benchmark"
    assert t.source["benchmark"] == "arc-agi-2"
    assert run_checker(t, [[8, 7], [6, 5]])
    # the test OUTPUT (gold) must not appear in the prompt the solver sees
    assert "8 7" not in prompt_view(t).prompt


# --- GPQA ingest ---------------------------------------------------------- #
def _gpqa_raw():
    return RawItem("qdeadbeef", {
        "Question": "What is the capital of Examplia?",
        "Correct Answer": "CorrectCity",
        "Incorrect Answer 1": "WrongA",
        "Incorrect Answer 2": "WrongB",
        "Incorrect Answer 3": "WrongC",
    })


def test_gpqa_to_task_shuffles_options_and_records_gold_letter():
    label = LabelRecord("qdeadbeef", ["language"], 3, "recall", "rubric", "labelled")
    d = GpqaDiamondAdapter().to_task_dict(_gpqa_raw(), label)
    t = validate_task(d)
    assert t.checker["type"] == "exact_label"
    assert t.checker["labels"] == ["A", "B", "C", "D"]
    gold_letter = t.checker["answer"]
    # the gold letter must point at the correct option in the prompt
    line = [ln for ln in t.prompt.splitlines() if ln.startswith(f"{gold_letter})")][0]
    assert "CorrectCity" in line
    assert t.gold_substrate == ["language"] and t.provenance == "benchmark"


def test_gpqa_placement_is_deterministic():
    label = LabelRecord("qdeadbeef", ["language"], 3, "", "rubric", "labelled")
    a = GpqaDiamondAdapter().to_task_dict(_gpqa_raw(), label)
    b = GpqaDiamondAdapter().to_task_dict(_gpqa_raw(), label)
    assert a["checker"]["answer"] == b["checker"]["answer"]
    assert a["prompt"] == b["prompt"]


# --- build_tasks excludes needs_human_review ------------------------------ #
class _FakeAdapter(BenchmarkAdapter):
    def __init__(self):
        pass  # skip manifest load

    def fetch(self, limit=None):
        return 0

    def iter_items(self):
        yield RawItem("a", {})
        yield RawItem("b", {})

    def to_task_dict(self, raw, label):
        return {
            "id": f"x-{raw.item_id}", "category": "language", "prompt": "p",
            "gold_substrate": label.gold_substrate, "checker": {"type": "exact_label", "answer": "y", "labels": ["y", "n"]},
            "difficulty": label.difficulty, "provenance": "benchmark",
        }

    def load_labels(self):
        return {
            "a": LabelRecord("a", ["language"], 2, "", "rubric", "labelled"),
            "b": LabelRecord("b", ["language"], 2, "", "rubric", "needs_human_review"),
        }


def test_build_tasks_excludes_needs_human_review_by_default():
    tasks = _FakeAdapter().build_tasks()
    assert [t.id for t in tasks] == ["x-a"]
    assert len(_FakeAdapter().build_tasks(include_needs_review=True)) == 2
