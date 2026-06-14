# Equipment Domain Models for To Boldly Respawn

import math
from dataclasses import dataclass
from typing import Any, Dict, List
from space_demo.domain.content_ids import validate_content_id
from space_demo.domain.ships import ALLOWED_EQUIPMENT_SLOTS

ALLOWED_MODIFIER_STATS = {
    "max_hull",
    "move_speed",
    "fire_cooldown",
    "missile_capacity",
    "bomb_capacity",
}

@dataclass(frozen=True)
class ModifierEntry:
    add: float = 0.0
    pct: float = 0.0

    def validate(self) -> None:
        """Validates that modifier fields are finite numbers, not booleans or strings."""
        for name, val in [("add", self.add), ("pct", self.pct)]:
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise ValueError(f"Modifier '{name}' must be a finite float or int, got {type(val).__name__}")
            if not math.isfinite(val):
                raise ValueError(f"Modifier '{name}' must be a finite number, got {val}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any], strict: bool = False) -> "ModifierEntry":
        """Builds a ModifierEntry from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError("ModifierEntry must be a dictionary.")
        if strict:
            unknown = set(data.keys()) - {"add", "pct"}
            if unknown:
                raise ValueError(f"Unknown fields in modifier entry: {unknown}")

        add_val = data.get("add", 0.0)
        pct_val = data.get("pct", 0.0)
        return cls(add=add_val, pct=pct_val)


@dataclass(frozen=True)
class EquipmentDef:
    id: str
    display_name: str
    slot_type: str
    rarity: str
    stat_modifiers: Dict[str, ModifierEntry]
    unlock: Dict[str, Any]
    abilities: List[str]

    def validate(self, strict: bool = False) -> None:
        """Validates the equipment definition. Raises ValueError on violation."""
        validate_content_id(self.id)
        if not self.display_name or not isinstance(self.display_name, str):
            raise ValueError("display_name must be a non-empty string.")
        if not isinstance(self.slot_type, str) or self.slot_type not in ALLOWED_EQUIPMENT_SLOTS:
            raise ValueError(f"Invalid slot_type '{self.slot_type}'. Allowed: {ALLOWED_EQUIPMENT_SLOTS}")
        if not isinstance(self.rarity, str) or not self.rarity:
            raise ValueError("rarity must be a non-empty string.")
        
        # Validate stat modifiers
        if not isinstance(self.stat_modifiers, dict):
            raise ValueError("stat_modifiers must be a dictionary.")
        
        for stat_name, modifier in self.stat_modifiers.items():
            if stat_name not in ALLOWED_MODIFIER_STATS:
                raise ValueError(f"Invalid modifier stat name '{stat_name}'. Allowed: {ALLOWED_MODIFIER_STATS}")
            if not isinstance(modifier, ModifierEntry):
                raise ValueError(f"Modifier for '{stat_name}' must be a ModifierEntry.")
            modifier.validate()

        # Validate unlock dictionary structure
        if not isinstance(self.unlock, dict) or "type" not in self.unlock:
            raise ValueError("unlock must be a dict containing a 'type' field.")

        # Validate abilities list
        if not isinstance(self.abilities, list):
            raise ValueError("abilities must be a list of strings.")
        for ability in self.abilities:
            validate_content_id(ability)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], strict: bool = False) -> "EquipmentDef":
        """Builds an EquipmentDef from a dictionary."""
        expected_fields = {
            "id", "display_name", "slot_type", "rarity", "stat_modifiers", "unlock", "abilities"
        }
        if strict:
            unknown = set(data.keys()) - expected_fields
            if unknown:
                raise ValueError(f"Unknown fields in equipment definition: {unknown}")
            missing = expected_fields - set(data.keys())
            if missing:
                raise ValueError(f"Missing required fields in equipment definition: {missing}")

        modifiers_raw = data.get("stat_modifiers", {})
        if not isinstance(modifiers_raw, dict):
            raise ValueError("stat_modifiers must be a dictionary.")

        modifiers = {}
        for stat, mod_data in modifiers_raw.items():
            modifiers[stat] = ModifierEntry.from_dict(mod_data, strict=strict)

        return cls(
            id=data.get("id"),
            display_name=data.get("display_name"),
            slot_type=data.get("slot_type"),
            rarity=data.get("rarity"),
            stat_modifiers=modifiers,
            unlock=data.get("unlock", {}),
            abilities=data.get("abilities", []),
        )
