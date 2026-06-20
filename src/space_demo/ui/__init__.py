"""UI package exports for To Boldly Respawn.

Runtime implementations live in their canonical modules. Importing this package
must not monkey-patch screen classes; the screen controller owns its behavior
directly.
"""

from __future__ import annotations

from space_demo.ui.screens import GameMenuScreens

__all__ = ["GameMenuScreens"]
