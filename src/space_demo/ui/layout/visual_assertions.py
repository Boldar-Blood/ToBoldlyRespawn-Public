"""Static visual QA assertions for UI layout data."""

from __future__ import annotations

from space_demo.ui.layout.rect import LayoutIssue, RectPct
from space_demo.ui.layout.text_fit import text_fits_box


def assert_min_target_size(
    widget_name: str,
    rect: RectPct,
    screen_width_px: int,
    screen_height_px: int,
    min_px: int = 44,
) -> list[LayoutIssue]:
    """Return an issue when a clickable target is too small."""
    width_px = rect.w * screen_width_px
    height_px = rect.h * screen_height_px
    if width_px < min_px or height_px < min_px:
        return [
            LayoutIssue(
                severity="error",
                code="target_too_small",
                message=f"{widget_name} target is {width_px:.0f}x{height_px:.0f}px; minimum is {min_px}px",
                widget=widget_name,
            )
        ]
    return []


def assert_text_fits(
    widget_name: str,
    text: str,
    rect: RectPct,
    screen_width_px: int,
    screen_height_px: int,
    font_px: float,
) -> list[LayoutIssue]:
    """Return an issue when text is predicted not to fit in a rectangle."""
    width_px = rect.w * screen_width_px
    height_px = rect.h * screen_height_px
    if not text_fits_box(text, width_px, height_px, font_px):
        return [
            LayoutIssue(
                severity="warning",
                code="text_may_overflow",
                message=f"{widget_name} text may overflow {width_px:.0f}x{height_px:.0f}px box",
                widget=widget_name,
            )
        ]
    return []


def assert_required_assets(asset_names: list[str], available_assets: set[str]) -> list[LayoutIssue]:
    """Return warnings for missing optional-but-expected art assets."""
    issues: list[LayoutIssue] = []
    for asset_name in asset_names:
        if asset_name not in available_assets:
            issues.append(
                LayoutIssue(
                    severity="warning",
                    code="missing_asset",
                    message=f"Expected visual asset is missing: {asset_name}",
                    widget=asset_name,
                )
            )
    return issues
