# managers/weapons_manager.py
from panda3d.core import *
from direct.interval.IntervalGlobal import *
import random

class WeaponsManager:
    """Manages weapons: models, switching, shooting logic"""

    def __init__(self, game):
        self.game = game
        self.current_weapon = "rifle"
        self.can_shoot = True
        self.shoot_cooldown = 0.1
        self.last_shot_time = 0
        self.weapon_models = {}
        self.weapon = None
        self.weapon_model = None
        self.active_revolver = "left"
        self.weapon_animation = None
        self.is_drawing_weapon = False

        # Weapon stats (from main.py)
        self.weapons = {
            "pistol": {
                "cooldown": 0.2,
                "damage": 25,
                "recoil": {
                    "pitch": (0.5, 1.0),
                    "yaw": (0.3, 0.3)
                },
                "spread": {
                    "base": 0.02,
                    "max": 0.15,
                    "moving_mult": 1.5,
                    "jumping_mult": 2.0,
                    "recovery_time": 0.1
                },
                "sound": "sounds/pistol_shot.wav"
            },
            "rifle": {
                "cooldown": 0.1,
                "damage": 20,
                "recoil": {
                    "pitch": (0.3, 0.6),
                    "yaw": (-0.2, 0.2)
                },
                "spread": {
                    "base": 0.015,
                    "max": 0.12,
                    "moving_mult": 1.8,
                    "jumping_mult": 2.5,
                    "recovery_time": 0.08
                },
                "sound": "sounds/rifle_shot.wav"
            },
            "sniper": {
                "cooldown": 1.0,
                "damage": 100,
                "recoil": {
                    "pitch": (2.0, 3.0),
                    "yaw": (-0.1, 0.1)
                },
                "spread": {
                    "base": 0.001,
                    "max": 0.05,
                    "moving_mult": 5.0,
                    "jumping_mult": 10.0,
                    "recovery_time": 0.5
                },
                "sound": "sounds/sniper_shot.wav"
            },
            "dual_revolvers": {
                "cooldown": 0.1,
                "damage": 20,
                "recoil": {
                    "pitch": (0.3, 0.6),
                    "yaw": (-0.2, 0.2)
                },
                "spread": {
                    "base": 0.02,
                    "max": 0.12,
                    "moving_mult": 1.5,
                    "jumping_mult": 2.0,
                    "recovery_time": 0.1
                },
                "sound": "sounds/revik.wav"
            }
        }

        self.current_spread = 0.0

    def setup(self):
        """Creates weapon models"""
        self.weapon = NodePath("weapon")
        self.weapon.reparentTo(self.game.camera)

        # Create pistol
        self.create_pistol()
        # Create rifle
        self.create_rifle()
        # Create sniper
        self.create_sniper()
        # Create dual revolvers
        self.create_dual_revolvers()

        # Show current weapon
        self.switch_weapon(self.current_weapon)

    def create_pistol(self):
        """Creates pistol model"""
        pistol = NodePath("pistol")
        pistol.reparentTo(self.weapon)

        barrel = self.game.loader.loadModel("models/box")
        barrel.setScale(0.08, 0.4, 0.08)
        barrel.setPos(0, 1.0, -0.1)
        barrel.setColor(0.2, 0.2, 0.2)
        barrel.reparentTo(pistol)

        grip = self.game.loader.loadModel("models/box")
        grip.setScale(0.1, 0.1, 0.25)
        grip.setPos(0, 0.8, -0.3)
        grip.setColor(0.3, 0.3, 0.3)
        grip.reparentTo(pistol)

        self.weapon_models["pistol"] = pistol

    def create_rifle(self):
        """Creates rifle model"""
        rifle = NodePath("rifle")
        rifle.reparentTo(self.weapon)

        barrel = self.game.loader.loadModel("models/box")
        barrel.setScale(0.06, 0.8, 0.06)
        barrel.setPos(0, 1.2, -0.1)
        barrel.setColor(0.2, 0.2, 0.2)
        barrel.reparentTo(rifle)

        body = self.game.loader.loadModel("models/box")
        body.setScale(0.1, 0.4, 0.12)
        body.setPos(0, 0.8, -0.1)
        body.setColor(0.25, 0.25, 0.25)
        body.reparentTo(rifle)

        self.weapon_models["rifle"] = rifle

    def create_sniper(self):
        """Creates sniper model"""
        sniper = NodePath("sniper")
        sniper.reparentTo(self.weapon)

        barrel = self.game.loader.loadModel("models/box")
        barrel.setScale(0.05, 1.0, 0.05)
        barrel.setPos(0, 1.5, -0.1)
        barrel.setColor(0.2, 0.2, 0.2)
        barrel.reparentTo(sniper)

        scope = self.game.loader.loadModel("models/box")
        scope.setScale(0.08, 0.3, 0.08)
        scope.setPos(0, 1.0, 0.1)
        scope.setColor(0.1, 0.1, 0.1)
        scope.reparentTo(sniper)

        self.weapon_models["sniper"] = sniper

    def create_dual_revolvers(self):
        """Creates dual revolvers model"""
        revolvers = NodePath("dual_revolvers")
        revolvers.reparentTo(self.weapon)

        # Left revolver
        left = NodePath("left_revolver")
        left.reparentTo(revolvers)
        left.setPos(-0.2, 0.6, -0.2)

        left_barrel = self.game.loader.loadModel("models/box")
        left_barrel.setScale(0.06, 0.3, 0.06)
        left_barrel.setPos(0, 0.2, 0)
        left_barrel.setColor(0.2, 0.2, 0.2)
        left_barrel.reparentTo(left)

        # Right revolver
        right = NodePath("right_revolver")
        right.reparentTo(revolvers)
        right.setPos(0.2, 0.6, -0.2)

        right_barrel = self.game.loader.loadModel("models/box")
        right_barrel.setScale(0.06, 0.3, 0.06)
        right_barrel.setPos(0, 0.2, 0)
        right_barrel.setColor(0.2, 0.2, 0.2)
        right_barrel.reparentTo(right)

        self.weapon_models["dual_revolvers"] = revolvers

    def switch_weapon(self, weapon_name):
        """Switches to specified weapon"""
        if weapon_name not in self.weapon_models:
            return

        # Hide all weapons
        for name, model in self.weapon_models.items():
            model.hide()

        # Show selected weapon
        self.current_weapon = weapon_name
        self.weapon_model = self.weapon_models[weapon_name]
        self.weapon_model.show()

        # Update cooldown
        self.shoot_cooldown = self.weapons[weapon_name]["cooldown"]
        self.last_shot_time = 0

    def can_shoot_now(self):
        """Checks if weapon can shoot"""
        current_time = globalClock.getFrameTime()
        return self.can_shoot and (current_time - self.last_shot_time >= self.shoot_cooldown)

    def shoot(self):
        """Handles shooting (simplified - main logic still in main.py)"""
        if not self.can_shoot_now():
            return False

        self.last_shot_time = globalClock.getFrameTime()

        # Play sound
        weapon_params = self.weapons[self.current_weapon]
        try:
            shot_sound = self.game.loader.loadSfx(weapon_params["sound"])
            shot_sound.play()
        except:
            pass

        # For dual revolvers, alternate
        if self.current_weapon == "dual_revolvers":
            self.active_revolver = "right" if self.active_revolver == "left" else "left"

        return True

    def get_current_weapon_params(self):
        """Returns current weapon parameters"""
        return self.weapons[self.current_weapon]

    def update(self, dt):
        """Update weapon state"""
        # Spread recovery
        if self.current_spread > 0:
            weapon_params = self.weapons[self.current_weapon]
            if "spread" in weapon_params:
                recovery_rate = weapon_params["spread"]["base"] / weapon_params["spread"]["recovery_time"]
                self.current_spread = max(0, self.current_spread - recovery_rate * dt)

    def update_weapon_position(self):
        """Updates weapon position based on settings"""
        if not self.weapon or self.weapon.isEmpty():
            return

        weapon_pos = self.game.settings.get('weapon_position', {
            'x': 0.25,
            'y': 0.6,
            'z': -0.3
        })

        x = weapon_pos.get('x', 0.25)
        y = weapon_pos.get('y', 0.6)
        z = weapon_pos.get('z', -0.3)

        self.weapon.setPos(x, y, z)
