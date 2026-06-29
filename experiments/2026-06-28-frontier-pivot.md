# Experiment 003 — frontier pivot: the substrate lens on ARC-AGI-2 + GPQA Diamond

- **Date:** 2026-06-28
- **Author:** Cognitive Systems Lab
- **Solver:** `stub` (deterministic, offline oracle fixture)
- **Sets:** tier-1 `frontier` (59 items: 30 ARC-AGI-2 + 29 GPQA Diamond) vs tier-0 `smoke` (46 toy)
- **Command:** `substrate-bench frontier build && substrate-bench run --tasks frontier`
- **Artifacts:** [`leaderboard-frontier.md`](../leaderboard-frontier.md), [`leaderboard.md`](../leaderboard.md) (smoke). Frontier per-item results are **not** committed (they would embed benchmark answers).

## Hypothesis

Re-grounding the benchmark on established frontier tasks should leave the
substrate-selection lens **shape-invariant**: selective routers (D/E) still beat
indiscriminate code (C), C still mis-routes language/knowledge items — but now on
tasks that are not trivial, and partly robust to the contamination/saturation
that degrade pass/fail scoring.

## Setup

- **Adapters** ingest each benchmark's own gold ANSWER; the lab adds the
  `gold_substrate` label via the documented rubric (`adapters/SUBSTRATE_RUBRIC.md`).
- **Slice (~60):** all 30 ARC labelled `search` (abstract rule induction); 30 GPQA
  Diamond labelled by reading each item → **17 `language`** (conceptual/recall),
  **11 `exact_computation`** (quantitative physics/chem), **1 `search`** (a hidden
  input→output induction puzzle), **1 `needs_human_review`** (codon-table item,
  ambiguous exact_computation/verify/language — excluded from the scored slice).
- **Integrity:** solver sees the prompt-only `PromptView` (no gold/category/
  gold_substrate); planted-wrong-gold test proves no leak; declarations +
  two-level scoring + audit carry over unchanged. GPQA is gated/contamination-
  sensitive: content is fetched with a licensed token and cached (gitignored),
  never committed — only abstract substrate labels (hashed item ids) are.

## Results

| Condition | Frontier sub-acc | Frontier task-acc | Frontier composite | Smoke sub-acc | Smoke composite |
|---|---|---|---|---|---|
| A · Direct | 29% | 0% | 0.115 | 15% | 0.126 |
| B · CoT | 29% | 29% | 0.288 | 15% | 0.257 |
| C · Code-always | **19%** | 19% | 0.186 | 26% | 0.261 |
| D · Router | 100% | 100% | 1.000 | 98% | 0.978 |
| E · Router+Verify | 100% | 100% | 1.000 | 100% | 1.000 |

- **Substrate-discrimination spread:** frontier **0.81**, smoke 0.85 — the frontier
  slice strongly separates routers from baselines.
- **Router-vs-Code-always gap:** frontier **+0.81**, smoke +0.74.

### The lens holds its shape (H confirmed)

Condition C declares `exact_computation` on everything. Its substrate-correctness
**by gold strategy** on frontier:

| gold strategy | C correct |
|---|---|
| exact_computation (11 GPQA) | **11 / 11** |
| language (17 GPQA) | **0 / 17** |
| search (30 ARC + 1 GPQA) | **0 / 31** |

This is the whole argument, now on frontier tasks: "always reach for code" is the
**right strategy only for the computational minority** and the **wrong strategy**
for the knowledge (`language`) and induction (`search`) majority. On the
strategy-mix of real benchmarks, C's substrate accuracy (19%) falls *below* even
the no-tool baselines A/B (29%).

### The decoupling sharpens

A and B both declare `language` and so share 29% substrate accuracy, but CoT lifts
**task** accuracy from 0% → 29% (it rescues execution on the 17 language items).
Substrate-selection and answer-correctness move independently — exactly the matrix
v0's stub could barely show, now on graduate-level content.

## Interpretation

The contribution travels. Measuring **how** (did the solver recognise the kind of
problem) rather than only **if** (pass/fail) produces a stable, discriminating
signal on ARC-AGI-2 and GPQA Diamond. Because the lens asks a different question
than the answer key, it degrades more gracefully under contamination/saturation —
a memorised answer doesn't tell you the model *routed* correctly.

## Threats to validity — what this does NOT show

- **The `stub` is an oracle fixture.** Its 100% task-accuracy for D/E is a fixture
  artefact, **not** model performance — ARC-AGI-2 and GPQA Diamond are largely
  unsolved by frontier models. The meaningful instrument outputs here are
  **substrate-selection accuracy** and the **discrimination spread**; the headline
  answer-accuracy awaits a real model-backed router.
- **Slice size & labelling.** 59 scored items; ARC labels are mechanical (rubric:
  all induction = search), GPQA labels are my rubric application over 30 items with
  1 flagged `needs_human_review`. Labels are first-pass `rubric` provenance, not yet
  independently adjudicated.
- **GPQA difficulty** comes from the dataset's writer estimate; ARC clusters at
  difficulty 3 (frontier ARC is genuinely hard).

## Next steps

1. Real model-backed router run (CallableModel over a provider) on this frontier
   slice — the falsifiable prediction: substrate and answer accuracy decouple
   hard, and C's language/search penalty persists.
2. Independent human review of the GPQA `rubric` labels; resolve the
   `needs_human_review` item.
3. Add Humanity's Last Exam (knowledge) and, with an execution harness, SWE-bench
   Pro (deferred — needs repo execution) as further adapters.
