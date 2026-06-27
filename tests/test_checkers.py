"""Every checker type: a passing case and at least one failing case."""

from substrate_bench.checkers import is_verifiable, run_checker
from substrate_bench.references import search_ref
from substrate_bench.schema import Task


def _task(checker, gold=("exact_computation",), category="exact_computation"):
    return Task("t", category, "p", list(gold), checker, 2, "")


# --- exact_label ----------------------------------------------------------- #
def test_exact_label_pass_and_case_insensitive():
    t = _task({"type": "exact_label", "answer": "positive", "labels": ["positive", "negative"]},
              gold=("language",), category="language")
    assert run_checker(t, "positive")
    assert run_checker(t, "  Positive ")


def test_exact_label_fail_and_nonstring():
    t = _task({"type": "exact_label", "answer": "positive", "labels": ["positive", "negative"]})
    assert not run_checker(t, "negative")
    assert not run_checker(t, 1)


# --- numeric_exact --------------------------------------------------------- #
def test_numeric_exact_pass_fail_and_types():
    t = _task({"type": "numeric_exact", "answer": 15})
    assert run_checker(t, 15)
    assert not run_checker(t, 14)
    assert not run_checker(t, "15")     # string is not a number match
    assert not run_checker(t, True)     # bool must not sneak through as 1


# --- numeric_tol ----------------------------------------------------------- #
def test_numeric_tol_within_and_outside():
    t = _task({"type": "numeric_tol", "reference": 99.32, "tol": 0.5})
    assert run_checker(t, 99.32)
    assert run_checker(t, 99.7)
    assert not run_checker(t, 250.97)   # the vacuum-range mistake
    assert not run_checker(t, "99.32")


# --- sequence_valid: hanoi ------------------------------------------------- #
def _hanoi_checker():
    return {
        "type": "sequence_valid", "problem": "hanoi", "n": 4,
        "source": "A", "target": "C", "aux": "B", "require_optimal": True,
    }


def test_sequence_valid_hanoi_optimal_passes():
    t = _task(_hanoi_checker(), gold=("search",), category="search")
    moves = search_ref.hanoi_solve(4, "A", "C", "B")
    assert run_checker(t, moves)


def test_sequence_valid_hanoi_empty_and_nonoptimal_fail():
    t = _task(_hanoi_checker(), gold=("search",), category="search")
    assert not run_checker(t, [])
    # a legal but non-optimal sequence: pad with a redundant there-and-back move
    moves = search_ref.hanoi_solve(4, "A", "C", "B")
    padded = moves[:1] + [["A", "B"], ["B", "A"]] + moves[1:]
    assert not run_checker(t, padded)


def test_sequence_valid_hanoi_illegal_move_fails():
    t = _task(_hanoi_checker(), gold=("search",), category="search")
    # moving from an empty/again-illegal configuration
    assert not run_checker(t, [["A", "C"], ["A", "C"]])


# --- sequence_valid: gridworld --------------------------------------------- #
def _grid_checker():
    return {
        "type": "sequence_valid", "problem": "gridworld",
        "grid": [".....", ".###.", "...#.", ".#.#.", ".#..."],
        "start": [0, 0], "goal": [4, 4], "require_optimal": True,
    }


def test_sequence_valid_gridworld_shortest_passes_others_fail():
    t = _task(_grid_checker(), gold=("search",), category="search")
    path = search_ref.gridworld_shortest([".....", ".###.", "...#.", ".#.#.", ".#..."], [0, 0], [4, 4])
    assert run_checker(t, path)
    assert not run_checker(t, [])
    assert not run_checker(t, ["U", "U"])  # walks off the grid


def test_sequence_valid_waterjug():
    checker = {"type": "sequence_valid", "problem": "waterjug",
               "cap_a": 5, "cap_b": 3, "target": 4, "require_optimal": True}
    t = _task(checker, gold=("search",), category="search")
    sol = search_ref.waterjug_solve(5, 3, 4)
    assert run_checker(t, sol)
    assert not run_checker(t, [])
    assert not run_checker(t, ["fill A"])  # does not reach target


# --- grid_match ------------------------------------------------------------ #
def test_grid_match_pass_fail_and_nongrid():
    t = _task({"type": "grid_match", "answer": [[2, 1, 9], [5, 4, 3], [8, 7, 6]]},
              gold=("code", "search"), category="hidden_rule")
    assert run_checker(t, [[2, 1, 9], [5, 4, 3], [8, 7, 6]])
    assert run_checker(t, ((2, 1, 9), (5, 4, 3), (8, 7, 6)))  # tuples normalize
    assert not run_checker(t, [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    assert not run_checker(t, "nope")


# --- is_verifiable --------------------------------------------------------- #
def test_is_verifiable():
    comp = _task({"type": "numeric_exact", "answer": 15})
    ling = _task({"type": "exact_label", "answer": "x", "labels": ["x", "y"]},
                 gold=("language",), category="language")
    assert is_verifiable(comp) is True
    assert is_verifiable(ling) is False
