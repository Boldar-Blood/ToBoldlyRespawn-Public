# Authored Wave Configurations and Formations - To Boldly Respawn

from dataclasses import dataclass
from typing import List

@dataclass
class WaveEvent:
    time_offset: float          # Time in seconds since wave start to trigger this spawn
    enemy_type: str            # "drone", "speeder", "zigzag", "boss"
    x_positions: List[float]   # Screen horizontal positions on XZ plane
    pattern_name: str = ""     # parodied pattern name
    bark_trigger: str = ""     # category of comedy barks to fire optionally

# Author four waves representing the "Desperate Retreat" gameplay curve
WAVE_FORMATIONS = {
    # Wave 1: "Strategic Retreat 101" - gentle learning line
    1: [
        WaveEvent(time_offset=0.0, enemy_type="drone", x_positions=[-6.0, 0.0, 6.0], pattern_name="horizontal_line", bark_trigger="start"),
        WaveEvent(time_offset=5.0, enemy_type="drone", x_positions=[-3.0, 3.0], pattern_name="staggered_pair"),
        WaveEvent(time_offset=10.0, enemy_type="drone", x_positions=[-8.0, 8.0], pattern_name="flankers"),
        WaveEvent(time_offset=16.0, enemy_type="drone", x_positions=[-6.0, 0.0, 6.0], pattern_name="horizontal_line")
    ],
    
    # Wave 2: "Throw Interns Overboard!" - mixed quick flankers and area-denial mines
    2: [
        WaveEvent(time_offset=0.0, enemy_type="speeder", x_positions=[-9.0, 9.0], pattern_name="corner_speeders", bark_trigger="hit"),
        WaveEvent(time_offset=3.5, enemy_type="mine", x_positions=[-4.0, 4.0], pattern_name="filler_mines"),
        WaveEvent(time_offset=7.0, enemy_type="drone", x_positions=[-5.0, 0.0, 5.0], pattern_name="horizontal_line"),
        WaveEvent(time_offset=11.5, enemy_type="mine", x_positions=[-2.0, 2.0], pattern_name="denial_mines"),
        WaveEvent(time_offset=15.0, enemy_type="speeder", x_positions=[-8.0, 0.0, 8.0], pattern_name="corner_speeders"),
        WaveEvent(time_offset=19.0, enemy_type="drone", x_positions=[-6.0, -2.0, 2.0, 6.0], pattern_name="staggered_pursuit")
    ],
    
    # Wave 3: "Active Cowardice Engaged" - heavy zig-zag, frigate lane sweeps, and missile fire
    3: [
        WaveEvent(time_offset=0.0, enemy_type="zigzag", x_positions=[-7.0, 7.0], pattern_name="zigzag_line"),
        WaveEvent(time_offset=3.0, enemy_type="frigate", x_positions=[0.0], pattern_name="frigate_center_sweep"),
        WaveEvent(time_offset=7.5, enemy_type="speeder", x_positions=[-9.0, 9.0], pattern_name="fast_pursuit"),
        WaveEvent(time_offset=11.0, enemy_type="frigate", x_positions=[-5.0, 5.0], pattern_name="frigate_dual_sweep"),
        WaveEvent(time_offset=15.5, enemy_type="missile_boat", x_positions=[-3.0, 3.0], pattern_name="missile_barrage"),
        WaveEvent(time_offset=20.0, enemy_type="zigzag", x_positions=[-6.0, 0.0, 6.0], pattern_name="staggered_zigzag")
    ],
    
    # Wave 4: "Corporate Audit Imminent!" - boss dreadnought climax with looping escorts
    4: [
        WaveEvent(time_offset=0.0, enemy_type="boss", x_positions=[0.0], pattern_name="boss_dreadnought"),
        
        # Looping escorts (wrapped dynamically inside state manager every 60s)
        WaveEvent(time_offset=8.0, enemy_type="drone", x_positions=[-5.0, 5.0], pattern_name="boss_escort"),
        WaveEvent(time_offset=16.0, enemy_type="speeder", x_positions=[-8.0, 8.0], pattern_name="boss_escort"),
        WaveEvent(time_offset=24.0, enemy_type="mine", x_positions=[-6.0, 6.0], pattern_name="boss_escort"),
        WaveEvent(time_offset=32.0, enemy_type="frigate", x_positions=[0.0], pattern_name="boss_escort"),
        WaveEvent(time_offset=42.0, enemy_type="missile_boat", x_positions=[-4.0, 4.0], pattern_name="boss_escort"),
        WaveEvent(time_offset=52.0, enemy_type="zigzag", x_positions=[-5.0, 5.0], pattern_name="boss_escort")
    ]
}

def get_wave_events(wave_idx: int) -> List[WaveEvent]:
    """Returns the list of authored events for the requested wave level index."""
    return WAVE_FORMATIONS.get(wave_idx, [])

def get_wave_events_for_id(wave_id: str) -> List[WaveEvent]:
    """Maps wave ID string to existing WAVE_FORMATIONS while preserving integer key behavior."""
    mapping = {
        "wave_1": 1,
        "wave_2": 2,
        "wave_3": 3,
        "wave_4_boss": 4
    }
    mapped_idx = mapping.get(wave_id)
    if mapped_idx is not None:
        return get_wave_events(mapped_idx)
    if isinstance(wave_id, int):
        return get_wave_events(wave_id)
    return []
