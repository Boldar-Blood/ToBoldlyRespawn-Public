"""Canonical menu, manual, settings, pause, and result overlays.

This module owns the Panda3D/DirectGUI runtime implementation for non-gameplay
screens. Reusable geometry still lives in ``space_demo.ui.layout`` so layout
policy stays testable and reusable, while this controller owns Panda3D widgets,
textures, screen state, and settings persistence.
"""

from __future__ import annotations

import os
from typing import Any

from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectSlider
import direct.gui.DirectGuiGlobals as DGG
from panda3d.core import Filename, TextNode, TexturePool, TransparencyAttrib

from space_demo.core.ids import GameStateID
from space_demo.core.settings_store import GameSettings, save_settings
from space_demo.ui.components import GameButton, GamePanel, ScreenDimmer, wrap_text_lines
from space_demo.ui.display_capabilities import detect_supported_resolutions
from space_demo.ui.layout.bridge_calibration import build_bridge_calibration_layout
from space_demo.ui.layout.main_menu import build_main_menu_layout, compute_cover_size
from space_demo.ui.layout.tactical_manual import build_tactical_manual_layout
from space_demo.ui.theme import COLORS, FONTS, effective_text_scale, normalize_resolution


UI_SCALE_VALUES = [0.85, 1.0, 1.15, 1.30, 1.50]
TEXT_SCALE_VALUES = [0.85, 1.0, 1.15, 1.30, 1.50]
DIFFICULTIES = ["easy", "medium", "hard"]
HUD_DENSITIES = ("full", "compact", "minimal")
HUD_DENSITY_LABELS = {
    "full": "FULL",
    "compact": "COMPACT",
    "minimal": "MINIMAL",
}
COMMON_RESOLUTIONS = (
    (960, 540),
    (1024, 576),
    (1280, 720),
    (1366, 768),
    (1600, 900),
    (1920, 1080),
    (2560, 1440),
    (3840, 2160),
)

MENU_BACKGROUND_SOURCE_SIZE = (1920.0, 1080.0)
MENU_BACKGROUND_BASE_QUAD_SIZE = (60.0, 60.0)


class GameMenuScreens:
    """Manage all non-gameplay screens using Panda3D DirectGUI widgets."""

    def __init__(self, app: Any = None, font: Any = None, profile_store: Any = None, ship_adapter: Any = None) -> None:
        self.app = app
        self.font = font
        self.profile_store = profile_store or getattr(app, "profile_store", None)
        self.ship_adapter = ship_adapter or getattr(app, "ship_adapter", None)
        self.menu_sub_state = "main"
        self.active_settings_tab = "display"
        self.active_tut_tab = "actors"
        settings = getattr(app, "settings", None)
        self.ui_scale = getattr(settings, "ui_scale", 1.0)
        self.text_scale = getattr(settings, "text_scale", 1.0)
        self._load_gui_textures()
        self._init_pending_from_app()
        self._build_menu()
        self._build_tutorial()
        self._build_settings()
        self._build_results()
        self._build_pause()
        self._build_fleet()
        self._apply_curated_panel_skins()
        self.hide_all()

    def _load_gui_textures(self) -> None:
        """Load generated GUI textures and curated panel fallbacks."""
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))

        def load(name: str):
            try:
                path = Filename.fromOsSpecific(os.path.join(data_dir, name)).getFullpath()
                return TexturePool.loadTexture(path)
            except Exception:
                return None


        # Curated panel textures are the preferred menu/manual/settings frame art.
        # Load them locally too, so headless UI tests and fallback-only runs do
        # not depend on AssetManager.load_assets().
        self.ui_panel_glass_tex = load(os.path.join("sprites", "ui", "panel_glass.png"))
        self.ui_panel_card_tex = load(os.path.join("sprites", "ui", "panel_card.png"))


    def _root_frame(self, name: str) -> DirectFrame:
        """Create a transparent root frame for one full-screen overlay."""
        frame = DirectFrame(frameSize=(-1.15, 1.15, -0.80, 0.80), pos=(0, 0, 0), relief=None)
        frame.setName(name)
        frame.setTransparency(TransparencyAttrib.MAlpha)
        return frame

    def _effective_text_scale(self) -> float:
        """Return resolution-aware screen text scaling."""
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
        """Create a DirectLabel using readable text scale and shadow styling."""
        label = DirectLabel(
            parent=parent,
            text=text,
            pos=pos,
            scale=scale * self._effective_text_scale(),
            text_font=self.font,
            text_fg=color,
            text_shadow=(0, 0, 0, 0.85),
            text_align=align,
            relief=None,
        )
        label.setTransparency(TransparencyAttrib.MAlpha)
        return label

    def _row_label(self, parent, text: str, pos) -> DirectLabel:
        """Create a left-aligned settings-row label."""
        return self._label(parent, text, pos, 0.021, COLORS.text_secondary, TextNode.ALeft)

    def _button(
        self,
        parent,
        text: str,
        command,
        pos,
        variant: str = "primary",
        size: str = "medium",
        width: float | None = None,
        height: float | None = None,
    ):
        """Create a reusable themed button and return its DirectButton node."""
        return GameButton(
            parent=parent,
            text=text,
            command=command,
            pos=pos,
            variant=variant,
            size=size,
            width=width,
            height=height,
            font=self.font,
            ui_scale=self.ui_scale,
            text_scale=self._effective_text_scale(),
        ).node

    def _toggle_button(self, parent, text: str, command, pos, active: bool, width: float = 0.40):
        """Create a success/danger toggle button."""
        return self._button(parent, text, command, pos, "success" if active else "danger", "small", width=width, height=0.058)

    def _set_button_visual(self, button, text: str, active: bool) -> None:
        """Update a toggle-like button without recreating its DirectGUI node."""
        button["text"] = text
        button["frameColor"] = (0.06, 0.35, 0.16, 0.92) if active else (0.45, 0.08, 0.08, 0.92)
        button["text_scale"] = 0.0165 * self._effective_text_scale()
        button["text_pos"] = (0, -0.006)
        button["text_align"] = TextNode.ACenter

    def _asset(self, *names: str):
        """Return the first available texture from AssetManager or local UI fallbacks."""
        assets = getattr(self.app, "assets_mgr", None) or getattr(self.app, "assets", None)
        for source in (assets, self):
            if source is None:
                continue
            for name in names:
                tex = getattr(source, name, None)
                if tex is not None:
                    return tex
        return None

    def _hide_generated_panel_border(self, panel) -> None:
        """Hide generated border strips after curated frame art owns the chrome."""
        for border in getattr(panel, "border_nodes", []):
            try:
                border.hide()
            except Exception:
                pass

    def _destroy_existing_backing(self, panel) -> None:
        """Destroy an existing curated-panel readability backing node."""
        backing = getattr(panel, "curated_backing_node", None)
        if backing is not None:
            try:
                backing.destroy()
            except Exception:
                pass
        panel.curated_backing_node = None

    def _add_inner_backing(self, panel, width_scale: float, height_scale: float, alpha: float) -> None:
        """Place readable dark fill behind the curated frame, not over it."""
        self._destroy_existing_backing(panel)
        half_w = panel.width * width_scale / 2.0
        half_h = panel.height * height_scale / 2.0
        backing = DirectFrame(
            parent=panel.root,
            frameSize=(-half_w, half_w, -half_h, half_h),
            frameColor=(0.0, 0.0, 0.0, alpha),
            relief=DGG.FLAT,
            sortOrder=-30,
        )
        backing.setTransparency(TransparencyAttrib.MAlpha)
        panel.curated_backing_node = backing

    def _make_skinned_screen_panel(
        self,
        panel,
        texture,
        alpha: float,
        skin_scale: tuple[float, float] = (1.0, 1.0),
        backing_scale: tuple[float, float] = (0.78, 0.76),
        backing_alpha: float = 0.58,
    ) -> None:
        """Use curated frame art as screen chrome and keep fill inside the frame."""
        if panel is None or texture is None or not hasattr(panel, "set_skin"):
            return
        try:
            panel.root["frameColor"] = (0.0, 0.0, 0.0, 0.0)
        except Exception:
            pass
        self._add_inner_backing(panel, backing_scale[0], backing_scale[1], backing_alpha)
        panel.set_skin(texture, alpha)
        try:
            if getattr(panel, "skin_node", None) is not None:
                panel.skin_node["sortOrder"] = -20
                panel.skin_node["image_scale"] = (
                    panel.width * skin_scale[0] / 2.0,
                    1.0,
                    panel.height * skin_scale[1] / 2.0,
                )
                panel.skin_node.setColorScale(1.0, 1.0, 1.0, alpha)
        except Exception:
            pass
        self._hide_generated_panel_border(panel)

    def _flatten_content_panel(self, panel) -> None:
        """Remove nested colored boxes while preserving their child content."""
        if panel is None:
            return
        try:
            panel.root["frameColor"] = (0.0, 0.0, 0.0, 0.0)
        except Exception:
            pass
        self._destroy_existing_backing(panel)
        skin = getattr(panel, "skin_node", None)
        if skin is not None:
            try:
                skin.destroy()
            except Exception:
                pass
            panel.skin_node = None
        self._hide_generated_panel_border(panel)

    def _apply_curated_panel_skins(self) -> None:
        """Apply optional curated panel textures after screen construction."""
        glass = self._asset("ui_panel_glass_tex")
        card = self._asset("ui_panel_card_tex") or glass

        self._make_skinned_screen_panel(
            getattr(self, "menu_panel", None),
            glass,
            0.92,
            skin_scale=(1.16, 1.14),
            backing_scale=(1.03, 0.92),
            backing_alpha=0.66,
        )
        self._make_skinned_screen_panel(
            getattr(self, "tut_panel", None),
            glass,
            0.92,
            skin_scale=(1.36, 1.30),
            backing_scale=(1.16, 1.04),
            backing_alpha=0.68,
        )
        self._make_skinned_screen_panel(
            getattr(self, "set_panel", None),
            glass,
            0.92,
            skin_scale=(1.36, 1.26),
            backing_scale=(1.16, 1.02),
            backing_alpha=0.68,
        )
        self._make_skinned_screen_panel(
            getattr(self, "fleet_panel", None),
            glass,
            0.92,
            skin_scale=(1.36, 1.26),
            backing_scale=(1.16, 1.02),
            backing_alpha=0.68,
        )
        for attr_name in ("gameover_panel", "victory_panel", "paused_panel"):
            self._make_skinned_screen_panel(
                getattr(self, attr_name, None),
                glass,
                0.86,
                skin_scale=(1.18, 1.14),
                backing_scale=(1.00, 0.94),
                backing_alpha=0.66,
            )
        self._make_skinned_screen_panel(
            getattr(self, "confirm_panel", None),
            card,
            0.88,
            skin_scale=(1.12, 1.10),
            backing_scale=(0.90, 0.80),
            backing_alpha=0.70,
        )

        for attr_name in ("briefing_card", "card_obj", "card_ctrl", "card_upg", "fleet_list_panel", "fleet_detail_panel"):
            self._flatten_content_panel(getattr(self, attr_name, None))

    def _sprite(self, parent, texture, pos, scale) -> DirectFrame:
        """Create a transparent image frame for generated game/UI textures."""
        kwargs = {"parent": parent, "pos": pos, "relief": None}
        if texture is not None:
            kwargs["image"] = texture
            kwargs["image_scale"] = scale
        node = DirectFrame(**kwargs)
        node.setTransparency(TransparencyAttrib.MAlpha)
        return node

    def _slider(self, parent, pos, slider_range, value, command, width: float = 0.42) -> DirectSlider:
        """Create a styled DirectSlider with integer snapping for option lists."""
        is_discrete = slider_range[1] - slider_range[0] >= 2 and all(float(v).is_integer() for v in slider_range)
        slider = DirectSlider(
            parent=parent,
            pos=pos,
            range=slider_range,
            value=value,
            pageSize=1.0 if is_discrete else 0.05,
            frameSize=(-width / 2, width / 2, -0.010, 0.010),
            thumb_frameSize=(-0.020, 0.020, -0.038, 0.038),
            frameColor=(0.20, 0.24, 0.34, 0.88),
            thumb_frameColor=(0.22, 0.58, 0.95, 0.96),
            command=command,
        )
        slider.setTransparency(TransparencyAttrib.MAlpha)
        if is_discrete:
            def snap_on_release(event=None, s=slider, cb=command, lo=int(slider_range[0]), hi=int(slider_range[1])):
                raw = s.getValue()
                val = max(lo, min(hi, int(round(raw))))
                if raw != val:
                    s["command"] = None
                    s.setValue(val)
                    s["command"] = cb
                cb()
            slider.bind(DGG.B1RELEASE, snap_on_release)
        return slider

    def _init_pending_from_app(self) -> None:
        """Load pending settings from the active app/settings model."""
        settings = getattr(self.app, "settings", GameSettings())
        state_mgr = getattr(self.app, "state_mgr", None)
        self.resolutions = self._detect_resolutions(settings.resolution)
        self.pending_difficulty = getattr(state_mgr, "difficulty", settings.difficulty)
        self.pending_coop_mode = getattr(state_mgr, "coop_mode", settings.coop_mode)
        self.pending_vfx_high = getattr(state_mgr, "vfx_high", settings.vfx_high)
        self.pending_fullscreen = settings.fullscreen
        self.pending_resolution_idx = self._resolution_index(settings.resolution)
        self.pending_ui_scale = settings.ui_scale
        self.pending_text_scale = settings.text_scale
        self.pending_high_contrast_text = settings.high_contrast_text
        self.pending_reduce_ui_motion = settings.reduce_ui_motion
        self.pending_master_volume = settings.master_volume
        self.pending_music_volume = settings.music_volume
        self.pending_sfx_volume = settings.sfx_volume
        self.pending_master_muted = settings.master_muted
        self.pending_music_muted = settings.music_muted
        self.pending_sfx_muted = settings.sfx_muted
        self.pending_show_intro = settings.show_intro
        density = getattr(settings, "hud_density", "compact")
        self.pending_hud_density = density if density in HUD_DENSITIES else "compact"
        profile = getattr(self.app, "profile", None)
        if profile:
            self.selected_preview_id = profile.selected_ship_id
        else:
            self.selected_preview_id = None

    @staticmethod
    def _nearest_resolution_index(resolutions: list[tuple[int, int]], target: tuple[int, int]) -> int:
        """Return a stable nearest index for stale or unsupported saved settings."""
        if target in resolutions:
            return resolutions.index(target)
        target_area = target[0] * target[1]
        target_aspect = target[0] / max(1, target[1])
        return min(
            range(len(resolutions)),
            key=lambda i: (
                abs((resolutions[i][0] * resolutions[i][1]) - target_area),
                abs((resolutions[i][0] / max(1, resolutions[i][1])) - target_aspect),
            ),
        )

    def _detect_resolutions(self, current_resolution) -> list[tuple[int, int]]:
        """Return resolution choices using the shared platform-aware display policy."""
        return detect_supported_resolutions(self.app, current_resolution, COMMON_RESOLUTIONS)

    def _resolution_index(self, resolution) -> int:
        """Return the nearest index of a resolution in the current choices."""
        target = normalize_resolution(resolution)
        return self._nearest_resolution_index(self.resolutions, target)

    def _build_menu(self) -> None:
        """Build the main menu using centralized layout data."""
        self.main_menu_layout = build_main_menu_layout(self.ui_scale)
        layout = self.main_menu_layout
        self.menu_frame = self._root_frame("menu_frame")
        self.menu_dimmer = ScreenDimmer(parent=self.menu_frame, alpha=0.30)
        self.menu_panel = GamePanel(
            self.menu_frame,
            "main_menu_panel",
            (0, 0, 0),
            layout.panel_size,
            COLORS.panel_bg_dark,
            COLORS.panel_stroke,
        )
        title_texture = self._asset("title_banner_tex")
        self.menu_title = self._sprite(self.menu_panel.root, title_texture, layout.title_pos, layout.title_scale)
        if title_texture is None:
            self.menu_title_text = self._label(
                self.menu_panel.root,
                "TO BOLDLY RESPAWN",
                layout.fallback_title_pos,
                0.055,
                COLORS.text_primary,
            )
            self.menu_subtitle = self._label(
                self.menu_panel.root,
                "A CO-OP SPACE DISASTER",
                layout.fallback_subtitle_pos,
                0.026,
                COLORS.text_warning,
            )
        else:
            self.menu_subtitle = self._label(self.menu_panel.root, "", layout.fallback_subtitle_pos, FONTS.small_scale, COLORS.text_warning)
            self.menu_subtitle.hide()

        nav_x = layout.nav_x
        nav_step = -0.110 * self.ui_scale
        start_z = 0.080 * self.ui_scale
        nav_z = [start_z + i * nav_step for i in range(5)]

        self.btn_start = self._button(
            self.menu_panel.root,
            "START CO-OP RETREAT",
            self.on_start_click,
            (nav_x, 0, nav_z[0]),
            "success",
            "medium",
            width=layout.button_width,
            height=layout.button_height,
        )
        self.btn_fleet = self._button(
            self.menu_panel.root,
            "FLEET OPERATIONS",
            self.on_fleet_click,
            (nav_x, 0, nav_z[1]),
            "primary",
            "medium",
            width=layout.button_width,
            height=layout.button_height,
        )
        self.btn_tutorial = self._button(
            self.menu_panel.root,
            "TACTICAL MANUAL",
            self.on_tutorial_click,
            (nav_x, 0, nav_z[2]),
            "primary",
            "medium",
            width=layout.button_width,
            height=layout.button_height,
        )
        self.btn_settings = self._button(
            self.menu_panel.root,
            "RETREAT CALIBRATION",
            self.on_settings_click,
            (nav_x, 0, nav_z[3]),
            "warning",
            "medium",
            width=layout.button_width,
            height=layout.button_height,
        )
        self.btn_quit = self._button(
            self.menu_panel.root,
            "DISMISS COMMAND",
            self.on_quit_click,
            (nav_x, 0, nav_z[4]),
            "danger",
            "medium",
            width=layout.button_width,
            height=layout.button_height,
        )
        self.briefing_card = GamePanel(
            self.menu_panel.root,
            "menu_briefing_card",
            layout.briefing_pos,
            layout.briefing_size,
            (0.003, 0.008, 0.02, 0.90),
            COLORS.purple,
        )
        log_text = (
            "STATUS: ACTIVE RETREAT\n"
            "HULL: BREACHED\n"
            "SHIELDS: OFFLINE\n"
            "ENGINES: HOT\n"
            "DREADNOUGHT: CLOSING\n\n"
            "Select a bridge system."
        )
        self.menu_log = self._label(
            self.briefing_card.root,
            wrap_text_lines(log_text, 30),
            layout.briefing_text_pos,
            layout.briefing_text_scale,
            COLORS.text_primary,
            TextNode.ALeft,
        )

    def _build_tutorial(self) -> None:
        """Build the tactical manual using centralized layout data."""
        self.tutorial_layout = build_tactical_manual_layout(self.ui_scale)
        layout = self.tutorial_layout
        self.tutorial_frame = self._root_frame("tutorial_frame")
        self.tut_dimmer = ScreenDimmer(parent=self.tutorial_frame, alpha=0.32)
        self.tut_panel = GamePanel(
            self.tutorial_frame,
            "tutorial_panel",
            (0, 0, 0),
            layout.panel_size,
            COLORS.panel_bg_dark,
            COLORS.panel_stroke,
        )
        self.tutorial_title = self._label(
            self.tut_panel.root,
            "COWARD'S STRATEGIC MANUAL",
            layout.title_pos,
            FONTS.heading_scale,
            COLORS.cyan,
        )
        self.tab_actors_btn = self._button(
            self.tut_panel.root,
            "ACTORS",
            lambda: self.set_tut_tab("actors"),
            (layout.tab_x[0], 0, layout.tab_z),
            "success",
            "small",
            width=layout.tab_width,
            height=layout.tab_height,
        )
        self.tab_systems_btn = self._button(
            self.tut_panel.root,
            "FLIGHT SYSTEMS",
            lambda: self.set_tut_tab("systems"),
            (layout.tab_x[1], 0, layout.tab_z),
            "primary",
            "small",
            width=layout.tab_width,
            height=layout.tab_height,
        )
        self.tab_upgrades_btn = self._button(
            self.tut_panel.root,
            "UPGRADES",
            lambda: self.set_tut_tab("upgrades"),
            (layout.tab_x[2], 0, layout.tab_z),
            "primary",
            "small",
            width=layout.tab_width,
            height=layout.tab_height,
        )
        self.card_obj = GamePanel(self.tut_panel.root, "card_objective", layout.card_pos, layout.card_size, (0.003, 0.008, 0.02, 0.92), COLORS.amber)
        self.card_ctrl = GamePanel(self.tut_panel.root, "card_controls", layout.card_pos, layout.card_size, (0.003, 0.008, 0.02, 0.92), COLORS.cyan)
        self.card_upg = GamePanel(self.tut_panel.root, "card_upgrades", layout.card_pos, layout.card_size, (0.003, 0.008, 0.02, 0.92), COLORS.green)
        self._populate_actor_card()
        self._populate_system_card()
        self._populate_upgrade_card()
        self.btn_tut_back = self._button(
            self.tut_panel.root,
            "RETURN TO BRIDGE",
            self.on_back_click,
            layout.return_pos,
            "warning",
            "medium",
            width=layout.return_width,
            height=layout.return_height,
        )
        self.set_tut_tab("actors")

    def _populate_actor_card(self) -> None:
        """Populate the actor/threat directory using the manual layout helper."""
        layout = self.tutorial_layout
        self._label(self.card_obj.root, "ACTOR / THREAT DIRECTORY", layout.card_title_pos, 0.025, COLORS.text_warning)
        entries = [
            (layout.left_entries[0], self._asset("player_hull_100_tex", "player_tex"), "PLAYER STARSHIP", "Rear-firing escape craft."),
            (layout.left_entries[1], self._asset("enemy_drone_tex", "drone_tex"), "CHASER DRONE", "Basic pursuer; destroy for score."),
            (layout.left_entries[2], self._asset("enemy_speeder_tex", "enemy_drone_tex"), "SPEEDER", "Fast lane pressure interceptor."),
            (layout.left_entries[3], self._asset("enemy_zigzag_tex", "enemy_drone_tex"), "ZIGZAG CUTTER", "Weaves through escape lanes."),
            (layout.right_entries[0], self._asset("enemy_mine_tex", "enemy_drone_tex"), "EXPENSE MINE", "Pulsing contact hazard."),
            (layout.right_entries[1], self._asset("enemy_frigate_tex", "enemy_drone_tex"), "POLICY FRIGATE", "Telegraphs lane lasers."),
            (layout.right_entries[2], self._asset("enemy_missile_boat_tex", "enemy_drone_tex"), "MISSILE BOAT", "Launches homing deadlines."),
            (layout.right_entries[3], self._asset("boss_phase_1_tex", "boss_tex"), "AUDIT DREADNOUGHT", "Boss fleet closing the gap."),
        ]
        for entry, tex, title, desc in entries:
            self._sprite(self.card_obj.root, tex, entry.icon_pos, layout.entry_icon_scale)
            self._label(self.card_obj.root, f"{title}\n{desc}", entry.text_pos, 0.0175, COLORS.text_primary, TextNode.ALeft)

    def _populate_system_card(self) -> None:
        """Populate flight-system manual content."""
        layout = self.tutorial_layout
        self._label(self.card_ctrl.root, "FLIGHT SYSTEMS", layout.card_title_pos, 0.025, COLORS.cyan)
        text = (
            "STEER: WASD / ARROWS\n"
            "FIRE: SPACE rear laser, C missile, B decision bomb\n\n"
            "TACTIC: keep the dreadnought gap above capture distance while clearing the bottom enemy-entry lane.\n\n"
            "CO-OP MODE: one player can steer while the other handles weapons."
        )
        self._label(self.card_ctrl.root, wrap_text_lines(text, 58), layout.body_text_pos, 0.022, COLORS.text_primary, TextNode.ALeft)

    def _populate_upgrade_card(self) -> None:
        """Populate the Tactical Manual upgrades tab with icon entries."""
        layout = self.tutorial_layout
        self._label(self.card_upg.root, "FIELD UPGRADES", layout.card_title_pos, 0.025, COLORS.green)

        entries = [
            (layout.left_entries[0], self._asset("pickup_health_tex"), "DUCT TAPE", "Repair damaged hull."),
            (layout.left_entries[1], self._asset("pickup_speed_tex"), "COOLING OVERCLOCK", "Fire rear lasers faster."),
            (layout.left_entries[2], self._asset("pickup_shield_tex"), "LIABILITY WAIVER", "Temporary shield bubble."),
            (layout.left_entries[3], self._asset("pickup_magnet_tex"), "SYNERGY MAGNET", "Pull nearby rewards inward."),
            (layout.right_entries[0], self._asset("pickup_intern_tex"), "UNPAID INTERN", "Temporary support fire."),
            (layout.right_entries[1], self._asset("pickup_missile_tex"), "MISSILE CACHE", "+2 anti-matter missiles."),
            (layout.right_entries[2], self._asset("pickup_bomb_tex"), "EXECUTIVE DECISION", "Smart bomb and pushback."),
            (layout.right_entries[3], self._asset("shield_skin_tex", "pickup_shield_tex"), "STACKING BUFFS", "Combine shields and magnets."),
        ]

        for entry, tex, title, desc in entries:
            self._sprite(self.card_upg.root, tex, entry.icon_pos, layout.entry_icon_scale)
            self._label(
                self.card_upg.root,
                f"{title}\n{desc}",
                entry.text_pos,
                0.0175,
                COLORS.text_primary,
                TextNode.ALeft,
            )

    def _build_settings(self) -> None:
        """Build Bridge Calibration using centralized settings layout data."""
        self.settings_layout = build_bridge_calibration_layout(self.ui_scale)
        layout = self.settings_layout
        self.settings_frame = self._root_frame("settings_frame")
        self.set_dimmer = ScreenDimmer(parent=self.settings_frame, alpha=0.32)
        self.set_panel = GamePanel(
            self.settings_frame,
            "settings_panel",
            (0, 0, 0),
            (1.88, 1.48),
            COLORS.panel_bg_dark,
            COLORS.panel_stroke,
        )
        self.settings_title = self._label(self.set_panel.root, "BRIDGE CALIBRATION", layout.title_pos, FONTS.heading_scale, COLORS.text_warning)
        self.btn_tab_display = self._button(
            self.set_panel.root,
            "DISPLAY",
            lambda: self.show_settings_tab("display"),
            (layout.tab_x[0], 0, layout.tab_z),
            "primary",
            "small",
            width=layout.tab_width,
            height=layout.tab_height,
        )
        self.btn_tab_audio = self._button(
            self.set_panel.root,
            "AUDIO",
            lambda: self.show_settings_tab("audio"),
            (layout.tab_x[1], 0, layout.tab_z),
            "primary",
            "small",
            width=layout.tab_width,
            height=layout.tab_height,
        )
        self.btn_tab_gameplay = self._button(
            self.set_panel.root,
            "TACTICAL",
            lambda: self.show_settings_tab("gameplay"),
            (layout.tab_x[2], 0, layout.tab_z),
            "primary",
            "small",
            width=layout.tab_width,
            height=layout.tab_height,
        )
        self.display_tab_frame = DirectFrame(parent=self.set_panel.root, frameSize=layout.tab_frame_size, pos=layout.tab_frame_pos, relief=None)
        self.audio_tab_frame = DirectFrame(parent=self.set_panel.root, frameSize=layout.tab_frame_size, pos=layout.tab_frame_pos, relief=None)
        self.gameplay_tab_frame = DirectFrame(parent=self.set_panel.root, frameSize=layout.tab_frame_size, pos=layout.tab_frame_pos, relief=None)
        self._build_display_settings()
        self._build_audio_settings()
        self._build_gameplay_settings()
        self.btn_apply = self._button(
            self.set_panel.root,
            "APPLY CALIBRATION",
            self.on_apply_changes,
            (layout.footer_x[0], 0, layout.footer_z),
            "success",
            "medium",
            width=layout.footer_width,
            height=layout.footer_height,
        )
        self.btn_reset = self._button(
            self.set_panel.root,
            "RESET TO DEFAULTS",
            self.on_reset_defaults,
            (layout.footer_x[1], 0, layout.footer_z),
            "danger",
            "medium",
            width=layout.footer_width,
            height=layout.footer_height,
        )
        self.btn_set_back = self._button(
            self.set_panel.root,
            "RETURN TO BRIDGE",
            self.on_back_click,
            (layout.footer_x[2], 0, layout.footer_z),
            "warning",
            "medium",
            width=layout.footer_width,
            height=layout.footer_height,
        )
        self.settings_note = self._label(
            self.set_panel.root,
            "Settings persist after Apply. UI/text changes rebuild the interface.",
            layout.note_pos,
            0.017,
            COLORS.text_secondary,
        )
        self._build_confirm_modal()
        self.show_settings_tab("display")
        self.refresh_settings_controls_visuals()

    def _build_display_settings(self) -> None:
        """Build display settings without applying UI scale twice."""
        rows = self.settings_layout.display_rows
        self.res_label = self._row_label(self.display_tab_frame, "RESOLUTION", rows[0].label_pos)
        self.res_slider = self._slider(
            self.display_tab_frame,
            rows[0].control_pos,
            (0, max(0, len(self.resolutions) - 1)),
            self.pending_resolution_idx,
            self.on_res_slider_change,
            width=rows[0].slider_width,
        )
        self.btn_full_label = self._row_label(self.display_tab_frame, "FULLSCREEN", rows[1].label_pos)
        self.btn_full = self._toggle_button(
            self.display_tab_frame,
            "FULLSCREEN: OFF",
            self.on_fullscreen_toggle,
            rows[1].control_pos,
            False,
            width=rows[1].toggle_width,
        )
        self.btn_vfx_label = self._row_label(self.display_tab_frame, "VFX QUALITY", rows[2].label_pos)
        self.btn_vfx = self._toggle_button(
            self.display_tab_frame,
            "VFX QUALITY: ACTIVE",
            self.on_vfx_toggle,
            rows[2].control_pos,
            True,
            width=rows[2].toggle_width,
        )
        self.ui_scale_label = self._row_label(self.display_tab_frame, "UI SCALE", rows[3].label_pos)
        self.ui_scale_slider = self._slider(
            self.display_tab_frame,
            rows[3].control_pos,
            (0, 4),
            1,
            self.on_ui_scale_slider_change,
            width=rows[3].slider_width,
        )
        self.text_scale_label = self._row_label(self.display_tab_frame, "TEXT SIZE", rows[4].label_pos)
        self.text_scale_slider = self._slider(
            self.display_tab_frame,
            rows[4].control_pos,
            (0, 4),
            1,
            self.on_text_scale_slider_change,
            width=rows[4].slider_width,
        )
        paired_z = self.settings_layout.paired_toggle_z
        paired_width = self.settings_layout.paired_toggle_width
        self.btn_high_contrast = self._toggle_button(
            self.display_tab_frame,
            "HIGH CONTRAST: OFF",
            self.on_high_contrast_toggle,
            (self.settings_layout.paired_toggle_x[0], 0, paired_z),
            False,
            width=paired_width,
        )
        self.btn_reduce_motion = self._toggle_button(
            self.display_tab_frame,
            "REDUCE MOTION: OFF",
            self.on_reduce_motion_toggle,
            (self.settings_layout.paired_toggle_x[1], 0, paired_z),
            False,
            width=paired_width,
        )

    def _build_audio_settings(self) -> None:
        """Build audio settings controls."""
        rows = self.settings_layout.audio_rows
        self.master_vol_label = self._row_label(self.audio_tab_frame, "MASTER VOLUME", rows[0].label_pos)
        self.master_vol_slider = self._slider(
            self.audio_tab_frame,
            rows[0].control_pos,
            (0, 1),
            0.85,
            self.on_master_vol_change,
            width=rows[0].slider_width,
        )
        self.btn_master_mute = self._toggle_button(
            self.audio_tab_frame,
            "MUTE MASTER: OFF",
            self.on_master_mute_toggle,
            (0.55, 0, rows[0].control_pos[2]),
            True,
            width=rows[0].toggle_width,
        )
        self.music_vol_label = self._row_label(self.audio_tab_frame, "MUSIC VOLUME", rows[1].label_pos)
        self.music_vol_slider = self._slider(
            self.audio_tab_frame,
            rows[1].control_pos,
            (0, 1),
            0.65,
            self.on_music_vol_change,
            width=rows[1].slider_width,
        )
        self.btn_music_mute = self._toggle_button(
            self.audio_tab_frame,
            "MUTE MUSIC: OFF",
            self.on_music_mute_toggle,
            (0.55, 0, rows[1].control_pos[2]),
            True,
            width=rows[1].toggle_width,
        )
        self.sfx_vol_label = self._row_label(self.audio_tab_frame, "SFX VOLUME", rows[2].label_pos)
        self.sfx_vol_slider = self._slider(
            self.audio_tab_frame,
            rows[2].control_pos,
            (0, 1),
            0.85,
            self.on_sfx_vol_change,
            width=rows[2].slider_width,
        )
        self.btn_sfx_mute = self._toggle_button(
            self.audio_tab_frame,
            "MUTE SFX: OFF",
            self.on_sfx_mute_toggle,
            (0.55, 0, rows[2].control_pos[2]),
            True,
            width=rows[2].toggle_width,
        )
        self.btn_test_sfx = self._button(
            self.audio_tab_frame,
            "TEST SYSTEM SFX",
            self.on_test_sfx_click,
            (0, 0, -0.32),
            "primary",
            "medium",
            width=0.44,
        )

    def _build_gameplay_settings(self) -> None:
        """Build tactical settings including persistent HUD density."""
        rows = self.settings_layout.gameplay_rows
        self.difficulty_label = self._row_label(self.gameplay_tab_frame, "DIFFICULTY", rows[0].label_pos)
        self.difficulty_slider = self._slider(
            self.gameplay_tab_frame,
            rows[0].control_pos,
            (0, 2),
            1,
            self.on_difficulty_change,
            width=rows[0].slider_width,
        )
        self.btn_hud_density_label = self._row_label(self.gameplay_tab_frame, "HUD DENSITY", rows[1].label_pos)
        self.hud_density_slider = self._slider(
            self.gameplay_tab_frame,
            rows[1].control_pos,
            (0, 2),
            1,
            self.on_hud_density_change,
            width=rows[1].slider_width,
        )
        self.btn_coop_label = self._row_label(self.gameplay_tab_frame, "CO-OP STEERING", rows[2].label_pos)
        self.btn_coop = self._toggle_button(
            self.gameplay_tab_frame,
            "CO-OP: OFF",
            self.on_coop_toggle,
            rows[2].control_pos,
            False,
            width=rows[2].toggle_width,
        )
        self.btn_show_intro_label = self._row_label(self.gameplay_tab_frame, "TACTICAL INTRO", rows[3].label_pos)
        self.btn_show_intro = self._toggle_button(
            self.gameplay_tab_frame,
            "INTRO: SHOW",
            self.on_show_intro_toggle,
            rows[3].control_pos,
            True,
            width=rows[3].toggle_width,
        )

    def _build_confirm_modal(self) -> None:
        """Build the apply/discard confirmation modal."""
        self.confirm_modal = DirectFrame(
            parent=self.settings_frame,
            frameSize=(-2, 2, -1.2, 1.2),
            frameColor=(0, 0, 0, 0.45),
            relief=DGG.FLAT,
            sortOrder=100,
        )
        self.confirm_modal.setTransparency(TransparencyAttrib.MAlpha)
        self.confirm_panel = GamePanel(self.confirm_modal, "confirm_settings_panel", (0, 0, 0), (1.25, 0.62), COLORS.panel_bg_dark, COLORS.amber)
        self.confirm_title = self._label(self.confirm_panel.root, "UNAPPLIED CALIBRATION", (0, 0, 0.20), 0.034, COLORS.text_warning)
        self.confirm_body = self._label(self.confirm_panel.root, "Apply changes, discard them, or continue editing?", (0, 0, 0.05), 0.024, COLORS.text_primary)
        self.btn_confirm_apply = self._button(self.confirm_panel.root, "APPLY", self.on_confirm_apply, (-0.36, 0, -0.20), "success", "small", width=0.30)
        self.btn_confirm_discard = self._button(self.confirm_panel.root, "DISCARD", self.on_confirm_discard, (0, 0, -0.20), "danger", "small", width=0.30)
        self.btn_confirm_cancel = self._button(self.confirm_panel.root, "CANCEL", self.on_confirm_cancel, (0.36, 0, -0.20), "primary", "small", width=0.30)
        self.confirm_modal.hide()

    def _build_results(self) -> None:
        """Build game-over and victory overlays."""
        self.gameover_frame = self._root_frame("gameover_frame")
        self.victory_frame = self._root_frame("victory_frame")
        self.gameover_panel = GamePanel(self.gameover_frame, "gameover_panel", (0, 0, 0), (1.50, 0.80), (0.08, 0.02, 0.02, 0.86), COLORS.red)
        self.victory_panel = GamePanel(self.victory_frame, "victory_panel", (0, 0, 0), (1.50, 0.80), (0.02, 0.08, 0.04, 0.86), COLORS.green)
        self.gameover_title = self._label(self.gameover_panel.root, "TACTICAL FAILURE", (0, 0, 0.20), 0.060, COLORS.red)
        self.gameover_slogan = self._label(
            self.gameover_panel.root,
            "You have boldly respawned. Command is deducting the ship from your paycheck.",
            (0, 0, 0.03),
            0.026,
            COLORS.text_primary,
        )
        self.btn_gameover_restart = self._button(self.gameover_panel.root, "ENGAGE AGAIN", self.on_restart_click, (-0.30, 0, -0.22), "success", "small", width=0.36)
        self.btn_gameover_menu = self._button(self.gameover_panel.root, "BRIDGE", self.on_menu_click, (0.30, 0, -0.22), "warning", "small", width=0.36)
        self.victory_title = self._label(self.victory_panel.root, "DISASTER MANAGED", (0, 0, 0.20), 0.060, COLORS.green)
        self.victory_slogan = self._label(
            self.victory_panel.root,
            "The dreadnought has retreated. The disaster is now slightly further behind us.",
            (0, 0, 0.03),
            0.026,
            COLORS.text_primary,
        )
        self.btn_victory_restart = self._button(self.victory_panel.root, "FLEE AGAIN", self.on_restart_click, (-0.30, 0, -0.22), "success", "small", width=0.36)
        self.btn_victory_menu = self._button(self.victory_panel.root, "BRIDGE", self.on_menu_click, (0.30, 0, -0.22), "warning", "small", width=0.36)

    def _build_pause(self) -> None:
        """Build pause overlay."""
        self.paused_frame = self._root_frame("paused_frame")
        self.paused_panel = GamePanel(self.paused_frame, "paused_panel", (0, 0, 0), (1.20, 0.62), COLORS.panel_bg_dark, COLORS.cyan)
        self.paused_title = self._label(self.paused_panel.root, "GAME PAUSED", (0, 0, 0.15), 0.060, COLORS.cyan)
        self.paused_slogan = self._label(
            self.paused_panel.root,
            "Administrative hold active.\nPress P to resume, R to restart, or ESC for bridge.",
            (0, 0, -0.05),
            0.030,
            COLORS.text_primary,
        )

    def _build_fleet(self) -> None:
        """Build the Fleet/Ship Selection screen."""
        self.fleet_frame = self._root_frame("fleet_frame")
        self.fleet_dimmer = ScreenDimmer(parent=self.fleet_frame, alpha=0.32)
        
        self.fleet_panel = GamePanel(
            self.fleet_frame,
            "fleet_panel",
            (0, 0, 0),
            (1.88, 1.48),
            COLORS.panel_bg_dark,
            COLORS.panel_stroke,
        )
        
        # Title
        self.fleet_title = self._label(
            self.fleet_panel.root,
            "FLEET OPERATIONS",
            (0, 0, 0.62),
            FONTS.heading_scale,
            COLORS.cyan,
        )
        
        # Left side panel: Ship List
        self.fleet_list_panel = GamePanel(
            self.fleet_panel.root,
            "fleet_list_panel",
            (-0.46, 0, -0.05),
            (0.80, 1.05),
            (0.003, 0.008, 0.02, 0.90),
            COLORS.panel_stroke,
        )
        self._label(self.fleet_list_panel.root, "AVAILABLE VESSELS", (0, 0, 0.46), 0.022, COLORS.text_warning)
        
        # Right side panel: Selected Ship Details
        self.fleet_detail_panel = GamePanel(
            self.fleet_panel.root,
            "fleet_detail_panel",
            (0.46, 0, -0.05),
            (0.80, 1.05),
            (0.003, 0.008, 0.02, 0.90),
            COLORS.panel_stroke,
        )
        self._label(self.fleet_detail_panel.root, "VESSEL DATA SHEET", (0, 0, 0.46), 0.022, COLORS.text_warning)
        
        self.fleet_list_buttons = []
        self.fleet_detail_labels = {}
        self.btn_select_ship = None
        self.selected_preview_id = None
        
        # Back button at the bottom
        self.btn_fleet_back = self._button(
            self.fleet_panel.root,
            "RETURN TO BRIDGE",
            self.on_back_click,
            (0, 0, -0.62),
            "warning",
            "medium",
            width=0.46,
            height=0.076,
        )

    def on_fleet_click(self) -> None:
        """Open the Fleet/Ship Selection screen."""
        self.menu_sub_state = "fleet"
        self.refresh_fleet_ui()
        if self.app:
            self.update_screen_state(self.app.state_mgr.current_state)

    def on_preview_ship(self, ship_id: str) -> None:
        """Update the previewed ship and refresh UI."""
        self.selected_preview_id = ship_id
        self.refresh_fleet_ui()

    def select_ship(self, ship_id: str) -> None:
        """Update selected ship in profile, save it, and refresh runtime settings."""
        if not self.app or not getattr(self.app, "profile", None) or not self.profile_store:
            return
            
        profile = self.app.profile
        if ship_id not in profile.unlocked_ships:
            return
            
        from dataclasses import replace
        new_profile = replace(profile, selected_ship_id=ship_id)
        
        try:
            new_profile.validate(strict=True)
            if self.ship_adapter:
                self.ship_adapter.resolve_selected_ship(new_profile)
                
            self.profile_store.save_profile(new_profile)
            self.app.profile = new_profile
            
            if self.ship_adapter:
                self.app.current_ship_def = self.ship_adapter.resolve_selected_ship(new_profile)
                if getattr(self.app, "state_mgr", None):
                    self.app.state_mgr.reset(ship_def=self.app.current_ship_def)
                if getattr(self.app, "player", None):
                    self.app.player.reset(ship_def=self.app.current_ship_def)
            
            self.refresh_fleet_ui()
        except Exception as e:
            print(f"Error selecting ship: {e}")

    def refresh_fleet_ui(self) -> None:
        """Refresh Available Vessels and Vessel Data Sheet panels."""
        # Clean out existing elements
        for btn in self.fleet_list_buttons:
            try:
                btn.destroy()
            except Exception:
                pass
        self.fleet_list_buttons.clear()
        
        for key, lbl in list(self.fleet_detail_labels.items()):
            try:
                lbl.destroy()
            except Exception:
                pass
        self.fleet_detail_labels.clear()
        
        if self.btn_select_ship:
            try:
                self.btn_select_ship.destroy()
            except Exception:
                pass
            self.btn_select_ship = None
            
        profile = getattr(self.app, "profile", None)
        has_error = not profile or not self.profile_store or not self.ship_adapter
        
        if has_error:
            # Show error labels on both panels
            self.fleet_detail_labels["error_list"] = self._label(
                self.fleet_list_panel.root,
                "ERROR: SHIP ARCHIVE\nUNAVAILABLE",
                (0, 0, 0),
                0.018,
                COLORS.red
            )
            error_msg = getattr(self.app, "profile_error", "Profile or ship definitions not loaded.")
            self.fleet_detail_labels["error_detail"] = self._label(
                self.fleet_detail_panel.root,
                f"VESSEL DATA SHEET OFFLINE\n\n{error_msg}",
                (0, 0, 0),
                0.018,
                COLORS.red
            )
            return
            
        try:
            ship_defs = self.ship_adapter.load_ships_defs()
        except Exception as e:
            self.fleet_detail_labels["error_detail"] = self._label(
                self.fleet_detail_panel.root,
                f"Error loading ships:\n{e}",
                (0, 0, 0),
                0.018,
                COLORS.red
            )
            return
            
        if self.selected_preview_id not in ship_defs:
            self.selected_preview_id = profile.selected_ship_id
            
        if self.selected_preview_id not in ship_defs and ship_defs:
            self.selected_preview_id = list(ship_defs.keys())[0]
            
        # 1. Available Vessels list
        start_y = 0.35
        y_step = -0.10
        for idx, ship_id in enumerate(ship_defs.keys()):
            ship_def = ship_defs[ship_id]
            is_unlocked = ship_id in profile.unlocked_ships
            is_selected = ship_id == profile.selected_ship_id
            
            status_str = ""
            if is_selected:
                status_str = " [ACTIVE]"
            elif not is_unlocked:
                status_str = " [LOCKED]"
            else:
                status_str = " [READY]"
                
            button_text = f"{ship_def.display_name}{status_str}"
            
            variant = "success" if is_selected else ("primary" if is_unlocked else "danger")
            if ship_id == self.selected_preview_id:
                button_text = f"> {button_text} <"
                
            pos = (0, 0, start_y + idx * y_step)
            
            def make_cb(sid=ship_id):
                return lambda: self.on_preview_ship(sid)
                
            btn = self._button(
                self.fleet_list_panel.root,
                button_text,
                make_cb(),
                pos,
                variant=variant,
                size="small",
                width=0.70,
                height=0.065
            )
            self.fleet_list_buttons.append(btn)
            
        # 2. Selected preview ship details
        if self.selected_preview_id in ship_defs:
            preview_def = ship_defs[self.selected_preview_id]
            is_unlocked = preview_def.id in profile.unlocked_ships
            is_selected = preview_def.id == profile.selected_ship_id
            
            self.fleet_detail_labels["name"] = self._label(
                self.fleet_detail_panel.root,
                preview_def.display_name.upper(),
                (0, 0, 0.38),
                0.026,
                COLORS.cyan
            )
            
            self.fleet_detail_labels["desc"] = self._label(
                self.fleet_detail_panel.root,
                wrap_text_lines(preview_def.description, 45),
                (0, 0, 0.28),
                0.017,
                COLORS.text_primary
            )
            
            stats_y = [0.16, 0.09, 0.02, -0.05, -0.12]
            stat_rows = [
                ("MAX HULL", f"{preview_def.stats.max_hull}"),
                ("MOVE SPEED", f"{preview_def.stats.move_speed:.1f}"),
                ("FIRE COOLDOWN", f"{preview_def.stats.fire_cooldown:.2f}s"),
                ("MISSILE CAPACITY", f"{preview_def.stats.missile_capacity}"),
                ("BOMB CAPACITY", f"{preview_def.stats.bomb_capacity}"),
            ]
            
            for i, (label_txt, val_txt) in enumerate(stat_rows):
                lbl_name = f"stat_lbl_{i}"
                self.fleet_detail_labels[lbl_name] = self._label(
                    self.fleet_detail_panel.root,
                    label_txt,
                    (-0.32, 0, stats_y[i]),
                    0.0175,
                    COLORS.text_secondary,
                    align=TextNode.ALeft
                )
                val_name = f"stat_val_{i}"
                self.fleet_detail_labels[val_name] = self._label(
                    self.fleet_detail_panel.root,
                    val_txt,
                    (0.32, 0, stats_y[i]),
                    0.0175,
                    COLORS.text_primary,
                    align=TextNode.ARight
                )
                
            slots_str = ", ".join(preview_def.equipment_slots) if preview_def.equipment_slots else "None"
            self.fleet_detail_labels["slots_lbl"] = self._label(
                self.fleet_detail_panel.root,
                "EQUIPMENT SLOTS",
                (-0.32, 0, -0.19),
                0.0175,
                COLORS.text_secondary,
                align=TextNode.ALeft
            )
            self.fleet_detail_labels["slots_val"] = self._label(
                self.fleet_detail_panel.root,
                slots_str,
                (0.32, 0, -0.19),
                0.0175,
                COLORS.text_primary,
                align=TextNode.ARight
            )
            
            abilities_str = ", ".join(preview_def.abilities) if preview_def.abilities else "None"
            self.fleet_detail_labels["abilities_lbl"] = self._label(
                self.fleet_detail_panel.root,
                "PASSIVES / ABILITIES",
                (-0.32, 0, -0.26),
                0.0175,
                COLORS.text_secondary,
                align=TextNode.ALeft
            )
            self.fleet_detail_labels["abilities_val"] = self._label(
                self.fleet_detail_panel.root,
                abilities_str,
                (0.32, 0, -0.26),
                0.0175,
                COLORS.text_primary,
                align=TextNode.ARight
            )
            
            if is_selected:
                action_text = "CURRENTLY SELECTED"
                variant = "success"
                enabled = False
            elif not is_unlocked:
                action_text = "LOCKED / UNAVAILABLE"
                variant = "danger"
                enabled = False
            else:
                action_text = "SELECT AS ACTIVE VESSEL"
                variant = "warning"
                enabled = True
                
            def make_select_cb(sid=preview_def.id):
                return lambda: self.select_ship(sid)
                
            self.btn_select_ship = self._button(
                self.fleet_detail_panel.root,
                action_text,
                make_select_cb() if enabled else None,
                (0, 0, -0.38),
                variant=variant,
                size="medium",
                width=0.64,
                height=0.070
            )
            if not enabled:
                self.btn_select_ship["state"] = DGG.DISABLED

    def set_tut_tab(self, tab_name: str) -> None:
        """Show one tactical-manual tab."""
        self.active_tut_tab = tab_name
        self.card_obj.hide()
        self.card_ctrl.hide()
        self.card_upg.hide()
        if tab_name == "systems":
            self.card_ctrl.show()
        elif tab_name == "upgrades":
            self.card_upg.show()
        else:
            self.card_obj.show()

    def show_settings_tab(self, tab_name: str) -> None:
        """Show one Bridge Calibration tab."""
        self.active_settings_tab = tab_name
        self.display_tab_frame.hide()
        self.audio_tab_frame.hide()
        self.gameplay_tab_frame.hide()
        if tab_name == "audio":
            self.audio_tab_frame.show()
        elif tab_name == "gameplay":
            self.gameplay_tab_frame.show()
        else:
            self.display_tab_frame.show()

    def hide_all(self) -> None:
        """Hide all non-gameplay screen roots."""
        for frame in (self.menu_frame, self.tutorial_frame, self.settings_frame, self.gameover_frame, self.victory_frame, self.paused_frame, getattr(self, "fleet_frame", None)):
            if frame:
                frame.hide()

    def _apply_menu_background_cover(self) -> None:
        """Scale menu background art with an aspect-preserving cover rule."""
        app = getattr(self, "app", None)
        if app is None or getattr(app, "headless", False):
            return
        bg_node = getattr(app, "menu_bg_np", None)
        if bg_node is None:
            return
        try:
            lens = app.cam.node().getLens()
            film_size = lens.getFilmSize()
            view_width = float(film_size[0])
            view_height = float(film_size[1])
            assets = getattr(app, "assets_mgr", None) or getattr(app, "assets", None)
            texture = getattr(assets, "menu_bg_tex", None)
            image_width = float(texture.getXSize()) if texture is not None and texture.getXSize() > 0 else MENU_BACKGROUND_SOURCE_SIZE[0]
            image_height = float(texture.getYSize()) if texture is not None and texture.getYSize() > 0 else MENU_BACKGROUND_SOURCE_SIZE[1]
            target_width, target_height = compute_cover_size(view_width, view_height, image_width, image_height)
            bg_node.setScale(
                target_width / MENU_BACKGROUND_BASE_QUAD_SIZE[0],
                1.0,
                target_height / MENU_BACKGROUND_BASE_QUAD_SIZE[1],
            )
        except Exception:
            pass

    def update_screen_state(self, current_state) -> None:
        """Show the correct overlay for the current game state."""
        self.hide_all()
        self._apply_menu_background_cover()

        if current_state == GameStateID.MENU:
            if self.menu_sub_state == "tutorial":
                self.tutorial_frame.show()
            elif self.menu_sub_state == "settings":
                self.settings_frame.show()
            elif self.menu_sub_state == "fleet":
                self.fleet_frame.show()
            else:
                self.menu_frame.show()
        elif current_state == GameStateID.PAUSED:
            self.paused_frame.show()
        elif current_state == GameStateID.GAMEOVER:
            self.gameover_frame.show()
        elif current_state == GameStateID.VICTORY:
            self.victory_frame.show()

        app = getattr(self, "app", None)
        if app is not None and hasattr(app, "active_3d_state_nodes"):
            try:
                for node in list(app.active_3d_state_nodes):
                    node.removeNode()
                app.active_3d_state_nodes.clear()
            except Exception:
                pass

    def _snap_slider(self, slider, callback, lo: int, hi: int) -> int:
        """Snap a DirectSlider to an integer option and return that option."""
        raw = slider.getValue()
        val = max(lo, min(hi, int(round(raw))))
        if raw != val:
            slider["command"] = None
            slider.setValue(val)
            slider["command"] = callback
        return val

    def refresh_settings_controls_visuals(self) -> None:
        """Refresh all settings controls from pending values."""
        self.res_slider["command"] = None
        self.res_slider.setValue(self.pending_resolution_idx)
        self.res_slider["command"] = self.on_res_slider_change
        width, height = self.resolutions[self.pending_resolution_idx]
        self.res_label["text"] = f"RESOLUTION: {width} x {height}"
        self.update_fullscreen_button_visual(self.pending_fullscreen)
        self.update_vfx_button_visual(self.pending_vfx_high)

        ui_idx = min(range(len(UI_SCALE_VALUES)), key=lambda i: abs(UI_SCALE_VALUES[i] - self.pending_ui_scale))
        self.ui_scale_slider["command"] = None
        self.ui_scale_slider.setValue(ui_idx)
        self.ui_scale_slider["command"] = self.on_ui_scale_slider_change
        self.ui_scale_label["text"] = f"UI SCALE: {int(self.pending_ui_scale * 100)}%"

        text_idx = min(range(len(TEXT_SCALE_VALUES)), key=lambda i: abs(TEXT_SCALE_VALUES[i] - self.pending_text_scale))
        self.text_scale_slider["command"] = None
        self.text_scale_slider.setValue(text_idx)
        self.text_scale_slider["command"] = self.on_text_scale_slider_change
        self.text_scale_label["text"] = f"TEXT SIZE: {int(self.pending_text_scale * 100)}%"

        self.update_high_contrast_visual(self.pending_high_contrast_text)
        self.update_reduce_motion_visual(self.pending_reduce_ui_motion)
        self.master_vol_slider.setValue(self.pending_master_volume)
        self.music_vol_slider.setValue(self.pending_music_volume)
        self.sfx_vol_slider.setValue(self.pending_sfx_volume)
        self.on_master_vol_change()
        self.on_music_vol_change()
        self.on_sfx_vol_change()
        self.update_mute_visual(self.btn_master_mute, self.pending_master_muted, "MASTER")
        self.update_mute_visual(self.btn_music_mute, self.pending_music_muted, "MUSIC")
        self.update_mute_visual(self.btn_sfx_mute, self.pending_sfx_muted, "SFX")

        diff_idx = DIFFICULTIES.index(self.pending_difficulty) if self.pending_difficulty in DIFFICULTIES else 1
        self.difficulty_slider["command"] = None
        self.difficulty_slider.setValue(diff_idx)
        self.difficulty_slider["command"] = self.on_difficulty_change
        self.difficulty_label["text"] = f"DIFFICULTY: {self.pending_difficulty.upper()}"

        density_idx = HUD_DENSITIES.index(self.pending_hud_density) if self.pending_hud_density in HUD_DENSITIES else 1
        self.hud_density_slider["command"] = None
        self.hud_density_slider.setValue(density_idx)
        self.hud_density_slider["command"] = self.on_hud_density_change
        self.btn_hud_density_label["text"] = f"HUD DENSITY: {HUD_DENSITY_LABELS[self.pending_hud_density]}"
        self.update_coop_visual(self.pending_coop_mode)
        self.update_show_intro_visual(self.pending_show_intro)

    def on_difficulty_change(self) -> None:
        """Handle difficulty slider changes."""
        idx = self._snap_slider(self.difficulty_slider, self.on_difficulty_change, 0, 2)
        self.pending_difficulty = DIFFICULTIES[idx]
        self.difficulty_label["text"] = f"DIFFICULTY: {self.pending_difficulty.upper()}"

    def on_hud_density_change(self) -> None:
        """Handle HUD-density slider changes."""
        idx = self._snap_slider(self.hud_density_slider, self.on_hud_density_change, 0, len(HUD_DENSITIES) - 1)
        self.pending_hud_density = HUD_DENSITIES[idx]
        self.btn_hud_density_label["text"] = f"HUD DENSITY: {HUD_DENSITY_LABELS[self.pending_hud_density]}"

    def on_res_slider_change(self) -> None:
        """Handle resolution slider changes."""
        self.pending_resolution_idx = self._snap_slider(self.res_slider, self.on_res_slider_change, 0, len(self.resolutions) - 1)
        width, height = self.resolutions[self.pending_resolution_idx]
        self.res_label["text"] = f"RESOLUTION: {width} x {height}"

    def on_ui_scale_slider_change(self) -> None:
        """Handle UI scale slider changes."""
        idx = self._snap_slider(self.ui_scale_slider, self.on_ui_scale_slider_change, 0, len(UI_SCALE_VALUES) - 1)
        self.pending_ui_scale = UI_SCALE_VALUES[idx]
        self.ui_scale_label["text"] = f"UI SCALE: {int(self.pending_ui_scale * 100)}%"

    def on_text_scale_slider_change(self) -> None:
        """Handle text scale slider changes."""
        idx = self._snap_slider(self.text_scale_slider, self.on_text_scale_slider_change, 0, len(TEXT_SCALE_VALUES) - 1)
        self.pending_text_scale = TEXT_SCALE_VALUES[idx]
        self.text_scale_label["text"] = f"TEXT SIZE: {int(self.pending_text_scale * 100)}%"

    def on_master_vol_change(self) -> None:
        """Handle master-volume slider changes."""
        self.pending_master_volume = float(self.master_vol_slider.getValue())
        self.master_vol_label["text"] = f"MASTER VOLUME: {int(self.pending_master_volume * 100)}%"

    def on_music_vol_change(self) -> None:
        """Handle music-volume slider changes."""
        self.pending_music_volume = float(self.music_vol_slider.getValue())
        self.music_vol_label["text"] = f"MUSIC VOLUME: {int(self.pending_music_volume * 100)}%"

    def on_sfx_vol_change(self) -> None:
        """Handle SFX-volume slider changes."""
        self.pending_sfx_volume = float(self.sfx_vol_slider.getValue())
        self.sfx_vol_label["text"] = f"SFX VOLUME: {int(self.pending_sfx_volume * 100)}%"

    def update_fullscreen_button_visual(self, active: bool) -> None:
        self._set_button_visual(self.btn_full, "FULLSCREEN: ACTIVE" if active else "FULLSCREEN: INACTIVE", active)

    def update_vfx_button_visual(self, active: bool) -> None:
        self._set_button_visual(self.btn_vfx, "VFX QUALITY: ACTIVE" if active else "VFX QUALITY: INACTIVE", active)

    def update_high_contrast_visual(self, active: bool) -> None:
        self._set_button_visual(self.btn_high_contrast, "HIGH CONTRAST: ON" if active else "HIGH CONTRAST: OFF", active)

    def update_reduce_motion_visual(self, active: bool) -> None:
        self._set_button_visual(self.btn_reduce_motion, "REDUCE MOTION: ON" if active else "REDUCE MOTION: OFF", active)

    def update_mute_visual(self, button, is_muted: bool, label_prefix: str) -> None:
        self._set_button_visual(button, f"MUTE {label_prefix}: {'ON' if is_muted else 'OFF'}", not is_muted)

    def update_coop_visual(self, active: bool) -> None:
        self._set_button_visual(self.btn_coop, "CO-OP: ACTIVE" if active else "CO-OP: INACTIVE", active)

    def update_show_intro_visual(self, active: bool) -> None:
        self._set_button_visual(self.btn_show_intro, "INTRO BRIEFING: SHOW" if active else "INTRO BRIEFING: HIDE", active)

    def update_fullscreen_button(self) -> None:
        """Backward-compatible hook used by older tests."""
        self.update_fullscreen_button_visual(self.pending_fullscreen)

    def on_fullscreen_toggle(self) -> None:
        self.pending_fullscreen = not self.pending_fullscreen
        self.update_fullscreen_button_visual(self.pending_fullscreen)

    def on_vfx_toggle(self) -> None:
        self.pending_vfx_high = not self.pending_vfx_high
        self.update_vfx_button_visual(self.pending_vfx_high)

    def on_high_contrast_toggle(self) -> None:
        self.pending_high_contrast_text = not self.pending_high_contrast_text
        self.update_high_contrast_visual(self.pending_high_contrast_text)

    def on_reduce_motion_toggle(self) -> None:
        self.pending_reduce_ui_motion = not self.pending_reduce_ui_motion
        self.update_reduce_motion_visual(self.pending_reduce_ui_motion)

    def on_master_mute_toggle(self) -> None:
        self.pending_master_muted = not self.pending_master_muted
        self.update_mute_visual(self.btn_master_mute, self.pending_master_muted, "MASTER")

    def on_music_mute_toggle(self) -> None:
        self.pending_music_muted = not self.pending_music_muted
        self.update_mute_visual(self.btn_music_mute, self.pending_music_muted, "MUSIC")

    def on_sfx_mute_toggle(self) -> None:
        self.pending_sfx_muted = not self.pending_sfx_muted
        self.update_mute_visual(self.btn_sfx_mute, self.pending_sfx_muted, "SFX")

    def on_coop_toggle(self) -> None:
        self.pending_coop_mode = not self.pending_coop_mode
        self.update_coop_visual(self.pending_coop_mode)

    def on_show_intro_toggle(self) -> None:
        self.pending_show_intro = not self.pending_show_intro
        self.update_show_intro_visual(self.pending_show_intro)

    def on_test_sfx_click(self) -> None:
        """Play a lightweight SFX preview when available."""
        if self.app and hasattr(self.app, "play_sound") and getattr(self.app, "pickup_sfx", None):
            self.app.play_sound(self.app.pickup_sfx)

    def has_unapplied_settings(self) -> bool:
        """Return whether pending settings differ from persisted/runtime state."""
        settings = getattr(self.app, "settings", GameSettings())
        state_mgr = getattr(self.app, "state_mgr", None)
        width, height = self.resolutions[self.pending_resolution_idx]
        return any(
            [
                self.pending_difficulty != getattr(state_mgr, "difficulty", settings.difficulty),
                self.pending_coop_mode != getattr(state_mgr, "coop_mode", settings.coop_mode),
                self.pending_vfx_high != getattr(state_mgr, "vfx_high", settings.vfx_high),
                self.pending_fullscreen != settings.fullscreen,
                (width, height) != tuple(settings.resolution),
                self.pending_ui_scale != settings.ui_scale,
                self.pending_text_scale != settings.text_scale,
                self.pending_high_contrast_text != settings.high_contrast_text,
                self.pending_reduce_ui_motion != settings.reduce_ui_motion,
                abs(self.pending_master_volume - settings.master_volume) > 0.001,
                abs(self.pending_music_volume - settings.music_volume) > 0.001,
                abs(self.pending_sfx_volume - settings.sfx_volume) > 0.001,
                self.pending_master_muted != settings.master_muted,
                self.pending_music_muted != settings.music_muted,
                self.pending_sfx_muted != settings.sfx_muted,
                self.pending_show_intro != settings.show_intro,
                self.pending_hud_density != getattr(settings, "hud_density", "compact"),
            ]
        )

    def on_settings_click(self, from_menu: bool = True) -> None:
        """Open Bridge Calibration and discard unsaved draft drift."""
        self._init_pending_from_app()
        self.refresh_settings_controls_visuals()
        self.confirm_modal.hide()
        self.menu_sub_state = "settings"
        self.show_settings_tab(self.active_settings_tab or "display")
        if self.app:
            self.update_screen_state(self.app.state_mgr.current_state)

    def on_tutorial_click(self) -> None:
        """Open the tactical manual."""
        self.menu_sub_state = "tutorial"
        if self.app:
            self.update_screen_state(self.app.state_mgr.current_state)

    def on_back_click(self) -> None:
        """Return to main menu, confirming unsaved settings when needed."""
        if self.menu_sub_state == "settings" and self.has_unapplied_settings():
            self.confirm_modal.show()
            return
        self.menu_sub_state = "main"
        if self.app:
            self.update_screen_state(self.app.state_mgr.current_state)

    def on_confirm_cancel(self) -> None:
        self.confirm_modal.hide()

    def on_confirm_discard(self) -> None:
        self.confirm_modal.hide()
        self._init_pending_from_app()
        self.refresh_settings_controls_visuals()
        self.menu_sub_state = "main"
        if self.app:
            self.update_screen_state(self.app.state_mgr.current_state)

    def on_confirm_apply(self) -> None:
        self.on_apply_changes()
        self.confirm_modal.hide()
        self.menu_sub_state = "main"
        if self.app:
            self.update_screen_state(self.app.state_mgr.current_state)

    def _apply_window_settings(self, width: int, height: int) -> None:
        """Apply window settings through Panda3D when a real window exists."""
        if not self.app or getattr(self.app, "headless", False) or not getattr(self.app, "win", None):
            return
        try:
            from panda3d.core import WindowProperties

            props = WindowProperties()
            props.setFullscreen(self.pending_fullscreen)
            props.setSize(width, height)
            self.app.win.requestProperties(props)
        except Exception:
            pass

    def _schedule_rebuild_if_needed(self, old_ui_scale: float, old_text_scale: float) -> None:
        """Schedule an app UI rebuild when scale/density settings require it."""
        if not self.app or getattr(self.app, "headless", False):
            return
        if old_ui_scale == self.pending_ui_scale and old_text_scale == self.pending_text_scale:
            return
        if not hasattr(self.app, "rebuild_ui"):
            return

        def do_rebuild(task):
            self.app.rebuild_ui()
            return task.done

        try:
            self.app.taskMgr.doMethodLater(0.01, do_rebuild, "rebuild-ui-after-settings")
        except Exception:
            pass

    def on_apply_changes(self) -> None:
        """Apply and persist pending settings."""
        if not self.app:
            return
        old_ui_scale = self.app.settings.ui_scale
        old_text_scale = self.app.settings.text_scale
        old_hud_density = getattr(self.app.settings, "hud_density", "compact")
        width, height = self.resolutions[self.pending_resolution_idx]
        settings = self.app.settings
        settings.difficulty = self.pending_difficulty
        settings.coop_mode = self.pending_coop_mode
        settings.vfx_high = self.pending_vfx_high
        settings.fullscreen = self.pending_fullscreen
        settings.resolution = (width, height)
        settings.ui_scale = self.pending_ui_scale
        settings.text_scale = self.pending_text_scale
        settings.high_contrast_text = self.pending_high_contrast_text
        settings.reduce_ui_motion = self.pending_reduce_ui_motion
        settings.master_volume = self.pending_master_volume
        settings.music_volume = self.pending_music_volume
        settings.sfx_volume = self.pending_sfx_volume
        settings.master_muted = self.pending_master_muted
        settings.music_muted = self.pending_music_muted
        settings.sfx_muted = self.pending_sfx_muted
        settings.show_intro = self.pending_show_intro
        settings.hud_density = self.pending_hud_density
        save_settings(settings)
        self.app.state_mgr.difficulty = settings.difficulty
        self.app.state_mgr.coop_mode = settings.coop_mode
        self.app.state_mgr.vfx_high = settings.vfx_high
        self.app.state_mgr.intro_active = settings.show_intro
        if hasattr(self.app, "audio_mgr"):
            self.app.audio_mgr.apply_volume_settings(settings)
        self._apply_window_settings(width, height)
        self._init_pending_from_app()
        self.refresh_settings_controls_visuals()
        if old_hud_density != settings.hud_density:
            old_ui_scale = -1.0
        self._schedule_rebuild_if_needed(old_ui_scale, old_text_scale)

    def on_reset_defaults(self) -> None:
        """Reset pending values to safe defaults without persisting immediately."""
        defaults = GameSettings()
        self.pending_difficulty = defaults.difficulty
        self.pending_coop_mode = defaults.coop_mode
        self.pending_vfx_high = defaults.vfx_high
        self.pending_fullscreen = defaults.fullscreen
        self.pending_resolution_idx = self._resolution_index(defaults.resolution)
        self.pending_ui_scale = defaults.ui_scale
        self.pending_text_scale = defaults.text_scale
        self.pending_high_contrast_text = defaults.high_contrast_text
        self.pending_reduce_ui_motion = defaults.reduce_ui_motion
        self.pending_master_volume = defaults.master_volume
        self.pending_music_volume = defaults.music_volume
        self.pending_sfx_volume = defaults.sfx_volume
        self.pending_master_muted = defaults.master_muted
        self.pending_music_muted = defaults.music_muted
        self.pending_sfx_muted = defaults.sfx_muted
        self.pending_show_intro = defaults.show_intro
        self.pending_hud_density = defaults.hud_density
        self.refresh_settings_controls_visuals()

    def on_start_click(self) -> None:
        if self.app:
            self.app.input_mgr.handle_enter()

    def on_restart_click(self) -> None:
        if self.app:
            self.app.input_mgr.handle_restart()

    def on_menu_click(self) -> None:
        if self.app:
            if hasattr(self.app, "clear_views"):
                self.app.clear_views()
            self.app.state_mgr.transition_to(GameStateID.MENU)
            self.menu_sub_state = "main"
            self.update_screen_state(self.app.state_mgr.current_state)

    def on_quit_click(self) -> None:
        if self.app and hasattr(self.app, "clean_quit"):
            self.app.clean_quit()

    def destroy(self) -> None:
        """Destroy all top-level DirectGUI screen frames."""
        for frame in (self.menu_frame, self.tutorial_frame, self.settings_frame, self.gameover_frame, self.victory_frame, self.paused_frame):
            try:
                frame.destroy()
            except Exception:
                pass
