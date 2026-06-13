"""Reusable UI text/button fit helpers.

These helpers intentionally use deterministic geometry estimates rather than
Panda3D font measurement so they can be tested headlessly.  They are conservative
for DirectGUI labels/buttons: reduce scale first, then increase wrapping, and
finally clamp the requested frame to its parent bounds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


FrameSize = Tuple[float, float, float, float]


@dataclass(frozen=True)
class AutoFitTextSpec:
    text: str
    max_width: float
    max_height: float
    preferred_scale: float
    min_scale: float = 0.026
    max_wordwrap: int = 72
    min_wordwrap: int = 18


@dataclass(frozen=True)
class AutoFitTextResult:
    text_scale: float
    wordwrap: int
    estimated_lines: int
    estimated_width: float
    estimated_height: float


@dataclass(frozen=True)
class AutoFitButtonResult:
    frame_size: FrameSize
    text_scale: float
    wordwrap: int
    estimated_lines: int


def fit_text(spec: AutoFitTextSpec) -> AutoFitTextResult:
    if spec.max_width <= 0 or spec.max_height <= 0:
        raise ValueError("max_width and max_height must be positive")
    if spec.min_scale <= 0 or spec.preferred_scale <= 0:
        raise ValueError("text scales must be positive")

    text = spec.text or ""
    candidates = []
    # DirectGUI text_width is roughly proportional to scale and character count.
    # The 0.62 factor is conservative for mixed uppercase/lowercase UI copy.
    steps = max(1, int((spec.preferred_scale - spec.min_scale) / 0.002) + 2)
    for scale_step in range(steps):
        scale = max(spec.min_scale, spec.preferred_scale - scale_step * 0.002)
        chars_per_line = max(spec.min_wordwrap, int(spec.max_width / max(scale * 0.62, 0.0001)))
        wordwrap = min(spec.max_wordwrap, max(spec.min_wordwrap, chars_per_line))
        lines = _estimate_wrapped_lines(text, wordwrap)
        estimated_width = min(len(text), wordwrap) * scale * 0.62
        estimated_height = max(1, lines) * scale * 1.28
        candidate = AutoFitTextResult(
            text_scale=scale,
            wordwrap=wordwrap,
            estimated_lines=lines,
            estimated_width=estimated_width,
            estimated_height=estimated_height,
        )
        candidates.append(candidate)
        if estimated_width <= spec.max_width and estimated_height <= spec.max_height:
            return candidate

    # Return the least-overflowing candidate when no exact fit exists.  Callers
    # can still keep the frame clamped and the text at the minimum readable size.
    return min(candidates, key=lambda item: _overflow_score(item, spec.max_width, spec.max_height))


def fit_button_text(
    text: str,
    parent_frame: FrameSize,
    desired_center_z: float,
    desired_width: float,
    desired_height: float,
    preferred_scale: float = 0.036,
    min_scale: float = 0.024,
    padding_x: float = 0.09,
    padding_y: float = 0.018,
) -> AutoFitButtonResult:
    left, right, bottom, top = parent_frame
    parent_width = right - left
    parent_height = top - bottom
    width = min(max(0.12, desired_width), max(0.12, parent_width - 0.08))
    height = min(max(0.08, desired_height), max(0.08, parent_height - 0.08))

    half_height = height / 2.0
    if desired_center_z - half_height < bottom:
        desired_center_z = bottom + half_height
    if desired_center_z + half_height > top:
        desired_center_z = top - half_height

    text_result = fit_text(
        AutoFitTextSpec(
            text=text,
            max_width=max(0.04, width - padding_x),
            max_height=max(0.03, height - padding_y),
            preferred_scale=preferred_scale,
            min_scale=min_scale,
            max_wordwrap=64,
            min_wordwrap=12,
        )
    )
    return AutoFitButtonResult(
        frame_size=(-width / 2.0, width / 2.0, -height / 2.0, height / 2.0),
        text_scale=text_result.text_scale,
        wordwrap=text_result.wordwrap,
        estimated_lines=text_result.estimated_lines,
    )


def clamp_frame_inside(parent_frame: FrameSize, center_x: float, center_z: float, frame_size: FrameSize) -> tuple[float, float, float]:
    left, right, bottom, top = parent_frame
    f_left, f_right, f_bottom, f_top = frame_size
    if center_x + f_left < left:
        center_x = left - f_left
    if center_x + f_right > right:
        center_x = right - f_right
    if center_z + f_bottom < bottom:
        center_z = bottom - f_bottom
    if center_z + f_top > top:
        center_z = top - f_top
    return center_x, 0.0, center_z


def _overflow_score(result: AutoFitTextResult, max_width: float, max_height: float) -> float:
    width_over = max(0.0, result.estimated_width - max_width)
    height_over = max(0.0, result.estimated_height - max_height)
    return (width_over * 10.0) + (height_over * 20.0) + result.text_scale


def _estimate_wrapped_lines(text: str, wordwrap: int) -> int:
    if not text:
        return 1
    lines = 1
    current = 0
    for raw_word in text.split():
        word_len = len(raw_word)
        if current == 0:
            current = word_len
        elif current + 1 + word_len <= wordwrap:
            current += 1 + word_len
        else:
            lines += 1
            current = word_len
        while current > wordwrap:
            lines += 1
            current -= wordwrap
    return lines
