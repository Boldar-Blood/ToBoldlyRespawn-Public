from __future__ import annotations

import os
import json
import uuid
import re
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import urllib.parse
import webbrowser

from space_demo import __version__ as APP_VERSION
from space_demo.core.state import GameStateManager


# Banned PII keywords/patterns for safety checks
BANNED_TELEMETRY_KEYWORDS = {
    "username",
    "os_user",
    "ip_address",
    "email",
    "machine_id",
    "path",
    "token",
    "secret",
    "api_key"
}


def redact_sensitive_patterns(text: str) -> str:
    """Lightweight redaction helper for obvious accidental sensitive patterns (emails, paths)."""
    if not text:
        return text

    # Redact email addresses
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    text = re.sub(email_pattern, "[REDACTED EMAIL]", text)

    # Redact Windows paths (e.g. C:\Users\...)
    win_path_pattern = r'[a-zA-Z]:\\[\\\w\s.-]+'
    text = re.sub(win_path_pattern, "[REDACTED PATH]", text)

    # Redact Unix paths (e.g. /home/user/...)
    unix_path_pattern = r'/(?:[\w.-]+/)+[\w.-]+'
    text = re.sub(unix_path_pattern, "[REDACTED PATH]", text)

    return text


@dataclass
class PlaytestSessionSummary:
    schema_version: str = "phase3x-playtest-session-v1"
    app_version: str = APP_VERSION
    session_id: str = ""
    timestamp_utc: str = ""
    difficulty: str = "medium"
    map_id: str = "unknown"
    ship_id: str = "unknown"
    wave_index: int = 1
    max_wave_reached: int = 1
    survival_time: float = 0.0
    result: str = "unknown"  # win, loss, quit, unknown
    player_hp_end: float = 0.0
    max_hull: float = 100.0
    final_chase_gap: float = 200.0
    min_chase_gap: float = 200.0
    time_inside_critical_gap: float = 0.0
    capture_gap_used: float = 5.0
    pressure_director_policy: str = "baseline_observer"
    last_pressure_director_decision_reason: str = "unknown"
    gain_rate_multiplier: float = 1.0
    pushback_distance_applied: float = 0.0
    raw_chase_closure_distance: float = 0.0
    warnings_count: int = 0
    boss_active: bool = False
    boss_phase_reached: int = 0
    boss_result: str = "none" # none, win, loss, unknown
    freeform_player_feedback: str = ""

    def __post_init__(self):
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        if not self.timestamp_utc:
            self.timestamp_utc = datetime.now(timezone.utc).isoformat()
        
        # Clean feedback
        self.freeform_player_feedback = redact_sensitive_patterns(self.freeform_player_feedback)

    def to_dict(self) -> Dict[str, Any]:
        """Returns serialized dictionary while strictly excluding any forbidden PII/secrets."""
        data = asdict(self)
        clean_data = {}
        for k, v in data.items():
            if any(forbidden in k.lower() for forbidden in BANNED_TELEMETRY_KEYWORDS):
                continue
            if isinstance(v, str):
                clean_data[k] = redact_sensitive_patterns(v)
            else:
                clean_data[k] = v
        return clean_data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_markdown(self) -> str:
        d = self.to_dict()
        lines = [
            f"# To Boldly Respawn - Playtest Report",
            "*(Please review and ensure no personal or sensitive information is included below before submitting.)*",
            "",
            f"**Session ID**: `{d.get('session_id', '')}`",
            f"**Timestamp (UTC)**: {d.get('timestamp_utc', '')}",
            f"**App Version**: {d.get('app_version', '')}",
            f"**Schema Version**: `{d.get('schema_version', '')}`",
            "",
            "## Session Settings",
            f"* **Difficulty**: {d.get('difficulty', '')}",
            f"* **Map ID**: {d.get('map_id', '')}",
            f"* **Ship ID**: {d.get('ship_id', '')}",
            "",
            "## Match Outcomes",
            f"* **Result**: {d.get('result', '')}",
            f"* **Max Wave Reached**: {d.get('max_wave_reached', 1)} (Final Wave Index: {d.get('wave_index', 1)})",
            f"* **Survival Time**: {d.get('survival_time', 0.0):.2f}s",
            f"* **Final Player HP**: {d.get('player_hp_end', 0.0)} / {d.get('max_hull', 100.0)}",
            "",
            "## Chase & Proximity Metrics",
            f"* **Final Chase Gap**: {d.get('final_chase_gap', 0.0):.2f} units (Capture Gap: {d.get('capture_gap_used', 5.0)} units)",
            f"* **Minimum Chase Gap**: {d.get('min_chase_gap', 0.0):.2f} units",
            f"* **Time inside Critical Gap**: {d.get('time_inside_critical_gap', 0.0):.2f}s",
            f"* **Raw Closure Distance**: {d.get('raw_chase_closure_distance', 0.0):.2f} units",
            f"* **Total Pushback Distance Applied**: {d.get('pushback_distance_applied', 0.0):.2f} units",
            "",
            "## Pressure Director Telemetry",
            f"* **Policy**: {d.get('pressure_director_policy', '')}",
            f"* **Last Decision Reason**: {d.get('last_pressure_director_decision_reason', '')}",
            f"* **Last Gain Rate Multiplier**: {d.get('gain_rate_multiplier', 1.0):.3f}",
            "",
            "## Boss Performance",
            f"* **Boss Active**: {d.get('boss_active', False)}",
            f"* **Boss Phase Reached**: {d.get('boss_phase_reached', 0)}",
            f"* **Boss Result**: {d.get('boss_result', 'none')}",
            "",
            "## Player Feedback",
            f"```text\n{d.get('freeform_player_feedback', '') or 'No feedback entered.'}\n```"
        ]
        return "\n".join(lines)

    def write_local_files(self, output_dir: str = "artifacts/playtest_feedback") -> tuple[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        json_path = os.path.join(output_dir, f"playtest_session_{self.session_id}.json")
        md_path = os.path.join(output_dir, f"playtest_feedback_{self.session_id}.md")
        
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self.to_markdown())
            
        return json_path, md_path

    def generate_github_issue_url(self, repo: str = "Boldar-Blood/ToBoldlyRespawn-Public") -> str:
        body_content = (
            "Please review the session telemetry below, add any comments/feedback under the "
            "'Player Feedback' section, and submit this issue to help us tune difficulty!\n\n"
            f"{self.to_markdown()}"
        )
        base_url = f"https://github.com/{repo}/issues/new"
        params = {
            "title": f"Playtest Feedback - {self.session_id}",
            "body": body_content
        }
        query = urllib.parse.urlencode(params)
        full_url = f"{base_url}?{query}"
        
        if len(full_url) > 2000:
            short_body = (
                "Your playtest report has been saved locally because it exceeds the GitHub URL limit.\n\n"
                f"Please open the markdown report file at:\n"
                f"`artifacts/playtest_feedback/playtest_feedback_{self.session_id}.md`\n"
                "Copy its contents and paste them here.\n\n"
                "Add any additional comments/feedback under the 'Player Feedback' section. Thank you!"
            )
            params = {
                "title": f"Playtest Feedback - {self.session_id}",
                "body": short_body
            }
            query = urllib.parse.urlencode(params)
            full_url = f"{base_url}?{query}"
            
        return full_url

    def open_github_feedback_form(self, repo: str = "Boldar-Blood/ToBoldlyRespawn-Public") -> None:
        url = self.generate_github_issue_url(repo)
        webbrowser.open(url)


def create_session_summary(
    state_mgr: GameStateManager,
    result: str = "unknown",
    freeform_feedback: str = ""
) -> PlaytestSessionSummary:
    """Defensively constructs a PlaytestSessionSummary from a GameStateManager instance."""
    # Normalize result
    result_lower = str(result).lower().strip()
    if result_lower in ("win", "victory"):
        normalized_result = "win"
    elif result_lower in ("loss", "defeat", "gameover"):
        normalized_result = "loss"
    elif result_lower in ("quit", "exit"):
        normalized_result = "quit"
    else:
        normalized_result = "unknown"

    # Safely query attributes via getattr/defaults
    difficulty = getattr(state_mgr, "difficulty", "medium")
    wave_index = getattr(state_mgr, "wave_index", 1)
    survival_time = getattr(state_mgr, "survival_time", 0.0)
    player_hp = getattr(state_mgr, "player_hp", 0.0)
    max_hull = getattr(state_mgr, "max_hull", 100.0)
    chase_gap = getattr(state_mgr, "chase_gap", 200.0)

    # Safe capture gap query
    try:
        capture_gap = state_mgr.effective_capture_gap()
    except AttributeError:
        capture_gap = 5.0

    # Map ID
    map_id = "unknown"
    map_def = getattr(state_mgr, "_map_def", None)
    if map_def:
        map_id = getattr(map_def, "id", "unknown")

    # Ship ID
    ship_id = "unknown"
    ship_def = getattr(state_mgr, "_ship_def", None)
    if ship_def:
        ship_id = getattr(ship_def, "id", "unknown")

    # Ledger queries
    chase_pressure_ledger = getattr(state_mgr, "chase_pressure_ledger", None)
    time_inside_critical_gap = 0.0
    pushback_distance_applied = 0.0
    raw_chase_closure_distance = 0.0
    min_chase_gap = chase_gap
    
    if isinstance(chase_pressure_ledger, dict):
        time_inside_critical_gap = chase_pressure_ledger.get("critical_gap_time", 0.0)
        pushback_distance_applied = chase_pressure_ledger.get("pushback_distance_applied", 0.0)
        raw_chase_closure_distance = chase_pressure_ledger.get("raw_chase_closure_distance", 0.0)
        
        lowest_gaps = chase_pressure_ledger.get("lowest_gap_by_wave", {})
        if isinstance(lowest_gaps, dict) and lowest_gaps:
            lowest_vals = [v for v in lowest_gaps.values() if isinstance(v, (int, float))]
            if lowest_vals:
                min_chase_gap = min(lowest_vals)

    # Director queries
    director = getattr(state_mgr, "pressure_director", None)
    policy_name = "baseline_observer"
    if director:
        policy_name = getattr(director, "policy", "baseline_observer")

    last_decision = getattr(state_mgr, "last_pressure_director_decision", None)
    last_reason = "unknown"
    gain_mult = 1.0
    if last_decision:
        last_reason = getattr(last_decision, "reason", "unknown")
        gain_mult = getattr(last_decision, "gain_rate_multiplier", 1.0)

    # Boss queries
    boss_active = getattr(state_mgr, "boss_active", False)
    boss_phase = 0
    boss_result = "none"
    if boss_active:
        boss_result = "unknown"
        if normalized_result == "win":
            boss_result = "win"
        elif normalized_result == "loss":
            boss_result = "loss"

    # Boss phase determination from active enemies list
    enemies = getattr(state_mgr, "enemies", [])
    if isinstance(enemies, list):
        for enemy in enemies:
            enemy_type = getattr(enemy, "enemy_type", None)
            if enemy_type == "boss":
                boss_phase = max(boss_phase, getattr(enemy, "boss_phase", 1))

    return PlaytestSessionSummary(
        difficulty=difficulty,
        map_id=map_id,
        ship_id=ship_id,
        wave_index=wave_index,
        max_wave_reached=wave_index,
        survival_time=survival_time,
        result=normalized_result,
        player_hp_end=player_hp,
        max_hull=max_hull,
        final_chase_gap=chase_gap,
        min_chase_gap=min_chase_gap,
        time_inside_critical_gap=time_inside_critical_gap,
        capture_gap_used=capture_gap,
        pressure_director_policy=policy_name,
        last_pressure_director_decision_reason=last_reason,
        gain_rate_multiplier=gain_mult,
        pushback_distance_applied=pushback_distance_applied,
        raw_chase_closure_distance=raw_chase_closure_distance,
        boss_active=boss_active,
        boss_phase_reached=boss_phase,
        boss_result=boss_result,
        freeform_player_feedback=freeform_feedback
    )
