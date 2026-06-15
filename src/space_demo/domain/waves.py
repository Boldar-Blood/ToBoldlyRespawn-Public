# Wave Domain Models for To Boldly Respawn

import math
from dataclasses import dataclass
from typing import Any, Dict, List
from space_demo.domain.content_ids import validate_content_id

@dataclass(frozen=True)
class WaveDef:
    id: str
    duration: float
    max_enemies: int
    spawn_cooldown: float
    escorts: List[str]

    def validate(self, strict: bool = False) -> None:
        """Validates the wave definition. Raises ValueError on violation."""
        validate_content_id(self.id)
        
        # duration validation
        # Reject booleans (isinstance(True, (int, float)) is True in Python)
        if isinstance(self.duration, bool) or not isinstance(self.duration, (int, float)):
            raise ValueError("duration must be a positive number.")
        if math.isnan(self.duration) or math.isinf(self.duration) or self.duration <= 0.0:
            raise ValueError("duration must be a positive number.")

        # max_enemies validation
        if isinstance(self.max_enemies, bool) or not isinstance(self.max_enemies, int):
            raise ValueError("max_enemies must be a non-negative integer.")
        if self.max_enemies < 0:
            raise ValueError("max_enemies must be a non-negative integer.")

        # spawn_cooldown validation
        if isinstance(self.spawn_cooldown, bool) or not isinstance(self.spawn_cooldown, (int, float)):
            raise ValueError("spawn_cooldown must be a positive number.")
        if math.isnan(self.spawn_cooldown) or math.isinf(self.spawn_cooldown) or self.spawn_cooldown <= 0.0:
            raise ValueError("spawn_cooldown must be a positive number.")

        # escorts validation
        if not isinstance(self.escorts, list) or not self.escorts:
            raise ValueError("escorts must be a non-empty list of strings.")
        for e in self.escorts:
            if isinstance(e, bool) or not isinstance(e, str):
                raise ValueError(f"Every escort entry must be a string, got {type(e)}")
            validate_content_id(e)

    @classmethod
    def from_dict(cls, wave_id: str, data: Dict[str, Any], strict: bool = False) -> "WaveDef":
        expected_fields = {"duration", "max_enemies", "spawn_cooldown", "escorts"}
        if strict:
            unknown = set(data.keys()) - expected_fields
            if unknown:
                raise ValueError(f"Unknown fields in wave definition: {unknown}")
            missing = expected_fields - set(data.keys())
            if missing:
                raise ValueError(f"Missing required fields in wave definition: {missing}")

        return cls(
            id=wave_id,
            duration=data.get("duration"),
            max_enemies=data.get("max_enemies"),
            spawn_cooldown=data.get("spawn_cooldown"),
            escorts=data.get("escorts", []),
        )
