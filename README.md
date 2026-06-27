# substrate-bench

A measurement instrument — with a CLI — for a single, narrow question:

> When an agent gets a task, does it recognise **what kind of thinking the task
> requires**, and route to the right computational substrate?

Most benchmarks score *did the agent get the right answer*. `substrate-bench`
scores the prior thing: **substrate-selection accuracy** — was the chosen
substrate (`language`, `code`, `simulation`, `search`, `memory`, `verify`) the
right one for the task — measured *independently* of whether the final answer
was correct. That number is the contribution here; almost nobody reports it.

## The thesis (and what this is *not*)

The claim is deliberately small and falsifiable:

> **Agents that select the right substrate beat agents that don't — and we can
> measure the difference.**

That's it. **No AGI claims.** This is not a general agent framework, it does not
train models, and it does not solve ARC-AGI (`rule-001` is an ARC-*flavoured*
toy). See [Limitations](#limitations).

The sharpest evidence for the thesis is an **asymmetry**: an agent that
*indiscriminately* reaches for code (condition C below) should *lose* points on
genuinely linguistic tasks (sentiment, theory-of-mind), where routing to code is
a category error. Selective routing (D, E) should win there *and* on the
computational tasks. If that asymmetry doesn't show up, the thesis is wrong.

## Install

```bash
pip install -e .
```

Zero runtime dependencies (pure standard library), so it runs offline and the
scorer stays deterministic. Tests need `pytest`:

```bash
pip install -e ".[test]"
```

## Run

One command runs all 10 seed tasks under all 5 conditions, prints the metrics
(including substrate-selection accuracy and the composite), writes a
machine-readable results file, and regenerates [`leaderboard.md`](leaderboard.md):

```bash
substrate-bench run --condition all --tasks v0
# or, equivalently, without the console script on PATH:
python -m substrate_bench.cli run --condition all --tasks v0
```

Regenerate the leaderboard from a saved results file:

```bash
substrate-bench leaderboard --from results/v0-stub.json
```

By default this uses the offline **`stub`** solver. Its numbers are illustrative
*of the instrument*, not measured model performance — to get real numbers, plug
in a provider (see [Bring your own model](#bring-your-own-model)).

## The leaderboard (offline `stub` solver)

| Condition | Substrate-sel. acc | Task acc | Composite | Switch rate (meta) |
|---|---|---|---|---|
| A · Direct | 20% | 10% | 0.140 | 0% |
| B · CoT | 20% | 20% | 0.200 | 0% |
| C · Code-always | 50% | 50% | 0.500 | n/a |
| D · Router | 90% | 90% | 0.900 | 0% |
| E · Router+Verify | 100% | 100% | **1.000** | 100% |

Read it for the asymmetry, not the totals: **C fails `lang-001` and
`social-001`** (routing to code is wrong there) and **`sim-001`** (projectile
*with drag* has no closed form, so the closed-form code reflex misses), while the
routers D/E get them right. **E** is the only condition that solves `meta-001`
by *switching* substrate after its first attempt is verified wrong. Full
per-task grids are in [`leaderboard.md`](leaderboard.md).

## How it works

### Substrate taxonomy
`language` · `code` · `simulation` · `search` · `memory` · `verify`.
(`memory` exists for forward-compatibility; the v0 task set does not require it.)

### The five conditions (controls)
| ID | Condition | What it isolates |
|---|---|---|
| A | Direct LLM answer | Floor: pure next-token. |
| B | LLM + chain-of-thought | The value of a reasoning trace alone. |
| C | LLM with code tool always on | Whether *indiscriminate* tool use beats routing. |
| D | Router that chooses one substrate | The thesis: select-then-execute. |
| E | Router + verifier | A `verify` pass (and re-route) before committing. |

### Scoring (per task, per condition)
`answer_correct`, `substrate_correct`, `cost`, `latency_s`, `verified`,
`self_corrected`, and a `failure_mode` ∈ {`wrong_substrate`,
`right_substrate_bad_execution`, `no_verification`, `gave_up`, `none`}.

Headline aggregates: **task accuracy**, **substrate-selection accuracy** (the
novel number), **cost-adjusted accuracy**, and the **switch rate** on the
meta-cognition subset.

**Composite = 0.6 × task accuracy + 0.4 × substrate-selection accuracy.**

### The gate (this repo is also the safety stop-condition)
An experiment that modifies a downstream system is **accepted** iff it (1)
improves the composite vs the recorded baseline on the same task set, (2) is
reproducible (fixed tasks, fixed seeds, logged config + metrics), and (3) causes
**no cost regression beyond +15%**. No composite improvement → no merge,
regardless of how confident the prose is. See `scoring.evaluate_gate`.

### Trusted references
The gold answers are computed by deterministic Python references
(`references/`): RK4 projectile-with-drag, Newton cooling, a Hanoi
solver/validator, gridworld BFS, a constraint-count enumerator, and an
ARC-flavoured rule inducer. **No model is ever consulted during scoring.**
`tests/test_references.py` re-derives every stored gold value from its reference
to prove it.

## Bring your own model

Conditions call a model only through the thin `Model` interface
(`model.Model.answer(task, *, cot)`), so the suite is provider-agnostic. The
offline `StubModel` implements it deterministically. No provider SDK is imported
anywhere in the package.

The quickest way to wire a real provider is `model.CallableModel`, which adapts
any completion callable into a `Model` and parses the output with
`model.parse_answer`:

```python
from substrate_bench import CallableModel

def complete(prompt, cot):
    r = client.messages.create(model="claude-opus-4-8",
                               messages=[{"role": "user", "content": prompt}])
    return r.content[0].text, r.usage.input_tokens, r.usage.output_tokens

model = CallableModel(complete, name="claude-opus-4-8")
```

Register a zero-arg factory in `cli.SOLVERS` to expose it as `--solver`.
See `tests/test_model.py` for a fully offline end-to-end example.

## Repo layout

```
src/substrate_bench/
  schema.py        Task/Result/SolverOutput + JSON load & validate
  substrates.py    taxonomy + router category map
  model.py         provider-agnostic Model interface + offline StubModel
  checkers/        the 5 checker types + dispatch
  references/      trusted deterministic gold computers (never an LLM)
  conditions/      A-E harnesses + executor + cost model
  runner.py        run conditions -> scored Results
  scoring.py       metrics, composite, failure taxonomy, the gate
  leaderboard.py   Results -> leaderboard.md
  cli.py           `substrate-bench run | leaderboard`
tasks/v0/*.json    the 10 seed tasks
experiments/       dated run logs (hypothesis, config, metrics, reflection)
tests/             checkers, references, scoring/gate, conditions, e2e
```

## Tests

```bash
pytest -q
```

Covers every checker type, every failure-mode branch, the scoring/composite
math, the gate (accept + each rejection reason), the reference-derived gold
values, and the end-to-end run → leaderboard path. All offline.

## Limitations

This is a v0 instrument with a small, hand-authored task set. Be honest about
what it does and does not show:

- **10 tasks is a probe, not a population.** Results are illustrative of the
  *measurement*, not a ranking of real systems.
- **The `stub` solver is a deterministic mock.** Its correctness is substrate-
  gated *by construction* so the harness can run offline and the asymmetry is
  legible. Real models will produce a messier, less perfectly correlated picture
  — that is expected and is the point of plugging one in.
- **Substrate boundaries are modelling choices.** Treating `code` (closed-form /
  exact arithmetic) as distinct from `simulation` (time-stepping) and `search`
  (state-space exploration) is a v0 simplification; a real system could express
  any of these as "code."
- **The condition-E verifier is idealised.** It refutes a wrong computational
  answer by independent recomputation; it cannot verify purely linguistic
  answers, and a real verifier would be imperfect.
- **Cost and latency are deterministic synthetic estimates** (for reproducible
  gating), not wall-clock measurements.
- **`memory` is untested in v0** and `rule-001` is an ARC-*flavoured* toy, not an
  ARC-AGI attempt.

## License

MIT.
