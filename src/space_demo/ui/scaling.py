# src/space_demo/ui/scaling.py

from __future__ import annotations

BASE_TEXT_SCALES = {
    "heading": 0.060,
    "subtitle": 0.042,
    "body": 0.032,
    "small": 0.024,
    "button": 0.032,
    "hud_label": 0.026,
    "hud_value": 0.030,
    "manual_heading": 0.040,
    "manual_body": 0.030,
    "modal_title": 0.055,
    "modal_body": 0.034,
}

def text_scale(token: str, user_text_scale: float = 1.0) -> float:
    """Return a scaled value for the given text style token, multiplied by the user's text_scale option."""
    return BASE_TEXT_SCALES.get(token, BASE_TEXT_SCALES["body"]) * user_text_scale

def ui_value(value: float, user_ui_scale: float = 1.0) -> float:
    """Scale a UI layout/spacing coordinate by the user's UI scale factor."""
    return value * user_ui_scale
