"""Autofit helpers for result-screen text."""
from __future__ import annotations

from dataclasses import dataclass

from space_demo.ui.components import wrap_text_lines


@dataclass(frozen=True)
class ResultTextFit:
    """Computed text and scale for a bounded result-screen label."""

    text: str
    scale: float
    line_count: int


RESULT_SLOGAN_MAX_CHARS_PER_LINE = 42
RESULT_SLOGAN_MAX_LINES = 3
RESULT_SLOGAN_MIN_SCALE = 0.017
RESULT_SLOGAN_BASE_SCALE = 0.026


def fit_result_slogan_text(
    text: str,
    base_scale: float = RESULT_SLOGAN_BASE_SCALE,
    max_chars_per_line: int = RESULT_SLOGAN_MAX_CHARS_PER_LINE,
    max_lines: int = RESULT_SLOGAN_MAX_LINES,
    min_scale: float = RESULT_SLOGAN_MIN_SCALE,
) -> ResultTextFit:
    """Wrap and scale result-screen slogan text for a fixed result panel.

    The result overlays use fixed panel geometry, so a slogan must fit by wrapping
    and only then scaling down when the resulting line count or longest line would
    still be too large. This intentionally mirrors the button autofit policy: keep
    content readable but never let it spill out of its frame.
    """
    wrapped = wrap_text_lines(text, max_chars_per_line)
    lines = wrapped.splitlines() or [""]
    line_count = len(lines)
    longest_line = max((len(line) for line in lines), default=0)

    scale = base_scale
    if line_count > max_lines:
        scale *= max_lines / max(line_count, 1)
    if longest_line > max_chars_per_line:
        scale *= max_chars_per_line / max(longest_line, 1)

    return ResultTextFit(
        text=wrapped,
        scale=max(min_scale, min(base_scale, scale)),
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
            current_scale = float(label["text_scale"])
            fitted = fit_result_slogan_text(original_text, base_scale=current_scale)
            label["text"] = fitted.text
            label["text_scale"] = fitted.scale
            label["text_pos"] = (0, -0.01 if fitted.line_count > 1 else 0)
        except Exception:
            # Result screen creation should never fail because a label did not expose
            # a mutable DirectGUI option in a test double or fallback runtime.
            continue
