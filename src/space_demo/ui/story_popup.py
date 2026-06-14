"""Panda3D/DirectGUI story popup view."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from space_demo.story_popup_runtime import StoryPopupState
from space_demo.ui.autofit import AutoFitTextSpec, clamp_frame_inside, fit_button_text, fit_text


@dataclass(frozen=True)
class StoryPopupButtonLayout:
    text: str
    pos: Tuple[float, float, float]
    frame_size: Tuple[float, float, float, float]
    text_scale: float
    wordwrap: int
    estimated_lines: int


@dataclass(frozen=True)
class StoryPopupLayout:
    frame_size: Tuple[float, float, float, float]
    title_pos: Tuple[float, float, float]
    body_pos: Tuple[float, float, float]
    title_scale: float
    title_wordwrap: int
    body_scale: float
    body_wordwrap: int
    body_estimated_lines: int
    button_layouts: Tuple[StoryPopupButtonLayout, ...]


def build_story_popup_layout(state: StoryPopupState) -> StoryPopupLayout:
    frame_size = (-1.28, 1.28, -0.70, 0.70)
    title_text = state.story_display_name if not state.speaker else f"{state.story_display_name} — {state.speaker}"
    title_fit = fit_text(
        AutoFitTextSpec(
            text=title_text,
            max_width=2.20,
            max_height=0.10,
            preferred_scale=0.048,
            min_scale=0.034,
            max_wordwrap=60,
            min_wordwrap=24,
        )
    )
    body_fit = fit_text(
        AutoFitTextSpec(
            text=state.body,
            max_width=2.18,
            max_height=0.42,
            preferred_scale=0.038,
            min_scale=0.028,
            max_wordwrap=72,
            min_wordwrap=36,
        )
    )

    button_texts = [f"{index + 1}. {choice}" for index, choice in enumerate(state.choices)]
    if not button_texts:
        button_texts = ["Continue  [Enter]"]

    max_buttons = max(1, len(button_texts))
    button_height = 0.12 if max_buttons <= 3 else 0.105
    spacing = button_height + 0.026
    start_y = -0.31 + ((max_buttons - 1) * spacing / 2.0)
    layouts: List[StoryPopupButtonLayout] = []
    for index, text in enumerate(button_texts):
        desired_z = start_y - index * spacing
        fit = fit_button_text(
            text=text,
            parent_frame=frame_size,
            desired_center_z=desired_z,
            desired_width=2.16,
            desired_height=button_height,
            preferred_scale=0.036,
            min_scale=0.024,
        )
        pos = clamp_frame_inside(frame_size, 0.0, desired_z, fit.frame_size)
        layouts.append(
            StoryPopupButtonLayout(
                text=text,
                pos=pos,
                frame_size=fit.frame_size,
                text_scale=fit.text_scale,
                wordwrap=fit.wordwrap,
                estimated_lines=fit.estimated_lines,
            )
        )

    return StoryPopupLayout(
        frame_size=frame_size,
        title_pos=(0.0, 0.0, 0.56),
        body_pos=(-1.08, 0.0, 0.37),
        title_scale=title_fit.text_scale,
        title_wordwrap=title_fit.wordwrap,
        body_scale=body_fit.text_scale,
        body_wordwrap=body_fit.wordwrap,
        body_estimated_lines=body_fit.estimated_lines,
        button_layouts=tuple(layouts),
    )


class StoryPopupView:
    """Small disposable DirectGUI story popup.

    In headless mode this class stores visibility and layout state only and
    creates no Panda3D UI objects, keeping tests windowless and deterministic.
    """

    def __init__(self, app):
        self.app = app
        self.frame = None
        self.visible = False
        self.current_state: Optional[StoryPopupState] = None
        self.last_layout: Optional[StoryPopupLayout] = None

    def show(
        self,
        state: StoryPopupState,
        on_advance: Callable[[], None],
        on_choice: Callable[[int], None],
    ) -> None:
        self.hide()
        self.visible = True
        self.current_state = state
        self.last_layout = build_story_popup_layout(state)

        if getattr(self.app, "headless", False):
            return

        from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel

        layout = self.last_layout
        self.frame = DirectFrame(
            parent=self.app.aspect2d,
            frameColor=(0.02, 0.03, 0.08, 0.96),
            frameSize=layout.frame_size,
            pos=(0.0, 0.0, 0.0),
        )

        title = state.story_display_name
        if state.speaker:
            title = f"{title} — {state.speaker}"

        DirectLabel(
            parent=self.frame,
            text=title,
            text_fg=(0.65, 0.95, 1.0, 1.0),
            text_align=0,
            text_scale=layout.title_scale,
            text_wordwrap=layout.title_wordwrap,
            frameColor=(0, 0, 0, 0),
            pos=layout.title_pos,
        )
        DirectLabel(
            parent=self.frame,
            text=state.body,
            text_fg=(0.92, 0.96, 1.0, 1.0),
            text_align=-1,
            text_scale=layout.body_scale,
            text_wordwrap=layout.body_wordwrap,
            frameColor=(0, 0, 0, 0),
            pos=layout.body_pos,
        )

        if state.choices:
            for index, button_layout in enumerate(layout.button_layouts):
                DirectButton(
                    parent=self.frame,
                    text=button_layout.text,
                    text_scale=button_layout.text_scale,
                    text_wordwrap=button_layout.wordwrap,
                    text_align=0,
                    text_fg=(1.0, 1.0, 1.0, 1.0),
                    frameColor=(0.09, 0.16, 0.28, 0.96),
                    frameSize=button_layout.frame_size,
                    pos=button_layout.pos,
                    command=on_choice,
                    extraArgs=[index],
                )
        else:
            button_layout = layout.button_layouts[0]
            DirectButton(
                parent=self.frame,
                text=button_layout.text,
                text_scale=button_layout.text_scale,
                text_wordwrap=button_layout.wordwrap,
                text_align=0,
                text_fg=(1.0, 1.0, 1.0, 1.0),
                frameColor=(0.09, 0.16, 0.28, 0.96),
                frameSize=button_layout.frame_size,
                pos=button_layout.pos,
                command=on_advance,
            )

    def hide(self) -> None:
        if self.frame is not None:
            self.frame.destroy()
            self.frame = None
        self.visible = False
        self.current_state = None

    def destroy(self) -> None:
        self.hide()
