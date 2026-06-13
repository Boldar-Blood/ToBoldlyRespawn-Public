"""Presentation audio manager for procedural music and sound effects."""

from __future__ import annotations

import logging
import os
import random

from panda3d.core import Filename

LOGGER = logging.getLogger(__name__)


class AudioManager:
    """Load procedural audio and apply persistent volume/mute settings."""

    def __init__(self, app):
        self.app = app
        self.headless = app.headless

        self.laser_sfx = None
        self.missile_sfx = None
        self.explosion_sfx = None
        self.pickup_sfx = None
        self.alarm_sfx = None

        self.menu_music = None
        self.chase_music = None

        self.master_volume = 0.85
        self.music_volume = 0.65
        self.sfx_volume = 0.85
        self.master_muted = False
        self.music_muted = False
        self.sfx_muted = False

        self.initialize_audio()

    def effective_music_volume(self) -> float:
        """Return effective music volume after master/music mute routing."""
        if self.master_muted or self.music_muted:
            return 0.0
        return self.master_volume * self.music_volume

    def effective_sfx_volume(self) -> float:
        """Return effective SFX volume after master/SFX mute routing."""
        if self.master_muted or self.sfx_muted:
            return 0.0
        return self.master_volume * self.sfx_volume

    def _configure_music_tracks(self) -> None:
        """Apply looping and volume to both music tracks.

        Persistent settings are loaded during startup, so looping must be applied
        whenever track volume is configured rather than only in fallback startup
        paths.
        """
        music_vol = self.effective_music_volume()
        for track in (self.menu_music, self.chase_music):
            if track:
                track.setLoop(True)
                track.setVolume(music_vol)

    def apply_volume_settings(self, settings) -> None:
        """Update volume settings and propagate them to active music tracks."""
        self.master_volume = settings.master_volume
        self.music_volume = settings.music_volume
        self.sfx_volume = settings.sfx_volume
        self.master_muted = settings.master_muted
        self.music_muted = settings.music_muted
        self.sfx_muted = settings.sfx_muted
        self._configure_music_tracks()

    def initialize_audio(self) -> None:
        """Generate, load, and configure procedural audio assets."""
        try:
            data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))

            from space_demo.core.procedural_audio import generate_all_audio

            generate_all_audio()

            self.laser_sfx = self.app.loader.loadSfx(Filename.fromOsSpecific(os.path.join(data_dir, "laser.wav")))
            self.missile_sfx = self.app.loader.loadSfx(Filename.fromOsSpecific(os.path.join(data_dir, "missile.wav")))
            self.explosion_sfx = self.app.loader.loadSfx(Filename.fromOsSpecific(os.path.join(data_dir, "explosion.wav")))
            self.pickup_sfx = self.app.loader.loadSfx(Filename.fromOsSpecific(os.path.join(data_dir, "pickup.wav")))
            self.alarm_sfx = self.app.loader.loadSfx(Filename.fromOsSpecific(os.path.join(data_dir, "alarm.wav")))

            self.menu_music = self.app.loader.loadMusic(Filename.fromOsSpecific(os.path.join(data_dir, "menu_music.wav")))
            self.chase_music = self.app.loader.loadMusic(Filename.fromOsSpecific(os.path.join(data_dir, "chase_music.wav")))

            if hasattr(self.app, "settings") and self.app.settings:
                self.apply_volume_settings(self.app.settings)
            else:
                self._configure_music_tracks()

            if not self.headless and self.menu_music:
                self.menu_music.play()

            LOGGER.info("Procedural chiptunes and SFX loaded successfully.")
        except Exception as exc:  # pragma: no cover - depends on local audio drivers.
            LOGGER.warning("Audio manager failed to initialize; running without audio: %s", exc)

    def play_sound(self, sfx) -> None:
        """Play a sound effect through the persisted SFX/master volume route."""
        if self.headless or not sfx:
            return
        vol = self.effective_sfx_volume()
        if vol <= 0.0:
            return
        try:
            if hasattr(sfx, "setVolume"):
                sfx.setVolume(vol)
            sfx.setPlayRate(random.uniform(0.95, 1.05))
            sfx.play()
        except Exception:
            try:
                if hasattr(sfx, "setVolume"):
                    sfx.setVolume(vol)
                sfx.play()
            except Exception:
                LOGGER.debug("Failed to play SFX", exc_info=True)
