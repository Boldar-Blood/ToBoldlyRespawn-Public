# Runtime Equipment Resolver and Adapter for To Boldly Respawn

import json
import math
from pathlib import Path
from typing import Dict, Optional, Union
from space_demo.data.loader import get_data_dir
from space_demo.domain.ships import ShipDef, ShipStats
from space_demo.domain.profile import PlayerProfile
from space_demo.domain.equipment import EquipmentDef, ModifierEntry

class EquipmentRuntimeAdapter:
    """
    Loads equipment definitions from equipment.json, validates player inventory equipment
    references, and computes effective ship stats after applying modifiers.
    """
    def __init__(self, equipment_path: Optional[Union[Path, str]] = None):
        if equipment_path:
            self.equipment_path = Path(equipment_path)
        else:
            self.equipment_path = Path(get_data_dir()) / "equipment.json"

    def load_equipment_defs(self) -> Dict[str, EquipmentDef]:
        """Loads and validates all equipment definitions from equipment.json."""
        if not self.equipment_path.exists():
            raise FileNotFoundError(f"equipment.json not found at {self.equipment_path}")

        try:
            with open(self.equipment_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse equipment.json: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("Root of equipment.json must be a JSON object.")
        if "equipment" not in data or not isinstance(data["equipment"], list):
            raise ValueError("Invalid equipment.json format: Missing or invalid 'equipment' list.")

        equipment_defs = {}
        for index, item in enumerate(data["equipment"]):
            try:
                eq_def = EquipmentDef.from_dict(item, strict=True)
                eq_def.validate(strict=True)
                if eq_def.id in equipment_defs:
                    raise ValueError(f"Duplicate equipment ID found in definitions: {eq_def.id}")
                equipment_defs[eq_def.id] = eq_def
            except Exception as e:
                raise ValueError(f"Invalid equipment definition at index {index}: {e}") from e
        return equipment_defs

    def resolve_effective_stats(self, profile: PlayerProfile, ship_def: ShipDef) -> ShipStats:
        """
        Validates the equipped equipment against the ship definition slots and ownership,
        then calculates the effective ShipStats for this ship by applying all modifiers.
        """
        # Validate profile invariants
        profile.validate(strict=True)

        equipment_defs = self.load_equipment_defs()
        owned_equipment = profile.inventory.get("equipment", [])

        # 1. Validate that all owned equipment exists in definitions
        for eq_id in owned_equipment:
            if eq_id not in equipment_defs:
                raise ValueError(f"Owned equipment ID '{eq_id}' in player profile does not exist in definitions.")

        # 2. Extract equipped items for this ship
        equipped_by_ship = profile.inventory.get("equipped_by_ship", {})
        ship_equipped = equipped_by_ship.get(ship_def.id, {})

        active_equipment = []
        for slot_type, eq_id in ship_equipped.items():
            if eq_id is None:
                continue

            # Validate that slot exists on the ship
            if slot_type not in ship_def.equipment_slots:
                raise ValueError(f"Slot type '{slot_type}' is not a valid equipment slot on ship '{ship_def.id}'.")

            # Validate that item is defined
            if eq_id not in equipment_defs:
                raise ValueError(f"Equipped item '{eq_id}' in slot '{slot_type}' for ship '{ship_def.id}' does not exist in definitions.")

            # Validate that item is owned
            if eq_id not in owned_equipment:
                raise ValueError(f"Equipped item '{eq_id}' in slot '{slot_type}' for ship '{ship_def.id}' is not owned.")

            # Validate slot compatibility
            eq_def = equipment_defs[eq_id]
            if eq_def.slot_type != slot_type:
                raise ValueError(f"Equipped item '{eq_id}' defined slot_type '{eq_def.slot_type}' does not match slot '{slot_type}' on ship '{ship_def.id}'.")

            active_equipment.append(eq_def)

        # 3. Calculate effective stats by applying modifiers
        base_stats = ship_def.stats
        effective_hull = float(base_stats.max_hull)
        effective_speed = base_stats.move_speed
        effective_cooldown = base_stats.fire_cooldown
        effective_missile = float(base_stats.missile_capacity)
        effective_bomb = float(base_stats.bomb_capacity)

        stats_mapping = {
            "max_hull": effective_hull,
            "move_speed": effective_speed,
            "fire_cooldown": effective_cooldown,
            "missile_capacity": effective_missile,
            "bomb_capacity": effective_bomb,
        }

        # Apply stat modifiers deterministically
        for stat_name in stats_mapping.keys():
            add_sum = 0.0
            pct_sum = 0.0
            for eq_def in active_equipment:
                mod_entry = eq_def.stat_modifiers.get(stat_name)
                if mod_entry is not None:
                    add_sum += mod_entry.add
                    pct_sum += mod_entry.pct
            
            base_val = getattr(base_stats, stat_name)
            effective_val = (base_val + add_sum) * (1.0 + pct_sum)
            stats_mapping[stat_name] = effective_val

        # Clamp values
        effective_hull = max(10.0, min(1000.0, stats_mapping["max_hull"]))
        effective_speed = max(2.0, min(30.0, stats_mapping["move_speed"]))
        effective_cooldown = max(0.05, min(2.0, stats_mapping["fire_cooldown"]))
        effective_missile = max(0.0, min(50.0, stats_mapping["missile_capacity"]))
        effective_bomb = max(0.0, min(10.0, stats_mapping["bomb_capacity"]))

        return ShipStats(
            max_hull=int(round(effective_hull)),
            move_speed=effective_speed,
            fire_cooldown=effective_cooldown,
            missile_capacity=int(round(effective_missile)),
            bomb_capacity=int(round(effective_bomb)),
        )
