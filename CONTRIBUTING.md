# Contributing to substrate-bench

The instrument is meant to grow. The three extension surfaces, easiest first:

## 1. Add a task

Prefer the committed generator `tools/author_tasks.py` (gold from references, or
human-reviewed for language/social) — `python tools/author_tasks.py` regenerates
the grown set deterministically. To add one by hand, drop a JSON file in
`tasks/<set>/` (validated by `schema.validate_task`):

```json
{
  "id": "exact-201",
  "category": "exact_computation",
  "prompt": "…the question as the solver sees it…",
  "gold_substrate": ["exact_computation"],
  "checker": { "type": "numeric_exact", "reference_impl": "…", "params": {…}, "answer": 42 },
  "difficulty": 2,
  "rationale": "why this discriminates a strategy choice",
  "provenance": "reference"
}
```

Rules (contract v0.1):
- `gold_substrate` is the **strategy** axis ⊆ {`language`, `exact_computation`,
  `simulation`, `search`, `memory`, `verify`, `social`}, non-empty. **`code` is not
  a strategy** — it's the execution medium (`executes_code`), carried on the
  solver's route declaration, not on the task.
- `difficulty` ∈ {1, 2, 3}; `provenance` ∈ {`reference`, `human_review`}.
- `checker.type` ∈ {`exact_label`, `numeric_exact`, `numeric_tol`, `sequence_valid`, `grid_match`}.
- **Gold provenance:** computational gold (`exact/simulation/search/verify`) comes
  from a trusted reference (`provenance: "reference"`); `language`/`social` gold is
  human-authored (`provenance: "human_review"`). **Never from a solver.** Reference
  golds are re-derived in `tests/test_references.py` to prove it.

Make sure the offline `stub` solver still behaves sensibly: under the stub, a
task's correctness is gated by whether the declared strategy ∈ `gold_substrate`
(see `model.StubModel`), so a new task slots in without code changes as long as
its `category` is in `substrates.ROUTER_CATEGORY_MAP` (categories that *are*
strategy names map to themselves). New categories need a line there.

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

## 4. Add a benchmark adapter (tier-1 frontier)

Create `adapters/<name>/` with three things:

1. **`manifest.json`** — `benchmark_id`, `name`, `version`, `licence`,
   `source_url`, `citation`, `redistributable` (bool), `contamination_note`,
   `fetch_instructions`. Be honest about the licence.
2. **`adapter.py`** — subclass `BenchmarkAdapter`; implement `fetch(limit)`
   (populate `cache/`, **respecting the licence** — do NOT vendor where it
   forbids; gated sources read a token from env), `iter_items()` (yield
   `RawItem`s from cache), and `to_task_dict(raw, label)` (map to the task schema,
   **carrying the benchmark's own gold answer**, `provenance="benchmark"`).
   Register it in `adapters/__init__.py`.
3. **`labels.json`** — the lab's substrate labels per item, applied via
   `SUBSTRATE_RUBRIC.md`. Each record: `{gold_substrate, difficulty, rationale,
   provenance, status}`. Flag ambiguous items `needs_human_review` (excluded from
   the scored slice). Keep rationales abstract so committing labels leaks nothing.

Hard rules: gold ANSWERS come from the benchmark, gold SUBSTRATE labels from the
rubric + review — **never a solver**. Caches and materialised `tasks/frontier/`
are gitignored; only adapters, manifests, and labels are committed. Add offline
(synthetic-item) tests to `tests/test_adapters.py` — CI must not hit the network.

## Plugging in a real model

Conditions only ever call `Model.solve(task, *, force_strategy,
force_executes_code, cot)`. Implement it once and register a zero-arg factory in
`cli.SOLVERS`. The quickest path is `model.CallableModel`, which wraps a
`complete(prompt, cot) -> (text, in_tok, out_tok[, code_executed])` callable. For
D/E it asks the model to emit the JSON route declaration and parses it (loud
failure on malformed); for A/B/C the declaration is fixed and only the answer is
parsed. The optional 4th return value (observed `code_executed`) feeds the
consistency audit.

## Promoting a baseline (human-only)

`substrate-bench baseline promote` requires a TTY and refuses for any
non-interactive caller (contract §4). Do not work around this from an agent —
the guardrail is the point. Commit `baselines/` so promotions show in git history.

## Before you push

```bash
pytest -q          # all green
substrate-bench run --condition all --tasks smoke   # regenerates leaderboard.md
```

Keep the README's [Limitations](README.md#limitations) honest, and **never add
AGI claims**. The whole value of this repo is that its claims are small and
falsifiable.
