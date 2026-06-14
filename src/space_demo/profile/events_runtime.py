"""Pure event pack runtime adapter for Phase 5I."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

from space_demo.data.loader import get_data_dir
from space_demo.domain.events import EventPackDef


PathLike = Optional[Union[Path, str]]


class EventRuntimeAdapter:
    """Load and resolve content-defined event pack manifests.

    Phase 5I does not activate events.  This adapter only loads, validates, and
    exposes enabled event packs for future systems.
    """

    def __init__(self, events_path: PathLike = None):
        self.events_path = Path(events_path) if events_path else Path(get_data_dir()) / "events.json"

    def load_event_pack_defs(self) -> Dict[str, EventPackDef]:
        if not self.events_path.exists():
            raise FileNotFoundError(f"events.json not found at {self.events_path}")

        try:
            data = json.loads(self.events_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError(f"Failed to parse events.json: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError("Root of events.json must be a JSON object.")
        if "event_packs" not in data:
            raise ValueError("Root of events.json is missing required field 'event_packs'.")
        if not isinstance(data["event_packs"], list):
            raise ValueError("'event_packs' field in events.json must be a list.")

        event_packs: Dict[str, EventPackDef] = {}
        for index, item in enumerate(data["event_packs"]):
            try:
                event_pack = EventPackDef.from_dict(item, strict=True)
                event_pack.validate(strict=True)
                if event_pack.id in event_packs:
                    raise ValueError(f"Duplicate event pack ID found: {event_pack.id}")
                event_packs[event_pack.id] = event_pack
            except Exception as exc:
                raise ValueError(f"Invalid event pack definition at index {index}: {exc}") from exc
        return event_packs

    def enabled_event_packs(self) -> List[EventPackDef]:
        return [event for event in self.load_event_pack_defs().values() if event.enabled]

    def resolve_event_pack(self, event_pack_id: str) -> EventPackDef:
        event_packs = self.load_event_pack_defs()
        if event_pack_id not in event_packs:
            raise ValueError(f"Event pack ID '{event_pack_id}' does not exist in events.json.")
        return event_packs[event_pack_id]
