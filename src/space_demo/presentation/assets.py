"""Presentation asset loading for To Boldly Respawn."""

from __future__ import annotations

import json
from pathlib import Path

from panda3d.core import Filename


class AssetManager:
    """Load runtime textures with curated sprites preferred over fallbacks."""

    def __init__(self, app):
        self.app = app
        self.headless = app.headless
        self.loader = app.loader
        self.manifest: dict = {}
        self.player_tex = None
        self.player_hull_100_tex = None
        self.player_hull_75_tex = None
        self.player_hull_50_tex = None
        self.player_hull_25_tex = None
        self.player_hull_critical_tex = None
        self.drone_tex = None
        self.enemy_drone_tex = None
        self.enemy_speeder_tex = None
        self.enemy_zigzag_tex = None
        self.enemy_frigate_tex = None
        self.enemy_missile_boat_tex = None
        self.enemy_mine_tex = None
        self.boss_tex = None
        self.boss_phase_1_tex = None
        self.boss_phase_2_tex = None
        self.boss_phase_3_tex = None
        self.boss_destroyed_tex = None
        self.pickup_health_tex = None
        self.pickup_speed_tex = None
        self.pickup_shield_tex = None
        self.pickup_bomb_tex = None
        self.pickup_magnet_tex = None
        self.pickup_intern_tex = None
        self.pickup_missile_tex = None
        self.shield_skin_tex = None
        self.laser_player_tex = None
        self.laser_enemy_tex = None
        self.missile_tex = None
        self.menu_bg_tex = None
        self.title_banner_tex = None
        self.icon_player_mini_tex = None
        self.icon_dreadnought_mini_tex = None
        self.ui_pursuit_gauge_tex = None
        self.ui_panel_glass_tex = None
        self.ui_panel_card_tex = None
        self.vfx_muzzle_flash = None
        self.vfx_explosion_core = None
        self.vfx_explosion_ring = None
        self.vfx_smoke_puff = None
        self.vfx_spark = None
        self.vfx_shockwave_orange = None
        self.vfx_shockwave_cyan = None
        self.consolas_font = None
        self.consolas_font_3d = None
        self.app.assets = self

        from space_demo.core.procedural_gui import generate_gui_assets
        from space_demo.core.generated_assets import generate_extra_assets

        generate_gui_assets()
        generate_extra_assets()
        self.manifest = self._load_manifest()

        if not self.headless:
            self.load_assets()

    @staticmethod
    def _data_dir() -> Path:
        """Return the repository/package data directory used by loaders."""
        return Path(__file__).resolve().parents[3] / "data"

    def _load_manifest(self) -> dict:
        """Load the optional curated asset manifest."""
        path = self._data_dir() / "asset_manifest.json"
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _load_texture_path(self, path: Path, fallback=None):
        """Load a texture path if it exists, otherwise return fallback."""
        if not path.exists():
            return fallback
        return self.loader.loadTexture(Filename.fromOsSpecific(str(path)))

    def _load_manifest_texture(self, key: str, fallback=None):
        """Load the first existing texture path for a manifest key."""
        data_dir = self._data_dir()
        paths = self.manifest.get("textures", {}).get(key, [])
        if isinstance(paths, str):
            paths = [paths]
        for rel in paths:
            path = data_dir / rel
            if path.exists():
                return self.loader.loadTexture(Filename.fromOsSpecific(str(path)))
        return fallback

    def _load_texture(self, filename: str, fallback=None):
        """Load a legacy data texture, returning fallback if absent."""
        return self._load_texture_path(self._data_dir() / filename, fallback)

    def _load_font_candidates(self) -> None:
        """Keep the default Panda3D font when no bundled font is provided."""
        print("[GUI Font] Using Panda3D defaults.")

    def load_assets(self):
        """Load all runtime textures, preferring curated sprites."""
        self.player_tex = self._load_manifest_texture("player")
        self.player_hull_100_tex = self._load_manifest_texture("player_hull_100", self.player_tex)
        self.player_hull_75_tex = self._load_manifest_texture("player_hull_75", self.player_tex)
        self.player_hull_50_tex = self._load_manifest_texture("player_hull_50", self.player_tex)
        self.player_hull_25_tex = self._load_manifest_texture("player_hull_25", self.player_tex)
        self.player_hull_critical_tex = self._load_manifest_texture("player_hull_critical", self.player_tex)
        legacy_drone = self._load_texture("drone_skin.png")
        self.enemy_drone_tex = self._load_manifest_texture("enemy_drone", legacy_drone)
        self.enemy_speeder_tex = self._load_manifest_texture("enemy_speeder", self.enemy_drone_tex)
        self.enemy_zigzag_tex = self._load_manifest_texture("enemy_zigzag", self.enemy_drone_tex)
        self.enemy_frigate_tex = self._load_manifest_texture("enemy_frigate", self.enemy_drone_tex)
        self.enemy_missile_boat_tex = self._load_manifest_texture("enemy_missile_boat", self.enemy_drone_tex)
        self.enemy_mine_tex = self._load_manifest_texture("enemy_mine", self.enemy_drone_tex)
        self.drone_tex = self.enemy_drone_tex or legacy_drone
        self.boss_tex = self._load_texture("boss_skin.png")
        self.boss_phase_1_tex = self._load_manifest_texture("boss_phase_1", self.boss_tex)
        self.boss_phase_2_tex = self._load_manifest_texture("boss_phase_2", self.boss_phase_1_tex)
        self.boss_phase_3_tex = self._load_manifest_texture("boss_phase_3", self.boss_phase_2_tex)
        self.boss_destroyed_tex = self._load_manifest_texture("boss_destroyed", self.boss_phase_3_tex)
        self.pickup_health_tex = self._load_texture("pickup_health.png")
        self.pickup_speed_tex = self._load_texture("pickup_speed.png")
        self.pickup_shield_tex = self._load_texture("pickup_shield.png")
        self.pickup_bomb_tex = self._load_texture("pickup_bomb.png")
        self.pickup_magnet_tex = self._load_texture("pickup_magnet.png")
        self.pickup_intern_tex = self._load_texture("pickup_intern.png")
        self.pickup_missile_tex = self._load_texture("pickup_missile.png")
        self.shield_skin_tex = self._load_texture("shield_skin.png")
        self.laser_player_tex = self._load_texture("laser_player.png")
        self.laser_enemy_tex = self._load_texture("laser_enemy.png")
        self.missile_tex = self._load_texture("missile_skin.png")
        self.menu_bg_tex = self._load_manifest_texture("menu_background", self._load_texture("start_menu_background.png"))
        self.title_banner_tex = self._load_manifest_texture("title_banner")
        self.icon_player_mini_tex = self._load_manifest_texture("icon_player_mini")
        self.icon_dreadnought_mini_tex = self._load_manifest_texture("icon_dreadnought_mini")
        self.ui_pursuit_gauge_tex = self._load_manifest_texture("pursuit_gauge")
        self.ui_panel_glass_tex = self._load_manifest_texture("ui_panel_glass")
        self.ui_panel_card_tex = self._load_manifest_texture("ui_panel_card")
        self.vfx_muzzle_flash = self._load_manifest_texture("vfx_muzzle_flash")
        self.vfx_explosion_core = self._load_manifest_texture("vfx_explosion_core")
        self.vfx_explosion_ring = self._load_manifest_texture("vfx_explosion_ring")
        self.vfx_smoke_puff = self._load_manifest_texture("vfx_smoke_puff")
        self.vfx_spark = self._load_manifest_texture("vfx_spark")
        self.vfx_shockwave_orange = self._load_manifest_texture("vfx_shockwave_orange")
        self.vfx_shockwave_cyan = self._load_manifest_texture("vfx_shockwave_cyan")
        self._load_font_candidates()

    def pickup_texture(self, pickup_type: str):
        """Return the texture assigned to a pickup type, with health as the safe default."""
        textures = {
            "health": self.pickup_health_tex,
            "speed": self.pickup_speed_tex,
            "shield": self.pickup_shield_tex,
            "bomb": self.pickup_bomb_tex,
            "magnet": self.pickup_magnet_tex,
            "intern": self.pickup_intern_tex,
            "missile": self.pickup_missile_tex,
        }
        return textures.get(pickup_type, self.pickup_health_tex)
