"""Consistency audit (contract §3): executes_code=true must be backed by code."""

from substrate_bench.audit import audit_consistency
from substrate_bench.schema import RouteDeclaration


def test_consistent_when_code_claimed_and_ran():
    d = RouteDeclaration("exact_computation", executes_code=True, rationale="")
    a = audit_consistency(d, code_executed=True)
    assert a.passed
    assert any("consistent" in c for c in a.checks)


def test_fails_when_code_claimed_but_not_run():
    d = RouteDeclaration("search", executes_code=True, rationale="")
    a = audit_consistency(d, code_executed=False)
    assert not a.passed
    assert any("FAIL" in c for c in a.checks)


def test_consistent_when_no_code_claimed():
    d = RouteDeclaration("language", executes_code=False, rationale="")
    assert audit_consistency(d, code_executed=False).passed
    # claiming no code but code happening is a v0.2 structural concern, not failed in v0.1
    assert audit_consistency(d, code_executed=True).passed


def test_structural_audit_hook_is_recorded_but_deferred():
    d = RouteDeclaration("search", executes_code=True, rationale="")
    a = audit_consistency(d, code_executed=True)
    assert any("structural-audit deferred to v0.2" in c for c in a.checks)
