# Player Profile Domain Models for To Boldly Respawn

from dataclasses import dataclass
from typing import Any, Dict, List
from space_demo.domain.content_ids import validate_content_id
from space_demo.domain.ships import ALLOWED_EQUIPMENT_SLOTS

@dataclass(frozen=True)
class PlayerProfile:
    schema_version: int
    selected_ship_id: str
    unlocked_ships: List[str]
    inventory: Dict[str, Any]
    progression: Dict[str, Any]

    def validate(self, strict: bool = False) -> None:
        """Validates the profile structure and constraints. Raises ValueError on violation."""
        if not isinstance(self.schema_version, int) or self.schema_version <= 0:
            raise ValueError(f"schema_version must be a positive integer, got {self.schema_version}")

        validate_content_id(self.selected_ship_id)

        if not isinstance(self.unlocked_ships, list) or not self.unlocked_ships:
            raise ValueError("unlocked_ships must be a non-empty list of strings.")

        for ship_id in self.unlocked_ships:
            validate_content_id(ship_id)

        if len(self.unlocked_ships) != len(set(self.unlocked_ships)):
            raise ValueError(f"unlocked_ships contains duplicates: {self.unlocked_ships}")

        if self.selected_ship_id not in self.unlocked_ships:
            raise ValueError(
                f"Selected ship ID '{self.selected_ship_id}' is not in unlocked_ships list: {self.unlocked_ships}"
            )

        # Validate inventory
        if not isinstance(self.inventory, dict):
            raise ValueError("inventory must be a dictionary.")
        
        if strict:
            allowed_inv = {"equipment", "equipped_by_ship", "resources", "cosmetics"}
            unknown_inv = set(self.inventory.keys()) - allowed_inv
            if unknown_inv:
                raise ValueError(f"Unknown keys in inventory: {unknown_inv}")

        resources = self.inventory.get("resources", {})
        if not isinstance(resources, dict):
            raise ValueError("inventory['resources'] must be a dictionary.")
        for res_id, amount in resources.items():
            validate_content_id(res_id)
            if not isinstance(amount, (int, float)) or amount < 0:
                raise ValueError(f"Resource '{res_id}' amount must be non-negative, got {amount}")

        equipment = self.inventory.get("equipment", [])
        if not isinstance(equipment, list):
            raise ValueError("inventory['equipment'] must be a list.")
        for item in equipment:
            validate_content_id(item)

        if len(equipment) != len(set(equipment)):
            raise ValueError(f"inventory['equipment'] contains duplicate IDs: {equipment}")

        equipped_by_ship = self.inventory.get("equipped_by_ship", {})
        if not isinstance(equipped_by_ship, dict):
            raise ValueError("inventory['equipped_by_ship'] must be a dictionary.")
        
        for ship_id, slots in equipped_by_ship.items():
            validate_content_id(ship_id)
            if not isinstance(slots, dict):
                raise ValueError(f"Slots for ship '{ship_id}' must be a dictionary.")
            for slot_type, eq_id in slots.items():
                if slot_type not in ALLOWED_EQUIPMENT_SLOTS:
                    raise ValueError(f"Invalid slot_type '{slot_type}' for ship '{ship_id}'. Allowed: {ALLOWED_EQUIPMENT_SLOTS}")
                if eq_id is not None:
                    if not isinstance(eq_id, str):
                        raise ValueError(f"Equipped item ID in slot '{slot_type}' for ship '{ship_id}' must be a string or None.")
                    validate_content_id(eq_id)
                    if eq_id not in equipment:
                        raise ValueError(f"Equipped item '{eq_id}' in slot '{slot_type}' for ship '{ship_id}' is not in owned equipment list.")

        cosmetics = self.inventory.get("cosmetics", [])
        if not isinstance(cosmetics, list):
            raise ValueError("inventory['cosmetics'] must be a list.")
        for item in cosmetics:
            validate_content_id(item)

        # Validate progression
        if not isinstance(self.progression, dict):
            raise ValueError("progression must be a dictionary.")

        if strict:
            allowed_prog = {"completed_maps", "awarded_unique_rewards", "quest_flags", "story_flags", "research"}
            unknown_prog = set(self.progression.keys()) - allowed_prog
            if unknown_prog:
                raise ValueError(f"Unknown keys in progression: {unknown_prog}")

        # Validate unique rewards list
        awarded_unique_rewards = self.progression.get("awarded_unique_rewards", [])
        if not isinstance(awarded_unique_rewards, list):
            raise ValueError("progression['awarded_unique_rewards'] must be a list.")
        for reward_id in awarded_unique_rewards:
            if not isinstance(reward_id, str):
                raise ValueError(f"Unique reward ID must be a string, got {type(reward_id)}")
            validate_content_id(reward_id)
        if len(awarded_unique_rewards) != len(set(awarded_unique_rewards)):
            raise ValueError(f"progression['awarded_unique_rewards'] contains duplicates: {awarded_unique_rewards}")

        completed_maps = self.progression.get("completed_maps", {})
        if not isinstance(completed_maps, dict):
            raise ValueError("progression['completed_maps'] must be a dictionary.")
        for m_id, comp_data in completed_maps.items():
            validate_content_id(m_id)
            if not isinstance(comp_data, dict):
                raise ValueError(f"progression['completed_maps']['{m_id}'] must be a dictionary.")
            
            # Validate completions structure
            completions = comp_data.get("completions", {})
            if not isinstance(completions, dict):
                raise ValueError(f"completions under map '{m_id}' must be a dictionary.")
            for diff, count in completions.items():
                if diff not in {"easy", "medium", "hard"}:
                    raise ValueError(f"Invalid completion difficulty '{diff}' for map '{m_id}'.")
                if not isinstance(count, int) or isinstance(count, bool):
                    raise ValueError(f"Completion count for difficulty '{diff}' under map '{m_id}' must be an integer, got {type(count).__name__}.")
                if count < 0:
                    raise ValueError(f"Completion count for difficulty '{diff}' under map '{m_id}' must be non-negative, got {count}.")

    @classmethod
    def from_dict(cls, data: Dict[str, Any], strict: bool = False) -> "PlayerProfile":
        """Builds a PlayerProfile from a dictionary."""
        expected_fields = {
            "schema_version", "selected_ship_id", "unlocked_ships", "inventory", "progression"
        }
        if strict:
            unknown = set(data.keys()) - expected_fields
            if unknown:
                raise ValueError(f"Unknown fields in player profile: {unknown}")
            missing = expected_fields - set(data.keys())
            if missing:
                raise ValueError(f"Missing required fields in player profile: {missing}")

        return cls(
            schema_version=data.get("schema_version", 1),
            selected_ship_id=data.get("selected_ship_id"),
            unlocked_ships=data.get("unlocked_ships", []),
            inventory=data.get("inventory", {}),
            progression=data.get("progression", {}),
        )
