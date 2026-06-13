"""Main Menu layout helper.

The main menu is the first screen players see, so its coordinates are centralized
here instead of hand-authored inside the screen builder. Values are expressed in
the local coordinate space of the existing centered DirectGUI panel.
"""

from __future__ import annotations

from dataclasses import dataclass


_FLOAT_PRECISION = 12


def _clean(value: float) -> float:
    """Round binary floating-point artifacts out of layout constants."""
    cleaned = round(float(value), _FLOAT_PRECISION)
    return 0.0 if cleaned == -0.0 else cleaned


def _pos(x_pos: float, z_pos: float) -> tuple[float, float, float]:
    """Return a cleaned DirectGUI-style position tuple."""
    return (_clean(x_pos), 0.0, _clean(z_pos))


def compute_cover_size(
    view_width: float,
    view_height: float,
    image_width: float,
    image_height: float,
) -> tuple[float, float]:
    """Return the smallest aspect-preserving size that fills a viewport."""
    view_width = max(0.001, float(view_width))
    view_height = max(0.001, float(view_height))
    image_width = max(0.001, float(image_width))
    image_height = max(0.001, float(image_height))

    view_aspect = view_width / view_height
    image_aspect = image_width / image_height

    if image_aspect >= view_aspect:
        target_height = view_height
        target_width = target_height * image_aspect
    else:
        target_width = view_width
        target_height = target_width / image_aspect

    return (_clean(target_width), _clean(target_height))


@dataclass(frozen=True)
class MainMenuLayout:
    """Parent-local layout data for the main menu screen."""

    panel_size: tuple[float, float]
    bracket_pos: tuple[float, float, float]
    bracket_scale: tuple[float, float, float]
    title_pos: tuple[float, float, float]
    title_scale: tuple[float, float, float]
    fallback_title_pos: tuple[float, float, float]
    fallback_subtitle_pos: tuple[float, float, float]
    nav_x: float
    nav_z: tuple[float, float, float, float]
    button_width: float
    button_height: float
    briefing_pos: tuple[float, float, float]
    briefing_size: tuple[float, float]
    briefing_text_pos: tuple[float, float, float]
    briefing_text_scale: float


def build_main_menu_layout(ui_scale: float = 1.0) -> MainMenuLayout:
    """Return deterministic main-menu positions and sizes."""
    ui_scale = _clean(ui_scale)
    return MainMenuLayout(
        panel_size=(_clean(1.90 * ui_scale), _clean(1.30 * ui_scale)),
        bracket_pos=_pos(0.0, -0.02 * ui_scale),
        bracket_scale=(_clean(0.90 * ui_scale), 1.0, _clean(0.60 * ui_scale)),
        title_pos=_pos(0.0, 0.310 * ui_scale),
        title_scale=(_clean(0.50 * ui_scale), 1.0, _clean(0.1875 * ui_scale)),
        fallback_title_pos=_pos(0.0, 0.360 * ui_scale),
        fallback_subtitle_pos=_pos(0.0, 0.270 * ui_scale),
        nav_x=_clean(-0.32 * ui_scale),
        nav_z=tuple(_clean(z * ui_scale) for z in (0.020, -0.095, -0.210, -0.325)),
        button_width=_clean(0.50 * ui_scale),
        button_height=_clean(0.076 * ui_scale),
        briefing_pos=_pos(0.38 * ui_scale, -0.170 * ui_scale),
        briefing_size=(_clean(0.62 * ui_scale), _clean(0.40 * ui_scale)),
        briefing_text_pos=_pos(-0.245 * ui_scale, 0.115 * ui_scale),
        briefing_text_scale=_clean(0.0155 * ui_scale),
    )
