"""`substrate-bench` command line.

    substrate-bench run --condition all --tasks v0
    substrate-bench leaderboard --from results/smoke-stub.json
    substrate-bench baseline show --solver stub --task-set smoke
    substrate-bench baseline promote results/smoke-stub.json --solver stub --task-set smoke   # human-only
    substrate-bench gate results/candidate.json --solver stub --task-set smoke --condition E
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
from .registry import PromotionDenied, promote_baseline, show_baseline
from .runner import run_all
from .schema import Result, load_tasks
from .scoring import evaluate_gate, summarize

# Registry of available (offline) solvers. Real providers register a factory here.
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
    task_set: str = "smoke",
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
    print(f"\n{'Cond':<16}{'Sub-acc':>9}{'Task-acc':>9}{'Composite':>11}{'MeanCost':>11}{'Audit':>8}")
    print("-" * 64)
    for c in CONDITION_ORDER:
        if c not in metrics:
            continue
        m = metrics[c]
        name = CONDITION_INFO[c][0]
        print(
            f"{c + ' ' + name:<16}"
            f"{m['substrate_selection_accuracy'] * 100:>8.0f}%"
            f"{m['task_accuracy'] * 100:>8.0f}%"
            f"{m['composite']:>11.3f}"
            f"{m['mean_cost']:>11.6f}"
            f"{m['audit_pass_rate'] * 100:>7.0f}%"
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
    print(f"results     -> {out_path}")
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


def cmd_baseline_show(ns: argparse.Namespace) -> int:
    data = show_baseline(_repo_root(), ns.task_set, ns.solver)
    if data is None:
        print(f"no baseline recorded for (task_set={ns.task_set}, solver={ns.solver})")
        return 1
    print(json.dumps(data, indent=2))
    return 0


def cmd_baseline_promote(ns: argparse.Namespace) -> int:
    payload = json.loads(Path(ns.run).read_text(encoding="utf-8"))
    interactive = sys.stdin.isatty()

    def _confirm() -> bool:
        ans = input(
            f"Promote {ns.run} as baseline for (task_set={ns.task_set}, solver={ns.solver})? [y/N] "
        )
        return ans.strip().lower() in ("y", "yes")

    try:
        path = promote_baseline(
            _repo_root(), ns.task_set, ns.solver, payload,
            interactive=interactive, confirm=_confirm,
        )
    except PromotionDenied as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(f"baseline promoted -> {path}")
    print("remember to `git add baselines/ && git commit` so the promotion is auditable.")
    return 0


def cmd_gate(ns: argparse.Namespace) -> int:
    baseline = show_baseline(_repo_root(), ns.task_set, ns.solver)  # read-only
    if baseline is None:
        print(f"no baseline for (task_set={ns.task_set}, solver={ns.solver}); cannot gate", file=sys.stderr)
        return 2
    _, _, cand_metrics = _load_payload(ns.run)
    cond = ns.condition.upper()
    base_m = baseline["metrics"].get(cond)
    cand_m = cand_metrics.get(cond)
    if base_m is None or cand_m is None:
        print(f"condition {cond} missing in baseline or candidate", file=sys.stderr)
        return 2
    g = evaluate_gate(base_m, cand_m, reproducible=True)
    verdict = "ACCEPTED" if g.accepted else "REJECTED"
    print(f"gate [{cond}] {verdict}  Δcomposite={g.composite_delta:+.3f}  cost_ratio={g.cost_ratio:.2f}")
    for r in g.reasons:
        print(f"  - {r}")
    return 0 if g.accepted else 1


def cmd_frontier(ns: argparse.Namespace) -> int:
    from . import frontier
    from .adapters import available

    if ns.frontier_cmd == "list":
        for bid in available():
            s = frontier.label_summary(bid)
            print(f"{bid}: labelled={s['labelled']} needs_review={s['needs_human_review']} total={s['total']}")
        return 0
    if ns.frontier_cmd == "fetch":
        benchmarks = available() if ns.benchmark in (None, "all") else [ns.benchmark]
        for bid in benchmarks:
            try:
                n = frontier.fetch(bid, limit=ns.limit)
                print(f"{bid}: cached {n} items")
            except Exception as exc:  # licence/token/network issues are expected
                print(f"{bid}: fetch failed: {exc}", file=sys.stderr)
        return 0
    if ns.frontier_cmd == "build":
        benchmarks = None if ns.benchmark in (None, "all") else [ns.benchmark]
        tasks = frontier.build(benchmarks=benchmarks, include_needs_review=ns.include_needs_review)
        print(f"built {len(tasks)} frontier tasks -> {frontier.frontier_dir()}")
        return 0
    return 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="substrate-bench", description="Substrate-selection benchmark.")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run conditions over a task set and regenerate the leaderboard")
    r.add_argument("--condition", default="all", help="'all' or a subset like 'D,E' (default: all)")
    r.add_argument("--tasks", default="smoke", help="task set name under tasks/ (default: smoke)")
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

    bl = sub.add_parser("baseline", help="baseline registry (show is read-only; promote is human-only)")
    blsub = bl.add_subparsers(dest="baseline_cmd", required=True)
    bls = blsub.add_parser("show", help="print the recorded baseline (read-only)")
    bls.add_argument("--solver", required=True)
    bls.add_argument("--task-set", dest="task_set", required=True)
    bls.set_defaults(func=cmd_baseline_show)
    blp = blsub.add_parser("promote", help="record a run as the baseline (HUMAN-ONLY, needs a TTY)")
    blp.add_argument("run", help="results JSON to promote")
    blp.add_argument("--solver", required=True)
    blp.add_argument("--task-set", dest="task_set", required=True)
    blp.set_defaults(func=cmd_baseline_promote)

    gt = sub.add_parser("gate", help="compare a candidate run to the recorded baseline (read-only)")
    gt.add_argument("run", help="candidate results JSON")
    gt.add_argument("--solver", required=True)
    gt.add_argument("--task-set", dest="task_set", required=True)
    gt.add_argument("--condition", default="E", help="condition to gate on (default: E)")
    gt.set_defaults(func=cmd_gate)

    fr = sub.add_parser("frontier", help="tier-1 frontier tasks: fetch benchmark data, build tasks, list labels")
    frsub = fr.add_subparsers(dest="frontier_cmd", required=True)
    frl = frsub.add_parser("list", help="show labelled / needs-review counts per benchmark")
    frl.set_defaults(func=cmd_frontier)
    frf = frsub.add_parser("fetch", help="fetch+cache raw benchmark data (respects licences/tokens)")
    frf.add_argument("--benchmark", default="all", help="benchmark id or 'all'")
    frf.add_argument("--limit", type=int, default=None, help="cap items fetched (where supported)")
    frf.set_defaults(func=cmd_frontier)
    frb = frsub.add_parser("build", help="materialise tasks/frontier/ from adapters + labels + cache")
    frb.add_argument("--benchmark", default="all", help="benchmark id or 'all'")
    frb.add_argument("--include-needs-review", action="store_true", help="also build needs_human_review items")
    frb.set_defaults(func=cmd_frontier)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    ns = build_parser().parse_args(argv)
    return ns.func(ns)


if __name__ == "__main__":
    sys.exit(main())
