# Baseline registry

Recorded baselines keyed by `(task_set, solver_id)`, e.g. `v0__stub.json`. The
acceptance gate (contract §5) compares a candidate run against *the same solver's*
recorded baseline on the same task set.

## Promotion is human-only (contract §4)

The autonomous loop may **read** baselines (the gate needs them) but must **never
promote** — otherwise an agent could quietly lower its own bar and "pass" the gate
by regressing the baseline. The `promote` command refuses to run without an
interactive TTY; any non-interactive caller gets a hard error.

Promote a run as the baseline (run this yourself, in a terminal):

```bash
substrate-bench run --condition all --tasks v0          # produces results/v0-stub.json
substrate-bench baseline promote results/v0-stub.json --solver stub --task-set v0
git add baselines/ && git commit -m "baseline: promote v0 stub"
```

`substrate-bench baseline show --solver stub --task-set v0` reads it back
(read-only, always allowed). Commit promotions so they are visible — and
tamper-evident — in git history.

> This directory is intentionally committed without an initial promoted baseline:
> the build agent does **not** promote (it is bound by the same guardrail). The
> first promotion is a human action.
