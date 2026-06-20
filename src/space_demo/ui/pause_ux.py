"""Pause overlay UX helpers."""
from __future__ import annotations


PAUSE_HELP_TEXT = "Esc/P resumes  |  R restarts  |  Q opens Bridge"


def apply_pause_overlay_copy(screens) -> bool:
    """Update pause overlay copy so Escape is clearly reversible."""
    label = getattr(screens, "paused_slogan", None)
    if label is None:
        return False
    try:
        label["text"] = f"Administrative hold active.\n{PAUSE_HELP_TEXT}"
        label["text_scale"] = 1.0
        label["text_pos"] = (0, 0)
        label["text_wordwrap"] = 42
        return True
    except Exception:
        return False
