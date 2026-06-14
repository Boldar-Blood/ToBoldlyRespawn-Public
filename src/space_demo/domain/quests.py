# Quest Domain Models for To Boldly Respawn

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from space_demo.domain.content_ids import validate_content_id

ALLOWED_OBJECTIVE_TYPES = {
    "complete_map",
    "defeat_enemy_type",
    "defeat_boss",
    "collect_pickup_type",
    "survive_seconds",
    "reach_score"
}

@dataclass(frozen=True)
class QuestObjective:
    id: str
    type: str
    target: Union[int, float]
    map_id: Optional[str] = None
    difficulty: Optional[str] = None
    wave_id: Optional[str] = None
    enemy_id: Optional[str] = None
    boss_id: Optional[str] = None
    pickup_id: Optional[str] = None

    def validate(self, strict: bool = False) -> None:
        validate_content_id(self.id)
        if self.type not in ALLOWED_OBJECTIVE_TYPES:
            raise ValueError(f"Invalid objective type '{self.type}'. Allowed: {ALLOWED_OBJECTIVE_TYPES}")
        
        import math
        # Numeric targets are positive where relevant
        if not isinstance(self.target, (int, float)) or isinstance(self.target, bool):
            raise ValueError("target must be a number.")
        if not math.isfinite(self.target):
            raise ValueError("target must be a finite number.")
        if self.target <= 0:
            raise ValueError("target must be a positive number.")

        if self.type == "complete_map":
            if not self.map_id:
                raise ValueError("complete_map objective type requires a map_id.")
            validate_content_id(self.map_id)
            if self.target != 1:
                raise ValueError("complete_map objectives currently support only target == 1.")
            if self.difficulty is not None:
                if self.difficulty not in {"easy", "medium", "hard"}:
                    raise ValueError(f"Invalid difficulty '{self.difficulty}'.")
        elif self.type == "defeat_enemy_type":
            if not self.enemy_id:
                raise ValueError("defeat_enemy_type objective type requires an enemy_id.")
            validate_content_id(self.enemy_id)
        elif self.type == "defeat_boss":
            if not self.boss_id:
                raise ValueError("defeat_boss objective type requires a boss_id.")
            validate_content_id(self.boss_id)
        elif self.type == "collect_pickup_type":
            if not self.pickup_id:
                raise ValueError("collect_pickup_type objective type requires a pickup_id.")
            if not isinstance(self.pickup_id, str) or not self.pickup_id:
                raise ValueError("pickup_id must be a non-empty string.")
            validate_content_id(self.pickup_id)
        elif self.type == "survive_seconds":
            pass
        elif self.type == "reach_score":
            if not isinstance(self.target, int):
                raise ValueError("target for reach_score must be an integer.")

    @classmethod
    def from_dict(cls, data: Dict[str, Any], strict: bool = False) -> "QuestObjective":
        if not isinstance(data, dict):
            raise ValueError("QuestObjective input must be a dictionary.")
        expected_fields = {
            "id", "type", "target", "map_id", "difficulty", "wave_id",
            "enemy_id", "boss_id", "pickup_id"
        }
        if strict:
            unknown = set(data.keys()) - expected_fields
            if unknown:
                raise ValueError(f"Unknown fields in quest objective: {unknown}")
        return cls(
            id=data.get("id"),
            type=data.get("type"),
            target=data.get("target"),
            map_id=data.get("map_id"),
            difficulty=data.get("difficulty"),
            wave_id=data.get("wave_id"),
            enemy_id=data.get("enemy_id"),
            boss_id=data.get("boss_id"),
            pickup_id=data.get("pickup_id")
        )

@dataclass(frozen=True)
class QuestDef:
    id: str
    display_name: str
    description: str
    objectives: List[QuestObjective]
    reward_ids: List[str]
    unlock_requirements: Dict[str, Any] = field(default_factory=dict)

    def validate(self, strict: bool = False) -> None:
        validate_content_id(self.id)
        if not self.display_name or not isinstance(self.display_name, str):
            raise ValueError("display_name must be a non-empty string.")
        if not isinstance(self.description, str):
            raise ValueError("description must be a string.")
        if not isinstance(self.objectives, list) or not self.objectives:
            raise ValueError("objectives must be a non-empty list of QuestObjective objects.")
        
        obj_ids = set()
        for obj in self.objectives:
            if not isinstance(obj, QuestObjective):
                raise TypeError("All objectives must be instances of QuestObjective.")
            obj.validate(strict)
            if obj.id in obj_ids:
                raise ValueError(f"Duplicate objective ID '{obj.id}' in quest '{self.id}'.")
            obj_ids.add(obj.id)

        if not isinstance(self.reward_ids, list):
            raise ValueError("reward_ids must be a list of strings.")
        for rid in self.reward_ids:
            if not isinstance(rid, str):
                raise ValueError("reward_ids entries must be strings.")
            validate_content_id(rid)

        if not isinstance(self.unlock_requirements, dict):
            raise ValueError("unlock_requirements must be a dictionary.")

    @classmethod
    def from_dict(cls, data: Dict[str, Any], strict: bool = False) -> "QuestDef":
        if not isinstance(data, dict):
            raise ValueError("QuestDef input must be a dictionary.")
        expected_fields = {"id", "display_name", "description", "objectives", "reward_ids", "unlock_requirements"}
        if strict:
            unknown = set(data.keys()) - expected_fields
            if unknown:
                raise ValueError(f"Unknown fields in quest definition: {unknown}")
        
        raw_objectives = data.get("objectives", [])
        if not isinstance(raw_objectives, list):
            raise ValueError("objectives field in quest definition must be a list.")
        for index, item in enumerate(raw_objectives):
            if not isinstance(item, dict):
                raise ValueError(f"Objective at index {index} must be a dictionary object.")
        objectives = [QuestObjective.from_dict(o, strict) for o in raw_objectives]
        
        return cls(
            id=data.get("id"),
            display_name=data.get("display_name"),
            description=data.get("description", ""),
            objectives=objectives,
            reward_ids=data.get("reward_ids", []),
            unlock_requirements=data.get("unlock_requirements", {})
        )
