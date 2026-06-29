"""End-to-end: run -> metrics -> leaderboard offline, the gate, and the CLI
(including the baseline registry's read-only guardrail)."""

import json

from substrate_bench.cli import main, run_benchmark
from substrate_bench.leaderboard import render_leaderboard
from substrate_bench.scoring import evaluate_gate


def test_run_benchmark_all_conditions_offline():
    tasks, results, metrics = run_benchmark(task_set="smoke")
    assert len(tasks) >= 46
    assert set(results) == set("ABCDE")
    for c in "ABCDE":
        assert len(results[c]) == len(tasks)


def test_leaderboard_renders_rescaled_markdown():
    _, results, metrics = run_benchmark(task_set="smoke")
    md = render_leaderboard(results, metrics, solver_name="stub", task_set="smoke")
    assert "substrate-bench leaderboard" in md
    assert "Substrate-sel. acc" in md
    assert "Substrate-selection accuracy by gold strategy" in md
    assert "Task accuracy by difficulty" in md
    for strat in ("simulation", "search", "social", "verify"):
        assert strat in md
    assert "Audit pass" in md


def test_gate_enforces_cost_budget_even_on_a_big_composite_win():
    _, _, metrics = run_benchmark(task_set="smoke")
    g = evaluate_gate(metrics["C"], metrics["E"], reproducible=True)
    assert not g.accepted
    assert g.composite_delta > 0
    assert any("cost regression" in r for r in g.reasons)


def test_gate_accepts_composite_win_when_cost_budget_permits():
    _, _, metrics = run_benchmark(task_set="smoke")
    g = evaluate_gate(metrics["C"], metrics["E"], reproducible=True, max_cost_regression=10.0)
    assert g.accepted, g.reasons


def test_gate_rejects_C_over_D_baseline():
    _, _, metrics = run_benchmark(task_set="smoke")
    g = evaluate_gate(metrics["D"], metrics["C"], reproducible=True)
    assert not g.accepted
    assert any("composite" in r for r in g.reasons)


def test_cli_run_writes_results_and_leaderboard(tmp_path):
    out = tmp_path / "res.json"
    board = tmp_path / "board.md"
    rc = main(["run", "--condition", "all", "--tasks", "smoke",
               "--out", str(out), "--leaderboard", str(board)])
    assert rc == 0
    assert out.exists() and board.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["config"]["n_tasks"] >= 46
    assert payload["metrics"]["E"]["composite"] == 1.0


def test_cli_leaderboard_regenerates_from_results(tmp_path):
    out = tmp_path / "res.json"
    board1 = tmp_path / "b1.md"
    board2 = tmp_path / "b2.md"
    main(["run", "--tasks", "smoke", "--out", str(out), "--leaderboard", str(board1)])
    rc = main(["leaderboard", "--from", str(out), "--leaderboard", str(board2)])
    assert rc == 0
    assert board2.read_text(encoding="utf-8") == board1.read_text(encoding="utf-8")


def test_cli_baseline_promote_is_refused_non_interactively(tmp_path, capsys):
    """Under pytest there is no TTY, so an agent-style promote must be refused."""
    run = tmp_path / "run.json"
    run.write_text(json.dumps({"config": {}, "metrics": {}, "results": {}}), encoding="utf-8")
    rc = main(["baseline", "promote", str(run), "--solver", "stub", "--task-set", "smoke"])
    assert rc == 2
    assert "REFUSED" in capsys.readouterr().err


def test_cli_baseline_show_missing_returns_nonzero():
    rc = main(["baseline", "show", "--solver", "does-not-exist", "--task-set", "zzz"])
    assert rc == 1


def test_cli_gate_without_baseline_returns_error(tmp_path):
    run = tmp_path / "run.json"
    run.write_text(json.dumps({"config": {}, "metrics": {}, "results": {}}), encoding="utf-8")
    rc = main(["gate", str(run), "--solver", "does-not-exist", "--task-set", "zzz"])
    assert rc == 2
