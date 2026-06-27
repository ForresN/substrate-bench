"""Baseline registry (contract §4): read is open, promote is human-only."""

import json

import pytest

from substrate_bench.registry import (
    PromotionDenied,
    baseline_path,
    promote_baseline,
    show_baseline,
)

RUN = {
    "config": {"task_set": "v0", "solver": "stub", "seed": 0},
    "metrics": {"E": {"composite": 1.0, "mean_cost": 0.004}},
    "results": {},
}


def test_show_missing_returns_none(tmp_path):
    assert show_baseline(tmp_path, "v0", "stub") is None


def test_non_interactive_promote_is_denied(tmp_path):
    """The autonomous loop (no TTY) must NOT be able to promote."""
    with pytest.raises(PromotionDenied):
        promote_baseline(tmp_path, "v0", "stub", RUN, interactive=False)
    assert not baseline_path(tmp_path, "v0", "stub").exists()


def test_interactive_promote_writes_and_is_readable(tmp_path):
    path = promote_baseline(tmp_path, "v0", "stub", RUN, interactive=True, confirm=lambda: True)
    assert path.exists()
    data = show_baseline(tmp_path, "v0", "stub")
    assert data["task_set"] == "v0" and data["solver_id"] == "stub"
    assert data["metrics"]["E"]["composite"] == 1.0


def test_interactive_promote_can_be_aborted(tmp_path):
    with pytest.raises(PromotionDenied):
        promote_baseline(tmp_path, "v0", "stub", RUN, interactive=True, confirm=lambda: False)
    assert not baseline_path(tmp_path, "v0", "stub").exists()


def test_show_is_always_allowed_after_promote(tmp_path):
    promote_baseline(tmp_path, "v0", "stub", RUN, interactive=True)
    # a subsequent read (the gate's access) needs no interactivity
    assert show_baseline(tmp_path, "v0", "stub") is not None
