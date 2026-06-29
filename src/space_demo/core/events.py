# Decoupled Event System - To Boldly Respawn

from dataclasses import dataclass
from typing import Tuple

class GameEvent:
    """Base class for all pure-Python game simulation events."""
    pass

@dataclass
class PopupEvent(GameEvent):
    """Event representing a floating 3D text notification."""
    text: str
    x: float
    y: float
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    scale: float = 0.35
    lifetime: float = 1.0

@dataclass
class EnemyHitEvent(GameEvent):
    """Event fired when an enemy chaser takes damage."""
    enemy_type: str
    damage: int
    x: float
    y: float
    proj_type: str = "unknown"

@dataclass
class EnemyDestroyedEvent(GameEvent):
    """Event fired when an enemy chaser is defeated."""
    enemy_type: str
    x: float
    y: float
    score_val: int

@dataclass
class PlayerHitEvent(GameEvent):
    """Event fired when the player ship is hit."""
    damage: int
    x: float
    y: float

@dataclass
class CollisionEvent(GameEvent):
    """Event fired when the player ship collides with a chaser."""
    damage: int
    x: float
    y: float

@dataclass
class PickupCollectedEvent(GameEvent):
    """Event fired when the player collects a reward."""
    pickup_type: str
    x: float
    y: float

@dataclass
class ShieldBrokenEvent(GameEvent):
    """Event fired when the player's liability waiver shield is destroyed."""
    x: float
    y: float


@dataclass
class ExecutiveDecisionEvent(GameEvent):
    """Event representing the firing of an Executive Decision bomb."""
    x: float
    y: float

@dataclass
class MagnetActivatedEvent(GameEvent):
    """Event representing activation of the Synergy Magnet."""
    x: float
    y: float
    duration: float

@dataclass
class MagnetDeactivatedEvent(GameEvent):
    """Event representing expiration of the Synergy Magnet."""
    pass


@dataclass
class InternActivatedEvent(GameEvent):
    """Event representing activation of the Unpaid Intern."""
    x: float
    y: float
    duration: float


@dataclass
class InternDeactivatedEvent(GameEvent):
    """Event representing expiration of the Unpaid Intern."""
    pass


@dataclass
class NotificationEvent(GameEvent):
    """Event representing a sleek, high-priority status notification."""
    title: str
    message: str = ""
    category: str = "system"
    severity: str = "info"
    icon: str | None = None
    value: str | None = None
    duration: float = 1.0

