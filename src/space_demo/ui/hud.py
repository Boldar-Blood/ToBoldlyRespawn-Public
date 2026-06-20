"""Canonical gameplay HUD for To Boldly Respawn.

The HUD owns gameplay-only DirectGUI widgets and reads reusable layout policy
from ``space_demo.ui.layout``. Keeping the Panda3D node creation here and the
geometry decisions in layout helpers makes the HUD easier to test, refactor,
and reuse without monkey-patching module exports.
"""

from __future__ import annotations

import math
from typing import Any

from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel
import direct.gui.DirectGuiGlobals as DGG
from panda3d.core import TextNode, TransparencyAttrib

from space_demo import config
from space_demo.ui.components import (
    GameButton,
    GameMeter,
    GamePanel,
    wrap_text_lines,
    UILabelSpec,
    create_label_from_spec,
    update_label_from_spec,
    update_label_text,
)
from space_demo.ui.layout.gameplay_hud import build_gameplay_hud_layout
from space_demo.ui.layout.panel_state import HudPanel, HudPanelController, HudPanelPresentation
from space_demo.ui.layout.viewport import ViewportContext
from space_demo.ui.theme import COLORS, LAYERS, effective_text_scale


CRITICAL_DREADNOUGHT_COLOR = (0.7, 0.08, 0.08, 0.90)
HUD_TOGGLE_FRAME_COLOR = (0.005, 0.010, 0.030, 0.92)
HUD_TOGGLE_HOVER_COLOR = (0.02, 0.18, 0.27, 0.98)
HUD_TOGGLE_WIDTH = 0.046
HUD_TOGGLE_HEIGHT = 0.042


class GameHUD:
    """Own gameplay-only HUD widgets and update them from game state."""

    def __init__(self, app: Any = None, font: Any = None) -> None:
        self.app = app
        self.font = font
        self.visible = False
        settings = getattr(app, "settings", None)
        self.ui_scale = getattr(settings, "ui_scale", 1.0)
        self.text_scale = getattr(settings, "text_scale", 1.0)
        self.assets = getattr(app, "assets_mgr", None) or getattr(app, "assets", None)
        viewport = ViewportContext.from_window(getattr(app, "win", None)) if app else None
        density = getattr(settings, "hud_density", None)
        self.layout = build_gameplay_hud_layout(
            ui_scale=self.ui_scale,
            viewport=viewport,
            preferred_density=density,
        )
        self.panel_controller = HudPanelController(self.layout.profile)

        self._build_left_console()
        self._build_top_banner()
        self._build_pursuit_gauge()
        self._build_intro_modal()
        self._build_notifications()
        self.hide()

    # ------------------------------------------------------------------
    # Shared DirectGUI helpers
    # ------------------------------------------------------------------
    def _asset(self, *names: str):
        """Return the first loaded texture matching one of the given names."""
        if not self.assets:
            return None
        for name in names:
            tex = getattr(self.assets, name, None)
            if tex is not None:
                return tex
        return None

    def _effective_text_scale(self) -> float:
        """Return readability-adjusted text scale for the active settings."""
        settings = getattr(self.app, "settings", None)
        user_scale = getattr(settings, "text_scale", self.text_scale)
        resolution = getattr(settings, "resolution", (1280, 720))
        return effective_text_scale(user_scale, resolution)

    def _label(
        self,
        parent,
        text: str,
        pos,
        scale: float,
        color=COLORS.text_primary,
        align=TextNode.ACenter,
    ) -> DirectLabel:
        """Create a readable HUD label."""
        spec = UILabelSpec(
            text=text,
            pos=pos,
            base_scale=scale,
            color=color,
            align=align,
        )
        return create_label_from_spec(parent, spec, self.font, self._effective_text_scale())

    def _bar(self, parent, z_pos: float, color):
        """Create a left-filled meter bar."""
        bg = DirectFrame(
            parent=parent,
            frameSize=(-0.115 * self.ui_scale, 0.115 * self.ui_scale, -0.006 * self.ui_scale, 0.006 * self.ui_scale),
            pos=(0, 0, z_pos),
            frameColor=(0.02, 0.03, 0.06, 0.95),
            relief=DGG.FLAT,
        )
        fg = DirectFrame(
            parent=parent,
            frameSize=(0, 0.23 * self.ui_scale, -0.006 * self.ui_scale, 0.006 * self.ui_scale),
            pos=(-0.115 * self.ui_scale, 0, z_pos),
            frameColor=color,
            relief=DGG.FLAT,
        )
        return bg, fg

    def _panel_toggle_button(self, parent, arrow: str, pos, command) -> DirectButton:
        """Create a compact icon-only HUD collapse/expand tab."""
        width = HUD_TOGGLE_WIDTH * self.ui_scale
        height = HUD_TOGGLE_HEIGHT * self.ui_scale
        button = DirectButton(
            parent=parent,
            text=arrow,
            command=command,
            pos=pos,
            frameSize=(-width / 2, width / 2, -height / 2, height / 2),
            frameColor=HUD_TOGGLE_FRAME_COLOR,
            relief=DGG.FLAT,
            text_font=self.font,
            text_scale=0.017 * self._effective_text_scale(),
            text_align=TextNode.ACenter,
            text_pos=(0.0, -0.0055 * self.ui_scale),
            text_fg=COLORS.cyan,
            text_shadow=(0.0, 0.0, 0.0, 0.95),
            rolloverSound=None,
            clickSound=None,
            sortOrder=LAYERS.button + 8,
        )
        button.setTransparency(TransparencyAttrib.MAlpha)
        button.bind(DGG.WITHIN, lambda event=None, node=button: node.configure(frameColor=HUD_TOGGLE_HOVER_COLOR))
        button.bind(DGG.WITHOUT, lambda event=None, node=button: node.configure(frameColor=HUD_TOGGLE_FRAME_COLOR))
        return button

    def _set_panel_toggle_visual(self, button: DirectButton, arrow: str) -> None:
        """Update an icon-only HUD tab when its panel changes state."""
        width = HUD_TOGGLE_WIDTH * self.ui_scale
        height = HUD_TOGGLE_HEIGHT * self.ui_scale
        button["text"] = arrow
        button["frameSize"] = (-width / 2, width / 2, -height / 2, height / 2)
        button["text_scale"] = 0.017 * self._effective_text_scale()
        button["text_pos"] = (0.0, -0.0055 * self.ui_scale)
        button["frameColor"] = HUD_TOGGLE_FRAME_COLOR

    # ------------------------------------------------------------------
    # HUD builders
    # ------------------------------------------------------------------
    def _build_left_console(self) -> None:
        """Build the left tactical console."""
        console_parent = self.app.a2dTopLeft if self.app and hasattr(self.app, "a2dTopLeft") else None
        self.console_panel = GamePanel(
            parent=console_parent,
            name="hud_tactical_console",
            pos=(0.19 * self.ui_scale, 0, -0.42 * self.ui_scale),
            size=(0.32 * self.ui_scale, 0.78 * self.ui_scale),
            bg_color=COLORS.panel_bg_dark,
            stroke_color=COLORS.panel_stroke,
            border_thickness=0.005 * self.ui_scale,
        )
        # The console's right edge is 0.35 at ui_scale=1.0. Place the toggle
        # outside that edge with its left edge flush against the panel border.
        self.console_toggle_expanded_pos = (0.373 * self.ui_scale, 0, -0.030 * self.ui_scale)
        self.console_toggle_collapsed_pos = (0.023 * self.ui_scale, 0, -0.030 * self.ui_scale)
        self.console_toggle_btn = self._panel_toggle_button(
            parent=console_parent,
            arrow="<",
            pos=self.console_toggle_expanded_pos,
            command=lambda: self.toggle_panel(HudPanel.TACTICAL_CONSOLE),
        )
        root = self.console_panel.root
        self.console_title = self._label(root, "TACTICAL CONSOLE", (0, 0, 0.335 * self.ui_scale), 0.019, COLORS.cyan)
        self.console_divider = DirectFrame(
            parent=root,
            frameSize=(-0.13 * self.ui_scale, 0.13 * self.ui_scale, -0.0015 * self.ui_scale, 0.0015 * self.ui_scale),
            pos=(0, 0, 0.300 * self.ui_scale),
            frameColor=COLORS.panel_stroke,
            relief=DGG.FLAT,
        )
        self.hull_label = self._label(root, "REAR HULL: 100/100", (0, 0, 0.245 * self.ui_scale), 0.020)
        self.hull_bar_bg, self.hull_bar = self._bar(root, 0.215 * self.ui_scale, COLORS.green)
        self.score_label = self._label(root, "SYNERGY VALUE: 0", (0, 0, 0.125 * self.ui_scale), 0.020, COLORS.text_warning)
        self.multiplier_label = self._label(root, "SYNERGY MULT: 1.0x", (0, 0, 0.080 * self.ui_scale), 0.018)
        self.missile_label = self._label(root, "MISSILES: 3/10", (0, 0, 0.015 * self.ui_scale), 0.019)
        self.missile_bar_bg, self.missile_bar = self._bar(root, -0.015 * self.ui_scale, COLORS.red)
        self.bomb_label = self._label(root, "DECISIONS: 1/3", (0, 0, -0.085 * self.ui_scale), 0.019)
        self.bomb_bar_bg, self.bomb_bar = self._bar(root, -0.115 * self.ui_scale, COLORS.orange)
        self.magnet_pill = self._label(root, "MAGNET: 0.0s", (0, 0, -0.190 * self.ui_scale), 0.017, COLORS.purple)
        self.intern_pill = self._label(root, "INTERN: 0.0s", (0, 0, -0.235 * self.ui_scale), 0.017, COLORS.cyan)
        self.pause_btn_comp = GameButton(
            parent=root,
            text="PAUSE [P]",
            command=self.on_pause_click,
            pos=(0, 0, -0.320 * self.ui_scale),
            size="small",
            variant="warning",
            font=self.font,
            ui_scale=self.ui_scale,
            text_scale=self._effective_text_scale(),
            width=0.24,
            height=0.060,
        )
        self.pause_btn = self.pause_btn_comp.node

        # Backward compatibility aliases used by existing regression tests.
        self.hp_pill = self.hull_label
        self.score_pill = self.score_label
        self.missile_pill = self.missile_label
        self.bomb_pill = self.bomb_label

    def _build_top_banner(self) -> None:
        """Build top-right phase banner and hidden boss meter."""
        self.wave_panel = GamePanel(
            parent=self.app.a2dTopRight if self.app and hasattr(self.app, "a2dTopRight") else None,
            name="hud_wave_panel",
            pos=(-0.39 * self.ui_scale, 0, -0.055 * self.ui_scale),
            size=(0.58 * self.ui_scale, 0.075 * self.ui_scale),
            bg_color=(0.005, 0.014, 0.032, 0.76),
            stroke_color=COLORS.purple,
            border_thickness=0.004 * self.ui_scale,
        )
        self.wave_pill = self._label(self.wave_panel.root, "Phase 1: Strategic Retreat 101", (0, 0, -0.008 * self.ui_scale), 0.023)
        self.boss_meter = GameMeter(
            parent=self.app.aspect2d if self.app else None,
            label="AUDIT DREADNOUGHT CLASS CLIMAX",
            pos=(0, 0, 0.80 * self.ui_scale),
            width=0.66 * self.ui_scale,
            height=0.040 * self.ui_scale,
            font=self.font,
        )
        self.boss_meter.hide()
        self.bark_label = self._label(
            self.app.aspect2d if self.app else None,
            "",
            (0, 0, 0.50 * self.ui_scale),
            0.026,
            COLORS.cyan,
        )

    def _build_pursuit_gauge(self) -> None:
        """Build the right-side dreadnought pursuit gauge."""
        pursuit_parent = self.app.a2dRightCenter if self.app and hasattr(self.app, "a2dRightCenter") else None
        layout = self.layout
        self.pursuit_panel = GamePanel(
            parent=pursuit_parent,
            name="hud_pursuit_panel",
            pos=layout.pursuit_panel_pos,
            size=layout.pursuit_panel_size,
            bg_color=COLORS.panel_bg_dark,
            stroke_color=COLORS.amber,
            border_thickness=0.005 * self.ui_scale,
        )
        self.pursuit_toggle_expanded_pos = layout.pursuit_toggle_expanded_pos
        self.pursuit_toggle_collapsed_pos = layout.pursuit_toggle_collapsed_pos
        self.pursuit_toggle_btn = self._panel_toggle_button(
            parent=pursuit_parent,
            arrow=">",
            pos=self.pursuit_toggle_expanded_pos,
            command=lambda: self.toggle_panel(HudPanel.PURSUIT_GAUGE),
        )
        root = self.pursuit_panel.root
        track_tex = self._asset("ui_pursuit_gauge_tex")
        track_w, track_h = layout.pursuit_track_size
        self.pursuit_track = DirectFrame(
            parent=root,
            frameSize=(-track_w / 2, track_w / 2, -track_h / 2, track_h / 2),
            pos=layout.pursuit_track_pos,
            frameTexture=track_tex,
            frameColor=(1, 1, 1, 1) if track_tex else (0.05, 0.10, 0.20, 0.85),
            relief=DGG.FLAT,
        )
        self.player_icon = DirectFrame(
            parent=root,
            frameSize=(-0.032 * self.ui_scale, 0.032 * self.ui_scale, -0.032 * self.ui_scale, 0.032 * self.ui_scale),
            pos=layout.player_icon_pos,
            frameTexture=self._asset("player_hull_100_tex", "player_tex", "icon_player_mini_tex"),
            frameColor=(1, 1, 1, 1),
            relief=DGG.FLAT,
        )
        self.escape_label = self._label(root, "YOU / ESCAPE", layout.escape_label_pos, 0.0105, COLORS.cyan)
        self.dread_icon = DirectFrame(
            parent=root,
            frameSize=(-0.035 * self.ui_scale, 0.035 * self.ui_scale, -0.028 * self.ui_scale, 0.028 * self.ui_scale),
            pos=(0, 0, layout.dread_icon_bottom_z),
            frameTexture=self._asset("boss_phase_1_tex", "icon_dreadnought_mini_tex"),
            frameColor=(1, 1, 1, 1),
            relief=DGG.FLAT,
        )
        for node in (self.pursuit_track, self.player_icon, self.dread_icon):
            node.setTransparency(TransparencyAttrib.MAlpha)
        self.proximity_label = self._label(root, "DREADNOUGHT GAP\n200.0 m", layout.proximity_label_pos, 0.0105)
        self.prox_panel = self.pursuit_panel

        # Build Escape route progress bar (at the bottom of the pursuit panel)
        bg_w, bg_h = layout.distance_bar_bg_size
        self.distance_bar_bg = DirectFrame(
            parent=root,
            frameSize=(-bg_w / 2, bg_w / 2, -bg_h / 2, bg_h / 2),
            pos=layout.distance_bar_bg_pos,
            frameColor=(0.02, 0.03, 0.06, 0.95),
            relief=DGG.FLAT,
        )
        
        fg_w, fg_h = layout.distance_bar_fg_size
        self.distance_bar = DirectFrame(
            parent=root,
            frameSize=(0, fg_w, -fg_h / 2, fg_h / 2),
            pos=layout.distance_bar_fg_pos,
            frameColor=COLORS.cyan,
            relief=DGG.FLAT,
        )
        
        self.distance_remaining_label = self._label(
            root,
            "ESCAPE: 1000 m",
            layout.distance_remaining_label_pos,
            0.010,
            color=COLORS.text_primary,
            align=TextNode.ACenter
        )

    def _build_intro_modal(self) -> None:
        """Build the opening controls modal from gameplay HUD layout constants."""
        layout = self.layout
        self.controls_callout = DirectFrame(
            parent=self.app.aspect2d if self.app else None,
            pos=layout.intro_root_pos,
            relief=None,
        )
        self.controls_callout.setTransparency(TransparencyAttrib.MAlpha)
        self.controls_panel = GamePanel(
            parent=self.controls_callout,
            name="controls_modal_panel",
            pos=(0, 0, 0),
            size=layout.intro_panel_size,
            bg_color=(0.005, 0.014, 0.032, 0.90),
            stroke_color=COLORS.amber,
            border_thickness=0.007 * self.ui_scale,
        )
        root = self.controls_panel.root
        self.controls_title = self._label(
            root,
            "COWARDICE MODE ENGAGED",
            layout.intro_title_pos,
            0.034,
            COLORS.text_danger,
        )
        desc = (
            "[WASD / ARROWS] Navigate the retreat lane\n"
            "[SPACE] Fire rear laser downward\n"
            "[C] Anti-matter missile pushback\n"
            "[B] Executive decision bomb\n\n"
            "KEEP DREADNOUGHT GAP ABOVE 5 METERS"
        )
        self.controls_text = self._label(
            root,
            wrap_text_lines(desc, layout.intro_wrap_chars),
            layout.intro_text_pos,
            0.020,
            COLORS.text_warning,
        )
        self.controls_btn_comp = GameButton(
            parent=root,
            text="ACKNOWLEDGE KPIs [ENTER]",
            command=self.dismiss_controls_callout,
            pos=layout.intro_button_pos,
            size="modal",
            variant="success",
            font=self.font,
            ui_scale=self.ui_scale,
            text_scale=self._effective_text_scale(),
            width=layout.intro_button_width,
            height=layout.intro_button_height,
        )
        self.controls_btn = self.controls_btn_comp.node
        self.controls_close_comp = GameButton(
            parent=root,
            text="X",
            command=self.dismiss_controls_callout,
            pos=layout.intro_close_pos,
            size="small",
            variant="danger",
            font=self.font,
            ui_scale=self.ui_scale,
            text_scale=self._effective_text_scale(),
            width=0.060,
            height=0.060,
        )
        self.controls_close_btn = self.controls_close_comp.node

    def _build_notifications(self) -> None:
        """Build notifications with the canonical layout-backed manager."""
        from space_demo.ui.notifications import NotificationManager

        self.notifications = NotificationManager(app=self.app, font=self.font)

    # ------------------------------------------------------------------
    # Runtime handlers
    # ------------------------------------------------------------------
    def dismiss_controls_callout(self) -> None:
        """Dismiss the intro modal and return cursor focus to gameplay."""
        if self.app:
            self.app.state_mgr.intro_active = False
            self.controls_callout.hide()
            self.app.set_cursor_visible(False)

    def on_pause_click(self) -> None:
        """Forward pause-button clicks into the input manager."""
        if self.app:
            self.app.input_mgr.toggle_pause()

    def toggle_panel(self, panel: HudPanel | str) -> HudPanelPresentation:
        """Collapse or expand a HUD panel without changing gameplay state."""
        state = self.panel_controller.toggle_collapsed(panel)
        self._apply_panel_presentation()
        return state

    def set_panel_collapsed(self, panel: HudPanel | str, collapsed: bool) -> HudPanelPresentation:
        """Set a panel's collapsed state explicitly for input bindings/settings."""
        state = self.panel_controller.collapse(panel) if collapsed else self.panel_controller.expand(panel)
        self._apply_panel_presentation()
        return state

    def _apply_panel_presentation(self) -> None:
        """Apply current panel-controller state to Panda3D nodes."""
        if not self.visible:
            for node_name in ("console_toggle_btn", "pursuit_toggle_btn"):
                node = getattr(self, node_name, None)
                if node is not None:
                    node.hide()
            return

        console_state = self.panel_controller.state_for(HudPanel.TACTICAL_CONSOLE)
        if console_state.expanded:
            self.console_panel.show()
            self.console_toggle_btn.show()
            self.console_toggle_btn.setPos(self.console_toggle_expanded_pos)
            self._set_panel_toggle_visual(self.console_toggle_btn, "<")
        elif console_state.visible:
            self.console_panel.hide()
            self.console_toggle_btn.show()
            self.console_toggle_btn.setPos(self.console_toggle_collapsed_pos)
            self._set_panel_toggle_visual(self.console_toggle_btn, ">")
        else:
            self.console_panel.hide()
            self.console_toggle_btn.hide()

        pursuit_state = self.panel_controller.state_for(HudPanel.PURSUIT_GAUGE)
        if pursuit_state.expanded:
            self.pursuit_panel.show()
            self.pursuit_toggle_btn.show()
            self.pursuit_toggle_btn.setPos(self.pursuit_toggle_expanded_pos)
            self._set_panel_toggle_visual(self.pursuit_toggle_btn, ">")
        elif pursuit_state.visible:
            self.pursuit_panel.hide()
            self.pursuit_toggle_btn.show()
            self.pursuit_toggle_btn.setPos(self.pursuit_toggle_collapsed_pos)
            self._set_panel_toggle_visual(self.pursuit_toggle_btn, "<")
        else:
            self.pursuit_panel.hide()
            self.pursuit_toggle_btn.hide()

    def show(self) -> None:
        """Show gameplay HUD elements."""
        self.visible = True
        self.wave_panel.show()
        self.controls_callout.show()
        self.bark_label.show()
        self._apply_panel_presentation()
        if hasattr(self, "notifications"):
            self.notifications.show()

    def hide(self) -> None:
        """Hide gameplay HUD elements."""
        self.visible = False
        self.console_panel.hide()
        self.wave_panel.hide()
        self.boss_meter.hide()
        self.pursuit_panel.hide()
        self.controls_callout.hide()
        self.bark_label.hide()
        for node_name in ("console_toggle_btn", "pursuit_toggle_btn"):
            node = getattr(self, node_name, None)
            if node is not None:
                node.hide()
        if hasattr(self, "notifications"):
            self.notifications.hide()

    def _set_fraction_bar(self, bar, fraction: float, color) -> None:
        """Set a meter bar to a clamped fraction."""
        fraction = max(0.0, min(1.0, fraction))
        bar["frameSize"] = (0, 0.23 * fraction * self.ui_scale, -0.006 * self.ui_scale, 0.006 * self.ui_scale)
        bar["frameColor"] = color

    def update(self, state_mgr, player, dt: float = 0.0) -> None:
        """Update HUD widgets from current game state."""
        update_label_text(self.hull_label, f"REAR HULL: {state_mgr.player_hp}/{config.PLAYER_START_HP}")
        hull_fraction = max(0.0, min(1.0, state_mgr.player_hp / config.PLAYER_START_HP))
        hull_color = COLORS.red if state_mgr.player_hp <= 30 else COLORS.amber if state_mgr.player_hp <= 60 else COLORS.green
        self._set_fraction_bar(self.hull_bar, hull_fraction, hull_color)
        self.hull_label["text_fg"] = COLORS.text_danger if state_mgr.player_hp <= 30 else COLORS.text_primary

        update_label_text(self.score_label, f"SYNERGY VALUE: {state_mgr.score}")
        update_label_text(self.multiplier_label, f"SYNERGY MULT: {state_mgr.synergy_multiplier:.1f}x")
        self.multiplier_label["text_fg"] = COLORS.text_warning if state_mgr.synergy_multiplier > 1.0 else COLORS.text_primary
        update_label_text(self.missile_label, f"MISSILES: {state_mgr.missile_ammo}/{config.MAX_MISSILES}")
        self._set_fraction_bar(self.missile_bar, state_mgr.missile_ammo / config.MAX_MISSILES, COLORS.red)
        update_label_text(self.bomb_label, f"DECISIONS: {state_mgr.bomb_ammo}/3")
        self._set_fraction_bar(self.bomb_bar, state_mgr.bomb_ammo / 3, COLORS.orange)

        if state_mgr.magnet_active_timer > 0.0:
            update_label_text(self.magnet_pill, f"MAGNET: {state_mgr.magnet_active_timer:.1f}s")
            self.magnet_pill.show()
        else:
            self.magnet_pill.hide()
        if state_mgr.intern_active_timer > 0.0:
            update_label_text(self.intern_pill, f"INTERN: {state_mgr.intern_active_timer:.1f}s")
            self.intern_pill.show()
        else:
            self.intern_pill.hide()

        # Get canonical HUD progress state
        hud_state = state_mgr.compute_progress_hud_state()

        # Update escape progress bar (fill fraction)
        fg_w, fg_h = self.layout.distance_bar_fg_size
        self.distance_bar["frameSize"] = (0, fg_w * hud_state.progress_fraction, -fg_h / 2, fg_h / 2)
        self.distance_bar["frameColor"] = COLORS.cyan if not hud_state.is_final_phase else COLORS.amber

        # Update escape remaining label
        update_label_text(self.distance_remaining_label, f"ESCAPE: {hud_state.distance_remaining:.0f} m")
        self.distance_remaining_label["text_fg"] = COLORS.text_primary if not hud_state.is_final_phase else COLORS.text_warning

        # Update phase pill text using canonical HUD state
        update_label_text(self.wave_pill, f"Phase {hud_state.phase_index}: {hud_state.phase_name}")

        # Boss meter visibility based on canonical hud_state and boss activity
        if hud_state.is_final_phase and state_mgr.boss_active:
            self.boss_meter.show()
            boss_max = getattr(state_mgr, "boss_max_hp", config.DREADNOUGHT_MAX_HP)
            self.boss_meter.set_fraction(
                max(0.0, min(1.0, state_mgr.boss_hp / boss_max)),
                f"AUDIT DREADNOUGHT HP: {int(state_mgr.boss_hp)}/{int(boss_max)}",
            )
        else:
            self.boss_meter.hide()

        # Dreadnought proximity icon translation (sliding between bottom_z and top_z based on gap ratio)
        gap = state_mgr.chase_gap
        pressure = (config.INITIAL_CHASE_GAP - gap) / max(1.0, config.INITIAL_CHASE_GAP - config.DREADNOUGHT_CAPTURE_GAP)
        pressure = max(0.0, min(1.0, pressure))
        
        bottom_z = self.layout.dread_icon_bottom_z
        top_z = self.layout.dread_icon_top_z
        self.dread_icon.setZ(bottom_z + pressure * (top_z - bottom_z))
        if pressure < 0.5:
            self.dread_icon.setColorScale(0.70, 1.0, 0.75, 1.0)
        elif pressure < 0.85:
            self.dread_icon.setColorScale(1.0, 0.78, 0.25, 1.0)
        else:
            self.dread_icon.setColorScale(1.0, 0.30, 0.25, 1.0)

        # Proximity warning check from canonical hud_state
        if hud_state.chase_gap_warning:
            self.pursuit_panel.root["frameColor"] = CRITICAL_DREADNOUGHT_COLOR
            self.proximity_label["text_fg"] = COLORS.text_warning
            update_label_text(self.proximity_label, f"CRITICAL GAP\n{gap:.1f} m")
            if not getattr(getattr(self.app, "settings", None), "reduce_ui_motion", False):
                frame_time = getattr(getattr(self.app, "clock", None), "getFrameTime", lambda: 0.0)()
                self.dread_icon.setScale(1.0 + 0.10 * math.sin(frame_time * 10.0))
        else:
            self.pursuit_panel.root["frameColor"] = COLORS.panel_bg_dark
            self.proximity_label["text_fg"] = COLORS.text_primary
            update_label_text(self.proximity_label, f"DREADNOUGHT GAP\n{gap:.1f} m")
            self.dread_icon.setScale(1.0)

        if state_mgr.active_bark:
            update_label_text(self.bark_label, state_mgr.active_bark)
            self.bark_label.show()
            self.bark_label.setColorScale(1.0, 1.0, 1.0, min(1.0, max(0.0, state_mgr.bark_timer)))
        else:
            self.bark_label.hide()
        if hasattr(self, "notifications") and self.notifications:
            self.notifications.update(dt)

    def destroy(self) -> None:
        """Clean up HUD widgets and notification resources."""
        if hasattr(self, "notifications") and self.notifications:
            self.notifications.clear()
            self.notifications = None
        for attr in (
            "console_panel",
            "console_toggle_btn",
            "console_title",
            "console_divider",
            "hull_label",
            "hull_bar_bg",
            "hull_bar",
            "score_label",
            "multiplier_label",
            "missile_label",
            "missile_bar_bg",
            "missile_bar",
            "bomb_label",
            "bomb_bar_bg",
            "bomb_bar",
            "magnet_pill",
            "intern_pill",
            "pause_btn_comp",
            "wave_panel",
            "wave_pill",
            "boss_meter",
            "pursuit_panel",
            "pursuit_toggle_btn",
            "pursuit_track",
            "player_icon",
            "escape_label",
            "dread_icon",
            "proximity_label",
            "distance_bar_bg",
            "distance_bar",
            "distance_remaining_label",
            "controls_callout",
            "controls_panel",
            "controls_title",
            "controls_text",
            "controls_btn_comp",
            "controls_close_comp",
            "bark_label",
        ):
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).destroy()
                except Exception:
                    pass


LegacyGameHUD = GameHUD
