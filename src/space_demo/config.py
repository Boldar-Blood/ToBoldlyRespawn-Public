# Configuration Constants - To Boldly Respawn

# Screen Plane Bounds (Flat Z=0 XY coordinates)
BOUNDS_X_MIN = -12.5
BOUNDS_X_MAX = 12.5
BOUNDS_Y_MIN = -9.0
BOUNDS_Y_MAX = 9.0

# Starfield Scroll settings
STAR_SCROLL_SPEED = -1.5  # Downwards vertical scroll speed
MAX_STARS = 150

# Player settings
PLAYER_START_HP = 100
PLAYER_STEER_SPEED = 10.0
PLAYER_RELOAD_TIME = 0.15  # Cooldown between rear fire shots

# Projectile settings
PLAYER_LASER_SPEED = -20.0  # Fires DOWNWARD towards pursuers
ENEMY_LASER_SPEED = 12.0   # Fires UPWARD towards player
LASER_LIFETIME = 1.5
PLAYER_MISSILE_SPEED = -25.0 # Missiles fly down even faster!
MISSILE_DAMAGE = 50
MISSILE_PUSH_BACK = 25.0
INITIAL_MISSILES = 3
MAX_MISSILES = 10

# Combat & Collision settings
COLLISION_RADIUS_PLAYER = 1.3
COLLISION_RADIUS_ENEMY = 1.0
COLLISION_RADIUS_PICKUP = 0.7

# Dreadnought Chase settings
INITIAL_CHASE_GAP = 200.0   # Dreadnought starts 200 units behind
DREADNOUGHT_GAIN_RATE = 2.2 # Gap decreases by 2.2 units per second
DREADNOUGHT_PUSH_BACK = 12.0 # Defeating/damaging engines pushes it back by 12 units
DREADNOUGHT_CRITICAL_GAP = 25.0 # Proximity alarm activates below this threshold
DREADNOUGHT_CAPTURE_GAP = 5.0 # Captured game-over condition
DREADNOUGHT_MAX_HP = 300
