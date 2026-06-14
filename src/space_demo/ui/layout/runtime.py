"""Runtime adapter for canonical UI screen specs.

This module is the bridge between normalized layout contracts and Panda3D UI
construction. It lets screens request named widget rectangles instead of
hand-typing coordinates, and it lets visual QA dump the exact intended layout.
"""

from __future__ import annotations

from dataclasses import dataclass

from space_demo.ui.layout.context import AspectRect, LayoutContext
from space_demo.ui.layout.contracts import get_screen_contract, validate_screen_layout
from space_demo.ui.layout.reporting import LayoutReporter
from space_demo.ui.layout.screen_specs import WidgetSpec, get_screen_widget_specs, widget_rects_for, widget_zones_for


@dataclass(frozen=True)
class RuntimeWidgetLayout:
    """A widget spec paired with converted aspect2d geometry."""

    spec: WidgetSpec
    aspect_rect: AspectRect

    @property
    def pos(self) -> tuple[float, float, float]:
        """Return the Panda3D/DirectGUI position tuple."""
        return self.aspect_rect.pos

    @property
    def frame_size(self) -> tuple[float, float, float, float]:
        """Return the DirectGUI frameSize tuple."""
        return self.aspect_rect.frame_size


class ScreenRuntimeLayout:
    """Convert and validate canonical widget specs for one screen."""

    def __init__(self, screen_name: str, context: LayoutContext | None = None):
        self.screen_name = screen_name
        self.context = context or LayoutContext()
        self.contract = get_screen_contract(screen_name)
        self.specs = get_screen_widget_specs(screen_name)
        self._by_name = {spec.name: spec for spec in self.specs}

    def spec(self, widget_name: str) -> WidgetSpec:
        """Return a named widget spec."""
        return self._by_name[widget_name]

    def widget(self, widget_name: str, apply_ui_scale: bool = True) -> RuntimeWidgetLayout:
        """Return converted layout data for one widget."""
        spec = self.spec(widget_name)
        return RuntimeWidgetLayout(spec=spec, aspect_rect=self.context.to_aspect_rect(spec.rect, apply_ui_scale=apply_ui_scale))

    def widgets(self, apply_ui_scale: bool = True) -> dict[str, RuntimeWidgetLayout]:
        """Return all converted widget layouts keyed by widget name."""
        return {spec.name: self.widget(spec.name, apply_ui_scale=apply_ui_scale) for spec in self.specs}

    def validate(self):
        """Validate this screen's canonical widgets against its contract."""
        return validate_screen_layout(self.contract, widget_rects_for(self.screen_name), widget_zones_for(self.screen_name))

    def reporter(self) -> LayoutReporter:
        """Return a populated layout reporter for visual QA output."""
        reporter = LayoutReporter(self.screen_name)
        for spec in self.specs:
            reporter.add_widget(spec.name, spec.zone, spec.rect, kind=spec.kind, text=spec.text)
        reporter.add_issues(self.validate())
        return reporter


def build_runtime_layout(screen_name: str, ui_scale: float = 1.0, text_scale: float = 1.0, aspect_ratio: float = 16.0 / 9.0) -> ScreenRuntimeLayout:
    """Create a runtime layout for a screen using common UI settings."""
    return ScreenRuntimeLayout(
        screen_name,
        context=LayoutContext(aspect_ratio=aspect_ratio, ui_scale=ui_scale, text_scale=text_scale),
    )
