"""The provider seam (contract §2): the stub emits declarations; a real model
plugs in via CallableModel and must emit a parseable declaration or fail loudly."""

import json

import pytest

from conftest import TASKS_V0
from substrate_bench.checkers import run_checker
from substrate_bench.model import (
    CallableModel,
    Model,
    RouteDeclarationError,
    StubModel,
    parse_declaration,
)
from substrate_bench.schema import load_tasks

TASKS = {t.id: t for t in load_tasks(TASKS_V0)}


# --- StubModel emits a declaration ---------------------------------------- #
def test_stub_chooses_and_emits_declaration():
    m = StubModel()
    resp = m.solve(TASKS["sim-001"])  # no forced strategy -> emits
    assert resp.declaration.strategy == "simulation"
    assert resp.declaration.executes_code is True
    assert resp.declaration.rationale  # non-empty


def test_stub_honours_forced_declaration():
    m = StubModel()
    resp = m.solve(TASKS["lang-001"], force_strategy="exact_computation", force_executes_code=True)
    assert resp.declaration.strategy == "exact_computation"
    assert resp.code_executed is True


# --- parse_declaration: success + loud failure ---------------------------- #
def test_parse_declaration_ok():
    t = TASKS["meta-001"]
    text = '{"strategy": "exact_computation", "executes_code": true, "rationale": "count", "answer": 15}'
    decl, answer = parse_declaration(t, text)
    assert decl.strategy == "exact_computation" and decl.executes_code is True
    assert answer == 15


def test_parse_declaration_missing_key_raises():
    t = TASKS["meta-001"]
    with pytest.raises(RouteDeclarationError):
        parse_declaration(t, '{"strategy": "exact_computation", "executes_code": true}')  # no answer


def test_parse_declaration_bad_strategy_raises():
    t = TASKS["meta-001"]
    with pytest.raises(RouteDeclarationError):
        parse_declaration(t, '{"strategy": "code", "executes_code": true, "answer": 15}')


def test_parse_declaration_no_json_raises():
    t = TASKS["meta-001"]
    with pytest.raises(RouteDeclarationError):
        parse_declaration(t, "I think the answer is 15.")


def test_parse_declaration_non_bool_executes_code_raises():
    t = TASKS["meta-001"]
    with pytest.raises(RouteDeclarationError):
        parse_declaration(t, '{"strategy": "exact_computation", "executes_code": "yes", "answer": 15}')


# --- CallableModel end-to-end (non-stub, offline) ------------------------- #
def _emit(decl_by_key):
    """Fake provider that emits a JSON declaration based on a prompt substring."""

    def complete(prompt, cot):
        for key, obj in decl_by_key.items():
            if key in prompt:
                return json.dumps(obj), 60, 30
        return json.dumps({"strategy": "language", "executes_code": False,
                           "rationale": "fallback", "answer": "unknown"}), 60, 10

    return complete


def test_callable_model_satisfies_protocol_and_emits():
    canned = {
        "projectile": {"strategy": "simulation", "executes_code": True,
                       "rationale": "drag, no closed form", "answer": 99.32},
    }
    model = CallableModel(_emit(canned), name="oracle")
    assert isinstance(model, Model)
    resp = model.solve(TASKS["sim-001"])
    assert resp.declaration.strategy == "simulation"
    assert run_checker(TASKS["sim-001"], resp.answer)


def test_callable_model_observed_code_executed_drives_audit_input():
    # 4-tuple: the harness reports code did NOT actually run despite the claim.
    def complete(prompt, cot):
        obj = {"strategy": "exact_computation", "executes_code": True,
               "rationale": "x", "answer": 15}
        return json.dumps(obj), 60, 30, False  # observed code_executed=False

    model = CallableModel(complete, name="liar")
    resp = model.solve(TASKS["meta-001"])
    assert resp.declaration.executes_code is True
    assert resp.code_executed is False  # the inconsistency the audit will catch


def test_callable_model_malformed_declaration_fails_loudly():
    def complete(prompt, cot):
        return "no json here, sorry", 10, 5

    model = CallableModel(complete, name="bad")
    with pytest.raises(RouteDeclarationError):
        model.solve(TASKS["sim-001"])
