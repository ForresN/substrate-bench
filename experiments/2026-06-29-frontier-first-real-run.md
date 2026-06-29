# Experiment 004 — first full manual loop: real model on frontier, by hand

- **Date:** 2026-06-29
- **Loop:** MEASURE (cognitive-os router on frontier, scored by substrate-bench) → FIND THE GAP → RECON (frontier-recon). The dry-run of what the harness will automate.
- **Solver:** cognitive-os `ModelRouter` on **claude-opus-4-8** (real), via `cognitive_os.adapter.CognitiveOSModel` → substrate-bench `run_all`.
- **Task set:** `frontier` (60: 30 ARC-AGI-2 `search` + 30 GPQA Diamond), conditions A–E.
- **Integrity:** prompt-only view throughout (solver sees `Problem(id, prompt, difficulty)` only — no gold/category/gold_substrate); no `temperature` sent (Opus 4.8 omits it). Run: 27.9 min, **0 errors**.
- **Artifacts:** results JSON `results/frontier-cognitive-os-model.json` (gitignored — embeds GPQA answers); recon brief `frontier-recon/runs/run_20260629T031513Z_107ddd/`; gate threshold in [gate-calibration.md](gate-calibration.md).

## Step 0 — gold trusted first

- **Adjudicated** the one flagged item (`q1eb26b9c365e`, select-the-DNA-encoding-P53): `needs_human_review` → `labelled`, `gold_substrate = [exact_computation, verify]` (translate each candidate via the genetic code = deterministic mapping; check against the target protein = verify). Provenance `human_review`.
- **Spot-reviewed** the other 29 GPQA labels against the rubric; re-read every borderline case (the `search` induction puzzle, the eV→colour and H-atom-branching items, the epistasis item, the parallax scaling). **No clear mislabels; all retained with rationale.** Trusted slice = 60 (30 ARC `search`; 30 GPQA = 17 `language`, 12 `exact_computation`, 1 `search`).

## Step 1 — the real measurement

| Cond | Substrate-sel. acc | Task acc | Composite | Audit |
|---|---|---|---|---|
| A · Direct | 28% | 30% | 0.293 | 100% |
| B · CoT | 28% | 38% | 0.343 | 100% |
| C · Code-always | 20% | **0%** | 0.080 | 43% |
| **D · Router** | **88%** | 12% | 0.423 | 42% |
| **E · Router+Verify** | **88%** | 12% | 0.423 | 40% |

**Substrate-discrimination spread 0.68; router-vs-code-always gap +0.68.**

### The headline finding: routing ≠ solving

The real router selects the right substrate **88%** of the time (53/60) while the
model solves only **12%**. Low task-accuracy is **expected and correct** — ARC-AGI-2
and GPQA Diamond are largely unsolved by frontier models. The scientific signal is
that *the router knows what kind of problem it faces even on problems it cannot
solve.* Quantified as the **answer/substrate decoupling** (condition D):

| | right-substrate, solved | **right-substrate, UNSOLVED** | wrong-substrate |
|---|---|---|---|
| ARC-AGI-2 (30) | 0 (0%) | **30 (100%)** | 0 (0%) |
| GPQA Diamond (30) | 7 (23%) | 16 (53%) | 7 (23%) |
| **All (60)** | 7 (12%) | **46 (77%)** | 7 (12%) |

**77% of tasks are right-substrate-but-unsolved.** On ARC the router calls "this is
`search`" on all 30 and the model solves none — a clean separation of *recognition*
from *capability*.

## Step 2 — routing-failure map

Substrate-selection accuracy by cell (D/E):

| benchmark × gold | n | D/E |
|---|---|---|
| ARC `search` | 30 | **100%** |
| GPQA `exact_computation` | 12 | **100%** |
| GPQA `search` | 1 | 100% |
| **GPQA `language`** | 17 | **59%** ← only weak cell |

Router confusion (D), `language` gold → declared: `language`×10, **`search`×4,
`exact_computation`×2, `verify`×1**. **The single routing weakness is tool
over-triggering: on graduate-science questions that need parametric knowledge
(`language`), the router reaches for computation/search/verify in 7/17 cases.**
Every mis-route is an over-reach toward tools; the reverse error (under-using a tool
where one is needed) did not occur in this slice. The 7 over-triggered items are
exactly the 7 tasks where routing *hurt* vs the language floor (spread −1 in
[gate-calibration.md](gate-calibration.md)).

### Secondary finding — the consistency audit earns its keep

Audit pass-rate falls to ~40% on C/D/E because cognitive-os declares
`executes_code = true` (e.g. for `search`/`exact_computation`) but its substrate
often **abstains without actually running code** (`gave_up` dominates D/E execution
on ARC). The audit correctly catches *declared-but-not-executed* — an
**execution-layer** signal about cognitive-os, orthogonal to routing accuracy. The
router's *declaration* is right; its *executor* doesn't follow through on these hard
tasks. (A/B declare `language`/no-code and pass audit 100%.)

## Step 3 — gate calibration

Per-task E−A substrate spread: **+1 on 72%** of tasks, 0 on 17%, −1 on 12%. ARC mean
+1.00, GPQA mean +0.20. Recommended gate: **admit routing-positive tasks at spread
≥ +1, plus a reserved ~30% knowledge/`language` quota as over-triggering traps**,
with a batch floor of 0.70 routing-positive. Full rationale + the structural caveat
(language-gold tasks can never score +1) in [gate-calibration.md](gate-calibration.md).

## Step 4 — recon on the sharpest gap

Ran `frontier-recon` (keyed, complete) on: *when should an LLM answer from parametric
knowledge vs. invoke tools/code/search, and how to reduce tool over-triggering on
knowledge-heavy QA*. **`frontier-recon audit` → PASS** (16 claims / 40 citations all
resolve to fetched evidence; status `complete`, $0.13, 150s). One weak Tier-3
entailment verdict flagged (the low-confidence gap claim "no GPQA-specific
answer-internally-vs-tool method exists", score 0.30) — appropriately advisory.

The brief converges on our finding from the literature:
- **Diagnosis matches:** LLMs misjudge their own knowledge boundaries and over-rely
  on tools when internal knowledge suffices; tool-necessity is more recoverable from
  **hidden states** than from verbalized reasoning.
- **Methods (candidate directions):** SMART (metacognitive tool-use training),
  Probe&Prefill (hidden-state probe + steering), necessity/utility decision
  frameworks, epistemic-boundary DPO alignment. Diagnostics: When2Tool, LiveBrowseComp.
- **Novel angle (validates this lab):** "benchmark the decision boundary itself, not
  just final accuracy" — exactly substrate-bench's substrate-selection lens.

**Candidate improvement direction for cognitive-os (recorded, NOT implemented this
session):** add an *epistemic-boundary check* to the ModelRouter — before declaring a
computational/search strategy, estimate whether the model already knows the answer
(necessity/utility framing; hidden-state probe where internals are available) — to
cut over-triggering on `language`/knowledge items, the only weak cell. This is a
candidate for a future gated experiment, measured by this same harness.

## Limitations (honest)

- **First-pass labels.** GPQA substrate labels are one rubric pass + one adjudication;
  not independently double-blind reviewed. Substrate-selection accuracy is scored
  against them.
- **Single model, single router, n=60.** One run of claude-opus-4-8 + cognitive-os
  ModelRouter on a 60-task slice; no repeats/seeds (the real model is non-deterministic
  — re-runs will wobble). No confidence intervals claimed.
- **Low solve rate is by design**, not a result about model quality; do not read task
  accuracy as a capability ranking.
- **Audit ≠ routing.** The ~40% audit rate reflects cognitive-os's executor abstaining,
  not router error; keep the two separate.
- **No AGI claims.** The claim is narrow: a frontier model's router identifies the
  required substrate far better than it solves the task, and we can measure that.

## What this hands the harness

The recon and adapter interfaces exercised end-to-end by hand, plus a data-backed
discrimination threshold ([gate-calibration.md](gate-calibration.md)) for the
autonomous task-gen gate — the inputs the harness handoff was waiting on.
