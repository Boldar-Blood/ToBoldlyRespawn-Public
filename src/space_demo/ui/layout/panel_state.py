"""Presentation-only HUD panel visibility state.

This module does not create Panda3D nodes. It models whether reusable HUD panels
should render in full, compact, or collapsed form for a given responsive layout
profile. The gameplay systems remain authoritative; hiding a panel never changes
player stats, hit boxes, scoring, timers, or enemy behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from space_demo.ui.layout.profiles import HudDensity, LayoutProfile


class HudPanel(str, Enum):
    """Reusable gameplay HUD panel identifiers."""

    TACTICAL_CONSOLE = "tactical_console"
    TACTICAL_LOG = "tactical_log"
    PURSUIT_GAUGE = "pursuit_gauge"
    PHASE_BANNER = "phase_banner"
    INTRO_MODAL = "intro_modal"
    BOSS_METER = "boss_meter"


@dataclass(frozen=True)
class HudPanelPresentation:
    """Visible/collapsed presentation state for a single panel."""

    panel: HudPanel
    visible: bool
    collapsed: bool = False
    collapsible: bool = True

    @property
    def expanded(self) -> bool:
        """Whether the panel should render in full instead of as a small affordance."""
        return self.visible and not self.collapsed


class HudPanelController:
    """Small deterministic controller for player-selectable HUD visibility.

    The controller intentionally stores only presentation state. It can be reused
    by Panda3D DirectGUI screens, smoke-test tooling, or future engine ports.
    """

    def __init__(self, profile: LayoutProfile):
        self.profile = profile
        self._states: dict[HudPanel, HudPanelPresentation] = self._build_defaults(profile)

    @staticmethod
    def _build_defaults(profile: LayoutProfile) -> dict[HudPanel, HudPanelPresentation]:
        can_collapse = profile.allow_collapsible_panels
        minimal = profile.hud_density == HudDensity.MINIMAL
        compact = profile.hud_density == HudDensity.COMPACT
        has_left_console_space = profile.left_console_width_pct > 0.0
        has_right_gauge_space = profile.right_gauge_width_pct > 0.0

        return {
            HudPanel.TACTICAL_CONSOLE: HudPanelPresentation(
                panel=HudPanel.TACTICAL_CONSOLE,
                visible=has_left_console_space and not minimal,
                collapsed=not has_left_console_space or minimal,
                collapsible=can_collapse,
            ),
            HudPanel.TACTICAL_LOG: HudPanelPresentation(
                panel=HudPanel.TACTICAL_LOG,
                visible=profile.show_log_when_empty and not minimal,
                collapsed=not profile.show_log_when_empty or compact or minimal,
                collapsible=can_collapse,
            ),
            HudPanel.PURSUIT_GAUGE: HudPanelPresentation(
                panel=HudPanel.PURSUIT_GAUGE,
                visible=has_right_gauge_space,
                collapsed=False,
                collapsible=can_collapse,
            ),
            HudPanel.PHASE_BANNER: HudPanelPresentation(
                panel=HudPanel.PHASE_BANNER,
                visible=True,
                collapsed=False,
                collapsible=can_collapse,
            ),
            HudPanel.INTRO_MODAL: HudPanelPresentation(
                panel=HudPanel.INTRO_MODAL,
                visible=True,
                collapsed=False,
                collapsible=False,
            ),
            HudPanel.BOSS_METER: HudPanelPresentation(
                panel=HudPanel.BOSS_METER,
                visible=False,
                collapsed=False,
                collapsible=False,
            ),
        }

    def state_for(self, panel: HudPanel | str) -> HudPanelPresentation:
        """Return immutable presentation state for one panel."""
        return self._states[self._normalize(panel)]

    def is_visible(self, panel: HudPanel | str) -> bool:
        """Whether a panel or its collapsed affordance should be visible."""
        return self.state_for(panel).visible

    def is_expanded(self, panel: HudPanel | str) -> bool:
        """Whether a panel should render full content."""
        return self.state_for(panel).expanded

    def set_visible(self, panel: HudPanel | str, visible: bool) -> HudPanelPresentation:
        """Set visibility while preserving collapsed state when possible."""
        current = self.state_for(panel)
        updated = HudPanelPresentation(
            panel=current.panel,
            visible=bool(visible),
            collapsed=current.collapsed if visible else True,
            collapsible=current.collapsible,
        )
        self._states[current.panel] = updated
        return updated

    def collapse(self, panel: HudPanel | str) -> HudPanelPresentation:
        """Collapse a panel to its small affordance if the active profile permits it."""
        current = self.state_for(panel)
        if not current.collapsible:
            return current
        updated = HudPanelPresentation(
            panel=current.panel,
            visible=True,
            collapsed=True,
            collapsible=current.collapsible,
        )
        self._states[current.panel] = updated
        return updated

    def expand(self, panel: HudPanel | str) -> HudPanelPresentation:
        """Expand a panel if there is enough space for it to exist on this profile."""
        current = self.state_for(panel)
        if not current.collapsible:
            return current
        updated = HudPanelPresentation(
            panel=current.panel,
            visible=True,
            collapsed=False,
            collapsible=current.collapsible,
        )
        self._states[current.panel] = updated
        return updated

    def toggle_collapsed(self, panel: HudPanel | str) -> HudPanelPresentation:
        """Toggle between expanded and collapsed presentation."""
        current = self.state_for(panel)
        return self.expand(current.panel) if current.collapsed else self.collapse(current.panel)

    def as_dict(self) -> dict[str, dict[str, bool]]:
        """Return a stable serializable snapshot for settings persistence."""
        return {
            panel.value: {
                "visible": state.visible,
                "collapsed": state.collapsed,
                "collapsible": state.collapsible,
            }
            for panel, state in self._states.items()
        }

    @staticmethod
    def _normalize(panel: HudPanel | str) -> HudPanel:
        if isinstance(panel, HudPanel):
            return panel
        return HudPanel(str(panel))
