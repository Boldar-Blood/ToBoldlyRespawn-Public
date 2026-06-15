"""Autofit helpers for result-screen text.

Result overlays now follow the shared DirectGUI sizing contract used by the
broader UI hardening pass: standard labels use NodePath scale for layout and keep
inner ``text_scale`` near ``1.0``.  Older result-label tests and any legacy
callers may still pass small absolute ``text_scale`` values such as ``0.026``.
This module intentionally supports both forms so result slogans remain readable
without competing with the newer generic screen autofit pass.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from space_demo.ui.components import wrap_text_lines


@dataclass(frozen=True)
class ResultTextFit:
    """Computed text and scale for a bounded result-screen label."""

    text: str
    scale: float
    line_count: int


RESULT_SLOGAN_MAX_CHARS_PER_LINE = 42
RESULT_SLOGAN_MAX_LINES = 3
RESULT_SLOGAN_MIN_ABSOLUTE_SCALE = 0.017
RESULT_SLOGAN_BASE_ABSOLUTE_SCALE = 0.026
RESULT_SLOGAN_MIN_RELATIVE_SCALE = 0.85
RESULT_SLOGAN_BASE_RELATIVE_SCALE = 1.0

# Backward-compatible names used by existing tests and callers.
RESULT_SLOGAN_MIN_SCALE = RESULT_SLOGAN_MIN_ABSOLUTE_SCALE
RESULT_SLOGAN_BASE_SCALE = RESULT_SLOGAN_BASE_ABSOLUTE_SCALE


def _coerce_text_scale(value: Any, fallback: float = RESULT_SLOGAN_BASE_SCALE) -> float:
    """Return a scalar DirectGUI text scale from float, tuple, or test double values."""
    if isinstance(value, (int, float)):
        return float(value)
    try:
        first = value[0]  # DirectGUI commonly returns two-component scale tuples.
    except Exception:
        return fallback
    if isinstance(first, (int, float)):
        return float(first)
    return fallback


def _minimum_scale_for_contract(base_scale: float, min_absolute_scale: float, min_relative_scale: float) -> float:
    """Return the minimum scale floor for old absolute or new relative scale contracts."""
    return min_absolute_scale if base_scale < 0.1 else min_relative_scale


def fit_result_slogan_text(
    text: str,
    base_scale: float | None = RESULT_SLOGAN_BASE_SCALE,
    max_chars_per_line: int = RESULT_SLOGAN_MAX_CHARS_PER_LINE,
    max_lines: int = RESULT_SLOGAN_MAX_LINES,
    min_scale: float = RESULT_SLOGAN_MIN_SCALE,
    min_relative_scale: float = RESULT_SLOGAN_MIN_RELATIVE_SCALE,
) -> ResultTextFit:
    """Wrap and scale result-screen slogan text for a fixed result panel.

    Supports both legacy absolute DirectGUI text scales (for example ``0.026``)
    and the newer relative inner-text contract (``1.0``) where the label's
    NodePath scale owns layout sizing.  Wrapping happens first; shrinking is a
    bounded fallback and never goes below the relevant readability floor.
    """
    scale_base = _coerce_text_scale(base_scale, RESULT_SLOGAN_BASE_SCALE)
    wrapped = wrap_text_lines(text, max_chars_per_line)
    lines = wrapped.splitlines() or [""]
    line_count = len(lines)
    longest_line = max((len(line) for line in lines), default=0)

    scale = scale_base
    if line_count > max_lines:
        scale *= max_lines / max(line_count, 1)
    if longest_line > max_chars_per_line:
        scale *= max_chars_per_line / max(longest_line, 1)

    minimum_scale = _minimum_scale_for_contract(scale_base, min_scale, min_relative_scale)
    return ResultTextFit(
        text=wrapped,
        scale=max(minimum_scale, min(scale_base, scale)),
        line_count=line_count,
    )


def apply_result_slogan_autofit(screens) -> None:
    """Apply safe wrapping/scaling to result-screen slogan DirectLabels."""
    for attr_name in ("gameover_slogan", "victory_slogan"):
        label = getattr(screens, attr_name, None)
        if label is None:
            continue
        try:
            original_text = str(label["text"])
            current_scale = _coerce_text_scale(label["text_scale"], RESULT_SLOGAN_BASE_SCALE)
            fitted = fit_result_slogan_text(original_text, base_scale=current_scale)
            label["text"] = fitted.text
            label["text_scale"] = fitted.scale
            label["text_pos"] = (0, -0.01 if fitted.line_count > 1 else 0)
        except Exception:
            # Result screen creation should never fail because a label did not expose
            # a mutable DirectGUI option in a test double or fallback runtime.
            continue
