# Profile Migration Logic for To Boldly Respawn

import copy
from typing import Dict, Any

CURRENT_SCHEMA_VERSION = 3

def migrate_profile_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrates profile data dictionary to the current schema version sequentially.
    Raises ValueError if schema_version is unsupported or missing.
    """
    if not isinstance(data, dict):
        raise ValueError("Profile data must be a dictionary.")

    if "schema_version" not in data:
        raise ValueError("Profile data is missing required field: 'schema_version'")

    version = data["schema_version"]
    if not isinstance(version, int) or version <= 0:
        raise ValueError(f"Profile schema_version must be a positive integer, got {version}")

    if version > CURRENT_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported profile schema_version: {version}. "
            f"Maximum supported version is {CURRENT_SCHEMA_VERSION}."
        )

    migrated = copy.deepcopy(data)

    # Sequentially migrate profile versions
    if version == 1:
        inventory = migrated.setdefault("inventory", {})
        inventory.setdefault("equipment", [])
        inventory.setdefault("equipped_by_ship", {})
        migrated["schema_version"] = 2
        version = 2

    if version == 2:
        progression = migrated.setdefault("progression", {})
        progression.setdefault("awarded_unique_rewards", [])
        completed_maps = progression.setdefault("completed_maps", {})
        
        if not isinstance(completed_maps, dict):
            raise ValueError("progression['completed_maps'] must be a dictionary.")

        for map_id, map_data in completed_maps.items():
            if not isinstance(map_data, dict):
                raise ValueError(
                    f"Map entry '{map_id}' in completed_maps must be a dictionary, got {type(map_data).__name__}"
                )
            
            if "completions" in map_data:
                if not isinstance(map_data["completions"], dict):
                    raise ValueError(
                        f"completions under map '{map_id}' must be a dictionary, got {type(map_data['completions']).__name__}"
                    )
                completions = copy.deepcopy(map_data["completions"])
            else:
                completions = {}
            
            completions.setdefault("easy", 0)
            completions.setdefault("medium", 0)
            completions.setdefault("hard", 0)
            
            new_map_data = copy.deepcopy(map_data)
            new_map_data["completions"] = completions
            completed_maps[map_id] = new_map_data
                
        migrated["schema_version"] = 3
        version = 3

    return migrated
