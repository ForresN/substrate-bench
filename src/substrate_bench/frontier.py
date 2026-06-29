"""Materialise tier-1 `frontier` tasks from benchmark adapters + labels + cache.

Frontier tasks embed benchmark content (e.g. GPQA questions), so they are written
to a gitignored directory and rebuilt at runtime — never committed. Only the
adapters, manifests, and substrate labels live in version control.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .adapters import available, get_adapter
from .schema import Task


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def frontier_dir() -> Path:
    return _repo_root() / "tasks" / "frontier"


def fetch(benchmark_id: str, limit: Optional[int] = None) -> int:
    return get_adapter(benchmark_id).fetch(limit=limit)


def label_summary(benchmark_id: str) -> Dict[str, int]:
    labels = get_adapter(benchmark_id).load_labels()
    out: Dict[str, int] = {"total": len(labels), "labelled": 0, "needs_human_review": 0}
    for rec in labels.values():
        out["labelled" if rec.status == "labelled" else "needs_human_review"] += 1
    return out


def build(
    benchmarks: Optional[Sequence[str]] = None,
    out_dir: Optional[Path] = None,
    include_needs_review: bool = False,
) -> List[Task]:
    """Build frontier tasks for the given benchmarks (default: all) and write them
    to `out_dir` (default tasks/frontier/, gitignored). Returns the Tasks."""
    benchmarks = list(benchmarks) if benchmarks else available()
    out_dir = out_dir or frontier_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks: List[Task] = []
    for bid in benchmarks:
        adapter = get_adapter(bid)
        built = adapter.build_tasks(include_needs_review=include_needs_review)
        for t in built:
            (out_dir / f"{t.id}.json").write_text(
                json.dumps(asdict(t), indent=2) + "\n", encoding="utf-8"
            )
        tasks.extend(built)
    return tasks
