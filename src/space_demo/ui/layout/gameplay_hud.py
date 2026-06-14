"""Gameplay HUD layout helper."""

from __future__ import annotations

from dataclasses import dataclass

from space_demo.ui.layout.profiles import HudDensity, LayoutProfile, choose_layout_profile
from space_demo.ui.layout.viewport import ViewportContext


_FLOAT_PRECISION = 12


def _clean(value: float) -> float:
    cleaned = round(float(value), _FLOAT_PRECISION)
    return 0.0 if cleaned == -0.0 else cleaned


def _pos(x_pos: float, z_pos: float) -> tuple[float, float, float]:
    return (_clean(x_pos), 0.0, _clean(z_pos))


@dataclass(frozen=True)
class GameplayHudLayout:
    """Runtime HUD positions in their parent anchor spaces."""

    profile: LayoutProfile
    intro_root_pos: tuple[float, float, float]
    intro_panel_size: tuple[float, float]
    intro_title_pos: tuple[float, float, float]
    intro_text_pos: tuple[float, float, float]
    intro_button_pos: tuple[float, float, float]
    intro_close_pos: tuple[float, float, float]
    intro_button_width: float
    intro_button_height: float
    intro_wrap_chars: int
    log_pos: tuple[float, float, float]
    log_size: tuple[float, float]
    log_title_pos: tuple[float, float, float]
    log_divider_z: float
    log_entry_top_z: float
    log_entry_spacing_z: float
    show_log_when_empty: bool
    max_log_entries: int


def build_gameplay_hud_layout(
    ui_scale: float = 1.0,
    viewport: ViewportContext | None = None,
    preferred_density: HudDensity | str | None = None,
) -> GameplayHudLayout:
    """Return stable gameplay HUD positions and panel sizes."""
    ui_scale = _clean(ui_scale)
    active_viewport = viewport or ViewportContext.from_size(1920, 1080)
    profile = choose_layout_profile(active_viewport, preferred_density)
    modal_w = _clean(min(0.94, profile.center_modal_width_pct * 2.0) * ui_scale)
    modal_h = _clean(min(0.56, profile.center_modal_height_pct * 1.25) * ui_scale)
    log_w = _clean(min(0.24, profile.left_console_width_pct * 1.55) * ui_scale)
    log_h = _clean((0.64 if profile.show_log_when_empty else 0.38) * ui_scale)
    log_x = _clean((0.18 + profile.left_console_width_pct * 2.6) * ui_scale)
    return GameplayHudLayout(
        profile=profile,
        intro_root_pos=_pos(0.0, 0.02 * ui_scale),
        intro_panel_size=(modal_w, modal_h),
        intro_title_pos=_pos(0.0, (modal_h / 2.0) - (0.09 * ui_scale)),
        intro_text_pos=_pos(0.0, 0.010 * ui_scale),
        intro_button_pos=_pos(0.0, (-modal_h / 2.0) + (0.08 * ui_scale)),
        intro_close_pos=_pos((modal_w / 2.0) - (0.055 * ui_scale), (modal_h / 2.0) - (0.060 * ui_scale)),
        intro_button_width=0.58,
        intro_button_height=0.065,
        intro_wrap_chars=profile.intro_wrap_chars,
        log_pos=_pos(log_x, -0.24 * ui_scale),
        log_size=(log_w, log_h),
        log_title_pos=_pos(0.0, (log_h / 2.0) - (0.060 * ui_scale)),
        log_divider_z=_clean((log_h / 2.0) - (0.100 * ui_scale)),
        log_entry_top_z=_clean((log_h / 2.0) - (0.165 * ui_scale)),
        log_entry_spacing_z=_clean(0.082 * ui_scale),
        show_log_when_empty=profile.show_log_when_empty,
        max_log_entries=profile.max_log_entries,
    )
