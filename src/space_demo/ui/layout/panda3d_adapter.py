"""Panda3D adapter for responsive UI layout.

The responsive layout policy is intentionally engine-light and reusable. This
adapter is the Panda3D-facing bridge: it reads ShowBase/window data and creates
layout contexts that DirectGUI/NodePath screen builders can use.
"""

from __future__ import annotations

from dataclasses import dataclass

from space_demo.ui.layout.context import LayoutContext
from space_demo.ui.layout.profiles import HudDensity, LayoutProfile, choose_layout_profile
from space_demo.ui.layout.viewport import ViewportContext


@dataclass(frozen=True)
class Panda3DUiLayoutContext:
    """Responsive layout context derived from a Panda3D app/window."""

    viewport: ViewportContext
    profile: LayoutProfile
    layout_context: LayoutContext
    ui_scale: float = 1.0
    text_scale: float = 1.0

    @classmethod
    def from_app(
        cls,
        app,
        ui_scale: float | None = None,
        text_scale: float | None = None,
        preferred_density: HudDensity | str | None = None,
        input_mode: str = "keyboard_mouse",
    ) -> "Panda3DUiLayoutContext":
        """Create a layout context from a Panda3D ShowBase-like app."""
        settings = getattr(app, "settings", None)
        resolved_ui_scale = float(ui_scale if ui_scale is not None else getattr(settings, "ui_scale", 1.0))
        resolved_text_scale = float(text_scale if text_scale is not None else getattr(settings, "text_scale", 1.0))
        density = preferred_density if preferred_density is not None else getattr(settings, "hud_density", None)
        viewport = ViewportContext.from_window(getattr(app, "win", None), input_mode=input_mode)
        profile = choose_layout_profile(viewport, density)
        return cls.from_viewport(
            viewport=viewport,
            ui_scale=resolved_ui_scale,
            text_scale=resolved_text_scale,
            preferred_density=profile.hud_density,
        )

    @classmethod
    def from_viewport(
        cls,
        viewport: ViewportContext,
        ui_scale: float = 1.0,
        text_scale: float = 1.0,
        preferred_density: HudDensity | str | None = None,
    ) -> "Panda3DUiLayoutContext":
        """Create a layout context from an explicit viewport."""
        profile = choose_layout_profile(viewport, preferred_density)
        return cls(
            viewport=viewport,
            profile=profile,
            layout_context=LayoutContext(
                aspect_ratio=viewport.aspect_ratio,
                ui_scale=ui_scale,
                text_scale=text_scale,
            ),
            ui_scale=ui_scale,
            text_scale=text_scale,
        )

    @property
    def aspect_ratio(self) -> float:
        """Return the safe-area aspect ratio."""
        return self.viewport.aspect_ratio

    @property
    def is_touch_first(self) -> bool:
        """Whether touch-first target sizing should be favored."""
        return self.viewport.touch_first

    @property
    def should_show_empty_log(self) -> bool:
        """Whether an empty tactical log should remain visible."""
        return self.profile.show_log_when_empty


def viewport_from_app(app, input_mode: str = "keyboard_mouse") -> ViewportContext:
    """Return a ViewportContext from a Panda3D app without creating a full context."""
    return ViewportContext.from_window(getattr(app, "win", None), input_mode=input_mode)
