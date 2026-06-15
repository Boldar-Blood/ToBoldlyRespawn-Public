"""Pure reward application helpers for Phase 5G."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

from space_demo.data.loader import get_data_dir
from space_demo.domain.profile import PlayerProfile
from space_demo.domain.rewards import RewardDef
from space_demo.profile.migration import CURRENT_SCHEMA_VERSION


PathLike = Optional[Union[Path, str]]


@dataclass(frozen=True)
class RewardGrantResult:
    profile: PlayerProfile
    granted_reward_ids: List[str] = field(default_factory=list)
    skipped_reward_ids: List[str] = field(default_factory=list)
    resource_deltas: Dict[str, int] = field(default_factory=dict)
    unlocked_ship_ids: List[str] = field(default_factory=list)
    unlocked_equipment_ids: List[str] = field(default_factory=list)


class RewardRuntimeAdapter:
    def __init__(self, rewards_path: PathLike = None):
        self.rewards_path = Path(rewards_path) if rewards_path else Path(get_data_dir()) / "rewards.json"

    def load_reward_defs(self) -> Dict[str, RewardDef]:
        if not self.rewards_path.exists():
            raise FileNotFoundError(f"rewards.json not found at {self.rewards_path}")
        try:
            data = json.loads(self.rewards_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError(f"Failed to parse rewards.json: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("Root of rewards.json must be a JSON object.")
        if "rewards" not in data:
            raise ValueError("Root of rewards.json is missing required field 'rewards'.")
        if not isinstance(data["rewards"], list):
            raise ValueError("'rewards' field in rewards.json must be a list.")

        result: Dict[str, RewardDef] = {}
        for index, item in enumerate(data["rewards"]):
            try:
                reward = RewardDef.from_dict(item, strict=True)
                reward.validate(strict=True)
                if reward.id in result:
                    raise ValueError(f"Duplicate reward ID found in definitions: {reward.id}")
                result[reward.id] = reward
            except Exception as exc:
                raise ValueError(f"Invalid reward definition at index {index}: {exc}") from exc
        return result

    def resolve_reward(self, reward_id: str) -> RewardDef:
        reward_defs = self.load_reward_defs()
        if reward_id not in reward_defs:
            raise ValueError(f"Reward ID '{reward_id}' does not exist in reward definitions.")
        return reward_defs[reward_id]


class RewardGrantService:
    def __init__(self, rewards_path: PathLike = None):
        self.adapter = RewardRuntimeAdapter(rewards_path=rewards_path)

    def apply_reward_ids(self, profile: PlayerProfile, reward_ids: Iterable[str]) -> RewardGrantResult:
        reward_id_list = list(reward_ids)
        new_profile = _copy_profile(profile)
        if not reward_id_list:
            return RewardGrantResult(profile=new_profile)

        reward_defs = self.adapter.load_reward_defs()
        rewards: List[RewardDef] = []
        for reward_id in reward_id_list:
            if reward_id not in reward_defs:
                raise ValueError(f"Reward ID '{reward_id}' does not exist in reward definitions.")
            rewards.append(reward_defs[reward_id])

        resources = new_profile.inventory.setdefault("resources", {})
        equipment = new_profile.inventory.setdefault("equipment", [])
        awarded_unique = new_profile.progression.setdefault("awarded_unique_rewards", [])
        if not isinstance(resources, dict):
            raise ValueError("inventory['resources'] must be a dictionary.")
        if not isinstance(equipment, list):
            raise ValueError("inventory['equipment'] must be a list.")
        if not isinstance(awarded_unique, list):
            raise ValueError("progression['awarded_unique_rewards'] must be a list.")

        granted: List[str] = []
        skipped: List[str] = []
        resource_deltas: Dict[str, int] = {}
        unlocked_ships: List[str] = []
        unlocked_equipment: List[str] = []

        for reward in rewards:
            if reward.unique and reward.id in awarded_unique:
                skipped.append(reward.id)
                continue
            changed = self._apply_one(new_profile, reward, resource_deltas, unlocked_ships, unlocked_equipment)
            if changed:
                granted.append(reward.id)
            else:
                skipped.append(reward.id)
            if reward.unique and reward.id not in awarded_unique:
                awarded_unique.append(reward.id)

        new_profile.validate(strict=True)
        return RewardGrantResult(
            profile=new_profile,
            granted_reward_ids=granted,
            skipped_reward_ids=skipped,
            resource_deltas=resource_deltas,
            unlocked_ship_ids=unlocked_ships,
            unlocked_equipment_ids=unlocked_equipment,
        )

    @staticmethod
    def _apply_one(
        profile: PlayerProfile,
        reward: RewardDef,
        resource_deltas: Dict[str, int],
        unlocked_ships: List[str],
        unlocked_equipment: List[str],
    ) -> bool:
        if reward.type == "resource_grant":
            if reward.resource_id is None or reward.amount is None:
                raise ValueError(f"Reward '{reward.id}' is missing resource grant data.")
            resources = profile.inventory.setdefault("resources", {})
            current = resources.get(reward.resource_id, 0)
            if not isinstance(current, (int, float)) or current < 0:
                raise ValueError(f"Resource '{reward.resource_id}' amount must be non-negative.")
            resources[reward.resource_id] = current + reward.amount
            resource_deltas[reward.resource_id] = resource_deltas.get(reward.resource_id, 0) + reward.amount
            return reward.amount > 0
        if reward.type == "ship_unlock":
            if reward.target_id is None:
                raise ValueError(f"Reward '{reward.id}' is missing target_id.")
            if reward.target_id in profile.unlocked_ships:
                return False
            profile.unlocked_ships.append(reward.target_id)
            unlocked_ships.append(reward.target_id)
            return True
        if reward.type == "equipment_unlock":
            if reward.target_id is None:
                raise ValueError(f"Reward '{reward.id}' is missing target_id.")
            equipment = profile.inventory.setdefault("equipment", [])
            if reward.target_id in equipment:
                return False
            equipment.append(reward.target_id)
            unlocked_equipment.append(reward.target_id)
            return True
        raise ValueError(f"Unsupported reward type '{reward.type}'.")


def apply_reward_ids_to_profile(
    profile: PlayerProfile,
    reward_ids: Iterable[str],
    reward_service: RewardGrantService,
) -> RewardGrantResult:
    return reward_service.apply_reward_ids(profile, reward_ids)


def _copy_profile(profile: PlayerProfile) -> PlayerProfile:
    if not isinstance(profile, PlayerProfile):
        raise TypeError("profile must be a PlayerProfile instance")
    profile.validate(strict=True)
    if profile.schema_version != CURRENT_SCHEMA_VERSION:
        raise ValueError(
            f"Profile schema_version {profile.schema_version} is not current {CURRENT_SCHEMA_VERSION}."
        )
    copied = PlayerProfile(
        schema_version=profile.schema_version,
        selected_ship_id=profile.selected_ship_id,
        unlocked_ships=list(profile.unlocked_ships),
        inventory=copy.deepcopy(profile.inventory),
        progression=copy.deepcopy(profile.progression),
    )
    copied.validate(strict=True)
    return copied
