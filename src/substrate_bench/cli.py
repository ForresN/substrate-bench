"""`substrate-bench` command line: run the benchmark and (re)generate the board.

    substrate-bench run --condition all --tasks v0
    substrate-bench leaderboard --from results/v0-stub.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .conditions import CONDITION_INFO, CONDITION_ORDER, Pricing
from .leaderboard import write_leaderboard
from .model import StubModel
from .runner import run_all
from .schema import Result, load_tasks
from .scoring import summarize

# Registry of available (offline) solvers. Real providers register here.
SOLVERS = {"stub": StubModel, "mock": StubModel}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def find_tasks_dir(task_set: str, override: Optional[str] = None) -> Path:
    if override:
        p = Path(override)
        if p.is_dir():
            return p
        raise FileNotFoundError(f"--tasks-dir not found: {p}")
    for base in (_repo_root(), Path.cwd()):
        cand = base / "tasks" / task_set
        if cand.is_dir():
            return cand
    raise FileNotFoundError(f"could not locate tasks/{task_set} (try --tasks-dir)")


def _parse_conditions(value: str) -> List[str]:
    if value.strip().lower() == "all":
        return list(CONDITION_ORDER)
    out = []
    for tok in value.replace(",", " ").split():
        c = tok.strip().upper()
        if c not in CONDITION_ORDER:
            raise SystemExit(f"unknown condition {c!r}; expected subset of {CONDITION_ORDER} or 'all'")
        out.append(c)
    return out


def run_benchmark(
    task_set: str = "v0",
    conditions: Sequence[str] = CONDITION_ORDER,
    solver: str = "stub",
    tasks_dir: Optional[str] = None,
    pricing: Optional[Pricing] = None,
):
    tasks = load_tasks(find_tasks_dir(task_set, tasks_dir))
    model = SOLVERS[solver]()
    results = run_all(tasks, conditions, model=model, pricing=pricing or Pricing())
    metrics = summarize(results)
    return tasks, results, metrics


def _results_payload(config, results, metrics) -> dict:
    return {
        "config": config,
        "metrics": metrics,
        "results": {c: [r.to_dict() for r in rs] for c, rs in results.items()},
    }


def _load_payload(path: str | Path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    results = {c: [Result.from_dict(d) for d in rs] for c, rs in data["results"].items()}
    return data["config"], results, data["metrics"]


def _print_summary(metrics: Dict[str, dict]) -> None:
    print(f"\n{'Cond':<14}{'Sub-acc':>9}{'Task-acc':>9}{'Composite':>11}{'MeanCost':>11}{'Switch':>9}")
    print("-" * 63)
    for c in CONDITION_ORDER:
        if c not in metrics:
            continue
        m = metrics[c]
        name = CONDITION_INFO[c][0]
        sw = "n/a" if m["switch_rate"] is None else f"{m['switch_rate'] * 100:.0f}%"
        print(
            f"{c + ' ' + name:<14}"
            f"{m['substrate_selection_accuracy'] * 100:>8.0f}%"
            f"{m['task_accuracy'] * 100:>8.0f}%"
            f"{m['composite']:>11.3f}"
            f"{m['mean_cost']:>11.6f}"
            f"{sw:>9}"
        )
    print()


def cmd_run(ns: argparse.Namespace) -> int:
    conditions = _parse_conditions(ns.condition)
    tasks, results, metrics = run_benchmark(
        task_set=ns.tasks, conditions=conditions, solver=ns.solver, tasks_dir=ns.tasks_dir
    )
    config = {
        "task_set": ns.tasks,
        "n_tasks": len(tasks),
        "conditions": conditions,
        "solver": ns.solver,
        "seed": ns.seed,
        "pricing": asdict(Pricing()),
        "composite_weights": {"task": 0.6, "substrate": 0.4},
    }

    root = _repo_root()
    out_path = Path(ns.out) if ns.out else root / "results" / f"{ns.tasks}-{ns.solver}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(_results_payload(config, results, metrics), indent=2), encoding="utf-8")

    board_path = Path(ns.leaderboard) if ns.leaderboard else root / "leaderboard.md"
    write_leaderboard(board_path, results, metrics, solver_name=ns.solver, task_set=ns.tasks)

    _print_summary(metrics)
    print(f"results   -> {out_path}")
    print(f"leaderboard -> {board_path}")
    return 0


def cmd_leaderboard(ns: argparse.Namespace) -> int:
    config, results, metrics = _load_payload(ns.from_)
    board_path = Path(ns.leaderboard) if ns.leaderboard else _repo_root() / "leaderboard.md"
    write_leaderboard(
        board_path, results, metrics,
        solver_name=config.get("solver", "?"), task_set=config.get("task_set", "?"),
    )
    print(f"leaderboard -> {board_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="substrate-bench", description="Substrate-selection benchmark.")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run conditions over a task set and regenerate the leaderboard")
    r.add_argument("--condition", default="all", help="'all' or a subset like 'D,E' (default: all)")
    r.add_argument("--tasks", default="v0", help="task set name under tasks/ (default: v0)")
    r.add_argument("--tasks-dir", default=None, help="explicit path to a task directory")
    r.add_argument("--solver", default="stub", choices=sorted(SOLVERS), help="solver/model (default: stub)")
    r.add_argument("--seed", type=int, default=0, help="seed, recorded for reproducibility")
    r.add_argument("--out", default=None, help="results JSON output path")
    r.add_argument("--leaderboard", default=None, help="leaderboard.md output path")
    r.set_defaults(func=cmd_run)

    lb = sub.add_parser("leaderboard", help="regenerate leaderboard.md from a results JSON")
    lb.add_argument("--from", dest="from_", required=True, help="results JSON path")
    lb.add_argument("--leaderboard", default=None, help="leaderboard.md output path")
    lb.set_defaults(func=cmd_leaderboard)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    ns = build_parser().parse_args(argv)
    return ns.func(ns)


if __name__ == "__main__":
    sys.exit(main())
