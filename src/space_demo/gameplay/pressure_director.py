# Neutral pressure director scaffolding - To Boldly Respawn
from __future__ import annotations

from dataclasses import dataclass
from space_demo import config


BASELINE_OBSERVER_POLICY = "baseline_observer"
GAP_SOFTENER_EARLY_LOW_POLICY = "gap_softener_early_low"
SUPPORTED_PRESSURE_DIRECTOR_POLICIES = {BASELINE_OBSERVER_POLICY, GAP_SOFTENER_EARLY_LOW_POLICY}



@dataclass(frozen=True)
class PressureDirectorInputs:
    """Stable runtime inputs that a pressure director may observe."""

    difficulty: str
    player_hp: float
    max_hp: float
    chase_gap: float
    wave_index: int
    critical_gap: float
    capture_gap: float

    @property
    def hp_fraction(self) -> float:
        if self.max_hp <= 0.0:
            return 0.0
        return max(0.0, min(1.0, self.player_hp / self.max_hp))

    @property
    def inside_critical_gap(self) -> bool:
        return self.chase_gap <= self.critical_gap

    @property
    def inside_capture_gap(self) -> bool:
        return self.chase_gap <= self.capture_gap


@dataclass(frozen=True)
class PressureDirectorDecision:
    """Bounded output contract for pressure-director decisions."""

    gain_rate_multiplier: float = 1.0
    pushback_multiplier: float = 1.0
    reason: str = "baseline"

    def validate_neutral_or_bounded(self) -> None:
        if not 0.5 <= self.gain_rate_multiplier <= 1.5:
            raise ValueError("gain_rate_multiplier must stay within [0.5, 1.5]")
        if not 0.5 <= self.pushback_multiplier <= 1.5:
            raise ValueError("pushback_multiplier must stay within [0.5, 1.5]")


class PressureDirector:
    """Neutral baseline observer for future pressure-director policies.

    This class intentionally returns neutral multipliers for all supported inputs.
    It establishes a small tested contract for future live policies without changing
    current gameplay feel.
    """

    def __init__(self, policy: str = BASELINE_OBSERVER_POLICY):
        if policy not in SUPPORTED_PRESSURE_DIRECTOR_POLICIES:
            raise ValueError(
                f"Unsupported pressure director policy '{policy}'. "
                f"Supported policies: {sorted(SUPPORTED_PRESSURE_DIRECTOR_POLICIES)}"
            )
        self.policy = policy

    def decide(self, inputs: PressureDirectorInputs) -> PressureDirectorDecision:
        gain_rate_mult = 1.0
        pushback_mult = 1.0
        reason = "neutral"

        if self.policy == "gap_softener_early_low":
            if inputs.difficulty == "medium":
                threshold = getattr(config, "PRESSURE_DIRECTOR_EARLY_SOFTENER_THRESHOLD", 120.0)
                soften_mult = getattr(config, "PRESSURE_DIRECTOR_LOW_SOFTEN_MULT", 0.90)
                if inputs.chase_gap <= threshold:
                    gain_rate_mult = soften_mult
                    reason = "gap_softener_early_low:soften"
                else:
                    reason = "gap_softener_early_low:neutral"
            else:
                reason = "gap_softener_early_low:non_medium_neutral"
        else: # BASELINE_OBSERVER_POLICY
            reason = self._baseline_reason(inputs)

        decision = PressureDirectorDecision(
            gain_rate_multiplier=gain_rate_mult,
            pushback_multiplier=pushback_mult,
            reason=reason,
        )
        decision.validate_neutral_or_bounded()
        return decision

    def _baseline_reason(self, inputs: PressureDirectorInputs) -> str:
        if inputs.inside_capture_gap:
            return "baseline_observer:capture_gap"
        if inputs.inside_critical_gap:
            return "baseline_observer:critical_gap"
        if inputs.hp_fraction <= 0.25:
            return "baseline_observer:low_hp"
        return "baseline_observer:neutral"
