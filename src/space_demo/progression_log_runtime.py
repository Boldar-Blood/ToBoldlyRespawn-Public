"""Pure progression log snapshots for Phase 5H.

This module contains no Panda3D objects.  It builds read-only story, quest, and
profile progression snapshots from validated content definitions and the current
PlayerProfile.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

from space_demo.domain.profile import PlayerProfile
from space_demo.domain.quests import QuestObjective
from space_demo.domain.story import StoryNode
from space_demo.profile.migration import CURRENT_SCHEMA_VERSION
from space_demo.profile.runtime import QuestRuntimeAdapter, StoryRuntimeAdapter


PathLike = Optional[Union[Path, str]]


@dataclass(frozen=True)
class StoryLogEntry:
    id: str
    display_name: str
    description: str
    status: str
    current_node_id: Optional[str] = None
    current_node_summary: str = ""


@dataclass(frozen=True)
class QuestObjectiveLogEntry:
    id: str
    objective_type: str
    target: float
    current: float
    completed: bool
    label: str


@dataclass(frozen=True)
class QuestLogEntry:
    id: str
    display_name: str
    description: str
    status: str
    objectives: List[QuestObjectiveLogEntry] = field(default_factory=list)
    reward_ids: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProgressionLogState:
    stories: List[StoryLogEntry]
    quests: List[QuestLogEntry]
    resources: Dict[str, float]
    awarded_unique_rewards: List[str]
    unlocked_ships: List[str]
    equipment: List[str]

    def to_lines(self) -> List[str]:
        lines: List[str] = []
        lines.append("STORIES")
        if not self.stories:
            lines.append("  No story entries.")
        for story in self.stories:
            line = f"  [{story.status.upper()}] {story.display_name}"
            if story.current_node_summary:
                line += f" — {story.current_node_summary}"
            lines.append(line)

        lines.append("")
        lines.append("QUESTS")
        if not self.quests:
            lines.append("  No quest entries.")
        for quest in self.quests:
            lines.append(f"  [{quest.status.upper()}] {quest.display_name}")
            for objective in quest.objectives:
                marker = "✓" if objective.completed else "•"
                lines.append(
                    f"    {marker} {objective.label}: {objective.current:g}/{objective.target:g}"
                )

        lines.append("")
        lines.append("RESOURCES")
        if not self.resources:
            lines.append("  No resources yet.")
        for resource_id, amount in sorted(self.resources.items()):
            lines.append(f"  {resource_id}: {amount:g}")

        lines.append("")
        lines.append("UNLOCKS")
        lines.append(f"  Ships: {len(self.unlocked_ships)}")
        lines.append(f"  Equipment: {len(self.equipment)}")
        lines.append(f"  Unique rewards: {len(self.awarded_unique_rewards)}")
        return lines


class ProgressionLogBuilder:
    """Build read-only progression log snapshots from profile/content state."""

    def __init__(self, story_path: PathLike = None, quests_path: PathLike = None):
        self.story_adapter = StoryRuntimeAdapter(story_path=story_path)
        self.quest_adapter = QuestRuntimeAdapter(quests_path=quests_path)

    def build(self, profile: PlayerProfile) -> ProgressionLogState:
        if not isinstance(profile, PlayerProfile):
            raise TypeError("profile must be a PlayerProfile instance")
        profile.validate(strict=True)
        if profile.schema_version != CURRENT_SCHEMA_VERSION:
            raise ValueError(
                f"Profile schema_version {profile.schema_version} is not current {CURRENT_SCHEMA_VERSION}."
            )

        story_defs = self.story_adapter.load_story_defs()
        quest_defs = self.quest_adapter.load_quest_defs()

        story_flags = _story_flags(profile)
        quest_flags = _quest_flags(profile)

        stories = [
            _build_story_entry(story_def, story_flags)
            for story_def in story_defs.values()
        ]
        quests = [
            _build_quest_entry(quest_def, quest_flags)
            for quest_def in quest_defs.values()
        ]

        return ProgressionLogState(
            stories=stories,
            quests=quests,
            resources=dict(profile.inventory.get("resources", {})),
            awarded_unique_rewards=list(profile.progression.get("awarded_unique_rewards", [])),
            unlocked_ships=list(profile.unlocked_ships),
            equipment=list(profile.inventory.get("equipment", [])),
        )


def _story_flags(profile: PlayerProfile) -> dict:
    flags = profile.progression.get("story_flags", {})
    if not isinstance(flags, dict):
        raise ValueError("progression['story_flags'] must be a dictionary.")
    return flags


def _quest_flags(profile: PlayerProfile) -> dict:
    flags = profile.progression.get("quest_flags", {})
    if not isinstance(flags, dict):
        raise ValueError("progression['quest_flags'] must be a dictionary.")
    return flags


def _build_story_entry(story_def, story_flags: dict) -> StoryLogEntry:
    completed = story_flags.get("completed_stories", [])
    unlocked = story_flags.get("unlocked_stories", [])
    current_nodes = story_flags.get("current_nodes", {})
    if not isinstance(completed, list):
        raise ValueError("completed_stories must be a list.")
    if not isinstance(unlocked, list):
        raise ValueError("unlocked_stories must be a list.")
    if not isinstance(current_nodes, dict):
        raise ValueError("current_nodes must be a dictionary.")

    current_node_id = current_nodes.get(story_def.id)
    status = "locked"
    if story_def.id in completed:
        status = "completed"
    elif current_node_id:
        status = "active"
    elif story_def.id in unlocked:
        status = "unlocked"

    current_node_summary = ""
    if current_node_id:
        node = _find_story_node(story_def.nodes, current_node_id)
        current_node_summary = _summarize_text(node.body)

    return StoryLogEntry(
        id=story_def.id,
        display_name=story_def.display_name,
        description=story_def.description,
        status=status,
        current_node_id=current_node_id,
        current_node_summary=current_node_summary,
    )


def _find_story_node(nodes: List[StoryNode], node_id: str) -> StoryNode:
    for node in nodes:
        if node.id == node_id:
            return node
    raise ValueError(f"Story node '{node_id}' does not exist.")


def _build_quest_entry(quest_def, quest_flags: dict) -> QuestLogEntry:
    completed_quests = quest_flags.get("completed_quests", [])
    unlocked_quests = quest_flags.get("unlocked_quests", [])
    objective_progress = quest_flags.get("objective_progress", {})
    if not isinstance(completed_quests, list):
        raise ValueError("completed_quests must be a list.")
    if not isinstance(unlocked_quests, list):
        raise ValueError("unlocked_quests must be a list.")
    if not isinstance(objective_progress, dict):
        raise ValueError("objective_progress must be a dictionary.")

    quest_progress = objective_progress.get(quest_def.id, {})
    if not isinstance(quest_progress, dict):
        raise ValueError(f"objective_progress['{quest_def.id}'] must be a dictionary.")

    objectives = [
        _build_objective_entry(objective, quest_progress)
        for objective in quest_def.objectives
    ]

    if quest_def.id in completed_quests:
        status = "completed"
    elif quest_progress:
        status = "active"
    elif quest_def.id in unlocked_quests or not quest_def.unlock_requirements:
        status = "available"
    else:
        status = "locked"

    return QuestLogEntry(
        id=quest_def.id,
        display_name=quest_def.display_name,
        description=quest_def.description,
        status=status,
        objectives=objectives,
        reward_ids=list(quest_def.reward_ids),
    )


def _build_objective_entry(
    objective: QuestObjective,
    quest_progress: dict,
) -> QuestObjectiveLogEntry:
    current = quest_progress.get(objective.id, 0)
    if not isinstance(current, (int, float)):
        raise ValueError(f"Progress for objective '{objective.id}' must be numeric.")
    completed = current >= objective.target
    return QuestObjectiveLogEntry(
        id=objective.id,
        objective_type=objective.type,
        target=float(objective.target),
        current=float(current),
        completed=completed,
        label=_objective_label(objective),
    )


def _objective_label(objective: QuestObjective) -> str:
    if objective.type == "complete_map":
        difficulty = f" ({objective.difficulty})" if objective.difficulty else ""
        return f"Complete {objective.map_id}{difficulty}"
    if objective.type == "survive_seconds":
        return "Survive seconds"
    if objective.type == "defeat_enemy_type":
        return f"Defeat {objective.enemy_id}"
    if objective.type == "defeat_boss":
        return f"Defeat boss {objective.boss_id}"
    if objective.type == "collect_pickup_type":
        return f"Collect {objective.pickup_id}"
    if objective.type == "reach_score":
        return "Reach score"
    return objective.type


def _summarize_text(text: str, limit: int = 72) -> str:
    one_line = " ".join(text.split())
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 1].rstrip() + "…"
