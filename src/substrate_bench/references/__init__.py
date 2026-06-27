"""Trusted, deterministic reference implementations.

These compute gold answers and validate candidate solutions. They are plain
Python and must NEVER call a model -- that invariant is what keeps scoring
seed-stable and the gate falsifiable.
"""

from . import arithmetic, dynamics, gold, rules, search_ref

__all__ = ["arithmetic", "dynamics", "rules", "search_ref", "gold"]
