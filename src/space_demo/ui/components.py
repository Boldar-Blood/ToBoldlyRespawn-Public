# Reusable UI Components - To Boldly Respawn

from dataclasses import dataclass

from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel
import direct.gui.DirectGuiGlobals as DGG
from direct.interval.IntervalGlobal import Sequence, LerpScaleInterval
from panda3d.core import TextNode, TransparencyAttrib

from space_demo.ui.theme import COLORS, FONTS, LAYERS


MAX_BUTTON_FRAME_UI_SCALE = 1.15
MAX_BUTTON_HEIGHT_UI_SCALE = 1.20
MIN_BUTTON_TEXT_SCALE = 0.012


def wrap_text_lines(text: str, max_chars: int = 48) -> str:
    """Simple word-wrap for DirectGUI/TextNode labels to prevent boundary overflow, preserving newlines."""
    paragraphs = text.split('\n')
    wrapped_paragraphs = []

    for paragraph in paragraphs:
        if not paragraph.strip():
            wrapped_paragraphs.append("")
            continue

        words = paragraph.split()
        current = []
        lines = []
        for word in words:
            if len(word) > max_chars:
                if current:
                    lines.append(" ".join(current))
                    current = []
                sub_words = [word[i:i + max_chars] for i in range(0, len(word), max_chars)]
                lines.extend(sub_words[:-1])
                current = [sub_words[-1]]
                continue

            candidate = " ".join(current + [word])
            if len(candidate) > max_chars and current:
                lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)

        if current:
            lines.append(" ".join(current))

        wrapped_paragraphs.append("\n".join(lines))

    return "\n".join(wrapped_paragraphs)


def fit_text_scale(
    text: str,
    base_scale: float,
    max_chars: int,
    min_scale: float = 0.020,
) -> float:
    """Reduce text scale for longer labels, but never below min_scale."""
    if not text or len(text) <= max_chars:
        return base_scale

    overflow_ratio = len(text) / max_chars
    adjusted = base_scale / max(1.0, overflow_ratio * 0.85)
    return max(min_scale, adjusted)


class GamePanel:
    """Reusable holographic panel wrapper.

    Creates a dark backing layer plus a subtle glowing border layer. A curated
    panel texture can optionally be placed as a translucent child layer behind
    text/widgets without changing existing panel sizing or layout.
    """

    def __init__(
        self,
        parent,
        name: str,
        pos=(0, 0, 0),
        size=(1.0, 0.6),
        bg_color=COLORS.panel_bg,
        stroke_color=COLORS.panel_stroke,
        border_thickness=0.010,
        sort=LAYERS.panel,
        skin_texture=None,
        skin_alpha: float = 0.32,
    ):
        self.name = name
        self.parent = parent
        self.width, self.height = size
        self.skin_node = None

        half_w = self.width / 2
        half_h = self.height / 2

        self.root = DirectFrame(
            parent=parent,
            frameSize=(-half_w, half_w, -half_h, half_h),
            pos=pos,
            frameColor=bg_color,
            relief=DGG.FLAT,
            sortOrder=sort,
        )
        self.root.setTransparency(TransparencyAttrib.MAlpha)

        if skin_texture is not None:
            self.set_skin(skin_texture, skin_alpha)

        self.border_nodes = []
        self._add_border(
            frameSize=(-half_w, half_w, -border_thickness, border_thickness),
            pos=(0, 0, half_h),
            color=stroke_color,
        )
        self._add_border(
            frameSize=(-half_w, half_w, -border_thickness, border_thickness),
            pos=(0, 0, -half_h),
            color=stroke_color,
        )
        self._add_border(
            frameSize=(-border_thickness, border_thickness, -half_h, half_h),
            pos=(-half_w, 0, 0),
            color=stroke_color,
        )
        self._add_border(
            frameSize=(-border_thickness, border_thickness, -half_h, half_h),
            pos=(half_w, 0, 0),
            color=stroke_color,
        )

    def set_skin(self, texture, alpha: float = 0.32):
        """Apply or replace a translucent curated panel texture.

        The texture is intentionally a child of the root panel, not the root
        frame itself. That keeps live labels/buttons as normal children above the
        skin and avoids distorting text or changing existing hit boxes.
        """
        if self.skin_node is not None:
            self.skin_node.destroy()
            self.skin_node = None
        if texture is None:
            return None

        half_w = self.width / 2
        half_h = self.height / 2
        self.skin_node = DirectFrame(
            parent=self.root,
            image=texture,
            image_scale=(half_w, 1.0, half_h),
            frameColor=(0.0, 0.0, 0.0, 0.0),
            relief=None,
            sortOrder=LAYERS.curated_skin,
        )
        self.skin_node.setTransparency(TransparencyAttrib.MAlpha)
        self.skin_node.setColorScale(1.0, 1.0, 1.0, max(0.0, min(1.0, alpha)))
        return self.skin_node

    def _add_border(self, frameSize, pos, color):
        border = DirectFrame(
            parent=self.root,
            frameSize=frameSize,
            pos=pos,
            frameColor=color,
            relief=DGG.FLAT,
        )
        border.setTransparency(TransparencyAttrib.MAlpha)
        self.border_nodes.append(border)

    def show(self):
        self.root.show()

    def hide(self):
        self.root.hide()

    def destroy(self):
        if self.skin_node is not None:
            self.skin_node.destroy()
            self.skin_node = None
        for b in self.border_nodes:
            b.destroy()
        self.border_nodes.clear()
        self.root.destroy()


@dataclass(frozen=True)
class ButtonSpec:
    """Layout constants for a reusable themed button.

    Sizes are expressed in DirectGUI coordinate units.  User UI scaling is
    intentionally capped for button frames because most screens use fixed anchor
    positions; uncapped 150% frame growth can make adjacent controls overlap.
    Text still uses the user text scale and auto-fits inside the capped frame.
    """

    width: float
    height: float
    text_scale: float
    horizontal_padding: float
    vertical_padding: float


BUTTON_SPECS = {
    "small": ButtonSpec(width=0.32, height=0.070, text_scale=0.026, horizontal_padding=0.035, vertical_padding=0.012),
    "medium": ButtonSpec(width=0.52, height=0.080, text_scale=0.030, horizontal_padding=0.045, vertical_padding=0.014),
    "large": ButtonSpec(width=0.72, height=0.090, text_scale=0.034, horizontal_padding=0.055, vertical_padding=0.016),
    "wide": ButtonSpec(width=0.92, height=0.090, text_scale=0.032, horizontal_padding=0.060, vertical_padding=0.016),
    "modal": ButtonSpec(width=0.66, height=0.085, text_scale=0.031, horizontal_padding=0.050, vertical_padding=0.016),
}


def capped_button_frame_scale(ui_scale: float) -> tuple[float, float]:
    """Return frame scaling that remains safe for fixed-position button rows."""
    safe_scale = max(0.50, ui_scale)
    width_scale = min(safe_scale, MAX_BUTTON_FRAME_UI_SCALE)
    height_scale = min(safe_scale, MAX_BUTTON_HEIGHT_UI_SCALE)
    return width_scale, height_scale


def estimate_button_width(text: str, text_scale: float, padding: float) -> float:
    """Estimate the width needed for a one-line button label."""
    if not text:
        return padding * 2.0
    return len(text) * text_scale * 0.58 + padding * 2.0


def estimate_fit_text_scale(text: str, base_scale: float, available_width: float, min_scale: float) -> float:
    """Return a conservative text scale that should fit inside a button width."""
    if not text:
        return base_scale
    estimated_char_width = base_scale * 0.58
    estimated_width = len(text) * estimated_char_width
    if estimated_width <= available_width:
        return base_scale
    scale = base_scale * (available_width / max(estimated_width, 1e-6))
    return max(min_scale, min(base_scale, scale))


class GameButton:
    """Reusable themed button with consistent sizing, padding, and text fitting."""

    def __init__(
        self,
        parent,
        text: str,
        command,
        pos=(0, 0, 0),
        size: str = "medium",
        variant: str = "primary",
        font=None,
        ui_scale: float = 1.0,
        text_scale: float = 1.0,
        auto_fit: bool = True,
        width=None,
        height=None,
    ) -> None:
        self.parent = parent
        self.text = text
        self.command = command
        self.font = font
        self.variant = variant
        self.size_name = size

        spec = BUTTON_SPECS.get(size, BUTTON_SPECS["medium"])
        frame_width_scale, frame_height_scale = capped_button_frame_scale(ui_scale)
        self.width = (width if width is not None else spec.width) * frame_width_scale
        self.height = (height if height is not None else spec.height) * frame_height_scale

        base_text_scale = spec.text_scale * text_scale
        safe_width = max(0.05, self.width - 2.0 * spec.horizontal_padding * frame_width_scale)

        self.final_text_scale = base_text_scale
        if auto_fit:
            self.final_text_scale = estimate_fit_text_scale(
                text=text,
                base_scale=base_text_scale,
                available_width=safe_width,
                min_scale=MIN_BUTTON_TEXT_SCALE,
            )

        half_w = self.width / 2.0
        half_h = self.height / 2.0
        frame_size = (-half_w, half_w, -half_h, half_h)
        self.bg_color = self._variant_color(variant)

        self.node = DirectButton(
            parent=parent,
            text=text,
            command=command,
            pos=pos,
            frameSize=frame_size,
            frameColor=self.bg_color,
            relief=DGG.FLAT,
            text_font=font,
            text_scale=self.final_text_scale,
            text_align=TextNode.ACenter,
            text_pos=(0.0, -self.final_text_scale * 0.34),
            text_fg=COLORS.text_primary,
            text_shadow=(0.0, 0.0, 0.0, 0.85),
            text_shadowOffset=(0.035, -0.035),
            rolloverSound=None,
            clickSound=None,
            sortOrder=LAYERS.button,
        )
        self.node.setTransparency(TransparencyAttrib.MAlpha)

        self.node.bind(DGG.WITHIN, self._hover_in)
        self.node.bind(DGG.WITHOUT, self._hover_out)
        self.node.bind(DGG.B1PRESS, self._press)

        self.default_scale = self.node.getScale()
        self.default_color = self.bg_color
        self.pulse_seq = None

    def _variant_color(self, variant):
        if variant == "danger":
            return (0.45, 0.08, 0.08, 0.92)
        if variant == "success":
            return (0.06, 0.35, 0.16, 0.92)
        if variant == "warning":
            return (0.55, 0.32, 0.05, 0.92)
        return COLORS.button_bg

    def _hover_in(self, event=None):
        self.node.setScale(self.default_scale * 1.045)
        self.node.setColorScale(1.12, 1.12, 1.12, 1.0)
        import builtins
        if hasattr(builtins, "base"):
            app = builtins.base
            if hasattr(app, "play_sound") and hasattr(app, "pickup_sfx") and app.pickup_sfx:
                app.play_sound(app.pickup_sfx)

    def _hover_out(self, event=None):
        self.node.setScale(self.default_scale)
        self.node.setColorScale(1.0, 1.0, 1.0, 1.0)

    def _press(self, event=None):
        if self.pulse_seq:
            self.pulse_seq.finish()
        self.pulse_seq = Sequence(
            LerpScaleInterval(self.node, 0.055, self.default_scale * 0.98),
            LerpScaleInterval(self.node, 0.080, self.default_scale * 1.045),
        )
        self.pulse_seq.start()

    def validate_layout(self) -> list[str]:
        """Return warnings for obvious layout issues."""
        warnings: list[str] = []
        if self.final_text_scale <= 0:
            warnings.append(f"Button {self.text!r} has non-positive text scale.")
        if len(self.text) > 32 and self.size_name not in {"wide", "modal"}:
            warnings.append(f"Button {self.text!r} is long for size {self.size_name!r}.")
        return warnings

    def show(self):
        self.node.show()

    def hide(self):
        self.node.hide()

    def destroy(self):
        if self.pulse_seq:
            self.pulse_seq.finish()
            self.pulse_seq = None
        self.node.destroy()


class GameTitle:
    """Cyan holographic text title, centering itself on pos, pulsing slowly via intervals."""

    def __init__(self, parent, text, font, pos=(0, 0, 0.48), scale=None):
        self.base_scale = scale or FONTS.title_scale
        self.node = DirectLabel(
            parent=parent,
            text=text,
            pos=pos,
            scale=self.base_scale,
            text_font=font,
            text_fg=COLORS.cyan,
            text_shadow=(0, 0, 0, 0.95),
            text_shadowOffset=(0.055, -0.055),
            relief=None,
            sortOrder=LAYERS.text,
        )
        self.node.setTransparency(TransparencyAttrib.MAlpha)
        self.pulse = None

    def start_idle(self):
        if self.pulse:
            self.pulse.finish()

        self.pulse = Sequence(
            LerpScaleInterval(self.node, 1.2, self.base_scale * 1.015),
            LerpScaleInterval(self.node, 1.2, self.base_scale),
        )
        self.pulse.loop()

    def stop_idle(self):
        if self.pulse:
            self.pulse.finish()
            self.pulse = None

    def show(self):
        self.node.show()

    def hide(self):
        self.node.hide()

    def destroy(self):
        self.stop_idle()
        self.node.destroy()


class ScreenDimmer:
    """Full-screen dimming panel to control focus and contrast behind active menus."""

    def __init__(self, parent, alpha=0.42):
        self.node = DirectFrame(
            parent=parent,
            frameSize=(-2.5, 2.5, -1.5, 1.5),
            frameColor=(0.0, 0.0, 0.0, alpha),
            relief=DGG.FLAT,
            sortOrder=LAYERS.background,
        )
        self.node.setTransparency(TransparencyAttrib.MAlpha)

    def set_alpha(self, alpha):
        self.node["frameColor"] = (0.0, 0.0, 0.0, alpha)

    def show(self):
        self.node.show()

    def hide(self):
        self.node.hide()

    def destroy(self):
        self.node.destroy()


class GameMeter:
    """Reusable progress meter for clean graphical loading/stats."""

    def __init__(
        self,
        parent,
        label: str,
        pos=(0, 0, 0),
        width=0.90,
        height=0.055,
        font=None,
    ):
        self.width = width
        self.height = height

        self.root = DirectFrame(
            parent=parent,
            pos=pos,
            frameSize=(-width / 2, width / 2, -height / 2, height / 2),
            frameColor=(0.02, 0.025, 0.04, 0.88),
            relief=DGG.FLAT,
            sortOrder=LAYERS.panel,
        )
        self.root.setTransparency(TransparencyAttrib.MAlpha)

        self.fill = DirectFrame(
            parent=self.root,
            pos=(-width / 2, 0, 0),
            frameSize=(0, width, -height / 2, height / 2),
            frameColor=COLORS.green,
            relief=DGG.FLAT,
        )
        self.fill.setTransparency(TransparencyAttrib.MAlpha)

        self.label = DirectLabel(
            parent=self.root,
            text=label,
            pos=(0, 0, height * 0.85),
            scale=FONTS.small_scale,
            text_font=font,
            text_fg=COLORS.text_primary,
            relief=None,
        )

    def set_fraction(self, fraction: float, label: str | None = None):
        fraction = max(0.0, min(1.0, fraction))
        fill_w = self.width * fraction

        self.fill["frameSize"] = (0, fill_w, -self.height / 2, self.height / 2)
        self.fill.setX(-self.width / 2)

        if fraction > 0.50:
            self.fill["frameColor"] = COLORS.green
        elif fraction > 0.20:
            self.fill["frameColor"] = COLORS.amber
        else:
            self.fill["frameColor"] = COLORS.red

        if label is not None:
            update_label_text(self.label, label)

    def show(self):
        self.root.show()

    def hide(self):
        self.root.hide()

    def destroy(self):
        self.fill.destroy()
        self.label.destroy()
        self.root.destroy()


@dataclass(frozen=True)
class UILabelSpec:
    text: str
    pos: tuple[float, float, float]
    base_scale: float
    min_scale: float = 0.014
    max_lines: int = 4
    wordwrap: int = 44
    color: tuple[float, float, float, float] = COLORS.text_primary
    align: int = TextNode.ACenter
    sort_order: int = LAYERS.text


def create_label_from_spec(parent, spec: UILabelSpec, font, effective_scale: float) -> DirectLabel:
    """Create a DirectLabel from a UILabelSpec enforcing standard layout contract.

    This contract guarantees that layout sizing is handled at the NodePath level
    via `setScale` (computed using base_scale and effective_scale) while the inner
    `text_scale` is set to 1.0.
    """
    label = DirectLabel(
        parent=parent,
        text=spec.text,
        pos=spec.pos,
        text_font=font,
        text_fg=spec.color,
        text_shadow=(0, 0, 0, 0.85),
        text_align=spec.align,
        text_wordwrap=spec.wordwrap,
        relief=None,
        sortOrder=spec.sort_order,
    )
    # Ensure inner text_scale defaults to 1.0
    label["text_scale"] = 1.0
    label["text_pos"] = (0, 0)
    label.setTransparency(TransparencyAttrib.MAlpha)
    
    # NodePath layout scale application
    label.setScale(spec.base_scale * effective_scale)
    return label


def update_label_from_spec(label: DirectLabel, spec: UILabelSpec, effective_scale: float) -> None:
    """Update an existing DirectLabel using UILabelSpec parameters.

    Ensures the NodePath scale and position are updated, keeping inner text_scale at 1.0.
    """
    label["text"] = spec.text
    label["text_fg"] = spec.color
    label["text_align"] = spec.align
    label["text_wordwrap"] = spec.wordwrap
    label["text_scale"] = 1.0
    label["text_pos"] = (0, 0)
    
    label.setPos(spec.pos[0], spec.pos[1], spec.pos[2])
    label.setScale(spec.base_scale * effective_scale)


def update_label_text(label: DirectLabel, text: str) -> None:
    """Update label text dynamically while ensuring inner text_scale remains 1.0."""
    label["text"] = text
    label["text_scale"] = 1.0
    label["text_pos"] = (0, 0)


