"""Central styling and readability helpers for To Boldly Respawn UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

Color = Tuple[float, float, float, float]
Resolution = Tuple[int, int]


@dataclass(frozen=True)
class UIColors:
    panel_bg: Color = (0.015, 0.025, 0.060, 0.82)
    panel_bg_dark: Color = (0.005, 0.010, 0.030, 0.92)
    panel_stroke: Color = (0.20, 0.75, 1.00, 0.95)
    panel_glow: Color = (0.10, 0.55, 1.00, 0.45)

    text_primary: Color = (0.92, 0.96, 1.00, 1.00)
    text_secondary: Color = (0.70, 0.82, 0.95, 1.00)
    text_warning: Color = (1.00, 0.78, 0.20, 1.00)
    text_danger: Color = (1.00, 0.25, 0.18, 1.00)
    text_success: Color = (0.20, 1.00, 0.55, 1.00)

    button_bg: Color = (0.05, 0.17, 0.30, 0.92)
    button_hover: Color = (0.10, 0.45, 0.85, 0.98)
    button_pressed: Color = (0.04, 0.12, 0.24, 1.00)
    button_disabled: Color = (0.20, 0.20, 0.24, 0.65)

    green: Color = (0.20, 0.90, 0.45, 1.00)
    amber: Color = (1.00, 0.68, 0.18, 1.00)
    orange: Color = (1.00, 0.38, 0.12, 1.00)
    red: Color = (1.00, 0.15, 0.12, 1.00)
    purple: Color = (0.70, 0.35, 1.00, 1.00)
    cyan: Color = (0.18, 0.80, 1.00, 1.00)


@dataclass(frozen=True)
class UIFonts:
    title_scale: float = 0.095
    subtitle_scale: float = 0.048
    heading_scale: float = 0.052
    body_scale: float = 0.032
    small_scale: float = 0.025
    button_scale: float = 0.038
    hud_scale: float = 0.030
    min_scale: float = 0.022


@dataclass(frozen=True)
class UISpacing:
    panel_pad_x: float = 0.055
    panel_pad_z: float = 0.045
    row_gap: float = 0.095
    button_w: float = 0.58
    button_h: float = 0.090
    button_gap: float = 0.125
    modal_w: float = 1.05
    modal_h: float = 0.48


@dataclass(frozen=True)
class UILayers:
    # --- DirectGUI Sibling sortOrder Constants ---
    # These govern layout ordering among sibling widgets attached to the same parent.
    # Higher values draw on top.
    curated_skin: int = -10  # Placed inside panel root frame, draws behind panels/buttons
    background: int = 0      # Background frames/canvases
    panel: int = 20          # Standard backing panels
    button: int = 30         # Interactive components (buttons, sliders, etc.)
    text: int = 40           # Foreground text labels
    modal: int = 80          # Modals overlaying standard screens
    tooltip: int = 90        # Tooltips hovering above everything

    # --- Panda3D NodePath Render Bin & Sort Constants ---
    # These govern global rendering phases/order in Panda3D's scene graph.
    BIN_BACKGROUND: str = "background"
    BIN_FIXED: str = "fixed"
    BIN_TRANSPARENT: str = "transparent"

    SORT_BG_CARD: int = 0
    SORT_MENU_BG: int = 1
    SORT_EARLY_SPLASH_BG: int = 9999
    SORT_EARLY_SPLASH_FG: int = 10000



def normalize_resolution(resolution: Iterable[int] | None, fallback: Resolution = (1280, 720)) -> Resolution:
    """Return a safe integer ``(width, height)`` tuple."""
    try:
        width, height = resolution  # type: ignore[misc]
        width = int(width)
        height = int(height)
    except Exception:
        return fallback
    if width <= 0 or height <= 0:
        return fallback
    return (width, height)


def readability_multiplier_for_resolution(resolution: Iterable[int] | None) -> float:
    """Return a conservative text-readability baseline for the viewport.

    Physical display size is not reliable across every desktop/mobile target, so
    the shorter viewport dimension is used as a conservative proxy. These values
    bias default text toward small laptops, phones, and 7-inch tablets; the
    player's text-size setting is then applied on top of this baseline.
    """
    width, height = normalize_resolution(resolution)
    short_edge = min(width, height)
    if short_edge <= 540:
        return 1.42
    if short_edge <= 720:
        return 1.34
    if short_edge <= 900:
        return 1.25
    if short_edge <= 1080:
        return 1.16
    if short_edge <= 1440:
        return 1.08
    return 1.00


def effective_text_scale(user_text_scale: float, resolution: Iterable[int] | None) -> float:
    """Apply readable defaults to the user's text-size preference."""
    try:
        scale = float(user_text_scale)
    except (TypeError, ValueError):
        scale = 1.0
    return max(0.80, min(2.25, scale * readability_multiplier_for_resolution(resolution)))


COLORS = UIColors()
FONTS = UIFonts()
SPACING = UISpacing()
LAYERS = UILayers()
