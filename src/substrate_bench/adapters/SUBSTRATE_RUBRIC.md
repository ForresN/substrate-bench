# Substrate-labelling rubric (v0.1)

The substrate label is the lab's value-add: for each ingested benchmark item we
assign `gold_substrate` (the strategy axis from contract §1) by a **documented
decision procedure, not vibes**. Gold *answers* come from the benchmark; gold
*substrate labels* come from this rubric + human review — **never from a solver**.

## Strategy axis

`language · exact_computation · simulation · search · memory · verify · social`

## Decision procedure (assign the PRIMARY strategy by first match, top-down)

1. **social** — the item hinges on modelling another agent's mental state
   (belief, intent, emotion), theory-of-mind, or social norms.
2. **simulation** — the answer requires evolving a system over time / continuous
   dynamics with no closed form (trajectories, reaction kinetics over time,
   transients, population dynamics).
3. **search** — the answer requires systematic exploration of a discrete or
   combinatorial space: **inducing a transformation rule from worked examples
   (all ARC-AGI items)**, planning/pathfinding, constraint enumeration.
4. **exact_computation** — the answer reduces to a deterministic calculation:
   arithmetic/algebra, closed-form physics/chemistry, stoichiometry, unit
   conversion, evaluating a known formula to a number.
5. **verify** — the task is to *check a given candidate* against constraints or
   tests. Usually a **co-label** (`primary + verify`) when the item asks to both
   solve and confirm against stated conditions.
6. **language** — DEFAULT: genuine linguistic / domain-knowledge recall plus
   qualitative reasoning expressed in prose, where no computation, search, or
   simulation is required (most GPQA conceptual items).
7. **memory** — never used for frontier labelling (no skill library yet).

## Co-labels

Add `verify` to the primary when the item explicitly requires confirming a
candidate/answer against stated constraints. Otherwise keep a single primary.

## Flag `needs_human_review` (do NOT guess) when

- Two strategies are genuinely co-primary **and the choice flips whether
  condition C ("always code") is correctly routed** (e.g. a kinetics item that is
  closed-form `exact_computation` if the system is linear but `simulation` if
  non-linear/stiff).
- `exact_computation` vs `language` is unclear (mostly-recall with a small
  embedded calculation, and the dominant cognitive load is ambiguous).
- The item needs decomposition into sub-strategies the single-primary schema
  can't hold.
- Domain expertise beyond the labeller's is needed to judge what the item requires.

Flagged items are excluded from the scored slice until adjudicated.

## Difficulty (1–3)

- **ARC-AGI-2**: clusters at 3; assign 2 only for small grids (≤10×10) with a
  small palette (≤5 colours) and few example pairs.
- **GPQA Diamond**: graduate-level by construction; default 3, assign 2 for short
  single-step computational items. Use the dataset's writer difficulty hint when
  present.

## Provenance & integrity

- Each label record: `{gold_substrate, difficulty, rationale, provenance, status}`
  where `provenance ∈ {rubric, human_review}` and `status ∈ {labelled,
  needs_human_review}`.
- Rationales are kept **abstract** (e.g. "closed-form kinematics", "conceptual
  recall of reaction mechanism") so committing labels never leaks gated content.
- The solver never sees the label, the category, or the gold answer (prompt-only
  view); the planted-wrong-gold test guards against leakage.

## Why this is partly contamination-robust

Even if a model has memorised a benchmark's answers, the substrate-selection lens
asks a different question — *did it recognise what kind of problem it faced* — so
the **how** signal degrades more gracefully than the **if** (pass/fail) signal as
benchmarks saturate or leak.
