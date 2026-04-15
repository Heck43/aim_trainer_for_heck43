from panda3d.core import NodePath, Point3, Vec3
from direct.interval.IntervalGlobal import Sequence, Parallel, Wait, LerpPosInterval, LerpHprInterval


class WeaponManagerNew:
    """Управляет оружием, прицеливанием, отдачей и разбросом"""

    def __init__(self, game):
        self.game = game

        # Weapon definitions
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
                    "base": 0.015,
                    "max": 0.12,
                    "moving_mult": 1.8,
                    "jumping_mult": 2.5,
                    "recovery_time": 0.08
                },
                "sound": "sounds/revik.wav"
            }
        }

        # Current weapon state
        self.current_weapon = "rifle"
        self.shoot_cooldown = self.weapons[self.current_weapon]["cooldown"]
        self.recoil_time = 0.05
        self.is_shooting = False
        self.shoot_state_frames = 0
        self.shoot_time = 0
        self.original_weapon_pos = None
        self.original_weapon_hpr = None

        # Recoil parameters
        self.recoil_pitch = 0
        self.recoil_yaw = 0
        self.max_recoil_pitch = 2.0
        self.max_recoil_yaw = 1.0
        self.recoil_recovery_speed = 5.0
        self.recoil_recovery_delay = 0.1
        self.last_shot_time = 0

        # Spread
        self.current_spread = 0.0

        # Aiming
        self.is_aiming = False
        self.aim_transition = 0.0
        self.ads_sensitivity_multiplier = 0.6

        # Weapon models
        self.weapon = None
        self.weapon_models = {}
        self.weapon_model = None
        self.weapon_animation = None
        self.is_drawing_weapon = False

        # ADS positions
        self.default_weapon_pos = {}
        self.ads_weapon_pos = {}
        self.ads_fov = {}

    def setup_weapon(self):
        """Создает модели оружия"""
        self.weapon = NodePath("weapon")
        self.weapon.reparentTo(self.game.camera)

        self.weapon_models = {}

        # Create pistol
        pistol = self._create_pistol()
        self.weapon_models["pistol"] = pistol

        # Create rifle
        rifle = self._create_rifle()
        self.weapon_models["rifle"] = rifle

        # Create sniper
        sniper = self._create_sniper()
        self.weapon_models["sniper"] = sniper

        # Create dual revolvers
        dual_revolvers = self._create_dual_revolvers()
        self.weapon_models["dual_revolvers"] = dual_revolvers

        # Show current weapon
        for weapon_name, model in self.weapon_models.items():
            if weapon_name == self.current_weapon:
                model.show()
            else:
                model.hide()

        self.update_weapon_position()

        self.original_weapon_pos = self.weapon.getPos()
        self.original_weapon_hpr = self.weapon.getHpr()

        # Setup ADS positions
        self._setup_ads_positions()

    def _create_pistol(self):
        """Создает модель пистолета"""
        pistol = NodePath("pistol")
        pistol.reparentTo(self.weapon)

        barrel = self.game.safe_load_model("models/box")
        barrel.setScale(0.08, 0.4, 0.08)
        barrel.setPos(0, 1.0, -0.1)
        barrel.setColor(0.2, 0.2, 0.2)
        barrel.reparentTo(pistol)

        grip = self.game.safe_load_model("models/box")
        grip.setScale(0.1, 0.1, 0.25)
        grip.setPos(0, 0.8, -0.3)
        grip.setColor(0.3, 0.3, 0.3)
        grip.reparentTo(pistol)

        return pistol

    def _create_rifle(self):
        """Создает модель винтовки"""
        rifle = NodePath("rifle")
        rifle.reparentTo(self.weapon)

        barrel = self.game.safe_load_model("models/box")
        barrel.setScale(0.06, 0.8, 0.06)
        barrel.setPos(0, 1.2, -0.1)
        barrel.setColor(0.2, 0.2, 0.2)
        barrel.reparentTo(rifle)

        body = self.game.safe_load_model("models/box")
        body.setScale(0.1, 0.4, 0.12)
        body.setPos(0, 0.8, -0.1)
        body.setColor(0.25, 0.25, 0.25)
        body.reparentTo(rifle)

        stock = self.game.safe_load_model("models/box")
        stock.setScale(0.08, 0.3, 0.15)
        stock.setPos(0, 0.4, -0.15)
        stock.setColor(0.3, 0.3, 0.3)
        stock.reparentTo(rifle)

        grip = self.game.safe_load_model("models/box")
        grip.setScale(0.08, 0.1, 0.2)
        grip.setPos(0, 0.7, -0.3)
        grip.setColor(0.3, 0.3, 0.3)
        grip.reparentTo(rifle)

        return rifle

    def _create_sniper(self):
        """Создает модель снайперской винтовки"""
        sniper = NodePath("sniper")
        sniper.reparentTo(self.weapon)

        barrel = self.game.safe_load_model("models/box")
        barrel.setScale(0.05, 1.0, 0.05)
        barrel.setPos(0, 1.5, -0.1)
        barrel.setColor(0.2, 0.2, 0.2)
        barrel.reparentTo(sniper)

        body = self.game.safe_load_model("models/box")
        body.setScale(0.1, 0.5, 0.15)
        body.setPos(0, 1.0, -0.1)
        body.setColor(0.25, 0.25, 0.25)
        body.reparentTo(sniper)

        stock = self.game.safe_load_model("models/box")
        stock.setScale(0.08, 0.4, 0.15)
        stock.setPos(0, 0.6, -0.15)
        stock.setColor(0.3, 0.3, 0.3)
        stock.reparentTo(sniper)

        grip = self.game.safe_load_model("models/box")
        grip.setScale(0.08, 0.1, 0.2)
        grip.setPos(0, 0.9, -0.3)
        grip.setColor(0.3, 0.3, 0.3)
        grip.reparentTo(sniper)

        return sniper

    def _create_dual_revolvers(self):
        """Создает модель двух револьверов"""
        dual_revolvers = NodePath("dual_revolvers")
        dual_revolvers.reparentTo(self.weapon)

        left_revolver = NodePath("left_revolver")
        left_revolver.reparentTo(dual_revolvers)
        left_revolver.setPos(-2.0, 0.6, -0.2)

        right_revolver = NodePath("right_revolver")
        right_revolver.reparentTo(dual_revolvers)
        right_revolver.setPos(0.4, 0.6, -0.2)

        for revolver in [left_revolver, right_revolver]:
            barrel = self.game.safe_load_model("models/box")
            barrel.setScale(0.06, 0.3, 0.06)
            barrel.setPos(0, 0.8, 0)
            barrel.setColor(0.2, 0.2, 0.2)
            barrel.reparentTo(revolver)

            cylinder = self.game.safe_load_model("models/box")
            cylinder.setScale(0.1, 0.15, 0.1)
            cylinder.setPos(0, 0.6, 0)
            cylinder.setColor(0.3, 0.3, 0.3)
            cylinder.reparentTo(revolver)

            grip = self.game.safe_load_model("models/box")
            grip.setScale(0.08, 0.1, 0.2)
            grip.setPos(0, 0.5, -0.15)
            grip.setColor(0.4, 0.2, 0.1)
            grip.reparentTo(revolver)

        return dual_revolvers

    def _setup_ads_positions(self):
        """Настраивает позиции для прицеливания"""
        for weapon in self.weapons:
            self.default_weapon_pos[weapon] = {
                "pos": Point3(0.7, 1.0, -0.5),
                "hpr": Vec3(0, 0, 0)
            }
            self.ads_weapon_pos[weapon] = {
                "pos": Point3(0, 1.2, -0.3),
                "hpr": Vec3(0, 0, 0)
            }

        self.ads_fov = {
            "pistol": 60,
            "rifle": 55,
            "sniper": 30,
            "dual_revolvers": 60
        }

    def update_weapon_position(self):
        """Обновляет позицию оружия на основе настроек"""
        if not hasattr(self, 'weapon') or self.weapon is None or self.weapon.isEmpty():
            return

        if 'weapon_position' not in self.game.settings:
            self.game.settings['weapon_position'] = self.game.DEFAULT_SETTINGS['weapon_position'].copy()

        x = self.game.settings['weapon_position'].get('x', self.game.DEFAULT_SETTINGS['weapon_position']['x'])
        y = self.game.settings['weapon_position'].get('y', self.game.DEFAULT_SETTINGS['weapon_position']['y'])
        z = self.game.settings['weapon_position'].get('z', self.game.DEFAULT_SETTINGS['weapon_position']['z'])

        self.weapon.setPos(x, y, z)
        self.original_weapon_pos = self.weapon.getPos()
        self.original_weapon_hpr = self.weapon.getHpr()

        self.game.settings_manager.save_settings()

    def animate_weapon_recoil(self):
        """Анимирует отдачу оружия"""
        if not hasattr(self, 'weapon') or self.weapon is None or self.weapon.isEmpty():
            return

        if self.original_weapon_pos is None or self.original_weapon_hpr is None:
            return

        recoil_offset = Vec3(0, -0.1, 0.05)
        recoil_rotation = Vec3(5, 0, 0)

        target_pos = self.original_weapon_pos + recoil_offset
        target_hpr = self.original_weapon_hpr + recoil_rotation

        self.weapon.setPos(target_pos)
        self.weapon.setHpr(target_hpr)

        recovery_time = 0.1

        def recover_weapon(task):
            if task.time >= recovery_time:
                self.weapon.setPos(self.original_weapon_pos)
                self.weapon.setHpr(self.original_weapon_hpr)
                return task.done

            t = task.time / recovery_time
            current_pos = target_pos + (self.original_weapon_pos - target_pos) * t
            current_hpr = target_hpr + (self.original_weapon_hpr - target_hpr) * t

            self.weapon.setPos(current_pos)
            self.weapon.setHpr(current_hpr)

            return task.cont

        self.game.taskMgr.add(recover_weapon, "weapon_recoil_recovery")

    def switch_weapon(self, weapon_name):
        """Переключает оружие"""
        if self.game.is_splash_screen_active:
            return

        if weapon_name in self.weapon_models and weapon_name != self.current_weapon:
            if self.weapon_animation:
                self.weapon_animation.finish()
                self.weapon_animation = None

            if self.current_weapon:
                self.weapon_models[self.current_weapon].hide()

            self.current_weapon = weapon_name
            self.weapon_model = self.weapon_models[weapon_name]
            self.weapon_model.show()
            self.game.shader_system.rebind_scene_objects()

            self.shoot_cooldown = self.weapons[weapon_name]["cooldown"]
            self.last_shot_time = 0

            self.play_weapon_draw_animation()

    def play_weapon_draw_animation(self):
        """Проигрывает анимацию доставания оружия"""
        if self.weapon_animation:
            self.weapon_animation.finish()
            self.weapon_animation = None

        self.is_drawing_weapon = True

        if self.current_weapon == "dual_revolvers":
            left_revolver = self.weapon_models["dual_revolvers"].find("left_revolver")
            right_revolver = self.weapon_models["dual_revolvers"].find("right_revolver")

            left_revolver.setPos(0, -1.0, -0.5)
            right_revolver.setPos(0, -1.0, -0.5)
            left_revolver.setHpr(-180, 0, 180)
            right_revolver.setHpr(-180, 0, 180)

            left_sequence = Sequence(
                Parallel(
                    left_revolver.posInterval(
                        0.15,
                        Point3(-1.0, 0.2, -0.3),
                        startPos=Point3(0, -1.0, -0.5),
                        blendType='easeOut'
                    ),
                    left_revolver.hprInterval(
                        0.15,
                        Point3(-90, -30, 90),
                        startHpr=Point3(-180, 0, 180),
                        blendType='easeOut'
                    )
                ),
                Parallel(
                    left_revolver.posInterval(
                        0.25,
                        Point3(-2.0, 0.6, -0.2),
                        blendType='easeOut'
                    ),
                    left_revolver.hprInterval(
                        0.25,
                        Point3(0, 0, 0),
                        blendType='easeOut'
                    )
                )
            )

            right_sequence = Sequence(
                Wait(0.1),
                Parallel(
                    right_revolver.posInterval(
                        0.15,
                        Point3(0.0, 0.2, -0.3),
                        startPos=Point3(0, -1.0, -0.5),
                        blendType='easeOut'
                    ),
                    right_revolver.hprInterval(
                        0.15,
                        Point3(-90, -30, 90),
                        startHpr=Point3(-180, 0, 180),
                        blendType='easeOut'
                    )
                ),
                Parallel(
                    right_revolver.posInterval(
                        0.25,
                        Point3(0.4, 0.6, -0.2),
                        blendType='easeOut'
                    ),
                    right_revolver.hprInterval(
                        0.25,
                        Point3(0, 0, 0),
                        blendType='easeOut'
                    )
                )
            )

            self.weapon_animation = Parallel(
                left_sequence,
                right_sequence,
                name="dual_revolvers_draw"
            )

            self.weapon_animation.start()
        else:
            self.weapon_model.setPos(0.25, 0.6, -1.0)
            self.weapon_model.setHpr(30, -30, 0)

            pos_interval = LerpPosInterval(
                self.weapon_model,
                duration=0.4,
                pos=Point3(0.25, 0.6, -0.3),
                startPos=Point3(0.25, 0.6, -1.0),
                blendType='easeOut'
            )

            rot_interval = LerpHprInterval(
                self.weapon_model,
                duration=0.4,
                hpr=Vec3(0, 0, 0),
                startHpr=Vec3(30, -30, 0),
                blendType='easeOut'
            )

            self.weapon_animation = Parallel(
                pos_interval,
                rot_interval,
                name="weapon_draw"
            )

        def finish_animation():
            self.is_drawing_weapon = False
            self.weapon_animation = None

        self.weapon_animation.setDoneEvent('weaponDrawComplete')
        self.game.accept('weaponDrawComplete', finish_animation)

        self.weapon_animation.start()

    def start_aiming(self):
        """Начинает прицеливание"""
        self.is_aiming = True

    def stop_aiming(self):
        """Останавливает прицеливание"""
        self.is_aiming = False

    def update_aim(self, task):
        """Обновляет анимацию прицеливания"""
        if self.is_aiming and self.aim_transition < 1.0:
            self.aim_transition = min(1.0, self.aim_transition + 0.1)
        elif not self.is_aiming and self.aim_transition > 0.0:
            self.aim_transition = max(0.0, self.aim_transition - 0.1)

        default_pos = self.default_weapon_pos[self.current_weapon]["pos"]
        ads_pos = self.ads_weapon_pos[self.current_weapon]["pos"]
        current_pos = default_pos + (ads_pos - default_pos) * self.aim_transition

        self.weapon_models[self.current_weapon].setPos(current_pos)

        default_fov = self.game.settings["fov"]
        target_fov = default_fov + (self.ads_fov[self.current_weapon] - default_fov) * self.aim_transition
        self.game.camLens.setFov(target_fov)

        base_sensitivity = self.game.settings["sensitivity"]

        if self.is_aiming:
            sensitivity = base_sensitivity * self.ads_sensitivity_multiplier
        else:
            sensitivity = base_sensitivity

        self.game.mouse_sensitivity = sensitivity

        return task.cont
