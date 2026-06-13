"""Pure story popup controller for Phase 5F.

This module contains no Panda3D UI objects.  It resolves story definitions,
tracks the active story node to display, and delegates profile mutations to the
existing StoryProgressionService so UI code does not duplicate story logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Union, List

from space_demo.domain.profile import PlayerProfile
from space_demo.domain.story import StoryNode
from space_demo.profile.runtime import StoryProgressionService


PathLike = Optional[Union[Path, str]]


@dataclass(frozen=True)
class StoryPopupState:
    """Serializable UI-facing snapshot of the currently active story node."""

    story_id: str
    story_display_name: str
    node_id: str
    speaker: str
    body: str
    choices: Tuple[str, ...]

    @property
    def requires_choice(self) -> bool:
        return bool(self.choices)


@dataclass(frozen=True)
class StoryPopupAdvanceResult:
    """Result of advancing or choosing inside an active story popup."""

    profile: PlayerProfile
    next_state: Optional[StoryPopupState]
    processed_node: StoryNode
    eligible_reward_ids: Tuple[str, ...]


class StoryPopupController:
    """Pure controller for starting and advancing story popups."""

    def __init__(self, story_path: PathLike = None):
        self.service = StoryProgressionService(story_path=story_path)
        self.active_state: Optional[StoryPopupState] = None

    def start_story(
        self,
        profile: PlayerProfile,
        story_id: str,
    ) -> tuple[PlayerProfile, Optional[StoryPopupState]]:
        """Unlock and show the current/first node for a story if not completed."""
        story_def = self.service.adapter.resolve_story(story_id)
        story_flags = profile.progression.get("story_flags", {})
        completed = story_flags.get("completed_stories", [])
        if story_id in completed:
            self.active_state = None
            return profile, None

        updated_profile = self.service.unlock_story(profile, story_id)
        updated_story_flags = updated_profile.progression.get("story_flags", {})
        current_nodes = updated_story_flags.get("current_nodes", {})
        node_id = current_nodes.get(story_id, story_def.nodes[0].id)
        node = self._resolve_node(story_def.nodes, node_id)
        self.active_state = self._to_popup_state(story_id, story_def.display_name, node)
        return updated_profile, self.active_state

    def advance(
        self,
        profile: PlayerProfile,
        choice_index: Optional[int] = None,
    ) -> StoryPopupAdvanceResult:
        """Advance the active popup, optionally selecting a response choice."""
        if self.active_state is None:
            raise ValueError("No active story popup to advance.")

        current = self.active_state
        updated_profile, processed_node, reward_ids = self.service.advance_story_node(
            profile,
            current.story_id,
            current.node_id,
            choice_index=choice_index,
        )

        story_def = self.service.adapter.resolve_story(current.story_id)
        story_flags = updated_profile.progression.get("story_flags", {})
        next_node_id = story_flags.get("current_nodes", {}).get(current.story_id)
        if next_node_id is None:
            self.active_state = None
            next_state = None
        else:
            next_node = self._resolve_node(story_def.nodes, next_node_id)
            next_state = self._to_popup_state(
                current.story_id,
                story_def.display_name,
                next_node,
            )
            self.active_state = next_state

        return StoryPopupAdvanceResult(
            profile=updated_profile,
            next_state=next_state,
            processed_node=processed_node,
            eligible_reward_ids=tuple(reward_ids),
        )

    def clear(self) -> None:
        self.active_state = None

    @staticmethod
    def _resolve_node(nodes: List[StoryNode], node_id: str) -> StoryNode:
        for node in nodes:
            if node.id == node_id:
                return node
        raise ValueError(f"Story node '{node_id}' does not exist.")

    @staticmethod
    def _to_popup_state(
        story_id: str,
        story_display_name: str,
        node: StoryNode,
    ) -> StoryPopupState:
        return StoryPopupState(
            story_id=story_id,
            story_display_name=story_display_name,
            node_id=node.id,
            speaker=node.speaker,
            body=node.body,
            choices=tuple(choice.text for choice in node.choices),
        )
