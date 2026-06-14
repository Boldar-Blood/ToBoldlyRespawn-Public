# Pursuer Interceptors Models - To Boldly Respawn

import math
import random
from space_demo import config

class Enemy:
    def __init__(self, x, y=-10.0, enemy_type="drone"):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        self.shoot_cooldown = random.uniform(1.0, 3.0) # Delay before first shot
        
        # Load dynamic data-driven statistics from ships config
        from space_demo.data.loader import load_ships_config
        ships_cfg = load_ships_config()
        
        spec = ships_cfg.get(enemy_type, {"hp": 20, "speed": 3.0})
        self.hp = spec.get("hp", 20)
        self.max_hp = spec.get("hp", 20)
        self.speed = spec.get("speed", 3.0)
        self.visual_turns_with_movement = bool(
            spec.get("visual_turns_with_movement", enemy_type not in ("boss", "mine"))
        )
        
        if enemy_type == "zigzag":
            self.phase = random.uniform(0.0, math.pi * 2.0)
        elif enemy_type == "boss":
            self.shoot_cooldown = 1.5
        elif enemy_type == "frigate":
            self.frigate_phase = "climbing"
            self.frigate_timer = 0.0
            self.shoot_cooldown = 9999.0
        elif enemy_type == "mine":
            self.shoot_cooldown = 9999.0
        elif enemy_type == "missile_boat":
            self.shoot_cooldown = random.uniform(2.0, 4.0)

    @property
    def boss_phase(self):
        """Derived boss fight phase based on active HP ratio."""
        if self.enemy_type != "boss":
            return 1
        frac = self.hp / self.max_hp
        if frac > 0.67:
            return 1
        elif frac > 0.34:
            return 2
        else:
            return 3

    def update(self, dt, player_x=0.0, difficulty="medium"):
        """Ticks movement coordinates with target-tracking AI and weapons fire timers."""
        # Standard upward Y movement (chasing the player)
        if self.enemy_type == "boss":
            # Boss Dreadnought climbs up until it reaches Y = -3.0, then hovers there!
            if self.y < -3.0:
                self.y += self.speed * dt
            else:
                self.y = -3.0
        elif self.enemy_type == "frigate":
            if self.frigate_phase == "climbing":
                self.y += self.speed * dt
                if self.y >= -2.0:
                    self.y = -2.0
                    self.frigate_phase = "telegraphing"
                    self.frigate_timer = 1.2
            elif self.frigate_phase == "telegraphing":
                self.frigate_timer -= dt
                if self.frigate_timer <= 0.0:
                    self.frigate_phase = "firing"
                    self.frigate_timer = 2.0
            elif self.frigate_phase == "firing":
                self.frigate_timer -= dt
                if self.frigate_timer <= 0.0:
                    self.frigate_phase = "leaving"
            elif self.frigate_phase == "leaving":
                self.y += self.speed * dt
        else:
            self.y += self.speed * dt
        
        # 1. Smart Target-Steering AI (tracking player's X coordinate)
        if self.enemy_type == "boss":
            # Boss dreadnought slowly aligns horizontally with the player ship to lay down heavy fire!
            steer_speed = 0.8 if difficulty == "hard" else 0.4
            if self.x < player_x:
                self.x += steer_speed * dt
            elif self.x > player_x:
                self.x -= steer_speed * dt
                
            # Clamp horizontal coordinates to legal boundaries
            if self.x < config.BOUNDS_X_MIN: self.x = config.BOUNDS_X_MIN
            if self.x > config.BOUNDS_X_MAX: self.x = config.BOUNDS_X_MAX
        elif self.enemy_type not in ("boss", "mine", "frigate") and difficulty != "easy":
            # Hard mode tracking speed is double medium mode tracking speed!
            steer_speed = 3.2 if difficulty == "hard" else 1.5
            
            # Speeder AI is even more hyperactive!
            if self.enemy_type == "speeder":
                steer_speed *= 1.3
                
            if self.x < player_x:
                self.x += steer_speed * dt
            elif self.x > player_x:
                self.x -= steer_speed * dt
                
            # Clamp horizontal coordinates to legal boundaries
            if self.x < config.BOUNDS_X_MIN: self.x = config.BOUNDS_X_MIN
            if self.x > config.BOUNDS_X_MAX: self.x = config.BOUNDS_X_MAX

        # 2. Unique movement patterns
        if self.enemy_type == "zigzag":
            # Oscillate horizontally relative to climbing height
            self.x += math.sin(self.y * 1.5 + self.phase) * 4.0 * dt
            # Clamp X to screen boundaries
            if self.x < config.BOUNDS_X_MIN: self.x = config.BOUNDS_X_MIN
            if self.x > config.BOUNDS_X_MAX: self.x = config.BOUNDS_X_MAX
            
        # Fire rate ticking
        if self.shoot_cooldown > 0.0:
            self.shoot_cooldown -= dt

    def can_shoot(self):
        """Returns True if the interceptor is ready to fire upward."""
        if self.enemy_type in ("mine", "frigate"):
            return False
        return self.shoot_cooldown <= 0.0 and self.y < config.BOUNDS_Y_MAX

    def reset_shoot_cooldown(self, difficulty="medium"):
        """Resets the weapon timer to fire again, scaled dynamically by difficulty."""
        if self.enemy_type == "boss":
            phase = self.boss_phase
            if phase == 1:
                if difficulty == "easy":
                    self.shoot_cooldown = random.uniform(2.5, 4.0)
                elif difficulty == "hard":
                    self.shoot_cooldown = random.uniform(0.8, 1.4)
                else:
                    self.shoot_cooldown = random.uniform(1.5, 2.2)
            elif phase == 2:
                if difficulty == "easy":
                    self.shoot_cooldown = random.uniform(2.0, 3.2)
                elif difficulty == "hard":
                    self.shoot_cooldown = random.uniform(0.6, 1.0)
                else:
                    self.shoot_cooldown = random.uniform(1.0, 1.6)
            else:  # Phase 3
                if difficulty == "easy":
                    self.shoot_cooldown = random.uniform(1.2, 2.0)
                elif difficulty == "hard":
                    self.shoot_cooldown = random.uniform(0.35, 0.6)
                else:
                    self.shoot_cooldown = random.uniform(0.6, 1.0)
        elif self.enemy_type == "missile_boat":
            if difficulty == "easy":
                self.shoot_cooldown = random.uniform(5.5, 7.0)
            elif difficulty == "hard":
                self.shoot_cooldown = random.uniform(3.0, 4.5)
            else:
                self.shoot_cooldown = random.uniform(4.0, 5.5)
        else:
            if difficulty == "easy":
                self.shoot_cooldown = random.uniform(3.5, 6.0)
            elif difficulty == "hard":
                self.shoot_cooldown = random.uniform(1.2, 2.5) # Fast firing
            else:
                self.shoot_cooldown = random.uniform(2.0, 4.0)

    def is_out_of_bounds(self):
        """Returns True if the enemy climbs beyond the top edge without being killed."""
        return self.y > config.BOUNDS_Y_MAX + 1.0
