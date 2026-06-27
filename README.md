# substrate-bench

*v0.1 — built to the [measurement contract](measurement-contract-v0.1.md), which governs.*

A measurement instrument — with a CLI — for a single, narrow question:

> When an agent gets a task, does it recognise **what kind of thinking the task
> requires**, and route to the right cognitive strategy?

Most benchmarks score *did the agent get the right answer*. `substrate-bench`
scores the prior thing: **substrate-selection accuracy** — was the chosen
*strategy* right for the task — measured *independently* of whether the final
answer was correct. That number is the contribution here; almost nobody reports it.

## The thesis (and what this is *not*)

The claim is deliberately small and falsifiable:

> **Agents that select the right strategy beat agents that don't — and we can
> measure the difference.**

That's it. **No AGI claims.** This is not a general agent framework, it does not
train models, and it does not solve ARC-AGI (`rule-001` is an ARC-*flavoured*
toy). See [Limitations](#limitations).

The sharpest evidence is an **asymmetry**: an agent that *indiscriminately*
reaches for code (condition C) is choosing the wrong **strategy** on genuinely
linguistic and social tasks (sentiment, theory-of-mind) — and loses points there
even though it "used a tool." Selective routing (D, E) wins there *and* on the
computational tasks. If that asymmetry doesn't show up, the thesis is wrong.

## The two-axis ontology (v0.1)

v0 conflated *what kind of thinking* with *how it's executed*. v0.1 splits them:

- **Strategy axis** — the only axis scored by substrate-selection accuracy:
  `language` · `exact_computation` · `simulation` · `search` · `memory` ·
  `verify` · `social`.
- **Execution medium** — the orthogonal `executes_code: true|false` flag.

`code` is **not** a strategy — it was the medium that `exact_computation`,
`simulation`, and `search` are realised through. "Writes Python that time-steps a
trajectory" is strategy `simulation`, `executes_code: true`; "writes Python that
multiplies two integers" is strategy `exact_computation`, `executes_code: true`.
This is *why* condition C is still meaningfully wrong on `language`/`social`:
running code is the wrong strategy there, regardless of medium.

## The route-declaration contract

A solver must **emit a structured declaration before its answer** — we never
infer the strategy from tool calls (that would measure our heuristic, not the
agent's cognition):

```json
{ "strategy": "search", "executes_code": true,
  "rationale": "discrete state-space; needs expansion, not a formula",
  "answer": "<final answer in the checker's expected form>" }
```

Conditions A/B/C carry a fixed implicit declaration; D/E **emit** one. The
`CallableModel` path parses a real model's declaration and **fails loudly** if it
is missing or malformed.

## Install

```bash
pip install -e .          # zero runtime deps (pure stdlib); runs offline
pip install -e ".[test]"  # for pytest
```

## Run

One command runs the whole task set under all 5 conditions, prints the metrics
(including substrate-selection accuracy and the composite), writes a
machine-readable results file, and regenerates [`leaderboard.md`](leaderboard.md):

```bash
substrate-bench run --condition all --tasks v0
python -m substrate_bench run --condition all --tasks v0   # equivalent, no PATH needed
```

By default this uses the offline **`stub`** solver, whose numbers are
illustrative *of the instrument*, not measured model performance.

## The leaderboard (offline `stub` solver, 46 tasks)

| Condition | Substrate-sel. acc | Task acc | Composite | Switch (meta) | Audit |
|---|---|---|---|---|---|
| A · Direct | 15% | 11% | 0.126 | 0% | 100% |
| B · CoT | 15% | 33% | 0.257 | 0% | 100% |
| C · Code-always | 26% | 26% | 0.261 | n/a | 100% |
| D · Router | 98% | 98% | 0.978 | 0% | 100% |
| E · Router+Verify | 100% | 100% | **1.000** | 100% | 100% |

Read it for the *decoupling*, which is the whole v0.1 point: **B answers 33%**
(every linguistic task, via CoT) but is **substrate-correct only 15%** — it
labels `social` tasks as `language`. **A** has the right strategy on hard
language tasks but the wrong answer (`right_substrate_bad_execution`). **C**'s
indiscriminate `exact_computation` is the wrong strategy on ~74% of tasks. Only
**E** solves the `meta-001` trap, by *switching* strategy after its first attempt
is verified wrong. Per-strategy and per-difficulty breakdowns are in
[`leaderboard.md`](leaderboard.md).

## The five conditions (controls)

| ID | Condition | Declaration | What it isolates |
|---|---|---|---|
| A | Direct | fixed: `language`, no code | Floor: pure next-token. |
| B | CoT | fixed: `language`, no code | The value of a reasoning trace alone. |
| C | Code-always | fixed: `exact_computation`, code on | Whether *indiscriminate* code beats routing. |
| D | Router | **emitted** | The thesis: select-then-execute. |
| E | Router+Verify | **emitted** | A `verify` pass (and re-route) before committing. |

## Two-level scoring + consistency audit

Per task, per condition: `answer_correct` (via the declared checker) and
`substrate_correct` (declared strategy ∈ gold) are scored **independently**, then
a **consistency audit** checks behaviour against the declaration — v0.1 scope: if
`executes_code: true`, did code actually run? (The deeper *structural* audit —
"did a `search` declaration actually expand states" — is a recorded hook,
deferred to v0.2.)

Failure taxonomy: `wrong_substrate`, `right_substrate_bad_execution`,
`no_verification`, `gave_up`, `none`. **Composite = 0.6 × task accuracy + 0.4 ×
substrate-selection accuracy.**

## The gate + baseline registry (this repo is also the safety stop-condition)

A change to a downstream solver is **accepted** iff it (1) improves the composite
vs **that solver's own recorded baseline** on the same task set, (2) is
reproducible, and (3) causes no cost regression beyond +15%. Cross-condition
comparisons (E vs C) are **leaderboard findings, never merge gates.**

Baselines live in [`baselines/`](baselines/), keyed by `(task_set, solver_id)`:

```bash
substrate-bench baseline show    --solver stub --task-set v0      # read-only (the gate's access)
substrate-bench baseline promote results/v0-stub.json --solver stub --task-set v0   # HUMAN-ONLY
substrate-bench gate     results/candidate.json --solver stub --task-set v0 --condition E
```

**Promotion is human-only.** The autonomous loop may read a baseline but the
`promote` command refuses to run without a TTY — otherwise an agent could quietly
lower its own bar and "pass" the gate by regressing the baseline. Commit
promotions so they are visible (tamper-evident) in git history.

## Trusted references

Gold answers are computed by deterministic Python references (`references/`):
projectile-with-drag (RK4), Newton cooling, exponential decay, RC charging, a
Hanoi solver/validator, gridworld BFS, a water-jug BFS, a constraint enumerator,
an ARC-flavoured rule inducer, and validators for the `verify` tasks (primality,
balanced brackets, n-queens, Latin squares). **No model is ever consulted during
scoring.** `tests/test_references.py` re-derives every `reference`-provenance gold
value to prove it. The `language`/`social` tasks have no algorithmic reference, so
their gold is human-authored and tagged `provenance: "human_review"` — never from
a solver.

## Bring your own model

Conditions call a model only through `Model.solve(task, *, force_strategy,
force_executes_code, cot)`, so the suite is provider-agnostic; no provider SDK is
imported. The quickest path is `model.CallableModel`:

```python
from substrate_bench import CallableModel

def complete(prompt, cot):
    r = client.messages.create(model="claude-opus-4-8",
                               messages=[{"role": "user", "content": prompt}])
    # optional 4th element: whether a code tool actually ran (feeds the audit)
    return r.content[0].text, r.usage.input_tokens, r.usage.output_tokens

model = CallableModel(complete, name="claude-opus-4-8")
```

For D/E the model is asked to emit the JSON declaration (parsed, loud failure on
malformed). Register a zero-arg factory in `cli.SOLVERS` to expose it as
`--solver`. See `tests/test_model.py` for an offline end-to-end example.

## Repo layout

```
src/substrate_bench/
  schema.py        Task / RouteDeclaration / SolverOutput / Result + validation
  substrates.py    two-axis ontology + router category map
  model.py         Model.solve interface, StubModel, CallableModel, declaration parsing
  audit.py         declaration↔behaviour consistency audit (+ v0.2 hook)
  checkers/        the 5 checker types + dispatch
  references/      trusted deterministic gold computers (incl. verify_ref); never an LLM
  conditions/      A-E policy wrappers + cost model
  runner.py        run conditions -> scored Results
  scoring.py       metrics, composite, failure taxonomy, the gate
  registry.py      baseline registry with the human-only promotion guardrail
  leaderboard.py   Results -> leaderboard.md
  cli.py           run | leaderboard | baseline show/promote | gate
tasks/v0/*.json    the task set (~46: ~5 per strategy × difficulty)
tools/author_tasks.py   committed deterministic task generator (gold from references)
baselines/         the baseline registry (promotions visible in git history)
experiments/       dated run logs
tests/             checkers, references, scoring/gate, conditions, audit, registry, model, e2e
```

## Tests

```bash
pytest -q
```

Covers every checker type, every failure-mode branch, the scoring split and
composite math, the consistency audit (pass + fail), the gate, the baseline
registry **including the read-only guardrail**, route-declaration parsing
(emit + loud failure on malformed), the reference-derived gold, and the
end-to-end run → leaderboard path. All offline.

## Limitations

- **~46 tasks is a probe, not a population.** Results are illustrative of the
  *measurement*, not a ranking of real systems.
- **The `stub` solver is a deterministic mock.** Its correctness is strategy-gated
  by construction (the offline fixture per contract §8). Real models will show the
  full answer/substrate decoupling matrix — that *is* the research signal.
- **Strategy boundaries are modelling choices.** Treating `exact_computation` vs
  `simulation` vs `search` as distinct strategies (all realisable in code) is a
  v0.1 stance; the route declaration is what makes it the *agent's* call to defend.
- **The condition-E verifier and the audit are idealised.** E refutes wrong
  computational answers by independent recomputation; the audit only checks the
  execution medium (`executes_code`), with the structural audit deferred to v0.2.
- **Cost and latency are deterministic synthetic estimates** (for reproducible
  gating), not wall-clock measurements.
- **`memory` is untested** and `rule-001` is an ARC-*flavoured* toy, not ARC-AGI.

## License

MIT.
