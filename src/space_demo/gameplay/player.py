# Player Ship Simulation Model - To Boldly Respawn

from space_demo import config
from space_demo.core.math2d import clamp_value

class Player:
    def __init__(self, start_x=0.0, start_y=5.0, ship_def=None):
        self.x = start_x
        self.y = start_y
        self.reload_timer = 0.0
        self.fire_rate_multiplier = 1.0
        self._ship_def = ship_def
        
        if ship_def is not None:
            self.steer_speed = ship_def.stats.move_speed
            self.reload_time = ship_def.stats.fire_cooldown
        else:
            # Load data-driven configurations dynamically
            from space_demo.data.loader import load_ships_config, load_weapons_config
            ships_cfg = load_ships_config()
            weapons_cfg = load_weapons_config()
            
            player_spec = ships_cfg.get("player", {"speed": 10.0})
            laser_spec = weapons_cfg.get("player_laser", {"reload_time": 0.15})
            
            self.steer_speed = player_spec.get("speed", 10.0)
            self.reload_time = laser_spec.get("reload_time", 0.15)

    def reset(self, start_x=0.0, start_y=5.0, ship_def=None):
        self.x = start_x
        self.y = start_y
        self.reload_timer = 0.0
        self.fire_rate_multiplier = 1.0
        
        if ship_def is not None:
            self._ship_def = ship_def
            
        if self._ship_def is not None:
            self.steer_speed = self._ship_def.stats.move_speed
            self.reload_time = self._ship_def.stats.fire_cooldown
        else:
            from space_demo.data.loader import load_ships_config, load_weapons_config
            ships_cfg = load_ships_config()
            weapons_cfg = load_weapons_config()
            
            player_spec = ships_cfg.get("player", {"speed": 10.0})
            laser_spec = weapons_cfg.get("player_laser", {"reload_time": 0.15})
            
            self.steer_speed = player_spec.get("speed", 10.0)
            self.reload_time = laser_spec.get("reload_time", 0.15)

    def move(self, dx, dy, dt):
        """Moves the player coordinates based on steering velocity and dt, clamped to screen bounds."""
        # Normalize diagonal inputs so travel is not 41.4% faster
        if dx != 0.0 and dy != 0.0:
            # 1 / sqrt(2) ≈ 0.70710678
            dx *= 0.70710678
            dy *= 0.70710678

        speed = self.steer_speed
        self.x += dx * speed * dt
        self.y += dy * speed * dt

        # Apply strict coordinate clamping to the entire playable screen bounds
        self.x = clamp_value(self.x, config.BOUNDS_X_MIN, config.BOUNDS_X_MAX)
        self.y = clamp_value(self.y, config.BOUNDS_Y_MIN, config.BOUNDS_Y_MAX)

    def tick_cooldown(self, dt):
        """Ticks weapon firing cooldown reload timers."""
        if self.reload_timer > 0.0:
            self.reload_timer -= dt
            if self.reload_timer < 0.0:
                self.reload_timer = 0.0

    def can_fire(self):
        """Returns True if the weapon is ready to fire."""
        return self.reload_timer <= 0.0

    def reset_cooldown(self):
        """Resets the reload timer with fire rate multipliers applied."""
        self.reload_timer = self.reload_time / self.fire_rate_multiplier
