# Reward Domain Models for To Boldly Respawn

from dataclasses import dataclass
from typing import Any, Dict, Optional
from space_demo.domain.content_ids import validate_content_id

ALLOWED_REWARD_TYPES = {"resource_grant", "ship_unlock", "equipment_unlock"}

@dataclass(frozen=True)
class RewardDef:
    id: str
    display_name: str
    type: str
    unique: bool
    resource_id: Optional[str] = None
    amount: Optional[int] = None
    target_id: Optional[str] = None

    def validate(self, strict: bool = False) -> None:
        """Validates the reward definition. Raises ValueError on violation."""
        validate_content_id(self.id)
        if not self.display_name or not isinstance(self.display_name, str):
            raise ValueError("display_name must be a non-empty string.")
        
        if self.type not in ALLOWED_REWARD_TYPES:
            raise ValueError(f"Invalid reward type '{self.type}'. Allowed types: {ALLOWED_REWARD_TYPES}")

        if not isinstance(self.unique, bool):
            raise ValueError("unique must be a boolean.")

        if self.type == "resource_grant":
            if not self.resource_id:
                raise ValueError("resource_grant reward type requires a resource_id.")
            validate_content_id(self.resource_id)
            if self.amount is None or not isinstance(self.amount, int) or self.amount < 0:
                raise ValueError("resource_grant reward type requires a non-negative integer amount.")
        elif self.type in ("ship_unlock", "equipment_unlock"):
            if not self.target_id:
                raise ValueError(f"{self.type} reward type requires a target_id.")
            validate_content_id(self.target_id)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], strict: bool = False) -> "RewardDef":
        """Builds a RewardDef from a dictionary."""
        expected_fields = {
            "id", "display_name", "type", "unique", "resource_id", "amount", "target_id"
        }
        if strict:
            unknown = set(data.keys()) - expected_fields
            if unknown:
                raise ValueError(f"Unknown fields in reward definition: {unknown}")
            
            base_required = {"id", "display_name", "type", "unique"}
            missing = base_required - set(data.keys())
            if missing:
                raise ValueError(f"Missing required fields in reward definition: {missing}")
            
            rtype = data.get("type")
            if rtype == "resource_grant":
                missing_cond = {"resource_id", "amount"} - set(data.keys())
                if missing_cond:
                    raise ValueError(f"Missing resource_grant fields in reward: {missing_cond}")
            elif rtype in ("ship_unlock", "equipment_unlock"):
                if "target_id" not in data:
                    raise ValueError(f"Missing target_id in {rtype} reward")

        return cls(
            id=data.get("id"),
            display_name=data.get("display_name"),
            type=data.get("type"),
            unique=data.get("unique"),
            resource_id=data.get("resource_id"),
            amount=data.get("amount"),
            target_id=data.get("target_id"),
        )
