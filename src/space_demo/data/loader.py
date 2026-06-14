# Data Loader & Ingestion - To Boldly Respawn

import os
import json

def get_data_dir():
    # Resolve root relative to src package
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    return os.path.join(base_dir, "data")

def safe_load_json(filename, fallback_dict):
    """Safely loads a JSON configuration file, falling back to a default dict if missing."""
    file_path = os.path.join(get_data_dir(), filename)
    if not os.path.exists(file_path):
        print(f"[Warning] Configuration {filename} not found at {file_path}. Using robust defaults.")
        return fallback_dict
        
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Warning] Failed to parse {filename}: {e}. Using robust defaults.")
        return fallback_dict

# ----------------- Fallback Configurations -----------------

FALLBACK_SHIPS = {
  "player": {"hp": 100, "speed": 10.0, "radius": 0.5},
  "drone": {"hp": 20, "speed": 3.0, "radius": 0.4},
  "speeder": {"hp": 10, "speed": 5.0, "radius": 0.35},
  "zigzag": {"hp": 30, "speed": 2.5, "radius": 0.4},
  "boss": {"hp": 300, "speed": 0.5, "radius": 1.2},
  "mine": {"hp": 40, "speed": 1.8, "radius": 0.45},
  "frigate": {"hp": 75, "speed": 1.5, "radius": 0.9},
  "missile_boat": {"hp": 50, "speed": 1.2, "radius": 0.6}
}

FALLBACK_WEAPONS = {
  "player_laser": {"reload_time": 0.15, "speed": -20.0, "damage": 10},
  "enemy_laser": {"reload_time": 2.5, "speed": 12.0, "damage": 10},
  "player_missile": {"reload_time": 0.50, "speed": -25.0, "damage": 50},
  "player_intern_laser": {"reload_time": 0.45, "speed": -15.0, "damage": 5}
}

FALLBACK_WAVES = {
  "wave_1": {"duration": 25.0, "max_enemies": 6, "spawn_cooldown": 2.5, "escorts": ["drone"]},
  "wave_2": {"duration": 25.0, "max_enemies": 10, "spawn_cooldown": 2.0, "escorts": ["drone", "speeder"]},
  "wave_3": {"duration": 25.0, "max_enemies": 12, "spawn_cooldown": 1.5, "escorts": ["drone", "speeder", "zigzag"]},
  "wave_4_boss": {"duration": 9999.0, "max_enemies": 20, "spawn_cooldown": 3.0, "escorts": ["drone", "speeder"]}
}

FALLBACK_FLAVOR = {
  "menu": {
    "title": "TO BOLDLY RESPAWN",
    "subtitle": "A Co-Op Space Disaster",
    "slogan": "Press ENTER to engage in a Courageous Strategic Retrograde!"
  },
  "waves": {
    "wave_1": "Strategic Retreat 101",
    "wave_2": "They're Gaining, Throw the Interns Overboard!",
    "wave_3": "Active Cowardice Mode Engaged",
    "wave_4": "Middle Management Closes the Gap"
  },
  "pickups": {
    "health": "Collected 'Emergency Duct Tape'! Rear hull integrity repaired by 25.",
    "speed": "Collected 'Totally Safe Space Snack'! Weapons cooling systems boosted."
  },
  "endings": {
    "gameover": "You have boldly respawned. Command will be deducting this starship from your paycheck.",
    "victory": "Congratulations, Captain! The audit dreadnought has retreated. The disaster is now slightly further behind us."
  }
}

# ----------------- Public Ingestion APIs -----------------

def load_ships_config():
    return safe_load_json("ships.json", FALLBACK_SHIPS)

def load_weapons_config():
    return safe_load_json("weapons.json", FALLBACK_WEAPONS)

def load_waves_config():
    return safe_load_json("waves.json", FALLBACK_WAVES)

def load_flavor_config():
    return safe_load_json("flavor.json", FALLBACK_FLAVOR)
