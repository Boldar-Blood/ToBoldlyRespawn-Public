import sys
from pathlib import Path

from setuptools import setup


def _prepare_branding_assets() -> None:
    """Ensure generated icon/splash assets exist before build_apps packaging."""
    src_dir = Path(__file__).resolve().parent / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    try:
        from space_demo.startup_branding import prepare_startup_branding_assets

        prepare_startup_branding_assets()
    except Exception as exc:
        print(f"[Branding] Could not prepare generated icon assets before setup: {exc}")


_prepare_branding_assets()

setup(
    name="ToBoldlyRespawn",
    version="0.3.0a3",
    description="To Boldly Respawn: A Co-Op Space Disaster",
    options={
        "build_apps": {
            # Files to bundle into the final distributable packages
            "include_patterns": [
                "data/*.png",
                "data/*.ico",
                "data/*.wav",
                "data/*.json",
                "data/sprites/**/*.png",
                "src/space_demo/**/*.py",
                "pyproject.toml",
                "requirements.txt",
                "README.md",
                "CHANGELOG.md",
            ],
            # Main application script entry point
            "gui_apps": {
                "ToBoldlyRespawn": "src/space_demo/main.py",
            },
            # Package/window icon generated from the same logo family as the main menu.
            "icons": {
                "*": "data/game_icon.ico",
            },
            # Active engine plugins required by the rendering and audio drivers
            "plugins": [
                "pandagl",
                "p3openal_audio",
            ],
            # Desktop build platforms (Windows, macOS, Linux)
            "platforms": [
                "win_amd64",
                "manylinux2014_x86_64",
                "macosx_10_13_x86_64",
            ],
            # Console output settings
            "log_filename": "game.log",
            "log_append": False,
        }
    },
)
