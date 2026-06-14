"""Enemy trail visual effects built on the shared particle trail pool."""

from __future__ import annotations

import random


ENEMY_TRAIL_PROFILES = {
    "speeder": {
        "scale": 0.16,
        "color": (1.00, 0.50, 0.12, 0.65),
        "decay_rate": 5.5,
        "velocity_z": -2.8,
        "jitter": 0.18,
    },
    "zigzag": {
        "scale": 0.15,
        "color": (0.95, 0.25, 1.00, 0.60),
        "decay_rate": 5.8,
        "velocity_z": -2.2,
        "jitter": 0.28,
    },
    "frigate": {
        "scale": 0.18,
        "color": (0.15, 0.95, 0.40, 0.55),
        "decay_rate": 4.8,
        "velocity_z": -1.5,
        "jitter": 0.35,
    },
    "missile_boat": {
        "scale": 0.17,
        "color": (1.00, 0.85, 0.15, 0.58),
        "decay_rate": 5.0,
        "velocity_z": -1.8,
        "jitter": 0.24,
    },
}


def spawn_enemy_engine_trail(vfx_mgr, enemy_type: str, x: float, z: float) -> None:
    """Spawn a lightweight enemy trail using VFXManager's pooled particle API."""
    if getattr(vfx_mgr, "headless", False):
        return

    profile = ENEMY_TRAIL_PROFILES.get(enemy_type)
    if profile is None:
        return

    app = getattr(vfx_mgr, "app", None)
    state_mgr = getattr(app, "state_mgr", None)
    if state_mgr is not None and not getattr(state_mgr, "vfx_high", True):
        clock = getattr(app, "clock", None)
        if clock is not None and clock.getFrameCount() % 3 != 0:
            return

    jitter = profile["jitter"]
    vfx_mgr.spawn_trail_segment(
        x + random.uniform(-jitter, jitter),
        z - 0.45,
        scale=profile["scale"],
        color=profile["color"],
        decay_rate=profile["decay_rate"],
        velocity=(random.uniform(-0.25, 0.25), profile["velocity_z"]),
    )
