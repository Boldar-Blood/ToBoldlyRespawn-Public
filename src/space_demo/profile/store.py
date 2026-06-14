# Profile Store persistence for To Boldly Respawn

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Union, Optional
from space_demo.data.loader import get_data_dir
from space_demo.domain.profile import PlayerProfile
from space_demo.profile.migration import migrate_profile_data, CURRENT_SCHEMA_VERSION

def get_default_profile_save_path() -> Path:
    """Return the per-user profile path for the current platform following project conventions."""
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "ToBoldlyRespawn" / "profile.json"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "ToBoldlyRespawn" / "profile.json"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "ToBoldlyRespawn" / "profile.json"

class ProfileStore:
    """Handles loading, saving, initialization, and validation of the PlayerProfile."""

    def __init__(
        self,
        profile_path: Optional[Union[Path, str]] = None,
        default_profile_path: Optional[Union[Path, str]] = None,
    ):
        self.profile_path = Path(profile_path) if profile_path else get_default_profile_save_path()
        if default_profile_path:
            self.default_profile_path = Path(default_profile_path)
        else:
            self.default_profile_path = Path(get_data_dir()) / "default_profile.json"

    def load_profile(self) -> PlayerProfile:
        """
        Loads the player profile from the configured save path.
        - If the file does not exist, it initializes from the default_profile.json, saves it, and returns it.
        - If the file exists but is invalid JSON, missing schema version, or fails validation,
          raises a clear ValueError without modifying/overwriting/deleting the file.
        """
        if not self.profile_path.exists():
            # Initialize from default profile
            if not self.default_profile_path.exists():
                raise FileNotFoundError(
                    f"Default profile template not found at: {self.default_profile_path}"
                )
            try:
                with open(self.default_profile_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
            except Exception as e:
                raise ValueError(
                    f"Failed to parse default profile template JSON: {e}"
                ) from e

            # Parse and validate the default profile
            try:
                profile = PlayerProfile.from_dict(raw_data, strict=True)
                profile.validate(strict=True)
            except Exception as e:
                raise ValueError(
                    f"Default profile template failed validation check: {e}"
                ) from e

            # Save newly initialized profile
            self.save_profile(profile)
            return profile

        # Read existing profile file
        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                content = f.read()
            if not content.strip():
                raise ValueError("Profile file is empty.")
            raw_data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse profile JSON at {self.profile_path}: {e}. "
                "Ensure the JSON file structure is correct and not corrupted."
            ) from e
        except Exception as e:
            raise ValueError(
                f"Error reading profile file at {self.profile_path}: {e}"
            ) from e

        if not isinstance(raw_data, dict):
            raise ValueError(
                f"Invalid profile file content at {self.profile_path}: Root must be a JSON object."
            )

        # Run schema migrations
        try:
            migrated_data = migrate_profile_data(raw_data)
        except Exception as e:
            raise ValueError(
                f"Failed to migrate profile data at {self.profile_path}: {e}"
            ) from e

        # Convert to domain model and validate
        try:
            profile = PlayerProfile.from_dict(migrated_data, strict=True)
            profile.validate(strict=True)
        except Exception as e:
            raise ValueError(
                f"Profile at {self.profile_path} is invalid: {e}"
            ) from e

        return profile

    def save_profile(self, profile: PlayerProfile) -> None:
        """
        Saves the PlayerProfile to the configured save path.
        Validates the profile object before writing.
        """
        if not isinstance(profile, PlayerProfile):
            raise TypeError("Expected a PlayerProfile domain object.")
        
        # Ensure it passes validation before writing
        profile.validate(strict=True)

        if profile.schema_version != CURRENT_SCHEMA_VERSION:
            raise ValueError(
                f"Cannot save profile schema_version {profile.schema_version}; "
                f"expected current schema_version {CURRENT_SCHEMA_VERSION}."
            )

        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "schema_version": profile.schema_version,
            "selected_ship_id": profile.selected_ship_id,
            "unlocked_ships": list(profile.unlocked_ships),
            "inventory": dict(profile.inventory),
            "progression": dict(profile.progression),
        }
        
        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
