"""Deterministic author for the v0.1 task growth (contract §7).

Gold provenance:
  * exact_computation / simulation / search / verify  -> gold computed by the
    trusted reference implementations (never a solver).
  * language / social  -> no algorithmic reference exists, so gold is
    human-authored/reviewed here and tagged provenance="human_review".

Run:  python tools/author_tasks.py        (writes tasks/v0/*.json)
This generator is committed so gold provenance is auditable and reproducible.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from substrate_bench.references import dynamics, gold as goldmod, search_ref, verify_ref  # noqa: E402
from substrate_bench.references import arithmetic  # noqa: E402

OUT = ROOT / "tasks" / "smoke"
NUMERIC = goldmod._NUMERIC_IMPLS


def _round(x: float) -> float:
    return round(float(x), 6)


def num_exact(tid, category, prompt, impl, params, difficulty, gold, rationale):
    answer = NUMERIC[impl](params)
    return {
        "id": tid, "category": category, "prompt": prompt, "gold_substrate": gold,
        "checker": {"type": "numeric_exact", "reference_impl": impl, "params": params, "answer": answer},
        "difficulty": difficulty, "rationale": rationale, "provenance": "reference",
    }


def num_tol(tid, category, prompt, impl, params, tol, difficulty, gold, rationale):
    ref = _round(NUMERIC[impl](params))
    return {
        "id": tid, "category": category, "prompt": prompt, "gold_substrate": gold,
        "checker": {"type": "numeric_tol", "reference_impl": impl, "params": params, "reference": ref, "tol": tol},
        "difficulty": difficulty, "rationale": rationale, "provenance": "reference",
    }


def hanoi(tid, prompt, n, difficulty, rationale):
    moves = search_ref.hanoi_solve(n, "A", "C", "B")
    return {
        "id": tid, "category": "search", "prompt": prompt, "gold_substrate": ["search"],
        "checker": {"type": "sequence_valid", "problem": "hanoi", "n": n, "source": "A",
                    "target": "C", "aux": "B", "require_optimal": True, "optimal_length": len(moves)},
        "difficulty": difficulty, "rationale": rationale, "provenance": "reference",
    }


def grid(tid, prompt, g, start, goalc, difficulty, rationale):
    path = search_ref.gridworld_shortest(g, start, goalc)
    return {
        "id": tid, "category": "search", "prompt": prompt, "gold_substrate": ["search"],
        "checker": {"type": "sequence_valid", "problem": "gridworld", "grid": g, "start": start,
                    "goal": goalc, "require_optimal": True, "optimal_length": len(path)},
        "difficulty": difficulty, "rationale": rationale, "provenance": "reference",
    }


def jug(tid, prompt, cap_a, cap_b, target, difficulty, rationale):
    sol = search_ref.waterjug_solve(cap_a, cap_b, target)
    return {
        "id": tid, "category": "search", "prompt": prompt, "gold_substrate": ["search"],
        "checker": {"type": "sequence_valid", "problem": "waterjug", "cap_a": cap_a, "cap_b": cap_b,
                    "target": target, "require_optimal": True, "optimal_length": len(sol)},
        "difficulty": difficulty, "rationale": rationale, "provenance": "reference",
    }


def verify(tid, prompt, impl, candidate, labels, difficulty, rationale):
    checker = {"type": "exact_label", "labels": labels, "verify_impl": impl, "candidate": candidate}
    checker["answer"] = verify_ref.label_for(checker)
    return {
        "id": tid, "category": "verify", "prompt": prompt, "gold_substrate": ["verify"],
        "checker": checker, "difficulty": difficulty, "rationale": rationale, "provenance": "reference",
    }


def label(tid, category, prompt, answer, labels, difficulty, gold, rationale):
    assert answer in labels
    return {
        "id": tid, "category": category, "prompt": prompt, "gold_substrate": gold,
        "checker": {"type": "exact_label", "answer": answer, "labels": labels},
        "difficulty": difficulty, "rationale": rationale, "provenance": "human_review",
    }


# --------------------------------------------------------------------------- #
# exact_computation
# --------------------------------------------------------------------------- #
TASKS = []
EC = "exact_computation"
TASKS += [
    num_exact("exact-101", EC, "What is the greatest common divisor of 1071 and 462?",
              "gcd", {"a": 1071, "b": 462}, 1, [EC], "GCD by exact computation."),
    num_exact("exact-102", EC,
              "A display stacks cans in rows: 3 cans in the top row, 5 in the next, 7 in the next, "
              "and so on (each row holds 2 more than the row above), for 12 rows total. How many cans are there?",
              "arithmetic_series_sum", {"a": 3, "d": 2, "n": 12}, 1, [EC], "Arithmetic-series sum."),
    num_exact("exact-103", EC, "What is 7 raised to the power 222, modulo 13?",
              "modexp", {"base": 7, "exp": 222, "mod": 13}, 2, [EC], "Modular exponentiation; text continuation flubs."),
    num_exact("exact-104", EC, "How many distinct 5-card hands can be dealt from a standard 52-card deck?",
              "combinations", {"n": 52, "k": 5}, 2, [EC], "Binomial coefficient C(52,5)."),
    num_exact("exact-105", EC, "What are the last three digits of 2 raised to the power 1000? "
              "(That is, 2^1000 modulo 1000.)",
              "modexp", {"base": 2, "exp": 1000, "mod": 1000}, 3, [EC],
              "Large modular exponentiation; far beyond reliable next-token arithmetic."),
]

# --------------------------------------------------------------------------- #
# simulation
# --------------------------------------------------------------------------- #
SIM, SIMEC = ["simulation"], ["simulation", "exact_computation"]
TASKS += [
    num_tol("sim-101", "simulation",
            "A radioactive sample of 80 mg has a half-life of 5 hours. How many milligrams remain after 12 hours?",
            "radioactive_decay", {"n0": 80.0, "half_life": 5.0, "t": 12.0}, 0.05, 1, SIMEC,
            "Exponential decay; closed form exists so exact_computation also valid."),
    num_tol("sim-102", "simulation",
            "A cup of tea at 95 C sits in a 22 C room and cools per Newton's law with k = 0.08 per minute. "
            "What is its temperature (C) after 15 minutes?",
            "newton_cooling", {"t_env": 22.0, "t0": 95.0, "k": 0.08, "t": 15.0}, 0.05, 1, SIMEC,
            "Newton cooling; closed form exists."),
    num_tol("sim-103", "simulation",
            "A capacitor charges through a 1000 ohm resistor and 0.002 F capacitance from a 9 V source. "
            "What is the capacitor voltage (V) after 3 seconds?",
            "rc_charge", {"v": 9.0, "r": 1000.0, "c": 0.002, "t": 3.0}, 0.02, 2, SIMEC,
            "RC charging; exponential approach, closed form exists."),
    num_tol("sim-104", "simulation",
            "A projectile is launched at 70 m/s at 35 degrees with quadratic drag a_drag = c*|v|*v, "
            "c = 0.008 per metre, g = 9.81. What horizontal range (m) does it reach before landing?",
            "projectile_drag", {"v0": 70.0, "angle_deg": 35.0, "drag": 0.008, "g": 9.81, "dt": 0.0005}, 0.5, 3, SIM,
            "Quadratic drag: no closed form, simulation required."),
    num_tol("sim-105", "simulation",
            "A projectile is launched at 60 m/s at 55 degrees with quadratic drag a_drag = c*|v|*v, "
            "c = 0.012 per metre, g = 9.81. What horizontal range (m) does it reach before landing?",
            "projectile_drag", {"v0": 60.0, "angle_deg": 55.0, "drag": 0.012, "g": 9.81, "dt": 0.0005}, 0.5, 3, SIM,
            "Steeper drag trajectory; no closed form."),
    num_tol("sim-106", "simulation",
            "A projectile is launched at 55 m/s at 45 degrees into an 8 m/s horizontal headwind, with quadratic "
            "drag relative to the air a_drag = c*|v_rel|*v_rel, c = 0.01 per metre, g = 9.81. What horizontal "
            "range (m) does it reach before landing?",
            "projectile_drag", {"v0": 55.0, "angle_deg": 45.0, "drag": 0.01, "g": 9.81, "dt": 0.0005, "wind": -8.0}, 0.5, 3, SIM,
            "Drag relative to moving air; firmly a simulation."),
]

# --------------------------------------------------------------------------- #
# search
# --------------------------------------------------------------------------- #
TASKS += [
    grid("search-101", "On the 3x3 grid below ('.' free, '#' wall), give the shortest path of U/D/L/R moves "
         "from (row 0, col 0) to (row 2, col 2).\n\n...\n.#.\n...",
         ["...", ".#.", "..."], [0, 0], [2, 2], 1, "Small shortest-path; optimality checked by BFS."),
    hanoi("search-102", "Tower of Hanoi with 3 disks on pegs A, B, C (all start on A). Move them all to C, one top "
          "disk at a time, never a larger disk on a smaller one. Give the shortest move sequence as [from, to] pairs.",
          3, 1, "Hanoi n=3: discrete planning."),
    jug("search-103", "You have a 5-litre jug and a 3-litre jug, both empty, and a tap. Allowed actions: 'fill A', "
        "'fill B', 'empty A', 'empty B', 'pour A->B', 'pour B->A'. Give the shortest action sequence that leaves "
        "exactly 4 litres in one of the jugs.", 5, 3, 4, 2,
        "Water-jug planning; BFS over jug states, optimality checked."),
    hanoi("search-104", "Tower of Hanoi with 5 disks on pegs A, B, C (all start on A). Move them all to C, one top "
          "disk at a time, never a larger disk on a smaller one. Give the shortest move sequence as [from, to] pairs.",
          5, 3, "Hanoi n=5: 31 moves, where text continuation degrades."),
    grid("search-105", "On the 6x6 grid below ('.' free, '#' wall), give the shortest path of U/D/L/R moves from "
         "(row 0, col 0) to (row 5, col 5).\n\n......\n.####.\n.####.\n.####.\n.####.\n......",
         ["......", ".####.", ".####.", ".####.", ".####.", "......"], [0, 0], [5, 5], 3,
         "Larger maze; greedy text reasoning tends to miss the shortest route."),
]

# --------------------------------------------------------------------------- #
# verify
# --------------------------------------------------------------------------- #
VL = ["valid", "invalid"]
TF = ["true", "false"]
_h3 = search_ref.hanoi_solve(3, "A", "C", "B")
TASKS += [
    verify("verify-101",
           "Below is a proposed complete solution to Tower of Hanoi with 3 disks (move all from A to C, one top "
           f"disk at a time, never larger on smaller). Is it valid? moves = {json.dumps([list(m) for m in _h3])}\n"
           "Answer 'valid' or 'invalid'.",
           "hanoi", {"n": 3, "moves": [list(m) for m in _h3]}, VL, 1, "Verify a candidate Hanoi solution."),
    verify("verify-102",
           "Is the following bracket string balanced (every opener correctly matched and nested)? \"([)]\"  "
           "Answer 'valid' or 'invalid'.",
           "balanced", {"s": "([)]"}, VL, 1, "Verify bracket balance."),
    verify("verify-103",
           "On the grid below ('.' free, '#' wall), does the move sequence ['D','D','R','R'] go from (0,0) to "
           "(2,2) without leaving the grid or hitting a wall?\n\n...\n.#.\n...\nAnswer 'valid' or 'invalid'.",
           "gridworld", {"grid": ["...", ".#.", "..."], "start": [0, 0], "goal": [2, 2],
                         "moves": ["D", "D", "R", "R"], "require_optimal": False}, VL, 2,
           "Verify a candidate path reaches the goal legally."),
    verify("verify-104", "Claim: 437 is a prime number. Is the claim true? Answer 'true' or 'false'.",
           "prime", {"n": 437}, TF, 2, "Verify a primality claim (437 = 19 x 23)."),
    verify("verify-105",
           "Three meetings A, B, C must take distinct slots from {9,10,11}, with A earlier than B and C not at 9. "
           "Proposed schedule: A=9, B=10, C=11. Does it satisfy all constraints? Answer 'valid' or 'invalid'.",
           "schedule", {"constraints": {"meetings": ["A", "B", "C"], "slots": [9, 10, 11],
                                        "before": [["A", "B"]], "not_in": {"C": [9]}},
                        "assignment": {"A": 9, "B": 10, "C": 11}}, VL, 2, "Verify a schedule against constraints."),
    verify("verify-106",
           "On a 6x6 chessboard, queens are placed one per row at columns [0,2,4,1,3,5] (row 0 has a queen in "
           "column 0, etc.). Is this a valid solution where no two queens attack each other? Answer 'valid' or 'invalid'.",
           "nqueens", {"positions": [0, 2, 4, 1, 3, 5], "n": 6}, VL, 3, "Verify an n-queens placement."),
    verify("verify-107",
           "Is the following 4x4 grid a valid Latin square (each row and each column contains 1,2,3,4 exactly "
           "once)? [[1,2,3,4],[2,1,4,3],[3,4,1,2],[4,3,2,1]]  Answer 'valid' or 'invalid'.",
           "latin", {"grid": [[1, 2, 3, 4], [2, 1, 4, 3], [3, 4, 1, 2], [4, 3, 2, 1]]}, VL, 3,
           "Verify a Latin-square candidate."),
]

# --------------------------------------------------------------------------- #
# language (human_review gold)
# --------------------------------------------------------------------------- #
LANG = ["language"]
SENT = ["positive", "negative", "neutral"]
TASKS += [
    label("lang-101", "language",
          "Classify the sentiment of this review as positive, negative, or neutral:\n"
          "\"The screen cracked in the first week and support ignored three emails.\"",
          "negative", SENT, 1, LANG, "Plain negative sentiment."),
    label("lang-102", "language",
          "Classify the sentiment of this message as positive, negative, or neutral:\n"
          "\"Oh, fantastic — another two-hour delay. Exactly how I wanted to spend my evening.\"",
          "negative", SENT, 2, LANG, "Sarcasm: positive words, negative intent."),
    label("lang-103", "language",
          "Premise: \"All of the cookies were eaten by the children.\" Hypothesis: \"Some cookies are left.\" "
          "Does the premise entail the hypothesis, contradict it, or is it neutral? "
          "Answer entailment, contradiction, or neutral.",
          "contradiction", ["entailment", "contradiction", "neutral"], 2, LANG, "Natural-language inference."),
    label("lang-104", "language",
          "Does the word 'bank' mean the same thing in these two sentences? "
          "(1) \"She sat on the river bank.\" (2) \"He deposited his paycheck at the bank.\" "
          "Answer same or different.",
          "different", ["same", "different"], 2, LANG, "Word-in-context sense disambiguation."),
    label("lang-105", "language",
          "Classify the sentiment of this review as positive, negative, or neutral:\n"
          "\"It's not that the food was bad, exactly — it's that I can't think of a single thing I'd order again.\"",
          "negative", SENT, 3, LANG, "Negation + faint-praise; surface words look mild."),
    label("lang-106", "language",
          "Anna asks, \"Did everyone pass the exam?\" Ben replies, \"Some of them did.\" What does Ben most likely "
          "implicate? (a) everyone passed (b) not everyone passed (c) nobody passed. Answer a, b, or c.",
          "b", ["a", "b", "c"], 3, LANG, "Scalar implicature ('some' implies 'not all')."),
]

# --------------------------------------------------------------------------- #
# social (human_review gold)
# --------------------------------------------------------------------------- #
SOC = ["social"]
TASKS += [
    label("social-101", "social",
          "Tom hides his keys in the drawer and leaves the house. While he is gone, his sister moves the keys to "
          "the cupboard. When Tom comes back, where will he look FIRST for his keys? Answer drawer or cupboard.",
          "drawer", ["drawer", "cupboard"], 1, SOC, "First-order false belief."),
    label("social-102", "social",
          "Maya spent weeks making a gift. Her friend opened it, smiled widely, and gave her a big hug. "
          "How does Maya most likely feel? Answer happy, sad, or angry.",
          "happy", ["happy", "sad", "angry"], 1, SOC, "Emotion attribution from social cues."),
    label("social-103", "social",
          "Sam was looking forward to a quiet evening alone. His roommate just invited ten friends over for the "
          "night. Is Sam most likely pleased or annoyed? Answer pleased or annoyed.",
          "annoyed", ["pleased", "annoyed"], 1, SOC, "Desire-based emotion prediction."),
    label("social-104", "social",
          "Anna puts her chocolate in the blue box and leaves the room. Ben moves it to the green box. Ben does "
          "not know that Anna secretly watched through the window and saw him move it. When Anna returns, which "
          "box does BEN think Anna will look in first? Answer blue or green.",
          "blue", ["blue", "green"], 2, SOC, "Second-order false belief (Ben's model of Anna's belief)."),
    label("social-105", "social",
          "At a dinner party, Jordan says loudly, \"Whoever baked this cake used way too much salt.\" The host, "
          "sitting right there, baked the cake. Did Jordan most likely commit a social faux pas? Answer yes or no.",
          "yes", ["yes", "no"], 2, SOC, "Faux-pas recognition."),
    label("social-106", "social",
          "Liam knows the surprise party is really in the garden. He wants to fool Mia, so he tells her it's in "
          "the kitchen, and she believes him. Where does Mia now think the party is? Answer kitchen or garden.",
          "kitchen", ["kitchen", "garden"], 3, SOC, "Induced false belief via deception."),
    label("social-107", "social",
          "Priya sees a new coworker take her labeled lunch bag from the office fridge and start eating it. The "
          "fridge happens to contain two identical bags, and the coworker started only last week. Was the "
          "coworker's action most likely deliberate theft or an honest mistake? Answer deliberate or mistake.",
          "mistake", ["deliberate", "mistake"], 3, SOC, "Intention attribution under exonerating context."),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for t in TASKS:
        (OUT / f"{t['id']}.json").write_text(json.dumps(t, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(TASKS)} tasks to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
