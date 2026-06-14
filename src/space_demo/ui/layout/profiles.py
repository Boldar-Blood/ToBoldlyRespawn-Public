"""Responsive UI layout profiles.

Profiles describe how much UI can safely remain visible for a viewport. They do
not skin widgets or create Panda3D nodes; they only provide deterministic layout
policy for screen builders.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from space_demo.ui.layout.viewport import ViewportContext


class HudDensity(str, Enum):
    """Player-selectable active gameplay HUD density."""

    FULL = "full"
    COMPACT = "compact"
    MINIMAL = "minimal"


class LayoutProfileName(str, Enum):
    """Supported responsive layout families."""

    PHONE_PORTRAIT = "phone_portrait"
    PHONE_LANDSCAPE = "phone_landscape"
    TABLET_PORTRAIT = "tablet_portrait"
    TABLET_LANDSCAPE = "tablet_landscape"
    DESKTOP = "desktop"
    ULTRAWIDE = "ultrawide"


@dataclass(frozen=True)
class LayoutProfile:
    """High-level responsive policy for one viewport class."""

    name: LayoutProfileName
    hud_density: HudDensity
    persistent_hud_budget: float
    left_console_width_pct: float
    right_gauge_width_pct: float
    show_log_when_empty: bool
    max_log_entries: int
    allow_collapsible_panels: bool
    center_modal_width_pct: float
    center_modal_height_pct: float
    intro_wrap_chars: int


def choose_layout_profile(
    viewport: ViewportContext,
    preferred_density: HudDensity | str | None = None,
) -> LayoutProfile:
    """Choose a responsive profile for the active viewport.

    The preferred density is a player setting. Compact touch viewports may clamp
    that preference downward so UI never crowds the combat lane. Keyboard/mouse
    windows stay on desktop-style profiles even when the window is temporarily
    small, because a small desktop window is not the same interaction context as
    a phone held in landscape.
    """
    density = _normalize_density(preferred_density)
    ratio = viewport.aspect_ratio
    short_side = viewport.short_side_px
    orientation = viewport.orientation
    touch_first = viewport.touch_first

    if orientation == "portrait" and short_side < 800:
        return _phone_portrait(HudDensity.MINIMAL if density == HudDensity.FULL else density)
    if touch_first and orientation == "landscape" and viewport.safe_height_px < 760 and short_side < 800:
        return _phone_landscape(HudDensity.MINIMAL if density != HudDensity.FULL else HudDensity.COMPACT)
    if ratio >= 2.2:
        return _ultrawide(density)
    if not touch_first and orientation == "landscape":
        return _desktop(density)
    if short_side >= 1000 and orientation == "portrait":
        return _tablet_portrait(density)
    if touch_first and short_side >= 900:
        return _tablet_landscape(density)
    return _desktop(density)


def _normalize_density(value: HudDensity | str | None) -> HudDensity:
    if isinstance(value, HudDensity):
        return value
    if isinstance(value, str):
        try:
            return HudDensity(value.lower().strip())
        except ValueError:
            return HudDensity.COMPACT
    return HudDensity.COMPACT


def _desktop(density: HudDensity) -> LayoutProfile:
    return LayoutProfile(
        name=LayoutProfileName.DESKTOP,
        hud_density=density,
        persistent_hud_budget=0.22 if density == HudDensity.FULL else 0.18,
        left_console_width_pct=0.125,
        right_gauge_width_pct=0.065,
        show_log_when_empty=density == HudDensity.FULL,
        max_log_entries=5 if density == HudDensity.FULL else 3,
        allow_collapsible_panels=True,
        center_modal_width_pct=0.50,
        center_modal_height_pct=0.44,
        intro_wrap_chars=42,
    )


def _ultrawide(density: HudDensity) -> LayoutProfile:
    profile = _desktop(density)
    return LayoutProfile(
        name=LayoutProfileName.ULTRAWIDE,
        hud_density=profile.hud_density,
        persistent_hud_budget=profile.persistent_hud_budget,
        left_console_width_pct=0.105,
        right_gauge_width_pct=0.050,
        show_log_when_empty=profile.show_log_when_empty,
        max_log_entries=profile.max_log_entries,
        allow_collapsible_panels=True,
        center_modal_width_pct=0.42,
        center_modal_height_pct=0.42,
        intro_wrap_chars=44,
    )


def _phone_portrait(density: HudDensity) -> LayoutProfile:
    return LayoutProfile(
        name=LayoutProfileName.PHONE_PORTRAIT,
        hud_density=density,
        persistent_hud_budget=0.14,
        left_console_width_pct=0.0,
        right_gauge_width_pct=0.070,
        show_log_when_empty=False,
        max_log_entries=1 if density == HudDensity.MINIMAL else 2,
        allow_collapsible_panels=True,
        center_modal_width_pct=0.86,
        center_modal_height_pct=0.38,
        intro_wrap_chars=30,
    )


def _phone_landscape(density: HudDensity) -> LayoutProfile:
    return LayoutProfile(
        name=LayoutProfileName.PHONE_LANDSCAPE,
        hud_density=density,
        persistent_hud_budget=0.12,
        left_console_width_pct=0.090,
        right_gauge_width_pct=0.050,
        show_log_when_empty=False,
        max_log_entries=1,
        allow_collapsible_panels=True,
        center_modal_width_pct=0.46,
        center_modal_height_pct=0.48,
        intro_wrap_chars=34,
    )


def _tablet_portrait(density: HudDensity) -> LayoutProfile:
    return LayoutProfile(
        name=LayoutProfileName.TABLET_PORTRAIT,
        hud_density=density,
        persistent_hud_budget=0.18,
        left_console_width_pct=0.110,
        right_gauge_width_pct=0.060,
        show_log_when_empty=density == HudDensity.FULL,
        max_log_entries=3 if density != HudDensity.MINIMAL else 1,
        allow_collapsible_panels=True,
        center_modal_width_pct=0.62,
        center_modal_height_pct=0.40,
        intro_wrap_chars=38,
    )


def _tablet_landscape(density: HudDensity) -> LayoutProfile:
    return LayoutProfile(
        name=LayoutProfileName.TABLET_LANDSCAPE,
        hud_density=density,
        persistent_hud_budget=0.20,
        left_console_width_pct=0.115,
        right_gauge_width_pct=0.060,
        show_log_when_empty=density == HudDensity.FULL,
        max_log_entries=4 if density == HudDensity.FULL else 2,
        allow_collapsible_panels=True,
        center_modal_width_pct=0.52,
        center_modal_height_pct=0.42,
        intro_wrap_chars=40,
    )
