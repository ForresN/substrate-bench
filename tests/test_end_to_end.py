"""End-to-end: the single command path (run -> metrics -> leaderboard) works
offline, and the gate consumes the produced metrics."""

import json

from substrate_bench.cli import main, run_benchmark
from substrate_bench.leaderboard import render_leaderboard
from substrate_bench.scoring import evaluate_gate


def test_run_benchmark_all_conditions_offline():
    tasks, results, metrics = run_benchmark(task_set="v0")
    assert len(tasks) == 10
    assert set(results) == set("ABCDE")
    for c in "ABCDE":
        assert len(results[c]) == 10


def test_leaderboard_renders_markdown():
    _, results, metrics = run_benchmark(task_set="v0")
    md = render_leaderboard(results, metrics, solver_name="stub", task_set="v0")
    assert "substrate-bench leaderboard" in md
    assert "Substrate-sel. acc" in md
    for tid in ("lang-001", "meta-001", "sim-001"):
        assert tid in md


def test_gate_enforces_cost_budget_even_on_a_big_composite_win():
    """E hugely improves composite over C (1.00 vs 0.50) but costs far more than
    +15%. The gate must still reject it on cost -- that discipline is the point."""
    _, _, metrics = run_benchmark(task_set="v0")
    g = evaluate_gate(metrics["C"], metrics["E"], reproducible=True)
    assert not g.accepted
    assert g.composite_delta > 0  # composite genuinely improved...
    assert any("cost regression" in r for r in g.reasons)  # ...but cost blew the budget


def test_gate_accepts_composite_win_when_cost_budget_permits():
    """With the cost clause satisfied, E clears the gate over C on composite."""
    _, _, metrics = run_benchmark(task_set="v0")
    g = evaluate_gate(metrics["C"], metrics["E"], reproducible=True, max_cost_regression=10.0)
    assert g.accepted, g.reasons


def test_gate_rejects_C_over_D_baseline():
    """Indiscriminate code (C) must NOT clear the gate against a router (D):
    no composite improvement."""
    _, _, metrics = run_benchmark(task_set="v0")
    g = evaluate_gate(metrics["D"], metrics["C"], reproducible=True)
    assert not g.accepted
    assert any("composite" in r for r in g.reasons)


def test_cli_run_writes_results_and_leaderboard(tmp_path):
    out = tmp_path / "res.json"
    board = tmp_path / "board.md"
    rc = main(["run", "--condition", "all", "--tasks", "v0",
               "--out", str(out), "--leaderboard", str(board)])
    assert rc == 0
    assert out.exists() and board.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["config"]["n_tasks"] == 10
    assert "E" in payload["metrics"]
    assert payload["metrics"]["E"]["composite"] == 1.0


def test_cli_leaderboard_regenerates_from_results(tmp_path):
    out = tmp_path / "res.json"
    board1 = tmp_path / "b1.md"
    board2 = tmp_path / "b2.md"
    main(["run", "--tasks", "v0", "--out", str(out), "--leaderboard", str(board1)])
    rc = main(["leaderboard", "--from", str(out), "--leaderboard", str(board2)])
    assert rc == 0
    assert board2.read_text(encoding="utf-8") == board1.read_text(encoding="utf-8")
