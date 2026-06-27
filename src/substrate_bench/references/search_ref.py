"""Trusted deterministic reference implementations for the search tasks.

Tower of Hanoi (optimal move generator + legality/optimality validator) and a
small gridworld (BFS shortest path + path validator). Plain Python, no models.
"""

from __future__ import annotations

from collections import deque
from typing import List, Sequence, Tuple

Move = Tuple[str, str]  # (from_peg, to_peg)


# --------------------------------------------------------------------------- #
# Tower of Hanoi
# --------------------------------------------------------------------------- #
def hanoi_solve(n: int, source: str = "A", target: str = "C", aux: str = "B") -> List[Move]:
    """Return the optimal (length 2**n - 1) sequence of [from, to] moves."""
    moves: List[Move] = []

    def rec(k: int, src: str, dst: str, spare: str) -> None:
        if k == 0:
            return
        rec(k - 1, src, spare, dst)
        moves.append((src, dst))
        rec(k - 1, spare, dst, src)

    rec(n, source, target, aux)
    return moves


def hanoi_validate(
    n: int,
    moves: Sequence[Sequence[str]],
    source: str = "A",
    target: str = "C",
    aux: str = "B",
    require_optimal: bool = True,
) -> bool:
    """True iff `moves` legally transfers n disks from source to target.

    A move is legal if it takes the top disk of a non-empty peg and never places
    a larger disk on a smaller one. Disks are integers 1..n (1 = smallest).
    """
    pegs = {source: list(range(n, 0, -1)), target: [], aux: []}
    for mv in moves:
        if len(mv) != 2:
            return False
        frm, to = mv[0], mv[1]
        if frm not in pegs or to not in pegs or frm == to:
            return False
        if not pegs[frm]:
            return False
        disk = pegs[frm][-1]
        if pegs[to] and pegs[to][-1] < disk:
            return False
        pegs[to].append(pegs[frm].pop())
    if pegs[target] != list(range(n, 0, -1)):
        return False
    if require_optimal and len(moves) != (2 ** n - 1):
        return False
    return True


# --------------------------------------------------------------------------- #
# Gridworld shortest path
# --------------------------------------------------------------------------- #
_DELTAS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}


def _parse_grid(grid: Sequence[str]) -> List[str]:
    return [row for row in grid]


def gridworld_shortest(
    grid: Sequence[str], start: Sequence[int], goal: Sequence[int]
) -> List[str]:
    """BFS shortest path on a 4-connected grid ('.'=free, '#'=wall).

    Returns the move string list (U/D/L/R). Raises if unreachable.
    """
    g = _parse_grid(grid)
    rows, cols = len(g), len(g[0])
    sr, sc = int(start[0]), int(start[1])
    gr, gc = int(goal[0]), int(goal[1])
    seen = {(sr, sc)}
    q = deque([((sr, sc), [])])
    while q:
        (r, c), path = q.popleft()
        if (r, c) == (gr, gc):
            return path
        for mv, (dr, dc) in _DELTAS.items():
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and g[nr][nc] != "#" and (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append(((nr, nc), path + [mv]))
    raise ValueError("goal unreachable")


def gridworld_optimal_length(
    grid: Sequence[str], start: Sequence[int], goal: Sequence[int]
) -> int:
    return len(gridworld_shortest(grid, start, goal))


def gridworld_validate(
    grid: Sequence[str],
    start: Sequence[int],
    goal: Sequence[int],
    moves: Sequence[str],
    require_optimal: bool = True,
) -> bool:
    """True iff `moves` walks from start to goal without hitting walls/edges."""
    g = _parse_grid(grid)
    rows, cols = len(g), len(g[0])
    r, c = int(start[0]), int(start[1])
    for mv in moves:
        if mv not in _DELTAS:
            return False
        dr, dc = _DELTAS[mv]
        r, c = r + dr, c + dc
        if not (0 <= r < rows and 0 <= c < cols) or g[r][c] == "#":
            return False
    if (r, c) != (int(goal[0]), int(goal[1])):
        return False
    if require_optimal and len(moves) != gridworld_optimal_length(grid, start, goal):
        return False
    return True
