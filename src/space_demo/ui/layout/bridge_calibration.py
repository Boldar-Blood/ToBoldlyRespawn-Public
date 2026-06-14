"""Bridge Calibration layout helper."""

from __future__ import annotations

from dataclasses import dataclass


_FLOAT_PRECISION = 12
_BUTTON_FRAME_SCALE_CAP = 1.15
_BUTTON_HEIGHT_SCALE_CAP = 1.20
_AUDIO_MUTE_X = 0.62
_SLIDER_THUMB_HALF_WIDTH = 0.020
_SLIDER_THUMB_HALF_HEIGHT = 0.038
_BOUNDS_EPSILON = 1e-9
_DYNAMIC_BUTTON_TEXT_SCALE = 0.0165
_DYNAMIC_BUTTON_HORIZONTAL_PADDING = 0.035
_TEXT_WIDTH_FACTOR = 0.80


def _clean(value: float) -> float:
    cleaned = round(float(value), _FLOAT_PRECISION)
    return 0.0 if cleaned == -0.0 else cleaned


def _pos(x_pos: float, z_pos: float) -> tuple[float, float, float]:
    return (_clean(x_pos), 0.0, _clean(z_pos))


@dataclass(frozen=True)
class ControlRowLayout:
    """Parent-local positions for a settings row."""

    label_pos: tuple[float, float, float]
    control_pos: tuple[float, float, float]
    slider_width: float = 0.38
    toggle_width: float = 0.36


@dataclass(frozen=True)
class BridgeCalibrationLayout:
    """Parent-local layout data for the Bridge Calibration screen."""

    title_pos: tuple[float, float, float]
    tab_z: float
    tab_x: tuple[float, float, float]
    tab_width: float
    tab_height: float
    tab_frame_size: tuple[float, float, float, float]
    tab_frame_pos: tuple[float, float, float]
    footer_z: float
    footer_x: tuple[float, float, float]
    footer_width: float
    footer_height: float
    note_pos: tuple[float, float, float]
    display_rows: tuple[ControlRowLayout, ...]
    audio_rows: tuple[ControlRowLayout, ...]
    gameplay_rows: tuple[ControlRowLayout, ...]
    paired_toggle_x: tuple[float, float]
    paired_toggle_z: float
    paired_toggle_width: float


@dataclass(frozen=True)
class LayoutBounds:
    """2D control bounds in parent-local x/z coordinates."""

    name: str
    left: float
    right: float
    bottom: float
    top: float

    def overlaps(self, other: "LayoutBounds", padding: float = 0.0) -> bool:
        return not (
            self.right + padding <= other.left + _BOUNDS_EPSILON
            or other.right + padding <= self.left + _BOUNDS_EPSILON
            or self.top + padding <= other.bottom + _BOUNDS_EPSILON
            or other.top + padding <= self.bottom + _BOUNDS_EPSILON
        )

    def inside(self, parent: "LayoutBounds") -> bool:
        return (
            self.left >= parent.left - _BOUNDS_EPSILON
            and self.right <= parent.right + _BOUNDS_EPSILON
            and self.bottom >= parent.bottom - _BOUNDS_EPSILON
            and self.top <= parent.top + _BOUNDS_EPSILON
        )

    @property
    def width(self) -> float:
        return _clean(self.right - self.left)


def build_bridge_calibration_layout(ui_scale: float = 1.0) -> BridgeCalibrationLayout:
    """Return deterministic settings-screen positions inside the frame safe area.

    UI scale affects slider geometry and reusable button geometry, so horizontal
    lanes must leave clear gaps at the supported 150% scale. Labels and controls
    are separated enough for long dynamic text such as the current resolution
    string. Use ``validate_bridge_calibration_layout`` in regression tests.
    """
    ui_scale = _clean(ui_scale)
    display_z = (0.185, 0.075, -0.035, -0.145, -0.245)
    audio_z = (0.170, 0.020, -0.130)
    gameplay_z = (0.180, 0.060, -0.060, -0.170)

    def row(
        z_value: float,
        slider_width: float = 0.34,
        toggle_width: float = 0.44,
        control_x: float = 0.24,
    ) -> ControlRowLayout:
        return ControlRowLayout(
            label_pos=_pos(-0.52, z_value),
            control_pos=_pos(control_x, z_value),
            slider_width=_clean(slider_width * ui_scale),
            toggle_width=_clean(toggle_width),
        )

    return BridgeCalibrationLayout(
        title_pos=_pos(0.0, 0.500),
        tab_z=0.345,
        tab_x=(-0.40, 0.0, 0.40),
        tab_width=0.29,
        tab_height=0.054,
        tab_frame_size=(-0.66, 0.66, -0.325, 0.250),
        tab_frame_pos=_pos(0.0, -0.010),
        footer_z=-0.535,
        footer_x=(-0.50, 0.0, 0.50),
        footer_width=0.30,
        footer_height=0.056,
        note_pos=_pos(0.0, -0.620),
        display_rows=tuple(row(z) for z in display_z),
        audio_rows=(
            row(audio_z[0], slider_width=0.20, toggle_width=0.38, control_x=0.12),
            row(audio_z[1], slider_width=0.20, toggle_width=0.38, control_x=0.12),
            row(audio_z[2], slider_width=0.20, toggle_width=0.38, control_x=0.12),
        ),
        gameplay_rows=tuple(row(z) for z in gameplay_z),
        paired_toggle_x=(-0.36, 0.36),
        paired_toggle_z=-0.350,
        paired_toggle_width=0.44,
    )


def validate_bridge_calibration_layout(ui_scale: float = 1.0, text_scale: float | None = None) -> list[str]:
    """Return layout warnings for settings controls at a supported UI/text scale."""
    layout = build_bridge_calibration_layout(ui_scale)
    text_scale = _clean(ui_scale if text_scale is None else text_scale)
    warnings: list[str] = []
    visible_bounds = _screen_safe_bounds()
    tab_frame_bounds = _bounds_from_frame("settings_tab_frame", layout.tab_frame_size, layout.tab_frame_pos)

    tab_buttons = [
        _button_bounds(f"tab_{index}", x_pos, layout.tab_z, layout.tab_width, layout.tab_height, ui_scale)
        for index, x_pos in enumerate(layout.tab_x)
    ]
    footer_buttons = [
        _button_bounds(f"footer_{index}", x_pos, layout.footer_z, layout.footer_width, layout.footer_height, ui_scale)
        for index, x_pos in enumerate(layout.footer_x)
    ]
    paired_toggles = [
        _button_bounds(
            f"display_paired_toggle_{index}",
            x_pos,
            layout.paired_toggle_z,
            layout.paired_toggle_width,
            0.058,
            ui_scale,
        )
        for index, x_pos in enumerate(layout.paired_toggle_x)
    ]
    dynamic_toggle_groups = [
        (paired_toggles[0], ("HIGH CONTRAST: OFF", "HIGH CONTRAST: ON")),
        (paired_toggles[1], ("REDUCE MOTION: OFF", "REDUCE MOTION: ON")),
    ]

    display_dynamic_toggles = [
        (
            _button_bounds(
                "display_fullscreen",
                layout.display_rows[1].control_pos[0],
                layout.display_rows[1].control_pos[2],
                layout.display_rows[1].toggle_width,
                0.058,
                ui_scale,
            ),
            ("FULLSCREEN: OFF", "FULLSCREEN: ON"),
        ),
        (
            _button_bounds(
                "display_vfx_quality",
                layout.display_rows[2].control_pos[0],
                layout.display_rows[2].control_pos[2],
                layout.display_rows[2].toggle_width,
                0.058,
                ui_scale,
            ),
            ("VFX QUALITY: ACTIVE", "VFX QUALITY: INACTIVE"),
        ),
    ]
    gameplay_dynamic_toggles = [
        (
            _button_bounds(
                "gameplay_coop",
                layout.gameplay_rows[2].control_pos[0],
                layout.gameplay_rows[2].control_pos[2],
                layout.gameplay_rows[2].toggle_width,
                0.058,
                ui_scale,
            ),
            ("CO-OP: ACTIVE", "CO-OP: INACTIVE"),
        ),
        (
            _button_bounds(
                "gameplay_intro",
                layout.gameplay_rows[3].control_pos[0],
                layout.gameplay_rows[3].control_pos[2],
                layout.gameplay_rows[3].toggle_width,
                0.058,
                ui_scale,
            ),
            ("INTRO BRIEFING: SHOW", "INTRO BRIEFING: HIDE"),
        ),
    ]
    dynamic_toggle_groups.extend(display_dynamic_toggles)
    dynamic_toggle_groups.extend(gameplay_dynamic_toggles)

    for control in (*tab_buttons, *footer_buttons, *paired_toggles):
        _require_within(control, visible_bounds, warnings)
    for control, _texts in (*display_dynamic_toggles, *gameplay_dynamic_toggles):
        _require_within(control, tab_frame_bounds, warnings)

    _require_non_overlapping(tab_buttons, warnings, padding=0.015)
    _require_non_overlapping(footer_buttons, warnings, padding=0.020)
    _require_non_overlapping(paired_toggles, warnings, padding=0.020)

    for index, (row_layout, label) in enumerate(zip(layout.audio_rows, ("MASTER", "MUSIC", "SFX"))):
        slider = _slider_bounds(f"audio_slider_{index}", row_layout.control_pos, row_layout.slider_width)
        toggle = _button_bounds(
            f"audio_mute_{index}",
            _AUDIO_MUTE_X,
            row_layout.control_pos[2],
            row_layout.toggle_width,
            0.058,
            ui_scale,
        )
        dynamic_toggle_groups.append((toggle, (f"MUTE {label}: OFF", f"MUTE {label}: ON")))
        _require_within(slider, tab_frame_bounds, warnings)
        _require_within(toggle, visible_bounds, warnings)
        if slider.overlaps(toggle, padding=0.025):
            warnings.append(f"{slider.name} overlaps or touches {toggle.name} at UI scale {ui_scale}.")

    for control, texts in dynamic_toggle_groups:
        _require_dynamic_text_fits(control, texts, ui_scale, text_scale, warnings)

    return warnings


def _screen_safe_bounds() -> LayoutBounds:
    return LayoutBounds("screen_safe", -1.15, 1.15, -0.80, 0.80)


def _bounds_from_frame(name: str, frame_size: tuple[float, float, float, float], pos: tuple[float, float, float]) -> LayoutBounds:
    left, right, bottom, top = frame_size
    x_pos, _, z_pos = pos
    return LayoutBounds(
        name,
        _clean(x_pos + left),
        _clean(x_pos + right),
        _clean(z_pos + bottom),
        _clean(z_pos + top),
    )


def _button_bounds(name: str, center_x: float, center_z: float, width: float, height: float, ui_scale: float) -> LayoutBounds:
    width_scale = min(max(0.50, ui_scale), _BUTTON_FRAME_SCALE_CAP)
    height_scale = min(max(0.50, ui_scale), _BUTTON_HEIGHT_SCALE_CAP)
    half_width = width * width_scale / 2.0
    half_height = height * height_scale / 2.0
    return LayoutBounds(
        name,
        _clean(center_x - half_width),
        _clean(center_x + half_width),
        _clean(center_z - half_height),
        _clean(center_z + half_height),
    )


def _slider_bounds(name: str, pos: tuple[float, float, float], width: float) -> LayoutBounds:
    center_x, _, center_z = pos
    half_width = width / 2.0 + _SLIDER_THUMB_HALF_WIDTH
    half_height = _SLIDER_THUMB_HALF_HEIGHT
    return LayoutBounds(
        name,
        _clean(center_x - half_width),
        _clean(center_x + half_width),
        _clean(center_z - half_height),
        _clean(center_z + half_height),
    )


def _require_dynamic_text_fits(
    control: LayoutBounds,
    texts: tuple[str, ...],
    ui_scale: float,
    text_scale: float,
    warnings: list[str],
) -> None:
    width_scale = min(max(0.50, ui_scale), _BUTTON_FRAME_SCALE_CAP)
    horizontal_padding = _DYNAMIC_BUTTON_HORIZONTAL_PADDING * width_scale
    available_width = max(0.01, control.width - 2.0 * horizontal_padding)
    rendered_text_scale = _DYNAMIC_BUTTON_TEXT_SCALE * text_scale

    for text in texts:
        estimated_width = len(text) * rendered_text_scale * _TEXT_WIDTH_FACTOR
        if estimated_width > available_width + _BOUNDS_EPSILON:
            warnings.append(
                f"{control.name} text {text!r} may overflow at UI scale {ui_scale} "
                f"and text scale {text_scale}: estimated width {estimated_width:.3f} "
                f"exceeds available width {available_width:.3f}."
            )


def _require_within(control: LayoutBounds, parent: LayoutBounds, warnings: list[str]) -> None:
    if not control.inside(parent):
        warnings.append(f"{control.name} is outside {parent.name}: {control} not within {parent}.")


def _require_non_overlapping(controls: list[LayoutBounds], warnings: list[str], padding: float = 0.0) -> None:
    for index, control in enumerate(controls):
        for other in controls[index + 1:]:
            if control.overlaps(other, padding=padding):
                warnings.append(f"{control.name} overlaps or touches {other.name}.")
