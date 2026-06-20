"""Conservative text fitting estimators for DirectGUI labels/buttons.

The estimators intentionally overestimate width so tests catch risky labels
before visual smoke screenshots show real overlap.
"""

from __future__ import annotations


def estimate_text_width_px(text: str, font_px: float, mono_factor: float = 0.62) -> float:
    """Estimate rendered text width in pixels for a sans/mono-like UI font."""
    if not text:
        return 0.0
    longest = max(text.splitlines() or [text], key=len)
    return len(longest) * font_px * mono_factor


def estimate_line_count(text: str) -> int:
    """Return at least one line for a text block."""
    return max(1, len(text.splitlines()))


def text_fits_box(text: str, width_px: float, height_px: float, font_px: float) -> bool:
    """Return True when text is predicted to fit inside a box."""
    line_height = font_px * 1.25
    return estimate_text_width_px(text, font_px) <= width_px and estimate_line_count(text) * line_height <= height_px


def shrink_font_to_fit(text: str, width_px: float, height_px: float, start_px: float, min_px: float = 10.0) -> float:
    """Return the largest font size predicted to fit the given box."""
    size = start_px
    while size > min_px and not text_fits_box(text, width_px, height_px, size):
        size -= 1.0
    return max(min_px, size)
