import sys
import random
import math
from direct.showbase.ShowBase import ShowBase
from panda3d.core import OrthographicLens, CardMaker, LineSegs, NodePath, Filename, TransparencyAttrib, Texture, TextureStage
from space_demo import config
from space_demo.core.state import GameStateManager
from space_demo.core.ids import GameStateID
from space_demo.gameplay.player import Player
from space_demo.gameplay.combat import resolve_collisions
from space_demo.ui.hud import GameHUD
from space_demo.ui.screens import GameMenuScreens
from space_demo.presentation.primitives import (
    create_player_ship_geom,
    create_textured_xz_quad,
    create_arrow_geom
)

# Import new modular presentation and input components
from space_demo.presentation.assets import AssetManager
from space_demo.presentation.vfx import VFXManager, PostFXManager
from space_demo.presentation.view_sync import ViewSyncManager
from space_demo.presentation.actor_orientation import player_bank_roll
from space_demo.input.controls import InputManager

class SpaceDisasterApp(ShowBase):
    """Main Panda3D application coordinator orchestrating decoupled pure gameplay simulation models, presentation views, and input handlers."""
    def __init__(self, headless=False, profile_path=None, default_profile_path=None, player_ships_path=None, ship_adapter=None):
        self.headless = headless
        
        # Load persisted settings
        from space_demo.core.settings_store import load_settings
        self.settings = load_settings()

        # Load player profile and ship definitions
        from space_demo.profile.store import ProfileStore
        from space_demo.profile.runtime import ShipRuntimeAdapter
        from pathlib import Path
        import tempfile

        self._temp_profile_dir = None
        if profile_path is None and self.headless:
            self._temp_profile_dir = tempfile.TemporaryDirectory()
            profile_path = Path(self._temp_profile_dir.name) / "profile.json"

        self.profile_error = None
        self.profile = None
        self.profile_store = None
        self.ship_adapter = None
        self.current_ship_def = None

        try:
            self.profile_store = ProfileStore(
                profile_path=profile_path,
                default_profile_path=default_profile_path
            )
            self.profile = self.profile_store.load_profile()
            if ship_adapter is not None:
                self.ship_adapter = ship_adapter
            else:
                self.ship_adapter = ShipRuntimeAdapter(player_ships_path=player_ships_path)
            self.current_ship_def = self.ship_adapter.resolve_selected_ship(self.profile)
        except Exception as e:
            import sys
            print(f"[Profile] Failed to initialize profile: {e}", file=sys.stderr)
            self.profile_error = str(e)
            self.profile = None
            self.current_ship_def = None

        self.state_mgr = GameStateManager(ship_def=self.current_ship_def)
        # Propagate settings immediately to state manager
        self.state_mgr.difficulty = self.settings.difficulty
        self.state_mgr.coop_mode = self.settings.coop_mode
        self.state_mgr.vfx_high = self.settings.vfx_high
        self.state_mgr.intro_active = self.settings.show_intro
        self.state_mgr.load_wave_params()
        
        self._run_active = False
        self._post_run_integrated = False

        self.player = Player(ship_def=self.current_ship_def)
        
        # Maps gameplay simulation models to Panda3D presentation nodes
        self.enemy_views = {}
        self.projectile_views = {}
        self.pickup_views = {}
        self.boss_view = None
        self.floating_popups = [] # Lists active floating 3D text nodes in gameplay
        self.active_3d_state_nodes = [] # Main Menu, Game Over, and Victory 3D texts
        
        # Setup core keyboard controls bindings state dictionary
        self.keys = {
            "left": False,
            "right": False,
            "up": False,
            "down": False,
            "space": False,
            "arrow_left": False,
            "arrow_right": False,
            "arrow_up": False,
            "arrow_down": False
        }
        
        # Initialize ShowBase first so that self.loader exists!
        if self.headless:
            ShowBase.__init__(self)
            self.stars = []
        else:
            # Set window size config variables prior to initializing ShowBase
            from panda3d.core import loadPrcFileData
            w, h = self.settings.resolution
            loadPrcFileData("", f"win-size {w} {h}")
            if self.settings.fullscreen:
                loadPrcFileData("", "fullscreen #t")
            else:
                loadPrcFileData("", "fullscreen #f")
                
            ShowBase.__init__(self)
            
            # Disable default mouse camera control to prevent trackball hijacking
            self.disableMouse()
            
            # Setup title
            if self.win:
                from panda3d.core import WindowProperties
                props = WindowProperties()
                props.setTitle("To Boldly Respawn: A Co-Op Space Disaster (Flipped Chase)")
                self.win.requestProperties(props)
                # Bind clean window-close button events
                self.win.setCloseRequestEvent("window-close-request")
                self.accept("window-close-request", self.clean_quit)
            
            # Setup orthographic camera lens looking onto native XZ screen plane
            lens = OrthographicLens()
            aspect = self.getAspectRatio()
            # 20 height maps beautifully to BOUNDS_Y with extra margins, width dynamically scales to prevent squishing
            lens.setFilmSize(20.0 * aspect, 20.0)
            lens.setNearFar(-100.0, 100.0) # Open up depth clipping range
            self.cam.node().setLens(lens)
            self.camera.setPos(0.0, -10.0, 0.0) # Position back along depth (-Y)
            self.camera.lookAt(0.0, 0.0, 0.0)    # Look straight along +Y at flat XZ plane
            
            # Setup window resize handler to update lens film size dynamically
            self.accept("window-event", self.handle_window_event)
            
        # Initialize our decoupled modular components (now that self.loader is fully bound)
        self.assets_mgr = AssetManager(self)
        self.vfx_mgr = VFXManager(self)
        self.postfx_mgr = PostFXManager(self)
        self.view_sync = ViewSyncManager(self)
        
        # Set up starfield, background, audio, inputs, HUD, and task loop
        if not self.headless:
            self.setup_starfield()
            
            # Create professional start screen spaceship bridge console backdrop
            menu_bg_geom = create_textured_xz_quad(30.0, 30.0)
            self.menu_bg_np = NodePath(menu_bg_geom)
            self.menu_bg_np.reparentTo(self.render)
            self.menu_bg_np.setTexture(self.assets_mgr.menu_bg_tex)
            self.menu_bg_np.setTwoSided(True)
            self.menu_bg_np.setLightOff()
            self.menu_bg_np.setPos(0.0, 40.0, 0.0) # Render at Y=40.0 (in front of Z star scroller, behind ships)
            self.menu_bg_np.setBin("background", 1)
            self.menu_bg_np.setDepthWrite(False)
            
            # Create player visual representation (positioned at X, 0.0, Y in XZ plane)
            player_geom = create_player_ship_geom()
            self.player_np = NodePath(player_geom)
            self.player_np.reparentTo(self.render)
            self.player_np.setPos(self.player.x, 0.0, self.player.y)
            self.player_np.setTwoSided(True)
            self.player_np.setLightOff()
            self.player_np.setTexture(self.assets_mgr.player_tex)
            self.player_np.setTransparency(TransparencyAttrib.MAlpha)
            self.player_np.setDepthWrite(False)
            
            # Procedural fading downward chevron arrow to hint rear-firing mechanic
            arrow_geom = create_arrow_geom()
            self.hint_arrow_np = NodePath(arrow_geom)
            self.hint_arrow_np.reparentTo(self.player_np)
            self.hint_arrow_np.setPos(0.0, -0.1, -2.2) # Position below player ship card
            self.hint_arrow_np.setScale(0.8)
            self.hint_arrow_np.setTwoSided(True)
            self.hint_arrow_np.setLightOff()

            # Create premium rotating holographic Liability Waiver Shield visual card
            shield_geom = create_textured_xz_quad(3.0, 3.0)
            self.shield_bubble_np = NodePath(shield_geom)
            self.shield_bubble_np.reparentTo(self.player_np)
            self.shield_bubble_np.setPos(0.0, -0.05, 0.0) # Prevent visual Z-fighting with player card
            self.shield_bubble_np.setTwoSided(True)
            self.shield_bubble_np.setLightOff()
            self.shield_bubble_np.setTexture(self.assets_mgr.shield_skin_tex)
            self.shield_bubble_np.setTransparency(TransparencyAttrib.MAlpha)
            self.shield_bubble_np.setDepthWrite(False)
            self.shield_bubble_np.hide() # Hidden by default
            
            self.hint_arrow_np.setTransparency(TransparencyAttrib.MAlpha)
            self.hint_arrow_np.setDepthWrite(False)
            self.hint_arrow_timer = 10.0
            self.intern_drone_np = None
            
        # Audio and dynamic settings variables
        self.alarm_timer = 0.0
        self.load_audio()
        
        if not self.headless:
            # Setup HUD and menu overlays
            self.hud = GameHUD(app=self, font=self.assets_mgr.consolas_font)
            self.screens = GameMenuScreens(self, self.assets_mgr.consolas_font)
            self.screens.update_screen_state(self.state_mgr.current_state)
            self.set_cursor_visible(True)
            
            # Start game loop task
            self.taskMgr.add(self.update_game, "updateGame")
            print("[System] Graphics initialized, game loop active.")
            
        # Bind controls
        self.input_mgr = InputManager(self)

    def set_cursor_visible(self, visible):
        if not self.headless and self.win:
            from panda3d.core import WindowProperties
            props = WindowProperties()
            props.setCursorHidden(not visible)
            self.win.requestProperties(props)

    def sync_cursor_for_current_state(self):
        state = self.state_mgr.current_state
        menu_sub_state = getattr(self.screens, "menu_sub_state", "main") if hasattr(self, "screens") else "main"
        intro_active = getattr(self.state_mgr, "intro_active", False)

        cursor_visible = False

        if state in (
            GameStateID.MENU,
            GameStateID.PAUSED,
            GameStateID.GAMEOVER,
            GameStateID.VICTORY,
        ):
            cursor_visible = True
        elif state == GameStateID.PLAYING and intro_active:
            cursor_visible = True

        # If any modal is visible, force cursor
        if hasattr(self, "screens") and self.screens:
            if hasattr(self.screens, "confirm_modal") and not self.screens.confirm_modal.isHidden():
                cursor_visible = True

        self.set_cursor_visible(cursor_visible)

    def update_3d_menu_texts(self):
        if self.headless:
            return
            
        # Clean out old state nodes
        if hasattr(self, "active_3d_state_nodes"):
            for np in self.active_3d_state_nodes:
                np.removeNode()
        self.active_3d_state_nodes = []
        
        # Access font
        if not self.assets_mgr.consolas_font_3d:
            return
            
        from panda3d.core import TextNode, TransparencyAttrib
        
        state = self.state_mgr.current_state
        if state == GameStateID.MENU and self.screens.menu_sub_state == "main":
            # Main Menu uses the premium Pillow generated title banner texture now; skip 3D rotating text node.
            pass
            
        elif state == GameStateID.GAMEOVER:
            # Game over 3D Title
            tn = TextNode("gameover_3d_title")
            tn.setText("TACTICAL FAILURE")
            tn.setFont(self.assets_mgr.consolas_font_3d)
            tn.setTextColor((1.0, 0.1, 0.1, 1.0)) # Flashing Red
            tn.setAlign(TextNode.ACenter)
            tn.setShadow(0.06, -0.06)
            tn.setShadowColor(0.0, 0.0, 0.0, 0.9)
            
            geom = tn.generate()
            np = self.aspect2d.attachNewNode(geom)
            np.setPos(0.20, 0.0, 0.35)
            np.setScale(0.08)
            np.setTwoSided(True)
            np.setLightOff()
            np.setTransparency(TransparencyAttrib.MAlpha)
            np.setDepthWrite(False)
            self.active_3d_state_nodes.append(np)
            
        elif state == GameStateID.VICTORY:
            # Victory 3D Title
            tn = TextNode("victory_3d_title")
            tn.setText("DISASTER MANAGED!")
            tn.setFont(self.assets_mgr.consolas_font_3d)
            tn.setTextColor((0.2, 1.0, 0.5, 1.0)) # Neon Green
            tn.setAlign(TextNode.ACenter)
            tn.setShadow(0.06, -0.06)
            tn.setShadowColor(0.0, 0.0, 0.0, 0.9)
            
            geom = tn.generate()
            np = self.aspect2d.attachNewNode(geom)
            np.setPos(0.20, 0.0, 0.35)
            np.setScale(0.08)
            np.setTwoSided(True)
            np.setLightOff()
            np.setTransparency(TransparencyAttrib.MAlpha)
            np.setDepthWrite(False)
            self.active_3d_state_nodes.append(np)

    def load_audio(self):
        from space_demo.presentation.audio import AudioManager
        self.audio_mgr = AudioManager(self)

    def play_sound(self, sfx):
        self.audio_mgr.play_sound(sfx)

    @property
    def laser_sfx(self):
        return self.audio_mgr.laser_sfx

    @property
    def missile_sfx(self):
        return self.audio_mgr.missile_sfx

    @property
    def explosion_sfx(self):
        return self.audio_mgr.explosion_sfx

    @property
    def pickup_sfx(self):
        return self.audio_mgr.pickup_sfx

    @property
    def alarm_sfx(self):
        return self.audio_mgr.alarm_sfx

    @property
    def menu_music(self):
        return self.audio_mgr.menu_music

    @property
    def chase_music(self):
        return self.audio_mgr.chase_music

    def clear_views(self):
        # Cleans out visual references upon session resets
        for np in self.enemy_views.values(): np.removeNode()
        for np in self.projectile_views.values(): np.removeNode()
        for np in self.pickup_views.values(): np.removeNode()
        if self.boss_view:
            self.boss_view.removeNode()
            self.boss_view = None
        if self.intern_drone_np:
            self.intern_drone_np.removeNode()
            self.intern_drone_np = None
            
        self.enemy_views.clear()
        self.projectile_views.clear()
        self.pickup_views.clear()

        # Clear active floating popups safely
        if hasattr(self, "floating_popups"):
            for popup in self.floating_popups:
                popup["np"].removeNode()
            self.floating_popups.clear()

        # Reset active particle trails to pool to prevent leaks on session restarts
        if hasattr(self, "vfx_mgr") and self.vfx_mgr:
            self.vfx_mgr.reset()

        # Clear active 3D text nodes safely
        if hasattr(self, "active_3d_state_nodes"):
            for np in self.active_3d_state_nodes:
                np.removeNode()
            self.active_3d_state_nodes.clear()
            
        # Reset 3D menu texts sync state
        self.prev_3d_state = None
        self.prev_3d_substate = None

    def clean_quit(self):
        print("[System] Clean quit requested by window close event. Exiting game process.")
        try:
            self.destroy()
        except Exception:
            pass
        import sys
        sys.exit(0)

    def handle_window_event(self, window):
        self.windowEvent(window)
        if window is not None:
            try:
                if window.isClosed():
                    self.clean_quit()
            except Exception:
                pass
            aspect = self.getAspectRatio()
            lens = self.cam.node().getLens()
            lens.setFilmSize(20.0 * aspect, 20.0)

    def setup_starfield(self):
        if self.win:
            self.win.setClearColor((0.01, 0.01, 0.03, 1.0))
            
        import os
        bg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "space_background.png"))
        bg_tex = self.loader.loadTexture(Filename.fromOsSpecific(bg_path))
        bg_tex.setWrapU(Texture.WM_repeat)
        bg_tex.setWrapV(Texture.WM_repeat)
        
        card_geom = create_textured_xz_quad(30.0, 30.0) 
        self.bg_card = NodePath(card_geom)
        self.bg_card.reparentTo(self.render)
        self.bg_card.setTexture(bg_tex)
        self.bg_card.setTwoSided(True)
        self.bg_card.setLightOff()
        self.bg_card.setPos(0.0, 50.0, 0.0)
        self.bg_card.setBin("background", 0)
        self.bg_card.setDepthWrite(False)
        self.bg_scroll = 0.0
            
        self.stars = []
        star_geom = create_textured_xz_quad(0.02, 0.02)
        
        for _ in range(40):
            star_np = NodePath(star_geom)
            star_np.reparentTo(self.render)
            star_np.setTwoSided(True)
            star_np.setLightOff()
            star_np.setTransparency(TransparencyAttrib.MAlpha)
            star_np.setDepthWrite(False)
            
            rx = random.uniform(config.BOUNDS_X_MIN - 1.0, config.BOUNDS_X_MAX + 1.0)
            rz = random.uniform(config.BOUNDS_Y_MIN - 1.0, config.BOUNDS_Y_MAX + 1.0)
            star_np.setPos(rx, 20.0, rz)
            
            b = random.uniform(0.3, 0.9)
            star_np.setColor(b, b, b, b)
            speed_scale = random.uniform(0.5, 1.2)
            self.stars.append((star_np, speed_scale))

    def update_starfield(self, dt):
        if self.state_mgr.current_state == GameStateID.PAUSED:
            return
        scroll_speed = 0.05
        self.bg_scroll += scroll_speed * dt
        self.bg_card.setTexOffset(TextureStage.getDefault(), 0.0, self.bg_scroll)
            
        for star_np, scale in self.stars:
            curr_z = star_np.getZ()
            next_z = curr_z + (-0.8 * scale * dt)
            
            if next_z < config.BOUNDS_Y_MIN - 1.0:
                next_z = config.BOUNDS_Y_MAX + 1.0
                star_np.setX(random.uniform(config.BOUNDS_X_MIN - 1.0, config.BOUNDS_X_MAX + 1.0))
                
            star_np.setZ(next_z)

    def process_events(self):
        """Processes and drains the decoupled pure-Python game simulation event queue."""
        if self.headless:
            self.state_mgr.events.clear()
            return
            
        from space_demo.core.events import (
            PopupEvent, ShieldBrokenEvent, ExecutiveDecisionEvent,
            PickupCollectedEvent, NotificationEvent
        )
        
        while self.state_mgr.events:
            event = self.state_mgr.events.pop(0)
            if isinstance(event, NotificationEvent):
                if hasattr(self.hud, "notifications") and self.hud.notifications:
                    self.hud.notifications.push(
                        title=event.title,
                        message=event.message,
                        category=event.category,
                        severity=event.severity,
                        icon=event.icon,
                        value=event.value,
                        duration=event.duration
                    )
            elif isinstance(event, PopupEvent):
                self.vfx_mgr.spawn_floating_popup(
                    event.text, event.x, event.y,
                    color=event.color, scale=event.scale, lifetime=event.lifetime
                )
            elif isinstance(event, ShieldBrokenEvent):
                # Play crisp procedural explosion sound on breaking shield
                self.play_sound(self.audio_mgr.explosion_sfx)
                self.vfx_mgr.spawn_shield_shatter_burst(event.x, event.y)
                self.vfx_mgr.trigger_screen_shake(0.25)
                if hasattr(self.hud, "notifications") and self.hud.notifications:
                    self.hud.notifications.push(
                        title="Waiver Broken",
                        message="Copay Applied to Rear Hull",
                        category="shield",
                        severity="danger"
                    )
            elif isinstance(event, ExecutiveDecisionEvent):
                self.vfx_mgr.handle_executive_decision_event(event)
                if hasattr(self.hud, "notifications") and self.hud.notifications:
                    self.hud.notifications.push(
                        title="Executive Decision",
                        message="Strategic KPI Bomb deployed!",
                        category="bomb",
                        severity="special"
                    )
            elif isinstance(event, PickupCollectedEvent):
                if hasattr(self.hud, "notifications") and self.hud.notifications:
                    if event.pickup_type == "health":
                        self.hud.notifications.push(
                            title="Emergency Duct Tape",
                            message="+25 HULL REPAIRED",
                            category="pickup",
                            severity="success"
                        )
                    elif event.pickup_type == "speed":
                        self.hud.notifications.push(
                            title="Cooling Overclocked",
                            message="WEAPONS COOLING UPGRADED",
                            category="pickup",
                            severity="success"
                        )
                    elif event.pickup_type == "missile":
                        self.hud.notifications.push(
                            title="+2 Anti-Matter Missiles",
                            message="SECONDARY MUNITIONS LOADED",
                            category="pickup",
                            severity="success"
                        )
                    elif event.pickup_type == "shield":
                        self.hud.notifications.push(
                            title="Liability Waiver Active",
                            message="CORPORATE INDEMNITY SHIELD ACTIVE",
                            category="shield",
                            severity="system"
                        )
                    elif event.pickup_type == "bomb":
                        self.hud.notifications.push(
                            title="+1 Executive Decision",
                            message="KPI TACTICAL BOMB ACQUIRED",
                            category="pickup",
                            severity="success"
                        )
                    elif event.pickup_type == "magnet":
                        self.hud.notifications.push(
                            title="Synergy Magnet Active",
                            message="ASSET ATTRACTION FIELDS ENABLED",
                            category="magnet",
                            severity="system"
                        )
                    elif event.pickup_type == "intern":
                        self.hud.notifications.push(
                            title="Unpaid Intern Deployed",
                            message="DELEGATED DOWNWARD LASER ACTIVE",
                            category="intern",
                            severity="system"
                        )


    def step_simulation(self, dt):
        # Update visual effects and camera offsets even during victory/gameover
        if not self.headless and hasattr(self, "vfx_mgr") and self.vfx_mgr:
            if self.state_mgr.current_state in (
                GameStateID.PLAYING,
                GameStateID.VICTORY,
                GameStateID.GAMEOVER,
            ):
                self.vfx_mgr.update(dt)
                if self.state_mgr.current_state == GameStateID.PLAYING:
                    if hasattr(self, "player") and self.player:
                        self.vfx_mgr.spawn_engine_glow(self.player.x, self.player.y)

        if self.state_mgr.current_state != GameStateID.PLAYING:
            return

        # Pure logical simulation updates
        self.state_mgr.update_simulation_tick(dt, player_x=self.player.x, player_y=self.player.y)
        self.player.tick_cooldown(dt)

        # Update Liability Waiver Shield & active Synergy Magnet visual representation
        if not self.headless and hasattr(self, "shield_bubble_np"):
            if self.state_mgr.liability_shield_active and self.state_mgr.current_state == GameStateID.PLAYING:
                self.shield_bubble_np.show()
                self.shield_bubble_np.setR(self.shield_bubble_np.getR() + 35.0 * dt)
                scale_pulse = 1.0 + 0.04 * math.sin(self.clock.getFrameTime() * 8.0)
                self.shield_bubble_np.setScale(scale_pulse)
                if self.state_mgr.magnet_active_timer > 0.0:
                    # Flash between cyan and purple when both shield and magnet are active
                    glow_factor = 0.5 + 0.5 * math.sin(self.clock.getFrameTime() * 12.0)
                    self.shield_bubble_np.setColorScale(160/255 * glow_factor, 120/255 * glow_factor, 1.0, 0.85)
                else:
                    self.shield_bubble_np.setColorScale(1.0, 1.0, 1.0, 1.0) # Normal cyan/white
            elif self.state_mgr.magnet_active_timer > 0.0 and self.state_mgr.current_state == GameStateID.PLAYING:
                # Synergy Magnet active on its own: purple pulsating consolidation ring
                self.shield_bubble_np.show()
                self.shield_bubble_np.setR(self.shield_bubble_np.getR() - 25.0 * dt)
                scale_pulse = 1.1 + 0.05 * math.sin(self.clock.getFrameTime() * 5.0)
                self.shield_bubble_np.setScale(scale_pulse)
                self.shield_bubble_np.setColorScale(180/255, 80/255, 1.0, 0.5) # Neon Violet
            else:
                self.shield_bubble_np.hide()
        
        # Update first-run/opening downward laser hint chevron
        if not self.headless and hasattr(self, "hint_arrow_np") and self.state_mgr.current_state == GameStateID.PLAYING:
            if hasattr(self, "hint_arrow_timer") and self.hint_arrow_timer > 0.0:
                self.hint_arrow_timer -= dt
                if self.hint_arrow_timer <= 0.0:
                    self.hint_arrow_np.hide()
                else:
                    # Gentle pulsating glow and gradual fade
                    pulsate = 0.55 + 0.45 * math.sin(self.clock.getFrameTime() * 9.0)
                    alpha = min(1.0, self.hint_arrow_timer / 3.0) * pulsate
                    self.hint_arrow_np.setColorScale(1.0, 1.0, 1.0, alpha)
            else:
                self.hint_arrow_np.hide()
        
        # Read controls only in playing state
        if self.state_mgr.current_state == GameStateID.PLAYING:
            dx = 0.0
            dy = 0.0
            if hasattr(self, "keys") and self.keys:
                if self.state_mgr.coop_mode:
                    # CO-OP MODE:
                    # Pilot steers using WASD (left/right/up/down keys)
                    if self.keys["left"]: dx = -1.0
                    if self.keys["right"]: dx = 1.0
                    if self.keys["up"]: dy = 1.0
                    if self.keys["down"]: dy = -1.0
                    
                    # Gunner fires using Arrow Keys (arrow_left/arrow_right/arrow_up/arrow_down)
                    fired_laser = False
                    laser_dx = 0.0
                    if self.keys["arrow_up"] and self.player.can_fire():
                        fired_laser = True
                        laser_dx = 0.0
                    elif self.keys["arrow_left"] and self.player.can_fire():
                        fired_laser = True
                        laser_dx = -1.8 # Tilted leftward
                    elif self.keys["arrow_right"] and self.player.can_fire():
                        fired_laser = True
                        laser_dx = 1.8 # Tilted rightward
                        
                    if fired_laser:
                        self.state_mgr.spawn_projectile(
                            self.player.x, self.player.y - 0.5,
                            is_player_owned=True, dx=laser_dx, proj_type="laser"
                        )
                        self.player.reset_cooldown()
                        self.play_sound(self.audio_mgr.laser_sfx)
                        self.vfx_mgr.spawn_muzzle_flash(self.player.x + (laser_dx * 0.1), self.player.y - 0.6, scale=1.0)
                else:
                    # SINGLE PLAYER MODE:
                    # Steer with WASD or Arrow Keys
                    if self.keys["left"] or self.keys["arrow_left"]: dx = -1.0
                    if self.keys["right"] or self.keys["arrow_right"]: dx = 1.0
                    if self.keys["up"] or self.keys["arrow_up"]: dy = 1.0
                    if self.keys["down"] or self.keys["arrow_down"]: dy = -1.0
                    
                    # Firing weapon with Spacebar
                    if self.keys["space"] and self.player.can_fire():
                        self.state_mgr.spawn_projectile(
                            self.player.x, self.player.y - 0.5,
                            is_player_owned=True, dx=0.0, proj_type="laser"
                        )
                        self.player.reset_cooldown()
                        self.play_sound(self.audio_mgr.laser_sfx)
                        self.vfx_mgr.spawn_muzzle_flash(self.player.x, self.player.y - 0.6, scale=1.0)
            
            if dx != 0.0 or dy != 0.0:
                self.player.move(dx, dy, dt)
                
            resolve_collisions(self.state_mgr, self.player)
            self.process_events()

        # Trigger repeating chaser engine proximity alarm siren SFX (every 1 second)
        if self.state_mgr.current_state == GameStateID.PLAYING and self.state_mgr.chase_gap <= config.DREADNOUGHT_CRITICAL_GAP:
            self.alarm_timer += dt
            if self.alarm_timer >= 1.0:
                self.alarm_timer = 0.0
                self.play_sound(self.audio_mgr.alarm_sfx)
        else:
            self.alarm_timer = 0.0

        # Synchronize NodePath coordinate renders
        if not self.headless:
            # Automatically update 3D menu titles when state/substate transitions occur
            curr_state = self.state_mgr.current_state
            curr_sub = self.screens.menu_sub_state
            if (curr_state != getattr(self, "prev_3d_state", None) or 
                curr_sub != getattr(self, "prev_3d_substate", None)):
                self.prev_3d_state = curr_state
                self.prev_3d_substate = curr_sub
                self.update_3d_menu_texts()

            # Animate active 3D state nodes (hovering titles, pulsating failure alerts)
            if hasattr(self, "active_3d_state_nodes") and len(self.active_3d_state_nodes) > 0:
                np_3d = self.active_3d_state_nodes[0]
                t_frame = self.clock.getFrameTime()
                if self.state_mgr.current_state == GameStateID.MENU and self.screens.menu_sub_state == "main":
                    # Slow hover up and down and gentle rotation
                    np_3d.setZ(0.48 + math.sin(t_frame * 2.0) * 0.015)
                    np_3d.setR(math.sin(t_frame * 1.5) * 2.0)
                    
                    # Hologram laser color flicker pulse
                    glow = 0.85 + 0.15 * math.sin(t_frame * 8.0)
                    if random.random() < 0.04: # random hologram terminal flicker!
                        glow *= 0.65
                    np_3d.setColorScale(glow, glow, 1.0, 1.0)
                elif self.state_mgr.current_state in (GameStateID.GAMEOVER, GameStateID.VICTORY):
                    # Pulsate scale and red/green alert glow flicker
                    scale_mult = 1.0 + math.sin(t_frame * 3.0) * 0.05
                    np_3d.setScale(0.08 * scale_mult)
                    glow = 0.90 + 0.10 * math.sin(t_frame * 12.0)
                    if random.random() < 0.03:
                        glow *= 0.70
                    np_3d.setColorScale(glow, glow, glow, 1.0)

            # Animate active menu frames with a gentle floating holographic sway
            if self.state_mgr.current_state != GameStateID.PLAYING:
                t_frame = self.clock.getFrameTime()
                sway_x = math.sin(t_frame * 1.2) * 0.015
                float_z = math.cos(t_frame * 0.8) * 0.010
                for frame in [self.screens.menu_frame, self.screens.tutorial_frame, self.screens.settings_frame, self.screens.gameover_frame, self.screens.victory_frame, self.screens.paused_frame]:
                    if not frame.isHidden():
                        frame.setPos(sway_x, 0, float_z)

            self.player_np.setPos(self.player.x, 0.0, self.player.y) # Map to XZ
            
            # Smooth visual roll/tilt on horizontal steering.
            target_roll = 0.0
            if self.state_mgr.current_state == GameStateID.PLAYING:
                left_pressed = self.keys.get("left", False)
                right_pressed = self.keys.get("right", False)
                if not self.state_mgr.coop_mode:
                    left_pressed = left_pressed or self.keys.get("arrow_left", False)
                    right_pressed = right_pressed or self.keys.get("arrow_right", False)
                target_roll = player_bank_roll(left_pressed, right_pressed)

            current_roll = self.player_np.getR()
            new_roll = current_roll + (target_roll - current_roll) * 12.0 * dt
            self.player_np.setR(new_roll)

            # Synchronize friendly Unpaid Intern Drone visual sidecar model
            if self.state_mgr.intern_active_timer > 0.0:
                if self.intern_drone_np is None:
                    from space_demo.presentation.primitives import create_chaser_drone_geom
                    drone_geom = create_chaser_drone_geom()
                    self.intern_drone_np = NodePath(drone_geom)
                    self.intern_drone_np.reparentTo(self.render)
                    self.intern_drone_np.setTwoSided(True)
                    self.intern_drone_np.setLightOff()
                    self.intern_drone_np.setTexture(self.assets_mgr.drone_tex)
                    self.intern_drone_np.setTransparency(TransparencyAttrib.MAlpha)
                    self.intern_drone_np.setDepthWrite(False)
                    self.intern_drone_np.setColorScale(0.4, 0.8, 1.0, 1.0) # Premium light-cyan tint!
                
                t = self.clock.getFrameTime()
                offset_x = -1.5 + math.sin(t * 3.0) * 0.2
                offset_z = 0.5 + math.cos(t * 2.0) * 0.1
                self.intern_drone_np.setPos(self.player.x + offset_x, 0.0, self.player.y + offset_z)
            else:
                if self.intern_drone_np is not None:
                    self.intern_drone_np.removeNode()
                    self.intern_drone_np = None
            
            # Handle visibility and UI layers based on active playing state
            if self.state_mgr.current_state == GameStateID.PLAYING:
                self.player_np.show()
                self.menu_bg_np.hide() # Hide bridge console backdrop card during active simulation
                self.screens.hide_all()
                self.view_sync.sync_views()
                self.hud.update(self.state_mgr, self.player, dt)
            elif self.state_mgr.current_state == GameStateID.PAUSED:
                self.player_np.show()
                self.menu_bg_np.hide()
                self.screens.update_screen_state(GameStateID.PAUSED)
                self.view_sync.sync_views()
            elif self.state_mgr.current_state == GameStateID.VICTORY:
                self.player_np.show()
                self.hud.hide()
                self.menu_bg_np.hide()
                # Stop chase track, return to menu ambient chiptune
                if self.audio_mgr.chase_music and self.audio_mgr.chase_music.status() == self.audio_mgr.chase_music.PLAYING:
                    self.audio_mgr.chase_music.stop()
                    if self.audio_mgr.menu_music:
                        self.audio_mgr.menu_music.play()
                self.screens.update_screen_state(self.state_mgr.current_state)
                self.view_sync.sync_views()
            elif self.state_mgr.current_state == GameStateID.GAMEOVER:
                self.player_np.hide()
                self.hud.hide()
                self.menu_bg_np.hide()
                # Stop chase track, return to menu ambient chiptune
                if self.audio_mgr.chase_music and self.audio_mgr.chase_music.status() == self.audio_mgr.chase_music.PLAYING:
                    self.audio_mgr.chase_music.stop()
                    if self.audio_mgr.menu_music:
                        self.audio_mgr.menu_music.play()
                self.screens.update_screen_state(self.state_mgr.current_state)
                self.clear_views()
            else: # MENU state
                self.player_np.hide()
                self.hud.hide()
                self.menu_bg_np.show() # Show spaceship bridge console card backdrop!
                # Start menu chiptune track loop
                if self.audio_mgr.menu_music and self.audio_mgr.menu_music.status() != self.audio_mgr.menu_music.PLAYING:
                    if self.audio_mgr.chase_music:
                        self.audio_mgr.chase_music.stop()
                    self.audio_mgr.menu_music.play()
                self.screens.update_screen_state(self.state_mgr.current_state)
                self.clear_views()
                
            self.sync_cursor_for_current_state()
            self.update_starfield(dt)

    def update_game(self, task):
        dt = self.clock.getDt()
        if dt > 0.1:
            dt = 0.1
            
        if not self.headless and self.win:
            aspect = self.getAspectRatio()
            lens = self.cam.node().getLens()
            current_size = lens.getFilmSize()
            expected_width = 20.0 * aspect
            if abs(current_size[0] - expected_width) > 0.001:
                lens.setFilmSize(expected_width, 20.0)
                
        previous_state = self.state_mgr.current_state
        self.step_simulation(dt)
        current_state = self.state_mgr.current_state

        # Transition-aware post-run integration detection logic
        if current_state == GameStateID.PLAYING:
            self._run_active = True
            self._post_run_integrated = False
        elif getattr(self, "_run_active", False):
            if current_state in (GameStateID.VICTORY, GameStateID.GAMEOVER):
                self.handle_post_run_integration()
                self._run_active = False
            elif current_state == GameStateID.MENU:
                self._run_active = False
                self._post_run_integrated = False
        elif current_state == GameStateID.MENU:
            self._run_active = False
            self._post_run_integrated = False

        if task is not None:
            return task.cont

    def handle_post_run_integration(self):
        """Constructs a GameplaySnapshot and updates all quest progress at the end of a run."""
        # One-shot guard
        if getattr(self, "_post_run_integrated", False):
            return
        self._post_run_integrated = True

        if not self.profile or not self.profile_store:
            return

        from space_demo.profile.runtime import (
            build_gameplay_snapshot_from_state,
            apply_quest_progress_for_snapshot,
            QuestProgressionService
        )

        snapshot = build_gameplay_snapshot_from_state(self.state_mgr)
        if snapshot is None:
            print("[Quest] No map context available. Skipping quest integration.")
            return

        print(f"[Quest] Processing post-run integration with snapshot: {snapshot}")

        try:
            quest_service = QuestProgressionService()
            new_profile, reward_ids = apply_quest_progress_for_snapshot(
                self.profile, snapshot, quest_service
            )
            
            # Save the updated profile atomically via existing persistence mechanism
            self.profile_store.save_profile(new_profile)
            self.profile = new_profile
            
            if reward_ids:
                print(f"[Quest] Completed quest rewards surfaced: {reward_ids}")
        except Exception as e:
            print(f"[Quest] Failed to update quest progression: {e}")

    def rebuild_ui(self):
        if self.headless:
            return
            
        print(f"[System] Rebuilding UI with UI scale {self.settings.ui_scale} and text scale {self.settings.text_scale}...")
        
        # Capture current menu sub state and current game state
        curr_state = self.state_mgr.current_state
        menu_sub = getattr(self.screens, "menu_sub_state", "main") if hasattr(self, "screens") else "main"
        
        # Destroy existing screens and HUD
        if hasattr(self, "screens") and self.screens:
            self.screens.destroy()
            self.screens = None
            
        if hasattr(self, "hud") and self.hud:
            self.hud.destroy()
            self.hud = None
            
        # Recreate HUD and screens with the new settings
        self.hud = GameHUD(app=self, font=self.assets_mgr.consolas_font)
        self.screens = GameMenuScreens(self, self.assets_mgr.consolas_font)
        
        # Restore active state views
        if curr_state == GameStateID.MENU and menu_sub == "settings":
            self.screens.on_settings_click(from_menu=False)
        elif curr_state == GameStateID.MENU and menu_sub == "fleet":
            self.screens.on_fleet_click()
        else:
            self.screens.menu_sub_state = menu_sub
            self.screens.update_screen_state(curr_state)
        
        # Sync cursor and visibility
        self.sync_cursor_for_current_state()
        if curr_state == GameStateID.PLAYING:
            self.hud.show()
