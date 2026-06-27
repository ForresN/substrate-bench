"""The two-axis ontology (contract v0.1 §1) and the router's category map.

v0 conflated *cognitive strategy* with *execution medium*. v0.1 splits them:

  * **Strategy axis** -- what the task requires; the only axis scored by
    substrate-selection accuracy. `code` is NOT here: it was never a peer of
    `simulation`/`search`, it is the medium they are realised through.
  * **Execution-medium axis** -- the orthogonal `executes_code: true|false` flag,
    carried on the route declaration, not on the task.
"""

from __future__ import annotations

# Strategy axis (the scored axis). `code` deliberately removed vs v0.
STRATEGIES: tuple[str, ...] = (
    "language",           # genuinely linguistic / world-modelling
    "exact_computation",  # exact arithmetic / closed-form / constraint counting
    "simulation",         # continuous dynamics over time
    "search",             # discrete state-space / combinatorial / planning
    "memory",             # reuse of a prior solution (forward-compat, not v0.1)
    "verify",             # checking a candidate against constraints/tests
    "social",             # theory-of-mind / social reasoning
)

# The six strategies the v0.1 task set covers (memory is forward-compat only).
TASK_BEARING_STRATEGIES: tuple[str, ...] = (
    "language",
    "exact_computation",
    "simulation",
    "search",
    "social",
    "verify",
)

# Execution-medium defaults. Strategies realised in prose carry executes_code=false.
LINGUISTIC_STRATEGIES: frozenset[str] = frozenset({"language", "social", "memory"})
# Strategies normally realised by running code.
CODE_BEARING_STRATEGIES: frozenset[str] = frozenset(
    {"exact_computation", "simulation", "search", "verify"}
)


def default_executes_code(strategy: str) -> bool:
    """The medium a competent solver would use for a strategy, by default."""
    return strategy in CODE_BEARING_STRATEGIES


# Back-compat alias (deprecated; prefer STRATEGIES).
SUBSTRATES = STRATEGIES

# Condition D/E router heuristic: task category -> declared strategy. Categories
# that ARE strategy names map to themselves (the stub's offline shortcut, still
# valid per §8). Two deliberate specials:
#   hidden_rule -> search       (rule induction is a hypothesis-space search)
#   meta_cognition -> language  (the trap: prose surface hides exact_computation)
ROUTER_CATEGORY_MAP: dict[str, str] = {
    "language": "language",
    "social": "social",
    "exact_computation": "exact_computation",
    "simulation": "simulation",
    "search": "search",
    "verify": "verify",
    "hidden_rule": "search",
    "meta_cognition": "language",
}


def route(category: str) -> str:
    """Return the strategy the v0.1 router declares for a task category."""
    if category in ROUTER_CATEGORY_MAP:
        return ROUTER_CATEGORY_MAP[category]
    if category in STRATEGIES:
        return category
    return "language"
