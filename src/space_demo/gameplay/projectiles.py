# Projectile Simulation Model - To Boldly Respawn

from space_demo import config

class Projectile:
    def __init__(self, x, y, is_player_owned=True, dx=0.0, proj_type="laser"):
        self.x = x
        self.y = y
        self.dx = dx
        self.is_player_owned = is_player_owned
        self.proj_type = proj_type
        self.lifetime = config.LASER_LIFETIME
        if self.proj_type == "lane_laser":
            self.lifetime = 2.0
        
        # Load weapons specs dynamically from weapons configuration
        from space_demo.data.loader import load_weapons_config
        weapons_cfg = load_weapons_config()
        
        # Player shoots DOWNWARD (rear turrets), enemies shoot UPWARD
        if self.is_player_owned:
            if self.proj_type == "missile":
                spec = weapons_cfg.get("player_missile", {"speed": -25.0})
                self.dy = spec.get("speed", -25.0)
            elif self.proj_type == "intern_laser":
                spec = weapons_cfg.get("player_intern_laser", {"speed": -15.0})
                self.dy = spec.get("speed", -15.0)
            else:
                spec = weapons_cfg.get("player_laser", {"speed": -20.0})
                self.dy = spec.get("speed", -20.0)
        else:
            if self.proj_type == "homing_missile":
                self.dy = 7.0 # Slow creeping homing missile
            elif self.proj_type == "lane_laser":
                self.dy = 0.0 # Vertical static lane
            else:
                spec = weapons_cfg.get("enemy_laser", {"speed": 12.0})
                self.dy = spec.get("speed", 12.0)

    def update(self, dt):
        """Moves projectile coordinates with vertical and horizontal velocity components."""
        self.x += self.dx * dt
        self.y += self.dy * dt
        self.lifetime -= dt

    def is_expired(self):
        """Returns True if the projectile has exceeded its lifetime or crossed boundaries."""
        if self.lifetime <= 0.0:
            return True
        if self.proj_type == "lane_laser":
            return False # Checked solely by self.lifetime <= 0.0
        if self.y < config.BOUNDS_Y_MIN - 2.0 or self.y > config.BOUNDS_Y_MAX + 2.0:
            return True
        if self.x < config.BOUNDS_X_MIN - 2.0 or self.x > config.BOUNDS_X_MAX + 2.0:
            return True
        return False
