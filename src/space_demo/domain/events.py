"""Event pack domain models for To Boldly Respawn."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from space_demo.domain.content_ids import validate_content_id


@dataclass(frozen=True)
class EventPackDef:
    """Content-defined event pack manifest.

    Phase 5I intentionally models only manifest metadata and content references.
    Runtime activation, stores, scheduling UI, and event-specific gameplay remain
    deferred.
    """

    id: str
    display_name: str
    description: str
    enabled: bool
    map_ids: List[str] = field(default_factory=list)
    quest_ids: List[str] = field(default_factory=list)
    story_ids: List[str] = field(default_factory=list)
    reward_ids: List[str] = field(default_factory=list)
    store_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None

    def validate(self, strict: bool = False) -> None:
        validate_content_id(self.id)
        if not self.display_name or not isinstance(self.display_name, str):
            raise ValueError("display_name must be a non-empty string.")
        if not isinstance(self.description, str):
            raise ValueError("description must be a string.")
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be a boolean.")

        for field_name in (
            "map_ids",
            "quest_ids",
            "story_ids",
            "reward_ids",
            "store_ids",
            "tags",
        ):
            values = getattr(self, field_name)
            if not isinstance(values, list):
                raise ValueError(f"{field_name} must be a list.")
            for value in values:
                if not isinstance(value, str) or not value:
                    raise ValueError(f"{field_name} entries must be non-empty strings.")
                validate_content_id(value)

        if self.starts_at is not None and not isinstance(self.starts_at, str):
            raise ValueError("starts_at must be a string or null.")
        if self.ends_at is not None and not isinstance(self.ends_at, str):
            raise ValueError("ends_at must be a string or null.")

    @classmethod
    def from_dict(cls, data: Dict[str, Any], strict: bool = False) -> "EventPackDef":
        if not isinstance(data, dict):
            raise ValueError("EventPackDef input must be a dictionary.")

        expected = {
            "id",
            "display_name",
            "description",
            "enabled",
            "map_ids",
            "quest_ids",
            "story_ids",
            "reward_ids",
            "store_ids",
            "tags",
            "starts_at",
            "ends_at",
        }
        if strict:
            unknown = set(data.keys()) - expected
            if unknown:
                raise ValueError(f"Unknown fields in event pack definition: {unknown}")
            required = {"id", "display_name", "description", "enabled"}
            missing = required - set(data.keys())
            if missing:
                raise ValueError(f"Missing required fields in event pack definition: {missing}")

        return cls(
            id=data.get("id"),
            display_name=data.get("display_name"),
            description=data.get("description", ""),
            enabled=data.get("enabled", False),
            map_ids=list(data.get("map_ids", [])),
            quest_ids=list(data.get("quest_ids", [])),
            story_ids=list(data.get("story_ids", [])),
            reward_ids=list(data.get("reward_ids", [])),
            store_ids=list(data.get("store_ids", [])),
            tags=list(data.get("tags", [])),
            starts_at=data.get("starts_at"),
            ends_at=data.get("ends_at"),
        )
