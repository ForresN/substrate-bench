"""Consistency audit of a route declaration vs observed behaviour (contract §3).

v0.1 scope: if a solver declares `executes_code: true`, confirm code actually
ran. The deeper *structural* audit -- e.g. confirm a `search` declaration
actually expanded states rather than emitting a one-liner -- is deferred to
v0.2; the hook is recorded here so the seam exists now.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .schema import RouteDeclaration


@dataclass
class RouteAudit:
    passed: bool
    checks: List[str] = field(default_factory=list)
    detail: str = ""


def audit_consistency(declaration: RouteDeclaration, code_executed: bool) -> RouteAudit:
    """Return whether observed behaviour is consistent with the declaration."""
    checks: List[str] = []
    passed = True

    # v0.1 medium check.
    if declaration.executes_code and not code_executed:
        passed = False
        checks.append("FAIL: executes_code=true but no code ran")
    else:
        checks.append("ok: execution-medium consistent")

    # v0.2 hook (deferred, contract §3) -- structural depth of the declared
    # strategy. Intentionally a no-op in v0.1; present so callers/tests can see
    # the seam and so adding it later does not change the Result shape.
    checks.append("skip: structural-audit deferred to v0.2")

    return RouteAudit(passed=passed, checks=checks, detail="; ".join(checks))
