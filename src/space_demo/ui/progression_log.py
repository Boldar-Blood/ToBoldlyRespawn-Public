"""Headless-safe DirectGUI progression log view for Phase 5H."""

from __future__ import annotations

from typing import Callable, Optional

from space_demo.progression_log_runtime import ProgressionLogState


class ProgressionLogView:
    """Small read-only progression log overlay.

    Headless mode stores visibility and state only, creating no Panda3D UI
    objects.  This keeps tests deterministic and avoids presentation dependency
    in pure progression-log tests.
    """

    def __init__(self, app):
        self.app = app
        self.frame = None
        self.visible = False
        self.current_state: Optional[ProgressionLogState] = None

    def show(self, state: ProgressionLogState, on_close: Callable[[], None]) -> None:
        self.hide()
        self.visible = True
        self.current_state = state

        if getattr(self.app, "headless", False):
            return

        from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel

        self.frame = DirectFrame(
            parent=self.app.aspect2d,
            frameColor=(0.015, 0.02, 0.055, 0.96),
            frameSize=(-1.25, 1.25, -0.68, 0.68),
            pos=(0.0, 0.0, 0.0),
        )

        DirectLabel(
            parent=self.frame,
            text="Progress Log",
            text_fg=(0.65, 0.95, 1.0, 1.0),
            text_align=0,
            text_scale=0.062,
            frameColor=(0, 0, 0, 0),
            pos=(0.0, 0.0, 0.56),
        )

        body_text = "\n".join(state.to_lines())
        DirectLabel(
            parent=self.frame,
            text=body_text,
            text_fg=(0.92, 0.96, 1.0, 1.0),
            text_align=-1,
            text_scale=0.036,
            text_wordwrap=62,
            frameColor=(0, 0, 0, 0),
            pos=(-1.08, 0.0, 0.43),
        )

        DirectButton(
            parent=self.frame,
            text="Close  [L / Escape]",
            text_scale=0.044,
            text_fg=(1.0, 1.0, 1.0, 1.0),
            frameColor=(0.09, 0.16, 0.28, 0.96),
            frameSize=(-0.45, 0.45, -0.055, 0.055),
            pos=(0.0, 0.0, -0.58),
            command=on_close,
        )

    def hide(self) -> None:
        if self.frame is not None:
            self.frame.destroy()
            self.frame = None
        self.visible = False
        self.current_state = None

    def destroy(self) -> None:
        self.hide()
