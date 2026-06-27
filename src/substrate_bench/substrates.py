"""The fixed substrate taxonomy (spec section 2) and the router's category map."""

from __future__ import annotations

# The fixed set of substrates a solver may route to in v0.
SUBSTRATES: tuple[str, ...] = (
    "language",    # genuinely linguistic / social / world-modelling
    "code",        # exact computation, arithmetic, constraint checking
    "simulation",  # continuous dynamics over time
    "search",      # discrete state-space / combinatorial / planning
    "memory",      # reuse of a previously solved near-identical task (not v0-critical)
    "verify",      # checking a candidate answer against constraints/tests
)

# Substrates that the deterministic references can execute (the "computational"
# ones). `language` is executed by the model; `memory`/`verify` are meta.
COMPUTATIONAL_SUBSTRATES: frozenset[str] = frozenset({"code", "simulation", "search"})

# The condition D/E router's heuristic: map a task category to one substrate.
# `meta_cognition -> language` is deliberate: the prose surface fools the router,
# which is exactly the trap meta-001 exists to expose. Conditions D and E differ
# only in whether a verifier later catches and corrects that mis-route.
ROUTER_CATEGORY_MAP: dict[str, str] = {
    "language": "language",
    "social": "language",
    "exact_computation": "code",
    "simulation": "simulation",
    "search": "search",
    "hidden_rule": "code",
    "meta_cognition": "language",  # the trap
}


def route(category: str) -> str:
    """Return the substrate the v0 router picks for a task category."""
    return ROUTER_CATEGORY_MAP.get(category, "language")
