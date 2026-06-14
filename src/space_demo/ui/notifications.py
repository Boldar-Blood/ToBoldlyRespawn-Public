"""Notification toasts and side log for To Boldly Respawn."""

from __future__ import annotations

from panda3d.core import TextNode, TransparencyAttrib
from direct.gui.DirectGui import DirectFrame, DirectLabel
import direct.gui.DirectGuiGlobals as DGG
from direct.interval.IntervalGlobal import Parallel, Sequence, LerpScaleInterval, LerpColorScaleInterval, Func

from space_demo.ui.theme import COLORS
from space_demo.ui.components import GamePanel
from space_demo.ui.layout.gameplay_hud import build_gameplay_hud_layout
from space_demo.ui.layout.viewport import ViewportContext


class NotificationManager:
    """Manage center toasts plus a layout-backed tactical event log."""

    def __init__(self, app, parent=None, font=None, max_entries=5):
        self.app = app
        self.parent = parent
        self.font = font
        self.max_entries = max_entries
        self.entries = []
        self.ui_scale = getattr(getattr(app, "settings", None), "ui_scale", 1.0)
        self.text_scale = getattr(getattr(app, "settings", None), "text_scale", 1.0)
        viewport = ViewportContext.from_window(getattr(app, "win", None)) if app else None
        density = getattr(getattr(app, "settings", None), "hud_density", None)
        self.layout = build_gameplay_hud_layout(
            ui_scale=self.ui_scale,
            viewport=viewport,
            preferred_density=density,
        )
        self.max_entries = min(self.max_entries, self.layout.max_log_entries)
        if self.text_scale > 1.3:
            self.max_entries = min(self.max_entries, 4)

        self.toast_root = DirectFrame(
            parent=self.app.aspect2d if self.app else None,
            pos=(0, 0, 0.42 * self.ui_scale),
            relief=None,
        )
        self.toast_root.setTransparency(TransparencyAttrib.MAlpha)
        self.active_toast = None
        self.toast_interval = None

        self.log_panel = GamePanel(
            parent=self.app.a2dTopLeft if (self.app and hasattr(self.app, "a2dTopLeft")) else None,
            name="hud_notification_log",
            pos=self.layout.log_pos,
            size=self.layout.log_size,
            bg_color=(0.005, 0.010, 0.020, 0.74),
            stroke_color=COLORS.purple,
            border_thickness=0.004 * self.ui_scale,
        )
        self.log_title = DirectLabel(
            parent=self.log_panel.root,
            text="TACTICAL LOG",
            pos=self.layout.log_title_pos,
            scale=0.0155 * self.text_scale,
            text_font=self.font,
            text_fg=COLORS.purple,
            text_shadow=(0, 0, 0, 0.85),
            relief=None,
        )
        self.log_divider = DirectFrame(
            parent=self.log_panel.root,
            frameSize=(-0.095 * self.ui_scale, 0.095 * self.ui_scale, -0.0015 * self.ui_scale, 0.0015 * self.ui_scale),
            pos=(0, 0, self.layout.log_divider_z),
            frameColor=COLORS.purple,
            relief=DGG.FLAT,
        )
        self.log_panel.hide()

    def _get_severity_color(self, severity, category):
        """Return a readable category color."""
        if severity == "danger" or category in ("damage", "no-ammo", "error", "warning"):
            return COLORS.red if "critical" in category or severity == "danger" else COLORS.amber
        if severity == "success" or category in ("pickup", "healing"):
            return COLORS.green
        if severity == "special" or category in ("synergy", "multiplier"):
            return COLORS.purple
        if category in ("system", "shield", "magnet", "intern"):
            return COLORS.cyan
        return COLORS.text_secondary

    def push(self, title, message="", category="system", severity="info", icon=None, value=None, duration=1.2):
        """Push a high-priority center toast and mirror it into the side log."""
        color = self._get_severity_color(severity, category)
        reduce_motion = getattr(getattr(self.app, "settings", None), "reduce_ui_motion", False)
        self.trigger_toast(title, message, color, duration, reduce_motion)
        self.push_to_log(title, message, color)

    def trigger_toast(self, title, message, color, duration, reduce_motion):
        """Create one readable center toast notification."""
        if self.toast_interval:
            self.toast_interval.finish()
            self.toast_interval = None
        if self.active_toast:
            self.active_toast.destroy()
            self.active_toast = None

        self.active_toast = DirectFrame(
            parent=self.toast_root,
            frameSize=(-0.48 * self.ui_scale, 0.48 * self.ui_scale, -0.060 * self.ui_scale, 0.060 * self.ui_scale),
            frameColor=(0.01, 0.02, 0.04, 0.94),
            relief=DGG.FLAT,
        )
        self.active_toast.setTransparency(TransparencyAttrib.MAlpha)
        border_thick = 0.004 * self.ui_scale
        for z_pos in (0.060 * self.ui_scale, -0.060 * self.ui_scale):
            DirectFrame(
                parent=self.active_toast,
                frameSize=(-0.48 * self.ui_scale, 0.48 * self.ui_scale, -border_thick, border_thick),
                pos=(0, 0, z_pos),
                frameColor=color,
                relief=DGG.FLAT,
            )
        DirectLabel(
            parent=self.active_toast,
            text=title.upper(),
            pos=(0, 0, 0.012 * self.ui_scale),
            scale=0.027 * self.text_scale,
            text_font=self.font,
            text_fg=color,
            text_shadow=(0, 0, 0, 0.9),
            relief=None,
        )
        DirectLabel(
            parent=self.active_toast,
            text=message,
            pos=(0, 0, -0.026 * self.ui_scale),
            scale=0.017 * self.text_scale,
            text_font=self.font,
            text_fg=COLORS.text_primary,
            text_shadow=(0, 0, 0, 0.8),
            relief=None,
        )

        if reduce_motion:
            self.active_toast.setColorScale(1.0, 1.0, 1.0, 0.0)
            self.toast_interval = Sequence(
                LerpColorScaleInterval(self.active_toast, 0.10, (1, 1, 1, 1), (1, 1, 1, 0)),
                LerpColorScaleInterval(self.active_toast, duration, (1, 1, 1, 1)),
                LerpColorScaleInterval(self.active_toast, 0.20, (1, 1, 1, 0), (1, 1, 1, 1)),
                Func(self._clear_active_toast),
            )
        else:
            self.active_toast.setScale(0.88)
            self.active_toast.setColorScale(1, 1, 1, 0)
            self.toast_interval = Sequence(
                Parallel(
                    LerpScaleInterval(self.active_toast, 0.18, 1.0, 0.88, blendType="easeOut"),
                    LerpColorScaleInterval(self.active_toast, 0.18, (1, 1, 1, 1), (1, 1, 1, 0)),
                ),
                LerpScaleInterval(self.active_toast, duration, 1.0),
                Parallel(
                    LerpScaleInterval(self.active_toast, 0.20, 1.04, 1.0),
                    LerpColorScaleInterval(self.active_toast, 0.20, (1, 1, 1, 0), (1, 1, 1, 1)),
                ),
                Func(self._clear_active_toast),
            )
        self.toast_interval.start()

    def _clear_active_toast(self):
        """Destroy the active toast, if present."""
        if self.active_toast:
            self.active_toast.destroy()
            self.active_toast = None
        self.toast_interval = None

    def push_to_log(self, title, message, color):
        """Insert a compact log entry inside the layout-backed log panel."""
        self.log_panel.show()
        reduce_motion = getattr(getattr(self.app, "settings", None), "reduce_ui_motion", False)
        new_entry = DirectFrame(
            parent=self.log_panel.root,
            frameSize=(-0.105 * self.ui_scale, 0.105 * self.ui_scale, -0.038 * self.ui_scale, 0.038 * self.ui_scale),
            pos=(0, 0, self.layout.log_entry_top_z),
            frameColor=(0.01, 0.02, 0.04, 0.76),
            relief=DGG.FLAT,
        )
        new_entry.setTransparency(TransparencyAttrib.MAlpha)
        DirectFrame(
            parent=new_entry,
            frameSize=(-0.003 * self.ui_scale, 0.003 * self.ui_scale, -0.036 * self.ui_scale, 0.036 * self.ui_scale),
            pos=(-0.098 * self.ui_scale, 0, 0),
            frameColor=color,
            relief=DGG.FLAT,
        )
        DirectLabel(
            parent=new_entry,
            text=title[:22],
            pos=(-0.088 * self.ui_scale, 0, 0.012 * self.ui_scale),
            scale=0.0125 * self.text_scale,
            text_font=self.font,
            text_fg=color,
            text_align=TextNode.ALeft,
            relief=None,
        )
        wrapped_msg = message if len(message) <= 22 else message[:19] + "..."
        DirectLabel(
            parent=new_entry,
            text=wrapped_msg,
            pos=(-0.088 * self.ui_scale, 0, -0.014 * self.ui_scale),
            scale=0.011 * self.text_scale,
            text_font=self.font,
            text_fg=COLORS.text_secondary,
            text_align=TextNode.ALeft,
            relief=None,
        )

        entry_data = {"root": new_entry, "target_z": self.layout.log_entry_top_z, "age": 0.0}
        for index, old_entry in enumerate(self.entries):
            old_entry["target_z"] = self.layout.log_entry_top_z - ((index + 1) * self.layout.log_entry_spacing_z)
            if reduce_motion:
                old_entry["root"].setZ(old_entry["target_z"])
            else:
                old_entry["root"].posInterval(0.15, (0, 0, old_entry["target_z"]), blendType="easeInOut").start()
        self.entries.insert(0, entry_data)
        if len(self.entries) > self.max_entries:
            removed = self.entries.pop()
            removed["root"].destroy()

    def update(self, dt):
        """Age and fade old log entries."""
        for entry in list(self.entries):
            entry["age"] += dt
            if entry["age"] > 7.0:
                rem_alpha = max(0.0, 1.0 - (entry["age"] - 7.0) / 2.0)
                entry["root"].setColorScale(1, 1, 1, rem_alpha)
                if rem_alpha <= 0.05:
                    self.entries.remove(entry)
                    entry["root"].destroy()
        if not self.entries and not self.layout.show_log_when_empty:
            self.log_panel.hide()

    def show(self):
        if self.entries or self.layout.show_log_when_empty:
            self.log_panel.show()
        else:
            self.log_panel.hide()
        for entry in self.entries:
            entry["root"].show()
        if self.active_toast:
            self.active_toast.show()

    def hide(self):
        self.log_panel.hide()
        for entry in self.entries:
            entry["root"].hide()
        if self.active_toast:
            self.active_toast.hide()

    def clear(self):
        """Clean up all notification elements."""
        self._clear_active_toast()
        for entry in self.entries:
            entry["root"].destroy()
        self.entries.clear()
        self.log_panel.destroy()
        self.toast_root.destroy()


LegacyNotificationManager = NotificationManager
