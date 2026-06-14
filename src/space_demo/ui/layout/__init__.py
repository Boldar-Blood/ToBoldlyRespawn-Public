"""Layout primitives and validation for To Boldly Respawn UI."""

from space_demo.ui.layout.rect import Rect, RectPct, LayoutIssue
from space_demo.ui.layout.contracts import get_screen_contract, validate_screen_layout
from space_demo.ui.layout.runtime import ScreenRuntimeLayout, RuntimeWidgetLayout, build_runtime_layout
from space_demo.ui.layout.viewport import SafeAreaPx, ViewportContext
from space_demo.ui.layout.profiles import HudDensity, LayoutProfile, LayoutProfileName, choose_layout_profile
from space_demo.ui.layout.panel_state import HudPanel, HudPanelController, HudPanelPresentation
from space_demo.ui.layout.panda3d_adapter import Panda3DUiLayoutContext, viewport_from_app

__all__ = [
    "Rect",
    "RectPct",
    "LayoutIssue",
    "get_screen_contract",
    "validate_screen_layout",
    "ScreenRuntimeLayout",
    "RuntimeWidgetLayout",
    "build_runtime_layout",
    "SafeAreaPx",
    "ViewportContext",
    "HudDensity",
    "LayoutProfile",
    "LayoutProfileName",
    "choose_layout_profile",
    "HudPanel",
    "HudPanelController",
    "HudPanelPresentation",
    "Panda3DUiLayoutContext",
    "viewport_from_app",
]
