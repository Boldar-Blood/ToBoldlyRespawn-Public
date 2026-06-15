# src/space_demo/core/settings_store.py

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import os
import sys
from typing import Any

VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_HUD_DENSITIES = {"full", "compact", "minimal"}
VALID_UI_SCALES = [0.85, 1.0, 1.15, 1.30, 1.50]
VALID_TEXT_SCALES = [0.85, 1.0, 1.15, 1.30, 1.50]


@dataclass
class GameSettings:
    """Persistent user-adjustable game, display, UI, and audio settings."""

    difficulty: str = "medium"
    coop_mode: bool = False
    vfx_high: bool = True
    fullscreen: bool = False
    resolution: tuple[int, int] = (1280, 720)
    show_intro: bool = True
    hud_density: str = "compact"

    ui_scale: float = 1.0
    text_scale: float = 1.0
    high_contrast_text: bool = False
    reduce_ui_motion: bool = False

    master_volume: float = 0.85
    music_volume: float = 0.65
    sfx_volume: float = 0.85
    master_muted: bool = False
    music_muted: bool = False
    sfx_muted: bool = False


def get_settings_path() -> Path:
    """Return the per-user settings path for the current platform."""
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "ToBoldlyRespawn" / "settings.json"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "ToBoldlyRespawn" / "settings.json"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "ToBoldlyRespawn" / "settings.json"


def clamp_float(value: Any, default: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp a numeric setting or return its default when invalid."""
    try:
        return max(lo, min(hi, float(value)))
    except (TypeError, ValueError):
        return default


def nearest(value: Any, valid_values: list[float], default: float) -> float:
    """Snap a numeric setting to the nearest supported discrete value."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return min(valid_values, key=lambda x: abs(x - v))


def normalize_choice(value: Any, valid_values: set[str], default: str) -> str:
    """Return a normalized string choice or the default when invalid."""
    if isinstance(value, str):
        normalized = value.lower().strip()
        if normalized in valid_values:
            return normalized
    return default


def normalize_settings(raw: dict[str, Any]) -> GameSettings:
    """Normalize raw JSON into a safe GameSettings instance."""
    defaults = GameSettings()

    difficulty = normalize_choice(raw.get("difficulty", defaults.difficulty), VALID_DIFFICULTIES, defaults.difficulty)
    hud_density = normalize_choice(raw.get("hud_density", defaults.hud_density), VALID_HUD_DENSITIES, defaults.hud_density)

    resolution_raw = raw.get("resolution", list(defaults.resolution))
    if (
        isinstance(resolution_raw, (list, tuple))
        and len(resolution_raw) == 2
        and all(isinstance(x, int) for x in resolution_raw)
    ):
        resolution = (max(640, resolution_raw[0]), max(360, resolution_raw[1]))
    else:
        resolution = defaults.resolution

    return GameSettings(
        difficulty=difficulty,
        coop_mode=bool(raw.get("coop_mode", defaults.coop_mode)),
        vfx_high=bool(raw.get("vfx_high", defaults.vfx_high)),
        fullscreen=bool(raw.get("fullscreen", defaults.fullscreen)),
        resolution=resolution,
        show_intro=bool(raw.get("show_intro", defaults.show_intro)),
        hud_density=hud_density,
        ui_scale=nearest(raw.get("ui_scale", defaults.ui_scale), VALID_UI_SCALES, defaults.ui_scale),
        text_scale=nearest(raw.get("text_scale", defaults.text_scale), VALID_TEXT_SCALES, defaults.text_scale),
        high_contrast_text=bool(raw.get("high_contrast_text", defaults.high_contrast_text)),
        reduce_ui_motion=bool(raw.get("reduce_ui_motion", defaults.reduce_ui_motion)),
        master_volume=clamp_float(raw.get("master_volume", defaults.master_volume), defaults.master_volume),
        music_volume=clamp_float(raw.get("music_volume", defaults.music_volume), defaults.music_volume),
        sfx_volume=clamp_float(raw.get("sfx_volume", defaults.sfx_volume), defaults.sfx_volume),
        master_muted=bool(raw.get("master_muted", defaults.master_muted)),
        music_muted=bool(raw.get("music_muted", defaults.music_muted)),
        sfx_muted=bool(raw.get("sfx_muted", defaults.sfx_muted)),
    )


def load_settings() -> GameSettings:
    """Load persisted settings, returning defaults when the file is absent or invalid."""
    path = get_settings_path()
    if not path.exists():
        return GameSettings()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return GameSettings()
        return normalize_settings(raw)
    except Exception:
        return GameSettings()


def save_settings(settings: GameSettings) -> Path:
    """Write settings JSON and return the saved path."""
    path = get_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(settings)
    data["resolution"] = list(settings.resolution)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return path
