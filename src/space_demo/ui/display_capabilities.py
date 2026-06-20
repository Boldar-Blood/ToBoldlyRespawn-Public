"""Display capability helpers for resolution settings.

This module keeps platform/display probing out of menu-screen construction so
resolution policy stays reusable and testable. Panda3D exposes display modes on
some platforms through GraphicsPipe display information; when that data is not
available, helpers fall back conservatively to the current/native window size.
"""

from __future__ import annotations

from typing import Any, Iterable

from space_demo.ui.theme import normalize_resolution

Resolution = tuple[int, int]
MIN_RESOLUTION: Resolution = (640, 360)
MAX_VISIBLE_RESOLUTION_CHOICES = 12
MIN_SLIDER_RESOLUTION_CHOICES = 2
CONSTRUCTIBLE_FALLBACK_RESOLUTIONS: tuple[Resolution, ...] = ((960, 540), (1280, 720))


def _landscape_resolution(width: int, height: int) -> Resolution:
    """Return a landscape-oriented resolution tuple for this horizontal game."""
    return (max(width, height), min(width, height))


def _is_reasonable_game_resolution(resolution: Resolution) -> bool:
    """Filter out unusable display modes while allowing widescreen variants."""
    width, height = resolution
    if width < MIN_RESOLUTION[0] or height < MIN_RESOLUTION[1]:
        return False
    aspect = width / max(1, height)
    return 1.25 <= aspect <= 3.00


def _add_resolution(target: set[Resolution], width: Any, height: Any) -> None:
    """Normalize and add a positive display size when it is usable for gameplay."""
    try:
        resolution = _landscape_resolution(int(width), int(height))
    except (TypeError, ValueError):
        return
    if _is_reasonable_game_resolution(resolution):
        target.add(resolution)


def _window_resolution(app: Any) -> Resolution | None:
    """Return the current Panda3D window size when a real window exists."""
    win = getattr(app, "win", None)
    if win is None:
        return None
    try:
        props = win.getProperties()
        width = int(props.getXSize())
        height = int(props.getYSize())
        if width > 0 and height > 0:
            return _landscape_resolution(width, height)
    except Exception:
        return None
    return None


def _desktop_resolution(app: Any) -> Resolution | None:
    """Return the best-known native desktop/display size."""
    for source_name in ("pipe", "win"):
        source = getattr(app, source_name, None)
        if source is None:
            continue
        try:
            if hasattr(source, "getDisplayWidth") and hasattr(source, "getDisplayHeight"):
                width = int(source.getDisplayWidth())
                height = int(source.getDisplayHeight())
                if width > 0 and height > 0:
                    return _landscape_resolution(width, height)
        except Exception:
            pass
        try:
            props = source.getProperties()
            width = int(props.getXSize())
            height = int(props.getYSize())
            if width > 0 and height > 0:
                return _landscape_resolution(width, height)
        except Exception:
            pass
    return None


def _query_display_modes(app: Any) -> set[Resolution]:
    """Return exact OS/display modes exposed by Panda3D, when available."""
    modes: set[Resolution] = set()
    pipe = getattr(app, "pipe", None)
    if pipe is None or not hasattr(pipe, "getDisplayInformation"):
        return modes

    try:
        info = pipe.getDisplayInformation()
    except Exception:
        return modes

    try:
        total = int(info.getTotalDisplayModes())
    except Exception:
        total = 0

    for index in range(max(0, total)):
        try:
            width = info.getDisplayModeWidth(index)
            height = info.getDisplayModeHeight(index)
        except Exception:
            continue
        _add_resolution(modes, width, height)
    return modes


def _fits_display(resolution: Resolution, display_size: Resolution | None) -> bool:
    """Return whether a resolution fits inside a known display size."""
    if display_size is None:
        return True
    width, height = resolution
    max_w, max_h = display_size
    return width <= max_w and height <= max_h


def _sort_resolutions(resolutions: Iterable[Resolution]) -> list[Resolution]:
    """Sort resolution choices from lowest to highest area."""
    return sorted(set(resolutions), key=lambda res: (res[0] * res[1], res[0], res[1]))


def _trim_resolution_choices(resolutions: list[Resolution], current: Resolution) -> list[Resolution]:
    """Keep settings compact without trimming out the current saved resolution."""
    if len(resolutions) <= MAX_VISIBLE_RESOLUTION_CHOICES:
        return resolutions
    kept = resolutions[-MAX_VISIBLE_RESOLUTION_CHOICES:]
    if current not in kept and current in resolutions:
        kept = _sort_resolutions([current, *kept[1:]])
    return kept


def _ensure_slider_safe_choices(
    choices: list[Resolution],
    current: Resolution,
    common: set[Resolution],
    desktop_size: Resolution | None,
) -> list[Resolution]:
    """Ensure DirectSlider never receives a single-point resolution range.

    Some CI/headless displays expose exactly one valid display mode. Panda3D's
    DirectSlider asserts when constructed with range ``(0, 0)``. Preserve the
    detected and saved choices, then add the best available resolution option.
    """
    expanded: list[Resolution] = _sort_resolutions([*choices, current])
    if len(expanded) >= MIN_SLIDER_RESOLUTION_CHOICES:
        return expanded

    fallback_candidates = _sort_resolutions(set(expanded) | common)

    for candidate in fallback_candidates:
        if candidate in expanded:
            continue
        if candidate == current or _fits_display(candidate, desktop_size):
            expanded.append(candidate)
        if len(expanded) >= MIN_SLIDER_RESOLUTION_CHOICES:
            break

    if len(expanded) < MIN_SLIDER_RESOLUTION_CHOICES:
        for candidate in _sort_resolutions(tuple(common) + CONSTRUCTIBLE_FALLBACK_RESOLUTIONS):
            if candidate not in expanded and _is_reasonable_game_resolution(candidate):
                expanded.append(candidate)
            if len(expanded) >= MIN_SLIDER_RESOLUTION_CHOICES:
                break

    if len(expanded) < MIN_SLIDER_RESOLUTION_CHOICES:
        for candidate in CONSTRUCTIBLE_FALLBACK_RESOLUTIONS:
            if candidate not in expanded:
                expanded.append(candidate)
            if len(expanded) >= MIN_SLIDER_RESOLUTION_CHOICES:
                break

    return _sort_resolutions(expanded)


def detect_supported_resolutions(
    app: Any,
    current_resolution: Iterable[int] | None,
    common_resolutions: Iterable[Resolution],
) -> list[Resolution]:
    """Return resolution choices that should be valid on the current display.

    Exact display-mode data is preferred because it prevents unsupported options
    from appearing in Bridge Calibration. The current saved resolution is always
    retained as a choice so opening settings does not create a false dirty state
    on platforms where display probing reports a smaller CI/headless mode.
    """
    current = _landscape_resolution(*normalize_resolution(current_resolution))
    desktop_size = _desktop_resolution(app) if app is not None else None
    window_size = _window_resolution(app) if app is not None else None
    exact_modes = _query_display_modes(app) if app is not None else set()
    common = {_landscape_resolution(*normalize_resolution(res)) for res in common_resolutions}

    if exact_modes:
        choices = [res for res in common if res in exact_modes and _fits_display(res, desktop_size)]
        if not choices:
            choices = [res for res in exact_modes if _fits_display(res, desktop_size)]
    else:
        choices = [res for res in common if _fits_display(res, desktop_size)]
        if window_size is not None:
            choices.append(window_size)

    choices.append(current)

    sorted_choices = _sort_resolutions(res for res in choices if _is_reasonable_game_resolution(res))
    if not sorted_choices:
        sorted_choices = [current]
    sorted_choices = _ensure_slider_safe_choices(sorted_choices, current, common, desktop_size)
    return _trim_resolution_choices(sorted_choices, current)