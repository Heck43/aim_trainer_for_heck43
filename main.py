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
            print(f"✓ Найден libpandagl.dll в: {internal_dir}")
        else:
            print(f"✗ libpandagl.dll НЕ найден в: {internal_dir}")
    
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
                        print(f"✓ Предзагружен: {dll_name}")
                    except Exception as e:
                        print(f"✗ Ошибка загрузки {dll_name}: {e}")
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
    import p3dimgui.backend as p3dimgui_backend
    import p3dimgui.shaders as p3dimgui_shaders
    p3dimgui_backend.VERT_SHADER = p3dimgui_shaders.VERT_SHADER
    p3dimgui_backend.FRAG_SHADER = p3dimgui_shaders.FRAG_SHADER

    def _patch_p3dimgui_backend():
        if getattr(p3dimgui_backend, "_aim_trainer_mouse_patch", False):
            return

        def _patched_window_event(self, _=None):
            if not self.window:
                return
            win_x = max(1, int(self.window.getXSize()))
            win_y = max(1, int(self.window.getYSize()))
            fb_x = max(1, int(getattr(self.window, "getFbXSize", lambda: win_x)()))
            fb_y = max(1, int(getattr(self.window, "getFbYSize", lambda: win_y)()))
            self._aim_trainer_window_size = (win_x, win_y)
            self._aim_trainer_framebuffer_size = (fb_x, fb_y)
            self.io.display_size = (win_x, win_y)
            self.io.display_framebuffer_scale = (fb_x / win_x, fb_y / win_y)

        def _patched_new_frame(self, task):
            if self.root.isHidden():
                return task.cont

            self.io.delta_time = base.clock.getDt()
            self._ImGuiBackend__windowEvent()
            win_x, win_y = getattr(self, "_aim_trainer_window_size", (1, 1))

            if getattr(base, "mouseWatcherNode", None) and base.mouseWatcherNode.hasMouse():
                mouse_x = (base.mouseWatcherNode.getMouseX() + 1.0) * 0.5 * win_x
                mouse_y = (1.0 - ((base.mouseWatcherNode.getMouseY() + 1.0) * 0.5)) * win_y
                self.io.mouse_pos = (mouse_x, mouse_y)
            elif self.window:
                mouse = self.window.getPointer(0)
                if mouse.getInWindow():
                    self.io.mouse_pos = (mouse.getX(), mouse.getY())
                else:
                    self.io.mouse_pos = (-imgui.FLT_MAX, -imgui.FLT_MAX)
            else:
                self.io.mouse_pos = (-imgui.FLT_MAX, -imgui.FLT_MAX)

            imgui.new_frame()
            base.messenger.send("imgui-new-frame")
            return task.cont

        def _patched_render_frame(self, task):
            if self.root.isHidden():
                return task.cont

            imgui.render()
            draw_data = imgui.get_draw_data()
            clip_off = draw_data.display_pos
            clip_scale = draw_data.framebuffer_scale
            fb_width = int(draw_data.display_size.x * clip_scale.x)
            fb_height = int(draw_data.display_size.y * clip_scale.y)
            if fb_width <= 0 or fb_height <= 0:
                return task.cont

            self._ImGuiBackend__updateTextures()

            for child in self.root.children:
                child.detachNode()

            for i, cmd_list in enumerate(draw_data.cmd_lists):
                if i > len(self.geomData) - 1:
                    self.geomData.append(
                        p3dimgui_backend.GeomList(
                            p3dimgui_backend.GeomVertexData(
                                f"imgui-vertex-{i}",
                                self.vformat,
                                p3dimgui_backend.Geom.UH_stream,
                            )
                        )
                    )

                geom_list = self.geomData[i]
                vertex_handle = geom_list.vdata.modifyArrayHandle(0)
                if vertex_handle.getNumRows() < cmd_list.vtx_buffer.size():
                    vertex_handle.uncleanSetNumRows(cmd_list.vtx_buffer.size())
                vertex_handle.setData(
                    p3dimgui_backend.ctypes.string_at(
                        cmd_list.vtx_buffer.data_address(),
                        cmd_list.vtx_buffer.size() * imgui.VERTEX_SIZE,
                    )
                )

                index_buffer = cmd_list.idx_buffer.data_address()
                for k, draw_cmd in enumerate(cmd_list.cmd_buffer):
                    if k > len(geom_list.nodepaths) - 1:
                        geom_list.nodepaths.append(
                            p3dimgui_backend.ImGuiBackend._ImGuiBackend__createGeomnode(geom_list.vdata)
                        )

                    np = geom_list.nodepaths[k]
                    np.reparentTo(self.root)
                    node = np.node()

                    index_handle = node.modifyGeom(0).modifyPrimitive(0).modifyVertices(draw_cmd.elem_count).modifyHandle()
                    if index_handle.getNumRows() < draw_cmd.elem_count:
                        index_handle.uncleanSetNumRows(draw_cmd.elem_count)

                    index_handle.setData(
                        p3dimgui_backend.ctypes.string_at(
                            index_buffer,
                            draw_cmd.elem_count * imgui.INDEX_SIZE,
                        )
                    )
                    index_buffer += draw_cmd.elem_count * imgui.INDEX_SIZE

                    state = p3dimgui_backend.RenderState.makeEmpty()

                    if draw_cmd.tex_ref.get_tex_id():
                        texture = self.textures[draw_cmd.tex_ref.get_tex_id()]
                        state = state.addAttrib(p3dimgui_backend.TextureAttrib.make(texture))

                    node.setGeomState(0, state)

            return task.cont

        p3dimgui_backend.ImGuiBackend._ImGuiBackend__windowEvent = _patched_window_event
        p3dimgui_backend.ImGuiBackend._ImGuiBackend__newFrame = _patched_new_frame
        p3dimgui_backend.ImGuiBackend._ImGuiBackend__renderFrame = _patched_render_frame
        p3dimgui_backend._aim_trainer_mouse_patch = True

    _patch_p3dimgui_backend()
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
from target import Target
from splash_screen import SplashScreen
from pause_menu import PauseMenu
from resource_manager import ResourceManager
from target_pool import TargetPool
from multiplayer.client import NetworkClient
from multiplayer.player_model import RemotePlayerModel
from multiplayer.lobby_menu import LobbyMenu
from shader_system import ShaderSystem
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
                    print(f"✓ Добавлен model-path и texture-path: {path}")

        self.fps = 0
        
        self.cTrav = CollisionTraverser('traverser')
        self.cQueue = CollisionHandlerQueue()
        
        try:
            self.map_model = self.safe_load_model("xz.egg")
            self.map_model.reparentTo(self.render)
            self.map_model.setPos(0, 0, 0)
            self.map_model.setScale(1)
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
        
        self.DEFAULT_SETTINGS = {
            'sensitivity': 50.0,
            'fov': 70,
            'resolution': '1280x720',
            'fullscreen': True,
            'show_score': True,
            'show_timer': True,
            'volume': 100,
            'show_target_images': False,
            'damage_numbers': True,
            'killfeed': True,
            'show_fps': True,
            'recoil_enabled': True,
            'weapon_position': {
                'x': 0.25,
                'y': 0.6,
                'z': -0.3
            },
            'bhop_enabled': True,
            'audio': {
                'music_enabled': True,
                'music_volume': 0.5,
                'current_track': 'kiss_me_again.mp3'
            },
            'target_count': 10,
            'bullet_traces': True,
            'spread_enabled': True,
        }
        
        self.settings = self.load_settings()
        
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
        print("📦 ResourceManager инициализирован")
        
        self.shader_system = ShaderSystem(self)
        self.shader_system.initialize()
        self.target_pool = None

        self.menu = None
        self.pause_menu = None
        
        self.network = None
        self.is_multiplayer = False
        self.remote_players = {}  # {player_id: RemotePlayerModel}
        self.lobby_menu = None
        self.current_weapon = "pistol"
        self.is_shooting = False
        self.shoot_state_frames = 0
        
        self.splash = SplashScreen(self)
        self.splash.start()

        self.score = 0
        self.combo_multiplier = 1.0
        self.last_hit_time = 0
        self.combo_window = 2.0
        self.start_time = 0
        self.game_time = 0
        
        self.score_text = OnscreenText(
            text="Score: 0",
            pos=(-1.3, 0.9),
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            scale=0.07,
            mayChange=True
        )
        self.score_text.hide()
        
        self.timer_text = OnscreenText(
            text="Time: 0.0",
            pos=(-0.0, -0.9),
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            scale=0.07,
            shadow=(0, 0, 0, 1)
        )
        self.timer_text.hide()

        self.is_chat_active = False
        self.chat_messages = []
        self.chat_message_lifetime = 10.0
        self.chat_last_toggle_time = 0.0
        self.chat_text = OnscreenText(
            text="",
            pos=(-1.28, -0.80),
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            scale=0.04,
            mayChange=True,
        )
        self.chat_text.hide()

        self.chat_entry = DirectEntry(
            text="",
            scale=0.05,
            pos=(-1.28, 0, -0.93),
            frameColor=(0, 0, 0, 0.7),
            text_fg=(1, 1, 1, 1),
            initialText="",
            numLines=1,
            width=28,
            focus=0,
            command=self.submit_chat_message,
            suppressKeys=False,
        )
        self.chat_entry.hide()

        self.show_scoreboard = False
        self.scoreboard_text = OnscreenText(
            text="",
            pos=(1.25, 0.86),
            fg=(1, 1, 1, 1),
            align=TextNode.ARight,
            scale=0.05,
            mayChange=True,
        )
        self.scoreboard_text.hide()

        self.is_shader_debug_open = False
        self.imgui_backend = None
        self.using_imgui_shader_debug = False
        self.shader_debug_widgets = []
        self.shader_debug_panel = None
        self.shader_ui_search = ""
        self.shader_ui_preset_name = self.shader_system.current_preset_name
        self.shader_ui_selected_preset = self.shader_system.current_preset_name
        self.shader_ui_config = {
            "width_ratio": 0.46,
            "height_ratio": 0.52,
            "min_width": 420.0,
            "min_height": 280.0,
            "max_width": 700.0,
            "max_height": 520.0,
            "margin_x": 24.0,
            "margin_y": 56.0,
            "alpha": 0.94,
            "font_scale": 0.82,
            "lock_window_size": False,
            "show_style_editor": False,
            "show_imgui_demo": False,
        }
        
        properties = WindowProperties()
        properties.setTitle("Aim Trainer")
        properties.setCursorHidden(True)
        properties.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(properties)

        if not self.initialize_shader_debug_imgui():
            self.create_shader_debug_ui()
        
        self.camLens.setFov(self.settings['fov'])
        
        self.move_speed = 10.0
        self.sprint_speed = 15.0
        self.jump_power = 15.0
        self.gravity = -50.0
        self.vertical_velocity = 0.0
        self.horizontal_velocity = Vec3(0, 0, 0)
        self.is_jumping = False
        self.ground_height = 0
        self.is_sprinting = False
        self.jump_speed_boost = 1.0
        
        self.prev_camera_heading = 0
        self.prev_camera_pitch = 0
        self.camera_rotation_speed = 0
        
        self.jump_combo_time = 1.0
        self.jump_combo_multiplier = 1.0
        self.max_combo_multiplier = 5.0
        self.combo_stages = [
            {'jumps': 1, 'multiplier': 1.0},
            {'jumps': 2, 'multiplier': 1.4},
            {'jumps': 3, 'multiplier': 1.8},
            {'jumps': 4, 'multiplier': 2.2},
            {'jumps': 5, 'multiplier': 2.6},
            {'jumps': 6, 'multiplier': 3.0},
            {'jumps': 7, 'multiplier': 3.2}
        ]
        self.current_combo_jumps = 0
        self.last_jump_time = 0
        self.combo_task = None
        
        self.can_shoot = True
        self.current_weapon = "rifle"
        
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
        
        self.shoot_cooldown = self.weapons[self.current_weapon]["cooldown"]
        self.recoil_time = 0.05
        self.is_shooting = False
        self.shoot_state_frames = 0
        self.shoot_time = 0
        self.original_weapon_pos = None
        self.original_weapon_hpr = None
        
        # Параметры отдачи
        self.recoil_pitch = 0
        self.recoil_yaw = 0
        self.max_recoil_pitch = 2.0
        self.max_recoil_yaw = 1.0
        self.recoil_recovery_speed = 5.0
        self.recoil_recovery_delay = 0.1
        self.last_shot_time = 0
        
        self.current_spread = 0.0
        
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
        
        self.killfeed_messages = []
        self.killfeed_fade_time = 0.3
        self.killfeed_slide_distance = 0.2
        self.killfeed_duration = 5
        
        self.active_shells = []
        
        self.shell_model = self.safe_load_model("models/box")
        self.shell_model.setScale(0.02, 0.05, 0.02)
        self.shell_model.setColor(0.8, 0.6, 0.2)
        
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
        self.accept("enter", self.toggle_chat_input)
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
        
        self.taskMgr.add(self.update_shells, "update_shells")
        
        self.ray = CollisionRay()
        rayNode = CollisionNode('mouseRay')
        rayNode.addSolid(self.ray)
        rayNode.setFromCollideMask(BitMask32.bit(1))
        rayNode.setIntoCollideMask(BitMask32.allOff())
        self.rayNodePath = self.camera.attachNewNode(rayNode)
        self.cTrav.addCollider(self.rayNodePath, self.cQueue)
        
        self.accept("window-event", self.cleanup)
        
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

        self.music = None
        self.current_music_path = None

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

    def create_text(self, x, y):
        return OnscreenText(
            text="",
            style=1,
            fg=(1, 1, 1, 1),
            pos=(x, y),
            align=TextNode.ALeft,
            scale=.05)

    def initialize_shader_debug_imgui(self):
        if not HAS_P3D_IMGUI:
            return False
        try:
            self.imgui_backend = p3dimgui.ImGuiBackend(style="dark")
            self.imgui_backend.io.mouse_draw_cursor = True
            self.imgui_backend.hide()
            self.accept("imgui-new-frame", self.render_shader_debug_imgui)
            self.using_imgui_shader_debug = True
            print("[ShaderDebug] Using in-game Dear ImGui backend")
            return True
        except Exception as exc:
            self.imgui_backend = None
            self.using_imgui_shader_debug = False
            print(f"[ShaderDebug] ImGui backend unavailable, falling back to DirectGUI: {exc}")
            return False

    def render_shader_debug_imgui(self):
        if not self.is_shader_debug_open or not self.using_imgui_shader_debug or not self.imgui_backend:
            return

        snapshot = self.shader_system.get_ui_snapshot()
        preset_names = snapshot["preset_names"]
        if self.shader_ui_selected_preset not in preset_names and preset_names:
            self.shader_ui_selected_preset = preset_names[0]
        if not self.shader_ui_preset_name:
            self.shader_ui_preset_name = snapshot["current_preset"]

        io = imgui.get_io()
        style = imgui.get_style()
        style.alpha = float(self.shader_ui_config.get("alpha", 1.0))
        display_width = float(io.display_size.x or 1024.0)
        display_height = float(io.display_size.y or 768.0)
        margin_x = float(self.shader_ui_config.get("margin_x", 24.0))
        margin_y = float(self.shader_ui_config.get("margin_y", 56.0))
        min_width = float(self.shader_ui_config.get("min_width", 480.0))
        min_height = float(self.shader_ui_config.get("min_height", 320.0))
        max_width = min(
            float(self.shader_ui_config.get("max_width", 860.0)),
            max(min_width, display_width - (margin_x * 2.0)),
        )
        max_height = min(
            float(self.shader_ui_config.get("max_height", 620.0)),
            max(min_height, display_height - (margin_y + 24.0)),
        )
        default_width = min(max_width, max(min_width, display_width * float(self.shader_ui_config.get("width_ratio", 0.58))))
        default_height = min(max_height, max(min_height, display_height * float(self.shader_ui_config.get("height_ratio", 0.62))))

        imgui.set_next_window_pos(ImVec2(margin_x, margin_y), imgui.Cond_.always)
        imgui.set_next_window_size_constraints(
            ImVec2(min_width, min_height),
            ImVec2(max_width, max_height),
        )
        imgui.set_next_window_size(ImVec2(default_width, default_height), imgui.Cond_.always)
        window_flags = (
            imgui.WindowFlags_.no_saved_settings.value
            | imgui.WindowFlags_.no_collapse.value
        )
        if self.shader_ui_config.get("lock_window_size", False):
            window_flags |= imgui.WindowFlags_.no_resize.value

        imgui.begin("Shader Shell", flags=window_flags)
        if hasattr(imgui, "set_window_font_scale"):
            imgui.set_window_font_scale(float(self.shader_ui_config.get("font_scale", 1.0)))
        imgui.text("F7 / Esc close")
        imgui.same_line()
        self._render_shader_status_badge(snapshot["compile_status"], "experimental")
        imgui.same_line()
        dirty_text = "Dirty" if snapshot["preset_dirty"] else "Saved"
        self._render_shader_status_badge(dirty_text, "active" if not snapshot["preset_dirty"] else "experimental")
        imgui.separator()

        if imgui.begin_tab_bar("shader-shell-tabs"):
            for tab in snapshot["tabs"]:
                opened, _ = imgui.begin_tab_item(tab["label"])
                if opened:
                    imgui.begin_child(f"shader-shell-body::{tab['id']}", ImVec2(0, 0))
                    if tab["id"] == "home":
                        self._render_shader_home_tab(snapshot)
                    elif tab["id"] == "techniques":
                        self._render_shader_techniques_tab(snapshot)
                    elif tab["id"] == "targets":
                        self._render_shader_panel_tab("targets", snapshot)
                    elif tab["id"] == "weapon":
                        self._render_shader_panel_tab("weapon", snapshot)
                    elif tab["id"] == "post":
                        self._render_shader_panel_tab("post", snapshot)
                    elif tab["id"] == "volumes":
                        self._render_shader_panel_tab("volumes", snapshot)
                    elif tab["id"] == "stats":
                        self._render_shader_stats_tab(snapshot)
                    imgui.end_child()
                    imgui.end_tab_item()
            opened, _ = imgui.begin_tab_item("ImGui")
            if opened:
                imgui.begin_child("shader-shell-body::imgui", ImVec2(0, 0))
                self._render_imgui_settings_tab(display_width, display_height)
                imgui.end_child()
                imgui.end_tab_item()
            imgui.end_tab_bar()

        if self.shader_ui_config.get("show_imgui_demo", False) and hasattr(imgui, "show_demo_window"):
            visible = True
            imgui.show_demo_window(visible)

        imgui.end()

    def _shader_status_color(self, status: str):
        palette = {
            "active": imgui.ImVec4(0.33, 0.82, 0.48, 1.0),
            "planned": imgui.ImVec4(0.45, 0.67, 0.95, 1.0),
            "experimental": imgui.ImVec4(0.97, 0.72, 0.25, 1.0),
            "broken": imgui.ImVec4(0.93, 0.33, 0.33, 1.0),
        }
        return palette.get(status, imgui.ImVec4(0.8, 0.8, 0.8, 1.0))

    def _render_shader_status_badge(self, text: str, status: str):
        imgui.text_colored(self._shader_status_color(status), text)

    def _render_shader_global_toggles(self):
        for label, key in [
            ("Master", "master_enabled"),
            ("Targets", "target_enabled"),
            ("Weapon", "weapon_enabled"),
            ("Post", "post_enabled"),
            ("Volumes", "volumes_enabled"),
            ("Debug Views", "debug_views_enabled"),
        ]:
            changed, value = imgui.checkbox(label, bool(self.shader_system.state.get(key, False)))
            if changed:
                self.update_shader_debug_bool(key, value)
            imgui.same_line()
        imgui.new_line()

    def _render_shader_home_tab(self, snapshot: dict):
        self._render_shader_global_toggles()
        imgui.separator_text("Presets")

        changed, self.shader_ui_preset_name = imgui.input_text("Preset Name", self.shader_ui_preset_name)
        if changed:
            self.shader_ui_preset_name = self.shader_ui_preset_name.strip()

        if imgui.button("Save"):
            if self.shader_system.save_preset(self.shader_ui_preset_name or "default"):
                self.shader_ui_selected_preset = self.shader_system.current_preset_name
                self.shader_ui_preset_name = self.shader_system.current_preset_name
        imgui.same_line()
        if imgui.button("Load"):
            if self.shader_system.load_preset(self.shader_ui_selected_preset):
                self.shader_ui_preset_name = self.shader_system.current_preset_name
        imgui.same_line()
        if imgui.button("Delete"):
            if self.shader_system.delete_preset(self.shader_ui_selected_preset):
                self.shader_ui_selected_preset = self.shader_system.current_preset_name
                self.shader_ui_preset_name = self.shader_system.current_preset_name
        imgui.same_line()
        if imgui.button("Reload Shaders"):
            self.shader_system.reload_shaders()
        imgui.same_line()
        if imgui.button("Reset All"):
            self.reset_shader_debug_values()
            self.shader_ui_preset_name = self.shader_system.current_preset_name

        if imgui.begin_list_box("Available Presets", ImVec2(-1, 72)):
            for preset_name in snapshot["preset_names"]:
                selected = preset_name == self.shader_ui_selected_preset
                clicked, selected = imgui.selectable(preset_name, selected)
                if clicked:
                    self.shader_ui_selected_preset = preset_name
            imgui.end_list_box()

        imgui.separator_text("Overview")
        imgui.bullet_text(f"Preset: {snapshot['current_preset']}")
        imgui.bullet_text(f"Enabled techniques: {snapshot['active_count']} / {snapshot['technique_count']}")
        imgui.bullet_text(f"Render: {snapshot['render_size'][0]} x {snapshot['render_size'][1]}")
        imgui.bullet_text(f"Framebuffer: {snapshot['framebuffer_size'][0]} x {snapshot['framebuffer_size'][1]}")
        if snapshot["buffer_size"]:
            imgui.bullet_text(f"Scene Buffer: {snapshot['buffer_size'][0]} x {snapshot['buffer_size'][1]}")
        imgui.bullet_text(f"Post Stage Applied: {snapshot['post_stage_applied']}")

        imgui.separator_text("Pipeline Order")
        for idx, stage_name in enumerate(snapshot["pipeline_order"], 1):
            imgui.bullet_text(f"{idx}. {stage_name}")

        imgui.separator_text("Roadmap")
        for roadmap_item in [
            "Color grading / tonemap / LUT pack",
            "Bloom / lens dirt / glare shell",
            "Reactive overlays for damage, kill and ADS states",
            "Target outline / respawn materialize pack",
            "Local fog, heat haze and impact dust placeholders",
        ]:
            imgui.bullet_text(roadmap_item)

    def _render_shader_techniques_tab(self, snapshot: dict):
        changed, self.shader_ui_search = imgui.input_text("Search", self.shader_ui_search)
        if changed:
            self.shader_ui_search = self.shader_ui_search.strip()
        imgui.separator()
        self._render_shader_grouped_cards(snapshot["registry"], self.shader_ui_search)

    def _render_shader_panel_tab(self, panel_id: str, snapshot: dict):
        panel_registry = snapshot["panels"].get(panel_id, [])
        self._render_shader_grouped_cards(panel_registry, "")

    def _render_shader_grouped_cards(self, techniques: list, search_query: str):
        grouped = {}
        lowered_search = search_query.lower().strip()
        for technique in techniques:
            haystack = " ".join(
                [
                    technique.get("display_name", ""),
                    technique.get("description", ""),
                    technique.get("group", ""),
                    technique.get("status", ""),
                ]
            ).lower()
            if lowered_search and lowered_search not in haystack:
                continue
            grouped.setdefault(technique.get("group", "Misc"), []).append(technique)

        if not grouped:
            imgui.text_colored(self._shader_status_color("planned"), "No techniques match the current filter.")
            return

        for group_name, items in grouped.items():
            imgui.separator_text(group_name)
            for technique in sorted(items, key=lambda item: item.get("order", 0)):
                self._render_shader_technique_card(technique)

    def _render_shader_technique_card(self, technique: dict):
        status = technique.get("status", "planned")
        header_open = imgui.collapsing_header(
            f"{technique['display_name']}##{technique['technique_id']}",
            imgui.TreeNodeFlags_.default_open.value if status in ("active", "experimental") else 0,
        )
        if not header_open:
            return

        self._render_shader_status_badge(status.upper(), status)
        imgui.same_line()
        imgui.text(f"Stage: {technique.get('stage', 'n/a')} | Cost: {technique.get('cost', 'n/a')}")
        imgui.text_wrapped(technique.get("description", ""))
        if technique.get("debug_notes"):
            imgui.text_colored(imgui.ImVec4(0.62, 0.70, 0.82, 1.0), technique["debug_notes"])

        enabled_key = technique.get("enabled_key")
        if enabled_key:
            changed, enabled = imgui.checkbox(
                f"Enabled##{technique['technique_id']}",
                bool(self.shader_system.state.get(enabled_key, False)),
            )
            if changed:
                self.update_shader_debug_bool(enabled_key, enabled)
        else:
            imgui.begin_disabled()
            imgui.checkbox(f"Enabled##{technique['technique_id']}", False)
            imgui.end_disabled()

        if technique["params"]:
            for param in technique["params"]:
                slider_width = max(240.0, imgui.get_content_region_avail().x - 8.0)
                imgui.set_next_item_width(slider_width)
                changed, value = imgui.slider_float(
                    f"{param['label']}##{technique['technique_id']}::{param['key']}",
                    float(param["value"]),
                    param["min"],
                    param["max"],
                    param.get("format", "%.2f"),
                )
                if changed:
                    self.update_shader_debug_value(param["key"], value)
        else:
            imgui.text_colored(
                self._shader_status_color("planned"),
                "Planned placeholder. GLSL implementation will be attached later.",
            )
        imgui.spacing()

    def _render_shader_stats_tab(self, snapshot: dict):
        imgui.separator_text("Runtime")
        imgui.bullet_text(f"Compile Status: {snapshot['compile_status']}")
        imgui.bullet_text(f"Current Preset: {snapshot['current_preset']}")
        imgui.bullet_text(f"Preset Dirty: {'Yes' if snapshot['preset_dirty'] else 'No'}")
        imgui.bullet_text(f"Active Techniques: {snapshot['active_count']}")
        imgui.bullet_text(f"Fullscreen Stage Applied: {snapshot['post_stage_applied']}")
        imgui.bullet_text(f"Post Supported: {'Yes' if snapshot['post_supported'] else 'No'}")
        imgui.separator_text("Buffers")
        imgui.bullet_text(f"Render Size: {snapshot['render_size'][0]} x {snapshot['render_size'][1]}")
        imgui.bullet_text(f"Framebuffer Size: {snapshot['framebuffer_size'][0]} x {snapshot['framebuffer_size'][1]}")
        if snapshot["buffer_size"]:
            imgui.bullet_text(f"Scene Buffer Size: {snapshot['buffer_size'][0]} x {snapshot['buffer_size'][1]}")
        else:
            imgui.bullet_text("Scene Buffer Size: inactive")
        imgui.separator_text("Debug")
        imgui.text_wrapped(
            "This shell is the future ReShade-Lite host for custom GLSL passes, object shaders and local volumetric placeholders."
        )

    def _render_imgui_settings_tab(self, display_width: float, display_height: float):
        cfg = self.shader_ui_config

        imgui.separator_text("Shell Window")
        changed, value = imgui.slider_float("Width Ratio", float(cfg["width_ratio"]), 0.35, 0.90, "%.2f")
        if changed:
            cfg["width_ratio"] = value
        changed, value = imgui.slider_float("Height Ratio", float(cfg["height_ratio"]), 0.35, 0.90, "%.2f")
        if changed:
            cfg["height_ratio"] = value
        changed, value = imgui.slider_float("Margin X", float(cfg["margin_x"]), 8.0, 96.0, "%.0f")
        if changed:
            cfg["margin_x"] = value
        changed, value = imgui.slider_float("Margin Y", float(cfg["margin_y"]), 8.0, 128.0, "%.0f")
        if changed:
            cfg["margin_y"] = value
        changed, value = imgui.slider_float("Min Width", float(cfg["min_width"]), 360.0, 760.0, "%.0f")
        if changed:
            cfg["min_width"] = value
        changed, value = imgui.slider_float("Min Height", float(cfg["min_height"]), 260.0, 640.0, "%.0f")
        if changed:
            cfg["min_height"] = value
        changed, value = imgui.slider_float("Max Width", float(cfg["max_width"]), 520.0, min(display_width, 1400.0), "%.0f")
        if changed:
            cfg["max_width"] = value
        changed, value = imgui.slider_float("Max Height", float(cfg["max_height"]), 360.0, min(display_height, 1200.0), "%.0f")
        if changed:
            cfg["max_height"] = value
        changed, value = imgui.checkbox("Lock Window Resize", bool(cfg["lock_window_size"]))
        if changed:
            cfg["lock_window_size"] = value

        imgui.separator_text("Visual")
        changed, value = imgui.slider_float("Font Scale", float(cfg["font_scale"]), 0.70, 1.35, "%.2f")
        if changed:
            cfg["font_scale"] = value
        changed, value = imgui.slider_float("Alpha", float(cfg["alpha"]), 0.65, 1.00, "%.2f")
        if changed:
            cfg["alpha"] = value

        imgui.separator_text("Tools")
        changed, value = imgui.checkbox("Show Style Editor", bool(cfg["show_style_editor"]))
        if changed:
            cfg["show_style_editor"] = value
        changed, value = imgui.checkbox("Show ImGui Demo", bool(cfg["show_imgui_demo"]))
        if changed:
            cfg["show_imgui_demo"] = value
        if imgui.button("Reset ImGui Shell"):
            self.shader_ui_config.update(
                {
                    "width_ratio": 0.46,
                    "height_ratio": 0.52,
                    "min_width": 420.0,
                    "min_height": 280.0,
                    "max_width": 700.0,
                    "max_height": 520.0,
                    "margin_x": 24.0,
                    "margin_y": 56.0,
                    "alpha": 0.94,
                    "font_scale": 0.82,
                    "lock_window_size": False,
                    "show_style_editor": False,
                    "show_imgui_demo": False,
                }
            )

        imgui.separator_text("Display")
        imgui.bullet_text(f"Display Size: {int(display_width)} x {int(display_height)}")
        imgui.bullet_text(f"Current Width Ratio: {cfg['width_ratio']:.2f}")
        imgui.bullet_text(f"Current Height Ratio: {cfg['height_ratio']:.2f}")

        if cfg.get("show_style_editor", False) and hasattr(imgui, "show_style_editor"):
            imgui.separator_text("Style Editor")
            imgui.show_style_editor()

    def create_shader_debug_ui(self):
        panel = DirectFrame(
            frameColor=(0.06, 0.06, 0.08, 0.92),
            frameSize=(-0.62, 0.62, -0.82, 0.82),
            pos=(0.0, 0, 0.0),
        )
        panel.hide()
        self.shader_debug_panel = panel

        title = DirectLabel(
            text="Shader Debug",
            scale=0.07,
            pos=(0, 0, 0.74),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            parent=panel,
        )
        self.shader_debug_widgets.append(title)

        subtitle = DirectLabel(
            text="F7 close | post stages: 0 off, 1 filter, 2 glsl copy, 3 fx",
            scale=0.04,
            pos=(0, 0, 0.66),
            text_fg=(0.75, 0.8, 0.9, 1),
            frameColor=(0, 0, 0, 0),
            parent=panel,
        )
        self.shader_debug_widgets.append(subtitle)

        rows = [
            ("Master", "master_enabled", "toggle"),
            ("Target Shader", "target_enabled", "toggle"),
            ("Weapon Shader", "weapon_enabled", "toggle"),
            ("Post FX", "post_enabled", "toggle"),
            ("Post Stage", "post_debug_stage", "slider", (0.0, 3.0)),
            ("Target Hit Flash", "target_hit_flash", "slider", (0.0, 4.0)),
            ("Target Emissive", "target_emissive", "slider", (0.0, 3.0)),
            ("Target Pulse", "target_pulse_speed", "slider", (0.0, 8.0)),
            ("Target Dissolve", "target_dissolve_test", "slider", (0.0, 1.0)),
            ("Weapon Fresnel", "weapon_fresnel", "slider", (0.0, 4.0)),
            ("Weapon Flash", "weapon_flash_strength", "slider", (0.0, 4.0)),
            ("Post Vignette", "post_vignette", "slider", (0.0, 1.0)),
            ("Post Contrast", "post_contrast", "slider", (0.5, 2.0)),
            ("Post Saturation", "post_saturation", "slider", (0.0, 2.0)),
            ("Post Sharpen", "post_sharpen", "slider", (0.0, 2.0)),
            ("Post Hit Tint", "post_hit_tint", "slider", (0.0, 1.0)),
            ("Post Speed FX", "post_speed_strength", "slider", (0.0, 1.0)),
        ]

        y = 0.54
        for row in rows:
            label_text, key, kind = row[:3]
            label = DirectLabel(
                text=label_text,
                scale=0.045,
                pos=(-0.42, 0, y),
                text_align=TextNode.ALeft,
                text_fg=(1, 1, 1, 1),
                frameColor=(0, 0, 0, 0),
                parent=panel,
            )
            self.shader_debug_widgets.append(label)

            if kind == "toggle":
                widget = DirectCheckButton(
                    text="",
                    scale=0.05,
                    pos=(0.38, 0, y - 0.01),
                    indicatorValue=1 if self.shader_system.state.get(key, False) else 0,
                    frameColor=(0, 0, 0, 0),
                    parent=panel,
                )
                widget["command"] = lambda shader_key=key, check_widget=widget: self.update_shader_debug_bool(
                    shader_key,
                    bool(check_widget["indicatorValue"]),
                )
            else:
                low, high = row[3]
                widget = DirectSlider(
                    range=(low, high),
                    value=float(self.shader_system.state.get(key, low)),
                    pageSize=(high - low) / 100.0,
                    scale=0.32,
                    pos=(0.15, 0, y),
                    parent=panel,
                )
                widget["command"] = lambda shader_key=key, slider_widget=widget: self.update_shader_debug_value(
                    shader_key,
                    float(slider_widget["value"]),
                )
            self.shader_debug_widgets.append(widget)
            y -= 0.12

        reset_btn = DirectButton(
            text="Reset",
            scale=0.055,
            pos=(-0.18, 0, -0.68),
            command=self.reset_shader_debug_values,
            parent=panel,
        )
        close_btn = DirectButton(
            text="Close",
            scale=0.055,
            pos=(0.18, 0, -0.68),
            command=self.toggle_shader_debug_panel,
            parent=panel,
        )
        self.shader_debug_widgets.extend([reset_btn, close_btn])

    def _set_overlay_mouse_mode(self, enabled: bool):
        props = WindowProperties()
        props.setCursorHidden(not enabled)
        props.setMouseMode(WindowProperties.M_absolute if enabled else WindowProperties.M_relative)
        self.win.requestProperties(props)

    def toggle_shader_debug_panel(self):
        if self.is_splash_screen_active:
            return
        if self.is_shader_debug_open:
            self.is_shader_debug_open = False
            if self.using_imgui_shader_debug and self.imgui_backend:
                self.imgui_backend.hide()
            if self.shader_debug_panel:
                self.shader_debug_panel.hide()
            self._set_overlay_mouse_mode(False)
            return

        if self.is_chat_active:
            self.close_chat_input()
        if self.is_shader_debug_open:
            self.toggle_shader_debug_panel()

        self.is_shader_debug_open = True
        if self.using_imgui_shader_debug and self.imgui_backend:
            self.imgui_backend.show()
            props = WindowProperties()
            props.setCursorHidden(True)
            props.setMouseMode(WindowProperties.M_absolute)
            self.win.requestProperties(props)
        elif self.shader_debug_panel:
            self.shader_debug_panel.show()
            self._set_overlay_mouse_mode(True)
        self.mouse_pressed = False
        for key in self.keyMap:
            self.keyMap[key] = False

    def update_shader_debug_bool(self, key: str, value):
        self.shader_system.set_state_bool(key, value)

    def update_shader_debug_value(self, key: str, value):
        self.shader_system.set_state_value(key, value)

    def reset_shader_debug_values(self):
        self.shader_system.reset_state()
        if self.using_imgui_shader_debug:
            return
        if not self.shader_debug_panel:
            return
        # Rebuild panel to keep slider values in sync.
        self.shader_debug_panel.destroy()
        self.shader_debug_widgets = []
        self.create_shader_debug_ui()
        if self.is_shader_debug_open and self.shader_debug_panel:
            self.shader_debug_panel.show()

    def create_cross_marker(self, position):
        marker_node = NodePath("hit_marker")
        marker_node.reparentTo(self.render)
        marker_node.setPos(position)
        
        segs = LineSegs()
        segs.setColor(1, 0, 0, 1)
        segs.setThickness(1.5)
        
        size = 0.1
        
        center = Point3(0, 0, 0)
        
        segs.moveTo(center + Point3(-size, 0, 0))
        segs.drawTo(center + Point3(size, 0, 0))
        
        segs.moveTo(center + Point3(0, -size, 0))
        segs.drawTo(center + Point3(0, size, 0))
        
        segs.moveTo(center + Point3(0, 0, -size))
        segs.drawTo(center + Point3(0, 0, size))
        
        cross_lines = segs.create()
        cross_node = NodePath(cross_lines)
        cross_node.reparentTo(marker_node)
        
        marker_node.setBillboardPointEye()
        
        return marker_node

    def create_hit_marker(self, position):
        segs = LineSegs()
        segs.setColor(1, 0, 0, 1)
        segs.setThickness(2.0)
        
        size = 0.2
        
        segs.moveTo(position + Point3(-size, 0, 0))
        segs.drawTo(position + Point3(size, 0, 0))
        
        segs.moveTo(position + Point3(0, 0, -size))
        segs.drawTo(position + Point3(0, 0, size))
        
        marker_node = self.render.attachNewNode(segs.create())
        
        scale_sequence = Sequence(
            marker_node.scaleInterval(0.1, 1.5),  # Увеличение
            marker_node.scaleInterval(0.1, 1.0)   # Уменьшение
        )
        scale_sequence.start()
        
        return marker_node

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

    def setup_weapon(self):
        self.weapon = NodePath("weapon")
        self.weapon.reparentTo(self.camera)
        
        self.weapon_models = {}
        
        pistol = NodePath("pistol")
        pistol.reparentTo(self.weapon)
        
        barrel = self.safe_load_model("models/box")
        barrel.setScale(0.08, 0.4, 0.08)
        barrel.setPos(0, 1.0, -0.1)
        barrel.setColor(0.2, 0.2, 0.2)
        barrel.reparentTo(pistol)
        
        grip = self.safe_load_model("models/box")
        grip.setScale(0.1, 0.1, 0.25)
        grip.setPos(0, 0.8, -0.3)
        grip.setColor(0.3, 0.3, 0.3)
        grip.reparentTo(pistol)
        
        self.weapon_models["pistol"] = pistol
        
        rifle = NodePath("rifle")
        rifle.reparentTo(self.weapon)
        
        barrel = self.safe_load_model("models/box")
        barrel.setScale(0.06, 0.8, 0.06)
        barrel.setPos(0, 1.2, -0.1)
        barrel.setColor(0.2, 0.2, 0.2)
        barrel.reparentTo(rifle)
        
        body = self.safe_load_model("models/box")
        body.setScale(0.1, 0.4, 0.12)
        body.setPos(0, 0.8, -0.1)
        body.setColor(0.25, 0.25, 0.25)
        body.reparentTo(rifle)
        
        stock = self.safe_load_model("models/box")
        stock.setScale(0.08, 0.3, 0.15)
        stock.setPos(0, 0.4, -0.15)
        stock.setColor(0.3, 0.3, 0.3)
        stock.reparentTo(rifle)
        
        grip = self.safe_load_model("models/box")
        grip.setScale(0.08, 0.1, 0.2)
        grip.setPos(0, 0.7, -0.3)
        grip.setColor(0.3, 0.3, 0.3)
        grip.reparentTo(rifle)
        
        self.weapon_models["rifle"] = rifle
        
        sniper = NodePath("sniper")
        sniper.reparentTo(self.weapon)
        
        barrel = self.safe_load_model("models/box")
        barrel.setScale(0.05, 1.0, 0.05)
        barrel.setPos(0, 1.5, -0.1)
        barrel.setColor(0.2, 0.2, 0.2)
        barrel.reparentTo(sniper)
        
        body = self.safe_load_model("models/box")
        body.setScale(0.1, 0.5, 0.15)
        body.setPos(0, 1.0, -0.1)
        body.setColor(0.25, 0.25, 0.25)
        body.reparentTo(sniper)
        
        stock = self.safe_load_model("models/box")
        stock.setScale(0.08, 0.4, 0.15)
        stock.setPos(0, 0.6, -0.15)
        stock.setColor(0.3, 0.3, 0.3)
        stock.reparentTo(sniper)
        
        grip = self.safe_load_model("models/box")
        grip.setScale(0.08, 0.1, 0.2)
        grip.setPos(0, 0.9, -0.3)
        grip.setColor(0.3, 0.3, 0.3)
        grip.reparentTo(sniper)
        
        self.weapon_models["sniper"] = sniper
        
        dual_revolvers = NodePath("dual_revolvers")
        dual_revolvers.reparentTo(self.weapon)
        
        left_revolver = NodePath("left_revolver")
        left_revolver.reparentTo(dual_revolvers)
        left_revolver.setPos(-2.0, 0.6, -0.2)
        
        right_revolver = NodePath("right_revolver")
        right_revolver.reparentTo(dual_revolvers)
        right_revolver.setPos(0.4, 0.6, -0.2)
        
        for revolver in [left_revolver, right_revolver]:
            barrel = self.safe_load_model("models/box")
            barrel.setScale(0.06, 0.3, 0.06)
            barrel.setPos(0, 0.8, 0)
            barrel.setColor(0.2, 0.2, 0.2)
            barrel.reparentTo(revolver)
            
            cylinder = self.safe_load_model("models/box")
            cylinder.setScale(0.1, 0.15, 0.1)
            cylinder.setPos(0, 0.6, 0)
            cylinder.setColor(0.3, 0.3, 0.3)
            cylinder.reparentTo(revolver)
            
            grip = self.safe_load_model("models/box")
            grip.setScale(0.08, 0.1, 0.2)
            grip.setPos(0, 0.5, -0.15)
            grip.setColor(0.4, 0.2, 0.1)
            grip.reparentTo(revolver)
        
        self.weapon_models["dual_revolvers"] = dual_revolvers
        
        for weapon_name, model in self.weapon_models.items():
            if weapon_name == self.current_weapon:
                model.show()
            else:
                model.hide()
        
        self.update_weapon_position()
        
        self.original_weapon_pos = self.weapon.getPos()
        self.original_weapon_hpr = self.weapon.getHpr()

    def setup_weapon_render_layer(self):
        return

    def cleanup_weapon_render_layer(self):
        return

    def sync_weapon_camera(self):
        return

    def update_weapon_position(self):
        """Обновляет позицию оружия на основе настроек"""
        if not hasattr(self, 'weapon') or self.weapon.isEmpty():
            return
            
        if 'weapon_position' not in self.settings:
            self.settings['weapon_position'] = self.DEFAULT_SETTINGS['weapon_position'].copy()
            
        x = self.settings['weapon_position'].get('x', self.DEFAULT_SETTINGS['weapon_position']['x'])
        y = self.settings['weapon_position'].get('y', self.DEFAULT_SETTINGS['weapon_position']['y'])
        z = self.settings['weapon_position'].get('z', self.DEFAULT_SETTINGS['weapon_position']['z'])
        
        self.weapon.setPos(x, y, z)
        self.original_weapon_pos = self.weapon.getPos()
        self.original_weapon_hpr = self.weapon.getHpr()
        
        self.save_settings()
        
    def animate_weapon_recoil(self):
        if self.current_weapon == "dual_revolvers":
            return
            
        if not self.original_weapon_pos:
            self.original_weapon_pos = self.weapon.getPos()
            self.original_weapon_hpr = self.weapon.getHpr()
        
        start_pos = self.weapon.getPos()
        start_hpr = self.weapon.getHpr()
        
        recoil_pos = Point3(
            start_pos.getX(),
            start_pos.getY() - 0.08,
            start_pos.getZ() + 0.03
        )
        
        recoil_hpr = Vec3(
            start_hpr.getX(),
            start_hpr.getY() + 3,
            start_hpr.getZ() + random.uniform(-1, 1)
        )
        
        recoil_sequence = Sequence(
            Parallel(
                self.weapon.posInterval(
                    0.04,
                    recoil_pos,
                    start_pos,
                    blendType='easeOut'
                ),
                self.weapon.hprInterval(
                    0.04,
                    recoil_hpr,
                    start_hpr,
                    blendType='easeOut'
                )
            ),
            Parallel(
                self.weapon.posInterval(
                    0.08,
                    self.original_weapon_pos,
                    recoil_pos,
                    blendType='easeIn'
                ),
                self.weapon.hprInterval(
                    0.08,
                    self.original_weapon_hpr,
                    recoil_hpr,
                    blendType='easeIn'
                )
            )
        )
        
        recoil_sequence.start()

    def updateKeyMap(self, key, value):
        if self.is_chat_active or self.is_shader_debug_open:
            self.keyMap[key] = False
            return
        self.keyMap[key] = value

    def start_jump(self):
        """Начинает прыжок и обновляет комбо прыжков"""
        if self.is_splash_screen_active:  # Check if splash screen is active
            return  # Ignore all actions during splash screen
        if self.is_chat_active:
            return

        if not self.is_jumping:
            # Увеличиваем множитель комбо при последовательных прыжках только если распрыжка включена
            current_time = time.time()
            
            if self.settings.get('bhop_enabled', True):  # Проверяем, включена ли распрыжка
                if current_time - self.last_jump_time < self.jump_combo_time:
                    self.current_combo_jumps += 1
                    for stage in self.combo_stages:
                        if stage['jumps'] == self.current_combo_jumps:
                            self.jump_combo_multiplier = stage['multiplier']
                            break
                else:
                    self.current_combo_jumps = 1
                    self.jump_combo_multiplier = 1.0
            else:
                self.jump_combo_multiplier = 1.0
                self.current_combo_jumps = 0
            
            self.vertical_velocity = self.jump_power
            
            move_vec = Vec3(0, 0, 0)
            if self.keyMap["w"]: move_vec.setY(move_vec.getY() + 1)
            if self.keyMap["s"]: move_vec.setY(move_vec.getY() - 1)
            if self.keyMap["a"]: move_vec.setX(move_vec.getX() - 1)
            if self.keyMap["d"]: move_vec.setX(move_vec.getX() + 1)
            
            if move_vec.length() > 0:
                move_vec.normalize()
                base_speed = self.sprint_speed if self.keyMap["shift"] else self.move_speed
                self.horizontal_velocity = move_vec * base_speed * self.jump_combo_multiplier
            else:
                self.horizontal_velocity = Vec3(0, 0, 0)
            
            self.is_jumping = True
            self.last_jump_time = current_time
            
            if self.combo_task:
                taskMgr.remove(self.combo_task)
            self.combo_task = taskMgr.doMethodLater(self.jump_combo_time, self.reset_jump_combo, 'reset_jump_combo')

    def reset_jump_combo(self, task):
        """Сбрасывает комбо прыжков и скорости"""
        self.jump_combo_multiplier = 1.0
        self.current_combo_jumps = 0
        self.horizontal_velocity = Vec3(0, 0, 0)
        return task.done

    def reset_shoot(self, task):
        self.can_shoot = True
        return task.done

    def shoot(self):
        if self.is_splash_screen_active:  # Check if splash screen is active
            return  # Ignore all actions during splash screen
        if self.is_chat_active or self.is_shader_debug_open:
            return
        
        if not self.can_shoot:
            return
            
        self.can_shoot = False
        
        if self.current_weapon == "dual_revolvers":
            active_revolver = self.weapon_models["dual_revolvers"].find(f"{self.active_revolver}_revolver")
            
            self.shot_sound = self.loader.loadSfx(self.weapons[self.current_weapon]["sound"])
            self.shot_sound.play()
            
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
            else:  # right revolver
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
            self.shot_sound = self.loader.loadSfx(self.weapons[self.current_weapon]["sound"])
            self.shot_sound.play()
            
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
        
        if self.settings.get('spread_enabled', True):
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
                
            final_spread = min(final_spread, spread_params["max"])
            
            spread_x = random.uniform(-final_spread, final_spread)
            spread_y = random.uniform(-final_spread, final_spread)
            
            spread_mouse_pos = Point2(
                mouse_pos.getX() + spread_x,
                mouse_pos.getY() + spread_y
            )
        else:
            spread_mouse_pos = mouse_pos
        
        self.ray.setFromLens(self.camNode, spread_mouse_pos.getX(), spread_mouse_pos.getY())
        
        if self.settings.get('recoil_enabled', True):
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
        
        self.last_shot_time = globalClock.getFrameTime()
        self.shader_system.pulse_weapon()
        # Emit a short multiplayer "shooting" pulse so remote clients can render shot effects.
        self.shoot_state_frames = 2
        is_authoritative_mp = self.is_multiplayer and self.network and self.network.is_connected()

        self.cTrav.traverse(self.render)
        
        if self.current_weapon == "dual_revolvers":
            active_revolver = self.weapon_models["dual_revolvers"].find(f"{self.active_revolver}_revolver")
            if self.active_revolver == "left":
                weapon_pos = self.camera.getPos() + self.camera.getMat().xformVec(Point3(-2.0, 0.6, -0.2))
            else:
                weapon_pos = self.camera.getPos() + self.camera.getMat().xformVec(Point3(0.4, 0.6, -0.2))
        else:
            if self.current_weapon == "rifle":
                local_pos = Point3(0.2, 0.6, -0.2)
            elif self.current_weapon == "pistol":
                local_pos = Point3(0.15, 0.6, -0.2)
            elif self.current_weapon == "sniper":
                local_pos = Point3(0.25, 0.6, -0.2)
            else:
                local_pos = Point3(0, 0.6, -0.2)
            weapon_pos = self.camera.getPos() + self.camera.getMat().xformVec(local_pos)
        
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
        
        end_pos = weapon_pos + (spread_direction * max_distance)
        
        if self.settings.get('bullet_traces', True):
            if self.cQueue.getNumEntries() > 0:
                self.cQueue.sortEntries()
                entry = self.cQueue.getEntry(0)
                hit_pos = entry.getSurfacePoint(self.render)
                
                if self.current_weapon == "dual_revolvers":
                    if self.active_revolver == "left":
                        local_pos = Point3(-2.0, 0.6, -0.2)
                    else:
                        local_pos = Point3(0.4, 0.6, -0.2)
                else:
                    if self.current_weapon == "rifle":
                        local_pos = Point3(0.2, 0.6, -0.2)
                    elif self.current_weapon == "pistol":
                        local_pos = Point3(0.15, 0.6, -0.2)
                    elif self.current_weapon == "sniper":
                        local_pos = Point3(0.25, 0.6, -0.2)
                    else:
                        local_pos = Point3(0, 0.6, -0.2)
                
                start_pos = weapon_pos
                self.create_bullet_trace(start_pos, hit_pos)
                if not is_authoritative_mp:
                    self.handle_collision(entry)
            else:
                start_pos = weapon_pos
                self.create_bullet_trace(start_pos, end_pos)
        
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
        if self.is_chat_active:
            self.close_chat_input()
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
            self.score_text.hide()
        if hasattr(self, 'timer_text'):
            self.timer_text.hide()
        if hasattr(self, 'chat_entry'):
            self.chat_entry["focus"] = 0
            self.chat_entry.hide()
        if hasattr(self, 'chat_text'):
            self.chat_text.hide()
        if hasattr(self, 'scoreboard_text'):
            self.scoreboard_text.hide()
        self.is_chat_active = False
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
            print(f"✅ TargetPool создан с размером {pool_size}")
        
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(props)
        
        if self.target_pool:
            self.target_pool.release_all()
        self.targets.clear()
        
        self.setup_targets()
        self.setup_weapon()
        self.shader_system.rebind_scene_objects()
        
        self.taskMgr.add(self.update, "update")
        self.accept("mouse1", self.on_mouse_press)
        self.accept("mouse1-up", self.on_mouse_release)
        
        self.score = 0
        self.start_time = time.time()
        self.update_score_display()
        self.update_timer_display()
        
        if self.show_score:
            self.score_text.show()
        if self.show_timer:
            self.timer_text.show()
            self.taskMgr.add(self.update_timer_task, "timer_task")
        
        self.setup_audio()

    def update_score_display(self):
        self.score_text.setText(f"Score: {self.score}")
    
    def update_timer_display(self):
        minutes = int(self.game_time) // 60
        seconds = int(self.game_time) % 60
        self.timer_text.setText(f"Time: {minutes}:{seconds:02d}")
    
    def update_timer_task(self, task):
        if not self.show_timer:
            return task.done
        self.game_time = time.time() - self.start_time
        self.update_timer_display()
        return task.cont
    
    def handle_collision(self, entry):
        if self.is_multiplayer:
            return

        hit_node = entry.getIntoNode()
        if not hit_node.getName().startswith('target_'):
            return
            
        target_np = entry.getIntoNodePath().getParent()
        while target_np.getName() != "target_root":
            target_np = target_np.getParent()
            if target_np is None:
                return
        
        damage = self.get_damage_for_part(hit_node.getName())
        
        if damage <= 0:
            return
            
        self.activate_hit_effects()
        
        self.hit_sound.play()
        
        current_time = time.time()
        if current_time - self.last_hit_time < self.combo_window:
            self.combo_multiplier = min(2.0, self.combo_multiplier + 0.2)
        else:
            self.combo_multiplier = 1.0
        self.last_hit_time = current_time
        
        points = int(damage * self.combo_multiplier)
        
        self.score += points
        
        if hasattr(self, 'score_text') and self.show_score:
            self.score_text.setText(f"Score: {self.score}")
        
        hit_pos = entry.getSurfacePoint(self.render)
        
        # Показываем текст с очками
        if self.settings.get('damage_numbers', True):
            self.spawn_damage_text(f"+{points}", hit_pos)
        
        target_obj = None
        for active_target in self.targets:
            if hasattr(active_target, 'model') and active_target.model == target_np:
                target_obj = active_target
                break

        if target_obj:
            self.shader_system.mark_target_hit(target_obj)
            if target_obj in self.targets:
                self.targets.remove(target_obj)
            target_obj.destroy()
        elif not target_np.isEmpty():
            target_np.removeNode()
        
        delay = random.uniform(0.5, 2.0)
        self.taskMgr.doMethodLater(delay, self.spawn_target, f"spawn_target_{time.time_ns()}")
        
        if self.settings.get('killfeed', True):
            self.create_killfeed_message("Training Bot")

    def get_damage_for_part(self, part_name):
        """Возвращает урон в зависимости от части тела"""
        base_damage = self.weapons[self.current_weapon]["damage"]
        
        damage_multipliers = {
            "target_head": 2.0,
            "target_body": 1.0,
            "target_left_arm": 0.75,
            "target_right_arm": 0.75,
            "target_legs": 0.75
        }
        
        multiplier = damage_multipliers.get(part_name, 0)
        
        return int(base_damage * multiplier)

    def spawn_damage_text(self, text, pos):
        damage_text = TextNode('damage')
        damage_text.setText(text)
        damage_text.setAlign(TextNode.ACenter)
        
        text_node_path = self.aspect2d.attachNewNode(damage_text)
        
        offset_x = random.uniform(-0.15, 0.15)
        offset_y = random.uniform(-0.15, 0.15)
        
        text_node_path.setPos(offset_x, 0, offset_y)
        
        text_node_path.setScale(0.07)
        
        if int(text) >= 100:
            text_node_path.setColor(1, 0, 0, 1)
        elif int(text) >= 60:
            text_node_path.setColor(1, 0.5, 0, 1)
        else:
            text_node_path.setColor(1, 1, 1, 1)
        
        fade_interval = LerpColorScaleInterval(
            text_node_path,
            0.5,
            Vec4(1, 1, 1, 0),
            Vec4(1, 1, 1, 1)
        )
        
        pos_interval = text_node_path.posInterval(
            0.5,
            Point3(offset_x, 0, offset_y + 0.2),
            Point3(offset_x, 0, offset_y)
        )
        
        Parallel(fade_interval, pos_interval).start()
        
        self.taskMgr.doMethodLater(
            0.5,
            lambda task: text_node_path.removeNode(),
            'remove_damage_text'
        )

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
            if target_id:
                hit_target = self.mp_targets_by_id.get(target_id)
                if hit_target:
                    self.shader_system.mark_target_hit(hit_target)
            if shooter_id == local_player_id:
                if not result.get("hit"):
                    continue
                self.score = int(result.get("new_score", self.score))
                if hasattr(self, 'score_text') and self.show_score:
                    self.score_text.setText(f"Score: {self.score}")
                if hit_pos and self.settings.get('damage_numbers', True):
                    points = int(result.get("score_delta", 0))
                    self.spawn_damage_text(f"+{points}", Point3(hit_pos[0], hit_pos[1], hit_pos[2]))
                self.activate_hit_effects()
                self.hit_sound.play()
                continue

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
        """Создает новое сообщение в килфиде"""
        y_pos = 0.9 - len(self.killfeed_messages) * 0.06
        x_pos = 1.3 + self.killfeed_slide_distance
        
        message = OnscreenText(
            text=f"You killed {target_name}",
            fg=(0.3, 0.6, 1, 0),
            shadow=(0, 0, 0, 0),
            pos=(x_pos, y_pos),
            align=TextNode.ARight,
            scale=0.04
        )
        message.setBin('gui-popup', 0)

        frame_root = aspect2d.attachNewNode("frame_root")
        frame_root.setPos(x_pos, 0, y_pos)
        
        cm = CardMaker('killfeed_bg')
        cm.setFrame(-0.5, 0.05, -0.015, 0.025)
        bg = frame_root.attachNewNode(cm.generate())
        bg.setTransparency(TransparencyAttrib.MAlpha)
        bg.setColor(0, 0, 0, 0)
        bg.setBin('background', 10)
        
        border_thickness = 0.002
        borders = []
        
        cm_top = CardMaker('border_top')
        cm_top.setFrame(-0.5, 0.05, 0.025, 0.025 + border_thickness)
        border_top = frame_root.attachNewNode(cm_top.generate())
        border_top.setColor(1, 1, 1, 0)
        border_top.setTransparency(TransparencyAttrib.MAlpha)
        border_top.setBin('background', 11)
        borders.append(border_top)
        
        cm_bottom = CardMaker('border_bottom')
        cm_bottom.setFrame(-0.5, 0.05, -0.015 - border_thickness, -0.015)
        border_bottom = frame_root.attachNewNode(cm_bottom.generate())
        border_bottom.setColor(1, 1, 1, 0)
        border_bottom.setTransparency(TransparencyAttrib.MAlpha)
        border_bottom.setBin('background', 11)
        borders.append(border_bottom)
        
        cm_left = CardMaker('border_left')
        cm_left.setFrame(-0.5 - border_thickness, -0.5, -0.015, 0.025)
        border_left = frame_root.attachNewNode(cm_left.generate())
        border_left.setColor(1, 1, 1, 0)
        border_left.setTransparency(TransparencyAttrib.MAlpha)
        border_left.setBin('background', 11)
        borders.append(border_left)
        
        cm_right = CardMaker('border_right')
        cm_right.setFrame(0.05, 0.05 + border_thickness, -0.015, 0.025)
        border_right = frame_root.attachNewNode(cm_right.generate())
        border_right.setColor(1, 1, 1, 0)
        border_right.setTransparency(TransparencyAttrib.MAlpha)
        border_right.setBin('background', 11)
        borders.append(border_right)
        
        self.killfeed_messages.append({
            'message': message,
            'frame_root': frame_root,
            'background': bg,
            'borders': borders,
            'creation_time': globalClock.getFrameTime(),
            'y_pos': y_pos,
            'x_pos': x_pos,
            'alpha': 0,
            'target_alpha': 1,
            'x_offset': self.killfeed_slide_distance
        })
        
        if len(self.killfeed_messages) > 5:
            oldest = self.killfeed_messages[0]
            oldest['target_alpha'] = 0

    def update_killfeed_positions(self):
        """Обновляет позиции всех сообщений в килфиде"""
        current_time = globalClock.getFrameTime()
        messages_to_remove = []
        
        for i, msg_data in enumerate(self.killfeed_messages):
            age = current_time - msg_data['creation_time']
            
            if msg_data['alpha'] != msg_data['target_alpha']:
                alpha_change = globalClock.getDt() / self.killfeed_fade_time
                if msg_data['target_alpha'] > msg_data['alpha']:
                    msg_data['alpha'] = min(msg_data['target_alpha'], msg_data['alpha'] + alpha_change)
                else:
                    msg_data['alpha'] = max(msg_data['target_alpha'], msg_data['alpha'] - alpha_change)
                
                msg_data['message'].setFg((0.3, 0.6, 1, msg_data['alpha']))
                msg_data['message'].setShadow((0, 0, 0, msg_data['alpha']))
                msg_data['background'].setColor(0, 0, 0, msg_data['alpha'] * 0.3)
                for border in msg_data['borders']:
                    border.setColor(1, 1, 1, msg_data['alpha'] * 0.8)
            
            if msg_data['x_offset'] > 0:
                slide_speed = self.killfeed_slide_distance / self.killfeed_fade_time
                msg_data['x_offset'] = max(0, msg_data['x_offset'] - slide_speed * globalClock.getDt())
                new_x = 1.3 + msg_data['x_offset']
                
                msg_data['message'].setPos(new_x, msg_data['y_pos'])
                msg_data['frame_root'].setPos(new_x, 0, msg_data['y_pos'])
                msg_data['x_pos'] = new_x
            
            if age > 5.0 and msg_data['target_alpha'] == 1:
                msg_data['target_alpha'] = 0
            
            if msg_data['alpha'] <= 0 and msg_data['target_alpha'] == 0:
                messages_to_remove.append(msg_data)
            
            target_y = 0.9 - i * 0.06
            if msg_data['y_pos'] != target_y:
                msg_data['y_pos'] = target_y
                msg_data['message'].setPos(msg_data['x_pos'], target_y)
                msg_data['frame_root'].setPos(msg_data['x_pos'], 0, target_y)
        
        for msg_data in messages_to_remove:
            msg_data['message'].removeNode()
            msg_data['frame_root'].removeNode()
            self.killfeed_messages.remove(msg_data)

    def update(self, task):
        """Обновление состояния игры"""
        if self.is_splash_screen_active:
            return task.cont
        
        if self.pause_menu and self.pause_menu.is_paused:
            return task.cont
        
        dt = globalClock.getDt()
        
        self.fps = int(globalClock.getAverageFrameRate())
        
        if self.current_time_scale != self.target_time_scale:
            diff = self.target_time_scale - self.current_time_scale
            change = min(abs(diff), dt * self.time_scale_speed) * (1 if diff > 0 else -1)
            self.current_time_scale += change
        
        scaled_dt = dt * self.current_time_scale
        
        self.update_score_display()
        
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
        
        move_vec = Vec3(0, 0, 0)
        
        if self.keyMap["w"]: move_vec.addY(1)
        if self.keyMap["s"]: move_vec.addY(-1)
        if self.keyMap["a"]: move_vec.addX(-1)
        if self.keyMap["d"]: move_vec.addX(1)
            
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
            speed *= self.jump_combo_multiplier
            
        if move_vec.length() > 0:
            self.horizontal_velocity = move_vec * speed
        elif not self.is_jumping:
            self.horizontal_velocity = Vec3(0, 0, 0)
            
        if self.horizontal_velocity.length() > 0:
            self.camera.setPos(
                self.camera.getX() + self.horizontal_velocity.getX() * scaled_dt,
                self.camera.getY() + self.horizontal_velocity.getY() * scaled_dt,
                self.camera.getZ()
            )
        
        if self.is_jumping:
            self.vertical_velocity += self.gravity * scaled_dt
            new_z = self.camera.getZ() + self.vertical_velocity * scaled_dt
            
            if new_z <= self.camera_height:
                new_z = self.camera_height
                self.vertical_velocity = 0
                self.is_jumping = False
                self.jump_speed_boost = 1.0
                if move_vec.length() == 0:
                    self.horizontal_velocity = Vec3(0, 0, 0)
            
            self.camera.setZ(new_z)
            
        if self.mouseWatcherNode.hasMouse() and not self.is_chat_active and not self.is_shader_debug_open:
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
        
        current_speed = math.sqrt(self.horizontal_velocity.getX()**2 + self.horizontal_velocity.getY()**2)
        self.speed_text.setText(f"Speed: {current_speed:.1f}")
        
        if self.mouse_pressed and self.current_weapon == "rifle":
            current_time = time.time()
            if current_time - self.last_shot_time >= self.weapons[self.current_weapon]["cooldown"]:
                self.shoot()
        
        self.update_killfeed_positions()
        self.refresh_chat_display()
        
        self.update_aim(task)
        self.shader_system.update(dt)
        
        if self.is_multiplayer and self.network and self.network.is_connected():
            snapshot = self.network.consume_latest_targets_snapshot()
            if snapshot:
                self.apply_targets_state(snapshot)
            self.process_network_shot_results()
            for chat in self.network.consume_chat_messages():
                self.add_chat_line(chat.get("name", "Player"), chat.get("text", ""))

            server_score = self.network.get_local_server_score()
            if server_score != self.score:
                self.score = server_score
                self.update_score_display()

            if self.show_scoreboard:
                scoreboard = self.network.get_scoreboard()
                lines = ["Players"]
                for idx, p in enumerate(scoreboard, 1):
                    pname = p.get("name", "Player")
                    pscore = int(p.get("score", 0))
                    lines.append(f"{idx}. {pname}: {pscore}")
                self.scoreboard_text.setText("\n".join(lines))

            self.is_shooting = self.shoot_state_frames > 0
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
        
        return task.cont

    def update_aim(self, task):
        """Обновление анимации прицеливания"""
        if self.is_aiming and self.aim_transition < 1.0:
            self.aim_transition = min(1.0, self.aim_transition + 0.1)
        elif not self.is_aiming and self.aim_transition > 0.0:
            self.aim_transition = max(0.0, self.aim_transition - 0.1)
            
        default_pos = self.default_weapon_pos[self.current_weapon]["pos"]
        ads_pos = self.ads_weapon_pos[self.current_weapon]["pos"]
        current_pos = default_pos + (ads_pos - default_pos) * self.aim_transition
        
        self.weapon_models[self.current_weapon].setPos(current_pos)
        
        default_fov = self.settings["fov"]
        target_fov = default_fov + (self.ads_fov[self.current_weapon] - default_fov) * self.aim_transition
        base.camLens.setFov(target_fov)
        
        base_sensitivity = self.settings["sensitivity"]
        
        if self.is_aiming:
            sensitivity = base_sensitivity * self.ads_sensitivity_multiplier
        else:
            sensitivity = base_sensitivity
        
        self.mouse_sensitivity = sensitivity
        
        return task.cont

    def start_aiming(self):
        """Начало прицеливания"""
        self.is_aiming = True
        
    def stop_aiming(self):
        """Конец прицеливания"""
        self.is_aiming = False

    def switch_weapon(self, weapon_name):
        if self.is_splash_screen_active:
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
            self.shader_system.rebind_scene_objects()
            
            self.shoot_cooldown = self.weapons[weapon_name]["cooldown"]
            self.last_shot_time = 0
            
            self.play_weapon_draw_animation()

    def play_weapon_draw_animation(self):
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
        self.accept('weaponDrawComplete', finish_animation)
        
        self.weapon_animation.start()

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

    def setup_audio(self):
        """Настраивает и запускает фоновую музыку"""
        audio_settings = self.settings.get('audio', self.DEFAULT_SETTINGS['audio'])
        
        if audio_settings['music_enabled']:
            self.play_music(audio_settings['current_track'], audio_settings['music_volume'])

    def play_music(self, track_name, volume=0.5):
        """Воспроизводит фоновую музыку с указанным объемом"""
        if self.is_splash_screen_active:
            return
        
        if self.music:
            self.music.stop()
        
        music_path = f"music/{track_name}"
        
        try:
            self.music = loader.loadSfx(music_path)
            if self.music:
                self.music.setLoop(True)
                self.music.setVolume(volume)
                self.music.play()
                self.current_music_path = music_path
        except Exception as e:
            print(f"Ошибка загрузки музыки: {e}")

    def update_music_volume(self, volume):
        """Обновляет объем текущей воспроизводимой музыки"""
        if self.music:
            self.music.setVolume(volume)
            
        if 'audio' not in self.settings:
            self.settings['audio'] = self.DEFAULT_SETTINGS['audio'].copy()
        self.settings['audio']['music_volume'] = volume
        self.save_settings()

    def change_music_track(self, track_name):
        """???????? ??????? ???? ??????"""
        if 'audio' not in self.settings:
            self.settings['audio'] = self.DEFAULT_SETTINGS['audio'].copy()
            
        self.settings['audio']['current_track'] = track_name
        self.save_settings()
        
        if self.settings['audio']['music_enabled']:
            self.play_music(track_name, self.settings['audio']['music_volume'])

    def toggle_music(self, enabled):
        """Включает/выключает фоновую музыку"""
        if 'audio' not in self.settings:
            self.settings['audio'] = self.DEFAULT_SETTINGS['audio'].copy()
            
        self.settings['audio']['music_enabled'] = enabled
        self.save_settings()
        
        if enabled:
            self.play_music(self.settings['audio']['current_track'], self.settings['audio']['music_volume'])
        elif self.music:
            self.music.stop()

    def add_chat_line(self, name: str, text: str):
        clean_name = (name or "Player").strip()[:24]
        clean_text = (text or "").strip()[:180]
        if not clean_text:
            return
        self.chat_messages.append({
            "t": time.time(),
            "line": f"{clean_name}: {clean_text}",
        })
        if len(self.chat_messages) > 30:
            self.chat_messages = self.chat_messages[-30:]
        self.refresh_chat_display()

    def refresh_chat_display(self):
        now = time.time()
        if self.is_chat_active:
            visible = self.chat_messages[-8:]
        else:
            self.chat_messages = [
                m for m in self.chat_messages
                if now - float(m.get("t", now)) <= self.chat_message_lifetime
            ]
            visible = self.chat_messages[-6:]

        if not visible:
            self.chat_text.setText("")
            self.chat_text.hide()
            return

        lines = [m.get("line", "") for m in reversed(visible)]
        self.chat_text.setText("\n".join(lines))
        self.chat_text.show()

    def toggle_chat_input(self):
        now = time.time()
        if now - self.chat_last_toggle_time < 0.2:
            return
        self.chat_last_toggle_time = now

        if self.is_splash_screen_active:
            return
        if not (self.is_multiplayer and self.network and self.network.is_connected()):
            return

        if not self.is_chat_active:
            self.is_chat_active = True
            self.chat_entry.enterText("")
            self.chat_entry.show()
            self.chat_entry["focus"] = 1
            self.mouse_pressed = False
            for key in self.keyMap:
                self.keyMap[key] = False
            self.refresh_chat_display()
        else:
            self.close_chat_input()

    def submit_chat_message(self, text):
        if self.network and self.network.is_connected():
            msg = (text or "").strip()
            if msg:
                self.network.send_chat(msg)
        self.chat_entry.enterText("")
        self.close_chat_input()

    def close_chat_input(self):
        self.chat_entry["focus"] = 0
        self.chat_entry.hide()
        self.is_chat_active = False
        self.chat_last_toggle_time = time.time()
        self.refresh_chat_display()

    def on_tab_down(self):
        if self.is_splash_screen_active:
            return
        if not (self.is_multiplayer and self.network and self.network.is_connected()):
            return
        self.show_scoreboard = True
        self.scoreboard_text.show()

    def on_tab_up(self):
        self.show_scoreboard = False
        self.scoreboard_text.hide()

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
        if self.is_chat_active or self.is_shader_debug_open:
            return
        
        self.mouse_pressed = True
        self.shoot()

    def on_mouse_release(self):
        """Обработчик отпускания кнопки мыши"""
        if self.is_splash_screen_active:
            return
        
        self.mouse_pressed = False

    def create_shell_casing(self):
        """Создает анимацию выброса гильзы"""
        if self.is_splash_screen_active:  
            return 
        
        current_weapon_model = self.weapon_models[self.current_weapon]
        
        shell = self.shell_model.copyTo(render)
        
        if self.current_weapon == "pistol":
            eject_offset = Vec3(0.1, 0.9, -0.1)
        elif self.current_weapon == "rifle":
            eject_offset = Vec3(0.1, 0.9, -0.05)
        else:  # sniper
            eject_offset = Vec3(0.1, 1.1, -0.05)

        shell_parent = render.attachNewNode("shell_parent")
        shell_parent.setPos(current_weapon_model.getPos(render))
        shell_parent.setHpr(current_weapon_model.getHpr(render))
        
        shell.reparentTo(shell_parent)
        shell.setPos(eject_offset)
        
        shell.wrtReparentTo(render)
        
        weapon_quat = current_weapon_model.getQuat(render)
        right = weapon_quat.getRight()
        up = weapon_quat.getUp()
        forward = weapon_quat.getForward()
        
        ejection_speed = 3.0
        vertical_speed = 1.0
        
        initial_velocity = Vec3()
        initial_velocity += right * ejection_speed
        initial_velocity += up * vertical_speed
        
        initial_velocity += Vec3(
            random.uniform(-0.2, 0.2),
            random.uniform(-0.2, 0.2),
            random.uniform(0, 0.5)
        )
        
        angular_velocity = Vec3(
            random.uniform(-720, 720),
            random.uniform(-720, 720),
            random.uniform(-720, 720)
        )
        
        shell_data = {
            'model': shell,
            'velocity': initial_velocity,
            'angular_velocity': angular_velocity,
            'time': 0
        }
        self.active_shells.append(shell_data)
        
        taskMgr.doMethodLater(2.0, self.remove_shell, 'remove_shell', 
                            extraArgs=[shell_data], appendTask=True)

    def update_shells(self, task):
        """Обновляет физику гильз"""
        if self.is_splash_screen_active:
            return task.cont
        
        dt = globalClock.getDt()
        gravity = Vec3(0, 0, -9.8)
        
        for shell in self.active_shells:
            shell['time'] += dt
            
            current_pos = shell['model'].getPos()
            shell['velocity'] += gravity * dt
            new_pos = current_pos + shell['velocity'] * dt
            shell['model'].setPos(new_pos)
            
            current_hpr = shell['model'].getHpr()
            rotation = shell['angular_velocity'] * dt
            new_hpr = current_hpr + rotation
            shell['model'].setHpr(new_hpr)
            
            if new_pos.getZ() < 0:
                new_pos.setZ(0)
                shell['velocity'] = Vec3(0, 0, 0)
                shell['angular_velocity'] = Vec3(0, 0, 0)
                shell['model'].setPos(new_pos)
        
        return task.cont

    def remove_shell(self, shell_data, task):
        """Удаляет гильзу"""
        if shell_data in self.active_shells:
            self.active_shells.remove(shell_data)
            shell_data['model'].removeNode()
        return task.done

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
            
        self.save_settings()

    def validate_settings(self, settings):
        """Валидация и нормализация настроек"""
        if 'fov' in settings:
            settings['fov'] = max(60, min(120, settings['fov']))
        
        if 'resolution' in settings:
            try:
                width, height = map(int, settings['resolution'].split('x'))
                if width < 640 or height < 480:
                    settings['resolution'] = '1280x720'
            except:
                settings['resolution'] = '1280x720'
        
        for key in [
            'bloom_enabled', 'bloom_intensity',
            'blur_enabled', 'blur_amount',
            'cartoon_enabled', 'inverted_enabled',
            'ao_enabled',
            'motion_blur_enabled', 'motion_blur_amount',
        ]:
            settings.pop(key, None)

        bool_keys = ['show_target_images', 'bhop_enabled', 'fullscreen', 'show_score', 
                     'show_timer', 'damage_numbers', 'killfeed', 'show_fps', 
                     'recoil_enabled', 'screen_shake_enabled', 'spread_enabled']
        
        for key in bool_keys:
            if key in settings:
                if isinstance(settings[key], int):
                    settings[key] = bool(settings[key])
        
        if 'sensitivity' in settings:
            settings['sensitivity'] = max(1.0, settings['sensitivity'])
        
        if 'target_count' in settings:
            settings['target_count'] = max(1, min(50, settings['target_count']))
        
        return settings
    
    def _get_settings_path(self):
        """Возвращает путь к settings.json (работает с PyInstaller)"""
        if hasattr(sys, 'frozen'):
            # В PyInstaller - сохраняем рядом с exe
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            return os.path.join(exe_dir, 'settings.json')
        else:
            # В обычном режиме - в корне проекта
            return 'settings.json'
    
    def load_settings(self):
        settings_path = self._get_settings_path()
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                loaded = self.validate_settings(loaded)
                return loaded
        except Exception as e:
            print(f"⚠️ Ошибка загрузки настроек: {e}")
            return self.DEFAULT_SETTINGS.copy()

    def save_settings(self):
        """Сохраняет текущие настройки в файл"""
        self.settings['sensitivity'] = self.mouse_sensitivity
        for key in [
            'bloom_enabled', 'bloom_intensity',
            'blur_enabled', 'blur_amount',
            'cartoon_enabled', 'inverted_enabled',
            'ao_enabled',
            'motion_blur_enabled', 'motion_blur_amount',
        ]:
            self.settings.pop(key, None)
        
        settings_path = self._get_settings_path()
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def show_main_menu(self):
        """Вызывается экраном загрузки при завершении его работы"""
        if self.menu is None:
            print("⚠️ Меню не было создано в splash screen, создаем сейчас...")
            self.menu = MainMenu(self)
        print("✅ Показываем главное меню")
        self.menu.show()
    
    # ==================== РњРЈР›Р¬РўРРџР›Р•Р•Р  ====================
    
    def show_multiplayer_menu(self):
        """Показывает меню мультиплеера"""
        if self.menu:
            self.menu.hide()
        
        if self.lobby_menu is None:
            self.lobby_menu = LobbyMenu(self)
            self.lobby_menu.set_connect_callback(self.connect_to_server)
            self.lobby_menu.set_back_callback(self.back_from_multiplayer)
        
        self.lobby_menu.show()
    
    def connect_to_server(self, server_ip: str, port: int, player_name: str):
        """Подключается к серверу мультиплеера"""
        if self.network is None:
            self.network = NetworkClient(self)
        
        success = self.network.connect(server_ip, port, player_name)
        
        if success:
            self.lobby_menu.set_connection_status(True, "Connected!")
        else:
            self.lobby_menu.set_connection_status(False, "Connection failed")
    
    def back_from_multiplayer(self):
        """Возвращается из мультиплеера в главное меню"""
        self.cleanup_multiplayer()
        
        if self.menu:
            self.menu.show()
    
    def start_multiplayer_game(self):
        """Запускает мультиплеерную игру"""
        if not self.network or not self.network.is_connected():
            print("⚠️ Не подключен к серверу!")
            return
        
        self.is_multiplayer = True
        
        if self.lobby_menu:
            self.lobby_menu.hide()
        
        self.start_game()
    
    def update_remote_players(self, dt: float):
        """Обновляет модели других игроков"""
        if not self.network:
            return
        
        remote_players_data = self.network.get_remote_players()
        
        for player_id in list(self.remote_players.keys()):
            if player_id not in remote_players_data:
                self.remote_players[player_id].destroy()
                del self.remote_players[player_id]
        
        for player_id, player_data in remote_players_data.items():
            if player_id not in self.remote_players:
                player_name = player_data.get("name", "Unknown")
                model = RemotePlayerModel(self, player_id, player_name)
                self.remote_players[player_id] = model
            
            self.remote_players[player_id].update(player_data, dt)
    
    def cleanup_multiplayer(self):
        """Очищает ресурсы мультиплеера"""
        if self.network:
            try:
                self.network.disconnect()
            except Exception:
                pass
            self.network = None
        
        # Удаляем модели других игроков
        for player_model in list(self.remote_players.values()):
            try:
                player_model.destroy()
            except Exception:
                pass
        self.remote_players.clear()
        
        for target_id in list(self.mp_targets_by_id.keys()):
            target_obj = self.mp_targets_by_id.pop(target_id)
            try:
                if target_obj in self.targets:
                    self.targets.remove(target_obj)
                target_obj.network_id = None
                target_obj.destroy()
            except Exception:
                pass
        self.mp_targets_revision = -1
        self.is_chat_active = False
        self.show_scoreboard = False
        self.chat_messages.clear()
        if hasattr(self, 'chat_entry'):
            self.chat_entry["focus"] = 0
            self.chat_entry.hide()
        if hasattr(self, 'chat_text'):
            self.chat_text.setText("")
            self.chat_text.hide()
        if hasattr(self, 'scoreboard_text'):
            self.scoreboard_text.hide()
        
        self.is_multiplayer = False

        
if __name__ == "__main__":
    game = Game()
    game.run()


