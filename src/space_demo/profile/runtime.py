# Runtime Ship Resolver and Adapter for To Boldly Respawn

import json
from pathlib import Path
from typing import Dict, Optional, Union, List, Any
from dataclasses import dataclass
from space_demo.data.loader import get_data_dir
from space_demo.domain import (
    ShipDef, PlayerProfile, MapDef, EquipmentDef, RewardDef, WaveDef,
    StoryChoice, StoryNode, StoryDef, QuestObjective, QuestDef
)
from space_demo.profile.migration import CURRENT_SCHEMA_VERSION

class ShipRuntimeAdapter:
    """
    Resolves the selected_ship_id from the PlayerProfile to a ShipDef from player_ships.json.
    Performs runtime cross-validation checks.
    """
    def __init__(self, player_ships_path: Optional[Union[Path, str]] = None):
        if player_ships_path:
            self.player_ships_path = Path(player_ships_path)
        else:
            self.player_ships_path = Path(get_data_dir()) / "player_ships.json"

    def load_ships_defs(self) -> Dict[str, ShipDef]:
        """Loads and validates all ship definitions from player_ships.json."""
        if not self.player_ships_path.exists():
            raise FileNotFoundError(f"player_ships.json not found at {self.player_ships_path}")
        
        try:
            with open(self.player_ships_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse player_ships.json: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("Root of player_ships.json must be a JSON object.")
        if "ships" not in data or not isinstance(data["ships"], list):
            raise ValueError("Invalid player_ships.json format: Missing or invalid 'ships' list.")

        ship_defs = {}
        for index, item in enumerate(data["ships"]):
            try:
                ship_def = ShipDef.from_dict(item, strict=True)
                ship_def.validate(strict=True)
                if ship_def.id in ship_defs:
                    raise ValueError(f"Duplicate ship ID found in definitions: {ship_def.id}")
                ship_defs[ship_def.id] = ship_def
            except Exception as e:
                raise ValueError(f"Invalid ship definition at index {index}: {e}") from e
        return ship_defs

    def resolve_selected_ship(self, profile: PlayerProfile) -> ShipDef:
        """
        Resolves the selected ship ID from the profile to a ShipDef.
        Performs runtime validation checks:
        - selected_ship_id exists in definitions
        - selected_ship_id is unlocked
        - all unlocked_ships exist in definitions
        """
        if not isinstance(profile, PlayerProfile):
            raise TypeError("profile must be a PlayerProfile instance")
        profile.validate(strict=True)

        ships_defs = self.load_ships_defs()

        if profile.selected_ship_id not in ships_defs:
            raise ValueError(
                f"Selected ship ID '{profile.selected_ship_id}' does not exist in ship definitions."
            )

        if profile.selected_ship_id not in profile.unlocked_ships:
            raise ValueError(
                f"Selected ship ID '{profile.selected_ship_id}' is not unlocked in the player profile."
            )

        # Validate that all unlocked_ships in profile exist in definitions
        for ship_id in profile.unlocked_ships:
            if ship_id not in ships_defs:
                raise ValueError(
                    f"Unlocked ship ID '{ship_id}' in player profile does not exist in ship definitions."
                )

        return ships_defs[profile.selected_ship_id]


class MapRuntimeAdapter:
    """
    Resolves map definitions from maps.json.
    Performs runtime validation checks.
    """
    def __init__(self, maps_path: Optional[Union[Path, str]] = None):
        if maps_path:
            self.maps_path = Path(maps_path)
        else:
            self.maps_path = Path(get_data_dir()) / "maps.json"

    def load_map_defs(self) -> Dict[str, MapDef]:
        """Loads and validates all map definitions from maps.json."""
        if not self.maps_path.exists():
            raise FileNotFoundError(f"maps.json not found at {self.maps_path}")
        
        try:
            with open(self.maps_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse maps.json: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("Root of maps.json must be a JSON object.")
        if "maps" not in data or not isinstance(data["maps"], list):
            raise ValueError("Invalid maps.json format: Missing or invalid 'maps' list.")

        map_defs = {}
        for index, item in enumerate(data["maps"]):
            try:
                map_def = MapDef.from_dict(item, strict=True)
                map_def.validate(strict=True)
                if map_def.id in map_defs:
                    raise ValueError(f"Duplicate map ID found in definitions: {map_def.id}")
                map_defs[map_def.id] = map_def
            except Exception as e:
                raise ValueError(f"Invalid map definition at index {index}: {e}") from e
        return map_defs

    def resolve_map(self, map_id: str) -> MapDef:
        """Resolves map_id to a MapDef. Raises ValueError if invalid."""
        map_defs = self.load_map_defs()
        if map_id not in map_defs:
            raise ValueError(
                f"Map ID '{map_id}' does not exist in map definitions."
            )
        return map_defs[map_id]

    def resolve_map_runtime_config(
        self,
        map_id: str,
        waves_path: Optional[Union[Path, str]] = None,
        ships_path: Optional[Union[Path, str]] = None
    ) -> tuple[MapDef, Dict[str, WaveDef]]:
        """
        Resolves map_id to a MapDef, loads and resolves all referenced waves from waves.json,
        and cross-validates waves against ships.json (which contains the allowed enemy/boss entities).
        """
        map_def = self.resolve_map(map_id)
        
        # Load wave definitions
        wave_adapter = WaveRuntimeAdapter(waves_path=waves_path)
        wave_defs = wave_adapter.load_wave_defs()
        
        # Load ships config to check for valid escort and boss entity IDs
        if not ships_path:
            ships_path = Path(get_data_dir()) / "ships.json"
        else:
            ships_path = Path(ships_path)
            
        if not ships_path.exists():
            raise FileNotFoundError(f"ships.json not found at {ships_path}")
            
        try:
            with open(ships_path, "r", encoding="utf-8") as f:
                ships_data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse ships.json: {e}") from e
            
        if not isinstance(ships_data, dict):
            raise ValueError("Root of ships.json must be a JSON object.")
            
        valid_entity_ids = set(ships_data.keys())
        
        # Validate boss ID if present
        if map_def.boss is not None and map_def.boss not in valid_entity_ids:
            raise ValueError(f"Map boss ID '{map_def.boss}' is not a valid entity defined in ships.json.")
            
        resolved_wave_defs = {}
        for wave_id in map_def.waves:
            if wave_id not in wave_defs:
                raise ValueError(f"Wave ID '{wave_id}' referenced by map '{map_id}' does not exist in wave definitions.")
            wave_def = wave_defs[wave_id]
            
            # Cross-validate escorts
            for escort in wave_def.escorts:
                if escort not in valid_entity_ids:
                    raise ValueError(f"Wave '{wave_id}' references unknown enemy/entity ID '{escort}' in escorts, which is not defined in ships.json.")
            
            resolved_wave_defs[wave_id] = wave_def
            
        return map_def, resolved_wave_defs


class WaveRuntimeAdapter:
    """
    Loads and validates wave definitions from waves.json.
    Performs runtime validation checks.
    """
    def __init__(self, waves_path: Optional[Union[Path, str]] = None):
        if waves_path:
            self.waves_path = Path(waves_path)
        else:
            self.waves_path = Path(get_data_dir()) / "waves.json"

    def load_wave_defs(self) -> Dict[str, WaveDef]:
        """Loads and validates all wave definitions from waves.json."""
        if not self.waves_path.exists():
            raise FileNotFoundError(f"waves.json not found at {self.waves_path}")
        
        try:
            with open(self.waves_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse waves.json: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("Root of waves.json must be a JSON object.")

        wave_defs = {}
        for wave_id, item in data.items():
            if wave_id == "schema_version":
                continue
            if not isinstance(item, dict):
                raise ValueError(f"Wave definition for '{wave_id}' must be a JSON object.")
            try:
                wave_def = WaveDef.from_dict(wave_id, item, strict=True)
                wave_def.validate(strict=True)
                wave_defs[wave_id] = wave_def
            except Exception as e:
                raise ValueError(f"Invalid wave definition for '{wave_id}': {e}") from e
        return wave_defs

    def resolve_wave(self, wave_id: str) -> WaveDef:
        """Resolves wave_id to a WaveDef. Raises ValueError if invalid."""
        wave_defs = self.load_wave_defs()
        if wave_id not in wave_defs:
            raise ValueError(
                f"Wave ID '{wave_id}' does not exist in wave definitions."
            )
        return wave_defs[wave_id]


class EquipmentRuntimeAdapter:
    """
    Loads and validates equipment definitions from equipment.json.
    """
    def __init__(self, equipment_path: Optional[Union[Path, str]] = None):
        if equipment_path:
            self.equipment_path = Path(equipment_path)
        else:
            self.equipment_path = Path(get_data_dir()) / "equipment.json"

    def load_equipment_defs(self) -> Dict[str, EquipmentDef]:
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

        eq_defs = {}
        for index, item in enumerate(data["equipment"]):
            try:
                eq_def = EquipmentDef.from_dict(item, strict=True)
                eq_def.validate(strict=True)
                if eq_def.id in eq_defs:
                    raise ValueError(f"Duplicate equipment ID found in definitions: {eq_def.id}")
                eq_defs[eq_def.id] = eq_def
            except Exception as e:
                raise ValueError(f"Invalid equipment definition at index {index}: {e}") from e
        return eq_defs


class RewardRuntimeAdapter:
    """
    Loads reward definitions and applies them atomically to PlayerProfile instances.
    """
    def __init__(
        self,
        rewards_path: Optional[Union[Path, str]] = None,
        player_ships_path: Optional[Union[Path, str]] = None,
        equipment_path: Optional[Union[Path, str]] = None
    ):
        if rewards_path:
            self.rewards_path = Path(rewards_path)
        else:
            self.rewards_path = Path(get_data_dir()) / "rewards.json"
        
        self.ship_adapter = ShipRuntimeAdapter(player_ships_path)
        self.equipment_adapter = EquipmentRuntimeAdapter(equipment_path)

    def load_reward_defs(self) -> Dict[str, RewardDef]:
        if not self.rewards_path.exists():
            raise FileNotFoundError(f"rewards.json not found at {self.rewards_path}")
        try:
            with open(self.rewards_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse rewards.json: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("Root of rewards.json must be a JSON object.")
        if "rewards" not in data or not isinstance(data["rewards"], list):
            raise ValueError("Invalid rewards.json format: Missing or invalid 'rewards' list.")

        reward_defs = {}
        for index, item in enumerate(data["rewards"]):
            try:
                reward_def = RewardDef.from_dict(item, strict=True)
                reward_def.validate(strict=True)
                if reward_def.id in reward_defs:
                    raise ValueError(f"Duplicate reward ID found in definitions: {reward_def.id}")
                reward_defs[reward_def.id] = reward_def
            except Exception as e:
                raise ValueError(f"Invalid reward definition at index {index}: {e}") from e
        return reward_defs

    def apply_rewards(
        self,
        profile: PlayerProfile,
        reward_ids: List[str],
        reward_defs: Dict[str, RewardDef]
    ) -> PlayerProfile:
        if not isinstance(profile, PlayerProfile):
            raise TypeError("profile must be a PlayerProfile instance")
        profile.validate(strict=True)
        if profile.schema_version != CURRENT_SCHEMA_VERSION:
            raise ValueError(f"Profile schema version must be current version {CURRENT_SCHEMA_VERSION}, got {profile.schema_version}")

        # Validate that all reward_ids exist in reward_defs
        for rid in reward_ids:
            if rid not in reward_defs:
                raise ValueError(f"Reward ID '{rid}' does not exist in reward definitions.")

        # Load valid ships and equipment definitions to cross-validate unlocks
        valid_ship_ids = set(self.ship_adapter.load_ships_defs().keys())
        valid_eq_ids = set(self.equipment_adapter.load_equipment_defs().keys())

        import copy
        new_unlocked_ships = list(profile.unlocked_ships)
        new_inventory = copy.deepcopy(profile.inventory)
        new_progression = copy.deepcopy(profile.progression)

        new_resources = new_inventory.setdefault("resources", {})
        new_equipment = new_inventory.setdefault("equipment", [])
        new_awarded_unique_rewards = new_progression.setdefault("awarded_unique_rewards", [])

        # Process each reward
        for rid in reward_ids:
            reward = reward_defs[rid]

            # 1. Unique reward prevention
            if reward.unique:
                if rid in new_awarded_unique_rewards:
                    raise ValueError(f"Unique reward '{rid}' has already been awarded.")
                new_awarded_unique_rewards.append(rid)

            # 2. Reward application based on type
            if reward.type == "resource_grant":
                res_id = reward.resource_id
                amount = reward.amount
                current_amount = new_resources.get(res_id, 0.0)
                new_amount = current_amount + amount
                if new_amount < 0:
                    raise ValueError(f"Resource '{res_id}' amount cannot go negative: {new_amount}")
                new_resources[res_id] = new_amount

            elif reward.type == "ship_unlock":
                ship_id = reward.target_id
                if ship_id not in valid_ship_ids:
                    raise ValueError(f"Cannot unlock undefined ship ID '{ship_id}'.")
                if ship_id not in new_unlocked_ships:
                    new_unlocked_ships.append(ship_id)

            elif reward.type == "equipment_unlock":
                eq_id = reward.target_id
                if eq_id not in valid_eq_ids:
                    raise ValueError(f"Cannot unlock undefined equipment ID '{eq_id}'.")
                if eq_id not in new_equipment:
                    new_equipment.append(eq_id)

        # Construct and validate new profile. If validation fails, ValueError is raised (atomicity)
        new_profile = PlayerProfile(
            schema_version=profile.schema_version,
            selected_ship_id=profile.selected_ship_id,
            unlocked_ships=new_unlocked_ships,
            inventory=new_inventory,
            progression=new_progression
        )
        new_profile.validate(strict=True)
        return new_profile


class MapProgressionService:
    """
    Manages map completion progression and triggers reward application atomically.
    """
    def __init__(
        self,
        maps_path: Optional[Union[Path, str]] = None,
        player_ships_path: Optional[Union[Path, str]] = None,
        equipment_path: Optional[Union[Path, str]] = None,
        rewards_path: Optional[Union[Path, str]] = None
    ):
        self.map_adapter = MapRuntimeAdapter(maps_path)
        self.reward_adapter = RewardRuntimeAdapter(rewards_path, player_ships_path, equipment_path)

    def record_completion(self, profile: PlayerProfile, map_id: str, difficulty: str) -> tuple[PlayerProfile, Dict[str, Any]]:
        if not isinstance(profile, PlayerProfile):
            raise TypeError("profile must be a PlayerProfile instance")
        profile.validate(strict=True)
        if profile.schema_version != CURRENT_SCHEMA_VERSION:
            raise ValueError(f"Profile schema version must be current version {CURRENT_SCHEMA_VERSION}, got {profile.schema_version}")

        # 1. Load map and reward definitions
        map_defs = self.map_adapter.load_map_defs()
        reward_defs = self.reward_adapter.load_reward_defs()

        # 2. Validate map_id and difficulty
        if map_id not in map_defs:
            raise ValueError(f"Map ID '{map_id}' does not exist in map definitions.")
        map_def = map_defs[map_id]

        if difficulty not in {"easy", "medium", "hard"}:
            raise ValueError(f"Invalid completion difficulty '{difficulty}'.")
        if difficulty not in map_def.difficulty_support:
            raise ValueError(f"Map '{map_id}' does not support difficulty '{difficulty}'.")

        # 3. Determine first-completion status (map-wide)
        completed_maps = profile.progression.get("completed_maps", {})
        map_entry = completed_maps.get(map_id, {})
        completions = map_entry.get("completions", {})
        
        total_completions = sum(completions.get(d, 0) for d in {"easy", "medium", "hard"})
        is_first_completion = (total_completions == 0)

        # 4. Gather rewards
        rewards_to_grant = []
        if is_first_completion:
            rewards_to_grant.extend(map_def.rewards.get("first_completion", []))
        
        rewards_to_grant.extend(map_def.rewards.get("repeat_completion", []))

        # Check if there are difficulty-specific rewards in map_def.rewards schema
        diff_reward_key = f"{difficulty}_completion"
        if diff_reward_key in map_def.rewards:
            rewards_to_grant.extend(map_def.rewards.get(diff_reward_key, []))

        # 5. Apply rewards (Atomic: raises ValueError if any reward is invalid or already awarded unique)
        updated_profile = self.reward_adapter.apply_rewards(profile, rewards_to_grant, reward_defs)

        # 6. Update completed_maps structure (Atomic)
        import copy
        new_progression = copy.deepcopy(updated_profile.progression)
        new_completed_maps = new_progression.setdefault("completed_maps", {})
        new_map_entry = new_completed_maps.setdefault(map_id, {})
        new_completions = new_map_entry.setdefault("completions", {"easy": 0, "medium": 0, "hard": 0})
        
        # Increment completion count
        new_completions[difficulty] = new_completions.get(difficulty, 0) + 1

        # Re-construct the final PlayerProfile with incremented count
        final_profile = PlayerProfile(
            schema_version=updated_profile.schema_version,
            selected_ship_id=updated_profile.selected_ship_id,
            unlocked_ships=updated_profile.unlocked_ships,
            inventory=updated_profile.inventory,
            progression=new_progression
        )
        final_profile.validate(strict=True)

        result_summary = {
            "map_id": map_id,
            "difficulty": difficulty,
            "first_completion": is_first_completion,
            "rewards_granted": rewards_to_grant,
        }

        return final_profile, result_summary


def _validate_and_copy_profile(profile: PlayerProfile) -> PlayerProfile:
    if not isinstance(profile, PlayerProfile):
        raise TypeError("profile must be a PlayerProfile instance")
    profile.validate(strict=True)
    if profile.schema_version != CURRENT_SCHEMA_VERSION:
        raise ValueError(f"Profile schema version must be current version {CURRENT_SCHEMA_VERSION}, got {profile.schema_version}")
    
    import copy
    return PlayerProfile(
        schema_version=profile.schema_version,
        selected_ship_id=profile.selected_ship_id,
        unlocked_ships=list(profile.unlocked_ships),
        inventory=copy.deepcopy(profile.inventory),
        progression=copy.deepcopy(profile.progression)
    )


def _init_story_progress(story_flags: Dict[str, Any]) -> None:
    if "unlocked_stories" not in story_flags:
        story_flags["unlocked_stories"] = []
    elif not isinstance(story_flags["unlocked_stories"], list):
        raise ValueError("story_flags['unlocked_stories'] exists but is not a list")

    if "completed_stories" not in story_flags:
        story_flags["completed_stories"] = []
    elif not isinstance(story_flags["completed_stories"], list):
        raise ValueError("story_flags['completed_stories'] exists but is not a list")

    if "current_nodes" not in story_flags:
        story_flags["current_nodes"] = {}
    elif not isinstance(story_flags["current_nodes"], dict):
        raise ValueError("story_flags['current_nodes'] exists but is not a dict")

    if "flags" not in story_flags:
        story_flags["flags"] = {}
    elif not isinstance(story_flags["flags"], dict):
        raise ValueError("story_flags['flags'] exists but is not a dict")


def _init_quest_progress(quest_flags: Dict[str, Any]) -> None:
    if "unlocked_quests" not in quest_flags:
        quest_flags["unlocked_quests"] = []
    elif not isinstance(quest_flags["unlocked_quests"], list):
        raise ValueError("quest_flags['unlocked_quests'] exists but is not a list")

    if "completed_quests" not in quest_flags:
        quest_flags["completed_quests"] = []
    elif not isinstance(quest_flags["completed_quests"], list):
        raise ValueError("quest_flags['completed_quests'] exists but is not a list")

    if "objective_progress" not in quest_flags:
        quest_flags["objective_progress"] = {}
    elif not isinstance(quest_flags["objective_progress"], dict):
        raise ValueError("quest_flags['objective_progress'] exists but is not a dict")


class StoryRuntimeAdapter:
    """
    Loads and validates story definitions from story.json.
    Performs runtime validation checks.
    """
    def __init__(self, story_path: Optional[Union[Path, str]] = None):
        if story_path:
            self.story_path = Path(story_path)
        else:
            self.story_path = Path(get_data_dir()) / "story.json"

    def load_story_defs(self) -> Dict[str, StoryDef]:
        """Loads and validates all story definitions from story.json."""
        if not self.story_path.exists():
            raise FileNotFoundError(f"story.json not found at {self.story_path}")
        
        try:
            with open(self.story_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse story.json: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("Root of story.json must be a JSON object.")
        if "stories" not in data:
            raise ValueError("Root of story.json is missing required field 'stories'.")
        if not isinstance(data["stories"], list):
            raise ValueError("'stories' field in story.json must be a list.")

        story_defs = {}
        for index, item in enumerate(data["stories"]):
            try:
                story_def = StoryDef.from_dict(item, strict=True)
                story_def.validate(strict=True)
                if story_def.id in story_defs:
                    raise ValueError(f"Duplicate story ID found in definitions: {story_def.id}")
                story_defs[story_def.id] = story_def
            except Exception as e:
                raise ValueError(f"Invalid story definition at index {index}: {e}") from e
        return story_defs

    def resolve_story(self, story_id: str) -> StoryDef:
        """Resolves story_id to a StoryDef. Raises ValueError if invalid."""
        story_defs = self.load_story_defs()
        if story_id not in story_defs:
            raise ValueError(
                f"Story ID '{story_id}' does not exist in story definitions."
            )
        return story_defs[story_id]


class QuestRuntimeAdapter:
    """
    Loads and validates quest definitions from quests.json.
    Performs runtime validation checks.
    """
    def __init__(self, quests_path: Optional[Union[Path, str]] = None):
        if quests_path:
            self.quests_path = Path(quests_path)
        else:
            self.quests_path = Path(get_data_dir()) / "quests.json"

    def load_quest_defs(self) -> Dict[str, QuestDef]:
        """Loads and validates all quest definitions from quests.json."""
        if not self.quests_path.exists():
            raise FileNotFoundError(f"quests.json not found at {self.quests_path}")
        
        try:
            with open(self.quests_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse quests.json: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("Root of quests.json must be a JSON object.")
        if "quests" not in data:
            raise ValueError("Root of quests.json is missing required field 'quests'.")
        if not isinstance(data["quests"], list):
            raise ValueError("'quests' field in quests.json must be a list.")

        quest_defs = {}
        for index, item in enumerate(data["quests"]):
            try:
                quest_def = QuestDef.from_dict(item, strict=True)
                quest_def.validate(strict=True)
                if quest_def.id in quest_defs:
                    raise ValueError(f"Duplicate quest ID found in definitions: {quest_def.id}")
                quest_defs[quest_def.id] = quest_def
            except Exception as e:
                raise ValueError(f"Invalid quest definition at index {index}: {e}") from e
        return quest_defs

    def resolve_quest(self, quest_id: str) -> QuestDef:
        """Resolves quest_id to a QuestDef. Raises ValueError if invalid."""
        quest_defs = self.load_quest_defs()
        if quest_id not in quest_defs:
            raise ValueError(
                f"Quest ID '{quest_id}' does not exist in quest definitions."
            )
        return quest_defs[quest_id]


@dataclass(frozen=True)
class GameplaySnapshot:
    map_id: str
    difficulty: str
    completed_map: bool
    defeated_enemy_counts: Dict[str, int]
    defeated_boss_id: Optional[str]
    pickup_counts: Dict[str, int]
    score: int
    survival_time: float
    special_flags: Dict[str, Any]


class QuestObjectiveEvaluator:
    """
    Pure utility class to evaluate quest objectives against gameplay snapshots.
    """
    @staticmethod
    def evaluate_objective(objective: QuestObjective, snapshot: GameplaySnapshot) -> tuple[bool, Union[int, float]]:
        """
        Evaluates the objective against the snapshot.
        Returns a tuple (is_complete, current_progress_value).
        """
        if objective.type == "complete_map":
            if snapshot.map_id == objective.map_id and snapshot.completed_map:
                if objective.difficulty is None or snapshot.difficulty == objective.difficulty:
                    return True, objective.target
            return False, 0
            
        elif objective.type == "defeat_enemy_type":
            val = snapshot.defeated_enemy_counts.get(objective.enemy_id, 0)
            return val >= objective.target, val
            
        elif objective.type == "defeat_boss":
            is_complete = (snapshot.defeated_boss_id == objective.boss_id and snapshot.defeated_boss_id is not None)
            val = 1 if is_complete else 0
            return is_complete, val
            
        elif objective.type == "collect_pickup_type":
            val = snapshot.pickup_counts.get(objective.pickup_id, 0)
            return val >= objective.target, val
            
        elif objective.type == "survive_seconds":
            return snapshot.survival_time >= objective.target, snapshot.survival_time
            
        elif objective.type == "reach_score":
            return snapshot.score >= objective.target, snapshot.score
            
        return False, 0


class StoryProgressionService:
    """
    Pure service that updates the in-memory PlayerProfile progression states for stories.
    """
    def __init__(self, story_path: Optional[Union[Path, str]] = None):
        self.adapter = StoryRuntimeAdapter(story_path)

    def unlock_story(self, profile: PlayerProfile, story_id: str) -> PlayerProfile:
        new_profile = _validate_and_copy_profile(profile)
        self.adapter.resolve_story(story_id)

        story_flags = new_profile.progression.setdefault("story_flags", {})
        _init_story_progress(story_flags)

        if story_id not in story_flags["unlocked_stories"]:
            story_flags["unlocked_stories"].append(story_id)

        new_profile.validate(strict=True)
        return new_profile

    def advance_story_node(
        self,
        profile: PlayerProfile,
        story_id: str,
        node_id: str,
        choice_index: Optional[int] = None
    ) -> tuple[PlayerProfile, StoryNode, List[str]]:
        new_profile = _validate_and_copy_profile(profile)
        story_def = self.adapter.resolve_story(story_id)
        
        target_node = None
        for node in story_def.nodes:
            if node.id == node_id:
                target_node = node
                break
        if not target_node:
            raise ValueError(f"Node '{node_id}' does not exist in story '{story_id}'.")

        story_flags = new_profile.progression.setdefault("story_flags", {})
        _init_story_progress(story_flags)

        if story_id in story_flags.get("completed_stories", []):
            raise ValueError(f"Story '{story_id}' is already completed.")

        current_node_id = story_flags.get("current_nodes", {}).get(story_id)
        if current_node_id is not None:
            if node_id != current_node_id:
                raise ValueError(f"Expected node '{current_node_id}', got '{node_id}' for story '{story_id}'.")
        else:
            start_node_id = story_def.nodes[0].id
            if node_id != start_node_id:
                raise ValueError(f"Story '{story_id}' must start at node '{start_node_id}', got '{node_id}'.")

        if target_node.choices and choice_index is None:
            raise ValueError(f"Node '{node_id}' has choices and requires choice_index.")

        if story_id not in story_flags["unlocked_stories"]:
            story_flags["unlocked_stories"].append(story_id)

        quest_flags = new_profile.progression.setdefault("quest_flags", {})
        _init_quest_progress(quest_flags)

        eligible_reward_ids = []

        if choice_index is not None:
            if not target_node.choices:
                raise ValueError(f"Node '{node_id}' has no choices to select.")
            if choice_index < 0 or choice_index >= len(target_node.choices):
                raise ValueError(f"Invalid choice_index {choice_index} for node '{node_id}'.")
            
            choice = target_node.choices[choice_index]
            next_node = choice.next_node_id
            
            for k, v in choice.flags_set.items():
                story_flags["flags"][k] = v
            for k in choice.flags_cleared:
                story_flags["flags"].pop(k, None)
                
            eligible_reward_ids.extend(choice.reward_ids)
        else:
            next_node = target_node.next_node_id
            
            for k, v in target_node.flags_set.items():
                story_flags["flags"][k] = v
            for k in target_node.flags_cleared:
                story_flags["flags"].pop(k, None)
                
            eligible_reward_ids.extend(target_node.reward_ids)

        if next_node is not None:
            story_flags["current_nodes"][story_id] = next_node
        else:
            story_flags["current_nodes"].pop(story_id, None)
            if story_id not in story_flags["completed_stories"]:
                story_flags["completed_stories"].append(story_id)

        new_profile.validate(strict=True)
        return new_profile, target_node, eligible_reward_ids


class QuestProgressionService:
    """
    Pure service that updates the in-memory PlayerProfile progression states for quests.
    """
    def __init__(self, quests_path: Optional[Union[Path, str]] = None):
        self.adapter = QuestRuntimeAdapter(quests_path)

    def unlock_quest(self, profile: PlayerProfile, quest_id: str) -> PlayerProfile:
        new_profile = _validate_and_copy_profile(profile)
        self.adapter.resolve_quest(quest_id)

        quest_flags = new_profile.progression.setdefault("quest_flags", {})
        _init_quest_progress(quest_flags)

        if quest_id not in quest_flags["unlocked_quests"]:
            quest_flags["unlocked_quests"].append(quest_id)

        new_profile.validate(strict=True)
        return new_profile

    def update_quest_progress(
        self,
        profile: PlayerProfile,
        quest_id: str,
        snapshot: GameplaySnapshot
    ) -> tuple[PlayerProfile, Dict[str, bool], List[str]]:
        new_profile = _validate_and_copy_profile(profile)
        quest_def = self.adapter.resolve_quest(quest_id)
        
        quest_flags = new_profile.progression.setdefault("quest_flags", {})
        _init_quest_progress(quest_flags)
        
        if quest_id not in quest_flags["unlocked_quests"]:
            quest_flags["unlocked_quests"].append(quest_id)

        # Check if already completed
        if quest_id in quest_flags["completed_quests"]:
            return new_profile, {obj.id: True for obj in quest_def.objectives}, []

        obj_progress = quest_flags["objective_progress"].setdefault(quest_id, {})

        completions = {}
        all_complete = True
        
        for obj in quest_def.objectives:
            is_complete, observed_val = QuestObjectiveEvaluator.evaluate_objective(obj, snapshot)
            
            # Idempotent progress update: new_progress = max(existing_progress, observed_value)
            existing_val = obj_progress.get(obj.id, 0)
            new_val = max(existing_val, observed_val)
            obj_progress[obj.id] = new_val
            
            # Re-check completion based on the stored progress
            is_complete_stored = (new_val >= obj.target)
            completions[obj.id] = is_complete_stored
            
            if not is_complete_stored:
                all_complete = False

        eligible_reward_ids = []
        if all_complete:
            if quest_id not in quest_flags["completed_quests"]:
                quest_flags["completed_quests"].append(quest_id)
                eligible_reward_ids.extend(quest_def.reward_ids)

        new_profile.validate(strict=True)
        return new_profile, completions, eligible_reward_ids


def build_gameplay_snapshot_from_state(state_mgr: Any) -> Optional[GameplaySnapshot]:
    """
    Constructs a GameplaySnapshot from game state manager stats.
    Returns None if no map context (map_id) is available.
    """
    # 1. Access map ID. No fallback allowed, if None return None
    map_id = state_mgr.map_id
    if map_id is None:
        return None

    # 2. Map transition to completed_map based on GameStateID.VICTORY
    from space_demo.core.ids import GameStateID
    completed_map = (state_mgr.current_state == GameStateID.VICTORY)

    return GameplaySnapshot(
        map_id=map_id,
        difficulty=getattr(state_mgr, "difficulty", "medium"),
        completed_map=completed_map,
        defeated_enemy_counts=dict(getattr(state_mgr, "defeated_enemy_counts", {})),
        defeated_boss_id=getattr(state_mgr, "defeated_boss_id", None),
        pickup_counts=dict(getattr(state_mgr, "pickup_counts", {})),
        score=getattr(state_mgr, "score", 0),
        survival_time=getattr(state_mgr, "survival_time", 0.0),
        special_flags={}
    )


def apply_quest_progress_for_snapshot(
    profile: PlayerProfile,
    snapshot: GameplaySnapshot,
    quest_service: QuestProgressionService
) -> tuple[PlayerProfile, List[str]]:
    """
    Updates quest progress for eligible quests in the snapshot.
    Eligible quests are:
    - Quests already unlocked in the player profile.
    - Starter quests (quests with empty/no unlock_requirements).
    Returns the updated PlayerProfile and a list of eligible reward IDs.
    """
    quest_defs = quest_service.adapter.load_quest_defs()
    
    quest_flags = profile.progression.get("quest_flags", {})
    unlocked_quests = quest_flags.get("unlocked_quests", [])

    current_profile = profile
    all_eligible_rewards = []

    for q_id, q_def in quest_defs.items():
        # Quest eligibility rule
        is_starter = not q_def.unlock_requirements
        if q_id in unlocked_quests or is_starter:
            current_profile, completions, rewards = quest_service.update_quest_progress(
                current_profile, q_id, snapshot
            )
            all_eligible_rewards.extend(rewards)

    return current_profile, all_eligible_rewards


