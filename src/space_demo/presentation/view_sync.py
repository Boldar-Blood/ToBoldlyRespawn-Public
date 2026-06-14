"""Synchronize gameplay simulation models with Panda3D presentation nodes."""

from __future__ import annotations

import math
import random

from panda3d.core import NodePath, TransparencyAttrib

from space_demo.presentation.actor_orientation import (
    enemy_roll_from_motion,
    enemy_turns_with_movement,
    smooth_roll,
)

from space_demo import config
from space_demo.presentation.enemy_trails import spawn_enemy_engine_trail
from space_demo.presentation.primitives import (
    create_boss_dreadnought_geom,
    create_chaser_drone_geom,
    create_laser_geom,
    create_missile_geom,
    create_pickup_geom,
)


def pickup_type_for_view(pickup) -> str:
    """Return the pickup type used by presentation rendering."""
    if hasattr(pickup, "pickup_type"):
        return pickup.pickup_type
    if hasattr(pickup, "kind"):
        return pickup.kind
    raise AttributeError("Pickup presentation requires pickup_type or kind")


class ViewSyncManager:
    """Map pure-Python gameplay models to lightweight Panda3D visuals."""

    def __init__(self, app):
        self.app = app
        self.headless = app.headless

        self.enemy_views = app.enemy_views
        self.projectile_views = app.projectile_views
        self.pickup_views = app.pickup_views

        self.prev_enemies_count = 0
        self.prev_pickups_count = 0
        self.prev_pickup_hp = config.PLAYER_START_HP
        self.prev_hit_hp = config.PLAYER_START_HP
        self.prev_missiles = config.INITIAL_MISSILES
        self.prev_fire_rate = 1.0
        # Backward-compatible attribute name for older debug tooling.
        self.prev_player_hp = config.PLAYER_START_HP

        self.player_flash_timer = 0.0

    def _maybe_set_texture(self, node, texture) -> None:
        """Set a texture only when a generated/loaded texture exists."""
        if texture is not None:
            node.setTexture(texture)

    def _enemy_texture(self, enemy_type: str):
        """Return the generated enemy texture matching the current enemy class."""
        assets = self.app.assets_mgr
        mapping = {
            "boss": getattr(assets, "boss_phase_1_tex", None),
            "speeder": getattr(assets, "enemy_speeder_tex", None),
            "zigzag": getattr(assets, "enemy_zigzag_tex", None),
            "frigate": getattr(assets, "enemy_frigate_tex", None),
            "missile_boat": getattr(assets, "enemy_missile_boat_tex", None),
            "mine": getattr(assets, "enemy_mine_tex", None),
            "drone": getattr(assets, "enemy_drone_tex", None),
        }
        return mapping.get(enemy_type) or getattr(assets, "enemy_drone_tex", None) or getattr(assets, "drone_tex", None)

    def _boss_phase_texture(self, phase: int):
        """Return the generated dreadnought phase texture with safe fallbacks."""
        assets = self.app.assets_mgr
        if phase == 1:
            return getattr(assets, "boss_phase_1_tex", None) or getattr(assets, "boss_tex", None)
        if phase == 2:
            return getattr(assets, "boss_phase_2_tex", None) or getattr(assets, "boss_phase_1_tex", None)
        return getattr(assets, "boss_phase_3_tex", None) or getattr(assets, "boss_phase_2_tex", None)

    def _apply_enemy_orientation(self, enemy, node) -> None:
        """Rotate enemy presentation toward recent movement without gameplay impact."""
        prev_x = getattr(enemy, "_prev_view_x", enemy.x)
        prev_y = getattr(enemy, "_prev_view_y", enemy.y)
        dx = enemy.x - prev_x
        dy = enemy.y - prev_y

        enemy._prev_view_x = enemy.x
        enemy._prev_view_y = enemy.y

        if not enemy_turns_with_movement(
            enemy.enemy_type,
            getattr(enemy, "visual_turns_with_movement", None),
        ):
            node.setR(0.0)
            enemy._visual_roll = 0.0
            return

        target_roll = enemy_roll_from_motion(dx, dy)
        current_roll = getattr(enemy, "_visual_roll", node.getR())
        next_roll = smooth_roll(current_roll, target_roll, 0.35)

        node.setR(next_roll)
        enemy._visual_roll = next_roll

    def sync_views(self):
        """Create, update, and remove NodePaths for active simulation objects."""
        if not self.headless:
            curr_enemies = len(self.app.state_mgr.enemies)
            if curr_enemies < self.prev_enemies_count:
                self.app.play_sound(self.app.audio_mgr.explosion_sfx)
            self.prev_enemies_count = curr_enemies

            curr_pickups = len(self.app.state_mgr.pickups)
            if curr_pickups < self.prev_pickups_count:
                if (
                    self.app.state_mgr.player_hp > self.prev_pickup_hp
                    or self.app.state_mgr.missile_ammo > self.prev_missiles
                    or self.app.player.fire_rate_multiplier > self.prev_fire_rate
                ):
                    self.app.play_sound(self.app.audio_mgr.pickup_sfx)
            self.prev_pickups_count = curr_pickups
            self.prev_pickup_hp = self.app.state_mgr.player_hp
            self.prev_missiles = self.app.state_mgr.missile_ammo
            self.prev_fire_rate = self.app.player.fire_rate_multiplier
            self.prev_player_hp = self.app.state_mgr.player_hp

        self._sync_projectiles()
        self._sync_player_damage_feedback()
        self._sync_enemies()
        self._sync_pickups()

    def _sync_projectiles(self) -> None:
        active_projs = set(self.app.state_mgr.projectiles)
        for proj in active_projs:
            if proj not in self.projectile_views:
                if proj.proj_type in ("missile", "homing_missile"):
                    geom = create_missile_geom()
                else:
                    geom = create_laser_geom(is_player=proj.is_player_owned)

                np = NodePath(geom)
                np.reparentTo(self.app.render)
                np.setTwoSided(True)
                np.setLightOff()
                np.setTransparency(TransparencyAttrib.MAlpha)
                np.setDepthWrite(False)

                if proj.proj_type in ("missile", "homing_missile"):
                    self._maybe_set_texture(np, self.app.assets_mgr.missile_tex)
                    if proj.proj_type == "homing_missile":
                        np.setColorScale(1.0, 0.8, 0.15, 1.0)
                elif proj.is_player_owned:
                    self._maybe_set_texture(np, self.app.assets_mgr.laser_player_tex)
                    if proj.proj_type == "intern_laser":
                        np.setColorScale(0.4, 0.8, 1.0, 1.0)
                else:
                    self._maybe_set_texture(np, self.app.assets_mgr.laser_enemy_tex)
                    if proj.proj_type == "lane_laser":
                        np.setColorScale(1.0, 0.1, 0.1, 0.85)
                        np.setScale(2.5, 1.0, 30.0)

                np.setR(180 if proj.is_player_owned else 0)
                self.projectile_views[proj] = np

            self.projectile_views[proj].setPos(proj.x, 0.0, proj.y)
            if not self.headless and hasattr(self.app, "vfx_mgr") and self.app.vfx_mgr:
                self.app.vfx_mgr.spawn_projectile_trail(proj.proj_type, proj.x, proj.y)

        for proj in list(self.projectile_views.keys()):
            if proj not in active_projs:
                self.projectile_views[proj].removeNode()
                del self.projectile_views[proj]

    def _sync_player_damage_feedback(self) -> None:
        if self.headless:
            return

        curr_player_hp = self.app.state_mgr.player_hp
        if curr_player_hp < self.prev_hit_hp:
            self.player_flash_timer = 0.18
            if hasattr(self.app, "vfx_mgr") and self.app.vfx_mgr:
                self.app.vfx_mgr.trigger_player_hit_flash()
        self.prev_hit_hp = curr_player_hp

        if self.player_flash_timer > 0.0:
            self.player_flash_timer -= self.app.clock.getDt()
            self.app.player_np.setColorScale(1.0, 0.2, 0.2, 1.0)
        else:
            self.app.player_np.setColorScale(1.0, 1.0, 1.0, 1.0)

        if hasattr(self.app, "player_np") and self.app.player_np:
            if curr_player_hp > 75:
                self._maybe_set_texture(self.app.player_np, self.app.assets_mgr.player_hull_100_tex)
            elif curr_player_hp > 50:
                self._maybe_set_texture(self.app.player_np, self.app.assets_mgr.player_hull_75_tex)
            elif curr_player_hp > 25:
                self._maybe_set_texture(self.app.player_np, self.app.assets_mgr.player_hull_50_tex)
            elif curr_player_hp > 10:
                self._maybe_set_texture(self.app.player_np, self.app.assets_mgr.player_hull_25_tex)
            else:
                self._maybe_set_texture(self.app.player_np, self.app.assets_mgr.player_hull_critical_tex)

        if curr_player_hp <= 25 and curr_player_hp > 0 and hasattr(self.app, "vfx_mgr") and self.app.vfx_mgr:
            is_high = getattr(self.app.state_mgr, "vfx_high", True)
            smoke_chance = 0.15 if is_high else 0.05
            if random.random() < smoke_chance:
                self.app.vfx_mgr.spawn_trail_segment(
                    self.app.player.x + random.uniform(-0.3, 0.3),
                    self.app.player.y + random.uniform(-0.3, 0.3),
                    scale=random.uniform(0.12, 0.22),
                    color=(0.15, 0.15, 0.18, 0.35),
                    decay_rate=1.8,
                    velocity=(random.uniform(-0.2, 0.2), random.uniform(-1.0, -0.4)),
                    is_expanding=True,
                )

            spark_chance = 0.08 if is_high else 0.02
            if random.random() < spark_chance:
                angle = random.uniform(0.0, 2.0 * math.pi)
                speed = random.uniform(1.2, 2.8)
                self.app.vfx_mgr.spawn_trail_segment(
                    self.app.player.x + random.uniform(-0.3, 0.3),
                    self.app.player.y + random.uniform(-0.3, 0.3),
                    scale=0.06,
                    color=(1.00, 0.70, 0.15, 0.85),
                    decay_rate=6.0,
                    velocity=(math.cos(angle) * speed, math.sin(angle) * speed),
                )

    def _sync_enemies(self) -> None:
        active_enemies = set(self.app.state_mgr.enemies)
        for enemy in active_enemies:
            if enemy not in self.enemy_views:
                geom = create_boss_dreadnought_geom() if enemy.enemy_type == "boss" else create_chaser_drone_geom()
                np = NodePath(geom)
                np.reparentTo(self.app.render)
                np.setTwoSided(True)
                np.setLightOff()
                np.setTransparency(TransparencyAttrib.MAlpha)
                np.setDepthWrite(False)

                if enemy.enemy_type == "boss":
                    self._maybe_set_texture(np, self._boss_phase_texture(getattr(enemy, "boss_phase", 1)))
                else:
                    self._maybe_set_texture(np, self._enemy_texture(enemy.enemy_type))

                if enemy.enemy_type == "mine":
                    np.setColorScale(1.0, 0.25, 0.1, 1.0)
                    np.setScale(1.1)
                elif enemy.enemy_type == "frigate":
                    np.setColorScale(0.15, 0.95, 0.4, 1.0)
                    np.setScale(1.6)
                elif enemy.enemy_type == "missile_boat":
                    np.setColorScale(0.95, 0.95, 0.15, 1.0)
                    np.setScale(1.3)

                self.enemy_views[enemy] = np
                enemy._prev_hp = enemy.hp
                enemy._flash_timer = 0.0
                enemy._prev_view_x = enemy.x
                enemy._prev_view_y = enemy.y
                enemy._visual_roll = 0.0

            np = self.enemy_views[enemy]
            np.setPos(enemy.x, 0.0, enemy.y)
            self._apply_enemy_orientation(enemy, np)

            if getattr(enemy, "enemy_type", "") == "boss" and hasattr(enemy, "boss_phase"):
                self._maybe_set_texture(np, self._boss_phase_texture(enemy.boss_phase))

            if enemy.hp < getattr(enemy, "_prev_hp", enemy.hp):
                enemy._flash_timer = 0.12
            enemy._prev_hp = enemy.hp

            if getattr(enemy, "_flash_timer", 0.0) > 0.0:
                enemy._flash_timer -= self.app.clock.getDt() if not self.headless else 0.016
                np.setColorScale(1.0, 0.35, 0.35, 1.0)
            else:
                np.setColorScale(1.0, 1.0, 1.0, 1.0)

            if not self.headless and hasattr(self.app, "vfx_mgr") and self.app.vfx_mgr:
                if getattr(enemy, "enemy_type", "") in ("speeder", "zigzag", "frigate", "missile_boat"):
                    spawn_enemy_engine_trail(self.app.vfx_mgr, enemy.enemy_type, enemy.x, enemy.y)

        for enemy in list(self.enemy_views.keys()):
            if enemy not in active_enemies:
                self.enemy_views[enemy].removeNode()
                del self.enemy_views[enemy]

    def _sync_pickups(self) -> None:
        active_pickups = set(self.app.state_mgr.pickups)
        for pickup in active_pickups:
            if pickup not in self.pickup_views:
                pickup_type = pickup_type_for_view(pickup)
                geom = create_pickup_geom(pickup_type)
                np = NodePath(geom)
                np.reparentTo(self.app.render)
                np.setTwoSided(True)
                np.setLightOff()
                np.setTransparency(TransparencyAttrib.MAlpha)
                self._maybe_set_texture(np, self.app.assets_mgr.pickup_texture(pickup_type))
                self.pickup_views[pickup] = np

            self.pickup_views[pickup].setPos(pickup.x, 0.0, pickup.y)

        for pickup in list(self.pickup_views.keys()):
            if pickup not in active_pickups:
                self.pickup_views[pickup].removeNode()
                del self.pickup_views[pickup]
