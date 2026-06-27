"""Baseline registry (contract v0.1 §4) with a human-only promotion guardrail.

Keyed by `(task_set, solver_id)`. The autonomous loop may **read** a baseline
(the gate needs it) but must **never promote** -- otherwise an agent could quietly
lower its own bar and "pass" the gate by regressing the baseline. Promotion is a
human action: any non-interactive caller gets read-only access and a hard error
on a promote attempt. The registry is committed, so promotions are visible (and
tamper-evident) in git history.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional


class PromotionDenied(PermissionError):
    """A non-interactive (agent) caller attempted to promote a baseline."""


def registry_dir(root: str | Path) -> Path:
    return Path(root) / "baselines"


def baseline_path(root: str | Path, task_set: str, solver_id: str) -> Path:
    return registry_dir(root) / f"{task_set}__{solver_id}.json"


def show_baseline(root: str | Path, task_set: str, solver_id: str) -> Optional[Dict[str, Any]]:
    """Read a recorded baseline. Always allowed (read-only)."""
    p = baseline_path(root, task_set, solver_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _baseline_payload(task_set: str, solver_id: str, run_payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "task_set": task_set,
        "solver_id": solver_id,
        "config": run_payload.get("config", {}),
        "metrics": run_payload.get("metrics", {}),
        "composite_weights": {"task": 0.6, "substrate": 0.4},
    }


def promote_baseline(
    root: str | Path,
    task_set: str,
    solver_id: str,
    run_payload: Dict[str, Any],
    *,
    interactive: bool,
    confirm: Callable[[], bool] = lambda: True,
) -> Path:
    """Record a run as the baseline for (task_set, solver_id).

    HARD GUARDRAIL: `interactive` must be True (a human at a TTY). A False value
    -- the autonomous loop, CI, any subprocess without a TTY -- raises
    PromotionDenied. `confirm` is the human's y/N confirmation.
    """
    if not interactive:
        raise PromotionDenied(
            "baseline promotion is human-only (contract §4): refusing in a "
            "non-interactive context. The autonomous loop has read-only access."
        )
    if not confirm():
        raise PromotionDenied("promotion aborted by user")

    p = baseline_path(root, task_set, solver_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = _baseline_payload(task_set, solver_id, run_payload)
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return p
