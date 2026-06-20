"""Phase 3x Chase-Pressure Tuning Proposal.

This module provides a structured, machine-readable representation of the proposed
chase-pressure tuning adjustments. This is an advisory-only artifact. It does NOT
apply any gameplay balance modifications and must NOT be imported by runtime gameplay systems.
"""

APPLIES_GAMEPLAY_CHANGES = False

# Structured proposal data for calibration review/automation checks
PROPOSAL_DATA = {
    "title": "Phase 3x Chase-Pressure Tuning Proposal",
    "version": "0.3.1",
    "advisory_only": True,
    "human_approval_required": True,
    "recommended_experiment": {
        "pr_number": 48,
        "description": "Increase base/medium dreadnought gain rate from 2.2 to 2.5 units/second",
        "levers": [
            {
                "name": "DREADNOUGHT_GAIN_RATE",
                "scope": "medium",
                "current_value": 2.2,
                "proposed_value": 2.5,
                "type": "constant",
                "expected_effect": "Increases chase pressure on Medium; win rate decays towards 55-70% band; Avg Critical Gap Time rises above 0.0s.",
                "risks": "Overshooting makes Medium difficulty unplayable; player captured too quickly.",
                "difficulty_specific": False
            }
        ],
        "rollback_steps": [
            "Revert DREADNOUGHT_GAIN_RATE in src/space_demo/config.py back to 2.2"
        ],
        "target_scenarios": [
            ("easy_skill", "easy"),
            ("medium_skill", "medium"),
            ("hard_skill", "hard")
        ]
    },
    "broader_follow_up_candidates": [
        {
            "name": "easy_chase_gain_rate",
            "scope": "easy",
            "current_value": 1.2,
            "proposed_value": 1.5,
            "type": "code_inline",
            "expected_effect": "Increases chase pressure on Easy difficulty; win rate decays towards 70-85% band.",
            "risks": "High risk for newer/casual players.",
            "difficulty_specific": True
        },
        {
            "name": "hard_chase_gain_rate",
            "scope": "hard",
            "current_value": 3.0,
            "proposed_value": 3.5,
            "type": "code_inline",
            "expected_effect": "Increases chase pressure on Hard difficulty; win rate decays towards 45-60% band.",
            "risks": "High risk of overwhelm when combined with hard-spawn pacing.",
            "difficulty_specific": True
        }
    ],
    "deferred_levers": [
        {
            "name": "DREADNOUGHT_PUSH_BACK",
            "current_value": 12.0,
            "expected_effect": "Lowering gives less relief distance per kill; raising gives more breathing room.",
            "deferred_reason": "Defer pushback adjustments until gain rate baseline is established."
        },
        {
            "name": "DREADNOUGHT_CRITICAL_GAP",
            "current_value": 25.0,
            "deferred_reason": "Cosmetic alert timing only; does not affect physical pressure."
        },
        {
            "name": "DREADNOUGHT_CAPTURE_GAP",
            "current_value": 5.0,
            "deferred_reason": "Directly affects visual/spatial gameover alignment; high regression risk."
        }
    ]
}
