"""Trusted deterministic reference implementations for the simulation tasks.

These compute *gold* answers by numerical integration / closed form. They are
plain Python and must never call a model. The benchmark stores the values they
produce inside the task JSON (``numeric_tol.reference``); ``tests/test_references.py``
re-derives them to prove the gold came from here, not from an LLM.
"""

from __future__ import annotations

import math
from typing import Mapping


def projectile_drag(params: Mapping[str, float]) -> float:
    """Horizontal range of a projectile under quadratic drag.

    Equations of motion (componentwise quadratic drag):
        ax = -c * |v| * vx
        ay = -g - c * |v| * vy
    Integrated with fixed-step RK4 until the projectile returns to y = 0, then
    linearly interpolated to the ground crossing. There is no closed form for
    the range under quadratic drag -- that is the whole point of the task.
    """
    v0 = float(params["v0"])
    angle = math.radians(float(params["angle_deg"]))
    c = float(params["drag"])
    g = float(params["g"])
    dt = float(params.get("dt", 0.0005))

    def deriv(state):
        x, y, vx, vy = state
        speed = math.hypot(vx, vy)
        ax = -c * speed * vx
        ay = -g - c * speed * vy
        return (vx, vy, ax, ay)

    def step(state):
        k1 = deriv(state)
        s2 = tuple(state[i] + 0.5 * dt * k1[i] for i in range(4))
        k2 = deriv(s2)
        s3 = tuple(state[i] + 0.5 * dt * k2[i] for i in range(4))
        k3 = deriv(s3)
        s4 = tuple(state[i] + dt * k3[i] for i in range(4))
        k4 = deriv(s4)
        return tuple(
            state[i] + (dt / 6.0) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i])
            for i in range(4)
        )

    state = (0.0, 0.0, v0 * math.cos(angle), v0 * math.sin(angle))
    prev = state
    # integrate; stop once we have launched and crossed back to y <= 0
    while True:
        nxt = step(state)
        if nxt[1] <= 0.0 and nxt[3] < 0.0:
            # interpolate the ground crossing between `state` (y>0) and `nxt` (y<=0)
            y0, y1 = state[1], nxt[1]
            frac = y0 / (y0 - y1) if y0 != y1 else 0.0
            return state[0] + frac * (nxt[0] - state[0])
        prev, state = state, nxt
        if state[0] > 1e7:  # safety guard, never hit for sane params
            return state[0]


def projectile_vacuum(params: Mapping[str, float]) -> float:
    """Closed-form range with NO drag -- the naive 'code' (algebra) answer.

    Used by the mock world as the deterministic *wrong* answer when an agent
    reaches for a closed-form formula on the drag task.
    """
    v0 = float(params["v0"])
    angle = math.radians(float(params["angle_deg"]))
    g = float(params["g"])
    return (v0 * v0) * math.sin(2 * angle) / g


def newton_cooling(params: Mapping[str, float]) -> float:
    """Temperature after time t under Newton's law of cooling (closed form).

        T(t) = T_env + (T0 - T_env) * exp(-k * t)

    A closed form exists, which is exactly why sim-002 lists both `simulation`
    and `code` as acceptable substrates.
    """
    t_env = float(params["t_env"])
    t0 = float(params["t0"])
    k = float(params["k"])
    t = float(params["t"])
    return t_env + (t0 - t_env) * math.exp(-k * t)
