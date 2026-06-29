# substrate-bench

*v0.1 — built to the [measurement contract](measurement-contract-v0.1.md), which governs.*

A measurement instrument — with a CLI — for a single, narrow question:

> When an agent gets a task, does it recognise **what kind of thinking the task
> requires**, and route to the right cognitive strategy?

## The reframe: a lens on top of established benchmarks

Public benchmarks measure **whether** a task was solved. substrate-bench's
contribution is the **substrate-selection lens** — *did the solver recognise what
kind of problem it faced and route correctly* — applied **on top of** established
frontier benchmarks. Measuring **how**, not just **if**, is also partly robust to
the **contamination and saturation** that degrade pass/fail benchmarks: a
memorised answer key doesn't tell you the model *routed* correctly. The lens is
the lab's contribution; frontier benchmarks (ARC-AGI-2, GPQA Diamond, …) are the
substrate it is measured on.

So `substrate-bench` scores the prior thing: **substrate-selection accuracy** —
was the chosen *strategy* right for the task — measured *independently* of whether
the final answer was correct. That number is the contribution; almost nobody
reports it.

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

## Tiers

| Tier | Set | Role |
|---|---|---|
| tier-0 | `smoke` | the toy tasks — a fast, deterministic, **offline CI smoke-test**. No longer the primary evaluation. |
| tier-1 | `frontier` | tasks adapted from established benchmarks (ARC-AGI-2, GPQA Diamond). The primary evaluation. |

## Run

One command runs a task set under all 5 conditions, prints the metrics
(substrate-selection accuracy, the composite, the discrimination spread), writes a
results file, and regenerates the leaderboard:

```bash
# tier-0 smoke (offline, no credentials)
substrate-bench run --condition all --tasks smoke

# tier-1 frontier: fetch benchmark data, materialise tasks, run
substrate-bench frontier fetch --benchmark arc-agi-2 --limit 30   # public
substrate-bench frontier fetch --benchmark gpqa-diamond           # needs HUGGING_FACE_TOKEN
substrate-bench frontier build
substrate-bench run --condition all --tasks frontier --leaderboard leaderboard-frontier.md
```

By default this uses the offline **`stub`** solver, whose numbers are illustrative
*of the instrument*, not measured model performance.

## The leaderboard

### tier-1 `frontier` — stub, 59 items (30 ARC-AGI-2 + 29 GPQA Diamond)

| Condition | Substrate-sel. acc | Task acc | Composite |
|---|---|---|---|
| A · Direct | 29% | 0% | 0.115 |
| B · CoT | 29% | 29% | 0.288 |
| C · Code-always | **19%** | 19% | 0.186 |
| D · Router | 100% | 100% | 1.000 |
| E · Router+Verify | 100% | 100% | 1.000 |

The lens **holds its shape** on real frontier tasks. Condition C declares
`exact_computation` everywhere; by gold strategy it is substrate-correct **11/11**
on the GPQA computational items, **0/17** on GPQA `language`, **0/31** on `search`
(ARC + 1 GPQA). "Always reach for code" is right only for the computational
minority — on the strategy-mix of real benchmarks C falls *below* the no-tool
baselines. Discrimination spread **0.81**. (Full breakdowns:
[`leaderboard-frontier.md`](leaderboard-frontier.md).)

> The `stub`'s 100% task-accuracy for D/E is an **oracle-fixture artefact**, not
> model performance — ARC-AGI-2 and GPQA Diamond are largely unsolved by frontier
> models. The meaningful outputs are **substrate-selection accuracy** and the
> **discrimination spread**; real answer-accuracy awaits a model-backed router.

### tier-0 `smoke` — stub, 46 toy tasks

A=0.126 · B=0.257 · C=0.261 · D=0.978 · E=**1.000** composite. Read for the
*decoupling*: B answers 33% (every linguistic task, via CoT) but is
substrate-correct only 15% (it labels `social` as `language`); only E solves the
`meta-001` switch. Details in [`leaderboard.md`](leaderboard.md).

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
substrate-bench baseline show    --solver stub --task-set smoke      # read-only (the gate's access)
substrate-bench baseline promote results/smoke-stub.json --solver stub --task-set smoke   # HUMAN-ONLY
substrate-bench gate     results/candidate.json --solver stub --task-set smoke --condition E
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

## Benchmark adapters (the frontier pivot)

A `BenchmarkAdapter` ingests an external benchmark's items into the task schema,
**carrying the benchmark's own gold answer**, and the lab adds the
substrate-selection layer (the `gold_substrate` label) on top via the documented
rubric in [`adapters/SUBSTRATE_RUBRIC.md`](src/substrate_bench/adapters/SUBSTRATE_RUBRIC.md).
Two adapters ship:

| Benchmark | Licence | Redistributable? | Handling |
|---|---|---|---|
| **ARC-AGI-2** (Chollet et al., arXiv:2505.11831) | Apache-2.0 | yes | fetched + cached at runtime (cache gitignored), `grid_match` checker |
| **GPQA Diamond** (Rein et al., arXiv:2311.12022) | CC BY 4.0, **gated + canary** | **no** | needs `HUGGING_FACE_TOKEN`; content cached locally, **never committed**; `exact_label` MCQ |

**Provenance & licences:** gold *answers* come from the benchmark; gold
*substrate labels* come from the rubric + review — **never a solver**. Raw data is
fetched/cached at runtime and **not vendored where the licence forbids** (GPQA is
gated and contamination-sensitive — only abstract substrate labels with hashed
item ids are committed; questions/answers are not). Per-benchmark provenance lives
in each adapter's `manifest.json`. Materialised frontier tasks embed benchmark
content, so `tasks/frontier/` is gitignored and rebuilt at runtime.

**Integrity (matters more here — frontier benchmarks have known contamination):**
- The solver only ever sees the **prompt-only `PromptView`** — no gold, no
  category, no `gold_substrate`.
- The **planted-wrong-gold test** plants a deliberately wrong gold and confirms a
  gold-blind solver is scored incorrect — proving no leak.
- A **substrate-labelling rubric**, not vibes; ambiguous items are flagged
  `needs_human_review` and excluded from the scored slice.
- The **discrimination signal** (substrate-selection spread across A–E) is partly
  robust to the contamination/saturation that degrade pass/fail benchmarks.

Add an adapter: see [CONTRIBUTING.md](CONTRIBUTING.md).

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
  frontier.py      materialise tier-1 frontier tasks from adapters + labels + cache
  cli.py           run | leaderboard | baseline | gate | frontier fetch/build/list
  adapters/        BenchmarkAdapter + SUBSTRATE_RUBRIC.md + arc_agi_2/ + gpqa_diamond/
                   (each: manifest.json, adapter.py, labels.json, cache/ [gitignored])
tasks/smoke/*.json      tier-0 toy tasks (CI smoke-test)
tasks/frontier/         tier-1 tasks, rebuilt at runtime (gitignored — embeds benchmark content)
tools/author_tasks.py   committed deterministic smoke-task generator (gold from references)
baselines/         the baseline registry (promotions visible in git history)
experiments/       dated run logs
tests/             checkers, references, scoring, conditions, audit, registry, model, adapters, integrity, e2e
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

- **The labelled frontier slice (~59) is a probe, not a population.** Results are
  illustrative of the *measurement*, not a ranking of real systems.
- **The `stub` solver is a deterministic oracle fixture.** Its task-accuracy
  (incl. 100% for D/E on frontier) is an artefact, **not** model performance —
  ARC-AGI-2 / GPQA Diamond are largely unsolved by frontier models. The meaningful
  outputs are substrate-selection accuracy + the discrimination spread; the full
  answer/substrate decoupling matrix awaits a real model-backed router.
- **Substrate labels are a first-pass rubric application.** ARC labels are
  mechanical (induction = `search`); GPQA labels are a human(agent) rubric pass
  with ambiguous items flagged `needs_human_review`, not yet independently
  adjudicated.
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
