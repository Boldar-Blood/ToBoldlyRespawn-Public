"""Runtime layout context for normalized screen contracts.

The context converts the project layout contract into concrete Panda3D/aspect2d
coordinates. It is deliberately small so UI screens can be migrated one at a
time without depending on a full browser-style layout engine.
"""

from __future__ import annotations

from dataclasses import dataclass

from space_demo.ui.layout.rect import RectPct


_FLOAT_PRECISION = 12


def _clean(value: float) -> float:
    """Round tiny binary floating-point artifacts out of layout values."""
    cleaned = round(float(value), _FLOAT_PRECISION)
    return 0.0 if cleaned == -0.0 else cleaned


@dataclass(frozen=True)
class AspectRect:
    """A rectangle in Panda3D aspect2d coordinates.

    x/z represent the rectangle center, while width/height are aspect2d units.
    """

    x: float
    z: float
    width: float
    height: float

    @property
    def frame_size(self) -> tuple[float, float, float, float]:
        """Return a DirectGUI frameSize centered around origin."""
        half_w = self.width / 2.0
        half_h = self.height / 2.0
        return (_clean(-half_w), _clean(half_w), _clean(-half_h), _clean(half_h))

    @property
    def pos(self) -> tuple[float, float, float]:
        """Return a DirectGUI/Panda3D position tuple."""
        return (_clean(self.x), 0.0, _clean(self.z))


@dataclass(frozen=True)
class LayoutContext:
    """Convert normalized layout rectangles into aspect2d units.

    Args:
        aspect_ratio: Window width / height. Use 16/9 for standard visual smoke.
        ui_scale: User-facing UI scale.
        text_scale: User-facing text scale.
        safe_margin_pct: Normalized margin removed from all edges.
    """

    aspect_ratio: float = 16.0 / 9.0
    ui_scale: float = 1.0
    text_scale: float = 1.0
    safe_margin_pct: float = 0.02

    def clamp_to_safe_area(self, rect: RectPct) -> RectPct:
        """Clamp a normalized rectangle into the configured safe area."""
        margin = self.safe_margin_pct
        x = max(margin, min(rect.x, 1.0 - margin))
        y = max(margin, min(rect.y, 1.0 - margin))
        w = min(rect.w, 1.0 - margin - x)
        h = min(rect.h, 1.0 - margin - y)
        return RectPct(_clean(x), _clean(y), _clean(max(0.0, w)), _clean(max(0.0, h)))

    def to_aspect_rect(self, rect: RectPct, apply_ui_scale: bool = True) -> AspectRect:
        """Convert normalized top-left coordinates to aspect2d center coords."""
        safe = self.clamp_to_safe_area(rect)
        scale = self.ui_scale if apply_ui_scale else 1.0
        width = safe.w * 2.0 * self.aspect_ratio * scale
        height = safe.h * 2.0 * scale
        center_x_pct = safe.x + safe.w / 2.0
        center_y_pct = safe.y + safe.h / 2.0
        x = (center_x_pct - 0.5) * 2.0 * self.aspect_ratio
        z = (0.5 - center_y_pct) * 2.0
        return AspectRect(x=_clean(x), z=_clean(z), width=_clean(width), height=_clean(height))

    def zone_child(self, zone: RectPct, rel: RectPct) -> RectPct:
        """Return a child rectangle relative to a parent normalized zone."""
        return RectPct(
            x=_clean(zone.x + rel.x * zone.w),
            y=_clean(zone.y + rel.y * zone.h),
            w=_clean(rel.w * zone.w),
            h=_clean(rel.h * zone.h),
        )
