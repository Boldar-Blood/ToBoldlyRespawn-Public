# Game State Manager & Simulation Loop - To Boldly Respawn

import random
from typing import Optional
from space_demo import config
from space_demo.core.ids import GameStateID
from space_demo.gameplay.enemies import Enemy
from space_demo.gameplay.projectiles import Projectile
from space_demo.gameplay.pickups import Pickup
from space_demo.core.waves import get_wave_events
from space_demo.core.events import GameEvent


class GameStateManager:
    def __init__(self, ship_def=None, map_def=None, wave_defs=None):
        self.current_state = GameStateID.MENU
        self.difficulty = "medium" # "easy", "medium", "hard"
        self.coop_mode = False     # Local Pilot/Gunner input split toggle
        self.vfx_high = True       # High-performance visual particles budget toggle
        self.liability_shield_active = False
        import sys
        self.intro_active = not ('pytest' in sys.modules)
        self._ship_def = ship_def
        self._map_def = map_def
        self._wave_defs = wave_defs

        
        # Pure Python event queue for MVP presentation decoupling
        self.events = []
        
        # Gameplay Session Statistics
        if ship_def is not None:
            self.player_hp = ship_def.stats.max_hull
            self.max_hull = ship_def.stats.max_hull
            self.missile_ammo = ship_def.stats.missile_capacity
            self.bomb_ammo = ship_def.stats.bomb_capacity
        else:
            self.player_hp = config.PLAYER_START_HP
            self.max_hull = config.PLAYER_START_HP
            self.missile_ammo = config.INITIAL_MISSILES
            self.bomb_ammo = 1
        self.score = 0
        self.wave_index = 1
        self.chase_gap = config.INITIAL_CHASE_GAP
        self.magnet_active_timer = 0.0
        self.intern_active_timer = 0.0
        self.intern_shoot_cooldown = 0.0
        
        # Synergy Multiplier variables
        self.synergy_multiplier = 1.0
        self.max_synergy_multiplier = 1.0
        self.multiplier_decay_timer = 0.0
        self.gap_bonus_accumulator = 0.0
        
        self.missiles_fired = 0
        self.assets_downsized = 0
        self.estimated_legal_exposure = 100000.0
        self.no_hit_wave_badge = True
        
        # Gameplay snapshot tracking counters
        self.defeated_enemy_counts = {}
        self.defeated_boss_id = None
        self.pickup_counts = {}
        
        # Boss / Dreadnought Status
        self.boss_active = False
        self.boss_max_hp = config.DREADNOUGHT_MAX_HP
        self.boss_hp = config.DREADNOUGHT_MAX_HP
        
        # Active Simulation Lists (Pure Python Models)
        self.enemies = []
        self.projectiles = []
        self.pickups = []
        
        # Spawn timers & counters
        self.survival_time = 0.0
        self.spawn_cooldown = 1.0
        self.wave_spawned_count = 0
        self.wave_max_enemies = 6
        self.wave_timer = 25.0  # Seconds per wave before next level
        self.wave_elapsed_time = 0.0
        self.triggered_events = set()
        self._seconds_since_enemy_presence = 0.0
        self._last_filler_spawn_time = -999.0
        
        # Satirical humor bark tracking state
        self.active_bark = ""
        self.bark_timer = 0.0
        self.bark_cooldown = 0.0


    @property
    def map_id(self) -> Optional[str]:
        if self._map_def is not None:
            return self._map_def.id
        return None

    @property
    def boss_wave_index(self) -> int:
        if self._map_def is not None:
            return len(self._map_def.waves)
        return 4

    @property
    def is_boss_wave(self) -> bool:
        if self._map_def is not None:
            return (self.wave_index == len(self._map_def.waves) and self._map_def.boss is not None)
        return (self.wave_index == 4)

    def load_wave_params(self):
        """Loads duration and max_enemies dynamically from waves configuration for active wave_index."""
        if self._map_def is not None and self._wave_defs is not None:
            # Data-driven path
            total_waves = len(self._map_def.waves)
            if self.wave_index <= total_waves:
                wave_key = self._map_def.waves[self.wave_index - 1]
                spec = self._wave_defs.get(wave_key)
                if spec is None:
                    duration = 25.0
                    max_enemies = 6
                    spawn_cooldown = 2.5
                else:
                    duration = spec.duration
                    max_enemies = spec.max_enemies
                    spawn_cooldown = spec.spawn_cooldown
            else:
                duration = 25.0
                max_enemies = 6
                spawn_cooldown = 2.5
                
            is_boss_wave = self.is_boss_wave
            
            if self.difficulty == "easy":
                self.wave_max_enemies = max(2, int(max_enemies * 0.6))
                self.wave_timer = duration * 0.6 if not is_boss_wave else duration
            elif self.difficulty == "hard":
                self.wave_max_enemies = int(max_enemies * 1.5)
                self.wave_timer = duration * 1.5 if not is_boss_wave else duration
            else:
                self.wave_max_enemies = max_enemies
                self.wave_timer = duration
            
            self.spawn_cooldown = spawn_cooldown
        else:
            # Fallback path (original 0.1.x behavior)
            from space_demo.data.loader import load_waves_config
            waves_cfg = load_waves_config()
            wave_key = f"wave_{self.wave_index}"
            if self.wave_index == 4:
                wave_key = "wave_4_boss"
            
            spec = waves_cfg.get(wave_key, {"duration": 25.0, "max_enemies": 6})
            duration = spec.get("duration", 25.0)
            max_enemies = spec.get("max_enemies", 6)
            
            if self.difficulty == "easy":
                self.wave_max_enemies = max(2, int(max_enemies * 0.6))
                self.wave_timer = duration * 0.6 if self.wave_index < 4 else duration
            elif self.difficulty == "hard":
                self.wave_max_enemies = int(max_enemies * 1.5)
                self.wave_timer = duration * 1.5 if self.wave_index < 4 else duration
            else:
                self.wave_max_enemies = max_enemies
                self.wave_timer = duration

    def reset(self, ship_def=None, map_def=None, wave_defs=None):
        if ship_def is not None:
            self._ship_def = ship_def
        if map_def is not None:
            self._map_def = map_def
        if wave_defs is not None:
            self._wave_defs = wave_defs
            
        if self._ship_def is not None:
            self.player_hp = self._ship_def.stats.max_hull
            self.max_hull = self._ship_def.stats.max_hull
            self.missile_ammo = self._ship_def.stats.missile_capacity
            self.bomb_ammo = self._ship_def.stats.bomb_capacity
        else:
            self.player_hp = config.PLAYER_START_HP
            self.max_hull = config.PLAYER_START_HP
            self.missile_ammo = config.INITIAL_MISSILES
            self.bomb_ammo = 1
            
        self.score = 0
        self.wave_index = 1
        self.chase_gap = config.INITIAL_CHASE_GAP
        self.magnet_active_timer = 0.0
        self.intern_active_timer = 0.0
        self.intern_shoot_cooldown = 0.0
        self.boss_active = False
        if self.difficulty == "easy":
            self.boss_max_hp = 600
        elif self.difficulty == "hard":
            self.boss_max_hp = 1200
        else:
            self.boss_max_hp = 900
        self.boss_hp = self.boss_max_hp
        self.liability_shield_active = False
        import sys
        self.intro_active = not ('pytest' in sys.modules)
        
        self.active_bark = ""
        self.bark_timer = 0.0
        self.bark_cooldown = 0.0
        
        # Synergy Multiplier variables
        self.synergy_multiplier = 1.0
        self.max_synergy_multiplier = 1.0
        self.multiplier_decay_timer = 0.0
        self.gap_bonus_accumulator = 0.0
        
        self.missiles_fired = 0
        self.assets_downsized = 0
        self.estimated_legal_exposure = 100000.0
        self.no_hit_wave_badge = True
        
        # Reset snapshot tracking counters
        self.defeated_enemy_counts = {}
        self.defeated_boss_id = None
        self.pickup_counts = {}
        
        # Clear all active entities and event queue
        self.enemies.clear()
        self.projectiles.clear()
        self.pickups.clear()
        self.events.clear()
        
        self.survival_time = 0.0
        self.spawn_cooldown = 1.0
        self.wave_spawned_count = 0
        self.wave_elapsed_time = 0.0
        self.triggered_events.clear()
        self._seconds_since_enemy_presence = 0.0
        self._last_filler_spawn_time = -999.0
 
        # Load wave parameters dynamically
        self.load_wave_params()

    def transition_to(self, new_state):
        self.current_state = new_state
        print(f"[FSM] State transitioned to: {new_state}")

    def start_game(self):
        self.reset()
        self.transition_to(GameStateID.PLAYING)
        self.trigger_bark("start")
        from space_demo.core.events import NotificationEvent
        self.post_event(NotificationEvent(
            title="Phase 1: Strategic Retreat 101",
            message="KEEP DREADNOUGHT GAP ABOVE 5 METERS!",
            category="phase",
            severity="info"
        ))


    def trigger_gameover(self):
        self.transition_to(GameStateID.GAMEOVER)

    def trigger_victory(self):
        self.transition_to(GameStateID.VICTORY)

    def update_simulation_tick(self, dt, player_x=0.0, player_y=5.0):
        if self.current_state != GameStateID.PLAYING:
            return
        if getattr(self, "intro_active", False):
            return

        self.survival_time += dt
        self.wave_elapsed_time += dt
        
        # Tick humor barks
        if self.bark_timer > 0.0:
            self.bark_timer -= dt
            if self.bark_timer <= 0.0:
                self.active_bark = ""
                
        if self.bark_cooldown > 0.0:
            self.bark_cooldown -= dt
            if self.bark_cooldown < 0.0:
                self.bark_cooldown = 0.0
        
        # 1. Dreadnought closes the distance scaled by difficulty
        gain_rate = config.DREADNOUGHT_GAIN_RATE
        if self.difficulty == "easy":
            gain_rate = 1.2
        elif self.difficulty == "hard":
            gain_rate = 3.0
        self.chase_gap -= gain_rate * dt

        if self.chase_gap <= config.DREADNOUGHT_CAPTURE_GAP:
            self.chase_gap = config.DREADNOUGHT_CAPTURE_GAP
            print("[Combat] Overtaken by the dreadnought chase fleet!")
            self.trigger_gameover()
            return

        # Tick Synergy Multiplier decay
        if self.multiplier_decay_timer > 0.0:
            self.multiplier_decay_timer -= dt
            if self.multiplier_decay_timer < 0.0:
                leftover = -self.multiplier_decay_timer
                self.multiplier_decay_timer = 0.0
                self.synergy_multiplier = max(1.0, self.synergy_multiplier - 0.5 * leftover)
        else:
            self.synergy_multiplier = max(1.0, self.synergy_multiplier - 0.5 * dt)

        # Passive Gap Bonus ticking
        if self.chase_gap > 50.0:
            self.gap_bonus_accumulator += dt
            if self.gap_bonus_accumulator >= 1.0:
                self.gap_bonus_accumulator -= 1.0
                multiplier = 1
                if self.difficulty == "easy":
                    multiplier = 1
                elif self.difficulty == "hard":
                    multiplier = 3
                else:
                    multiplier = 2
                self.add_score(multiplier)
                self.estimated_legal_exposure += 100.0

        # 2. Wave Spawner logic
        enemies_before_spawner = len(self.enemies)
        self.tick_spawner(dt)
        self._tick_pressure_filler(dt, enemies_before_spawner)

        # 3. Update Projectiles
        for proj in self.projectiles[:]:
            if proj.proj_type == "homing_missile" and not proj.is_player_owned:
                # Slowly track towards player ship X coordinate!
                dx = player_x - proj.x
                steer_amt = 2.0 * dt
                if abs(dx) < steer_amt:
                    proj.x = player_x
                else:
                    proj.x += steer_amt if dx > 0 else -steer_amt
            
            proj.update(dt)
            if proj.is_expired():
                self.projectiles.remove(proj)

        # 4. Update Enemies
        for enemy in self.enemies[:]:
            prev_phase = getattr(enemy, "frigate_phase", None)
            
            enemy.update(dt, player_x, self.difficulty)
            
            # Check frigate lane laser firing transition
            if enemy.enemy_type == "frigate":
                curr_phase = getattr(enemy, "frigate_phase", None)
                if prev_phase == "telegraphing" and curr_phase == "firing":
                    # Spawn the continuous lane laser!
                    self.spawn_projectile(enemy.x, enemy.y, is_player_owned=False, proj_type="lane_laser")
                    print(f"[Spawner] Frigate at X={enemy.x:.1f} commenced Policy Lane Sweep!")
                
                # Deal continuous laser lane tick damage if player is in the column
                if curr_phase == "firing":
                    if abs(player_x - enemy.x) <= 0.8 and player_y <= enemy.y:
                        self.take_damage(8.0 * dt, player_x, player_y)
                        if random.random() < 0.08:
                            from space_demo.core.events import PlayerHitEvent, PopupEvent
                            self.post_event(PlayerHitEvent(1, player_x, player_y))
                            self.post_event(PopupEvent("LANE LASER DAMAGE!", player_x, player_y + 0.5, (1.0, 0.2, 0.2, 1.0), 0.35, 0.5))
            
            # If chaser interceptor slips past top boundary, escape!
            if enemy.is_out_of_bounds():
                self.enemies.remove(enemy)
                self.take_damage(5) # Sneak attacks deal minor hull damage
                continue
                
            # Interceptors shoot upward at player
            if enemy.can_shoot():
                enemy.reset_shoot_cooldown(self.difficulty)
                if enemy.enemy_type == "boss":
                    phase = enemy.boss_phase
                    if phase == 1:
                        # Phase 1: Thruster Audit
                        self.spawn_projectile(enemy.x, enemy.y + 0.8, is_player_owned=False, dx=0.0)
                        self.spawn_projectile(enemy.x - 0.4, enemy.y + 0.8, is_player_owned=False, dx=-1.5)
                        self.spawn_projectile(enemy.x + 0.4, enemy.y + 0.8, is_player_owned=False, dx=1.5)
                    elif phase == 2:
                        # Phase 2: Compliance Broadside
                        self.spawn_projectile(enemy.x, enemy.y + 0.8, is_player_owned=False, dx=0.0)
                        self.spawn_projectile(enemy.x - 0.3, enemy.y + 0.8, is_player_owned=False, dx=-1.2)
                        self.spawn_projectile(enemy.x + 0.3, enemy.y + 0.8, is_player_owned=False, dx=1.2)
                        self.spawn_projectile(enemy.x - 0.6, enemy.y + 0.8, is_player_owned=False, dx=-2.4)
                        self.spawn_projectile(enemy.x + 0.6, enemy.y + 0.8, is_player_owned=False, dx=2.4)
                        
                        # deploy escort drone (35% chance)
                        if random.random() < 0.35:
                            escort_x = enemy.x + random.uniform(-4.0, 4.0)
                            escort_x = max(config.BOUNDS_X_MIN, min(config.BOUNDS_X_MAX, escort_x))
                            self.enemies.append(Enemy(x=escort_x, y=enemy.y, enemy_type="drone"))
                            print(f"[Spawner] Dreadnought deployed compliance escort drone at X={escort_x:.1f}!")
                    else:
                        # Phase 3: Final Performance Review
                        self.spawn_projectile(enemy.x, enemy.y + 0.8, is_player_owned=False, dx=0.0)
                        self.spawn_projectile(enemy.x - 0.3, enemy.y + 0.8, is_player_owned=False, dx=-1.5)
                        self.spawn_projectile(enemy.x + 0.3, enemy.y + 0.8, is_player_owned=False, dx=1.5)
                        self.spawn_projectile(enemy.x - 0.6, enemy.y + 0.8, is_player_owned=False, dx=-3.0)
                        self.spawn_projectile(enemy.x + 0.6, enemy.y + 0.8, is_player_owned=False, dx=3.0)
                        
                        # homing missile (50% chance)
                        if random.random() < 0.5:
                            self.spawn_projectile(enemy.x, enemy.y + 0.8, is_player_owned=False, proj_type="homing_missile")
                            print("[Spawner] Dreadnought fired parodied Auditing Homing Missile!")
                        
                        # lane laser (30% chance)
                        if random.random() < 0.3:
                            self.spawn_projectile(enemy.x, enemy.y, is_player_owned=False, proj_type="lane_laser")
                            print("[Spawner] Dreadnought initiated local Column Performance Review!")
                elif enemy.enemy_type == "missile_boat":
                    self.spawn_projectile(enemy.x, enemy.y + 0.5, is_player_owned=False, proj_type="homing_missile")
                else:
                    self.spawn_projectile(enemy.x, enemy.y + 0.5, is_player_owned=False)

        # Track Dreadnought phase transitions
        if self.boss_active:
            boss_enemy = next((e for e in self.enemies if e.enemy_type == "boss"), None)
            if boss_enemy:
                self.boss_hp = boss_enemy.hp
                curr_phase = boss_enemy.boss_phase
                if not hasattr(self, "boss_prev_phase"):
                    self.boss_prev_phase = 1
                if curr_phase > self.boss_prev_phase:
                    self.boss_prev_phase = curr_phase
                    from space_demo.core.events import NotificationEvent
                    if curr_phase == 2:
                        self.post_event(NotificationEvent(
                            title="BOSS PHASE 2: COMPLIANCE BROADSIDE",
                            message="Dreadnought wings damaged! Escort waves intensifying!",
                            category="boss",
                            severity="warning"
                        ))
                        self.trigger_bark("boss_phase_2")
                        print("[Combat] Dreadnought transitioned to Phase 2: Compliance Broadside!")
                    elif curr_phase == 3:
                        self.post_event(NotificationEvent(
                            title="BOSS PHASE 3: FINAL PERFORMANCE REVIEW",
                            message="Dreadnought core exposed! Warning lanes and missiles active!",
                            category="boss",
                            severity="danger"
                        ))
                        self.trigger_bark("boss_phase_3")
                        print("[Combat] Dreadnought transitioned to Phase 3: Final Performance Review!")

        # 5. Update Pickups (they float upward slowly)
        if self.magnet_active_timer > 0.0:
            self.magnet_active_timer -= dt
            if self.magnet_active_timer < 0.0:
                self.magnet_active_timer = 0.0
                
            for pickup in self.pickups:
                import math
                dx = player_x - pickup.x
                dy = player_y - pickup.y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= 8.0:
                    pull_speed = 8.0 * (1.0 - dist / 8.0) + 2.0
                    if dist > 0.1:
                        vx = (dx / dist) * pull_speed
                        vy = (dy / dist) * pull_speed
                        pickup.x += vx * dt
                        pickup.y += vy * dt

        for pickup in self.pickups[:]:
            pickup.update(dt)
            if pickup.is_expired():
                self.pickups.remove(pickup)

        # 6. Update Unpaid Intern Drone (automatically fires downward from sidecar when active)
        if self.intern_active_timer > 0.0:
            self.intern_active_timer -= dt
            self.intern_shoot_cooldown -= dt
            
            if self.intern_shoot_cooldown <= 0.0:
                from space_demo.data.loader import load_weapons_config
                weapons_cfg = load_weapons_config()
                laser_spec = weapons_cfg.get("player_intern_laser", {"reload_time": 0.45})
                reload_t = laser_spec.get("reload_time", 0.45)
                self.intern_shoot_cooldown = reload_t
                
                # Alternate left/right offset relative to the player
                side = -1.2 if (len(self.projectiles) % 2 == 0) else 1.2
                self.spawn_projectile(player_x + side, player_y - 0.5, is_player_owned=True, proj_type="intern_laser")
            
            if self.intern_active_timer <= 0.0:
                self.intern_active_timer = 0.0
                from space_demo.core.events import InternDeactivatedEvent
                self.post_event(InternDeactivatedEvent())
                self.trigger_bark("intern_expired")

    def _filler_type_for_wave(self):
        """Return a safe pressure-filler enemy type for the active wave."""
        if self._map_def is not None and self._wave_defs is not None:
            # If the configured escorts in data/waves.json are broader than the legacy pools,
            # we preserve the legacy filler-selection behavior for Map 001 for now to prevent
            # introducing new/broader enemy types (like frigates) as pressure fillers.
            # Fully data-driven filler tuning is deferred.
            if self._map_def.id == "map_001_retrograde_escape":
                if self.wave_index <= 1:
                    return "drone"
                elif self.wave_index == 2:
                    pool = ("drone", "speeder", "mine")
                elif self.wave_index == 3:
                    pool = ("drone", "speeder", "zigzag", "missile_boat")
                else:
                    pool = ("drone", "speeder")

                if len(pool) == 1:
                    return pool[0]
                return random.choice(pool)

            total_waves = len(self._map_def.waves)
            if self.wave_index <= total_waves:
                wave_key = self._map_def.waves[self.wave_index - 1]
                spec = self._wave_defs.get(wave_key)
                if spec is not None and spec.escorts:
                    # If exactly one option, return that option directly without calling random.choice()
                    if len(spec.escorts) == 1:
                        return spec.escorts[0]
                    return random.choice(spec.escorts)
            return "drone"

        # Legacy fallback logic when no map configuration is active
        if self.wave_index <= 1:
            return "drone"
        if self.wave_index == 2:
            return random.choice(("drone", "speeder", "mine"))
        if self.wave_index == 3:
            return random.choice(("drone", "speeder", "zigzag", "missile_boat"))
        return random.choice(("drone", "speeder"))

    def _tick_pressure_filler(self, dt, enemies_before_spawner):
        """Spawn a light filler contact when authored waves leave too much dead air."""
        enemies_after_spawner = len(self.enemies)
        if enemies_after_spawner > enemies_before_spawner or enemies_after_spawner > 0:
            self._seconds_since_enemy_presence = 0.0
            return

        # Keep scripted tests and boss sequences deterministic.
        if self.wave_index >= self.boss_wave_index or self.wave_max_enemies <= 0:
            return

        self._seconds_since_enemy_presence += dt
        recent_filler_gap = self.wave_elapsed_time - self._last_filler_spawn_time
        if self._seconds_since_enemy_presence < 2.5 or recent_filler_gap < 2.5:
            return
        if self.wave_timer <= 0.25:
            return

        enemy_type = self._filler_type_for_wave()
        count = 1 if self.difficulty != "hard" else 2
        for _ in range(count):
            x_pos = random.uniform(config.BOUNDS_X_MIN + 1.0, config.BOUNDS_X_MAX - 1.0)
            self.enemies.append(Enemy(x=x_pos, enemy_type=enemy_type))
            self.wave_spawned_count += 1
        self._last_filler_spawn_time = self.wave_elapsed_time
        self._seconds_since_enemy_presence = 0.0
        print(f"[Spawner] Pressure filler spawned {count} {enemy_type}(s) to avoid combat dead air.")

    def tick_spawner(self, dt):
        self.wave_timer -= dt
        
        # Check wave transition (Wave 4 is the boss chase!)
        if self.wave_timer <= 0.0 and self.wave_index < self.boss_wave_index:
            # Award Gap Retained and No-Hit Badge bonuses!
            gap_bonus = int(self.chase_gap * 10)
            self.add_score(gap_bonus)
            
            from space_demo.core.events import NotificationEvent
            # Post telemetry notification for Gap Retained
            self.post_event(NotificationEvent(
                title="GAP RETAINED BONUS",
                message=f"Gap of {self.chase_gap:.1f}m retained! +{gap_bonus} points.",
                category="reward",
                severity="success"
            ))
            
            # No-Hit Badge check
            if self.no_hit_wave_badge:
                self.add_score(500)
                self.post_event(NotificationEvent(
                    title="NO-HIT WAVE BADGE",
                    message="Survived without taking damage! +500 points.",
                    category="reward",
                    severity="success"
                ))
            
            # Reset no-hit state for the next wave
            self.no_hit_wave_badge = True

            self.wave_index += 1
            self.load_wave_params()
            self.wave_elapsed_time = 0.0
            self.triggered_events.clear()
            self.boss_active = False # Reset for boss level
            print(f"[Spawner] Wave transitioned to Wave {self.wave_index}!")
            self.trigger_bark("start")
            
            if self.wave_index == 2:
                self.post_event(NotificationEvent(
                    title="Phase 2: Broadside Compliance",
                    message="More Interceptor Drones Deployed",
                    category="phase",
                    severity="info"
                ))
            elif self.wave_index == 3:
                self.post_event(NotificationEvent(
                    title="Phase 3: Final Performance Review",
                    message="Auditor Chase Fleet Gaps Closing",
                    category="phase",
                    severity="info"
                ))
            elif self.wave_index == self.boss_wave_index:
                self.post_event(NotificationEvent(
                    title="Phase 4: Corporate Audit Imminent",
                    message="AUDITOR CLASS CLIMAX DREADNOUGHT SPAWNING!",
                    category="boss",
                    severity="danger"
                ))
            return


        # Fetch configured wave events
        if self._map_def is not None:
            wave_key = self._map_def.waves[self.wave_index - 1]
            from space_demo.core.waves import get_wave_events_for_id
            events = get_wave_events_for_id(wave_key)
        else:
            events = get_wave_events(self.wave_index)
        
        # Determine loop offset and iteration for Wave 4 escorts
        loop_time = self.wave_elapsed_time
        loop_iteration = 0
        if self.wave_index == self.boss_wave_index:
            # Boss Dreadnought spawns once immediately at start of wave
            if not self.boss_active:
                boss_type = self._map_def.boss if (self._map_def is not None and self._map_def.boss is not None) else "boss"
                boss_enemy = Enemy(x=0.0, y=-11.0, enemy_type=boss_type)
                if self.difficulty == "easy":
                    boss_enemy.hp = 600
                    boss_enemy.max_hp = 600
                elif self.difficulty == "hard":
                    boss_enemy.hp = 1200
                    boss_enemy.max_hp = 1200
                else:
                    boss_enemy.hp = 900
                    boss_enemy.max_hp = 900
                self.boss_max_hp = boss_enemy.max_hp
                self.boss_hp = boss_enemy.hp
                self.enemies.append(boss_enemy)
                self.boss_active = True
                self.boss_prev_phase = 1
                self.triggered_events.add((0, 0.0))
                print(f"[Spawner] Boss Dreadnought spawned at Wave {self.wave_index} Climax with {boss_enemy.max_hp} HP!")
            
            # Loop other escort spawns every 60 seconds
            loop_time = self.wave_elapsed_time % 60.0
            loop_iteration = int(self.wave_elapsed_time // 60.0)

        # Process spawner events
        for event in events:
            # Skip Wave 4 boss spawning here (handled manually above once)
            if self.wave_index == self.boss_wave_index and event.enemy_type == "boss":
                continue
                
            trigger_key = (loop_iteration, event.time_offset) if self.wave_index == self.boss_wave_index else event.time_offset
            
            # Telegraph warnings before spawn (Easy: 2.2s warning window, Medium: 1.5s, Hard: 0.9s)
            warning_window = 1.5
            if self.difficulty == "easy":
                warning_window = 2.2
            elif self.difficulty == "hard":
                warning_window = 0.9
            
            telegraph_key = ("telegraph", loop_iteration, event.time_offset) if self.wave_index == self.boss_wave_index else ("telegraph", event.time_offset)
            if loop_time >= (event.time_offset - warning_window) and event.time_offset > warning_window and telegraph_key not in self.triggered_events:
                self.triggered_events.add(telegraph_key)
                
                from space_demo.core.events import NotificationEvent
                category_map = {
                    "speeder": ("WARNING: HIGH VELOCITY CONTACTS", "Fast flankers closing in on vectors!", "warning", "warning"),
                    "zigzag": ("WARNING: UNSTABLE RADIAL CONTACTS", "Erratic evasive interceptors detected!", "warning", "warning"),
                    "frigate": ("ALERT: LANE LOCK-ON DETECTED", "Policy laser frigate preparing lane sweep!", "danger", "danger"),
                    "missile_boat": ("ALERT: LONG RANGE STRIKER", "Deadline missile boat locking on!", "danger", "danger"),
                    "mine": ("WARNING: AREA DENIAL HAZARD", "Expense report mines floating in sector!", "warning", "warning")
                }
                if event.enemy_type in category_map:
                    title, msg, cat, sev = category_map[event.enemy_type]
                    self.post_event(NotificationEvent(
                        title=title,
                        message=msg,
                        category=cat,
                        severity=sev
                    ))
            
            if loop_time >= event.time_offset and trigger_key not in self.triggered_events:
                self.triggered_events.add(trigger_key)
                
                # Determine positions dynamically scaled by difficulty settings
                positions = event.x_positions
                if self.difficulty == "easy" and len(positions) > 1:
                    # easy mode spawns one less chaser in formation
                    positions = positions[:-1]
                elif self.difficulty == "hard" and event.enemy_type != "boss":
                    # hard mode adds an extra aggressive randomly placed flanker!
                    import random
                    extra_x = random.uniform(config.BOUNDS_X_MIN + 1.0, config.BOUNDS_X_MAX - 1.0)
                    positions = list(positions) + [extra_x]
                
                # Spawn chasers at selected positions
                for x_pos in positions:
                    self.enemies.append(Enemy(x=x_pos, enemy_type=event.enemy_type))
                    self.wave_spawned_count += 1
                
                # Trigger optional parody barks
                if event.bark_trigger:
                    self.trigger_bark(event.bark_trigger)
                
                print(f"[Spawner] Triggered formation: '{event.pattern_name}' spawning {len(positions)} {event.enemy_type}(s).")

    def spawn_projectile(self, x, y, is_player_owned=True, dx=0.0, proj_type="laser"):
        self.projectiles.append(Projectile(x, y, is_player_owned, dx, proj_type))
        if is_player_owned:
            if proj_type == "missile":
                self.missiles_fired += 1
                self.estimated_legal_exposure += 15000.0
            elif proj_type in ("laser", "intern_laser"):
                self.estimated_legal_exposure += 5000.0

    def add_score(self, amount):
        added = int(amount * self.synergy_multiplier)
        self.score += added

    def take_damage(self, amount, x=0.0, y=-5.0):
        if self.liability_shield_active:
            copay = max(1, int(amount * 0.10))
            self.liability_shield_active = False
            self.player_hp -= copay
            self.no_hit_wave_badge = False
            self.estimated_legal_exposure += 25000.0
            from space_demo.core.events import ShieldBrokenEvent
            self.post_event(ShieldBrokenEvent(x, y))
            self.trigger_bark("shield_broken")
            if self.player_hp <= 0:
                self.player_hp = 0
                self.trigger_gameover()
            return

        self.player_hp -= amount
        self.no_hit_wave_badge = False
        self.estimated_legal_exposure += 25000.0
        if self.player_hp <= 0:
            self.player_hp = 0
            self.trigger_gameover()
        else:
            self.trigger_bark("hit")
            if self.player_hp <= 30:
                from space_demo.core.events import NotificationEvent
                self.post_event(NotificationEvent(
                    title="WARNING: HULL CRITICAL",
                    message="REAR HULL INTEGRITY SEVERELY COMPROMISED",
                    category="warning",
                    severity="danger"
                ))


    def heal(self, amount):
        self.player_hp += amount
        if self.player_hp > self.max_hull:
            self.player_hp = self.max_hull

    def push_back_chaser(self, amount):
        if self.boss_active:
            # Scale down pushback to maintain high tension during the final fight:
            # Standard lasers (amount ~3.6) get 5% effectiveness (0.18m)
            # Missiles (amount ~7.5) get 40% effectiveness (3.0m)
            # Decisions / Bombs (amount >= 12.5) get 60% effectiveness (7.5m+)
            if amount <= 4.0:
                scale = 0.05
            elif amount <= 8.0:
                scale = 0.40
            else:
                scale = 0.60
            
            self.chase_gap += amount * scale
        else:
            self.chase_gap += amount
            
        if self.chase_gap > config.INITIAL_CHASE_GAP:
            self.chase_gap = config.INITIAL_CHASE_GAP

    def trigger_bark(self, bark_type):
        if self.bark_cooldown > 0.0:
            return # Don't spam barks
            
        import random
        barks = {
            "start": [
                "Captain, we are bravely advancing away.",
                "Morale remains high. Morale is mandatory.",
                "Strategic retreat initiated. Paperwork pending."
            ],
            "hit": [
                "Hull integrity downgraded to vibes.",
                "Rear hull: damaged. Emergency duct tape: applied.",
                "Damage logged. Synergy levels unaffected."
            ],
            "pickup": [
                "Synergy collected! Nobody knows what it does.",
                "Anti-Matter missile acquired. Charge it to legal.",
                "Snack collected. Reload velocity overclocked."
            ],
            "shield": [
                "Liability waiver signed. Ignore flashing alarms.",
                "Risk successfully outsourced! Shield activated.",
                "Waiver clause active. Zero responsibility assumed."
            ],
            "shield_broken": [
                "Clause 4.2 invoked! Shield dissolved.",
                "Copay deductible applied! Billed to console.",
                "Waiver expired! Return to direct responsibility."
            ],
            "bomb": [
                "Executive decision made! All subordinates dismissed.",
                "Redundant assets downsized! Out of my sight!",
                "Quarterly review vetoed! Synergy cleared!"
            ],
            "magnet": [
                "Consolidating underperforming assets.",
                "Asset pooling protocol initiated!",
                "Horizontal integration active. Draw resources in!"
            ],
            "intern": [
                "Unpaid Intern deployed! No benefits packages provided.",
                "Delegated labor active. Fire lasers, recruit!",
                "Resume builder active. Experience is its own reward!"
            ],
            "intern_expired": [
                "Internship concluded. Recommendation letter pending.",
                "Unpaid labor caps met. Terminated without pay!",
                "Duration limit reached. Back to school!"
            ],
            "boss_phase_2": [
                "Wings compromised! File a complaint with the union!",
                "Structural discrepancies observed on their hull!",
                "Dreadnought broadsides active! Prepare for heavy audit!"
            ],
            "boss_phase_3": [
                "Exposed core! Their auditing loop is failing!",
                "Audit core exposed! Terminate their redundant managers!",
                "Critical failure in their spreadsheet! Finish them off!"
            ]
        }.get(bark_type, [])
        
        if barks:
            self.active_bark = random.choice(barks)
            self.bark_timer = 4.5 # Display for 4.5 seconds
            self.bark_cooldown = 8.0 # Cooldown of 8 seconds before next bark
            print(f"[Bark] Triggered: '{self.active_bark}'")

    def trigger_executive_decision(self, player_x, player_y):
        """Fires a screen-clearing bureaucratic shockwave if bomb ammo is available and playing.

        Returns True only if the bomb was actually fired.
        Returns False if unavailable or unsafe.
        """
        if self.current_state != "playing" and self.current_state != GameStateID.PLAYING:
            return False

        if getattr(self, "intro_active", False):
            return False

        if self.bomb_ammo <= 0:
            self.bomb_ammo = 0
            self.active_bark = "NO DECISIONS LEFT — leadership unavailable."
            self.bark_timer = 2.0
            return False
            
        self.bomb_ammo -= 1
        self.estimated_legal_exposure += 50000.0
        
        # Post the visual presentation event
        from space_demo.core.events import ExecutiveDecisionEvent, EnemyDestroyedEvent, EnemyHitEvent, PopupEvent
        self.post_event(ExecutiveDecisionEvent(player_x, player_y))
        
        # Trigger comedic barks
        self.trigger_bark("bomb")
        
        # Helper to post floating popups
        def safe_popup(text, x, z, color=(1.0, 1.0, 1.0, 1.0), scale=0.35, lifetime=1.0):
            self.post_event(PopupEvent(text, x, z, color, scale, lifetime))

        # Wreak absolute havoc on active interceptors
        for enemy in self.enemies[:]:
            if enemy.enemy_type == "boss":
                # Boss takes massive damage
                enemy.hp -= 150
                self.boss_hp = enemy.hp
                self.post_event(EnemyHitEvent("boss", 150, enemy.x, enemy.y))
                safe_popup("-150 HP", enemy.x, enemy.y, color=(1.0, 0.8, 0.2, 1.0), scale=0.48, lifetime=1.3)
                print(f"[Combat] Boss blasted by Executive Decision! HP: {enemy.hp}")
                
                # Check boss destruction
                if enemy.hp <= 0:
                    if enemy in self.enemies:
                        self.enemies.remove(enemy)
                    self.add_score(100)
                    self.push_back_chaser(config.MISSILE_PUSH_BACK * 0.5)
                    self.post_event(EnemyDestroyedEvent("boss", enemy.x, enemy.y, 100))
                    safe_popup("DREADNOUGHT CAPTURED!", enemy.x, enemy.y, color=(0.2, 1.0, 0.6, 1.0), scale=0.75, lifetime=2.0)
                    self.trigger_victory()
            else:
                # Normal enemies take 100 damage (fatal since max hp is 10-30)
                damage_dealt = enemy.hp
                enemy.hp = 0
                if enemy in self.enemies:
                    self.enemies.remove(enemy)
                score_val = 15
                self.add_score(score_val)
                self.post_event(EnemyHitEvent(enemy.enemy_type, damage_dealt, enemy.x, enemy.y))
                self.post_event(EnemyDestroyedEvent(enemy.enemy_type, enemy.x, enemy.y, score_val))
                safe_popup(f"+{score_val} SYNERGY", enemy.x, enemy.y, color=(0.2, 1.0, 0.5, 1.0), scale=0.40, lifetime=1.2)
                print(f"[Combat] Interceptor {enemy.enemy_type} downsized via Executive Decision.")

        # Push chasers back by a massive buffer
        self.push_back_chaser(4.0)
        return True

    def post_event(self, event):
        self.events.append(event)
        
        class_name = event.__class__.__name__
        if class_name == "EnemyDestroyedEvent":
            enemy_type = event.enemy_type
            self.defeated_enemy_counts[enemy_type] = self.defeated_enemy_counts.get(enemy_type, 0) + 1
            
            # Check if this matches map boss or default boss ID
            map_boss = self._map_def.boss if (hasattr(self, "_map_def") and self._map_def is not None and self._map_def.boss) else "boss"
            if enemy_type == map_boss:
                self.defeated_boss_id = enemy_type
        elif class_name == "PickupCollectedEvent":
            pickup_type = event.pickup_type
            self.pickup_counts[pickup_type] = self.pickup_counts.get(pickup_type, 0) + 1
