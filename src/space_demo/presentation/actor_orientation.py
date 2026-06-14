"""Pure presentation-orientation helpers for actor sprites."""

from __future__ import annotations

import math


PLAYER_MAX_BANK_DEGREES = 12.0
ENEMY_MAX_TURN_DEGREES = 32.0
MOVEMENT_DEADZONE = 0.001
NON_TURNING_ENEMY_TYPES = frozenset({"boss", "mine"})


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a numeric value to an inclusive range."""
    return max(minimum, min(maximum, value))


def player_bank_roll(left_pressed: bool, right_pressed: bool, max_bank: float = PLAYER_MAX_BANK_DEGREES) -> float:
    """Return player roll where right movement banks right and left movement banks left."""
    if left_pressed == right_pressed:
        return 0.0
    return -max_bank if left_pressed else max_bank


def enemy_turns_with_movement(enemy_type: str, explicit_flag: bool | None = None) -> bool:
    """Return whether a given enemy should visually roll toward movement."""
    if explicit_flag is not None:
        return bool(explicit_flag)
    return enemy_type not in NON_TURNING_ENEMY_TYPES


def enemy_roll_from_motion(
    dx: float,
    dy: float,
    max_turn: float = ENEMY_MAX_TURN_DEGREES,
    deadzone: float = MOVEMENT_DEADZONE,
) -> float:
    """Return a clamped sprite roll based on X/Z-plane movement.

    A sprite facing straight upward has roll 0. Positive X movement turns the
    actor right; negative X movement turns it left. The clamp keeps enemy art
    readable and prevents extreme spinning when an actor briefly moves sideways.
    """
    if abs(dx) <= deadzone and abs(dy) <= deadzone:
        return 0.0

    roll = math.degrees(math.atan2(dx, dy))
    return clamp(roll, -max_turn, max_turn)


def smooth_roll(current: float, target: float, blend: float) -> float:
    """Blend a current roll toward a target roll."""
    blend = clamp(blend, 0.0, 1.0)
    return current + (target - current) * blend
