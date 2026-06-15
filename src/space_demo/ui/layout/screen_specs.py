"""Canonical widget specs for each UI screen.

These specs are the source of truth for visual QA and future screen conversion.
They intentionally use normalized coordinates so they can be checked without a
running Panda3D window and converted to aspect2d coordinates at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass

from space_demo.ui.layout.rect import RectPct


@dataclass(frozen=True)
class WidgetSpec:
    """A normalized widget rectangle assigned to a contract zone."""

    name: str
    zone: str
    rect: RectPct
    kind: str = "widget"
    text: str = ""
    interactive: bool = False


SCREEN_WIDGET_SPECS: dict[str, list[WidgetSpec]] = {
    "main_menu": [
        WidgetSpec("title_banner", "title", RectPct(0.285, 0.105, 0.46, 0.18), "image", "TO BOLDLY RESPAWN"),
        WidgetSpec("start_button", "nav", RectPct(0.250, 0.365, 0.25, 0.085), "button", "START CO-OP RETREAT", True),
        WidgetSpec("manual_button", "nav", RectPct(0.250, 0.450, 0.25, 0.085), "button", "TACTICAL MANUAL", True),
        WidgetSpec("settings_button", "nav", RectPct(0.250, 0.535, 0.25, 0.085), "button", "RETREAT CALIBRATION", True),
        WidgetSpec("quit_button", "nav", RectPct(0.250, 0.620, 0.25, 0.085), "button", "DISMISS COMMAND", True),
        WidgetSpec("briefing_card", "briefing", RectPct(0.535, 0.335, 0.30, 0.36), "panel"),
    ],
    "tactical_manual": [
        WidgetSpec("manual_title", "title", RectPct(0.31, 0.115, 0.38, 0.055), "label", "COWARD'S STRATEGIC MANUAL"),
        WidgetSpec("actors_tab", "tabs", RectPct(0.315, 0.225, 0.11, 0.065), "button", "ACTORS", True),
        WidgetSpec("systems_tab", "tabs", RectPct(0.445, 0.225, 0.11, 0.065), "button", "FLIGHT SYSTEMS", True),
        WidgetSpec("upgrades_tab", "tabs", RectPct(0.575, 0.225, 0.11, 0.065), "button", "UPGRADES", True),
        WidgetSpec("manual_card", "content", RectPct(0.245, 0.335, 0.51, 0.37), "panel"),
        WidgetSpec("return_button", "bottom_nav", RectPct(0.40, 0.795, 0.20, 0.065), "button", "RETURN TO BRIDGE", True),
    ],
    "bridge_calibration": [
        WidgetSpec("settings_title", "title", RectPct(0.34, 0.125, 0.32, 0.055), "label", "BRIDGE CALIBRATION"),
        WidgetSpec("display_tab", "tabs", RectPct(0.305, 0.255, 0.105, 0.065), "button", "DISPLAY", True),
        WidgetSpec("audio_tab", "tabs", RectPct(0.4475, 0.255, 0.105, 0.065), "button", "AUDIO", True),
        WidgetSpec("tactical_tab", "tabs", RectPct(0.590, 0.255, 0.105, 0.065), "button", "TACTICAL", True),
        WidgetSpec("row_1_label", "controls", RectPct(0.285, 0.365, 0.16, 0.045), "label"),
        WidgetSpec("row_1_control", "controls", RectPct(0.49, 0.365, 0.20, 0.065), "control", interactive=True),
        WidgetSpec("row_2_label", "controls", RectPct(0.285, 0.445, 0.16, 0.045), "label"),
        WidgetSpec("row_2_control", "controls", RectPct(0.49, 0.445, 0.20, 0.065), "control", interactive=True),
        WidgetSpec("row_3_label", "controls", RectPct(0.285, 0.525, 0.16, 0.045), "label"),
        WidgetSpec("row_3_control", "controls", RectPct(0.49, 0.525, 0.20, 0.065), "control", interactive=True),
        WidgetSpec("row_4_label", "controls", RectPct(0.285, 0.605, 0.16, 0.045), "label"),
        WidgetSpec("row_4_control", "controls", RectPct(0.49, 0.605, 0.20, 0.065), "control", interactive=True),
        WidgetSpec("apply_button", "footer_buttons", RectPct(0.275, 0.715, 0.14, 0.065), "button", "APPLY CALIBRATION", True),
        WidgetSpec("reset_button", "footer_buttons", RectPct(0.43, 0.715, 0.14, 0.065), "button", "RESET TO DEFAULTS", True),
        WidgetSpec("back_button", "footer_buttons", RectPct(0.585, 0.715, 0.14, 0.065), "button", "RETURN TO BRIDGE", True),
        WidgetSpec("settings_note", "note", RectPct(0.32, 0.825, 0.36, 0.035), "label"),
    ],
    "gameplay_hud": [
        WidgetSpec("tactical_console", "tactical_console", RectPct(0.015, 0.025, 0.17, 0.55), "panel"),
        WidgetSpec("tactical_log", "tactical_log", RectPct(0.215, 0.145, 0.14, 0.26), "panel"),
        WidgetSpec("phase_banner", "phase_banner", RectPct(0.735, 0.020, 0.22, 0.055), "label"),
        WidgetSpec("pursuit_gauge", "pursuit_gauge", RectPct(0.915, 0.325, 0.06, 0.36), "panel"),
        WidgetSpec("intro_modal", "intro_modal", RectPct(0.30, 0.245, 0.40, 0.36), "modal", interactive=True),
        WidgetSpec("center_toast", "center_toast", RectPct(0.35, 0.145, 0.30, 0.075), "toast"),
    ],
}


def get_screen_widget_specs(screen_name: str) -> list[WidgetSpec]:
    """Return canonical widget specs for a screen."""
    return SCREEN_WIDGET_SPECS[screen_name]


def widget_rects_for(screen_name: str) -> dict[str, RectPct]:
    """Return widget rectangles keyed by name."""
    return {spec.name: spec.rect for spec in get_screen_widget_specs(screen_name)}


def widget_zones_for(screen_name: str) -> dict[str, str]:
    """Return widget zone names keyed by widget name."""
    return {spec.name: spec.zone for spec in get_screen_widget_specs(screen_name)}
