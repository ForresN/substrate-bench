> **Superseded (2026-06-28).** This is the historical v0 handoff. Its open
> questions were resolved by [`measurement-contract-v0.1.md`](measurement-contract-v0.1.md)
> and implemented in the v0.1 upgrade; see
> [`experiments/2026-06-28-v0.1-baseline-stub.md`](experiments/2026-06-28-v0.1-baseline-stub.md).
> The repo is now under git and pushed to GitHub. Kept for provenance.

# Handoff — substrate-bench v0 (build agent → design agent)

**Date:** 2026-06-27 · **From:** build/implementation agent · **Status:** v0 complete, all acceptance criteria met, ready for design review.

## TL;DR

The v0 spec is built end to end and green. `pip install -e .`; one command runs
all 10 tasks × 5 conditions and emits substrate-selection accuracy + the
composite; `leaderboard.md` regenerates from results; **63 tests pass**; the
acceptance gate and the trusted references exist and are exercised. The offline
`stub` solver reproduces the substrate-selection asymmetry the instrument is for:
**indiscriminate code (C) loses on the language tasks; selective routing (D/E)
wins; only E solves the meta-cognition switch.**

## What I built (against spec §8/§10)

- **Package** (`src/substrate_bench/`, src-layout, pure stdlib, zero runtime deps):
  `schema` · `substrates` · `model` · `checkers/` (all 5 types) · `references/`
  (deterministic gold) · `conditions/` (A–E + executor + cost model) · `runner` ·
  `scoring` (metrics, composite, failure taxonomy, **gate**) · `leaderboard` ·
  `cli` (`run`, `leaderboard`).
- **10 seed tasks** (`tasks/v0/*.json`) — exactly the §7 set.
- **Trusted references**: RK4 projectile-with-drag, Newton cooling, Hanoi
  solver+validator, gridworld BFS+validator, constraint-count enumerator,
  ARC-flavoured rule inducer. **No model is ever consulted in scoring**;
  `test_references.py` re-derives every stored gold value to prove it.
- **Tests** (63): every checker type (pass+fail), every failure-mode branch, the
  composite/aggregate/switch-rate math, the gate (accept + each rejection
  reason), reference-derived gold, the provider seam, and the e2e run→leaderboard.
- **Docs/artifacts**: honest `README` (narrow thesis + explicit Limitations, no
  AGI claims), `CONTRIBUTING.md` (how to add tasks/checkers/references),
  `LICENSE` (MIT), and the first experiment log
  (`experiments/2026-06-27-v0-baseline-stub.md`).

## Readiness pass (added after the core build)

- **Provider seam proven, not just asserted.** Added `model.CallableModel`
  (adapts any `complete(prompt, cot) -> (text, in, out)` callable) + a best-effort
  `parse_answer`, with `test_model.py` driving conditions A and D through a
  **non-stub** model fully offline. This de-risks "plug in a real provider."
- **Recorded baseline is now tracked.** `.gitignore` keeps ad-hoc runs out but
  retains `results/v0-stub.json` (the gate's baseline + the experiment's artifact).
- `python -m substrate_bench …` works (added `__main__.py`) as a fallback to the
  console script.
- Verified **byte-identical re-runs** (leaderboard + results) — the reproducibility
  the gate depends on.

## Results (offline `stub`)

| Cond | Substrate acc | Task acc | Composite | Switch (meta) |
|---|---|---|---|---|
| A Direct | 20% | 10% | 0.140 | 0% |
| B CoT | 20% | 20% | 0.200 | 0% |
| C Code-always | 50% | 50% | 0.500 | n/a |
| D Router | 90% | 90% | 0.900 | 0% |
| E Router+Verify | 100% | 100% | **1.000** | 100% |

## Decisions I made that you should ratify (or overturn)

1. **Substrate ontology in the mock.** I modelled condition C's "always code" as
   *closed-form / exact arithmetic*, deliberately distinct from `simulation`
   (time-stepping) and `search` (state-space). That's why C fails `sim-001`
   (drag, no closed form) and the search tasks. It makes the v0 demo crisp, but
   it bakes in a stance: **is `code` distinct from `simulation`/`search`, or is
   everything an agent writes "code"?** This directly affects how a real agent's
   substrate choice should be judged (see open question 1).
2. **Stub correctness is substrate-gated by construction** so the suite runs
   offline and the asymmetry is legible. Real models will decouple answer vs
   substrate correctness; the stub only shows one decoupling (A on `social-001`:
   right substrate, bad execution). Documented as a Limitation.
3. **E's verifier is idealised** — it refutes wrong *computational* answers by
   independent recomputation and passes through linguistic ones (you can't
   formally verify sentiment).
4. **Gate cost clause is strict and binding.** Notable finding: E improves
   composite over C by +0.50 but costs +133%, so the gate **rejects** it on the
   +15% cost budget. That's correct for "compare a change to its *own* baseline,"
   but it means cross-condition composite wins do not auto-merge. Worth a design
   decision on baseline semantics (open question 3).

## Open questions for you

1. **How does a real solver declare its chosen substrate?** D/E currently route
   by task *category* (a deterministic stub). A model-based router must *emit* its
   route. Define the contract: does the model name a substrate explicitly, or do
   we infer it from which tool it invoked? And if it writes Python that runs BFS,
   is that scored `code` or `search`? This is the central measurement-definition
   question before wiring autonomy.
2. **Baseline registry / promotion workflow.** The gate takes a baseline metrics
   dict; promoting a run to "the recorded baseline" is currently manual (the
   tracked `results/v0-stub.json`). Want a `substrate-bench baseline` command or a
   `baselines/` registry keyed by (task set, solver)?
3. **Gate comparison policy.** Confirm the gate is only ever
   candidate-vs-same-baseline (cognitive-os change), not cross-condition. If
   cross-condition comparisons are ever intended, the cost clause needs rethinking.
4. **Composite weights (0.6/0.4) and the +15% cost budget** are spec-fixed but are
   the obvious tuning levers — flagging them as policy you own.
5. **Task-set growth.** To see the difficulty-regime collapse (Apple-paper effect)
   we need more tasks per substrate × difficulty. How big for v0.1, and who
   authors them (you, or an autonomous task-gen loop gated by review)?

## Recommended next steps (my suggestion, your call)

1. **Put it under version control.** The repo is *not* a git repo yet (I did not
   `git init`/commit — outside the build scope and not requested). Recommend
   `git init` + an initial commit as step one before any autonomy wiring.
2. **Resolve open question 1**, then implement a real model-backed router behind
   `Model`/`CallableModel` and re-run. Falsifiable prediction to check: task and
   substrate accuracy **decouple**, while C's language-trap penalty persists.
3. **Grow `tasks/v0`** toward per-substrate difficulty coverage (CONTRIBUTING.md
   has the recipe).
4. **Exercise `memory`/`verify` as primary substrates** once a skill library
   exists (add memory-reuse tasks + a reuse-rate metric).

## How to run

```bash
pip install -e ".[test]"
pytest -q
substrate-bench run --condition all --tasks v0     # regenerates leaderboard.md
substrate-bench leaderboard --from results/v0-stub.json
```
