# Experiment 001 — v0 baseline (offline `stub` solver)

- **Date:** 2026-06-27
- **Author:** Cognitive Systems Lab
- **Task set:** `v0` (10 seed tasks)  ·  **Conditions:** A, B, C, D, E
- **Solver:** `stub` (deterministic, offline)  ·  **Seed:** 0
- **Command:** `substrate-bench run --condition all --tasks v0`
- **Artifacts:** [`results/v0-stub.json`](../results/v0-stub.json), [`leaderboard.md`](../leaderboard.md)

## Hypothesis

The instrument should expose the **substrate-selection asymmetry** the Lab is
built around:

1. Selective routing (D, E) beats indiscriminate code use (C) on the composite.
2. The win is *visible on the language tasks*: condition C, which always reaches
   for code, should **lose** points on `lang-001` and `social-001`, where code
   is the wrong substrate.
3. A verify-then-reroute condition (E) should be the only one to solve the
   meta-cognition trap `meta-001` by **switching** substrate after a failed first
   attempt.

This run also serves as the **recorded baseline** that the acceptance gate
(spec §6) will compare future experiments against.

## Setup / reproducibility

- Deterministic everywhere: the `stub` model and the synthetic cost/latency
  model use no randomness and no wall-clock time, so re-running is byte-identical.
- Gold answers come exclusively from the trusted references in
  `src/substrate_bench/references/`; `tests/test_references.py` re-derives every
  stored value to prove no model touched the gold.
- Config (task set, conditions, solver, seed, pricing, composite weights) is
  logged into the results JSON.
- Suite: **54 tests, all green** (`pytest -q`).

## Results

| Condition | Substrate-sel. acc | Task acc | Composite | Mean cost ($) | Cost-adj acc | Switch rate | Verified |
|---|---|---|---|---|---|---|---|
| A · Direct | 20% | 10% | 0.140 | 0.000788 | 126.9 | 0% | 0% |
| B · CoT | 20% | 20% | 0.200 | 0.003188 | 62.7 | 0% | 0% |
| C · Code-always | 50% | 50% | 0.500 | 0.001138 | 439.4 | n/a | 0% |
| D · Router | 90% | 90% | 0.900 | 0.001753 | 513.5 | 0% | 0% |
| E · Router+Verify | **100%** | **100%** | **1.000** | 0.002655 | 376.6 | **100%** | 100% |

Failure modes (genuine failures only; `none` = solved):

| Condition | wrong_substrate | right_substrate_bad_execution | solved |
|---|---|---|---|
| A | 8 | 1 | 1 |
| B | 8 | 0 | 2 |
| C | 5 | 0 | 5 |
| D | 1 | 0 | 9 |
| E | 0 | 0 | 10 |

Key per-task observations (full grids in `leaderboard.md`):

- **The asymmetry holds (H1, H2).** C scores 50% substrate accuracy: it nails
  the computational tasks but takes `wrong_substrate` on `lang-001`,
  `social-001`, `search-001`, `search-002`, and `sim-001`. The two language
  traps are exactly where "always use code" is a category error.
- **Drag needs simulation, not code.** On `sim-001` the closed-form reflex
  returns the vacuum range (~250.97 m vs the true ~99.32 m), badly outside
  tolerance; only D/E route to `simulation` and pass.
- **CoT rescues theory-of-mind without changing substrate.** On `social-001`,
  A has the right substrate (`language`) but `right_substrate_bad_execution`;
  B's reasoning trace fixes it. This is the one place the two metrics come apart
  for A — substrate-correct yet answer-wrong.
- **The switch is unique to E (H3).** On `meta-001`, the router is fooled by the
  prose and picks `language`; D commits the wrong answer (anchored on the host's
  "14"), while E's verifier refutes it, re-routes to `code`, and returns 15.
  `self_corrected = True` only for E → switch rate 100% vs 0% for D.

## Gate analysis

Treating this run's per-condition metrics as candidate-vs-baseline pairs through
`evaluate_gate` (spec §6):

| Candidate | Baseline | Accepted | ΔComposite | Cost ratio | Binding clause |
|---|---|---|---|---|---|
| E | C | ❌ | +0.500 | 2.33× | cost regression (+133%) |
| D | C | ❌ | +0.400 | 1.54× | cost regression (+54%) |
| C | D | ❌ | −0.400 | 0.65× | no composite improvement |
| E | C (budget ×10) | ✅ | +0.500 | 2.33× | — |

The instructive result: a **large composite win does not auto-merge**. E and D
improve the composite over C massively, but in this mock routing+CoT+verify costs
far more than a single code call, so the +15% cost clause blocks them. That is
the gate behaving correctly — it is designed to compare a modified system against
*its own* recorded baseline (where cost is comparable), not to wave through any
expensive accuracy gain. When the cost clause is satisfied, the composite +
reproducibility clauses pass and E clears.

## Interpretation — what this shows

The harness measures the thing the Lab claims matters: **substrate-selection
accuracy moves independently of the question "did tooling help at all,"** and the
language traps make indiscriminate tooling visibly worse than routing. The gate
converts "let it run overnight" into something falsifiable: composite-up,
reproducible, within budget — or it doesn't merge.

## Threats to validity — what this does *not* show

- The `stub` solver's correctness is **substrate-gated by construction**, so its
  task and substrate accuracies are near-identical. Real models will decouple
  them; the only decoupling visible here is A on `social-001`. This run validates
  the *instrument*, not any model.
- 10 tasks is a probe, not a population. No ranking claim about real systems.
- Substrate boundaries (`code` vs `simulation` vs `search`) are v0 modelling
  choices; a real agent might express all three as code.
- The E verifier is idealised (independent recomputation for computational
  tasks; pass-through for linguistic ones).

## Next steps

1. Plug in a real provider behind `Model.answer` and re-run; expect task and
   substrate accuracy to **decouple**, and expect C's language-trap penalty to
   persist (the falsifiable prediction).
2. Grow `tasks/v0` toward a size where difficulty-regime collapse (the Apple-
   paper effect) is visible per substrate.
3. Exercise the `memory` substrate once a skill library exists, then add
   memory-reuse tasks and a reuse-rate metric.
