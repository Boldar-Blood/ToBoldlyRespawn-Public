# Content Validation Logic - To Boldly Respawn

import os
import json
from typing import Any, Dict, List
from space_demo.domain import (
    ShipDef,
    MapDef,
    RewardDef,
    PlayerProfile,
    EquipmentDef,
    WaveDef,
    StoryDef,
    QuestDef,
    EventPackDef,
)


class ContentValidationError(ValueError):
    """Custom error representing a content validation failure."""
    pass


def load_json_file(file_path: str) -> Any:
    """Loads a JSON file, raising ContentValidationError on failure."""
    if not os.path.exists(file_path):
        if os.path.basename(file_path) == "events.json":
            return {"schema_version": 1, "event_packs": []}
        raise ContentValidationError(f"File not found: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise ContentValidationError(f"Failed to parse JSON from {file_path}: {e}")


class GameContentValidator:
    def __init__(self, data_root: str, strict: bool = False):
        self.data_root = data_root
        self.strict = strict
        self.ships_path = os.path.join(data_root, "player_ships.json")
        self.runtime_ships_path = os.path.join(data_root, "ships.json")
        self.maps_path = os.path.join(data_root, "maps.json")
        self.rewards_path = os.path.join(data_root, "rewards.json")
        self.profile_path = os.path.join(data_root, "default_profile.json")
        self.waves_path = os.path.join(data_root, "waves.json")
        self.equipment_path = os.path.join(data_root, "equipment.json")
        self.story_path = os.path.join(data_root, "story.json")
        self.quests_path = os.path.join(data_root, "quests.json")
        self.events_path = os.path.join(data_root, "events.json")

    def validate_all(self) -> None:
        """Validates all game content and cross-references.

        Raises ContentValidationError if any check fails.
        """
        # 1. Load files
        ships_data = load_json_file(self.ships_path)
        maps_data = load_json_file(self.maps_path)
        rewards_data = load_json_file(self.rewards_path)
        profile_data = load_json_file(self.profile_path)
        waves_data = load_json_file(self.waves_path)
        runtime_ships_data = load_json_file(self.runtime_ships_path)
        equipment_data = load_json_file(self.equipment_path)
        story_data = load_json_file(self.story_path)
        quests_data = load_json_file(self.quests_path)
        events_data = load_json_file(self.events_path)

        # Strict checks on root keys
        if self.strict:
            if not isinstance(ships_data, dict) or set(ships_data.keys()) - {"schema_version", "ships"}:
                raise ContentValidationError("player_ships.json has unknown root fields under strict mode.")
            if "schema_version" not in ships_data:
                raise ContentValidationError("player_ships.json is missing required root field 'schema_version' under strict mode.")
            if not isinstance(ships_data["schema_version"], int) or ships_data["schema_version"] <= 0:
                raise ContentValidationError("player_ships.json schema_version must be a positive integer under strict mode.")

            if not isinstance(maps_data, dict) or set(maps_data.keys()) - {"schema_version", "maps"}:
                raise ContentValidationError("maps.json has unknown root fields under strict mode.")
            if "schema_version" not in maps_data:
                raise ContentValidationError("maps.json is missing required root field 'schema_version' under strict mode.")
            if not isinstance(maps_data["schema_version"], int) or maps_data["schema_version"] <= 0:
                raise ContentValidationError("maps.json schema_version must be a positive integer under strict mode.")

            if not isinstance(rewards_data, dict) or set(rewards_data.keys()) - {"schema_version", "rewards"}:
                raise ContentValidationError("rewards.json has unknown root fields under strict mode.")
            if "schema_version" not in rewards_data:
                raise ContentValidationError("rewards.json is missing required root field 'schema_version' under strict mode.")
            if not isinstance(rewards_data["schema_version"], int) or rewards_data["schema_version"] <= 0:
                raise ContentValidationError("rewards.json schema_version must be a positive integer under strict mode.")

            if not isinstance(equipment_data, dict) or set(equipment_data.keys()) - {"schema_version", "equipment"}:
                raise ContentValidationError("equipment.json has unknown root fields under strict mode.")
            if "schema_version" not in equipment_data:
                raise ContentValidationError("equipment.json is missing required root field 'schema_version' under strict mode.")
            if not isinstance(equipment_data["schema_version"], int) or equipment_data["schema_version"] <= 0:
                raise ContentValidationError("equipment.json schema_version must be a positive integer under strict mode.")

            if not isinstance(story_data, dict) or set(story_data.keys()) - {"schema_version", "stories"}:
                raise ContentValidationError("story.json has unknown root fields under strict mode.")
            if "schema_version" not in story_data:
                raise ContentValidationError("story.json is missing required root field 'schema_version' under strict mode.")
            if not isinstance(story_data["schema_version"], int) or story_data["schema_version"] <= 0:
                raise ContentValidationError("story.json schema_version must be a positive integer under strict mode.")

            if not isinstance(quests_data, dict) or set(quests_data.keys()) - {"schema_version", "quests"}:
                raise ContentValidationError("quests.json has unknown root fields under strict mode.")
            if "schema_version" not in quests_data:
                raise ContentValidationError("quests.json is missing required root field 'schema_version' under strict mode.")
            if not isinstance(quests_data["schema_version"], int) or quests_data["schema_version"] <= 0:
                raise ContentValidationError("quests.json schema_version must be a positive integer under strict mode.")

            if not isinstance(events_data, dict) or set(events_data.keys()) - {"schema_version", "event_packs"}:
                raise ContentValidationError("events.json has unknown root fields under strict mode.")
            if "schema_version" not in events_data:
                raise ContentValidationError("events.json is missing required root field 'schema_version' under strict mode.")
            if not isinstance(events_data["schema_version"], int) or events_data["schema_version"] <= 0:
                raise ContentValidationError("events.json schema_version must be a positive integer under strict mode.")

        # 2. Parse and validate individual lists
        ships = self._parse_ships(ships_data)
        rewards = self._parse_rewards(rewards_data)
        maps = self._parse_maps(maps_data)
        profile = self._parse_profile(profile_data)
        equipment = self._parse_equipment(equipment_data)
        waves = self._parse_waves(waves_data)
        stories = self._parse_story(story_data)
        quests = self._parse_quests(quests_data)
        event_packs = self._parse_events(events_data)

        # 3. Cross-validation: unique IDs
        ship_ids = self._check_duplicates(ships, "ship")
        reward_ids = self._check_duplicates(rewards, "reward")
        map_ids = self._check_duplicates(maps, "map")
        eq_ids = self._check_duplicates(equipment, "equipment")
        story_ids = self._check_duplicates(stories, "story")
        quest_ids = self._check_duplicates(quests, "quest")
        self._check_duplicates(event_packs, "event pack")

        # 4. Cross-validate Map references
        self._cross_validate_maps(maps, reward_ids, waves_data, runtime_ships_data)
        self._cross_validate_waves(waves, runtime_ships_data)

        # 5. Cross-validate Profile references
        ships_by_id = {s.id: s for s in ships}
        eq_by_id = {eq.id: eq for eq in equipment}
        self._cross_validate_profile(profile, ships_by_id, eq_by_id, reward_ids, map_ids)

        # 6. Cross-validate Story, Quest, and Event references
        self._cross_validate_stories(stories, reward_ids, maps_data, waves_data)
        self._cross_validate_quests(quests, reward_ids, maps_data, runtime_ships_data)
        self._cross_validate_events(event_packs, map_ids, quest_ids, story_ids, reward_ids)

    def _parse_ships(self, data: Dict[str, Any]) -> List[ShipDef]:
        if "ships" not in data or not isinstance(data["ships"], list):
            raise ContentValidationError("Missing or invalid 'ships' list in player_ships.json.")

        ship_defs = []
        for index, item in enumerate(data["ships"]):
            if not isinstance(item, dict):
                raise ContentValidationError(f"Ship definition at index {index} is not an object.")
            try:
                ship_def = ShipDef.from_dict(item, strict=self.strict)
                ship_def.validate(strict=self.strict)
                ship_defs.append(ship_def)
            except ValueError as e:
                raise ContentValidationError(f"Invalid ship definition at index {index}: {e}")
        return ship_defs

    def _parse_rewards(self, data: Dict[str, Any]) -> List[RewardDef]:
        if "rewards" not in data or not isinstance(data["rewards"], list):
            raise ContentValidationError("Missing or invalid 'rewards' list in rewards.json.")

        reward_defs = []
        for index, item in enumerate(data["rewards"]):
            if not isinstance(item, dict):
                raise ContentValidationError(f"Reward definition at index {index} is not an object.")
            try:
                reward_def = RewardDef.from_dict(item, strict=self.strict)
                reward_def.validate(strict=self.strict)
                reward_defs.append(reward_def)
            except ValueError as e:
                raise ContentValidationError(f"Invalid reward definition at index {index}: {e}")
        return reward_defs

    def _parse_maps(self, data: Dict[str, Any]) -> List[MapDef]:
        if "maps" not in data or not isinstance(data["maps"], list):
            raise ContentValidationError("Missing or invalid 'maps' list in maps.json.")

        map_defs = []
        for index, item in enumerate(data["maps"]):
            if not isinstance(item, dict):
                raise ContentValidationError(f"Map definition at index {index} is not an object.")
            try:
                map_def = MapDef.from_dict(item, strict=self.strict)
                map_def.validate(strict=self.strict)
                map_defs.append(map_def)
            except ValueError as e:
                raise ContentValidationError(f"Invalid map definition at index {index}: {e}")
        return map_defs

    def _parse_profile(self, data: Dict[str, Any]) -> PlayerProfile:
        if not isinstance(data, dict):
            raise ContentValidationError("Profile data is not a valid dictionary object.")
        try:
            profile = PlayerProfile.from_dict(data, strict=self.strict)
            profile.validate(strict=self.strict)
            return profile
        except ValueError as e:
            raise ContentValidationError(f"Invalid default profile: {e}")

    def _check_duplicates(self, defs: List[Any], name: str) -> set:
        seen = set()
        for item in defs:
            if item.id in seen:
                raise ContentValidationError(f"Duplicate {name} ID found: '{item.id}'")
            seen.add(item.id)
        return seen

    def _cross_validate_maps(self, maps: List[MapDef], reward_ids: set, waves_data: Dict[str, Any], runtime_ships_data: Dict[str, Any]) -> None:
        if not isinstance(waves_data, dict):
            raise ContentValidationError("waves.json is not a valid dictionary object.")
        if not isinstance(runtime_ships_data, dict):
            raise ContentValidationError("ships.json is not a valid dictionary object.")

        valid_entity_keys = set(runtime_ships_data.keys())

        for m in maps:
            for w in m.waves:
                if w not in waves_data:
                    raise ContentValidationError(
                        f"Map '{m.id}' references wave '{w}' which does not exist in waves.json."
                    )

            for hook, r_list in m.rewards.items():
                for r_id in r_list:
                    if r_id not in reward_ids:
                        raise ContentValidationError(
                            f"Map '{m.id}' references reward '{r_id}' under '{hook}', "
                            f"but '{r_id}' is not defined in rewards.json."
                        )

            for enemy in m.enemy_pool:
                if enemy not in valid_entity_keys:
                    raise ContentValidationError(
                        f"Map '{m.id}' references enemy '{enemy}' in enemy_pool, "
                        f"which is not defined in ships.json."
                    )

            if m.boss is not None:
                if m.boss not in valid_entity_keys:
                    raise ContentValidationError(
                        f"Map '{m.id}' references boss '{m.boss}', "
                        f"which is not defined in ships.json."
                    )

    def _cross_validate_profile(self, profile: PlayerProfile, ships_by_id: Dict[str, Any], eq_by_id: Dict[str, Any], reward_ids: set, map_ids: set) -> None:
        ship_ids = set(ships_by_id.keys())
        eq_ids = set(eq_by_id.keys())

        if profile.selected_ship_id not in ship_ids:
            raise ContentValidationError(
                f"Player profile selected_ship_id '{profile.selected_ship_id}' "
                f"is not a defined ship in player_ships.json."
            )

        for ship_id in profile.unlocked_ships:
            if ship_id not in ship_ids:
                raise ContentValidationError(
                    f"Player profile unlocked_ships list contains '{ship_id}' "
                    f"which is not a defined ship in player_ships.json."
                )

        owned_eq = profile.inventory.get("equipment", [])
        for eq_id in owned_eq:
            if eq_id not in eq_ids:
                raise ContentValidationError(
                    f"Player profile owned equipment '{eq_id}' is not defined in equipment.json."
                )

        equipped_by_ship = profile.inventory.get("equipped_by_ship", {})
        for ship_id, slots in equipped_by_ship.items():
            if ship_id not in ship_ids:
                raise ContentValidationError(
                    f"Player profile equipped_by_ship contains undefined ship ID '{ship_id}'."
                )
            ship_def = ships_by_id[ship_id]
            for slot_type, eq_id in slots.items():
                if slot_type not in ship_def.equipment_slots:
                    raise ContentValidationError(
                        f"Slot type '{slot_type}' is not a valid equipment slot on ship '{ship_id}'."
                    )
                if eq_id is not None:
                    if eq_id not in eq_ids:
                        raise ContentValidationError(
                            f"Equipped item '{eq_id}' in slot '{slot_type}' for ship '{ship_id}' does not exist in equipment.json."
                        )
                    if eq_id not in owned_eq:
                        raise ContentValidationError(
                            f"Equipped item '{eq_id}' in slot '{slot_type}' for ship '{ship_id}' is not owned in the profile."
                        )
                    eq_def = eq_by_id[eq_id]
                    if eq_def.slot_type != slot_type:
                        raise ContentValidationError(
                            f"Equipped item '{eq_id}' defined slot_type '{eq_def.slot_type}' "
                            f"does not match slot '{slot_type}' on ship '{ship_id}'."
                        )

        awarded_unique_rewards = profile.progression.get("awarded_unique_rewards", [])
        for rid in awarded_unique_rewards:
            if rid not in reward_ids:
                raise ContentValidationError(
                    f"Player profile contains unique reward '{rid}' under 'awarded_unique_rewards' "
                    f"which is not defined in rewards.json."
                )

        completed_maps = profile.progression.get("completed_maps", {})
        for mid in completed_maps.keys():
            if mid not in map_ids:
                raise ContentValidationError(
                    f"Player profile contains completed map ID '{mid}' "
                    f"which is not defined in maps.json."
                )

    def _parse_equipment(self, data: Dict[str, Any]) -> List[EquipmentDef]:
        if "equipment" not in data or not isinstance(data["equipment"], list):
            raise ContentValidationError("Missing or invalid 'equipment' list in equipment.json.")

        eq_defs = []
        for index, item in enumerate(data["equipment"]):
            if not isinstance(item, dict):
                raise ContentValidationError(f"Equipment definition at index {index} is not an object.")
            try:
                eq_def = EquipmentDef.from_dict(item, strict=self.strict)
                eq_def.validate(strict=self.strict)
                eq_defs.append(eq_def)
            except ValueError as e:
                raise ContentValidationError(f"Invalid equipment definition at index {index}: {e}")
        return eq_defs

    def _parse_waves(self, data: Dict[str, Any]) -> List[WaveDef]:
        if not isinstance(data, dict):
            raise ContentValidationError("waves.json is not a valid dictionary object.")

        wave_defs = []
        for wave_id, item in data.items():
            if wave_id == "schema_version":
                continue
            if not isinstance(item, dict):
                raise ContentValidationError(f"Wave definition for '{wave_id}' is not an object.")
            try:
                wave_def = WaveDef.from_dict(wave_id, item, strict=self.strict)
                wave_def.validate(strict=self.strict)
                wave_defs.append(wave_def)
            except ValueError as e:
                raise ContentValidationError(f"Invalid wave definition for '{wave_id}': {e}")
        return wave_defs

    def _cross_validate_waves(self, waves: List[WaveDef], runtime_ships_data: Dict[str, Any]) -> None:
        if not isinstance(runtime_ships_data, dict):
            raise ContentValidationError("ships.json is not a valid dictionary object.")

        valid_entity_keys = set(runtime_ships_data.keys())
        for w in waves:
            for escort in w.escorts:
                if escort not in valid_entity_keys:
                    raise ContentValidationError(
                        f"Wave '{w.id}' references unknown enemy/entity ID '{escort}' in escorts, "
                        f"which is not defined in ships.json."
                    )

    def _parse_story(self, data: Dict[str, Any]) -> List[StoryDef]:
        if not isinstance(data, dict):
            raise ContentValidationError("Root of story.json must be a JSON object.")
        if "stories" not in data or not isinstance(data["stories"], list):
            raise ContentValidationError("Missing or invalid 'stories' list in story.json.")

        story_defs = []
        for index, item in enumerate(data["stories"]):
            if not isinstance(item, dict):
                raise ContentValidationError(f"Story definition at index {index} is not an object.")
            try:
                story_def = StoryDef.from_dict(item, strict=self.strict)
                story_def.validate(strict=self.strict)
                story_defs.append(story_def)
            except ValueError as e:
                raise ContentValidationError(f"Invalid story definition at index {index}: {e}")
        return story_defs

    def _parse_quests(self, data: Dict[str, Any]) -> List[QuestDef]:
        if not isinstance(data, dict):
            raise ContentValidationError("Root of quests.json must be a JSON object.")
        if "quests" not in data or not isinstance(data["quests"], list):
            raise ContentValidationError("Missing or invalid 'quests' list in quests.json.")

        quest_defs = []
        for index, item in enumerate(data["quests"]):
            if not isinstance(item, dict):
                raise ContentValidationError(f"Quest definition at index {index} is not an object.")
            try:
                quest_def = QuestDef.from_dict(item, strict=self.strict)
                quest_def.validate(strict=self.strict)
                quest_defs.append(quest_def)
            except ValueError as e:
                raise ContentValidationError(f"Invalid quest definition at index {index}: {e}")
        return quest_defs

    def _parse_events(self, data: Dict[str, Any]) -> List[EventPackDef]:
        if not isinstance(data, dict):
            raise ContentValidationError("Root of events.json must be a JSON object.")
        if "event_packs" not in data or not isinstance(data["event_packs"], list):
            raise ContentValidationError("Missing or invalid 'event_packs' list in events.json.")

        event_defs = []
        for index, item in enumerate(data["event_packs"]):
            if not isinstance(item, dict):
                raise ContentValidationError(f"Event pack definition at index {index} is not an object.")
            try:
                event_def = EventPackDef.from_dict(item, strict=self.strict)
                event_def.validate(strict=self.strict)
                event_defs.append(event_def)
            except ValueError as e:
                raise ContentValidationError(f"Invalid event pack definition at index {index}: {e}")
        return event_defs

    def _cross_validate_stories(self, stories: List[StoryDef], reward_ids: set, maps_data: Dict[str, Any], waves_data: Dict[str, Any]) -> None:
        if not isinstance(maps_data, dict) or "maps" not in maps_data:
            raise ContentValidationError("maps.json is invalid or not loaded.")
        if not isinstance(waves_data, dict):
            raise ContentValidationError("waves.json is invalid or not loaded.")

        map_defs = {m["id"]: m for m in maps_data.get("maps", []) if isinstance(m, dict) and "id" in m}

        for story in stories:
            for node in story.nodes:
                if node.map_id is not None:
                    if node.map_id not in map_defs:
                        raise ContentValidationError(
                            f"Story '{story.id}' node '{node.id}' references map_id '{node.map_id}' "
                            f"which does not exist in maps.json."
                        )
                    if node.wave_id is not None:
                        if node.wave_id not in waves_data:
                            raise ContentValidationError(
                                f"Story '{story.id}' node '{node.id}' references wave_id '{node.wave_id}' "
                                f"which does not exist in waves.json."
                            )
                        map_waves = map_defs[node.map_id].get("waves", [])
                        if node.wave_id not in map_waves:
                            raise ContentValidationError(
                                f"Story '{story.id}' node '{node.id}' references wave_id '{node.wave_id}' "
                                f"which is not part of map '{node.map_id}' waves list: {map_waves}."
                            )

                for rid in node.reward_ids:
                    if rid not in reward_ids:
                        raise ContentValidationError(
                            f"Story '{story.id}' node '{node.id}' references reward '{rid}' "
                            f"which does not exist in rewards.json."
                        )
                for choice in node.choices:
                    for rid in choice.reward_ids:
                        if rid not in reward_ids:
                            raise ContentValidationError(
                                f"Story '{story.id}' node '{node.id}' choice references reward '{rid}' "
                                f"which does not exist in rewards.json."
                            )

    def _cross_validate_quests(self, quests: List[QuestDef], reward_ids: set, maps_data: Dict[str, Any], runtime_ships_data: Dict[str, Any]) -> None:
        if not isinstance(maps_data, dict) or "maps" not in maps_data:
            raise ContentValidationError("maps.json is invalid or not loaded.")
        if not isinstance(runtime_ships_data, dict):
            raise ContentValidationError("ships.json is invalid or not loaded.")

        map_ids = {m["id"] for m in maps_data.get("maps", []) if isinstance(m, dict) and "id" in m}
        valid_entity_keys = set(runtime_ships_data.keys())

        for quest in quests:
            for rid in quest.reward_ids:
                if rid not in reward_ids:
                    raise ContentValidationError(
                        f"Quest '{quest.id}' references reward '{rid}' "
                        f"which does not exist in rewards.json."
                    )
            for obj in quest.objectives:
                if obj.map_id is not None:
                    if obj.map_id not in map_ids:
                        raise ContentValidationError(
                            f"Quest '{quest.id}' objective '{obj.id}' references map_id '{obj.map_id}' "
                            f"which does not exist in maps.json."
                        )
                if obj.enemy_id is not None:
                    if obj.enemy_id not in valid_entity_keys:
                        raise ContentValidationError(
                            f"Quest '{quest.id}' objective '{obj.id}' references enemy_id '{obj.enemy_id}' "
                            f"which does not exist in ships.json."
                        )
                if obj.boss_id is not None:
                    if obj.boss_id not in valid_entity_keys:
                        raise ContentValidationError(
                            f"Quest '{quest.id}' objective '{obj.id}' references boss_id '{obj.boss_id}' "
                            f"which does not exist in ships.json."
                        )

    def _cross_validate_events(self, event_packs: List[EventPackDef], map_ids: set, quest_ids: set, story_ids: set, reward_ids: set) -> None:
        for event_pack in event_packs:
            if not event_pack.enabled:
                continue
            self._require_existing_ids(event_pack.id, "map", event_pack.map_ids, map_ids)
            self._require_existing_ids(event_pack.id, "quest", event_pack.quest_ids, quest_ids)
            self._require_existing_ids(event_pack.id, "story", event_pack.story_ids, story_ids)
            self._require_existing_ids(event_pack.id, "reward", event_pack.reward_ids, reward_ids)
            if event_pack.store_ids:
                raise ContentValidationError(
                    f"Enabled event pack '{event_pack.id}' references store_ids, but store definitions are not implemented yet."
                )

    def _require_existing_ids(self, event_pack_id: str, ref_type: str, values: List[str], valid_values: set) -> None:
        for value in values:
            if value not in valid_values:
                raise ContentValidationError(
                    f"Enabled event pack '{event_pack_id}' references {ref_type} '{value}' which is not defined."
                )
