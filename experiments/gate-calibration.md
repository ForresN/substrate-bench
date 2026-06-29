# Gate calibration — discrimination threshold for the autonomous task-gen gate

*Data source: the first real-model run — cognitive-os `ModelRouter` on claude-opus-4-8,
scored by substrate-bench over the 60-item frontier slice (30 ARC-AGI-2 + 30 GPQA
Diamond), conditions A–E. See [2026-06-29-frontier-first-real-run.md](2026-06-29-frontier-first-real-run.md).*
*This file is machine-relevant: the harness's task-generation gate reads the threshold below.*

## What "discriminating" looks like on real frontier tasks

For each task we measure the **per-task substrate-selection spread E − A**: does the
verify-router (E) select a gold substrate where the pure-next-token floor (A, which
always declares `language`) does not?

Observed distribution over the 60-task frontier slice:

| spread (E − A) | tasks | share | meaning |
|---|---|---|---|
| **+1** | 43 | **72%** | routing matters and the router gets it (A floor wrong, E right) |
| 0 | 10 | 17% | both right or both wrong — task does not separate router from floor |
| −1 | 7 | 12% | routing *hurts*: router left `language` where `language` was correct (over-triggering) |

By benchmark: **ARC-AGI-2 mean +1.00** (all 30 tasks discriminate — abstract induction is never the `language` floor), **GPQA Diamond mean +0.20** (+1 on 13/30; the 7 −1 tasks are the GPQA `language` items the router over-routed to compute/search). Overall mean spread **+0.60**.

## Structural fact the gate must respect

A task whose gold strategy is `language` can **never** score E − A = +1: condition A
always declares `language`, so A is already substrate-correct there (spread ≤ 0).
Therefore a naive "admit iff spread ≥ +1" rule **structurally excludes every
language/knowledge task** — which would train the task generator to stop producing
exactly the items that expose tool **over-triggering** (the dominant real failure
mode found in this run). The gate needs two lanes, not one threshold.

## Recommended gate (data-backed)

**Lane 1 — routing-positive tasks (admit iff per-task spread ≥ +1).**
A generated task is admitted to the scored set if a reference router achieves
`substrate_correct` while the `language` floor (condition A) does not — i.e.
**E − A substrate spread ≥ +1**. This is the cleanest, most defensible signal and
is what the round-3 separation-of-powers gate should enforce per task. On this run
72% of frontier tasks pass; it admits all ARC and the routable GPQA items.

**Lane 2 — over-triggering traps (reserve a language/knowledge quota).**
Because Lane 1 excludes `language`-gold tasks, the gate must **separately reserve a
quota of knowledge/`language` tasks** (recommend ~30%, matching the frontier slice's
17/60 ≈ 28% language share) that act as over-triggering traps: a task qualifies if a
reference router is *tempted* to mis-route it (i.e. at least one of C/D mis-routes,
spread −1 is achievable). These catch the failure this run actually surfaced.

**Batch-level floor.** For a candidate batch, require the routing-positive fraction
**≥ 0.70** (frontier observed 0.72) AND a non-zero over-triggering-trap quota. Reject
batches that are all-Lane-1 (they can't measure over-triggering) or all-trivial
(spread 0 throughout).

## Caveats (do not over-fit)

- Calibrated on **one model** (claude-opus-4-8), **one router** (cognitive-os
  ModelRouter), **60 tasks**, **first-pass labels**. Treat the 0.70 batch floor as a
  starting value to re-estimate as the slice and model set grow.
- The threshold is about **routing discriminability**, not task quality; gold-answer
  provenance and the substrate rubric remain the separate quality gates.
- Re-run this calibration whenever the labelling rubric or the reference router
  changes; the spread distribution is a function of both.
