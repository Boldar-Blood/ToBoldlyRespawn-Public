"""Application runtime integration for To Boldly Respawn."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, Optional, Union

from space_demo.app_base import SpaceDisasterApp as BaseSpaceDisasterApp
from space_demo.core.ids import GameStateID
from space_demo.progression_log_runtime import ProgressionLogBuilder
from space_demo.story_popup_runtime import StoryPopupController
from space_demo.ui.progression_log import ProgressionLogView
from space_demo.ui.story_popup import StoryPopupView


PathLike = Optional[Union[Path, str]]


class SpaceDisasterApp(BaseSpaceDisasterApp):
    """Canonical app class with explicit Phase 5 runtime wiring."""

    def __init__(
        self,
        headless: bool = False,
        profile_path: PathLike = None,
        default_profile_path: PathLike = None,
        player_ships_path: PathLike = None,
        ship_adapter=None,
        maps_path: PathLike = None,
        waves_path: PathLike = None,
        quests_path: PathLike = None,
        story_path: PathLike = None,
        rewards_path: PathLike = None,
        default_map_id: str = "map_001_retrograde_escape",
        default_story_id: str = "story_001_intro_chase",
        enable_story_popups: bool = True,
        enable_progression_log: bool = True,
    ):
        self.maps_path = Path(maps_path) if maps_path is not None else None
        self.waves_path = Path(waves_path) if waves_path is not None else None
        self.quests_path = Path(quests_path) if quests_path is not None else None
        self.story_path = Path(story_path) if story_path is not None else None
        self.rewards_path = Path(rewards_path) if rewards_path is not None else None
        self.default_map_id = default_map_id
        self.default_story_id = default_story_id
        self.enable_story_popups = enable_story_popups
        self.enable_progression_log = enable_progression_log
        self.map_runtime_error = None
        self.story_runtime_error = None
        self.reward_runtime_error = None
        self.progression_log_error = None
        self.story_popup_controller = None
        self.story_popup_view = None
        self.progression_log_builder = None
        self.progression_log_view = None
        self._story_trigger_attempted = False

        super().__init__(
            headless=headless,
            profile_path=profile_path,
            default_profile_path=default_profile_path,
            player_ships_path=player_ships_path,
            ship_adapter=ship_adapter,
        )

        self._initialize_default_map_runtime()
        self._initialize_story_popup_runtime()
        self._initialize_progression_log_runtime()
        self._bind_story_popup_controls()
        self._bind_progression_log_controls()

    def _initialize_default_map_runtime(self) -> None:
        if not getattr(self, "state_mgr", None):
            return
        try:
            from space_demo.profile.runtime import MapRuntimeAdapter

            map_adapter = MapRuntimeAdapter(maps_path=self.maps_path)
            map_def, wave_defs = map_adapter.resolve_map_runtime_config(
                self.default_map_id,
                waves_path=self.waves_path,
            )
        except Exception as exc:
            self.map_runtime_error = str(exc)
            self.state_mgr.map_runtime_error = self.map_runtime_error
            print(f"[Map] Failed to initialize map runtime config: {exc}", file=sys.stderr)
            return

        self.map_runtime_error = None
        self.state_mgr.map_runtime_error = None
        self.state_mgr.default_map_id = self.default_map_id
        self.state_mgr._map_def = map_def
        self.state_mgr._wave_defs = wave_defs
        self.state_mgr.load_wave_params()
        print(f"[Map] Runtime map initialized: {map_def.id}")

    def _initialize_story_popup_runtime(self) -> None:
        if not self.enable_story_popups:
            return
        self.story_popup_controller = StoryPopupController(story_path=self.story_path)
        self.story_popup_view = StoryPopupView(self)

    def _initialize_progression_log_runtime(self) -> None:
        if not self.enable_progression_log:
            return
        self.progression_log_builder = ProgressionLogBuilder(
            story_path=self.story_path,
            quests_path=self.quests_path,
        )
        self.progression_log_view = ProgressionLogView(self)

    def _bind_story_popup_controls(self) -> None:
        if not self.enable_story_popups:
            return
        for index in range(9):
            self.accept(str(index + 1), self.choose_story_popup, [index])

    def _bind_progression_log_controls(self) -> None:
        if not self.enable_progression_log:
            return
        self.accept("f1", self.toggle_progression_log)

    def reset_story_trigger_for_new_run(self) -> None:
        self._story_trigger_attempted = False
        self.story_runtime_error = None
        if self.story_popup_view is not None:
            self.story_popup_view.hide()
        if self.story_popup_controller is not None:
            self.story_popup_controller.clear()

    def is_story_popup_active(self) -> bool:
        return bool(
            self.story_popup_controller is not None
            and self.story_popup_controller.active_state is not None
        )

    def is_progression_log_active(self) -> bool:
        return bool(self.progression_log_view is not None and self.progression_log_view.visible)

    def update_game(self, task):
        if not self.is_progression_log_active():
            self._maybe_trigger_story_popup()
        return super().update_game(task)

    def step_simulation(self, dt):
        if self.is_story_popup_active() or self.is_progression_log_active():
            return
        return super().step_simulation(dt)

    def toggle_progression_log(self) -> None:
        if self.is_progression_log_active():
            self.hide_progression_log()
        else:
            self.show_progression_log()

    def show_progression_log(self) -> None:
        if not self.enable_progression_log:
            return
        if self.is_story_popup_active():
            return
        if self.progression_log_builder is None or self.progression_log_view is None:
            return
        if not self.profile:
            return
        try:
            state = self.progression_log_builder.build(self.profile)
            self.progression_log_error = None
            self.progression_log_view.show(state, on_close=self.hide_progression_log)
        except Exception as exc:
            self.progression_log_error = str(exc)
            print(f"[Progression] Failed to build progression log: {exc}", file=sys.stderr)

    def hide_progression_log(self) -> None:
        if self.progression_log_view is not None:
            self.progression_log_view.hide()

    def _maybe_trigger_story_popup(self) -> None:
        if not self.enable_story_popups:
            return
        if self.story_popup_controller is None or self.story_popup_view is None:
            return
        if self.story_runtime_error is not None:
            return
        if self.is_story_popup_active() or self.is_progression_log_active():
            return
        if not self.profile or not self.profile_store:
            return
        if self.state_mgr.current_state != GameStateID.PLAYING:
            return
        if getattr(self.state_mgr, "intro_active", False):
            return
        if self.state_mgr.map_id != self.default_map_id:
            return
        if self._story_trigger_attempted:
            return

        self._story_trigger_attempted = True
        try:
            updated_profile, popup_state = self.story_popup_controller.start_story(
                self.profile,
                self.default_story_id,
            )
            if updated_profile != self.profile:
                self.profile_store.save_profile(updated_profile)
                self.profile = updated_profile
            if popup_state is not None:
                self.story_popup_view.show(
                    popup_state,
                    on_advance=self.advance_story_popup,
                    on_choice=self.choose_story_popup,
                )
        except Exception as exc:
            self.story_runtime_error = str(exc)
            print(f"[Story] Failed to trigger story popup: {exc}", file=sys.stderr)

    def advance_story_popup(self) -> None:
        if not self.is_story_popup_active():
            return
        active_state = self.story_popup_controller.active_state
        if active_state and active_state.requires_choice:
            return
        self._advance_story_popup(choice_index=None)

    def choose_story_popup(self, choice_index: int) -> None:
        if not self.is_story_popup_active():
            return
        active_state = self.story_popup_controller.active_state
        if active_state is None or not active_state.requires_choice:
            return
        self._advance_story_popup(choice_index=choice_index)

    def _advance_story_popup(self, choice_index: Optional[int]) -> None:
        if self.story_popup_controller is None or self.story_popup_view is None:
            return
        if not self.profile or not self.profile_store:
            return

        try:
            result = self.story_popup_controller.advance(
                self.profile,
                choice_index=choice_index,
            )
            updated_profile = result.profile
            if result.eligible_reward_ids:
                reward_result = self._apply_reward_ids(
                    updated_profile,
                    result.eligible_reward_ids,
                )
                updated_profile = reward_result.profile
                if reward_result.granted_reward_ids:
                    print(f"[Story] Applied story rewards: {reward_result.granted_reward_ids}")
                if reward_result.skipped_reward_ids:
                    print(f"[Story] Skipped story rewards: {reward_result.skipped_reward_ids}")

            self.profile_store.save_profile(updated_profile)
            self.profile = updated_profile

            if result.next_state is None:
                self.story_popup_view.hide()
            else:
                self.story_popup_view.show(
                    result.next_state,
                    on_advance=self.advance_story_popup,
                    on_choice=self.choose_story_popup,
                )
        except Exception as exc:
            self.story_runtime_error = str(exc)
            print(f"[Story] Failed to advance story popup: {exc}", file=sys.stderr)

    def _apply_reward_ids(self, profile, reward_ids: Iterable[str]):
        from space_demo.profile.reward_grants import (
            RewardGrantService,
            apply_reward_ids_to_profile,
        )

        reward_service = RewardGrantService(rewards_path=self.rewards_path)
        result = apply_reward_ids_to_profile(profile, reward_ids, reward_service)
        self.reward_runtime_error = None
        return result

    def handle_post_run_integration(self):
        if getattr(self, "_post_run_integrated", False):
            return
        self._post_run_integrated = True

        if not self.profile or not self.profile_store:
            return

        from space_demo.profile.runtime import (
            QuestProgressionService,
            apply_quest_progress_for_snapshot,
            build_gameplay_snapshot_from_state,
        )

        snapshot = build_gameplay_snapshot_from_state(self.state_mgr)
        if snapshot is None:
            print("[Quest] No map context available. Skipping quest integration.")
            return

        print(f"[Quest] Processing post-run integration with snapshot: {snapshot}")

        try:
            quest_service = QuestProgressionService(quests_path=self.quests_path)
            new_profile, reward_ids = apply_quest_progress_for_snapshot(
                self.profile,
                snapshot,
                quest_service,
            )
            if reward_ids:
                reward_result = self._apply_reward_ids(new_profile, reward_ids)
                new_profile = reward_result.profile
                if reward_result.granted_reward_ids:
                    print(f"[Quest] Applied quest rewards: {reward_result.granted_reward_ids}")
                if reward_result.skipped_reward_ids:
                    print(f"[Quest] Skipped quest rewards: {reward_result.skipped_reward_ids}")

            self.profile_store.save_profile(new_profile)
            self.profile = new_profile
        except Exception as exc:
            self.reward_runtime_error = str(exc)
            print(f"[Quest] Failed to update quest/reward progression: {exc}")
