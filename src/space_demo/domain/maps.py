# Map Domain Models for To Boldly Respawn

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from space_demo.domain.content_ids import validate_content_id

ALLOWED_DIFFICULTIES = {"easy", "medium", "hard"}

@dataclass(frozen=True)
class MapDef:
    id: str
    display_name: str
    description: str
    difficulty_support: List[str]
    waves: List[str]
    enemy_pool: List[str]
    boss: Optional[str]
    rewards: Dict[str, List[str]]
    unlock_requirements: Dict[str, Any] = field(default_factory=dict)

    def validate(self, strict: bool = False) -> None:
        """Validates the map definition. Raises ValueError on violation."""
        validate_content_id(self.id)
        if not self.display_name or not isinstance(self.display_name, str):
            raise ValueError("display_name must be a non-empty string.")
        if not isinstance(self.description, str):
            raise ValueError("description must be a string.")

        # Validate difficulty support
        if not isinstance(self.difficulty_support, list) or not self.difficulty_support:
            raise ValueError("difficulty_support must be a non-empty list of strings.")
        for diff in self.difficulty_support:
            if diff not in ALLOWED_DIFFICULTIES:
                raise ValueError(f"Invalid difficulty '{diff}'. Allowed difficulties: {ALLOWED_DIFFICULTIES}")

        # Validate waves
        if not isinstance(self.waves, list) or not self.waves:
            raise ValueError("waves must be a non-empty list of strings.")
        for wave in self.waves:
            validate_content_id(wave)

        # Validate enemy pool
        if not isinstance(self.enemy_pool, list):
            raise ValueError("enemy_pool must be a list of strings.")
        for enemy in self.enemy_pool:
            validate_content_id(enemy)

        # Validate boss
        if self.boss is not None:
            if not isinstance(self.boss, str) or not self.boss:
                raise ValueError("boss must be a non-empty string if provided.")
            validate_content_id(self.boss)

        # Validate rewards mapping
        if not isinstance(self.rewards, dict):
            raise ValueError("rewards must be a dictionary.")
        for hook, reward_list in self.rewards.items():
            if not isinstance(hook, str) or not hook:
                raise ValueError("reward hooks must be non-empty strings.")
            if not isinstance(reward_list, list):
                raise ValueError(f"rewards['{hook}'] must be a list of reward IDs.")
            for r_id in reward_list:
                validate_content_id(r_id)

        # Validate unlock requirements
        if not isinstance(self.unlock_requirements, dict):
            raise ValueError("unlock_requirements must be a dictionary.")

    @classmethod
    def from_dict(cls, data: Dict[str, Any], strict: bool = False) -> "MapDef":
        """Builds a MapDef from a dictionary."""
        expected_fields = {
            "id", "display_name", "description", "difficulty_support",
            "waves", "enemy_pool", "boss", "rewards", "unlock_requirements"
        }
        if strict:
            unknown = set(data.keys()) - expected_fields
            if unknown:
                raise ValueError(f"Unknown fields in map definition: {unknown}")
            missing = (expected_fields - {"unlock_requirements"}) - set(data.keys())
            if missing:
                raise ValueError(f"Missing required fields in map definition: {missing}")

        return cls(
            id=data.get("id"),
            display_name=data.get("display_name"),
            description=data.get("description", ""),
            difficulty_support=data.get("difficulty_support", []),
            waves=data.get("waves", []),
            enemy_pool=data.get("enemy_pool", []),
            boss=data.get("boss"),
            rewards=data.get("rewards", {}),
            unlock_requirements=data.get("unlock_requirements", {}),
        )

