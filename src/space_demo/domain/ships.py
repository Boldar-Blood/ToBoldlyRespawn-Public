# Ship Domain Models for To Boldly Respawn

from dataclasses import dataclass
from typing import Any, Dict, List
from space_demo.domain.content_ids import validate_content_id

ALLOWED_EQUIPMENT_SLOTS = {"weapon", "engine", "utility"}

@dataclass(frozen=True)
class ShipStats:
    max_hull: int
    move_speed: float
    fire_cooldown: float
    missile_capacity: int
    bomb_capacity: int

    def validate(self) -> None:
        """Validates stats bounds. Raises ValueError on violation."""
        if not isinstance(self.max_hull, int) or self.max_hull <= 0:
            raise ValueError(f"max_hull must be a positive integer, got {self.max_hull}")
        if not isinstance(self.move_speed, (int, float)) or self.move_speed <= 0.0:
            raise ValueError(f"move_speed must be a positive number, got {self.move_speed}")
        if not isinstance(self.fire_cooldown, (int, float)) or self.fire_cooldown <= 0.0:
            raise ValueError(f"fire_cooldown must be a positive number, got {self.fire_cooldown}")
        if not isinstance(self.missile_capacity, int) or self.missile_capacity < 0:
            raise ValueError(f"missile_capacity must be a non-negative integer, got {self.missile_capacity}")
        if not isinstance(self.bomb_capacity, int) or self.bomb_capacity < 0:
            raise ValueError(f"bomb_capacity must be a non-negative integer, got {self.bomb_capacity}")

@dataclass(frozen=True)
class ShipDef:
    id: str
    display_name: str
    description: str
    unlock: Dict[str, Any]
    stats: ShipStats
    equipment_slots: List[str]
    abilities: List[str]
    asset_keys: Dict[str, Any]

    def validate(self, strict: bool = False) -> None:
        """Validates the ship definition. Raises ValueError on violation."""
        validate_content_id(self.id)
        if not self.display_name or not isinstance(self.display_name, str):
            raise ValueError("display_name must be a non-empty string.")
        if not isinstance(self.description, str):
            raise ValueError("description must be a string.")
        
        # Validate unlock dictionary structure
        if not isinstance(self.unlock, dict) or "type" not in self.unlock:
            raise ValueError("unlock must be a dict containing a 'type' field.")
        
        # Validate stats
        if not isinstance(self.stats, ShipStats):
            raise ValueError("stats must be an instance of ShipStats.")
        self.stats.validate()

        # Validate equipment slots
        if not isinstance(self.equipment_slots, list):
            raise ValueError("equipment_slots must be a list of strings.")
        for slot in self.equipment_slots:
            if slot not in ALLOWED_EQUIPMENT_SLOTS:
                raise ValueError(f"Invalid equipment slot '{slot}'. Allowed slots are: {ALLOWED_EQUIPMENT_SLOTS}")

        # Validate abilities
        if not isinstance(self.abilities, list):
            raise ValueError("abilities must be a list of strings.")
        for ability in self.abilities:
            validate_content_id(ability)

        # Validate asset keys
        if not isinstance(self.asset_keys, dict) or "sprite" not in self.asset_keys:
            raise ValueError("asset_keys must be a dict containing a 'sprite' field.")
        if not isinstance(self.asset_keys.get("sprite"), str) or not self.asset_keys["sprite"]:
            raise ValueError("asset_keys['sprite'] must be a non-empty string.")
        if strict:
            unknown_keys = set(self.asset_keys.keys()) - {"sprite", "model_25d"}
            if unknown_keys:
                raise ValueError(f"Unknown keys in asset_keys: {unknown_keys}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any], strict: bool = False) -> "ShipDef":
        """Builds a ShipDef from a dictionary."""
        expected_fields = {
            "id", "display_name", "description", "unlock", "stats",
            "equipment_slots", "abilities", "asset_keys"
        }
        if strict:
            unknown = set(data.keys()) - expected_fields
            if unknown:
                raise ValueError(f"Unknown fields in ship definition: {unknown}")
            missing = expected_fields - set(data.keys())
            if missing:
                raise ValueError(f"Missing required fields in ship definition: {missing}")

        # Parse stats
        stats_data = data.get("stats")
        if not isinstance(stats_data, dict):
            raise ValueError("stats field must be a dictionary.")
        
        expected_stats = {
            "max_hull", "move_speed", "fire_cooldown", "missile_capacity", "bomb_capacity"
        }
        if strict:
            unknown_stats = set(stats_data.keys()) - expected_stats
            if unknown_stats:
                raise ValueError(f"Unknown fields in stats: {unknown_stats}")
            missing_stats = expected_stats - set(stats_data.keys())
            if missing_stats:
                raise ValueError(f"Missing required fields in stats: {missing_stats}")

        stats = ShipStats(
            max_hull=stats_data.get("max_hull"),
            move_speed=stats_data.get("move_speed"),
            fire_cooldown=stats_data.get("fire_cooldown"),
            missile_capacity=stats_data.get("missile_capacity"),
            bomb_capacity=stats_data.get("bomb_capacity"),
        )

        return cls(
            id=data.get("id"),
            display_name=data.get("display_name"),
            description=data.get("description", ""),
            unlock=data.get("unlock", {}),
            stats=stats,
            equipment_slots=data.get("equipment_slots", []),
            abilities=data.get("abilities", []),
            asset_keys=data.get("asset_keys", {}),
        )
