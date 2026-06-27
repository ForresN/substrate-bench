# Measurement Contract — v0.1

*Authoritative resolution of the open questions raised in the substrate-bench v0 build handoff. This is the source of truth for `substrate-bench` v0.1 and for any solver (incl. `cognitive-os`) measured by it. Where this conflicts with the original v0 spec, this governs.*

---

## 1. The two-axis ontology (resolves OQ1)

v0 conflated *cognitive strategy* with *execution medium*. They split:

**Strategy axis** — what the task actually requires, and the only thing `gold_substrate` and substrate-selection accuracy are scored against:

```
language | exact_computation | simulation | search | memory | verify | social
```

**Execution-medium flag** — orthogonal: `executes_code: true|false`.

`code` is **removed as a strategy**. It was never a peer of `simulation`/`search`; it is the medium they are realised through. Consequences:

- "Writes Python that time-steps a trajectory" → strategy `simulation`, `executes_code: true`.
- "Writes Python that runs BFS" → strategy `search`, `executes_code: true`.
- "Writes Python that multiplies two integers" → strategy `exact_computation`, `executes_code: true`.
- "Answers a sentiment question in prose" → strategy `language`, `executes_code: false`.

This is why condition C ("always reach for code") is still meaningfully *wrong* on `language`/`social` tasks: running code is the wrong **strategy** there, regardless of medium.

## 2. The route-declaration contract (resolves OQ1)

A solver **must emit a structured route declaration before producing its answer.** We never infer the substrate from tool calls — inference measures our heuristic, not the agent's cognition, and the lab's thesis is precisely that a capable agent *recognises what kind of problem it faces*. Forcing the declaration operationalises the thesis and makes it machine-checkable.

Required shape:

```json
{
  "strategy": "search",
  "executes_code": true,
  "rationale": "Discrete state-space; needs systematic expansion, not a formula.",
  "answer": "<final answer in the checker's expected form>"
}
```

- Conditions A/B/C have a fixed implicit declaration (A/B: `language`, no code; C: `exact_computation`, code on). D/E **emit** it.
- A solver may declare a primary strategy plus `verify` (E does this).

## 3. Two-level scoring (resolves OQ1)

Score the declaration and the answer **independently**, then audit consistency:

1. **`substrate_correct`** — is the declared `strategy` ∈ `gold_substrate`? (the novel metric)
2. **`answer_correct`** — via the declared checker, unchanged from v0.
3. **Consistency audit** — does observed behaviour match the declaration? v0.1 scope: if `executes_code: true`, did code actually execute? (Deeper structural audit — "did a `search` declaration actually expand states rather than emit a one-liner" — is deferred to v0.2; record the hook now.)

The decoupling is the point: a real model can be `substrate_correct` but `answer_correct=false` (`right_substrate_bad_execution`) or vice-versa. The stub only showed one such decoupling; real solvers will show the full matrix, and that matrix *is* the research signal.

Failure taxonomy maps cleanly: `wrong_substrate` (declaration ∉ gold), `right_substrate_bad_execution` (declaration ∈ gold, answer wrong), `no_verification`, `gave_up`, `none`.

## 4. Baseline registry (resolves OQ2) — with a guardrail

Add a `baselines/` registry keyed by `(task_set, solver_id)`, plus CLI:

```
substrate-bench baseline promote <run.json> --solver <id> --task-set v0
substrate-bench baseline show --solver <id> --task-set v0
```

**Guardrail — promotion is human-only.** The autonomous loop may **read** the baseline (the gate needs it) but must **never promote** to it. Otherwise an agent can quietly lower its own bar and "pass" the gate by regressing the baseline. The promote command is a human action; the loop has read-only access. Treat the registry as tamper-evident (commit it; promotions show up in git history).

## 5. Gate comparison policy (resolves OQ3) — confirmed

The gate is **candidate-vs-same-baseline only**: a `cognitive-os` change is compared to *that solver's own prior recorded baseline* on the same task set. Cross-condition comparisons (E vs C) are **leaderboard findings, never merge gates.**

This is why E's result is correct behaviour, not a bug: E beats C on composite by +0.50 but costs +133%, and the gate rejects it on the +15% budget — because the gate answers "did this *change* improve things without blowing its own cost," not "is verification worth it in absolute terms." The latter is a human judgment informed by the leaderboard. Keep them separate; do not let cross-condition wins auto-merge.

## 6. Policy levers (resolves OQ4)

Composite `= 0.6·task_accuracy + 0.4·substrate_selection_accuracy` and the +15% cost budget stay **fixed for v0.1**. They are deliberately *a* gate, not the perfect one. Revisit only **after** a real model-backed router produces data showing how answer- and substrate-accuracy actually decouple — tuning these on stub data would overfit to an artefact.

## 7. Task-set growth (resolves OQ5) — with separation of powers

Target for v0.1: ~5 tasks per (strategy × difficulty) across the 6 task-bearing strategies × 3 difficulties ≈ **~90 tasks**, enough to expose the difficulty-regime collapse (the Apple-paper effect).

Authoring: human-seeded now; then a **review-gated autonomous task-generation loop** — and this is the lab's first real autonomous job. Two hard rules:

- **Separation of powers.** The loop that *generates tasks* must never be the loop that is *scored on them*. An agent that authors its own exam writes an easy exam.
- **Gold provenance.** Generated tasks get gold answers from the trusted reference implementations or human review — **never from the solver under test.** This keeps the answer key uncontaminated.

## 8. Migration notes for the existing v0 build

What changes from the green v0:
- Remove `code` from the strategy enum; add the `executes_code` flag; remap the existing `code`-gold tasks to `exact_computation` (or `simulation`/`search` where that's what the reference actually does — re-check each).
- Add the route-declaration parse + the consistency audit to the solver seam.
- Split scoring into the two independent levels + audit.
- Add the `baselines/` registry + CLI with read-only access for any non-interactive (agent) caller.
- Grow `tasks/v0` toward §7 coverage.
- The stub's "substrate = task category" shortcut stays valid as an offline fixture, but the `CallableModel` path must exercise a real emitted declaration.
```

