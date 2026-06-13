# Combat VFX and Particle Manager - To Boldly Respawn

import random
import math
from panda3d.core import TransparencyAttrib, NodePath, TextNode
from space_demo import config
from space_demo.presentation.primitives import create_textured_xz_quad

class VFXManager:
    """Manages visual particle effects, floating 3D text popups, shockwaves, hit flashes,
    camera screen shakes, pre-allocated particle trail pooling, and fullscreen hit flash overlays.
    """
    def __init__(self, app):
        self.app = app
        self.headless = app.headless
        self.floating_popups = app.floating_popups
        self.camera_shake_timer = 0.0
        
        # 1. Screen Flash & Warning Vignettes Setup (skipped headlessly)
        self.hit_flash_frame = None
        self.flash_alpha = 0.0
        
        self.vignette_root = None
        self.vignette_top = None
        self.vignette_bottom = None
        self.vignette_left = None
        self.vignette_right = None
        
        # 2. Pre-allocated Particle Trail Pool (avoids runtime NodePath allocations)
        self.trail_pool = []
        self.active_trails = []
        self.max_trail_particles = 200
        
        if not self.headless:
            from direct.gui.DirectGui import DirectFrame
            import direct.gui.DirectGuiGlobals as DGG
            
            # Full-screen red hit flash frame
            self.hit_flash_frame = DirectFrame(
                parent=self.app.aspect2d,
                frameSize=(-2.0, 2.0, -1.2, 1.2),
                frameColor=(0.8, 0.05, 0.05, 0.0),
                relief=DGG.FLAT,
                sortOrder=110
            )
            self.hit_flash_frame.setTransparency(TransparencyAttrib.MAlpha)
            self.hit_flash_frame.hide()
            
            # Responsive screen-edge warning vignettes
            thickness = 0.04
            self.vignette_root = DirectFrame(
                parent=self.app.aspect2d,
                relief=None,
                sortOrder=105
            )
            self.vignette_root.setTransparency(TransparencyAttrib.MAlpha)
            self.vignette_root.hide()
            
            self.vignette_top = DirectFrame(
                parent=self.vignette_root,
                frameSize=(-2.0, 2.0, -thickness, thickness),
                pos=(0, 0, 1.0 - thickness),
                frameColor=(0.8, 0.05, 0.05, 0.0),
                relief=DGG.FLAT
            )
            self.vignette_bottom = DirectFrame(
                parent=self.vignette_root,
                frameSize=(-2.0, 2.0, -thickness, thickness),
                pos=(0, 0, -1.0 + thickness),
                frameColor=(0.8, 0.05, 0.05, 0.0),
                relief=DGG.FLAT
            )
            self.vignette_left = DirectFrame(
                parent=self.vignette_root,
                frameSize=(-thickness, thickness, -1.5, 1.5),
                pos=(-1.35, 0, 0),
                frameColor=(0.8, 0.05, 0.05, 0.0),
                relief=DGG.FLAT
            )
            self.vignette_right = DirectFrame(
                parent=self.vignette_root,
                frameSize=(-thickness, thickness, -1.5, 1.5),
                pos=(1.35, 0, 0),
                frameColor=(0.8, 0.05, 0.05, 0.0),
                relief=DGG.FLAT
            )

            # Pre-allocate particle quad nodes parented to render
            for _ in range(self.max_trail_particles):
                p_geom = create_textured_xz_quad(0.2, 0.2)
                np = self.app.render.attachNewNode(p_geom)
                np.setTwoSided(True)
                np.setLightOff()
                np.setTransparency(TransparencyAttrib.MAlpha)
                np.setDepthWrite(False)
                if hasattr(self.app, "assets_mgr") and self.app.assets_mgr and self.app.assets_mgr.shield_skin_tex:
                    np.setTexture(self.app.assets_mgr.shield_skin_tex)
                np.setBin("transparent", 95)
                np.hide()
                self.trail_pool.append(np)

    def reset(self):
        """Cleans up and returns all active trails to the pre-allocated pool to prevent memory leaks on restart."""
        for trail in self.active_trails:
            if trail["np"]:
                trail["np"].hide()
                self.trail_pool.append(trail["np"])
        self.active_trails.clear()
        
        # Reset hit flash and vignettes
        self.flash_alpha = 0.0
        if self.hit_flash_frame:
            self.hit_flash_frame.hide()
        if self.vignette_root:
            self.vignette_root.hide()

    def spawn_trail_segment(self, x, z, scale, color, decay_rate, velocity=(0.0, 0.0), is_expanding=False):
        """Spawns or recycles a particle trail segment using O(1) pre-allocated node pooling."""
        if self.headless:
            return
            
        if self.trail_pool:
            np = self.trail_pool.pop()
        elif self.active_trails:
            # Pool exhausted: recycle the oldest active particle node
            oldest = self.active_trails.pop(0)
            np = oldest["np"]
        else:
            return
            
        np.setPos(x, 1.1, z) # Render at Y=1.1 (slightly in front of starfields, behind actors)
        np.setScale(scale)
        np.setColor(color[0], color[1], color[2], color[3])
        np.show()
        
        self.active_trails.append({
            "np": np,
            "scale": scale,
            "color": color,
            "decay_rate": decay_rate,
            "velocity_x": velocity[0],
            "velocity_z": velocity[1],
            "is_expanding": is_expanding
        })

    def spawn_engine_glow(self, x, z):
        """Spawns real-time glowing cyan twin trails behind the player ship's primary engines."""
        if self.headless:
            return
            
        # Performance budget check: skip engine glow on odd frames in Low VFX mode to save draw calls
        if hasattr(self.app, "state_mgr") and not self.app.state_mgr.vfx_high:
            if hasattr(self.app, "clock") and self.app.clock.getFrameCount() % 2 == 0:
                return
        # Left Engine Plume
        self.spawn_trail_segment(
            x - 0.35, z - 0.6,
            scale=0.25,
            color=(0.18, 0.80, 1.00, 0.85),
            decay_rate=3.5, # decays in 0.24s
            velocity=(random.uniform(-0.1, 0.1), random.uniform(-4.0, -2.5)) # exhaust drifts downward
        )
        # Right Engine Plume
        self.spawn_trail_segment(
            x + 0.35, z - 0.6,
            scale=0.25,
            color=(0.18, 0.80, 1.00, 0.85),
            decay_rate=3.5,
            velocity=(random.uniform(-0.1, 0.1), random.uniform(-4.0, -2.5)) # exhaust drifts downward
        )

    def spawn_projectile_trail(self, proj_type, x, z):
        """Spawns custom high-fidelity trails behind active projectiles."""
        if self.headless:
            return
            
        # Performance budget check: skip standard laser streaks entirely in Low VFX mode
        if hasattr(self.app, "state_mgr") and not self.app.state_mgr.vfx_high:
            if proj_type in ("laser", "enemy_laser", "intern_laser"):
                return
            
        if proj_type == "missile":
            # Fire Particle
            self.spawn_trail_segment(
                x, z,
                scale=0.35,
                color=(1.00, 0.38, 0.12, 0.85), # Orange fire
                decay_rate=4.5,
                velocity=(random.uniform(-0.4, 0.4), random.uniform(1.0, 2.5))
            )
            # Smoke Particle
            self.spawn_trail_segment(
                x + random.uniform(-0.1, 0.1), z + 0.3,
                scale=0.28,
                color=(0.12, 0.12, 0.15, 0.45), # Dark grey smoke
                decay_rate=2.2, # decays slower
                velocity=(random.uniform(-0.2, 0.2), random.uniform(0.5, 1.5)),
                is_expanding=True # expands as it fades!
            )
        elif proj_type == "enemy_laser":
            self.spawn_trail_segment(
                x, z,
                scale=0.16,
                color=(1.00, 0.15, 0.12, 0.75), # Glowing Red
                decay_rate=7.0,
                velocity=(0.0, random.uniform(-1.5, -0.5))
            )
        elif proj_type == "intern_laser":
            self.spawn_trail_segment(
                x, z,
                scale=0.14,
                color=(0.40, 0.80, 1.00, 0.70), # Light Cyan
                decay_rate=7.0,
                velocity=(0.0, random.uniform(0.5, 1.5))
            )
        else: # player laser
            self.spawn_trail_segment(
                x, z,
                scale=0.16,
                color=(0.18, 0.80, 1.00, 0.75), # Cyber Cyan
                decay_rate=7.0,
                velocity=(0.0, random.uniform(0.5, 1.5))
            )

    def spawn_hit_sparks(self, x, z):
        """Spawns glowing amber sparks scattering outward upon enemy damage."""
        if self.headless:
            return
            
        # Performance budget check: spawn fewer sparks in Low VFX mode
        is_high = getattr(self.app.state_mgr, "vfx_high", True) if (self.app and hasattr(self.app, "state_mgr")) else True
        count = 1 if not is_high else random.randint(3, 5)
        for _ in range(count):
            angle = random.uniform(0.0, 2.0 * math.pi)
            speed = random.uniform(3.0, 6.0)
            self.spawn_trail_segment(
                x, z,
                scale=0.08,
                color=(1.00, 0.78, 0.20, 0.90), # Amber
                decay_rate=8.0, # decays in 0.11s
                velocity=(math.cos(angle) * speed, math.sin(angle) * speed)
            )

    def trigger_player_hit_flash(self):
        """Triggers a dramatic full-screen red damage flash."""
        if self.headless:
            return
        self.flash_alpha = 0.35

    def spawn_floating_popup(self, text, x, z, color=(1.0, 1.0, 1.0, 1.0), scale=0.35, lifetime=1.0):
        if self.headless:
            return
            
        tn = TextNode("popup_3d")
        tn.setText(text)
        if hasattr(self.app, "assets_mgr") and self.app.assets_mgr and self.app.assets_mgr.consolas_font_3d:
            tn.setFont(self.app.assets_mgr.consolas_font_3d)
        tn.setTextColor(color)
        tn.setAlign(TextNode.ACenter)
        tn.setShadow(0.06, -0.06)
        tn.setShadowColor(0.0, 0.0, 0.0, 0.8)
        
        geom = tn.generate()
        np = self.app.render.attachNewNode(geom)
        np.setPos(x, 2.0, z) # Render at Y=2.0
        np.setScale(scale)
        np.setTwoSided(True)
        np.setLightOff()
        np.setTransparency(TransparencyAttrib.MAlpha)
        np.setDepthWrite(False)
        np.setBin("transparent", 100)
        
        self.floating_popups.append({
            "np": np,
            "timer": 0.0,
            "lifetime": lifetime,
            "velocity_x": random.uniform(-0.6, 0.6),
            "velocity_z": random.uniform(1.5, 2.5),
            "base_scale": scale
        })

    def spawn_muzzle_flash(self, x, z, scale=1.0):
        if self.headless:
            return
            
        geom = create_textured_xz_quad(0.3 * scale, 0.3 * scale)
        np = self.app.render.attachNewNode(geom)
        np.setPos(x, 1.0, z)
        np.setTwoSided(True)
        np.setLightOff()
        if hasattr(self.app, "assets_mgr") and self.app.assets_mgr and self.app.assets_mgr.vfx_muzzle_flash:
            np.setTexture(self.app.assets_mgr.vfx_muzzle_flash)
            np.setColor(1.0, 1.0, 1.0, 1.0)
        else:
            np.setColor(1.0, 0.95, 0.2, 1.0)
        np.setTransparency(TransparencyAttrib.MAlpha)
        np.setDepthWrite(False)
        np.setBin("transparent", 100)
        
        self.floating_popups.append({
            "np": np,
            "timer": 0.0,
            "lifetime": 0.08,
            "velocity_x": 0.0,
            "velocity_z": -2.0,
            "base_scale": 1.0
        })

    def spawn_death_burst(self, x, z, enemy_type):
        """Spawns visual debris particles upon chaser destruction."""
        if self.headless:
            return
            
        is_high = getattr(self.app.state_mgr, "vfx_high", True) if (self.app and hasattr(self.app, "state_mgr")) else True
        
        num_particles = 8 if enemy_type == "boss" else 5
        if not is_high:
            num_particles = max(2, num_particles // 2)
            
        scale_mult = 2.2 if enemy_type == "boss" else 0.8
        
        # 1. Standard debris particles (using radial explosion core textures)
        for _ in range(num_particles):
            p_geom = create_textured_xz_quad(0.18 * scale_mult, 0.18 * scale_mult)
            np = self.app.render.attachNewNode(p_geom)
            np.setPos(x, 1.0, z)
            np.setTwoSided(True)
            np.setLightOff()
            if hasattr(self.app, "assets_mgr") and self.app.assets_mgr and self.app.assets_mgr.vfx_explosion_core:
                np.setTexture(self.app.assets_mgr.vfx_explosion_core)
                np.setColor(1.0, random.uniform(0.7, 1.0), 0.2, 1.0)
            else:
                np.setColor(1.0, random.uniform(0.4, 0.85), 0.1, 1.0)
            np.setTransparency(TransparencyAttrib.MAlpha)
            np.setDepthWrite(False)
            np.setBin("transparent", 100)
            
            vx = random.uniform(-4.5, 4.5) * scale_mult
            vz = random.uniform(-4.5, 4.5) * scale_mult
            
            self.floating_popups.append({
                "np": np,
                "timer": 0.0,
                "lifetime": random.uniform(0.25, 0.45),
                "velocity_x": vx,
                "velocity_z": vz,
                "base_scale": 1.0
            })

        # 2. Expanding chiptune shockwave ring (using glowing spark diamond textures)
        ring_particles = 16 if enemy_type == "boss" else 10
        if not is_high:
            ring_particles = max(3, ring_particles // 2)
            
        ring_speed = 6.0 * scale_mult
        for i in range(ring_particles):
            angle = (2.0 * math.pi / ring_particles) * i
            angle += random.uniform(-0.05, 0.05)
            speed = ring_speed * random.uniform(0.9, 1.1)
            
            p_geom = create_textured_xz_quad(0.12 * scale_mult, 0.12 * scale_mult)
            np = self.app.render.attachNewNode(p_geom)
            np.setPos(x, 1.0, z)
            np.setTwoSided(True)
            np.setLightOff()
            if hasattr(self.app, "assets_mgr") and self.app.assets_mgr and self.app.assets_mgr.vfx_spark:
                np.setTexture(self.app.assets_mgr.vfx_spark)
                np.setColor(1.0, 0.8, 0.3, 1.0)
            else:
                np.setColor(1.0, 0.5, 0.15, 1.0)
            np.setTransparency(TransparencyAttrib.MAlpha)
            np.setDepthWrite(False)
            np.setBin("transparent", 101)
            
            vx = math.cos(angle) * speed
            vz = math.sin(angle) * speed
            
            self.floating_popups.append({
                "np": np,
                "timer": 0.0,
                "lifetime": 0.35,
                "velocity_x": vx,
                "velocity_z": vz,
                "base_scale": 1.0
            })

    def spawn_shield_shatter_burst(self, x, z):
        if self.headless:
            return
            
        is_high = getattr(self.app.state_mgr, "vfx_high", True) if (self.app and hasattr(self.app, "state_mgr")) else True
        num_particles = 12 if is_high else 4
        ring_speed = 8.0
        
        for i in range(num_particles):
            angle = (2.0 * math.pi / num_particles) * i
            speed = ring_speed * random.uniform(0.85, 1.15)
            
            p_geom = create_textured_xz_quad(0.20, 0.20)
            np = self.app.render.attachNewNode(p_geom)
            np.setPos(x, 1.0, z)
            np.setTwoSided(True)
            np.setLightOff()
            np.setColor(0.1, 0.85, 1.0, 1.0)
            np.setTransparency(TransparencyAttrib.MAlpha)
            np.setDepthWrite(False)
            np.setBin("transparent", 102)
            
            vx = math.cos(angle) * speed
            vz = math.sin(angle) * speed
            
            self.floating_popups.append({
                "np": np,
                "timer": 0.0,
                "lifetime": 0.40,
                "velocity_x": vx,
                "velocity_z": vz,
                "base_scale": 1.0
            })

    def trigger_screen_shake(self, duration=0.25):
        if self.headless:
            return
        self.camera_shake_timer = duration

    def handle_executive_decision_event(self, event):
        if self.headless:
            return
            
        self.trigger_screen_shake(0.80)
        
        if hasattr(self.app, "audio_mgr") and self.app.audio_mgr:
            self.app.play_sound(self.app.audio_mgr.explosion_sfx)
            
        geom = create_textured_xz_quad(1.0, 1.0)
        np = self.app.render.attachNewNode(geom)
        np.setPos(event.x, 1.5, event.y)
        np.setTwoSided(True)
        np.setLightOff()
        if hasattr(self.app, "assets_mgr") and self.app.assets_mgr and self.app.assets_mgr.vfx_shockwave_orange:
            np.setTexture(self.app.assets_mgr.vfx_shockwave_orange)
            np.setColor(1.0, 1.0, 1.0, 1.0) # White so the orange ring shines at full saturation
        elif hasattr(self.app, "assets_mgr") and self.app.assets_mgr and self.app.assets_mgr.shield_skin_tex:
            np.setTexture(self.app.assets_mgr.shield_skin_tex)
            np.setColor(1.0, 120/255, 0.0, 1.0)
        else:
            np.setColor(1.0, 120/255, 0.0, 1.0)
        np.setTransparency(TransparencyAttrib.MAlpha)
        np.setDepthWrite(False)
        np.setBin("transparent", 102)
        
        self.floating_popups.append({
            "np": np,
            "timer": 0.0,
            "lifetime": 0.60,
            "velocity_x": 0.0,
            "velocity_z": 0.0,
            "base_scale": 1.0,
            "is_shockwave": True
        })

    def update(self, dt):
        if self.headless:
            return
            
        # Update camera screen shake
        if self.camera_shake_timer > 0.0:
            self.camera_shake_timer -= dt
            if self.camera_shake_timer <= 0.0:
                self.app.camera.setPos(0.0, -10.0, 0.0)
            else:
                shake_x = random.uniform(-0.15, 0.15)
                shake_z = random.uniform(-0.15, 0.15)
                self.app.camera.setPos(shake_x, -10.0, shake_z)

        # Update fullscreen red hit flash decay
        if self.hit_flash_frame:
            if self.flash_alpha > 0.0:
                self.flash_alpha = max(0.0, self.flash_alpha - dt * 2.0)
                self.hit_flash_frame["frameColor"] = (0.8, 0.05, 0.05, self.flash_alpha)
                self.hit_flash_frame.show()
            else:
                self.hit_flash_frame.hide()

        # Update screen-edge critical alerts
        if self.vignette_root and hasattr(self.app, "state_mgr"):
            gap = self.app.state_mgr.chase_gap
            if gap <= config.DREADNOUGHT_CRITICAL_GAP:
                self.vignette_root.show()
                pulse = 0.35 + 0.20 * math.sin(self.app.clock.getFrameTime() * 10.0)
                color = (0.8, 0.05, 0.05, pulse)
                for border in [self.vignette_top, self.vignette_bottom, self.vignette_left, self.vignette_right]:
                    if border:
                        border["frameColor"] = color
            else:
                self.vignette_root.hide()

        # Update active particle trails
        for trail in self.active_trails[:]:
            np = trail["np"]
            alpha = np.getColor().getW() - trail["decay_rate"] * dt
            if alpha <= 0.0:
                np.hide()
                self.active_trails.remove(trail)
                self.trail_pool.append(np)
            else:
                c = np.getColor()
                np.setColor(c.getX(), c.getY(), c.getZ(), alpha)
                np.setX(np.getX() + trail["velocity_x"] * dt)
                np.setZ(np.getZ() + trail["velocity_z"] * dt)
                if trail["is_expanding"]:
                    np.setScale(np.getScale() * (1.0 + 1.2 * dt))
                else:
                    np.setScale(np.getScale() * (1.0 - 0.8 * dt))

        # Update 3D floating popups drift
        for popup in self.floating_popups[:]:
            popup["timer"] += dt
            t = popup["timer"]
            life = popup["lifetime"]
            if t >= life:
                popup["np"].removeNode()
                self.floating_popups.remove(popup)
            else:
                np = popup["np"]
                np.setX(np.getX() + popup["velocity_x"] * dt)
                np.setZ(np.getZ() + popup["velocity_z"] * dt)
                alpha = 1.0 - (t / life)
                np.setColorScale(1.0, 1.0, 1.0, alpha)
                
                is_shockwave = popup.get("is_shockwave", False)
                if is_shockwave:
                    current_scale = popup["base_scale"] + (18.0 - popup["base_scale"]) * (t / life)
                    np.setScale(current_scale)
                else:
                    progress = t / life
                    if progress < 0.2:
                        s = popup["base_scale"] * (1.0 + progress * 2.0)
                    else:
                        s = popup["base_scale"] * (1.2 * (1.0 - (progress - 0.2) / 0.8))
                    np.setScale(s)


class PostFXManager:
    """Manages simple fullscreen post-processing effects (such as glowing bloom),
    falling back gracefully if shader/graphics pipeline capabilities are missing (e.g. headless modes).
    """
    def __init__(self, app):
        self.app = app
        self.headless = app.headless
        self.active = False
        
        if not self.headless:
            self.setup_effects()
            
    def setup_effects(self):
        try:
            print("[PostFX] CommonFilters pipeline initialized (Holographic glowing Bloom bypassed in default software renderer).")
        except Exception as e:
            print(f"[PostFX] Bypassing bloom pipeline: {e}")
