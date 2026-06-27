"""Provider-agnostic model interface + an offline stub.

The whole point of this thin seam is constraint compliance: conditions A-E call
a model only through `Model.answer(...)`, so the suite runs against any provider
*or* offline against `StubModel`. No provider SDK is imported anywhere in the
package. A real provider would subclass `Model` (sketch below) and parse its
completion into the checker's expected answer form.

    class AnthropicModel(Model):
        def __init__(self, client, model="claude-opus-4-8"): ...
        def answer(self, task, *, cot=False):
            prompt = task.prompt + ("\\nThink step by step." if cot else "")
            resp = self.client.messages.create(model=self.model, ...)
            return ModelResponse(answer=parse(resp, task.checker),
                                 text=resp.text,
                                 input_tokens=resp.usage.input_tokens,
                                 output_tokens=resp.usage.output_tokens)

`StubModel` is the mock: it stands in for a base LLM and is deliberately
task-aware so the harness can be exercised offline. Its competence model:
  * genuinely-linguistic tasks (`language` in gold): answered correctly, except
    that *hard* ones (difficulty >= 2, e.g. theory-of-mind) need CoT;
  * computational tasks: a language attempt flubs (returns a wrong answer),
    because text continuation is the wrong substrate.
These are illustrative stub behaviours, not measured model performance.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any, Callable, Optional, Protocol, Tuple, runtime_checkable

from .references import gold
from .schema import Task


@dataclass
class ModelResponse:
    answer: Any
    text: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


@runtime_checkable
class Model(Protocol):
    """A model answers a task linguistically. `cot` requests a reasoning trace."""

    name: str

    def answer(self, task: Task, *, cot: bool = False) -> ModelResponse: ...


def estimate_tokens(text: str) -> int:
    """Deterministic token estimate (~0.75 words/token), no tokenizer dependency."""
    return max(1, math.ceil(len(text.split()) * 1.3))


class StubModel:
    """Deterministic, offline stand-in for a base LLM (see module docstring)."""

    name = "stub"

    def answer(self, task: Task, *, cot: bool = False) -> ModelResponse:
        is_linguistic = "language" in task.gold_substrate
        if is_linguistic and (task.difficulty < 2 or cot):
            ans = gold.gold_answer(task)
        else:
            # computational task answered in language, or a hard linguistic task
            # without the reasoning trace it needs -> a flubbed answer.
            ans = gold.wrong_answer(task)

        in_tok = estimate_tokens(task.prompt)
        # CoT spends more output tokens on the reasoning trace.
        out_tok = 40 + (160 if cot else 0)
        return ModelResponse(
            answer=ans,
            text=f"[stub answer cot={cot}]",
            input_tokens=in_tok,
            output_tokens=out_tok,
        )


# --------------------------------------------------------------------------- #
# Plugging in a real provider
# --------------------------------------------------------------------------- #
def parse_answer(task: Task, text: str) -> Any:
    """Best-effort extraction of a checker-shaped answer from free model text.

    A real adapter should instruct the model to end with a line like
    ``Answer: <x>``; if such a line is present we parse from it, otherwise we
    fall back to scanning the whole completion. This is deliberately simple --
    answer formatting is a provider/prompt concern, not a scoring concern.
    """
    m = re.search(r"answer\s*[:=]\s*(.+)", text, flags=re.IGNORECASE | re.DOTALL)
    segment = m.group(1) if m else text
    ctype = task.checker["type"]

    if ctype == "exact_label":
        low = segment.lower()
        for label in task.checker.get("labels", []):
            if str(label).lower() in low:
                return label
        return segment.strip().split()[0].strip(".,!?\"'") if segment.strip() else ""
    if ctype == "numeric_exact":
        m2 = re.search(r"-?\d+", segment.replace(",", ""))
        return int(m2.group()) if m2 else None
    if ctype == "numeric_tol":
        m2 = re.search(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", segment)
        return float(m2.group()) if m2 else None
    if ctype in ("sequence_valid", "grid_match"):
        start, end = segment.find("["), segment.rfind("]")
        if start == -1 or end == -1 or end < start:
            return None
        try:
            return json.loads(segment[start : end + 1])
        except (ValueError, TypeError):
            return None
    return None


# A completion fn: (prompt, cot) -> (text, input_tokens, output_tokens).
CompleteFn = Callable[[str, bool], Tuple[str, int, int]]


class CallableModel:
    """Adapter that turns any completion callable into a `Model`.

    This is how a real provider plugs in without the package importing its SDK::

        def complete(prompt, cot):
            r = client.messages.create(model="claude-opus-4-8",
                                       messages=[{"role": "user", "content": prompt}])
            return r.content[0].text, r.usage.input_tokens, r.usage.output_tokens

        model = CallableModel(complete, name="claude-opus-4-8")

    Answers are extracted with `parse_answer` by default; pass `parser=` to
    override for a provider that returns structured output.
    """

    def __init__(
        self,
        complete: CompleteFn,
        *,
        name: str = "callable",
        parser: Callable[[Task, str], Any] = parse_answer,
    ) -> None:
        self._complete = complete
        self.name = name
        self._parser = parser

    def answer(self, task: Task, *, cot: bool = False) -> ModelResponse:
        instruction = (
            "\n\nThink step by step, then end with a line: Answer: <answer>"
            if cot
            else "\n\nEnd with a line: Answer: <answer>"
        )
        text, in_tok, out_tok = self._complete(task.prompt + instruction, cot)
        return ModelResponse(
            answer=self._parser(task, text),
            text=text,
            input_tokens=in_tok,
            output_tokens=out_tok,
        )
