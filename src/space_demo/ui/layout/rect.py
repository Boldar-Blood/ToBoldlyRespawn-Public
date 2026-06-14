"""Normalized rectangle primitives for UI layout validation."""

from __future__ import annotations

from dataclasses import dataclass


_FLOAT_PRECISION = 12


def _clean(value: float) -> float:
    """Round binary floating-point artifacts out of layout math."""
    cleaned = round(float(value), _FLOAT_PRECISION)
    return 0.0 if cleaned == -0.0 else cleaned


@dataclass(frozen=True)
class RectPct:
    """A rectangle in normalized top-left screen coordinates."""

    x: float
    y: float
    w: float
    h: float

    def __post_init__(self) -> None:
        """Normalize stored coordinates for deterministic equality tests."""
        object.__setattr__(self, "x", _clean(self.x))
        object.__setattr__(self, "y", _clean(self.y))
        object.__setattr__(self, "w", _clean(self.w))
        object.__setattr__(self, "h", _clean(self.h))

    def right(self) -> float:
        """Return the normalized right edge."""
        return _clean(self.x + self.w)

    def bottom(self) -> float:
        """Return the normalized bottom edge."""
        return _clean(self.y + self.h)

    def contains(self, other: "RectPct", tolerance: float = 0.0) -> bool:
        """Return True when this rectangle contains another rectangle."""
        tolerance = _clean(tolerance)
        return (
            other.x >= _clean(self.x - tolerance)
            and other.y >= _clean(self.y - tolerance)
            and other.right() <= _clean(self.right() + tolerance)
            and other.bottom() <= _clean(self.bottom() + tolerance)
        )

    def overlaps(self, other: "RectPct", tolerance: float = 0.0) -> bool:
        """Return True when this rectangle intersects another rectangle."""
        tolerance = _clean(tolerance)
        return not (
            self.right() <= _clean(other.x + tolerance)
            or other.right() <= _clean(self.x + tolerance)
            or self.bottom() <= _clean(other.y + tolerance)
            or other.bottom() <= _clean(self.y + tolerance)
        )

    def area(self) -> float:
        """Return normalized area."""
        return _clean(max(0.0, self.w) * max(0.0, self.h))

    def scaled(self, sx: float, sy: float) -> "Rect":
        """Convert to absolute pixel-like coordinates."""
        return Rect(_clean(self.x * sx), _clean(self.y * sy), _clean(self.w * sx), _clean(self.h * sy))


@dataclass(frozen=True)
class Rect:
    """An absolute rectangle in top-left coordinates."""

    x: float
    y: float
    w: float
    h: float

    def __post_init__(self) -> None:
        """Normalize stored coordinates for deterministic equality tests."""
        object.__setattr__(self, "x", _clean(self.x))
        object.__setattr__(self, "y", _clean(self.y))
        object.__setattr__(self, "w", _clean(self.w))
        object.__setattr__(self, "h", _clean(self.h))

    def right(self) -> float:
        """Return the normalized right edge."""
        return _clean(self.x + self.w)

    def bottom(self) -> float:
        """Return the normalized bottom edge."""
        return _clean(self.y + self.h)


@dataclass(frozen=True)
class LayoutIssue:
    """A machine-readable layout validation issue."""

    severity: str
    code: str
    message: str
    widget: str | None = None
    zone: str | None = None
