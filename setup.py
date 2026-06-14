from setuptools import setup

setup(
    name="ToBoldlyRespawn",
    version="0.2.0a2",
    description="To Boldly Respawn: A Co-Op Space Disaster",
    options={
        "build_apps": {
            # Files to bundle into the final distributable packages
            "include_patterns": [
                "data/*.png",
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
