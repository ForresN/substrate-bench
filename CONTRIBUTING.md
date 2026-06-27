# Contributing to substrate-bench

The instrument is meant to grow. The three extension surfaces, easiest first:

## 1. Add a task

Drop a JSON file in `tasks/<set>/` (e.g. `tasks/v0/`). Schema (validated by
`schema.validate_task`):

```json
{
  "id": "exact-003",
  "category": "exact_computation",
  "prompt": "…the question as the solver sees it…",
  "gold_substrate": ["code"],
  "checker": { "type": "numeric_exact", "reference_impl": "…", "params": {…}, "answer": 42 },
  "difficulty": 2,
  "rationale": "why this discriminates a substrate choice"
}
```

Rules:
- `gold_substrate` ⊆ {`language`, `code`, `simulation`, `search`, `memory`, `verify`}, non-empty.
- `difficulty` ∈ {1, 2, 3}.
- `checker.type` ∈ {`exact_label`, `numeric_exact`, `numeric_tol`, `sequence_valid`, `grid_match`}.
- **Gold must come from a reference, never an LLM.** For `numeric_*`, store the
  value a reference impl produces and add it to `tests/test_references.py` so the
  derivation is checked. For `sequence_valid`, store the problem params; the
  reference validates candidates at run time.

Make sure the offline `stub` solver still behaves sensibly: a task's correctness
under the stub is gated by whether the chosen substrate is in `gold_substrate`
(see `references/gold.py`), so a new task slots into the existing matrix without
code changes as long as its `category` is in `substrates.ROUTER_CATEGORY_MAP`.
New categories need a line there.

## 2. Add a checker type

1. Write `check_<type>(task, answer) -> bool` in `checkers/__init__.py` (be
   defensive: malformed candidates score `False`, never raise).
2. Register it in `_DISPATCH` and add the name to `schema.VALID_CHECKERS`.
3. Decide whether the type is independently verifiable (`is_verifiable`) — i.e.
   whether condition E's verifier can refute it by recomputation.
4. Extend `references/gold.py` (`gold_answer`/`wrong_answer`/`reference_value`).
5. Add a passing **and** a failing case to `tests/test_checkers.py`.

## 3. Add a reference implementation

Put deterministic, model-free Python in `references/`. It must be pure (no
network, no randomness, no wall-clock) so scoring stays seed-stable. Wire it into
`references/gold.py` and assert its output in `tests/test_references.py`.

## Plugging in a real model

Conditions only ever call `Model.answer(task, *, cot)`. Implement it once and
register a zero-arg factory in `cli.SOLVERS` to expose it to the CLI. The
quickest path is `model.CallableModel`, which wraps a
`complete(prompt, cot) -> (text, in_tok, out_tok)` callable and parses the
completion with `model.parse_answer` (instruct the model to end with
`Answer: <x>`).

## Before you push

```bash
pytest -q          # all green
substrate-bench run --condition all --tasks v0   # regenerates leaderboard.md
```

Keep the README's [Limitations](README.md#limitations) honest, and **never add
AGI claims**. The whole value of this repo is that its claims are small and
falsifiable.
