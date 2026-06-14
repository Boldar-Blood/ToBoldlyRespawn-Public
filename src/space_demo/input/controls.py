import sys
from space_demo import config
from space_demo.core.ids import GameStateID

class InputManager:
    """Manages all keyboard controls state, input bindings, routing, and transition handlers."""
    def __init__(self, app):
        self.app = app
        self.headless = app.headless
        self.keys = app.keys
        
        if not self.headless:
            self.setup_inputs()

    def _sync_cursor(self):
        """Apply the cursor policy immediately after input-driven state changes."""
        if not self.headless and hasattr(self.app, "sync_cursor_for_current_state"):
            self.app.sync_cursor_for_current_state()

    def _reset_story_trigger_for_new_run(self):
        if hasattr(self.app, "reset_story_trigger_for_new_run"):
            self.app.reset_story_trigger_for_new_run()

    def _allow_bomb_no_ammo_notice(self) -> bool:
        clock = getattr(self.app, "clock", None)
        now = clock.getFrameTime() if clock is not None else 0.0
        next_time = getattr(self.app, "_next_bomb_no_ammo_notice_time", -1.0)
        if now < next_time:
            return False
        self.app._next_bomb_no_ammo_notice_time = now + 0.75
        return True

    def _sync_post_input_terminal_state(self):
        """Synchronize terminal-state presentation after an input handler changes state.

        Some input handlers, especially Executive Decision, can transition from PLAYING to
        VICTORY before the next frame simulation starts. Base frame simulation intentionally
        skips gameplay work once the state is terminal, so the terminal UI must be synchronized
        immediately here instead of waiting for the next gameplay tick.
        """
        if self.headless:
            return

        if hasattr(self.app, "process_events"):
            self.app.process_events()

        state = self.app.state_mgr.current_state
        if state not in (GameStateID.VICTORY, GameStateID.GAMEOVER, GameStateID.PAUSED, GameStateID.MENU):
            return

        screens = getattr(self.app, "screens", None)
        if screens is not None:
            screens.update_screen_state(state)

        if state == GameStateID.VICTORY:
            if hasattr(self.app, "player_np"):
                self.app.player_np.show()
            if hasattr(self.app, "hud"):
                self.app.hud.hide()
            if hasattr(self.app, "menu_bg_np"):
                self.app.menu_bg_np.hide()
            if hasattr(self.app, "view_sync"):
                self.app.view_sync.sync_views()
        elif state == GameStateID.GAMEOVER:
            if hasattr(self.app, "player_np"):
                self.app.player_np.hide()
            if hasattr(self.app, "hud"):
                self.app.hud.hide()
            if hasattr(self.app, "menu_bg_np"):
                self.app.menu_bg_np.hide()
            if hasattr(self.app, "clear_views"):
                self.app.clear_views()
        elif state == GameStateID.MENU:
            if hasattr(self.app, "player_np"):
                self.app.player_np.hide()
            if hasattr(self.app, "hud"):
                self.app.hud.hide()
            if hasattr(self.app, "menu_bg_np"):
                self.app.menu_bg_np.show()
            if hasattr(self.app, "clear_views"):
                self.app.clear_views()

        if hasattr(self.app, "update_3d_menu_texts"):
            self.app.update_3d_menu_texts()
        self._sync_cursor()
            
    def setup_inputs(self):
        # Register key down/up events separately for Co-Op split handling
        self.app.accept("arrow_left", self.set_key, ["arrow_left", True])
        self.app.accept("arrow_left-up", self.set_key, ["arrow_left", False])
        self.app.accept("arrow_right", self.set_key, ["arrow_right", True])
        self.app.accept("arrow_right-up", self.set_key, ["arrow_right", False])
        self.app.accept("arrow_up", self.set_key, ["arrow_up", True])
        self.app.accept("arrow_up-up", self.set_key, ["arrow_up", False])
        
        # Arrow Down acts as secondary weapons fire in Co-Op, but normal steer in Single Player
        self.app.accept("arrow_down", self.handle_arrow_down)
        self.app.accept("arrow_down-up", self.handle_arrow_down_up)
        
        # Alternate WASD mapping (Pilot navigation)
        self.app.accept("a", self.set_key, ["left", True])
        self.app.accept("a-up", self.set_key, ["left", False])
        self.app.accept("d", self.set_key, ["right", True])
        self.app.accept("d-up", self.set_key, ["right", False])
        self.app.accept("w", self.set_key, ["up", True])
        self.app.accept("w-up", self.set_key, ["up", False])
        self.app.accept("s", self.set_key, ["down", True])
        self.app.accept("s-up", self.set_key, ["down", False])
        
        # Firing and controls keys (Single Player fire triggers)
        self.app.accept("space", self.set_key, ["space", True])
        self.app.accept("space-up", self.set_key, ["space", False])
        self.app.accept("c", self.fire_missile)
        self.app.accept("b", self.handle_bomb_key)
        
        # Menu/State control transitions
        self.app.accept("enter", self.handle_enter)
        self.app.accept("r", self.handle_restart)
        self.app.accept("escape", self.handle_escape)
        self.app.accept("p", self.toggle_pause)
        self.app.accept("q", self.handle_bridge)
        self.app.accept("tab", self.toggle_tactical_console)
        self.app.accept("l", self.toggle_tactical_log)
        self.app.accept("g", self.toggle_pursuit_gauge)

    def set_key(self, key, value):
        self.keys[key] = value

    def handle_bomb_key(self):
        if self.app.state_mgr.current_state in (GameStateID.PLAYING, "playing"):
            fired = self.app.state_mgr.trigger_executive_decision(self.app.player.x, self.app.player.y)
            if not fired:
                if not self._allow_bomb_no_ammo_notice():
                    return
                from space_demo.core.events import NotificationEvent
                self.app.state_mgr.post_event(NotificationEvent(
                    title="Audit Error",
                    message="NO DECISIONS LEFT",
                    category="no-ammo",
                    severity="warning"
                ))
                return
            self._sync_post_input_terminal_state()


    def handle_arrow_down(self):
        if self.app.state_mgr.coop_mode:
            self.fire_missile()
        else:
            self.set_key("arrow_down", True)

    def handle_arrow_down_up(self):
        self.set_key("arrow_down", False)

    def handle_enter(self):
        if hasattr(self.app, "is_story_popup_active") and self.app.is_story_popup_active():
            self.app.advance_story_popup()
            return

        if self.app.state_mgr.current_state == GameStateID.MENU and self.app.screens.menu_sub_state == "main":
            self._reset_story_trigger_for_new_run()
            self.app.state_mgr.start_game()
            self.app.player.reset()
            self.app.clear_views()
            
            # Switch tracks to intense chase chiptune
            if not self.headless:
                if self.app.audio_mgr.menu_music:
                    self.app.audio_mgr.menu_music.stop()
                if self.app.audio_mgr.chase_music:
                    self.app.audio_mgr.chase_music.play()
                self.app.screens.update_screen_state(self.app.state_mgr.current_state)
                self.app.hud.show()
                self.app.hint_arrow_timer = 10.0
                if hasattr(self.app, "hint_arrow_np"):
                    self.app.hint_arrow_np.show()
                    self.app.hint_arrow_np.setColorScale(1.0, 1.0, 1.0, 1.0)
                self._sync_cursor()
        elif self.app.state_mgr.current_state == GameStateID.PLAYING and getattr(self.app.state_mgr, "intro_active", False):
            if not self.headless:
                self.app.hud.dismiss_controls_callout()
                self._sync_cursor()
            else:
                self.app.state_mgr.intro_active = False

    def handle_restart(self):
        self._reset_story_trigger_for_new_run()
        self.app.state_mgr.start_game()
        self.app.player.reset()
        self.app.clear_views()
        
        # Switch tracks to intense chase chiptune
        if not self.headless:
            if self.app.audio_mgr.menu_music:
                self.app.audio_mgr.menu_music.stop()
            if self.app.audio_mgr.chase_music:
                self.app.audio_mgr.chase_music.play()
            self.app.screens.update_screen_state(self.app.state_mgr.current_state)
            self.app.hud.show()
            self.app.hint_arrow_timer = 10.0
            if hasattr(self.app, "hint_arrow_np"):
                self.app.hint_arrow_np.show()
                self.app.hint_arrow_np.setColorScale(1.0, 1.0, 1.0, 1.0)
            self._sync_cursor()

    def fire_missile(self):
        if self.app.state_mgr.current_state == GameStateID.PLAYING:
            if self.app.state_mgr.missile_ammo > 0:
                self.app.state_mgr.missile_ammo -= 1
                self.app.state_mgr.spawn_projectile(self.app.player.x, self.app.player.y - 0.5, is_player_owned=True, proj_type="missile")
                self.app.play_sound(self.app.audio_mgr.missile_sfx)
                self.app.vfx_mgr.spawn_muzzle_flash(self.app.player.x, self.app.player.y - 0.6, scale=1.8)
                print(f"[Weapons] Launched Anti-Matter Missile! Ammo left: {self.app.state_mgr.missile_ammo}")
            else:
                from space_demo.core.events import NotificationEvent
                self.app.state_mgr.post_event(NotificationEvent(
                    title="Audit Error",
                    message="NO MISSILES LEFT",
                    category="no-ammo",
                    severity="warning"
                ))


    def handle_escape(self):
        if hasattr(self.app, "is_progression_log_active") and self.app.is_progression_log_active():
            self.app.hide_progression_log()
            return

        state = self.app.state_mgr.current_state
        screens = getattr(self.app, "screens", None)

        if state == GameStateID.MENU:
            menu_sub_state = getattr(screens, "menu_sub_state", "main") if screens is not None else "main"
            if menu_sub_state != "main":
                confirm_modal = getattr(screens, "confirm_modal", None)
                if confirm_modal is not None and not confirm_modal.isHidden():
                    screens.on_confirm_cancel()
                else:
                    screens.on_back_click()
                self._sync_cursor()
                return
            sys.exit(0)

        if state == GameStateID.PLAYING:
            self.app.state_mgr.transition_to(GameStateID.PAUSED)
            if not self.headless and screens is not None:
                screens.update_screen_state(self.app.state_mgr.current_state)
                self._sync_cursor()
            return

        if state == GameStateID.PAUSED:
            self.app.state_mgr.transition_to(GameStateID.PLAYING)
            if not self.headless and screens is not None:
                screens.update_screen_state(self.app.state_mgr.current_state)
                self._sync_cursor()
            return

        if state in (GameStateID.GAMEOVER, GameStateID.VICTORY):
            self.handle_bridge()

    def handle_bridge(self):
        """Return to the Bridge from terminal states or the pause overlay.

        Escape remains the reversible pause/resume key. Returning to the Bridge is
        intentionally explicit so players do not accidentally abandon a run while
        trying to close the pause overlay.
        """
        state = self.app.state_mgr.current_state
        if state not in (GameStateID.PAUSED, GameStateID.GAMEOVER, GameStateID.VICTORY):
            return

        screens = getattr(self.app, "screens", None)
        self.app.state_mgr.transition_to(GameStateID.MENU)
        if screens is not None:
            screens.menu_sub_state = "main"
        if hasattr(self.app, "clear_views"):
            self.app.clear_views()
        if not self.headless:
            if getattr(self.app.audio_mgr, "chase_music", None):
                self.app.audio_mgr.chase_music.stop()
            if getattr(self.app.audio_mgr, "menu_music", None):
                self.app.audio_mgr.menu_music.play()
            if screens is not None:
                screens.update_screen_state(self.app.state_mgr.current_state)
            if hasattr(self.app, "hud"):
                self.app.hud.hide()
            if hasattr(self.app, "menu_bg_np"):
                self.app.menu_bg_np.show()
            if hasattr(self.app, "player_np"):
                self.app.player_np.hide()
            self._sync_cursor()

    def handle_t(self):
        if hasattr(self.app, "screens") and self.app.screens and self.app.state_mgr.current_state == GameStateID.MENU and self.app.screens.menu_sub_state == "main":
            self.app.screens.menu_sub_state = "tutorial"
            self.app.screens.update_screen_state(self.app.state_mgr.current_state)
            self._sync_cursor()

    def handle_s(self):
        if hasattr(self.app, "screens") and self.app.screens and self.app.state_mgr.current_state == GameStateID.MENU and self.app.screens.menu_sub_state == "main":
            self.app.screens.menu_sub_state = "settings"
            self.app.screens.update_screen_state(self.app.state_mgr.current_state)
            self._sync_cursor()

    def handle_b(self):
        if hasattr(self.app, "screens") and self.app.screens and self.app.state_mgr.current_state == GameStateID.MENU and self.app.screens.menu_sub_state != "main":
            self.app.screens.menu_sub_state = "main"
            self.app.screens.update_screen_state(self.app.state_mgr.current_state)
            self._sync_cursor()

    def handle_f(self):
        if hasattr(self.app, "screens") and self.app.screens and self.app.state_mgr.current_state == GameStateID.MENU and self.app.screens.menu_sub_state == "settings":
            if not self.headless:
                from panda3d.core import WindowProperties
                props = WindowProperties()
                is_full = self.app.win.getProperties().getFullscreen()
                next_full = not is_full
                props.setFullscreen(next_full)
                
                if next_full:
                    # Locked to native display monitor dimensions to prevent driver stretch
                    w = self.app.pipe.getDisplayWidth()
                    h = self.app.pipe.getDisplayHeight()
                    if w > 0 and h > 0:
                        props.setSize(w, h)
                    else:
                        props.setSize(1920, 1080)
                    print(f"[Window] Entering Fullscreen at resolution: {w}x{h}")
                else:
                    # Return to centered windowed mode at 1280x720
                    props.setSize(1280, 720)
                    w = self.app.pipe.getDisplayWidth()
                    h = self.app.pipe.getDisplayHeight()
                    if w > 0 and h > 0:
                        props.setOrigin((w - 1280) // 2, (h - 720) // 2)
                    print("[Window] Exiting Fullscreen to centered 1280x720 viewport")
                    
                self.app.win.requestProperties(props)

    def toggle_pause(self):
        if self.app.state_mgr.current_state == GameStateID.PLAYING:
            self.app.state_mgr.transition_to(GameStateID.PAUSED)
            if not self.headless:
                self.app.screens.update_screen_state(self.app.state_mgr.current_state)
                self._sync_cursor()
        elif self.app.state_mgr.current_state == GameStateID.PAUSED:
            self.app.state_mgr.transition_to(GameStateID.PLAYING)
            if not self.headless:
                self.app.screens.update_screen_state(self.app.state_mgr.current_state)
                self._sync_cursor()

    def toggle_tactical_console(self):
        if self.app.state_mgr.current_state != GameStateID.PLAYING or self.headless:
            return
        if hasattr(self.app.hud, "set_tactical_console_visible"):
            current = getattr(self.app.hud, "tactical_console_visible", True)
            self.app.hud.set_tactical_console_visible(not current)

    def toggle_tactical_log(self):
        if self.app.state_mgr.current_state != GameStateID.PLAYING or self.headless:
            return
        if hasattr(self.app.hud, "set_log_panel_visible"):
            current = getattr(self.app.hud, "log_panel_visible", True)
            self.app.hud.set_log_panel_visible(not current)

    def toggle_pursuit_gauge(self):
        if self.app.state_mgr.current_state != GameStateID.PLAYING or self.headless:
            return
        if hasattr(self.app.hud, "set_pursuit_gauge_visible"):
            current = getattr(self.app.hud, "pursuit_gauge_visible", True)
            self.app.hud.set_pursuit_gauge_visible(not current)
