"""Bounded reusable controls for the UI layout refactor.

These controls intentionally use a small, documented DirectGUI option surface and
explicit frame sizes so screens can be validated against layout contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel, DirectSlider
import direct.gui.DirectGuiGlobals as DGG
from panda3d.core import TextNode, TransparencyAttrib

from space_demo.ui.layout.context import AspectRect
from space_demo.ui.layout.text_fit import shrink_font_to_fit
from space_demo.ui.theme import COLORS, LAYERS


@dataclass(frozen=True)
class ControlStyle:
    """Basic colors for a bounded UI control."""

    bg: tuple[float, float, float, float]
    hover: tuple[float, float, float, float]
    active: tuple[float, float, float, float]
    text: tuple[float, float, float, float] = COLORS.text_primary
    stroke: tuple[float, float, float, float] = COLORS.panel_stroke


PRIMARY_STYLE = ControlStyle(
    bg=(0.06, 0.18, 0.32, 0.92),
    hover=(0.10, 0.25, 0.42, 0.96),
    active=(0.04, 0.13, 0.24, 0.96),
)
SUCCESS_STYLE = ControlStyle(
    bg=(0.05, 0.34, 0.16, 0.92),
    hover=(0.08, 0.46, 0.22, 0.96),
    active=(0.03, 0.25, 0.12, 0.96),
)
WARNING_STYLE = ControlStyle(
    bg=(0.52, 0.30, 0.05, 0.92),
    hover=(0.66, 0.40, 0.08, 0.96),
    active=(0.40, 0.22, 0.03, 0.96),
)
DANGER_STYLE = ControlStyle(
    bg=(0.42, 0.07, 0.07, 0.92),
    hover=(0.58, 0.10, 0.10, 0.96),
    active=(0.32, 0.04, 0.04, 0.96),
)


def style_for_variant(variant: str) -> ControlStyle:
    """Return a style by variant name."""
    if variant == "success":
        return SUCCESS_STYLE
    if variant == "warning":
        return WARNING_STYLE
    if variant == "danger":
        return DANGER_STYLE
    return PRIMARY_STYLE


class BoundedButton:
    """A button constrained to an explicit layout rectangle."""

    def __init__(
        self,
        parent,
        rect: AspectRect,
        text: str,
        command: Callable | None,
        font=None,
        text_scale: float = 1.0,
        variant: str = "primary",
        min_font_px: float = 10.0,
    ) -> None:
        self.rect = rect
        self.text = text
        self.style = style_for_variant(variant)
        # Approximate aspect2d units to pixels at 720p; conservative for fit.
        font_px = shrink_font_to_fit(text, rect.width * 360.0, rect.height * 360.0, 20.0 * text_scale, min_font_px)
        direct_scale = max(0.010, font_px / 720.0)
        self.node = DirectButton(
            parent=parent,
            text=text,
            command=command,
            pos=rect.pos,
            frameSize=rect.frame_size,
            frameColor=(self.style.bg, self.style.active, self.style.hover, self.style.bg),
            relief=DGG.FLAT,
            text_font=font,
            text_scale=direct_scale,
            text_align=TextNode.ACenter,
            text_pos=(0.0, -direct_scale * 0.35),
            text_fg=self.style.text,
            text_shadow=(0, 0, 0, 0.85),
            rolloverSound=None,
            clickSound=None,
            sortOrder=LAYERS.button,
        )
        self.node.setTransparency(TransparencyAttrib.MAlpha)

    def destroy(self) -> None:
        """Destroy the underlying DirectButton."""
        self.node.destroy()


class BoundedToggleButton:
    """A bounded two-state button with explicit on/off labels."""

    def __init__(
        self,
        parent,
        rect: AspectRect,
        label_on: str,
        label_off: str,
        value: bool,
        command: Callable | None,
        font=None,
        text_scale: float = 1.0,
    ) -> None:
        self.label_on = label_on
        self.label_off = label_off
        self.value = bool(value)
        self.command = command
        self.button = BoundedButton(
            parent=parent,
            rect=rect,
            text=self._label(),
            command=self._toggle,
            font=font,
            text_scale=text_scale,
            variant="success" if self.value else "danger",
        )

    @property
    def node(self):
        """Return the DirectButton node for compatibility."""
        return self.button.node

    def _label(self) -> str:
        return self.label_on if self.value else self.label_off

    def _toggle(self) -> None:
        self.value = not self.value
        self.set_value(self.value)
        if self.command:
            self.command()

    def set_value(self, value: bool) -> None:
        """Update the visual state without assuming DirectGUI option types."""
        self.value = bool(value)
        style = style_for_variant("success" if self.value else "danger")
        self.node["text"] = self._label()
        self.node["frameColor"] = (style.bg, style.active, style.hover, style.bg)

    def destroy(self) -> None:
        self.button.destroy()


class BoundedSlider:
    """A DirectSlider with explicit dimensions and an external label contract."""

    def __init__(
        self,
        parent,
        rect: AspectRect,
        value_range: tuple[float, float],
        value: float,
        command: Callable | None,
        page_size: float = 1.0,
    ) -> None:
        self.rect = rect
        self.node = DirectSlider(
            parent=parent,
            pos=rect.pos,
            range=value_range,
            value=value,
            pageSize=page_size,
            frameSize=(-rect.width / 2.0, rect.width / 2.0, -rect.height / 10.0, rect.height / 10.0),
            frameColor=(0.18, 0.22, 0.30, 0.92),
            relief=DGG.FLAT,
            command=command,
        )
        self.node.setScale(1.0)
        self.node.setTransparency(TransparencyAttrib.MAlpha)
        # DirectSlider's thumb is a DirectButton child. Configure it only through
        # stable DirectButton options after construction.
        try:
            thumb = self.node.thumb
            thumb["frameSize"] = (-rect.height * 0.20, rect.height * 0.20, -rect.height * 0.42, rect.height * 0.42)
            thumb["frameColor"] = (0.20, 0.58, 0.95, 0.98)
            thumb["relief"] = DGG.FLAT
        except Exception:
            pass

    def get_value(self) -> float:
        return float(self.node.getValue())

    def set_value(self, value: float) -> None:
        self.node.setValue(value)

    def destroy(self) -> None:
        self.node.destroy()


class SpritePanel:
    """A bounded image-backed panel with live text layered separately."""

    def __init__(self, parent, rect: AspectRect, texture=None, color=COLORS.panel_bg_dark, sort=LAYERS.panel):
        kwargs = {
            "parent": parent,
            "pos": rect.pos,
            "frameSize": rect.frame_size,
            "frameColor": color,
            "relief": DGG.FLAT,
            "sortOrder": sort,
        }
        if texture is not None:
            kwargs["frameTexture"] = texture
        self.node = DirectFrame(**kwargs)
        self.node.setTransparency(TransparencyAttrib.MAlpha)

    def add_label(self, text: str, x: float, z: float, font=None, scale: float = 0.02, color=COLORS.text_primary, align=TextNode.ACenter):
        """Add a live text label relative to this panel."""
        label = DirectLabel(
            parent=self.node,
            text=text,
            pos=(x, 0, z),
            scale=scale,
            text_font=font,
            text_fg=color,
            text_align=align,
            text_shadow=(0, 0, 0, 0.85),
            relief=None,
        )
        label.setTransparency(TransparencyAttrib.MAlpha)
        return label

    def destroy(self) -> None:
        self.node.destroy()
