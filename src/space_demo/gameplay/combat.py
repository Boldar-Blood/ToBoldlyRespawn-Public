# Combat Collision Resolver - To Boldly Respawn

import random
from space_demo import config
from space_demo.core.math2d import check_circle_overlap, calculate_distance
from space_demo.gameplay.pickups import Pickup
from space_demo.core.events import (
    PopupEvent, EnemyHitEvent, EnemyDestroyedEvent,
    PlayerHitEvent, CollisionEvent, PickupCollectedEvent
)

def resolve_collisions(state_mgr, player):
    """Processes coordinate overlap collisions across all active simulation entities."""
    if state_mgr.current_state != "playing":
        return

    # Load dynamic configurations for data-driven hitboxes and damage specs
    from space_demo.data.loader import load_ships_config, load_weapons_config
    ships_cfg = load_ships_config()
    weapons_cfg = load_weapons_config()

    # Helper function to post floating popups via the pure-Python event system
    def safe_popup(text, x, z, color=(1.0, 1.0, 1.0, 1.0), scale=0.35, lifetime=1.0):
        state_mgr.post_event(PopupEvent(text, x, z, color, scale, lifetime))

    # 1. Player lasers/missiles vs Pursuing Interceptors
    for proj in state_mgr.projectiles[:]:
        if not proj.is_player_owned:
            continue
            
        for enemy in state_mgr.enemies[:]:
            # Accurate hitboxes: rectangular box collision for boss dreadnought, radial for normal enemies
            is_hit = False
            if enemy.enemy_type == "boss":
                # Boss visual size is 9.6 wide and 7.2 high, centered at (enemy.x, enemy.y)
                is_hit = (abs(proj.x - enemy.x) <= 4.8) and (abs(proj.y - enemy.y) <= 3.6)
            else:
                enemy_spec = ships_cfg.get(enemy.enemy_type, {"radius": 0.4})
                rad = enemy_spec.get("radius", 0.4)
                is_hit = check_circle_overlap(proj.x, proj.y, 0.05, enemy.x, enemy.y, rad)
                
            if is_hit:
                # Calculate damage and pushback dynamically based on projectile type
                if proj.proj_type == "missile":
                    wpn_spec = weapons_cfg.get("player_missile", {"damage": 50})
                    dmg = wpn_spec.get("damage", 50)
                    push = config.MISSILE_PUSH_BACK
                    weapon_type = "missile"
                elif proj.proj_type == "intern_laser":
                    wpn_spec = weapons_cfg.get("player_intern_laser", {"damage": 5})
                    dmg = wpn_spec.get("damage", 5)
                    push = config.DREADNOUGHT_PUSH_BACK
                    weapon_type = "intern_laser"
                else:
                    wpn_spec = weapons_cfg.get("player_laser", {"damage": 10})
                    dmg = wpn_spec.get("damage", 10)
                    push = config.DREADNOUGHT_PUSH_BACK
                    weapon_type = "laser"
                
                # Deduct HP
                enemy.hp -= dmg
                
                # Post hit event
                state_mgr.post_event(EnemyHitEvent(enemy.enemy_type, dmg, proj.x, proj.y))
                
                # Show dynamic damage floating popup
                if enemy.enemy_type == "boss":
                    safe_popup(f"-{dmg} HP", proj.x, proj.y, color=(1.0, 0.8, 0.2, 1.0), scale=0.45, lifetime=1.2)
                else:
                    safe_popup(f"-{dmg}", proj.x, proj.y, color=(1.0, 1.0, 0.4, 1.0), scale=0.30, lifetime=0.8)
                
                # Damaging the boss pushes the dreadnought chase back!
                if enemy.enemy_type == "boss":
                    state_mgr.push_back_chaser(push * 0.3, event_type="boss_hit", weapon_type=weapon_type)
                    state_mgr.boss_hp = enemy.hp
                    print(f"[Combat] Boss hit! Dealt {dmg} damage. Fleet pushed back.")
                
                # Remove projectile
                if proj in state_mgr.projectiles:
                    state_mgr.projectiles.remove(proj)
                
                # Check destruction
                if enemy.hp <= 0:
                    if enemy in state_mgr.enemies:
                        state_mgr.enemies.remove(enemy)
                        
                    # Accumulate score & push chasers back (buying safety distance!)
                    score_val = 15 if enemy.enemy_type != "boss" else 100
                    
                    # Update synergy multiplier and session stats
                    state_mgr.synergy_multiplier = min(5.0, state_mgr.synergy_multiplier + 0.5)
                    state_mgr.max_synergy_multiplier = max(state_mgr.max_synergy_multiplier, state_mgr.synergy_multiplier)
                    state_mgr.multiplier_decay_timer = 3.5  # 3.5 seconds grace period
                    state_mgr.assets_downsized += 1
                    
                    synergy_added = int(score_val * state_mgr.synergy_multiplier)
                    state_mgr.add_score(score_val)
                    if enemy.enemy_type == "boss":
                        event_type = "boss_kill"
                        pushback_amount = push * 0.5
                    else:
                        event_type = "non_boss_enemy_destruction"
                        pushback_amount = push * config.DREADNOUGHT_NON_BOSS_PUSHBACK_MULT

                    state_mgr.push_back_chaser(pushback_amount, event_type=event_type, weapon_type=weapon_type)
                    print(f"[Combat] Destroyed {enemy.enemy_type}! Chaser fleet pushed back. Multiplier: {state_mgr.synergy_multiplier:.1f}x")
                    
                    # Post destruction event
                    state_mgr.post_event(EnemyDestroyedEvent(enemy.enemy_type, enemy.x, enemy.y, synergy_added))
                    
                    # Show beautiful destruction popups!
                    if enemy.enemy_type == "boss":
                        safe_popup("DREADNOUGHT CAPTURED!", enemy.x, enemy.y, color=(0.2, 1.0, 0.6, 1.0), scale=0.75, lifetime=2.0)
                        print("[Combat] Dreadnought engines completely disabled! Escape successful!")
                        state_mgr.trigger_victory()
                    else:
                        safe_popup(f"+{synergy_added} SYNERGY", enemy.x, enemy.y, color=(0.2, 1.0, 0.5, 1.0), scale=0.40, lifetime=1.2)
                        
                    # Random chance to drop fuel/medkits/missiles/shields/bombs/magnets floating upward
                    if enemy.enemy_type != "boss" and random.random() < 0.45:
                        p_type = random.choice(["health", "health", "speed", "speed", "missile", "shield", "bomb", "magnet", "intern"])
                        state_mgr.pickups.append(Pickup(enemy.x, enemy.y, p_type))
                break

    # Load player spec radius dynamically
    player_spec = ships_cfg.get("player", {"radius": 0.5})
    player_rad = player_spec.get("radius", 0.5)

    # 2. Enemy lasers vs Player Ship
    for proj in state_mgr.projectiles[:]:
        if proj.is_player_owned:
            continue
            
        if check_circle_overlap(proj.x, proj.y, 0.05, player.x, player.y, player_rad):
            if proj in state_mgr.projectiles:
                state_mgr.projectiles.remove(proj)
            
            # Load enemy laser damage dynamically from weapons specs
            enemy_laser_spec = weapons_cfg.get("enemy_laser", {"damage": 10})
            laser_dmg = enemy_laser_spec.get("damage", 10)

            # Subtracted from hull integrity (passing player coordinates in case of shield copay)
            state_mgr.take_damage(laser_dmg, player.x, player.y)
            print(f"[Combat] Player ship hit by chasing laser! HP reduced by {laser_dmg}.")
            # Post player hit event
            state_mgr.post_event(PlayerHitEvent(laser_dmg, player.x, player.y))
            # Damage popup on player
            safe_popup(f"-{laser_dmg} HULL", player.x, player.y + 0.5, color=(1.0, 0.2, 0.2, 1.0), scale=0.42, lifetime=1.2)

    # 3. Interceptors crashing directly into Player Ship (collisional hazard)
    for enemy in state_mgr.enemies[:]:
        enemy_spec = ships_cfg.get(enemy.enemy_type, {"radius": 0.4})
        enemy_rad = enemy_spec.get("radius", 0.4)
        
        if check_circle_overlap(enemy.x, enemy.y, enemy_rad, player.x, player.y, player_rad):
            if enemy in state_mgr.enemies:
                state_mgr.enemies.remove(enemy)
                
            # Crash damage is severe (passing player coordinates in case of shield copay)
            dmg = 30 if enemy.enemy_type == "mine" else 20
            state_mgr.take_damage(dmg, player.x, player.y)
            print(f"[Combat] Severe collision with pursuing {enemy.enemy_type}! HP reduced by {dmg}.")
            # Post crash collision event
            state_mgr.post_event(CollisionEvent(dmg, player.x, player.y))
            # Massive crash damage popup
            if enemy.enemy_type == "mine":
                safe_popup("MINE EXPLOSION! -30 HULL", player.x, player.y + 0.5, color=(1.0, 0.15, 0.05, 1.0), scale=0.55, lifetime=1.5)
            else:
                safe_popup(f"COLLISION! -{dmg} HULL", player.x, player.y + 0.5, color=(1.0, 0.1, 0.1, 1.0), scale=0.55, lifetime=1.5)

    # 4. Player Ship collecting floating rewards
    for pickup in state_mgr.pickups[:]:
        if check_circle_overlap(pickup.x, pickup.y, config.COLLISION_RADIUS_PICKUP, player.x, player.y, player_rad):
            if pickup in state_mgr.pickups:
                state_mgr.pickups.remove(pickup)
                if pickup.pickup_type in ["health", "speed", "missile"]:
                    state_mgr.trigger_bark("pickup")
                
            # Post pickup collection event
            state_mgr.post_event(PickupCollectedEvent(pickup.pickup_type, player.x, player.y))
            
            if pickup.pickup_type == "health":
                state_mgr.heal(25)
                state_mgr.add_score(5)
                print("[Inventory] Collected 'Emergency Duct Tape'! Rear hull integrity repaired by 25.")
                # Health popup
                safe_popup("+25 HULL", player.x, player.y + 0.5, color=(0.2, 1.0, 0.4, 1.0), scale=0.45, lifetime=1.2)
            elif pickup.pickup_type == "speed":
                # Increase reload fire-rates
                player.fire_rate_multiplier = min(3.0, player.fire_rate_multiplier + 0.3)
                state_mgr.add_score(5)
                print(f"[Inventory] Collected 'Totally Safe Space Snack'! Weapons cooling increased. Multiplier: {player.fire_rate_multiplier:.1f}")
                # Overclock popup
                safe_popup("COOLING OVERCLOCKED!", player.x, player.y + 0.5, color=(0.2, 0.6, 1.0, 1.0), scale=0.40, lifetime=1.2)
            elif pickup.pickup_type == "missile":
                # Collect secondary anti-matter missiles
                state_mgr.missile_ammo = min(config.MAX_MISSILES, state_mgr.missile_ammo + 2)
                state_mgr.add_score(10)
                print(f"[Inventory] Collected 'Anti-Matter Missile'! Ammo: {state_mgr.missile_ammo}/{config.MAX_MISSILES}")
                # Ammo popup
                safe_popup("+2 MISSILES", player.x, player.y + 0.5, color=(1.0, 0.6, 0.2, 1.0), scale=0.45, lifetime=1.2)
            elif pickup.pickup_type == "shield":
                state_mgr.liability_shield_active = True
                state_mgr.trigger_bark("shield")
                state_mgr.add_score(15)
                print("[Inventory] Collected 'Liability Waiver'! Shield active.")
                safe_popup("LIABILITY WAIVER SIGNED! (SHIELD)", player.x, player.y + 0.5, color=(0.2, 0.8, 1.0, 1.0), scale=0.42, lifetime=1.5)
            elif pickup.pickup_type == "bomb":
                state_mgr.bomb_ammo = min(3, state_mgr.bomb_ammo + 1)
                state_mgr.add_score(15)
                print(f"[Inventory] Collected 'Executive Decision'! Ammo: {state_mgr.bomb_ammo}/3")
                safe_popup("+1 EXECUTIVE DECISION", player.x, player.y + 0.5, color=(1.0, 120/255, 0.0, 1.0), scale=0.42, lifetime=1.5)
            elif pickup.pickup_type == "magnet":
                state_mgr.magnet_active_timer = 12.0
                state_mgr.trigger_bark("magnet")
                state_mgr.add_score(15)
                from space_demo.core.events import MagnetActivatedEvent
                state_mgr.post_event(MagnetActivatedEvent(player.x, player.y, 12.0))
                print("[Inventory] Collected 'Synergy Magnet'! Asset pooling active.")
                safe_popup("+12s SYNERGY MAGNET", player.x, player.y + 0.5, color=(180/255, 80/255, 1.0, 1.0), scale=0.42, lifetime=1.5)
            elif pickup.pickup_type == "intern":
                state_mgr.intern_active_timer = 15.0
                state_mgr.intern_shoot_cooldown = 0.0
                state_mgr.trigger_bark("intern")
                state_mgr.add_score(15)
                from space_demo.core.events import InternActivatedEvent
                state_mgr.post_event(InternActivatedEvent(player.x, player.y, 15.0))
                print("[Inventory] Collected 'Unpaid Intern Drone'! Delegated labor active.")
                safe_popup("+15s UNPAID INTERN", player.x, player.y + 0.5, color=(0.2, 0.8, 1.0, 1.0), scale=0.42, lifetime=1.5)
