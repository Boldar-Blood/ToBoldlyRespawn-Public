# Content ID utilities for To Boldly Respawn

import re

# Regex for strict lowercase snake_case IDs (starts with a letter, contains lowercase letters, digits, and underscores)
ID_REGEX = re.compile(r"^[a-z][a-z0-9_]*$")

def validate_content_id(content_id: str) -> None:
    """Validates that a content ID is a stable, non-empty, lowercase snake_case string.
    
    Raises ValueError if invalid.
    """
    if not content_id:
        raise ValueError("Content ID cannot be empty.")
    if not isinstance(content_id, str):
        raise ValueError(f"Content ID must be a string, got {type(content_id)}.")
    if not ID_REGEX.match(content_id):
        raise ValueError(
            f"Invalid content ID '{content_id}'. IDs must be non-empty, start with a letter, "
            f"and only contain lowercase letters, numbers, and underscores (strict snake_case)."
        )
