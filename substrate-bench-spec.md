# `substrate-bench` — v0 Task & Scoring Specification

*The keystone of the Cognitive Systems Lab: simultaneously the scientific instrument, the safety stop-condition for autonomous runs, and the portfolio's most original contribution.*

**Status:** v0 spec — buildable. Build this **before** wiring any autonomy.

---

## 1. What it measures

Most benchmarks ask *did the agent get the right answer*. `substrate-bench` asks the prior, harder question:

> Did the agent recognise **what kind of thinking the task required**, and route to the right computational substrate?

A task can be answered correctly by luck or brute verbosity. The thesis of the Lab is that reliable generality comes from *substrate selection* — using code when exactness is needed, a simulator when dynamics matter, search when combinatorics matter, language when the problem is genuinely linguistic, and verification before committing. So the headline novelty here is a metric almost nobody reports: **substrate-selection accuracy**, scored independently of answer accuracy.

---

## 2. The substrate taxonomy

The fixed set of substrates a solver may route to in v0:

| Substrate | When it's the right call | Example |
|---|---|---|
| `language` | Genuinely linguistic / social / world-modelling tasks | sentiment, theory-of-mind |
| `code` | Exact computation, arithmetic, constraint checking | long multiplication, scheduling |
| `simulation` | Continuous dynamics over time | projectile + drag, cooling, orbits |
| `search` | Discrete state-space / combinatorial / planning | river-crossing, Hanoi, pathfinding |
| `memory` | A near-identical task was solved before | reuse a saved skill (exercised later, not v0-critical) |
| `verify` | Checking a candidate answer against constraints/tests | confirm a proposed schedule is valid |

`memory` is in the taxonomy for forward-compatibility but the v0 task set does not require it; it becomes load-bearing once the skill library is exercised.

---

## 3. Task schema

One JSON object per task. Tasks live in `tasks/v0/*.json`.

```json
{
  "id": "exact-002",
  "category": "exact_computation",
  "prompt": "What is 4729 × 8813, plus 100237?",
  "gold_substrate": ["code"],
  "checker": { "type": "numeric_exact", "answer": 41680714 },
  "difficulty": 2,
  "rationale": "Long-multiplication is the canonical case where text continuation fails and exact computation is required."
}
```

Field notes:
- **`gold_substrate`** is a list. Most tasks have one correct substrate; some accept a primary plus `verify`.
- **`checker`** is declarative so scoring stays programmatic and seed-stable. v0 checker types:
  - `exact_label` — string match against a fixed set (classification).
  - `numeric_exact` — integer/exact match.
  - `numeric_tol` — float within `tol` (carries a reference value computed by a trusted reference implementation, not by an LLM).
  - `sequence_valid` — a validator function confirms a proposed action sequence solves the stated problem (and, where relevant, is optimal).
  - `grid_match` — exact 2D array match (hidden-rule tasks).
- **`difficulty`** 1–3 to let us see the regime collapse the Apple paper describes.

---

## 4. The five baseline conditions

Every task is run under all five. These are the columns of the leaderboard and the controls that make any later improvement falsifiable.

| ID | Condition | Purpose |
|---|---|---|
| A | Direct LLM answer | Floor: pure next-token. |
| B | LLM + chain-of-thought | Isolates the value of a reasoning trace alone. |
| C | LLM with code tool always on | "Always reach for code" — tests whether indiscriminate tool use beats routing. |
| D | Router that chooses one substrate | The thesis: select-then-execute. |
| E | Router + verifier | Adds a `verify` pass before committing the answer. |

The interesting result isn't "E wins." It's *where* D and E beat C — i.e. that **indiscriminate** code use is worse than **selective** substrate use, especially on `language`/`social` tasks where routing to code is a mistake. That asymmetry is the whole argument.

---

## 5. Scoring & metrics

Per task, per condition, record:

- **`answer_correct`** (bool) — via the declared checker.
- **`substrate_correct`** (bool) — was the chosen substrate ∈ `gold_substrate`? (Conditions A/B/C have a fixed implicit substrate; D/E choose.)
- **`cost`** — tokens × price, plus tool/compute time priced flat. Real number; this is what makes "spare credits, off-peak" a measurable budget, not a vibe.
- **`latency_s`**.
- **`verified`** (bool) — did the solver run a verification step before answering?
- **`self_corrected`** (bool) — did it detect a failure and switch approach? (Critical for the meta-cognition tasks.)
- **`failure_mode`** — one of: `wrong_substrate`, `right_substrate_bad_execution`, `no_verification`, `gave_up`, `none`.

Headline aggregate per condition:
- **Task accuracy** = mean(`answer_correct`).
- **Substrate-selection accuracy** = mean(`substrate_correct`). *(the novel number)*
- **Cost-adjusted accuracy** = accuracy per unit cost.
- **Switch rate** on the meta-cognition subset = mean(`self_corrected` | first attempt wrong).

---

## 6. The gate definition (why this repo is also the safety mechanism)

This is the rule the autonomous loop enforces. An experiment that modifies `cognitive-os` is **accepted** iff:

1. It improves the **composite score** — defined for v0 as `0.6 × task_accuracy + 0.4 × substrate_selection_accuracy` — versus the recorded baseline for the same task set, **and**
2. the run is **reproducible**: fixed task set, fixed seeds, logged config and metrics, **and**
3. it causes **no cost regression** beyond +15% relative to baseline.

No composite improvement → no merge, regardless of how confident the agent's prose is. This single rule is what converts "let it run overnight" from a slop generator into a research engine.

---

## 7. The 10 seed tasks (v0)

A deliberate spread so the leaderboard immediately shows the substrate asymmetry.

| id | category | gold | what it discriminates |
|---|---|---|---|
| lang-001 | language | `language` | sentiment classification — code-routing is *wrong* here |
| exact-001 | exact_computation | `code` | multi-step arithmetic LLMs flub |
| exact-002 | exact_computation | `code`,`verify` | constraint check on a small schedule |
| sim-001 | simulation | `simulation` | projectile **with drag** — no closed form, text-answer fails |
| sim-002 | simulation | `simulation`,`code` | Newton's-law-of-cooling temperature after t |
| search-001 | search | `search` | Tower of Hanoi, 4 disks — move sequence (Apple-paper flavour) |
| search-002 | search | `search` | shortest path in a small gridworld, optimality checked |
| rule-001 | hidden_rule | `code`,`search` | ARC-like: induce rule from 3 examples, apply to a 4th |
| social-001 | social | `language` | false-belief / theory-of-mind — routing to code is *wrong* |
| meta-001 | meta_cognition | `code` (after `language` fails) | prose-stated problem that's secretly combinatorial; scored on the **switch** |

The two `gold = language` tasks (lang-001, social-001) are not filler — they're the trap that exposes condition C. An agent that "always uses code" should *lose* points there, which is exactly how we demonstrate that selection beats indiscriminate tooling.

---

## 8. Repo structure

```
substrate-bench/
  pyproject.toml
  README.md                 # thesis, how to run, leaderboard, explicit non-overclaiming
  src/substrate_bench/
    __init__.py
    schema.py               # Task, Result dataclasses + JSON load/validate
    runner.py               # run(solver, tasks, condition) -> Results
    scoring.py              # metrics + failure taxonomy + composite score
    leaderboard.py          # Results -> leaderboard.md
    conditions/             # A-E harnesses (each exposes a uniform solver interface)
    checkers/               # numeric_exact, numeric_tol, sequence_valid, grid_match, exact_label
    references/             # trusted reference impls (the drag sim, the Hanoi validator, etc.)
  tasks/v0/*.json           # the 10 seed tasks
  experiments/              # dated run logs (hypothesis, config, metrics, reflection)
  tests/
  leaderboard.md
```

Ships installable: `pip install -e .`, then `substrate-bench run --condition all --tasks v0` emits metrics and regenerates `leaderboard.md`.

---

## 9. Non-goals (v0)

- Not a general agent framework — it's a measurement instrument with a CLI.
- Not solving ARC-AGI — `rule-001` is an ARC-*flavoured* toy, nothing more.
- No model training. Checkers and references are deterministic Python.
- No AGI claims anywhere in the README. The claim is narrow and defensible: *agents that select substrates beat agents that don't, and we can measure it.*

---

## 10. Definition of done (v0)

Installable package; all 10 tasks run under all 5 conditions from one command; metrics include substrate-selection accuracy and the composite; `leaderboard.md` regenerates from results; tests cover every checker type; README states the thesis without overclaiming. At that point the gate exists, and the rest of the Lab can start being driven against it.
