"""Tactical Manual layout helper."""

from __future__ import annotations

from dataclasses import dataclass


_FLOAT_PRECISION = 12


def _clean(value: float) -> float:
    cleaned = round(float(value), _FLOAT_PRECISION)
    return 0.0 if cleaned == -0.0 else cleaned


def _pos(x_pos: float, z_pos: float) -> tuple[float, float, float]:
    return (_clean(x_pos), 0.0, _clean(z_pos))


@dataclass(frozen=True)
class ManualEntryLayout:
    """One actor-directory entry anchor."""

    icon_pos: tuple[float, float, float]
    text_pos: tuple[float, float, float]


@dataclass(frozen=True)
class TacticalManualLayout:
    """Parent-local layout data for the tactical manual."""

    panel_size: tuple[float, float]
    bracket_pos: tuple[float, float, float]
    bracket_scale: tuple[float, float, float]
    title_pos: tuple[float, float, float]
    tab_z: float
    tab_x: tuple[float, float, float]
    tab_width: float
    tab_height: float
    card_pos: tuple[float, float, float]
    card_size: tuple[float, float]
    card_title_pos: tuple[float, float, float]
    entry_icon_scale: tuple[float, float, float]
    left_entries: tuple[ManualEntryLayout, ...]
    right_entries: tuple[ManualEntryLayout, ...]
    body_text_pos: tuple[float, float, float]
    return_pos: tuple[float, float, float]
    return_width: float
    return_height: float


def build_tactical_manual_layout(ui_scale: float = 1.0) -> TacticalManualLayout:
    """Return stable tactical-manual positions inside the curated frame safe area.

    The curated frame has thick top, side, and bottom rails. Content therefore
    uses a smaller centered safe area rather than occupying the full panel bounds.
    """
    ui_scale = _clean(ui_scale)
    z_values = (0.145, 0.030, -0.085, -0.200)

    def entries(x_icon: float, x_text: float) -> tuple[ManualEntryLayout, ...]:
        return tuple(
            ManualEntryLayout(
                icon_pos=_pos(x_icon, z),
                text_pos=_pos(x_text, z + 0.016),
            )
            for z in z_values
        )

    return TacticalManualLayout(
        panel_size=(2.12, 1.54),
        bracket_pos=_pos(0.0, 0.0),
        bracket_scale=(1.02, 1.0, 0.73),
        title_pos=_pos(0.0, 0.500),
        tab_z=0.355,
        tab_x=(-0.56, 0.0, 0.56),
        tab_width=0.34,
        tab_height=0.064,
        card_pos=_pos(0.0, -0.055),
        card_size=(1.50, 0.62),
        card_title_pos=_pos(0.0, 0.220),
        entry_icon_scale=(_clean(0.055 * ui_scale), 1.0, _clean(0.055 * ui_scale)),
        left_entries=entries(-0.54, -0.46),
        right_entries=entries(0.07, 0.15),
        body_text_pos=_pos(-0.54, 0.145),
        return_pos=_pos(0.0, -0.475),
        return_width=0.40,
        return_height=0.058,
    )
