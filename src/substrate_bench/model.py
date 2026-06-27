"""Provider-agnostic model interface + an offline stub (contract v0.1 §2).

A solver must emit a structured route declaration {strategy, executes_code,
rationale} before its answer; we never infer the substrate from tool calls.
Conditions call a model only through `Model.solve(...)`, so the suite runs
against any provider OR offline against `StubModel`. No provider SDK is imported.

`StubModel` keeps the v0 "strategy = task category" shortcut as an offline
fixture (valid per §8). `CallableModel` adapts a real provider and parses a real
emitted declaration, failing loudly on a missing/malformed one.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any, Callable, Optional, Protocol, Tuple, runtime_checkable

from .references import gold
from .schema import RouteDeclaration, Task
from .substrates import (
    LINGUISTIC_STRATEGIES,
    STRATEGIES,
    default_executes_code,
    route,
)


class RouteDeclarationError(ValueError):
    """A solver failed to emit a well-formed route declaration (contract §2)."""


@dataclass
class SolverResponse:
    """A model's full output for one task: a declaration + an answer + the
    observed execution medium (did code actually run)."""

    declaration: RouteDeclaration
    answer: Any
    code_executed: bool = False
    input_tokens: int = 0
    output_tokens: int = 0
    text: str = ""


@runtime_checkable
class Model(Protocol):
    name: str

    def solve(
        self,
        task: Task,
        *,
        force_strategy: Optional[str] = None,
        force_executes_code: Optional[bool] = None,
        cot: bool = False,
    ) -> SolverResponse:
        """Solve a task.

        `force_strategy=None` -> the solver *chooses* and emits its strategy
        (conditions D/E). A concrete `force_strategy` pins the declaration
        (conditions A/B/C). `force_executes_code` pins the medium; if None it
        defaults from the strategy.
        """
        ...


def estimate_tokens(text: str) -> int:
    """Deterministic token estimate (~0.75 words/token), no tokenizer dependency."""
    return max(1, math.ceil(len(text.split()) * 1.3))


def _is_linguistic_task(task: Task) -> bool:
    return bool(set(task.gold_substrate) & {"language", "social"})


class StubModel:
    """Deterministic, offline stand-in for a base LLM.

    Competence model (illustrative, not measured performance):
      * genuinely linguistic/social tasks -> answered correctly, except *hard*
        ones (difficulty >= 2) which need CoT;
      * a computational strategy answers correctly iff it is in the task's gold
        strategy set; otherwise it flubs (wrong substrate -> wrong answer).
    The stub honestly executes code exactly when it declares it, so its
    consistency audit always passes.
    """

    name = "stub"

    def solve(
        self,
        task: Task,
        *,
        force_strategy: Optional[str] = None,
        force_executes_code: Optional[bool] = None,
        cot: bool = False,
    ) -> SolverResponse:
        emitting = force_strategy is None
        strategy = force_strategy if force_strategy is not None else route(task.category)
        executes_code = (
            force_executes_code
            if force_executes_code is not None
            else default_executes_code(strategy)
        )

        if strategy in LINGUISTIC_STRATEGIES:
            if _is_linguistic_task(task) and (task.difficulty < 2 or cot):
                answer = gold.gold_answer(task)
            else:
                answer = gold.wrong_answer(task)
        else:  # computational strategy
            answer = gold.gold_answer(task) if strategy in task.gold_substrate else gold.wrong_answer(task)

        # The stub does exactly what it declares.
        code_executed = executes_code

        in_tok = estimate_tokens(task.prompt)
        out_tok = 40 + (160 if cot else 0) + (30 if emitting else 0)
        rationale = (
            f"category={task.category} -> strategy={strategy}; "
            f"{'runs code' if executes_code else 'answers in prose'}"
        )
        return SolverResponse(
            declaration=RouteDeclaration(strategy, executes_code, rationale),
            answer=answer,
            code_executed=code_executed,
            input_tokens=in_tok,
            output_tokens=out_tok,
            text=f"[stub strategy={strategy} cot={cot}]",
        )


# --------------------------------------------------------------------------- #
# Plugging in a real provider
# --------------------------------------------------------------------------- #
def parse_answer(task: Task, text: str) -> Any:
    """Best-effort extraction of a checker-shaped answer from free model text.

    Used for the forced-strategy conditions (A/B/C), where the model returns a
    prose answer rather than a JSON declaration. Instruct the model to end with
    ``Answer: <x>``; we parse from there if present.
    """
    m = re.search(r"answer\s*[:=]\s*(.+)", text, flags=re.IGNORECASE | re.DOTALL)
    segment = m.group(1) if m else text
    return _coerce_answer(task, segment)


def _coerce_answer(task: Task, segment: Any) -> Any:
    ctype = task.checker["type"]
    if ctype in ("sequence_valid", "grid_match"):
        if isinstance(segment, (list, tuple)):
            return segment
        text = str(segment)
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end == -1 or end < start:
            return None
        try:
            return json.loads(text[start : end + 1])
        except (ValueError, TypeError):
            return None
    if ctype == "exact_label":
        if not isinstance(segment, str):
            return segment
        low = segment.lower()
        for label in task.checker.get("labels", []):
            if str(label).lower() in low:
                return label
        return segment.strip().split()[0].strip(".,!?\"'") if segment.strip() else ""
    if ctype == "numeric_exact":
        if isinstance(segment, int) and not isinstance(segment, bool):
            return segment
        m2 = re.search(r"-?\d+", str(segment).replace(",", ""))
        return int(m2.group()) if m2 else None
    if ctype == "numeric_tol":
        if isinstance(segment, (int, float)) and not isinstance(segment, bool):
            return float(segment)
        m2 = re.search(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", str(segment))
        return float(m2.group()) if m2 else None
    return None


def parse_declaration(task: Task, text: str) -> Tuple[RouteDeclaration, Any]:
    """Parse a model's JSON route declaration {strategy, executes_code, rationale,
    answer}. Raises RouteDeclarationError on anything missing or malformed."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise RouteDeclarationError("no JSON object found in model output")
    try:
        obj = json.loads(text[start : end + 1])
    except (ValueError, TypeError) as exc:
        raise RouteDeclarationError(f"declaration is not valid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise RouteDeclarationError("declaration JSON is not an object")

    for key in ("strategy", "executes_code", "answer"):
        if key not in obj:
            raise RouteDeclarationError(f"declaration missing required key {key!r}")
    if not isinstance(obj["strategy"], str) or obj["strategy"] not in STRATEGIES:
        raise RouteDeclarationError(f"declaration strategy invalid: {obj.get('strategy')!r}")
    if not isinstance(obj["executes_code"], bool):
        raise RouteDeclarationError("declaration executes_code must be a boolean")

    decl = RouteDeclaration(
        strategy=obj["strategy"],
        executes_code=obj["executes_code"],
        rationale=str(obj.get("rationale", "")),
    )
    answer = _coerce_answer(task, obj["answer"])
    return decl, answer


# A completion fn: (prompt, cot) -> (text, in_tok, out_tok) or
# (text, in_tok, out_tok, code_executed).
CompleteFn = Callable[..., Tuple]


class CallableModel:
    """Adapter that turns any completion callable into a `Model`.

        def complete(prompt, cot):
            r = client.messages.create(model="claude-opus-4-8",
                                       messages=[{"role": "user", "content": prompt}])
            return r.content[0].text, r.usage.input_tokens, r.usage.output_tokens

        model = CallableModel(complete, name="claude-opus-4-8")

    For D/E (no forced strategy) the model is asked to emit a JSON declaration,
    parsed by `parse_declaration` (loud failure on malformed output). For A/B/C
    the declaration is fixed by the condition and only the answer is parsed.

    The completion callable may optionally return a 4th element -- the observed
    `code_executed` flag from the harness's tool runtime -- which the consistency
    audit checks against the declaration. If omitted it mirrors the declaration.
    """

    def __init__(self, complete: CompleteFn, *, name: str = "callable") -> None:
        self._complete = complete
        self.name = name

    def _call(self, prompt: str, cot: bool) -> Tuple[str, int, int, Optional[bool]]:
        out = self._complete(prompt, cot)
        if len(out) == 4:
            text, in_tok, out_tok, code_executed = out
            return text, in_tok, out_tok, bool(code_executed)
        text, in_tok, out_tok = out
        return text, in_tok, out_tok, None

    def solve(
        self,
        task: Task,
        *,
        force_strategy: Optional[str] = None,
        force_executes_code: Optional[bool] = None,
        cot: bool = False,
    ) -> SolverResponse:
        if force_strategy is None:
            instruction = (
                "\n\nFirst decide which cognitive strategy this task requires "
                f"(one of: {', '.join(STRATEGIES)}). Then respond with ONLY a JSON "
                'object: {"strategy": ..., "executes_code": true|false, '
                '"rationale": ..., "answer": <final answer>}.'
            )
            text, in_tok, out_tok, observed = self._call(task.prompt + instruction, cot)
            decl, answer = parse_declaration(task, text)
            code_executed = observed if observed is not None else decl.executes_code
            return SolverResponse(decl, answer, code_executed, in_tok, out_tok, text)

        # Forced declaration (A/B/C): only the answer comes from the model.
        executes_code = (
            force_executes_code
            if force_executes_code is not None
            else default_executes_code(force_strategy)
        )
        instruction = (
            "\n\nThink step by step, then end with a line: Answer: <answer>"
            if cot
            else "\n\nEnd with a line: Answer: <answer>"
        )
        text, in_tok, out_tok, observed = self._call(task.prompt + instruction, cot)
        decl = RouteDeclaration(force_strategy, executes_code, rationale="(fixed by condition)")
        code_executed = observed if observed is not None else executes_code
        return SolverResponse(decl, parse_answer(task, text), code_executed, in_tok, out_tok, text)
