# Reward Pickups Model - To Boldly Respawn

from space_demo import config

class Pickup:
    def __init__(self, x, y, pickup_type="health"):
        self.x = x
        self.y = y
        self.pickup_type = pickup_type
        self.lifetime = 6.0 # Expire after 6 seconds

    def update(self, dt):
        """Pickups float UPWARD toward the player's coordinate range."""
        self.y += 1.5 * dt
        self.lifetime -= dt

    def is_expired(self):
        """Returns True if the pickup has expired or floated off screen."""
        if self.lifetime <= 0.0:
            return True
        if self.y > config.BOUNDS_Y_MAX + 2.0:
            return True
        return False
