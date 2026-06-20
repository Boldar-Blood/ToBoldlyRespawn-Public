"""Helpers for exporting UI layout reports for visual QA."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from space_demo.ui.layout.rect import LayoutIssue, RectPct


@dataclass
class WidgetLayoutRecord:
    """Serializable widget rectangle record."""

    name: str
    zone: str
    rect: RectPct
    kind: str = "widget"
    text: str = ""

    def to_json(self) -> dict:
        """Return a JSON-serializable dictionary."""
        data = asdict(self)
        data["rect"] = asdict(self.rect)
        return data


class LayoutReporter:
    """Collect widget layout records and validation issues."""

    def __init__(self, screen_name: str):
        self.screen_name = screen_name
        self.records: list[WidgetLayoutRecord] = []
        self.issues: list[LayoutIssue] = []

    def add_widget(self, name: str, zone: str, rect: RectPct, kind: str = "widget", text: str = "") -> None:
        """Record a widget rectangle."""
        self.records.append(WidgetLayoutRecord(name=name, zone=zone, rect=rect, kind=kind, text=text))

    def add_issues(self, issues: list[LayoutIssue]) -> None:
        """Append validation issues."""
        self.issues.extend(issues)

    def as_dict(self) -> dict:
        """Return the report as plain JSON data."""
        return {
            "screen": self.screen_name,
            "widgets": [record.to_json() for record in self.records],
            "issues": [asdict(issue) for issue in self.issues],
        }

    def write_json(self, path: Path) -> None:
        """Write the report to JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.as_dict(), indent=2), encoding="utf-8")
