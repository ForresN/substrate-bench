# Frontier Recon — When should an LLM agent answer a question from its own parametric knowledge versus invoking tools, code execution, or search? Survey methods to decide tool use and to reduce tool over-triggering / over-reliance on tools for knowledge-heavy questions such as graduate-level science QA.

*Generated 2026-06-29T03:15:13Z · recency window 365d · status: **COMPLETE** · sources: 24 · cost: $0.1250 / 150s*

> ⚠ **Staleness:** This field moves fast. Treat this brief as stale ~30 days after generation.

> This is a research **aid**, not an oracle. Every claim below is a verbatim
> fragment of a fetched source (see References); read the sources before relying on them.

## 1. Problem framing

The core question is when an LLM agent should rely on its internal (parametric) knowledge versus invoking external tools (search, code execution, APIs), and how to mitigate 'tool overuse' — unnecessary tool calls for tasks solvable internally — which adds cost and latency without improving (and sometimes harming) accuracy. Multiple sources frame this as aligning the agent's tool-use decision boundary with its knowledge boundary, and several propose datasets, benchmarks, theoretical frameworks, training methods, and lightweight inference-time controllers to make this decision better. Knowledge-heavy QA (e.g., graduate-level science) is implicated because models often misjudge their own knowledge boundaries.

**Sub-queries investigated:** When should an LLM agent answer a question from its own parametric knowledge versus invoking tools, code execution, or search? Survey methods to decide tool use and to reduce tool over-triggering / over-reliance on tools for knowledge-heavy questions such as graduate-level science QA.; when should llm agent answer question from its own parametric knowledge versus invoking tools code execution search surv state of the art; when should llm agent answer question from its own parametric knowledge versus invoking tools code execution search surv benchmark leaderboard; when should llm agent answer question from its own parametric knowledge versus invoking tools code execution search surv github implementation; when should llm agent answer question from its own parametric knowledge versus invoking tools code execution search surv survey 2025 2026

## 2. SOTA methods

### SMART (Strategic Model-Aware Reasoning with Tools) — supervised metacognitive training [S1][S2][S3]
- **Does:** Trains agents on a dataset (SMART-ER) where reasoning alternates between parametric and tool-dependent steps with rationales for when tools are necessary, to enhance self-awareness and balance internal knowledge vs tool use.
- **Trade-offs:** Requires a curated dataset and supervised training; reported gains are large but on the authors' own dataset and OOD sets.
- _confidence: high_

### Probe&Prefill — hidden-state linear probe + steering [S4][S5][S6]
- **Does:** Uses a lightweight linear probe to read a hidden-state signal of tool necessity from the pre-generation representation, then prefills the model's response with a steering sentence to act on it.
- **Trade-offs:** Training-free baselines (prompt-only, reason-then-act) provide limited control; probe-based approach requires access to hidden states; large reductions in tool calls with small accuracy loss.
- _confidence: high_

### Prompt-only and Reason-then-Act (training-free baselines) [S7][S8]
- **Does:** Prompt-only varies the prompt to discourage unnecessary calls; Reason-then-Act requires the model to reason about tool necessity before acting.
- **Trade-offs:** Both provide limited control: prompt-only suppresses necessary calls alongside unnecessary ones, and reason-then-act still incurs a disproportionate accuracy cost on hard tasks.
- _confidence: high_

### Necessity/utility/affordability decision framework with hidden-state estimators [S9][S10][S11]
- **Does:** Evaluates web-search tool-use decisions along necessity, utility, and affordability using both a normative (optimal allocation) and descriptive (observed behavior) perspective, then trains lightweight estimators of need and utility from hidden states to drive simple controllers.
- **Trade-offs:** Models' perceived need/utility are often misaligned with true need/utility; estimators require hidden-state access; demonstrated across three tasks and six models.
- _confidence: high_

### Knowledge-aware epistemic boundary alignment (DPO) and balanced reward training [S12][S13][S14][S15]
- **Does:** Addresses 'knowledge epistemic illusion' (models misjudging internal knowledge boundaries) via a DPO-based boundary alignment strategy, and counters outcome-only-reward-induced overuse by balancing reward signals during training.
- **Trade-offs:** Outcome-only rewards inadvertently encourage tool overuse; balancing rewards reduces unnecessary calls without sacrificing accuracy but requires retraining.
- _confidence: high_

### Epistemic-framework alignment of decision boundary to knowledge boundary (position) [S16][S17]
- **Does:** Proposes treating internal reasoning and external actions as equivalent epistemic tools and aligning the agent's tool-use decision boundary with its knowledge boundary to minimize unnecessary tool use.
- **Trade-offs:** Position paper / theoretical framework rather than an implemented system.
- _confidence: high_

## 3. Relevant repos

| Repo | Does well | Maturity | License | Cite |
| --- | --- | --- | --- | --- |
| when2tool (Probe&Prefill / When2Tool benchmark) | Provides a benchmark of 18 environments spanning categories of tool necessity and code for the Probe&Prefill method. | unknown | unknown | [S18][S19] |
| AGI-Edgerunners/LLM-Agents-Papers | Curated repository listing papers related to LLM-based agents. | 2.3k stars, 164 commits, last updated ~11 months before snapshot | unknown | [S20][S21] |

## 4. Benchmarks & standings

### When2Tool [S22]
| System | Score | As of | Cite |
| --- | --- | --- | --- |
| Probe&Prefill | reduces tool calls by 48% with only 1.7% accuracy loss | arXiv:2605.09252v2 (20 May 2026) | [S23] |

### LiveBrowseComp / BrowseComp (search-agent diagnostics) [S24][S25]
| System | Score | As of | Cite |
| --- | --- | --- | --- |
| all evaluated agents (on LiveBrowseComp) | below 2% closed-book accuracy; search-augmented scores drop by 25–40 points relative to BrowseComp | arXiv:2605.28721v1 (27 May 2026) | [S26] |

### GSM8K / MINTQA (OOD generalization for SMARTAgent) [S27]
_Standings not extracted; benchmark identified only._

## 5. Synthesis — combine / novel angle / gaps

**Techniques to combine:**
- A consistent finding across independent works is that LLMs misjudge their own knowledge boundaries — they over-rely on tools even when internal knowledge suffices — and that tool necessity is more accurately recoverable from internal model signals (hidden states) than from the model's own verbalized reasoning. This suggests pairing an epistemic-boundary framing with hidden-state probes/estimators as a controller. [S28][S29][S30][S31]
- Training objectives shape overuse: outcome-only rewards encourage unnecessary tool calls, while either supervised metacognitive data (SMART) or reward balancing / DPO boundary alignment can cut tool use substantially without losing accuracy — complementing inference-time probe controllers that need no retraining. [S32][S33][S34]

**Candidate novel angle:** Knowledge-heavy QA benchmarks may be confounded by intrinsic knowledge: search agents often answer from memory rather than retrieval, so evaluations should distinguish memory-backed verification from evidence-driven discovery (e.g., using recency-controlled questions like LiveBrowseComp) when measuring whether tools were actually needed. This argues for benchmarking the decision boundary itself, not just final accuracy. [S35][S36][S37]

**Gaps & opportunities:**
- The fetched sources do not provide a method or benchmark specifically targeting graduate-level science QA (e.g., GPQA) for the answer-internally-vs-invoke-tools decision; coverage of knowledge-heavy QA is generic or web-search-focused rather than graduate-science-specific. [S38] ⚠ _weak support (0.30)_
- Hidden-state-based controllers (Probe&Prefill, need/utility estimators) require access to model internals, limiting applicability to closed/API-only models; the sources do not report a comparably effective approach for black-box models beyond limited prompt-only baselines. [S39][S40]

## 6. Recency & confidence

- Newest source: 2026-05-27T21:21:42Z
- Oldest source: 2021-08-29T19:33:51Z
- High confidence claims are anchored in primary arXiv/ACL sources directly addressing tool overuse (SMART, Tool-Overuse Illusion, To Call or Not to Call, When2Tool/Probe&Prefill, the epistemic-tool position paper, LiveBrowseComp). Reported quantitative gains are taken verbatim from author abstracts and reflect their own evaluations, not independent replication. Several sources are from 2026-dated arXiv listings whose dates appear in the provided metadata. Many fetched sources (gravitational-wave papers, code-generation challenges, generic agent overviews, YouTube/marketing pages) are off-topic and were not used for substantive claims.

[Tier-3 advisory] entailment: judged 16 claim(s), 1 flagged weakly-supported
  [T3 weak-entailment] claim=c_g01 score=0.30 :: Shows generic categories but doesn't establish absence of graduate-science-specific coverage.

## 7. What I could NOT verify

- **Performance specifically on graduate-level science QA (e.g., GPQA)** — No fetched source reports tool-use decision methods or numbers on a graduate-level science QA benchmark by name.
- **Licenses and maturity of the when2tool and LLM-Agents-Papers repos** — Source text does not state license; star/commit counts present only for LLM-Agents-Papers.
- **SMART numerical results in the ACL Findings PDF version (src_139ce7680a50)** — The PDF source text was truncated before reporting the quantitative results; identical claims verified instead from the arXiv HTML version (src_092263756033).

## References

_Every marker resolves to a source fetched in this run and stored in the evidence store (URL + sha256 + timestamp)._

- **[S1]** SMART: Self-Aware Agent for Tool Overuse Mitigation · https://arxiv.org/html/2502.11435v1 · fetched 2026-06-29T03:16:00Z · sha256 `487dcb6fcfb4` · arxiv
- **[S2]** SMART: Self-Aware Agent for Tool Overuse Mitigation · https://arxiv.org/html/2502.11435v1 · fetched 2026-06-29T03:16:00Z · sha256 `487dcb6fcfb4` · arxiv
- **[S3]** SMART: Self-Aware Agent for Tool Overuse Mitigation · https://arxiv.org/html/2502.11435v1 · fetched 2026-06-29T03:16:00Z · sha256 `487dcb6fcfb4` · arxiv
- **[S4]** LLM Agents Already Know When to Call Tools - Even Without Reasoning · https://arxiv.org/html/2605.09252v2 · fetched 2026-06-29T03:15:58Z · sha256 `2705bf6c2d2e` · arxiv
- **[S5]** LLM Agents Already Know When to Call Tools - Even Without Reasoning · https://arxiv.org/html/2605.09252v2 · fetched 2026-06-29T03:15:58Z · sha256 `2705bf6c2d2e` · arxiv
- **[S6]** LLM Agents Already Know When to Call Tools - Even Without Reasoning · https://arxiv.org/html/2605.09252v2 · fetched 2026-06-29T03:15:58Z · sha256 `2705bf6c2d2e` · arxiv
- **[S7]** LLM Agents Already Know When to Call Tools - Even Without Reasoning · https://arxiv.org/html/2605.09252v2 · fetched 2026-06-29T03:15:58Z · sha256 `2705bf6c2d2e` · arxiv
- **[S8]** LLM Agents Already Know When to Call Tools - Even Without Reasoning · https://arxiv.org/html/2605.09252v2 · fetched 2026-06-29T03:15:58Z · sha256 `2705bf6c2d2e` · arxiv
- **[S9]** To Call or Not to Call: A Framework to Assess and Optimize LLM Tool Calling · https://arxiv.org/html/2605.00737v1 · fetched 2026-06-29T03:16:02Z · sha256 `2de53186de69` · arxiv
- **[S10]** To Call or Not to Call: A Framework to Assess and Optimize LLM Tool Calling · https://arxiv.org/html/2605.00737v1 · fetched 2026-06-29T03:16:02Z · sha256 `2de53186de69` · arxiv
- **[S11]** To Call or Not to Call: A Framework to Assess and Optimize LLM Tool Calling · https://arxiv.org/html/2605.00737v1 · fetched 2026-06-29T03:16:02Z · sha256 `2de53186de69` · arxiv
- **[S12]** The Tool-Overuse Illusion: Why Does LLM Prefer External Tools over Internal Knowledge? · https://arxiv.org/html/2604.19749v1 · fetched 2026-06-29T03:16:10Z · sha256 `00e805e36d85` · arxiv
- **[S13]** The Tool-Overuse Illusion: Why Does LLM Prefer External Tools over Internal Knowledge? · https://arxiv.org/html/2604.19749v1 · fetched 2026-06-29T03:16:10Z · sha256 `00e805e36d85` · arxiv
- **[S14]** The Tool-Overuse Illusion: Why Does LLM Prefer External Tools over Internal Knowledge? · https://arxiv.org/html/2604.19749v1 · fetched 2026-06-29T03:16:10Z · sha256 `00e805e36d85` · arxiv
- **[S15]** The Tool-Overuse Illusion: Why Does LLM Prefer External Tools over Internal Knowledge? · https://arxiv.org/html/2604.19749v1 · fetched 2026-06-29T03:16:10Z · sha256 `00e805e36d85` · arxiv
- **[S16]** Toward a Theory of Agents as Tool-Use Decision-Makers · https://arxiv.org/html/2506.00886v1 · fetched 2026-06-29T03:15:56Z · sha256 `8f1d3719adb4` · arxiv
- **[S17]** Toward a Theory of Agents as Tool-Use Decision-Makers · https://arxiv.org/html/2506.00886v1 · fetched 2026-06-29T03:15:56Z · sha256 `8f1d3719adb4` · arxiv
- **[S18]** LLM Agents Already Know When to Call Tools - Even Without Reasoning · https://arxiv.org/html/2605.09252v2 · fetched 2026-06-29T03:15:58Z · sha256 `2705bf6c2d2e` · arxiv
- **[S19]** LLM Agents Already Know When to Call Tools - Even Without Reasoning · https://arxiv.org/html/2605.09252v2 · fetched 2026-06-29T03:15:58Z · sha256 `2705bf6c2d2e` · arxiv
- **[S20]** GitHub - AGI-Edgerunners/LLM-Agents-Papers: A repo lists papers related to LLM based agent · GitHub · https://github.com/AGI-Edgerunners/LLM-Agents-Papers · fetched 2026-06-29T03:16:16Z · sha256 `3a1b1a025d60` · github
- **[S21]** GitHub - AGI-Edgerunners/LLM-Agents-Papers: A repo lists papers related to LLM based agent · GitHub · https://github.com/AGI-Edgerunners/LLM-Agents-Papers · fetched 2026-06-29T03:16:16Z · sha256 `3a1b1a025d60` · github
- **[S22]** LLM Agents Already Know When to Call Tools - Even Without Reasoning · https://arxiv.org/html/2605.09252v2 · fetched 2026-06-29T03:15:58Z · sha256 `2705bf6c2d2e` · arxiv
- **[S23]** LLM Agents Already Know When to Call Tools - Even Without Reasoning · https://arxiv.org/html/2605.09252v2 · fetched 2026-06-29T03:15:58Z · sha256 `2705bf6c2d2e` · arxiv
- **[S24]** LiveBrowseComp: Are Search Agents Searching, or Just Verifying What They Already Know? · https://arxiv.org/html/2605.28721v1 · fetched 2026-06-29T03:16:18Z · sha256 `02191f92a885` · arxiv
- **[S25]** LiveBrowseComp: Are Search Agents Searching, or Just Verifying What They Already Know? · https://arxiv.org/html/2605.28721v1 · fetched 2026-06-29T03:16:18Z · sha256 `02191f92a885` · arxiv
- **[S26]** LiveBrowseComp: Are Search Agents Searching, or Just Verifying What They Already Know? · https://arxiv.org/html/2605.28721v1 · fetched 2026-06-29T03:16:18Z · sha256 `02191f92a885` · arxiv
- **[S27]** SMART: Self-Aware Agent for Tool Overuse Mitigation · https://arxiv.org/html/2502.11435v1 · fetched 2026-06-29T03:16:00Z · sha256 `487dcb6fcfb4` · arxiv
- **[S28]** The Tool-Overuse Illusion: Why Does LLM Prefer External Tools over Internal Knowledge? · https://arxiv.org/html/2604.19749v1 · fetched 2026-06-29T03:16:10Z · sha256 `00e805e36d85` · arxiv
- **[S29]** LLM Agents Already Know When to Call Tools - Even Without Reasoning · https://arxiv.org/html/2605.09252v2 · fetched 2026-06-29T03:15:58Z · sha256 `2705bf6c2d2e` · arxiv
- **[S30]** To Call or Not to Call: A Framework to Assess and Optimize LLM Tool Calling · https://arxiv.org/html/2605.00737v1 · fetched 2026-06-29T03:16:02Z · sha256 `2de53186de69` · arxiv
- **[S31]** Toward a Theory of Agents as Tool-Use Decision-Makers · https://arxiv.org/html/2506.00886v1 · fetched 2026-06-29T03:15:56Z · sha256 `8f1d3719adb4` · arxiv
- **[S32]** The Tool-Overuse Illusion: Why Does LLM Prefer External Tools over Internal Knowledge? · https://arxiv.org/html/2604.19749v1 · fetched 2026-06-29T03:16:10Z · sha256 `00e805e36d85` · arxiv
- **[S33]** SMART: Self-Aware Agent for Tool Overuse Mitigation · https://arxiv.org/html/2502.11435v1 · fetched 2026-06-29T03:16:00Z · sha256 `487dcb6fcfb4` · arxiv
- **[S34]** LLM Agents Already Know When to Call Tools - Even Without Reasoning · https://arxiv.org/html/2605.09252v2 · fetched 2026-06-29T03:15:58Z · sha256 `2705bf6c2d2e` · arxiv
- **[S35]** LiveBrowseComp: Are Search Agents Searching, or Just Verifying What They Already Know? · https://arxiv.org/html/2605.28721v1 · fetched 2026-06-29T03:16:18Z · sha256 `02191f92a885` · arxiv
- **[S36]** LiveBrowseComp: Are Search Agents Searching, or Just Verifying What They Already Know? · https://arxiv.org/html/2605.28721v1 · fetched 2026-06-29T03:16:18Z · sha256 `02191f92a885` · arxiv
- **[S37]** LLM Agents Already Know When to Call Tools - Even Without Reasoning · https://arxiv.org/html/2605.09252v2 · fetched 2026-06-29T03:15:58Z · sha256 `2705bf6c2d2e` · arxiv
- **[S38]** LLM Agents Already Know When to Call Tools - Even Without Reasoning · https://arxiv.org/html/2605.09252v2 · fetched 2026-06-29T03:15:58Z · sha256 `2705bf6c2d2e` · arxiv
- **[S39]** To Call or Not to Call: A Framework to Assess and Optimize LLM Tool Calling · https://arxiv.org/html/2605.00737v1 · fetched 2026-06-29T03:16:02Z · sha256 `2de53186de69` · arxiv
- **[S40]** LLM Agents Already Know When to Call Tools - Even Without Reasoning · https://arxiv.org/html/2605.09252v2 · fetched 2026-06-29T03:15:58Z · sha256 `2705bf6c2d2e` · arxiv
