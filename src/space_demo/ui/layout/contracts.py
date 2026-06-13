"""Screen layout contracts and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from space_demo.ui.layout.rect import LayoutIssue, RectPct


@dataclass(frozen=True)
class ZoneSpec:
    """A named screen zone with a normalized rectangle."""

    name: str
    rect: RectPct
    purpose: str = ""


@dataclass(frozen=True)
class ScreenContract:
    """A complete layout contract for one game screen."""

    name: str
    zones: dict[str, ZoneSpec]
    reserved: dict[str, ZoneSpec] = field(default_factory=dict)
    allowed_reserved_overlaps: frozenset[str] = frozenset()


CONTRACTS: dict[str, ScreenContract] = {
    "main_menu": ScreenContract(
        name="main_menu",
        zones={
            "title": ZoneSpec("title", RectPct(0.27, 0.09, 0.50, 0.22), "title/subtitle art"),
            "nav": ZoneSpec("nav", RectPct(0.24, 0.35, 0.28, 0.36), "primary navigation"),
            "briefing": ZoneSpec("briefing", RectPct(0.52, 0.32, 0.33, 0.40), "status card"),
            "footer": ZoneSpec("footer", RectPct(0.25, 0.78, 0.58, 0.06), "optional status"),
        },
    ),
    "tactical_manual": ScreenContract(
        name="tactical_manual",
        zones={
            "title": ZoneSpec("title", RectPct(0.25, 0.10, 0.50, 0.09), "manual title"),
            "tabs": ZoneSpec("tabs", RectPct(0.31, 0.22, 0.38, 0.08), "manual tabs"),
            "content": ZoneSpec("content", RectPct(0.23, 0.32, 0.54, 0.42), "manual content"),
            "bottom_nav": ZoneSpec("bottom_nav", RectPct(0.35, 0.78, 0.30, 0.09), "return button"),
        },
    ),
    "bridge_calibration": ScreenContract(
        name="bridge_calibration",
        zones={
            "title": ZoneSpec("title", RectPct(0.30, 0.12, 0.40, 0.08), "settings title"),
            "tabs": ZoneSpec("tabs", RectPct(0.29, 0.25, 0.42, 0.08), "settings tabs"),
            "controls": ZoneSpec("controls", RectPct(0.25, 0.35, 0.50, 0.33), "settings controls"),
            "footer_buttons": ZoneSpec("footer_buttons", RectPct(0.26, 0.70, 0.48, 0.09), "apply/reset/back"),
            "note": ZoneSpec("note", RectPct(0.30, 0.82, 0.40, 0.05), "settings note"),
        },
    ),
    "gameplay_hud": ScreenContract(
        name="gameplay_hud",
        zones={
            "tactical_console": ZoneSpec("tactical_console", RectPct(0.01, 0.02, 0.18, 0.58), "left gameplay HUD"),
            "tactical_log": ZoneSpec("tactical_log", RectPct(0.21, 0.02, 0.16, 0.42), "notification log"),
            "phase_banner": ZoneSpec("phase_banner", RectPct(0.72, 0.01, 0.25, 0.08), "wave label"),
            "pursuit_gauge": ZoneSpec("pursuit_gauge", RectPct(0.90, 0.31, 0.08, 0.41), "dreadnought distance"),
            "intro_modal": ZoneSpec("intro_modal", RectPct(0.27, 0.22, 0.46, 0.43), "first-run controls"),
            "center_toast": ZoneSpec("center_toast", RectPct(0.32, 0.12, 0.36, 0.11), "temporary toast"),
        },
        reserved={
            "bottom_enemy_entry_lane": ZoneSpec("bottom_enemy_entry_lane", RectPct(0.00, 0.82, 1.00, 0.18), "bottom gameplay lane"),
            "top_center_hazard_lane": ZoneSpec("top_center_hazard_lane", RectPct(0.30, 0.00, 0.40, 0.14), "future hazards"),
        },
        allowed_reserved_overlaps=frozenset({"phase_banner", "center_toast"}),
    ),
}


def get_screen_contract(name: str) -> ScreenContract:
    """Return a named screen contract."""
    return CONTRACTS[name]


def validate_screen_layout(
    contract: ScreenContract,
    widget_rects: dict[str, RectPct],
    widget_zones: dict[str, str],
    tolerance: float = 0.004,
) -> list[LayoutIssue]:
    """Validate widgets against a screen contract."""
    issues: list[LayoutIssue] = []
    seen_pairs: set[tuple[str, str]] = set()

    for widget, rect in widget_rects.items():
        zone_name = widget_zones.get(widget)
        if not zone_name:
            issues.append(LayoutIssue("error", "missing_zone", f"{widget} has no assigned zone", widget=widget))
            continue
        zone = contract.zones.get(zone_name)
        if not zone:
            issues.append(LayoutIssue("error", "unknown_zone", f"{widget} targets unknown zone {zone_name}", widget=widget, zone=zone_name))
            continue
        if not zone.rect.contains(rect, tolerance=tolerance):
            issues.append(LayoutIssue("error", "outside_zone", f"{widget} is outside zone {zone_name}", widget=widget, zone=zone_name))

    items = list(widget_rects.items())
    for idx, (name_a, rect_a) in enumerate(items):
        zone_a = widget_zones.get(name_a)
        for name_b, rect_b in items[idx + 1 :]:
            zone_b = widget_zones.get(name_b)
            if zone_a != zone_b:
                continue
            pair = tuple(sorted((name_a, name_b)))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            if rect_a.overlaps(rect_b, tolerance=tolerance):
                issues.append(LayoutIssue("warning", "same_zone_overlap", f"{name_a} overlaps {name_b} in zone {zone_a}", widget=name_a, zone=zone_a))

    for widget, rect in widget_rects.items():
        zone_name = widget_zones.get(widget, "")
        if zone_name in contract.allowed_reserved_overlaps:
            continue
        for reserved_name, reserved_zone in contract.reserved.items():
            if rect.overlaps(reserved_zone.rect, tolerance=tolerance):
                issues.append(LayoutIssue("error", "reserved_overlap", f"{widget} overlaps reserved zone {reserved_name}", widget=widget, zone=reserved_name))

    return issues


def error_count(issues: Iterable[LayoutIssue]) -> int:
    """Count validation errors."""
    return sum(1 for issue in issues if issue.severity == "error")
