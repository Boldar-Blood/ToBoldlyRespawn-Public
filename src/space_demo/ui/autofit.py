"""Reusable UI text/button fit helpers.

These helpers intentionally use deterministic geometry estimates rather than
Panda3D font measurement so they can be tested headlessly. They are conservative
for DirectGUI labels/buttons: reduce scale first, then increase wrapping, and
finally clamp the requested frame to its parent bounds.

Runtime screens should route labels and buttons through shared factories and then
run the screen-level pass in this module after construction. Future screens should
use these helpers directly when creating or updating text dynamically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Tuple

from space_demo.ui.components import wrap_text_lines
from space_demo.ui.pause_ux import apply_pause_overlay_copy
from space_demo.ui.result_text_fit import apply_result_slogan_autofit


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


@dataclass(frozen=True)
class TextFitPolicy:
    """Shared text fitting policy for DirectGUI widgets."""

    max_chars_per_line: int = 44
    max_lines: int = 4
    min_scale: float = 0.014           # Minimum absolute scale (old contract)
    min_relative_scale: float = 0.85   # Minimum relative scale (new contract, relative to 1.0)
    line_offset: float = -0.01


POLICIES = {
    "pause_help": TextFitPolicy(max_chars_per_line=42, max_lines=2, min_relative_scale=0.90),
    "result_slogan": TextFitPolicy(max_chars_per_line=35, max_lines=3, min_relative_scale=0.85),
    "modal_body": TextFitPolicy(max_chars_per_line=45, max_lines=6, min_relative_scale=0.85),
    "settings_row": TextFitPolicy(max_chars_per_line=32, max_lines=1, min_relative_scale=0.95),
    "fleet_details": TextFitPolicy(max_chars_per_line=40, max_lines=4, min_relative_scale=0.85),
    "tactical_log": TextFitPolicy(max_chars_per_line=50, max_lines=1, min_relative_scale=0.90),
    "hud_numeric": TextFitPolicy(max_chars_per_line=10, max_lines=1, min_relative_scale=0.90),
    "notification": TextFitPolicy(max_chars_per_line=40, max_lines=2, min_relative_scale=0.85),
}


@dataclass(frozen=True)
class FittedDirectText:
    """Result of wrapping/scaling a DirectGUI text option."""

    text: str
    scale: float | None
    line_count: int
    wrapped: bool


DEFAULT_TEXT_FIT_POLICY = TextFitPolicy()


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

    # Return the least-overflowing candidate when no exact fit exists. Callers
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


def fit_direct_text_to_policy(
    text: str,
    base_scale: float | None,
    policy: TextFitPolicy = DEFAULT_TEXT_FIT_POLICY,
) -> FittedDirectText:
    """Wrap and conservatively scale text for a bounded DirectGUI area."""
    wrapped_text = wrap_text_lines(text, policy.max_chars_per_line)
    lines = wrapped_text.splitlines() or [""]
    line_count = len(lines)
    longest_line = max((len(line) for line in lines), default=0)
    scale = base_scale

    if scale is not None:
        is_absolute = scale < 0.1
        mult = 1.0
        if line_count > policy.max_lines:
            mult *= policy.max_lines / max(line_count, 1)
        if longest_line > policy.max_chars_per_line:
            mult *= policy.max_chars_per_line / max(longest_line, 1)
        
        scale *= mult
        if is_absolute:
            scale = max(policy.min_scale, scale)
        else:
            scale = max(policy.min_relative_scale, scale)

    return FittedDirectText(
        text=wrapped_text,
        scale=scale,
        line_count=line_count,
        wrapped=wrapped_text != text,
    )


def fit_directgui_widget_text(widget: Any, policy: TextFitPolicy = DEFAULT_TEXT_FIT_POLICY) -> bool:
    """Apply shared wrapping/scaling policy to a DirectGUI-like widget.

    This accepts both real DirectGUI widgets and dict-like test doubles. It skips
    non-string or stateful tuple/list text to avoid corrupting multi-state button
    labels. The function is safe to call repeatedly after dynamic text updates.
    """
    text = _get_widget_option(widget, "text")
    if not isinstance(text, str) or not text:
        return False

    scale = _coerce_float(_get_widget_option(widget, "text_scale"))
    fitted = fit_direct_text_to_policy(text, scale, policy)
    changed = False

    if fitted.text != text:
        changed = _set_widget_option(widget, "text", fitted.text) or changed
        if fitted.line_count > 1:
            changed = _set_widget_option(widget, "text_pos", (0, policy.line_offset)) or changed

    if fitted.scale is not None and scale is not None and fitted.scale < scale:
        changed = _set_widget_option(widget, "text_scale", fitted.scale) or changed

    # DirectGUI supports text_wordwrap on labels/buttons; keep this advisory so
    # test doubles or widgets that do not expose the option still work.
    _set_widget_option(widget, "text_wordwrap", policy.max_chars_per_line)
    return changed


def fit_pause_help_text(widget: Any) -> bool:
    return fit_directgui_widget_text(widget, POLICIES["pause_help"])


def fit_result_slogan(widget: Any) -> bool:
    return fit_directgui_widget_text(widget, POLICIES["result_slogan"])


def fit_modal_body(widget: Any) -> bool:
    return fit_directgui_widget_text(widget, POLICIES["modal_body"])


def fit_settings_row(widget: Any) -> bool:
    return fit_directgui_widget_text(widget, POLICIES["settings_row"])


def fit_fleet_details(widget: Any) -> bool:
    return fit_directgui_widget_text(widget, POLICIES["fleet_details"])


def fit_tactical_log(widget: Any) -> bool:
    return fit_directgui_widget_text(widget, POLICIES["tactical_log"])


def fit_hud_numeric(widget: Any) -> bool:
    return fit_directgui_widget_text(widget, POLICIES["hud_numeric"])


def fit_notification(widget: Any) -> bool:
    return fit_directgui_widget_text(widget, POLICIES["notification"])


def iter_screen_widgets(screen_owner: Any) -> Iterable[Any]:
    """Yield DirectGUI-like widgets attached as attributes on a screen controller."""
    for value in vars(screen_owner).values():
        if hasattr(value, "__getitem__") and hasattr(value, "__setitem__"):
            yield value


def apply_screen_widget_autofit(screen_owner: Any, policy: TextFitPolicy = DEFAULT_TEXT_FIT_POLICY) -> None:
    """Apply shared text fitting to known screen-controller widgets.

    Result slogans get a specialized panel-aware policy first. Pause copy is
    normalized before the generic pass catches other label/button attributes on
    existing and future screens.
    """
    apply_result_slogan_autofit(screen_owner)
    apply_pause_overlay_copy(screen_owner)
    
    for name, widget in vars(screen_owner).items():
        if not (hasattr(widget, "__getitem__") and hasattr(widget, "__setitem__")):
            continue
            
        active_policy = policy
        name_lower = name.lower()
        if "pause" in name_lower and ("slogan" in name_lower or "help" in name_lower):
            active_policy = POLICIES["pause_help"]
        elif "slogan" in name_lower:
            active_policy = POLICIES["result_slogan"]
        elif "modal" in name_lower or "dialog" in name_lower:
            active_policy = POLICIES["modal_body"]
        elif "row" in name_lower or "setting" in name_lower:
            active_policy = POLICIES["settings_row"]
        elif "fleet" in name_lower or "ship" in name_lower:
            active_policy = POLICIES["fleet_details"]
        elif "log" in name_lower:
            active_policy = POLICIES["tactical_log"]
        elif "hud" in name_lower or "num" in name_lower:
            active_policy = POLICIES["hud_numeric"]
        elif "notify" in name_lower or "banner" in name_lower:
            active_policy = POLICIES["notification"]
            
        fit_directgui_widget_text(widget, active_policy)


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


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, (tuple, list)) and value and isinstance(value[0], (int, float)):
        return float(value[0])
    return None


def _get_widget_option(widget: Any, key: str) -> Any:
    try:
        return widget[key]
    except Exception:
        return None


def _set_widget_option(widget: Any, key: str, value: Any) -> bool:
    try:
        widget[key] = value
        return True
    except Exception:
        return False
