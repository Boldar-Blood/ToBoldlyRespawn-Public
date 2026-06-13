"""Viewport model for responsive UI layout decisions.

The game UI should adapt to the active window, not to a guessed device name.
This module keeps that decision data small, deterministic, and reusable without
requiring Panda3D to open a window.
"""

from __future__ import annotations

from dataclasses import dataclass


_MIN_DIMENSION_PX = 1


@dataclass(frozen=True)
class SafeAreaPx:
    """Safe-area insets in physical pixels."""

    left: int = 0
    right: int = 0
    top: int = 0
    bottom: int = 0

    def clamped(self, width_px: int, height_px: int) -> "SafeAreaPx":
        """Return insets that cannot exceed the viewport dimensions."""
        left = max(0, min(int(self.left), width_px - _MIN_DIMENSION_PX))
        right = max(0, min(int(self.right), width_px - left - _MIN_DIMENSION_PX))
        top = max(0, min(int(self.top), height_px - _MIN_DIMENSION_PX))
        bottom = max(0, min(int(self.bottom), height_px - top - _MIN_DIMENSION_PX))
        return SafeAreaPx(left=left, right=right, top=top, bottom=bottom)


@dataclass(frozen=True)
class ViewportContext:
    """Responsive layout inputs derived from the active render viewport."""

    width_px: int
    height_px: int
    safe_area: SafeAreaPx = SafeAreaPx()
    input_mode: str = "keyboard_mouse"

    @classmethod
    def from_size(
        cls,
        width_px: int,
        height_px: int,
        safe_area: SafeAreaPx | None = None,
        input_mode: str = "keyboard_mouse",
    ) -> "ViewportContext":
        """Create a viewport from explicit pixel dimensions."""
        width = max(_MIN_DIMENSION_PX, int(width_px))
        height = max(_MIN_DIMENSION_PX, int(height_px))
        area = (safe_area or SafeAreaPx()).clamped(width, height)
        return cls(width_px=width, height_px=height, safe_area=area, input_mode=input_mode)

    @classmethod
    def from_window(cls, window, input_mode: str = "keyboard_mouse") -> "ViewportContext":
        """Create a viewport from a Panda3D window-like object."""
        try:
            props = window.getProperties()
            width = int(props.getXSize())
            height = int(props.getYSize())
        except Exception:
            width, height = 1280, 720
        return cls.from_size(width, height, input_mode=input_mode)

    @property
    def safe_width_px(self) -> int:
        """Viewport width after safe-area insets."""
        return max(_MIN_DIMENSION_PX, self.width_px - self.safe_area.left - self.safe_area.right)

    @property
    def safe_height_px(self) -> int:
        """Viewport height after safe-area insets."""
        return max(_MIN_DIMENSION_PX, self.height_px - self.safe_area.top - self.safe_area.bottom)

    @property
    def aspect_ratio(self) -> float:
        """Safe-area aspect ratio."""
        return self.safe_width_px / self.safe_height_px

    @property
    def orientation(self) -> str:
        """Return portrait, landscape, or square."""
        if self.safe_width_px > self.safe_height_px:
            return "landscape"
        if self.safe_height_px > self.safe_width_px:
            return "portrait"
        return "square"

    @property
    def short_side_px(self) -> int:
        """Shorter safe-area dimension."""
        return min(self.safe_width_px, self.safe_height_px)

    @property
    def long_side_px(self) -> int:
        """Longer safe-area dimension."""
        return max(self.safe_width_px, self.safe_height_px)

    @property
    def touch_first(self) -> bool:
        """Whether the viewport should favor touch target budgets."""
        return self.input_mode in {"touch", "controller_touch"}
