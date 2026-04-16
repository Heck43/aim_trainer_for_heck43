import sys
import os
import sys

# Настройка PATH для DLL перед импортом Panda3D (для PyInstaller)
if hasattr(sys, 'frozen'):
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    
    # Проверяем папку _internal (новый формат PyInstaller)
    internal_dir = os.path.join(exe_dir, '_internal')
    paths_to_add = []
    
    if os.path.exists(internal_dir):
        paths_to_add.append(internal_dir)
        # Проверяем наличие libpandagl.dll для отладки
        pandagl_path = os.path.join(internal_dir, 'libpandagl.dll')
        if os.path.exists(pandagl_path):
            print(f"[OK] Found libpandagl.dll in: {internal_dir}")
        else:
            print(f"[WARN] libpandagl.dll NOT found in: {internal_dir}")
    
    # Также добавляем папку с exe
    paths_to_add.append(exe_dir)
    
    # Добавляем _MEIPASS если есть
    if hasattr(sys, '_MEIPASS'):
        meipass = sys._MEIPASS
        if meipass not in paths_to_add:
            paths_to_add.append(meipass)
    
    # Добавляем все пути в PATH и os.add_dll_directory
    for path in paths_to_add:
        if path and os.path.exists(path):
            if path not in os.environ.get('PATH', ''):
                os.environ['PATH'] = path + os.pathsep + os.environ.get('PATH', '')
            if sys.version_info >= (3, 8):
                try:
                    os.add_dll_directory(path)
                except (AttributeError, OSError) as e:
                    pass
    
    # Предзагружаем основные DLL через ctypes (для Windows)
    if os.path.exists(internal_dir):
        try:
            import ctypes
            # Загружаем основные DLL в правильном порядке
            dlls_to_preload = [
                'libpanda.dll',
                'libpandaexpress.dll',
                'libp3dtool.dll',
                'libp3dtoolconfig.dll',
                'libpandagl.dll'
            ]
            for dll_name in dlls_to_preload:
                dll_path = os.path.join(internal_dir, dll_name)
                if os.path.exists(dll_path):
                    try:
                        ctypes.CDLL(dll_path)
                        print(f"[OK] Preloaded: {dll_name}")
                    except Exception as e:
                        print(f"[ERROR] Failed to load {dll_name}: {e}")
        except ImportError:
            pass
    
    # Устанавливаем переменную окружения для Panda3D
    if os.path.exists(internal_dir):
        os.environ['PANDA_PLUGIN_PATH'] = internal_dir
        os.environ['PANDA_DLL_PATH'] = internal_dir
        # Также устанавливаем PRC_DIR для Config.prc
        os.environ['PRC_DIR'] = exe_dir
    
    # Отладочный вывод
    print(f"Настроен PATH для DLL:")
    for path in paths_to_add:
        if path and os.path.exists(path):
            print(f"  - {path}")

try:
    from imgui_bundle import imgui
    from imgui_bundle import ImVec2
    import p3dimgui
    from managers.imgui_patches import apply_imgui_patches
    apply_imgui_patches()
    HAS_P3D_IMGUI = True
except Exception:
    p3dimgui = None
    imgui = None
    ImVec2 = None
    HAS_P3D_IMGUI = False

from direct.showbase.ShowBase import ShowBase
from panda3d.core import Point3, Vec3, Vec4, Vec2, Point2, WindowProperties, MouseWatcher, NodePath
from panda3d.core import Camera, PerspectiveLens
from panda3d.core import CollisionTraverser, CollisionNode, CollisionHandlerQueue, CollisionHandlerPusher
from panda3d.core import CollisionRay, CollisionSphere, CollisionBox, BitMask32
from panda3d.core import TextNode, TextureStage, Texture, TransparencyAttrib
from panda3d.core import AmbientLight, DirectionalLight, LineSegs, ClockObject
from panda3d.core import CardMaker, loadPrcFileData, getModelPath
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame, DirectEntry, DirectButton, DirectCheckButton, DirectLabel, DirectSlider
from direct.task import Task
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpColorScaleInterval, LerpColorInterval, LerpPosInterval, LerpHprInterval, Wait, Func
from menu_system import MainMenu
from menu_system.ui_helpers import get_resolution_ui_scale
from managers.target import Target
from menu_system.splash_screen import SplashScreen
from menu_system.pause_menu import PauseMenu
from managers.resource_manager import ResourceManager
from managers.target_pool import TargetPool
from multiplayer.client import NetworkClient
from multiplayer.player_model import RemotePlayerModel
from multiplayer.lobby_menu import LobbyMenu
from shaders.shader_system import ShaderSystem
from managers.settings_manager import SettingsManager
from managers.effects_manager import EffectsManager
from managers.weapons_manager import WeaponsManager
from managers.movement_manager import MovementManager
from managers.killfeed_manager import KillfeedManager
from managers.shell_manager import ShellManager
from managers.shader_debug_ui import ShaderDebugUI
from managers.visual_markers import VisualMarkersManager
from managers.collision_manager import CollisionManager
from managers.multiplayer_manager import MultiplayerManager
from managers.audio_manager import AudioManager
from managers.chat_manager import ChatManager
from managers.hud_manager import HudManager
from managers.weapon_manager_new import WeaponManagerNew
import random
import math
import time
import json
from direct.actor.Actor import Actor
from math import sin, cos, pi, radians as deg2Rad

class Game(ShowBase):
    def safe_load_model(self, path):
        """Безопасная загрузка модели с поддержкой PyInstaller"""
        from panda3d.core import Filename
        
        if hasattr(sys, 'frozen'):
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            internal_dir = os.path.join(exe_dir, '_internal')
            
            # Пробуем разные варианты путей
            candidates = []
            
            # Если путь содержит models/, пробуем найти файл напрямую
            if 'models/' in path or 'models\\' in path:
                model_name = os.path.basename(path)
                # Пробуем в _internal/models
                for ext in ['.bam', '.egg', '']:
                    win_path = os.path.join(internal_dir, 'models', model_name + ext)
                    if os.path.exists(win_path):
                        candidates.append(Filename.fromOsSpecific(win_path))
            else:
                # Файл в корне (например, xz.egg)
                model_name = os.path.basename(path)
                for ext in ['.bam', '.egg', '']:
                    win_path = os.path.join(internal_dir, model_name + ext)
                    if os.path.exists(win_path):
                        candidates.append(Filename.fromOsSpecific(win_path))
            
            # Пробуем абсолютный путь с разными расширениями
            for ext in ['.bam', '.egg', '']:
                win_path = os.path.join(internal_dir, path.replace('/', '\\') + ext)
                if os.path.exists(win_path):
                    candidates.append(Filename.fromOsSpecific(win_path))
            
            # Пробуем загрузить каждый кандидат
            for candidate in candidates:
                try:
                    model = self.loader.loadModel(candidate)
                    if model and not model.isEmpty():
                        return model
                except Exception as e:
                    continue
            
            # Если ничего не помогло, пробуем относительный путь
            for ext in ['.bam', '.egg', '']:
                try:
                    model = self.loader.loadModel(path + ext)
                    if model and not model.isEmpty():
                        return model
                except:
                    continue
            
            # Последняя попытка - оригинальный путь
            return self.loader.loadModel(path)
        else:
            return self.loader.loadModel(path)

    def create_pvp_arena(self):
        """Создает простую арену для PvP режима"""
        from panda3d.core import CollisionPlane, Plane, Vec3

        arena = NodePath("pvp_arena")
        arena.reparentTo(self.render)

        # Пол
        floor = self.safe_load_model("models/box")
        floor.setScale(30, 30, 0.5)
        floor.setPos(0, 0, -0.5)
        floor.setColor(0.3, 0.3, 0.35, 1)
        floor.reparentTo(arena)

        # Стены
        wall_height = 5
        wall_thickness = 1

        # Северная стена
        north_wall = self.safe_load_model("models/box")
        north_wall.setScale(30, wall_thickness, wall_height)
        north_wall.setPos(0, 30, wall_height / 2)
        north_wall.setColor(0.4, 0.4, 0.45, 1)
        north_wall.reparentTo(arena)

        # Южная стена
        south_wall = self.safe_load_model("models/box")
        south_wall.setScale(30, wall_thickness, wall_height)
        south_wall.setPos(0, -30, wall_height / 2)
        south_wall.setColor(0.4, 0.4, 0.45, 1)
        south_wall.reparentTo(arena)

        # Западная стена
        west_wall = self.safe_load_model("models/box")
        west_wall.setScale(wall_thickness, 30, wall_height)
        west_wall.setPos(-30, 0, wall_height / 2)
        west_wall.setColor(0.4, 0.4, 0.45, 1)
        west_wall.reparentTo(arena)

        # Восточная стена
        east_wall = self.safe_load_model("models/box")
        east_wall.setScale(wall_thickness, 30, wall_height)
        east_wall.setPos(30, 0, wall_height / 2)
        east_wall.setColor(0.4, 0.4, 0.45, 1)
        east_wall.reparentTo(arena)

        # Укрытия в центре
        cover1 = self.safe_load_model("models/box")
        cover1.setScale(3, 3, 2)
        cover1.setPos(-8, 0, 1)
        cover1.setColor(0.5, 0.3, 0.3, 1)
        cover1.reparentTo(arena)

        cover2 = self.safe_load_model("models/box")
        cover2.setScale(3, 3, 2)
        cover2.setPos(8, 0, 1)
        cover2.setColor(0.5, 0.3, 0.3, 1)
        cover2.reparentTo(arena)

        return arena

    def switch_map(self, map_type: str):
        """Переключает карту между default и pvp"""
        if map_type == self.current_map:
            return

        # Удаляем старую карту
        if hasattr(self, 'map_model') and self.map_model:
            self.map_model.removeNode()

        # Загружаем новую карту
        if map_type == "pvp":
            self.map_model = self.create_pvp_arena()
            self.current_map = "pvp"
        else:
            self.map_model = self.safe_load_model("assets/xz.egg")
            self.map_model.reparentTo(self.render)
            self.map_model.setPos(0, 0, 0)
            self.map_model.setScale(1)
            self.current_map = "default"

        # Пересоздаем коллизии
        map_collision = CollisionNode('map_collision')
        map_collision_np = NodePath(map_collision)
        geom_node = self.map_model.find("**/+GeomNode")
        if not geom_node.isEmpty():
            geom_node.copyTo(map_collision_np)
            map_collision_np.reparentTo(self.map_model)

        # Применяем шейдеры к новой карте
        if hasattr(self, 'shader_system'):
            self.shader_system.rebind_scene_objects()

    def __init__(self):
        ShowBase.__init__(self)

        # Настройка model-path для PyInstaller
        if hasattr(sys, 'frozen'):
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            internal_dir = os.path.join(exe_dir, '_internal')
            
            # Добавляем пути для поиска моделей
            model_paths = []
            if os.path.exists(internal_dir):
                # Добавляем _internal и папку models внутри неё
                model_paths.append(os.path.normpath(internal_dir))
                models_internal = os.path.join(internal_dir, 'models')
                if os.path.exists(models_internal):
                    model_paths.append(os.path.normpath(models_internal))
            
            # Добавляем папку с exe и models в ней
            model_paths.append(os.path.normpath(exe_dir))
            models_exe = os.path.join(exe_dir, 'models')
            if os.path.exists(models_exe):
                model_paths.append(os.path.normpath(models_exe))
            
            # Если есть _MEIPASS, добавляем его
            if hasattr(sys, '_MEIPASS'):
                meipass = os.path.normpath(sys._MEIPASS)
                if meipass not in model_paths:
                    model_paths.append(meipass)
                meipass_models = os.path.join(sys._MEIPASS, 'models')
                if os.path.exists(meipass_models):
                    meipass_models_norm = os.path.normpath(meipass_models)
                    if meipass_models_norm not in model_paths:
                        model_paths.append(meipass_models_norm)
            
            # Устанавливаем model-path для Panda3D (используем прямые слеши для кроссплатформенности)
            for path in model_paths:
                if path and os.path.exists(path):
                    # Конвертируем в формат с прямыми слешами для Panda3D
                    panda_path = path.replace('\\', '/')
                    loadPrcFileData("", f"model-path {panda_path}")
                    # Также добавляем через API (более надежно)
                    getModelPath().appendDirectory(panda_path)
                    # Добавляем также в texture-path для поиска текстур
                    loadPrcFileData("", f"texture-path {panda_path}")
                    print(f"[OK] Added model-path and texture-path: {path}")

        self.fps = 0
        self.hud_update_counter = 0
        self.hud_update_interval = 6  # обновлять каждые 6 кадров (~10 раз в секунду)
        
        self.cTrav = CollisionTraverser('traverser')
        self.cQueue = CollisionHandlerQueue()
        
        try:
            self.map_model = self.safe_load_model("assets/xz.egg")
            self.map_model.reparentTo(self.render)
            self.map_model.setPos(0, 0, 0)
            self.map_model.setScale(1)
            self.current_map = "default"
        except Exception as e:
            raise
        
        map_collision = CollisionNode('map_collision')
        map_collision_np = NodePath(map_collision)
        geom_node = self.map_model.find("**/+GeomNode")
        if not geom_node.isEmpty():
            geom_node.copyTo(map_collision_np)
            map_collision_np.reparentTo(self.map_model)
        
        self.player_collision = CollisionNode('player')
        player_sphere = CollisionSphere(0, 0, 0, 1.0)
        self.player_collision.addSolid(player_sphere)
        self.player_collision_np = self.camera.attachNewNode(self.player_collision)
        
        self.collision_handler = CollisionHandlerPusher()
        self.collision_handler.addCollider(self.player_collision_np, self.camera)
        
        self.cTrav.addCollider(self.player_collision_np, self.collision_handler)
        
        self.disableMouse()
        
        # Initialize managers
        self.settings_manager = SettingsManager(self)
        self.settings = self.settings_manager.settings
        self.DEFAULT_SETTINGS = self.settings_manager.DEFAULT_SETTINGS
        
        self.mouse_sensitivity = self.settings.get('sensitivity', self.DEFAULT_SETTINGS['sensitivity'])
        self.show_score = self.settings.get('show_score', self.DEFAULT_SETTINGS['show_score'])
        self.show_timer = self.settings.get('show_timer', self.DEFAULT_SETTINGS['show_timer'])
        
        resolution = self.settings.get('resolution', self.DEFAULT_SETTINGS['resolution'])
        width, height = map(int, resolution.split('x'))
        props = WindowProperties()
        props.setSize(width, height)
        
        if self.settings.get('fullscreen', False):
            props.setFullscreen(True)
            
        self.win.requestProperties(props)

        self.resources = ResourceManager(self)
        print("ResourceManager initialized")
        
        self.shader_system = ShaderSystem(self)
        self.shader_system.initialize()
        self.target_pool = None

        self.menu = None
        self.pause_menu = None
        
        self.network = None
        self.is_multiplayer = False
        self.multiplayer_game_mode = "pve"
        self.remote_players = {}  # {player_id: RemotePlayerModel}
        self.lobby_menu = None
        self.current_weapon = "pistol"
        self.is_shooting = False
        self.shoot_state_frames = 0
        self.mp_local_hp = 100
        self.mp_local_max_hp = 100
        self.mp_local_kills = 0
        self.mp_local_deaths = 0
        self.mp_local_alive = True
        self.mp_local_respawn_at = 0.0
        self.mp_spawn_synced = False

        self.splash = SplashScreen(self)
        self.splash.start()

        self.score = 0
        self.combo_multiplier = 1.0
        self.last_hit_time = 0
        self.combo_window = 2.0
        self.start_time = 0
        self.game_time = 0

        # Initialize HUD manager
        self.hud_manager = HudManager(self)

        # Initialize chat manager
        self.chat_manager = ChatManager(self)

        self.show_scoreboard = False

        # Initialize shader debug UI manager
        self.shader_debug_ui = ShaderDebugUI(self)

        # Legacy references for compatibility
        self.is_shader_debug_open = False
        self.imgui_backend = None
        self.using_imgui_shader_debug = False
        self.shader_debug_widgets = []
        self.shader_debug_panel = None
        self.shader_ui_search = ""
        self.shader_ui_preset_name = self.shader_system.current_preset_name
        self.shader_ui_selected_preset = self.shader_system.current_preset_name
        self.shader_ui_config = {}

        properties = WindowProperties()
        properties.setTitle("Aim Trainer")
        properties.setCursorHidden(True)
        properties.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(properties)

        if not self.shader_debug_ui.initialize_imgui():
            self.shader_debug_ui.create_directgui_panel()

        # Sync legacy references
        self.is_shader_debug_open = self.shader_debug_ui.is_open
        self.imgui_backend = self.shader_debug_ui.imgui_backend
        self.using_imgui_shader_debug = self.shader_debug_ui.using_imgui
        self.shader_debug_panel = self.shader_debug_ui.debug_panel
        self.shader_ui_config = self.shader_debug_ui.ui_config
        
        self.camLens.setFov(self.settings['fov'])

        # Initialize movement manager
        self.movement_manager = MovementManager(self)

        # Legacy references for compatibility
        self.move_speed = self.movement_manager.move_speed
        self.sprint_speed = self.movement_manager.sprint_speed
        self.jump_power = self.movement_manager.jump_power
        self.gravity = self.movement_manager.gravity
        self.vertical_velocity = self.movement_manager.vertical_velocity
        self.horizontal_velocity = self.movement_manager.horizontal_velocity
        self.is_jumping = self.movement_manager.is_jumping
        self.ground_height = 0
        self.is_sprinting = False
        self.jump_speed_boost = 1.0
        
        self.prev_camera_heading = 0
        self.prev_camera_pitch = 0
        self.camera_rotation_speed = 0

        self.can_shoot = True
        self.combo_task = None

        # Initialize weapon manager
        self.weapon_manager_new = WeaponManagerNew(self)

        # Legacy references for compatibility
        self.current_weapon = self.weapon_manager_new.current_weapon
        self.weapons = self.weapon_manager_new.weapons
        self.shoot_cooldown = self.weapon_manager_new.shoot_cooldown
        self.recoil_time = self.weapon_manager_new.recoil_time
        self.is_shooting = self.weapon_manager_new.is_shooting
        self.shoot_state_frames = self.weapon_manager_new.shoot_state_frames
        self.shoot_time = self.weapon_manager_new.shoot_time
        self.original_weapon_pos = self.weapon_manager_new.original_weapon_pos
        self.original_weapon_hpr = self.weapon_manager_new.original_weapon_hpr
        self.recoil_pitch = self.weapon_manager_new.recoil_pitch
        self.recoil_yaw = self.weapon_manager_new.recoil_yaw
        self.max_recoil_pitch = self.weapon_manager_new.max_recoil_pitch
        self.max_recoil_yaw = self.weapon_manager_new.max_recoil_yaw
        self.recoil_recovery_speed = self.weapon_manager_new.recoil_recovery_speed
        self.recoil_recovery_delay = self.weapon_manager_new.recoil_recovery_delay
        self.last_shot_time = self.weapon_manager_new.last_shot_time
        self.current_spread = self.weapon_manager_new.current_spread
        self.is_aiming = self.weapon_manager_new.is_aiming
        self.aim_transition = self.weapon_manager_new.aim_transition
        self.ads_sensitivity_multiplier = self.weapon_manager_new.ads_sensitivity_multiplier
        self.weapon = None
        self.weapon_models = {}
        self.weapon_model = None
        self.weapon_animation = None
        self.is_drawing_weapon = False
        self.default_weapon_pos = {}
        self.ads_weapon_pos = {}
        self.ads_fov = {}

        self.camera_height = 1.8
        self.camera.setPos(0, 0, self.camera_height)
        self.camera_pitch = 0
        self.camera_heading = 0
        


        self.targets = []
        self.mp_targets_by_id = {}
        self.mp_targets_revision = -1
        
        self.crosshair = OnscreenText(
            text="+",
            style=1,
            fg=(1, 1, 1, 1),
            pos=(0, 0),
            scale=.05)

        self.shot_sound = self.loader.loadSfx("sounds/shot.wav")
        self.hit_sound = self.loader.loadSfx("sounds/hit.wav")
        self.shot_sound.setVolume(0.5)
        self.hit_sound.setVolume(0.7)
        
        self.fps_text = self.create_text(-1.3, 0.95)
        self.pos_text = self.create_text(-1.3, 0.85)
        self.speed_text = self.create_text(-1.3, 0.75)
        
        self.shot_effects = []
        
        self.damage_texts = []
        
        self.hit_markers = []

        # Initialize killfeed manager
        self.killfeed_manager = KillfeedManager(self)

        # Legacy references for compatibility
        self.killfeed_messages = self.killfeed_manager.messages
        self.killfeed_fade_time = self.killfeed_manager.fade_time
        self.killfeed_slide_distance = self.killfeed_manager.slide_distance
        self.killfeed_duration = self.killfeed_manager.display_duration
        
        # Initialize shell manager
        self.shell_manager = ShellManager(self)
        self.shell_model = self.safe_load_model("models/box")
        self.shell_model.setScale(0.02, 0.05, 0.02)
        self.shell_model.setColor(0.8, 0.6, 0.2)
        self.shell_manager.initialize(self.shell_model)

        # Legacy reference for compatibility
        self.active_shells = self.shell_manager.active_shells

        # Initialize visual markers manager
        self.visual_markers = VisualMarkersManager(self)

        # Initialize collision manager
        self.collision_manager = CollisionManager(self)

        # Legacy references for compatibility
        self.combo_window = self.collision_manager.combo_window
        self.combo_multiplier = self.collision_manager.combo_multiplier
        self.last_hit_time = self.collision_manager.last_hit_time

        # Initialize multiplayer manager
        self.multiplayer_manager = MultiplayerManager(self)

        self.accept("escape", self.toggle_pause)
        self.accept("p", self.toggle_pause)
        self.accept("space", self.start_jump)
        self.accept("1", self.switch_weapon, ["rifle"])
        self.accept("2", self.switch_weapon, ["pistol"])
        self.accept("3", self.switch_weapon, ["sniper"])
        self.accept("4", self.switch_weapon, ["dual_revolvers"])
        self.accept("wheel_up", self.cycle_weapon, [1])
        self.accept("wheel_down", self.cycle_weapon, [-1])
        self.accept("f7", self.toggle_shader_debug_panel)
        self.accept("f8", self.toggle_hitbox_debug)
        self.accept("enter", self.chat_manager.toggle_chat_input)
        self.accept("tab", self.on_tab_down)
        self.accept("tab-up", self.on_tab_up)
        
        self.keyMap = {
            "w": False,
            "s": False,
            "a": False,
            "d": False,
            "shift": False
        }
        
        self.accept("w", self.updateKeyMap, ["w", True])
        self.accept("w-up", self.updateKeyMap, ["w", False])
        self.accept("s", self.updateKeyMap, ["s", True])
        self.accept("s-up", self.updateKeyMap, ["s", False])
        self.accept("a", self.updateKeyMap, ["a", True])
        self.accept("a-up", self.updateKeyMap, ["a", False])
        self.accept("d", self.updateKeyMap, ["d", True])
        self.accept("d-up", self.updateKeyMap, ["d", False])
        self.accept("shift", self.updateKeyMap, ["shift", True])
        self.accept("shift-up", self.updateKeyMap, ["shift", False])
        
        self.previous_time = 0
        self.frame_count = 0
        self.fps_update_time = 0
        
        self.taskMgr.add(self.update_damage_texts, "update_damage_texts")

        self.taskMgr.add(self.shell_manager.update_shells, "update_shells")
        
        self.ray = CollisionRay()
        rayNode = CollisionNode('mouseRay')
        rayNode.addSolid(self.ray)
        rayNode.setFromCollideMask(BitMask32.bit(1))
        rayNode.setIntoCollideMask(BitMask32.allOff())
        self.rayNodePath = self.camera.attachNewNode(rayNode)
        self.cTrav.addCollider(self.rayNodePath, self.cQueue)
        
        self.accept("window-event", self.handle_window_event)
        
        self.current_time_scale = 1.0
        self.target_time_scale = 1.0
        self.normal_time_scale = 1.0
        self.slow_motion_scale = 0.3
        self.time_scale_speed = 6.0
        self.slow_motion_duration = 0.15
        self.is_in_slow_motion = False
        
        taskMgr.add(self.update_time_scale, 'update_time_scale')
        
        globalClock.setMode(ClockObject.MLimited)
        globalClock.setFrameRate(60)
        
        self.accept('update_weapon_position', self.update_weapon_position)

        # Initialize audio manager
        self.audio_manager = AudioManager(self)

        self.mouse_pressed = False
        
        self.bullet_traces = self.render.attachNewNode("bullet_traces")
        self.traces = []
        
        self.is_aiming = False
        self.default_weapon_pos = {}
        self.ads_weapon_pos = {}
        self.aim_transition = 0.0
        self.ads_sensitivity_multiplier = 0.6
        
        for weapon in self.weapons:
            self.default_weapon_pos[weapon] = {
                "pos": Point3(0.7, 1.0, -0.5),
                "hpr": Vec3(0, 0, 0)
            }
            self.ads_weapon_pos[weapon] = {
                "pos": Point3(0, 1.2, -0.3),
                "hpr": Vec3(0, 0, 0)
            }
        
        self.accept("mouse3", self.start_aiming)
        self.accept("mouse3-up", self.stop_aiming)

        self.ads_fov = {
            "pistol": 65,
            "rifle": 45,
            "sniper": 30,
            "dual_revolvers": 60
        }

        self.weapon_animation = None
        self.is_drawing_weapon = False

        self.is_splash_screen_active = True

        self.active_revolver = "left"
        self.hud_scale_targets = {
            "score_text": 0.07,
            "timer_text": 0.07,
            "chat_text": 0.04,
            "chat_entry": 0.05,
            "scoreboard_text": 0.05,
            "hp_text": 0.06,
            "kd_text": 0.055,
            "death_text": 0.09,
            "crosshair": 0.05,
            "fps_text": 0.05,
            "pos_text": 0.05,
            "speed_text": 0.05,
        }
        self.apply_resolution_ui_scale()

    def create_text(self, x, y):
        return OnscreenText(
            text="",
            style=1,
            fg=(1, 1, 1, 1),
            pos=(x, y),
            align=TextNode.ALeft,
            scale=.05)

    def get_hud_ui_scale(self):
        return get_resolution_ui_scale(self, base_width=1280, base_height=720, min_scale=0.50, max_scale=1.0)

    def get_imgui_shell_scale(self):
        return get_resolution_ui_scale(self, base_width=1280, base_height=720, min_scale=0.58, max_scale=1.0)

    def apply_resolution_ui_scale(self):
        hud_scale = self.get_hud_ui_scale()

        for attr_name, base_scale in getattr(self, "hud_scale_targets", {}).items():
            widget = getattr(self, attr_name, None)
            if widget is None:
                continue
            try:
                widget.setScale(base_scale * hud_scale)
            except Exception:
                pass

        for msg_data in getattr(self, "killfeed_messages", []):
            try:
                msg_data["message"].setScale(0.04 * hud_scale)
            except Exception:
                pass
            try:
                msg_data["frame_root"].setScale(hud_scale)
            except Exception:
                pass

    def initialize_shader_debug_imgui(self):
        return self.shader_debug_ui.initialize_imgui()

    def render_shader_debug_imgui(self):
        self.shader_debug_ui.render_imgui()

    def _shader_status_color(self, status: str):
        return self.shader_debug_ui._status_color(status)

    def _render_shader_status_badge(self, text: str, status: str):
        self.shader_debug_ui._render_status_badge(text, status)

    def _render_shader_global_toggles(self):
        self.shader_debug_ui._render_global_toggles()

    def _render_shader_home_tab(self, snapshot: dict):
        self.shader_debug_ui._render_home_tab(snapshot)

    def _render_shader_techniques_tab(self, snapshot: dict):
        self.shader_debug_ui._render_techniques_tab(snapshot)

    def _render_shader_panel_tab(self, panel_id: str, snapshot: dict):
        self.shader_debug_ui._render_panel_tab(panel_id, snapshot)

    def _render_shader_grouped_cards(self, techniques: list, search_query: str):
        self.shader_debug_ui._render_grouped_cards(techniques, search_query)

    def _render_shader_technique_card(self, technique: dict):
        self.shader_debug_ui._render_technique_card(technique)

    def _render_shader_stats_tab(self, snapshot: dict):
        self.shader_debug_ui._render_stats_tab(snapshot)

    def _render_imgui_settings_tab(self, display_width: float, display_height: float):
        self.shader_debug_ui._render_imgui_settings_tab(display_width, display_height)

    def create_shader_debug_ui(self):
        self.shader_debug_ui.create_directgui_panel()

    def _set_overlay_mouse_mode(self, enabled: bool):
        self.shader_debug_ui._set_overlay_mouse_mode(enabled)

    def toggle_shader_debug_panel(self):
        self.shader_debug_ui.toggle()
        # Sync legacy references
        self.is_shader_debug_open = self.shader_debug_ui.is_open
        self.imgui_backend = self.shader_debug_ui.imgui_backend
        self.shader_debug_panel = self.shader_debug_ui.debug_panel

    def update_shader_debug_bool(self, key: str, value):
        self.shader_debug_ui.update_bool(key, value)

    def update_shader_debug_value(self, key: str, value):
        self.shader_debug_ui.update_value(key, value)

    def reset_shader_debug_values(self):
        self.shader_debug_ui.reset_values()
    def create_cross_marker(self, position):
        return self.visual_markers.create_cross_marker(position)

    def create_hit_marker(self, position):
        return self.visual_markers.create_hit_marker(position)

    def setup_targets(self):
        """Создание манекенов"""
        if self.target_pool:
            self.target_pool.release_all()
        self.targets.clear()
        self.mp_targets_by_id.clear()
        self.mp_targets_revision = -1

        if self.is_multiplayer:
            return

        target_count = self.settings.get('target_count', 10)
        
        for _ in range(target_count):
            target = self.target_pool.acquire()
            self.targets.append(target)

    def sync_weapon_camera(self):
        return

    def update_weapon_position(self):
        """Обновляет позицию оружия на основе настроек"""
        self.weapon_manager_new.update_weapon_position()
        # Sync legacy references
        self.weapon = self.weapon_manager_new.weapon
        self.original_weapon_pos = self.weapon_manager_new.original_weapon_pos
        self.original_weapon_hpr = self.weapon_manager_new.original_weapon_hpr
        
    def animate_weapon_recoil(self):
        """Анимирует отдачу оружия"""
        self.weapon_manager_new.animate_weapon_recoil()

    def updateKeyMap(self, key, value):
        if self.chat_manager.is_chat_active or self.is_shader_debug_open:
            self.keyMap[key] = False
            return
        self.keyMap[key] = value

    def start_jump(self):
        self.movement_manager.start_jump()
        # Sync legacy references
        self.vertical_velocity = self.movement_manager.vertical_velocity
        self.horizontal_velocity = self.movement_manager.horizontal_velocity
        self.is_jumping = self.movement_manager.is_jumping

    def reset_jump_combo(self, task):
        return self.movement_manager.reset_jump_combo(task)

    def reset_shoot(self, task):
        self.can_shoot = True
        return task.done

    def _calculate_spread(self, weapon_params):
        """Вычисляет разброс с учетом движения и прыжка"""
        if not self.settings.get('spread_enabled', True):
            return 0.0

        spread_params = weapon_params["spread"]
        current_time = globalClock.getFrameTime()
        time_since_last_shot = current_time - self.last_shot_time

        if time_since_last_shot > spread_params["recovery_time"]:
            self.current_spread = spread_params["base"]
        else:
            self.current_spread = min(
                self.current_spread + spread_params["base"] * 0.5,
                spread_params["max"]
            )

        final_spread = self.current_spread
        is_moving = any(self.keyMap[key] for key in ["w", "s", "a", "d"])

        if is_moving:
            final_spread *= spread_params["moving_mult"]
        if self.is_jumping:
            final_spread *= spread_params["jumping_mult"]

        return min(final_spread, spread_params["max"])

    def _apply_weapon_recoil(self, weapon_params):
        """Применяет отдачу к камере"""
        if not self.settings.get('recoil_enabled', True):
            return

        recoil_pitch_range = weapon_params["recoil"]["pitch"]
        recoil_yaw_range = weapon_params["recoil"]["yaw"]

        recoil_pitch = random.uniform(recoil_pitch_range[0], recoil_pitch_range[1])
        recoil_yaw = random.uniform(recoil_yaw_range[0], recoil_yaw_range[1])

        self.recoil_pitch += recoil_pitch
        self.recoil_yaw += recoil_yaw

        self.recoil_pitch = min(self.recoil_pitch, self.max_recoil_pitch)
        self.recoil_yaw = max(min(self.recoil_yaw, self.max_recoil_yaw), -self.max_recoil_yaw)

        self.camera_pitch += recoil_pitch
        self.camera_heading += recoil_yaw

        self.animate_weapon_recoil()

    def _create_shot_trace(self, weapon_pos, spread_direction, max_distance, is_authoritative_mp):
        """Создает трассу выстрела и обрабатывает попадание"""
        end_pos = weapon_pos + (spread_direction * max_distance)

        if self.settings.get('bullet_traces', True):
            if self.cQueue.getNumEntries() > 0:
                self.cQueue.sortEntries()
                entry = self.cQueue.getEntry(0)
                hit_pos = entry.getSurfacePoint(self.render)

                start_pos = weapon_pos
                self.create_bullet_trace(start_pos, hit_pos)
                if not is_authoritative_mp:
                    self.handle_collision(entry)
            else:
                start_pos = weapon_pos
                self.create_bullet_trace(start_pos, end_pos)

    def shoot(self):
        if self.is_splash_screen_active:
            return
        if self.chat_manager.is_chat_active or self.is_shader_debug_open:
            return
        if not self.can_local_multiplayer_act():
            return

        if not self.can_shoot:
            return

        self.can_shoot = False

        if self.current_weapon == "dual_revolvers":
            active_revolver = self.weapon_models["dual_revolvers"].find(f"{self.active_revolver}_revolver")

            self.audio_manager.weapon_sounds[self.current_weapon].play()

            if self.active_revolver == "left":
                recoil_pos = Point3(
                    active_revolver.getX() + 0.15,
                    active_revolver.getY() - 0.08,
                    active_revolver.getZ() + 0.05
                )
                recoil_hpr = Vec3(
                    active_revolver.getH() + 12,
                    active_revolver.getP() + 15,
                    active_revolver.getR() + random.uniform(-8, 8)
                )
            else:
                recoil_pos = Point3(
                    active_revolver.getX() - 0.15,
                    active_revolver.getY() - 0.08,
                    active_revolver.getZ() + 0.05
                )
                recoil_hpr = Vec3(
                    active_revolver.getH() - 12,
                    active_revolver.getP() + 15,
                    active_revolver.getR() + random.uniform(-8, 8)
                )

            recoil_sequence = Sequence(
                Parallel(
                    active_revolver.posInterval(
                        0.05,
                        recoil_pos,
                        blendType='easeOut'
                    ),
                    active_revolver.hprInterval(
                        0.05,
                        recoil_hpr,
                        blendType='easeOut'
                    )
                ),
                Parallel(
                    active_revolver.posInterval(
                        0.1,
                        Point3(-2.0 if self.active_revolver == "left" else 0.4, 0.6, -0.2),
                        blendType='easeIn'
                    ),
                    active_revolver.hprInterval(
                        0.1,
                        Vec3(0, 0, 0),
                        blendType='easeIn'
                    )
                )
            )
            recoil_sequence.start()

            self.active_revolver = "right" if self.active_revolver == "left" else "left"

        else:
            self.audio_manager.weapon_sounds[self.current_weapon].play()

            self.create_shell_casing()

            self.animate_weapon_recoil()

        self.taskMgr.doMethodLater(
            self.shoot_cooldown,
            self.reset_shoot,
            'reset_shoot'
        )

        weapon_params = self.weapons[self.current_weapon]

        if not self.mouseWatcherNode.hasMouse():
            return

        mouse_pos = self.mouseWatcherNode.getMouse()

        # Вычисляем разброс
        final_spread = self._calculate_spread(weapon_params)

        if self.settings.get('spread_enabled', True):
            spread_x = random.uniform(-final_spread, final_spread)
            spread_y = random.uniform(-final_spread, final_spread)

            spread_mouse_pos = Point2(
                mouse_pos.getX() + spread_x,
                mouse_pos.getY() + spread_y
            )
        else:
            spread_mouse_pos = mouse_pos

        self.ray.setFromLens(self.camNode, spread_mouse_pos.getX(), spread_mouse_pos.getY())

        # Применяем отдачу
        self._apply_weapon_recoil(weapon_params)

        self.last_shot_time = globalClock.getFrameTime()
        self.shader_system.pulse_weapon()
        self.shoot_state_frames = 2
        is_authoritative_mp = self.is_multiplayer and self.network and self.network.is_connected()

        self.cTrav.traverse(self.render)

        # Используем полиморфизм для получения позиции дула
        weapon = self.weapon_manager_new.get_current_weapon_instance()
        weapon_pos = weapon.get_muzzle_position(self.camera.getPos(), self.camera.getMat())

        direction = self.camera.getQuat().getForward()

        if self.settings.get('spread_enabled', True):
            spread_x = random.uniform(-final_spread, final_spread)
            spread_y = random.uniform(-final_spread, final_spread)

            spread_direction = Vec3(
                direction.getX() + spread_x,
                direction.getY(),
                direction.getZ() + spread_y
            )
            spread_direction.normalize()
        else:
            spread_direction = direction

        if is_authoritative_mp:
            self.network.send_shot(
                origin=self.camera.getPos(),
                direction=spread_direction,
                weapon=self.current_weapon,
                camera_heading=self.camera_heading,
                camera_pitch=self.camera_pitch
            )

        max_distance = 1000

        # Создаем трассу и обрабатываем попадание
        self._create_shot_trace(weapon_pos, spread_direction, max_distance, is_authoritative_mp)
        
    def remove_specific_effect(self, effect_index, task):
        if 0 <= effect_index < len(self.shot_effects):
            _, marker_node, _ = self.shot_effects[effect_index]
            if marker_node:
                marker_node.removeNode()
            self.shot_effects[effect_index] = (None, None, None)
        return task.done

    def create_bullet_trace(self, start_pos, end_pos):
        """Создает след пули от точки start_pos до end_pos"""
        ls = LineSegs()
        ls.setColor(1.0, 1.0, 0.8, 0.5)
        ls.setThickness(2.0)
        ls.moveTo(start_pos)
        
        if end_pos is not None:
            ls.drawTo(end_pos)
        else:
            ls.drawTo(end_pos)
        
        trace = self.bullet_traces.attachNewNode(ls.create())
        
        trace.setTransparency(TransparencyAttrib.MAlpha)
        
        Sequence(
            Wait(0.1),
            LerpColorScaleInterval(trace, 0.2, Vec4(1, 1, 1, 0)),
            Func(trace.removeNode)
        ).start()
        
    def remove_trace(self, trace_np, task):
        """Удаляет след пули после того как он исчез"""
        self.traces = [(np, fade) for np, fade in self.traces if np != trace_np]
        trace_np.removeNode()
        return Task.done

    def update_damage_texts(self, task):
        current_time = globalClock.getFrameTime()
        
        for i in range(len(self.damage_texts) - 1, -1, -1):
            text_node, start_time, start_pos = self.damage_texts[i]
            age = current_time - start_time
            
            if age > 1.0:
                text_node.removeNode()
                self.damage_texts.pop(i)
            else:
                alpha = 1.0 - age
                z_offset = age * 2
                text_node.setPos(start_pos + Point3(0, 0, z_offset))
                text_node.setAlphaScale(alpha)
        
        return task.cont

    def handle_window_event(self, window=None):
        self.cleanup(window)
        self.apply_resolution_ui_scale()
        if hasattr(self, "splash") and self.splash:
            self.splash.update_layout()
        if hasattr(self, "menu") and self.menu:
            self.menu.schedule_layout_refresh(0.0)
        if hasattr(self, "pause_menu") and self.pause_menu:
            self.pause_menu.update_layout()

    def cleanup(self, window=None):
        for line_node, marker_node, task in self.shot_effects:
            if line_node:
                line_node.removeNode()
            if marker_node:
                marker_node.removeNode()
            if task:
                self.taskMgr.remove(task)
        self.shot_effects.clear()
        
        for text_node, _, _ in self.damage_texts:
            text_node.removeNode()
        self.damage_texts.clear()

    def toggle_pause(self):
        """Переключает паузу в игре"""
        if self.is_splash_screen_active:
            return
        if self.is_shader_debug_open:
            self.toggle_shader_debug_panel()
            return
        if self.chat_manager.is_chat_active:
            self.chat_manager.close_chat_input()
            return

        if not self.pause_menu:
            return
        
        if self.pause_menu.is_paused:
            self.pause_menu.hide()
        else:
            self.pause_menu.show()
    
    def return_to_menu(self):
        if self.is_splash_screen_active:
            return

        if self.is_multiplayer or self.network:
            self.cleanup_multiplayer()

        if self.is_shader_debug_open:
            self.toggle_shader_debug_panel()

        if hasattr(self, 'score_text'):
            self.hud_manager.score_text.hide()
        if hasattr(self, 'timer_text'):
            self.hud_manager.timer_text.hide()
        if hasattr(self, 'chat_manager'):
            self.chat_manager.cleanup()
        if hasattr(self, 'scoreboard_text'):
            self.hud_manager.scoreboard_text.hide()
        if hasattr(self, 'hp_text'):
            self.hud_manager.hp_text.hide()
        if hasattr(self, 'kd_text'):
            self.hud_manager.kd_text.hide()
        if hasattr(self, 'death_overlay'):
            self.hud_manager.death_overlay.hide()
        if hasattr(self, 'death_text'):
            self.hud_manager.death_text.hide()
        if hasattr(self, 'hurt_flash'):
            self.hud_manager.hurt_flash.hide()
        if hasattr(self, 'fps_text'):
            self.fps_text.hide()
        if hasattr(self, 'pos_text'):
            self.pos_text.hide()
        if hasattr(self, 'speed_text'):
            self.speed_text.hide()
        if hasattr(self, 'crosshair'):
            self.crosshair.hide()
        if hasattr(self, 'killfeed_manager'):
            for msg_data in self.killfeed_manager.messages:
                if 'message' in msg_data:
                    msg_data['message'].hide()
                if 'frame_root' in msg_data:
                    msg_data['frame_root'].hide()
        self.chat_manager.is_chat_active = False
        self.show_scoreboard = False
            
        self.taskMgr.remove("update")
        self.ignore("mouse1")
        
        if hasattr(self, 'targets'):
            for target in self.targets:
                target.destroy()
            self.targets.clear()
        
        if hasattr(self, 'weapon'):
            self.weapon.removeNode()
            
        if hasattr(self, 'taskMgr'):
            self.taskMgr.remove("timer_task")
        
        if not hasattr(self, 'main_menu'):
            self.show_main_menu()
        else:
            self.main_menu.show()

    def start_game(self):
        if self.is_splash_screen_active:
            return
        
        if not self.pause_menu:
            self.pause_menu = PauseMenu(self)
        
        if not self.target_pool:
            target_count = self.settings.get('target_count', 10)
            pool_size = max(target_count * 2, 30)
            self.target_pool = TargetPool(self, initial_size=pool_size)
            self.target_pool.initialize(Target)
            print(f"OK: TargetPool создан с размером {pool_size}")
        
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(props)
        
        if self.target_pool:
            self.target_pool.release_all()
        self.targets.clear()
        
        self.setup_targets()
        self.weapon_manager_new.setup_weapon()

        # Update legacy references after setup
        self.weapon = self.weapon_manager_new.weapon
        self.weapon_models = self.weapon_manager_new.weapon_models
        self.weapon_model = self.weapon_manager_new.weapon_model
        self.original_weapon_pos = self.weapon_manager_new.original_weapon_pos
        self.original_weapon_hpr = self.weapon_manager_new.original_weapon_hpr
        self.default_weapon_pos = self.weapon_manager_new.default_weapon_pos
        self.ads_weapon_pos = self.weapon_manager_new.ads_weapon_pos
        self.ads_fov = self.weapon_manager_new.ads_fov
        self.shader_system.rebind_scene_objects()
        
        self.taskMgr.add(self.update, "update")
        self.taskMgr.add(self.update_aim, "update_aim")
        self.accept("mouse1", self.on_mouse_press)
        self.accept("mouse1-up", self.on_mouse_release)
        
        self.score = 0
        self.start_time = time.time()
        self.hud_manager.update_score_display()
        self.hud_manager.update_timer_display()
        self.mp_spawn_synced = False
        self.hud_manager.hurt_flash_alpha = 0.0
        self.hud_manager.hurt_flash.hide()
        self.hud_manager.death_overlay.hide()
        self.hud_manager.death_text.hide()
        if self.is_multiplayer:
            self.mp_local_hp = 100
            self.mp_local_max_hp = 100
            self.mp_local_kills = 0
            self.mp_local_deaths = 0
            self.mp_local_alive = True
            self.mp_local_respawn_at = 0.0
            self.hud_manager.update_multiplayer_hud()
        else:
            self.hud_manager.hp_text.hide()
            self.hud_manager.kd_text.hide()
        
        if self.show_score:
            self.hud_manager.score_text.show()
        if self.show_timer:
            self.hud_manager.timer_text.show()
            self.taskMgr.add(self.hud_manager.update_timer_task, "timer_task")
        
        self.audio_manager.setup_audio()
        self.audio_manager.preload_weapon_sounds()

    def can_local_multiplayer_act(self):
        return self.multiplayer_manager.can_local_multiplayer_act()

    def reset_multiplayer_motion_state(self):
        return self.multiplayer_manager.reset_multiplayer_motion_state()

    def sync_local_multiplayer_spawn(self, state):
        return self.multiplayer_manager.sync_local_multiplayer_spawn(state)

    def update_multiplayer_feedback(self, dt: float):
        return self.multiplayer_manager.update_multiplayer_feedback(dt)

    def refresh_hitbox_debug_visibility(self):
        return self.multiplayer_manager.refresh_hitbox_debug_visibility()

    def set_hitbox_debug_enabled(self, enabled, save: bool = True):
        return self.multiplayer_manager.set_hitbox_debug_enabled(enabled, save)

    def toggle_hitbox_debug(self):
        return self.multiplayer_manager.toggle_hitbox_debug()

    def apply_local_multiplayer_state(self, state):
        return self.multiplayer_manager.apply_local_multiplayer_state(state)

    def handle_collision(self, entry):
        return self.collision_manager.handle_collision(entry)

    def get_damage_for_part(self, part_name):
        return self.collision_manager.get_damage_for_part(part_name)

    def spawn_damage_text(self, text, pos):
        return self.collision_manager.spawn_damage_text(text, pos)

    def spawn_target(self, task=None):
        if not self.target_pool:
            return Task.done if task is not None else None

        target = self.target_pool.acquire()
        if target not in self.targets:
            self.targets.append(target)
        
        return Task.done if task is not None else None

    def apply_targets_state(self, snapshot):
        """Apply authoritative multiplayer targets snapshot."""
        if not snapshot:
            return

        revision = int(snapshot.get("revision", -1))
        if revision <= self.mp_targets_revision:
            return
        self.mp_targets_revision = revision

        incoming = snapshot.get("targets", [])
        incoming_ids = set()

        for state in incoming:
            target_id = state.get("id")
            if not target_id:
                continue
            incoming_ids.add(target_id)
            target_obj = self.mp_targets_by_id.get(target_id)
            if target_obj is None:
                target_obj = self.target_pool.acquire()
                target_obj.network_id = target_id
                self.mp_targets_by_id[target_id] = target_obj
                if target_obj not in self.targets:
                    self.targets.append(target_obj)

            pos = state.get("pos", [0, 0, 1])
            alive = bool(state.get("alive", True))
            variant = state.get("variant", "default")
            respawn_at = state.get("respawn_at", 0.0)
            target_obj.set_network_state(pos, alive, variant, respawn_at)

        if incoming:
            server_variant = str(incoming[0].get("variant", "default")).lower()
            if server_variant in ("nsfw", "sfw"):
                desired_show_images = server_variant == "nsfw"
                if self.settings.get("show_target_images", True) != desired_show_images:
                    self.settings["show_target_images"] = desired_show_images
                    if self.target_pool:
                        self.target_pool.refresh_all_active()

        for target_id in list(self.mp_targets_by_id.keys()):
            if target_id in incoming_ids:
                continue
            target_obj = self.mp_targets_by_id.pop(target_id)
            if target_obj in self.targets:
                self.targets.remove(target_obj)
            target_obj.network_id = None
            target_obj.destroy()

    def process_network_shot_results(self):
        if not self.network:
            return
        shot_results = self.network.consume_shot_results()
        if not shot_results:
            return

        local_player_id = self.network.player_id
        for result in shot_results:
            shooter_id = result.get("shooter_id")
            hit_pos = result.get("hit_pos")
            target_id = result.get("target_id")
            hit_type = result.get("hit_type", "none")
            victim_id = result.get("victim_id")
            if target_id:
                hit_target = self.mp_targets_by_id.get(target_id)
                if hit_target:
                    self.shader_system.mark_target_hit(hit_target)

            if shooter_id == local_player_id:
                if not result.get("hit"):
                    continue
                self.score = int(result.get("new_score", self.score))
                self.hud_manager.update_score_display()
                if hit_pos and self.settings.get('damage_numbers', True):
                    if hit_type == "player":
                        points = int(result.get("damage", 0))
                    else:
                        points = int(result.get("score_delta", 0))
                    self.spawn_damage_text(f"+{points}", Point3(hit_pos[0], hit_pos[1], hit_pos[2]))
                if hit_type == "target":
                    self.activate_hit_effects()
                if hit_type in ("target", "player"):
                    self.hit_sound.play()
                if hit_type == "player" and result.get("kill") and self.settings.get('killfeed', True):
                    self.create_killfeed_message(result.get("victim_name", "Player"))
                continue

            if victim_id == local_player_id and hit_type == "player":
                victim_alive = bool(result.get("victim_alive", self.mp_local_alive))
                victim_hp = result.get("victim_hp", self.mp_local_hp)
                self.mp_local_alive = victim_alive
                self.mp_local_hp = max(0, int(victim_hp))
                self.mouse_pressed = False
                self.hud_manager.trigger_hurt_flash(0.85 if not victim_alive else 0.55)
                self.hud_manager.update_multiplayer_hud()

            # Visualize remote shots from authoritative server events.
            origin = result.get("origin")
            direction = result.get("dir")
            if not origin or not direction or len(origin) != 3 or len(direction) != 3:
                continue

            start_pos = Point3(float(origin[0]), float(origin[1]), float(origin[2]))
            dir_vec = Vec3(float(direction[0]), float(direction[1]), float(direction[2]))
            if dir_vec.lengthSquared() <= 1e-6:
                continue
            dir_vec.normalize()

            if hit_pos:
                end_pos = Point3(hit_pos[0], hit_pos[1], hit_pos[2])
            else:
                end_pos = start_pos + (dir_vec * 60.0)
            self.create_bullet_trace(start_pos, end_pos)

    def update_time_scale(self, task):
        if self.is_in_slow_motion:
            base.taskMgr.globalClock.setDt(base.taskMgr.globalClock.getDt() * self.slow_motion_scale)
        return task.cont

    def activate_hit_effects(self):
        # Активируем замедление времени
        self.target_time_scale = self.slow_motion_scale
        self.is_in_slow_motion = True
        taskMgr.doMethodLater(self.slow_motion_duration, self.deactivate_slow_motion, 'deactivate_slow_motion')

    def deactivate_slow_motion(self, task):
        self.target_time_scale = self.normal_time_scale
        self.is_in_slow_motion = False
        return task.done

    def create_killfeed_message(self, target_name="Target"):
        self.killfeed_manager.create_message(target_name)
        # Sync legacy reference
        self.killfeed_messages = self.killfeed_manager.messages

    def update_killfeed_positions(self):
        self.killfeed_manager.update_positions()
        # Sync legacy reference
        self.killfeed_messages = self.killfeed_manager.messages

    def update(self, task):
        """Обновление состояния игры"""
        if self.is_splash_screen_active:
            return task.cont
        
        if self.pause_menu and self.pause_menu.is_paused:
            return task.cont
        
        dt = globalClock.getDt()

        self.fps = int(globalClock.getAverageFrameRate())

        # Обновляем HUD текст только каждые N кадров для оптимизации
        self.hud_update_counter += 1
        if self.hud_update_counter >= self.hud_update_interval:
            self.hud_update_counter = 0
            self.fps_text.setText(f"FPS: {self.fps}")
            self.pos_text.setText(f"Pos: ({self.camera.getX():.1f}, {self.camera.getY():.1f}, {self.camera.getZ():.1f})")

        if self.current_time_scale != self.target_time_scale:
            diff = self.target_time_scale - self.current_time_scale
            change = min(abs(diff), dt * self.time_scale_speed) * (1 if diff > 0 else -1)
            self.current_time_scale += change
        
        scaled_dt = dt * self.current_time_scale
        
        self.hud_manager.update_score_display()
        
        self.fps_text.setText(f"FPS: {self.fps}")
        self.pos_text.setText(f"Pos: ({self.camera.getX():.1f}, {self.camera.getY():.1f}, {self.camera.getZ():.1f})")
        
        current_time = globalClock.getFrameTime()
        if current_time - self.last_shot_time > self.recoil_recovery_delay:
            if self.recoil_pitch > 0:
                old_pitch = self.recoil_pitch
                self.recoil_pitch = max(0, self.recoil_pitch - self.recoil_recovery_speed * dt)
                self.camera_pitch -= (old_pitch - self.recoil_pitch)
            
            if self.recoil_yaw != 0:
                old_yaw = self.recoil_yaw
                if self.recoil_yaw > 0:
                    self.recoil_yaw = max(0, self.recoil_yaw - self.recoil_recovery_speed * dt)
                else:
                    self.recoil_yaw = min(0, self.recoil_yaw + self.recoil_recovery_speed * dt)
                self.camera_heading -= (old_yaw - self.recoil_yaw)
            
            self.camera.setHpr(self.camera_heading, self.camera_pitch, 0)
        
        can_control_local_player = self.can_local_multiplayer_act()
        move_vec = Vec3(0, 0, 0)

        if self.keyMap["w"]: move_vec.addY(1)
        if self.keyMap["s"]: move_vec.addY(-1)
        if self.keyMap["a"]: move_vec.addX(-1)
        if self.keyMap["d"]: move_vec.addX(1)

        if not can_control_local_player:
            move_vec = Vec3(0, 0, 0)
            self.horizontal_velocity = Vec3(0, 0, 0)
            
        if move_vec.length() > 0:
            move_vec.normalize()
            
            heading = self.camera.getH() * (pi / 180.0)
            move_vec = Vec3(
                move_vec.getX() * cos(heading) - move_vec.getY() * sin(heading),
                move_vec.getX() * sin(heading) + move_vec.getY() * cos(heading),
                0
            )
        
        speed = (self.sprint_speed if self.keyMap["shift"] else self.move_speed) * self.current_time_scale
        if self.is_jumping:
            speed *= self.movement_manager.jump_combo_multiplier

        if move_vec.length() > 0:
            self.horizontal_velocity = move_vec * speed
            self.movement_manager.horizontal_velocity = self.horizontal_velocity
        elif not self.is_jumping:
            self.horizontal_velocity = Vec3(0, 0, 0)
            self.movement_manager.horizontal_velocity = Vec3(0, 0, 0)

        if self.horizontal_velocity.length() > 0:
            self.camera.setPos(
                self.camera.getX() + self.horizontal_velocity.getX() * scaled_dt,
                self.camera.getY() + self.horizontal_velocity.getY() * scaled_dt,
                self.camera.getZ()
            )

        if self.is_jumping:
            self.vertical_velocity += self.gravity * scaled_dt
            self.movement_manager.vertical_velocity = self.vertical_velocity
            new_z = self.camera.getZ() + self.vertical_velocity * scaled_dt

            if new_z <= self.camera_height:
                new_z = self.camera_height
                self.vertical_velocity = 0
                self.is_jumping = False
                self.movement_manager.vertical_velocity = 0
                self.movement_manager.is_jumping = False
                self.jump_speed_boost = 1.0
                if move_vec.length() == 0:
                    self.horizontal_velocity = Vec3(0, 0, 0)
                    self.movement_manager.horizontal_velocity = Vec3(0, 0, 0)

            self.camera.setZ(new_z)
            
        if self.mouseWatcherNode.hasMouse() and not self.chat_manager.is_chat_active and not self.is_shader_debug_open and can_control_local_player:
            mouse_x = self.mouseWatcherNode.getMouseX()
            mouse_y = self.mouseWatcherNode.getMouseY()
            
            sensitivity = self.settings["sensitivity"]
            
            if self.is_aiming:
                sensitivity *= self.ads_sensitivity_multiplier
            
            self.camera_heading -= mouse_x * sensitivity
            self.camera_pitch += mouse_y * sensitivity
            
            self.camera_pitch = min(89, max(-89, self.camera_pitch))
            
            self.camera.setHpr(self.camera_heading, self.camera_pitch, 0)
            
            heading_delta = abs(self.camera_heading - self.prev_camera_heading)
            pitch_delta = abs(self.camera_pitch - self.prev_camera_pitch)
            self.camera_rotation_speed = math.sqrt(heading_delta**2 + pitch_delta**2)
            
            self.prev_camera_heading = self.camera_heading
            self.prev_camera_pitch = self.camera_pitch
            
            self.win.movePointer(0,
                int(self.win.getProperties().getXSize() / 2),
                int(self.win.getProperties().getYSize() / 2))

        # Обновляем speed_text только когда обновляем остальной HUD
        if self.hud_update_counter == 0:
            current_speed = math.sqrt(self.horizontal_velocity.getX()**2 + self.horizontal_velocity.getY()**2)
            self.speed_text.setText(f"Speed: {current_speed:.1f}")
        
        if self.mouse_pressed and self.current_weapon == "rifle" and can_control_local_player:
            current_time = time.time()
            if current_time - self.last_shot_time >= self.weapons[self.current_weapon]["cooldown"]:
                self.shoot()
        
        self.update_killfeed_positions()
        self.chat_manager.refresh_chat_display()
        
        self.update_aim(task)
        self.shader_system.update(dt)
        
        if self.is_multiplayer and self.network and self.network.is_connected():
            snapshot = self.network.consume_latest_targets_snapshot()
            if snapshot:
                self.apply_targets_state(snapshot)
            self.process_network_shot_results()
            for chat in self.network.consume_chat_messages():
                self.chat_manager.add_chat_line(chat.get("name", "Player"), chat.get("text", ""))
            self.apply_local_multiplayer_state(self.network.get_local_player_state())

            if self.show_scoreboard:
                scoreboard = self.network.get_scoreboard()
                lines = ["Players"]
                for idx, p in enumerate(scoreboard, 1):
                    pname = p.get("name", "Player")
                    pscore = int(p.get("score", 0))
                    pkills = int(p.get("kills", 0))
                    pdeaths = int(p.get("deaths", 0))
                    php = "DEAD" if not p.get("alive", True) else str(int(p.get("hp", 0)))
                    lines.append(f"{idx}. {pname} | S:{pscore} | K/D:{pkills}/{pdeaths} | HP:{php}")
                self.hud_manager.scoreboard_text.setText("\n".join(lines))

            self.is_shooting = self.shoot_state_frames > 0 and self.can_local_multiplayer_act()
            self.network.send_state(
                pos=self.camera.getPos(),
                heading=self.camera_heading,
                pitch=self.camera_pitch,
                weapon=self.current_weapon,
                shooting=self.is_shooting,
                score=self.score
            )
            if self.shoot_state_frames > 0:
                self.shoot_state_frames -= 1
            
            self.update_remote_players(dt)

        self.update_multiplayer_feedback(dt)
        return task.cont

    def update_aim(self, task):
        """Обновление анимации прицеливания"""
        result = self.weapon_manager_new.update_aim(task)
        # Sync legacy references
        self.is_aiming = self.weapon_manager_new.is_aiming
        self.aim_transition = self.weapon_manager_new.aim_transition
        self.mouse_sensitivity = self.weapon_manager_new.game.mouse_sensitivity
        return result

    def start_aiming(self):
        """Начало прицеливания"""
        self.weapon_manager_new.start_aiming()
        self.is_aiming = self.weapon_manager_new.is_aiming

    def stop_aiming(self):
        """Конец прицеливания"""
        self.weapon_manager_new.stop_aiming()
        self.is_aiming = self.weapon_manager_new.is_aiming

    def switch_weapon(self, weapon_name):
        """Переключает оружие"""
        self.weapon_manager_new.switch_weapon(weapon_name)
        # Sync legacy references
        self.current_weapon = self.weapon_manager_new.current_weapon
        self.weapon_model = self.weapon_manager_new.weapon_model
        self.shoot_cooldown = self.weapon_manager_new.shoot_cooldown
        self.last_shot_time = self.weapon_manager_new.last_shot_time
        self.weapon_animation = self.weapon_manager_new.weapon_animation
        self.is_drawing_weapon = self.weapon_manager_new.is_drawing_weapon

    def play_weapon_draw_animation(self):
        """Проигрывает анимацию доставания оружия"""
        self.weapon_manager_new.play_weapon_draw_animation()
        # Sync legacy references
        self.is_drawing_weapon = self.weapon_manager_new.is_drawing_weapon
        self.weapon_animation = self.weapon_manager_new.weapon_animation

    def update_mouse_sensitivity(self):
        """Обновляет чувствительность мыши на основе настроек"""
        self.mouse_sensitivity = self.settings.get('sensitivity', self.DEFAULT_SETTINGS['sensitivity'])

    def setup_mouse(self):
        """Настраивает управление мышью"""
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)
        base.win.requestProperties(props)
        
        base.disableMouse()
        
        self.mouse_sensitivity = self.settings.get('sensitivity', self.DEFAULT_SETTINGS['sensitivity'])
        
        self.accept("mouse1", self.on_mouse_press)
        self.accept("mouse1-up", self.on_mouse_release)
        
        taskMgr.add(self.mouseTask, 'mouseTask')
        
    def mouseTask(self, task):
        """Обрабатывает движение мыши"""
        if task.time < 0.05:
            return Task.cont
            
        md = base.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        
        if base.win.movePointer(0,
            int(base.win.getProperties().getXSize() / 2),
            int(base.win.getProperties().getYSize() / 2)):
            deltaX = x - base.win.getProperties().getXSize()//2
            deltaY = y - base.win.getProperties().getYSize()//2
            
            sensitivity_factor = 25.0
            deltaX *= self.mouse_sensitivity * sensitivity_factor
            deltaY *= self.mouse_sensitivity * sensitivity_factor
            
            heading = self.camera.getH() - deltaX * 0.3
            pitch = self.camera.getP() + deltaY * 0.3
            
            pitch = min(90, max(-90, pitch))
            
            self.camera.setH(heading)
            self.camera.setP(pitch)
        
        return Task.cont

    def on_tab_down(self):
        if self.is_splash_screen_active:
            return
        if not (self.is_multiplayer and self.network and self.network.is_connected()):
            return
        self.show_scoreboard = True
        self.hud_manager.scoreboard_text.show()

    def on_tab_up(self):
        self.show_scoreboard = False
        self.hud_manager.scoreboard_text.hide()

    def cycle_weapon(self, direction):
        if self.is_splash_screen_active:
            return
        
        weapons_list = list(self.weapons.keys())
        current_index = weapons_list.index(self.current_weapon)
        new_index = (current_index + direction) % len(weapons_list)
        self.switch_weapon(weapons_list[new_index])

    def on_mouse_press(self):
        """Обработчик нажатия кнопки мыши"""
        if self.is_splash_screen_active:
            return
        if self.chat_manager.is_chat_active or self.is_shader_debug_open:
            return
        
        self.mouse_pressed = True
        self.shoot()

    def on_mouse_release(self):
        """Обработчик отпускания кнопки мыши"""
        if self.is_splash_screen_active:
            return
        
        self.mouse_pressed = False

    def create_shell_casing(self):
        self.shell_manager.create_shell_casing()
        # Sync legacy reference
        self.active_shells = self.shell_manager.active_shells

    def update_shells(self, task):
        return self.shell_manager.update_shells(task)

    def remove_shell(self, shell_data, task):
        return self.shell_manager.remove_shell(shell_data, task)

    def apply_settings(self, new_settings):
        self.settings.update(new_settings)
        
        if 'sensitivity' in new_settings:
            self.mouse_sensitivity = new_settings['sensitivity']
        if 'fov' in new_settings:
            lens = self.cam.node().getLens()
            lens.setFov(new_settings['fov'])
        if 'show_score' in new_settings:
            self.show_score = new_settings['show_score']
        if 'show_timer' in new_settings:
            self.show_timer = new_settings['show_timer']
        if 'show_hitbox_debug' in new_settings:
            self.refresh_hitbox_debug_visibility()
            
        self.settings_manager.save_settings()


    def show_main_menu(self):
        """Вызывается экраном загрузки при завершении его работы"""
        if self.menu is None:
            print("Warning: Меню не было создано в splash screen, создаем сейчас...")
            self.menu = MainMenu(self)
        print("OK: Показываем главное меню")
        self.menu.show()
    
    # ==================== РњРЈР›Р¬РўРРџР›Р•Р•Р  ====================
    
    def show_multiplayer_menu(self):
        return self.multiplayer_manager.show_multiplayer_menu()

    def connect_to_server(self, server_ip: str, port: int, player_name: str):
        return self.multiplayer_manager.connect_to_server(server_ip, port, player_name)

    def back_from_multiplayer(self):
        return self.multiplayer_manager.back_from_multiplayer()

    def start_multiplayer_game(self):
        return self.multiplayer_manager.start_multiplayer_game()

    def update_remote_players(self, dt: float):
        return self.multiplayer_manager.update_remote_players(dt)

    def cleanup_multiplayer(self):
        return self.multiplayer_manager.cleanup_multiplayer()

        
