# DRAFT — Do frontier models know *what kind* of problem they're facing?

### Substrate-selection on ARC-AGI-2 and GPQA Diamond

*Draft portfolio post. Numbers are from a single manual run (claude-opus-4-8, 60 tasks); see caveats. No AGI claims.*

Benchmarks usually ask one question: **did the model get the answer right?** That
collapses two very different abilities into one number — *recognising what kind of
thinking a problem needs*, and *being able to do it.* This post separates them.

We took a model's **router** — the component that decides "is this a computation? a
search? a knowledge question?" — and scored its choice **independently of the
answer**, on top of two hard public benchmarks: ARC-AGI-2 (abstract grid induction)
and GPQA Diamond (graduate science). The metric is **substrate-selection accuracy**:
did the declared strategy match an expert label of what the task actually requires.

## The result: routing ≠ solving

Running cognitive-os's `ModelRouter` on **claude-opus-4-8** over a 60-task slice:

> **It picked the right substrate 88% of the time — while solving only 12%.**

Those aren't in tension; they're the point. ARC-AGI-2 and GPQA Diamond are *largely
unsolved* by frontier models, so low task-accuracy is expected. What's striking is
that the router **knows what kind of problem it's looking at even when the model
can't solve it**:

- **77%** of tasks were *right-substrate-but-unsolved* — correct recognition, no solution.
- On **ARC-AGI-2 specifically: 100%** — the router called "this needs search/induction"
  on all 30 tasks and the model solved none. Pure recognition without capability.

Recognition and capability are different axes, and you can measure the first without
the second. That also makes the signal **partly robust to contamination**: a
memorised answer key tells you nothing about whether the model *routed* correctly.

## Selective routing beats reaching for a tool every time

As controls we ran fixed-strategy baselines. An agent that **always reaches for
code** (condition C) is choosing the wrong *strategy* on most of these tasks — it
scored **20%** substrate-selection and **0%** task-accuracy, versus the router's
**88% / 12%**. The gap between selective routing and indiscriminate tooling was
**+0.68** on substrate-selection. Knowing *when not* to compute is most of the skill.

## Where it fails: tool over-triggering

The router was **perfect** on ARC induction (100%) and on GPQA's genuinely
computational items (100%). Its one weak spot was **graduate-science knowledge
questions** (GPQA `language`): **59%**. Every error was the *same* error — reaching
for computation, search, or verification on a question that needed parametric
knowledge. It never under-used a tool; it over-used one.

That matches the research frontier. A grounded literature scan (every claim
cited to a fetched source) found the same diagnosis independently: **LLMs misjudge
their own knowledge boundaries and over-rely on tools when internal knowledge would
do**, and tool-necessity is often more recoverable from a model's *hidden states*
than from its stated reasoning. The fix direction people are exploring —
metacognitive "do I already know this?" checks before invoking a tool — is a clean
next experiment, not a claim we're making here.

## How this was measured (and what it isn't)

- **Prompt-only.** The solver never saw the gold answer, the task category, or the
  substrate label — only the question. A planted-wrong-gold test guards against leakage.
- **Gold answers come from the benchmarks; substrate labels come from a documented
  rubric**, not from the model being tested.
- **Honest limits:** one model, one router, **60 tasks**, first-pass labels, a single
  non-deterministic run (no error bars). Low solve-rate is by design and is **not** a
  capability ranking. This is a measurement-method result, not a leaderboard.

## The takeaway

On two benchmarks built to be hard, a frontier model's router **recognised the
required kind of reasoning far more often than the model could carry it out** — 88%
vs 12% — and its failures were systematic over-triggering of tools on knowledge
questions. If we want agents that *reliably* generalise, "did it route correctly?"
is a question worth scoring on its own. You can't fix what you don't measure.

---
*Method and full numbers: `substrate-bench` (substrate-selection benchmark) +
`cognitive-os` (the router) + `frontier-recon` (the cited literature scan). Run log:
experiments/2026-06-29-frontier-first-real-run.md.*
