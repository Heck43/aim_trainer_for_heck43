from direct.showbase.ShowBase import ShowBase
from panda3d.core import Point3, Vec3, Vec4, Vec2, WindowProperties, MouseWatcher, NodePath
from panda3d.core import CollisionTraverser, CollisionNode, CollisionHandlerQueue
from panda3d.core import CollisionRay, CollisionSphere, CollisionBox, BitMask32
from panda3d.core import TextNode, TextureStage, Texture, TransparencyAttrib
from panda3d.core import AmbientLight, DirectionalLight, LineSegs, ClockObject
from panda3d.core import CardMaker
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame
from direct.task import Task
from direct.interval.LerpInterval import LerpPosInterval
from direct.interval.IntervalGlobal import Sequence, LerpColorScaleInterval, Parallel, LerpColorInterval, Func
from direct.filter.CommonFilters import CommonFilters
from menu import MainMenu
from target import Target
import random
import math
import time
import json
import os
from direct.actor.Actor import Actor
from math import sin, cos, pi, radians as deg2Rad
import sys

class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Инициализация FPS
        self.fps = 0
        
        # Настройки по умолчанию
        self.DEFAULT_SETTINGS = {
            'sensitivity': 25.0,
            'fov': 70,
            'resolution': '1280x720',
            'show_score': True,
            'show_timer': True,
            'volume': 100,
            'show_target_images': True,  # Новая настройка для отображения картинок
            'damage_numbers': True,
            'killfeed': True,
            'show_fps': True,
            'recoil_enabled': True,  # Включение/выключение отдачи
            'weapon_position': {
                'x': 0.3,  # Правее от центра
                'y': 0.8,  # Вперед от камеры
                'z': -0.4  # Ниже центра
            },
            # Игровые настройки
            'bhop_enabled': True,  # Включение/выключение распрыжки
            'audio': {
                'music_enabled': True,
                'music_volume': 0.5,
                'current_track': 'default_track.mp3'
            },
            'target_count': 10  # Добавляем настройку количества манекенов
        }
        
        # Загружаем настройки
        self.settings = self.load_settings()
        
        # Применяем начальные настройки
        self.mouse_sensitivity = self.settings.get('sensitivity', self.DEFAULT_SETTINGS['sensitivity'])
        self.show_score = self.settings.get('show_score', self.DEFAULT_SETTINGS['show_score'])
        self.show_timer = self.settings.get('show_timer', self.DEFAULT_SETTINGS['show_timer'])
        
        # Устанавливаем начальное разрешение
        resolution = self.settings.get('resolution', self.DEFAULT_SETTINGS['resolution'])
        width, height = map(int, resolution.split('x'))
        props = WindowProperties()
        props.setSize(width, height)
        self.win.requestProperties(props)
        
        # Игровая статистика
        self.score = 0
        self.combo_multiplier = 1.0  # Множитель комбо
        self.last_hit_time = 0  # Время последнего попадания
        self.combo_window = 2.0  # Окно времени для комбо (в секундах)
        self.start_time = 0
        self.game_time = 0
        
        # UI элементы
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
            pos=(-0.0, -0.9),  # Центр внизу экрана
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            scale=0.07,
            shadow=(0, 0, 0, 1)
        )
        self.timer_text.hide()
        
        # Отключаем стандартное управление мышью
        self.disableMouse()

        # Инициализация коллизий
        self.cTrav = CollisionTraverser()
        self.cQueue = CollisionHandlerQueue()
        
        # Настройки окна
        properties = WindowProperties()
        properties.setTitle("Aim Trainer")
        properties.setCursorHidden(True)
        properties.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(properties)
        
        # Настраиваем FOV (поле зрения)
        self.camLens.setFov(self.settings['fov'])  # Увеличиваем FOV до значения из настроек
        
        # Базовые настройки
        self.move_speed = 10.0
        self.sprint_speed = 15.0
        self.jump_power = 15.0
        self.gravity = -50.0
        self.vertical_velocity = 0.0
        self.horizontal_velocity = Vec3(0, 0, 0)  # Горизонтальная скорость для прыжков
        self.is_jumping = False
        self.ground_height = 0
        self.is_sprinting = False  # Флаг для бега
        self.jump_speed_boost = 1.0  # Множитель скорости при прыжке
        
        # Параметры системы ускорения прыжков
        self.jump_combo_time = 1.0  # Время в секундах для комбо прыжков
        self.jump_combo_multiplier = 1.0  # Текущий множитель скорости
        self.max_combo_multiplier = 5.0  # Максимальный множитель
        self.combo_stages = [  # Стадии комбо
            {'jumps': 1, 'multiplier': 1.0},
            {'jumps': 2, 'multiplier': 1.4},
            {'jumps': 3, 'multiplier': 1.8},
            {'jumps': 4, 'multiplier': 2.2},
            {'jumps': 5, 'multiplier': 2.6},
            {'jumps': 6, 'multiplier': 3.0},
            {'jumps': 7, 'multiplier': 3.2}
        ]
        self.current_combo_jumps = 0  # Счетчик прыжков в текущем комбо
        self.last_jump_time = 0
        self.combo_task = None
        
        # Параметры стрельбы
        self.can_shoot = True
        self.current_weapon = "rifle"  # По умолчанию используем винтовку
        
        # Параметры оружий
        self.weapons = {
            "pistol": {
                "cooldown": 0.2,  # Задержка между выстрелами
                "damage": 25,
                "recoil": {
                    "pitch": (0.5, 1.0),  # Мин и макс вертикальной отдачи
                    "yaw": (-0.3, 0.3),   # Мин и макс горизонтальной отдачи
                }
            },
            "rifle": {
                "cooldown": 0.1,  # Быстрее стреляет
                "damage": 20,     # Меньше урон
                "recoil": {
                    "pitch": (0.3, 0.6),  # Меньше вертикальная отдача
                    "yaw": (-0.2, 0.2),   # Меньше разброс
                }
            }
        }
        
        self.shoot_cooldown = self.weapons[self.current_weapon]["cooldown"]
        self.recoil_time = 0.05
        self.is_shooting = False
        self.shoot_time = 0
        self.original_weapon_pos = None
        self.original_weapon_hpr = None
        
        # Параметры отдачи
        self.recoil_pitch = 0  # Текущий подъем камеры от отдачи
        self.recoil_yaw = 0    # Текущее боковое отклонение
        self.max_recoil_pitch = 2.0  # Максимальный подъем камеры
        self.max_recoil_yaw = 1.0   # Максимальное боковое отклонение
        self.recoil_recovery_speed = 5.0  # Скорость возврата камеры
        self.recoil_recovery_delay = 0.1  # Задержка перед началом восстановления
        self.last_shot_time = 0
        
        # Настройка камеры
        self.camera_height = 1.8
        self.camera.setPos(0, 0, self.camera_height)
        self.camera_pitch = 0
        self.camera_heading = 0
        
        # Создаем пол
        self.ground = self.loader.loadModel("models/box")
        self.ground.setScale(100, 100, 1)
        self.ground.setPos(0, 0, -1)
        self.ground.setColor(0.2, 0.2, 0.2)
        self.ground.reparentTo(self.render)

        # Создаем цель
        self.targets = []
        
        # Создаем прицел
        self.crosshair = OnscreenText(
            text="+",
            style=1,
            fg=(1, 1, 1, 1),
            pos=(0, 0),
            scale=.05)

        # Загрузка звуков
        self.shot_sound = self.loader.loadSfx("sounds/shot.wav")
        self.hit_sound = self.loader.loadSfx("sounds/hit.wav")
        # Настройка громкости
        self.shot_sound.setVolume(0.5)
        self.hit_sound.setVolume(0.7)
        
        # Настройка информационных текстов
        self.fps_text = self.create_text(-1.3, 0.95)
        self.pos_text = self.create_text(-1.3, 0.85)
        self.speed_text = self.create_text(-1.3, 0.75)
        
        # Список для хранения всех визуальных эффектов
        self.shot_effects = []  # Каждый элемент это кортеж (line_node, marker_node, task)
        
        # Список для хранения текста урона
        self.damage_texts = []  # Каждый элемент это кортеж (text_node, start_time, start_pos)
        
        # Список для хранения 2D маркеров попадания
        self.hit_markers = []  # Каждый элемент это NodePath
        
        # Инициализация килфида
        self.killfeed_messages = []
        self.killfeed_fade_time = 0.3  # Время для fade in/out анимации
        self.killfeed_slide_distance = 0.2  # Расстояние для slide анимации
        self.killfeed_duration = 5  # Длительность показа сообщения в секундах
        
        # Настройка управления
        self.accept("escape", self.return_to_menu)
        self.accept("space", self.start_jump)
        self.accept("1", self.switch_weapon, ["rifle"])    # Клавиша 1 для винтовки
        self.accept("2", self.switch_weapon, ["pistol"])   # Клавиша 2 для пистолета
        
        # Инициализируем keyMap
        self.keyMap = {
            "w": False,
            "s": False,
            "a": False,
            "d": False,
            "shift": False  # Добавляем клавишу Shift для бега
        }
        
        # Настройка клавиш
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
        
        # Добавляем задачи
        self.previous_time = 0
        self.frame_count = 0
        self.fps_update_time = 0
        
        # Добавляем задачу обновления текста урона
        self.taskMgr.add(self.update_damage_texts, "update_damage_texts")
        
        # Set up collision traverser and handler
        self.cTrav = CollisionTraverser('Main traverser')
        self.cQueue = CollisionHandlerQueue()
        
        # Create the collision ray
        self.ray = CollisionRay()
        rayNode = CollisionNode('mouseRay')
        rayNode.addSolid(self.ray)
        rayNode.setFromCollideMask(BitMask32.bit(1))
        rayNode.setIntoCollideMask(BitMask32.allOff())
        self.rayNodePath = self.camera.attachNewNode(rayNode)
        self.cTrav.addCollider(self.rayNodePath, self.cQueue)
        
        # Настройка выхода из игры
        self.accept("window-event", self.cleanup)
        
        # Создаем главное меню
        self.main_menu = MainMenu(self)
        self.main_menu.show()
        
        # Параметры эффектов при попадании
        self.current_time_scale = 1.0   # Текущий масштаб времени
        self.target_time_scale = 1.0    # Целевой масштаб времени
        self.normal_time_scale = 1.0    # Нормальная скорость времени
        self.slow_motion_scale = 0.3    # Скорость в замедленном режиме
        self.time_scale_speed = 6.0     # Скорость перехода между нормальным и замедленным временем
        self.slow_motion_duration = 0.15 # Длительность замедления в секундах
        self.is_in_slow_motion = False
        
        # Добавляем задачу обновления масштаба времени
        taskMgr.add(self.update_time_scale, 'update_time_scale')
        
        # Устанавливаем начальную скорость времени
        globalClock.setMode(ClockObject.MLimited)
        globalClock.setFrameRate(60)  # Ограничиваем FPS до 60
        
        # Добавляем обработчик обновления позиции оружия
        self.accept('update_weapon_position', self.update_weapon_position)

        # Initialize audio
        self.music = None
        self.current_music_path = None

        # Добавляем переменную для отслеживания зажатия кнопки
        self.mouse_pressed = False

    def create_text(self, x, y):
        return OnscreenText(
            text="",
            style=1,
            fg=(1, 1, 1, 1),
            pos=(x, y),
            align=TextNode.ALeft,
            scale=.05)

    def create_cross_marker(self, position):
        # Создаем узел для крестика
        marker_node = NodePath("hit_marker")
        marker_node.reparentTo(self.render)
        marker_node.setPos(position)
        
        # Создаем линии крестика
        segs = LineSegs()
        segs.setColor(1, 0, 0, 1)  # Красный цвет
        segs.setThickness(1.5)  # Толщина линий
        
        # Размер крестика
        size = 0.1
        
        # Центральная точка
        center = Point3(0, 0, 0)
        
        # Создаем шесть линий (по две для каждой оси)
        # X axis (вперед-назад)
        segs.moveTo(center + Point3(-size, 0, 0))
        segs.drawTo(center + Point3(size, 0, 0))
        
        # Y axis (влево-вправо)
        segs.moveTo(center + Point3(0, -size, 0))
        segs.drawTo(center + Point3(0, size, 0))
        
        # Z axis (вверх-вниз)
        segs.moveTo(center + Point3(0, 0, -size))
        segs.drawTo(center + Point3(0, 0, size))
        
        # Создаем и прикрепляем линии к узлу
        cross_lines = segs.create()
        cross_node = NodePath(cross_lines)
        cross_node.reparentTo(marker_node)
        
        # Настраиваем billboarding
        marker_node.setBillboardPointEye()
        
        return marker_node

    def create_hit_marker(self, position):
        # Создаем линии для крестика
        segs = LineSegs()
        segs.setColor(1, 0, 0, 1)  # Красный цвет
        segs.setThickness(2.0)
        
        # Размер крестика
        size = 0.2
        
        # Горизонтальная линия
        segs.moveTo(position + Point3(-size, 0, 0))
        segs.drawTo(position + Point3(size, 0, 0))
        
        # Вертикальная линия
        segs.moveTo(position + Point3(0, 0, -size))
        segs.drawTo(position + Point3(0, 0, size))
        
        # Создаем узел с крестиком
        marker_node = self.render.attachNewNode(segs.create())
        
        # Добавляем анимацию увеличения и исчезновения
        scale_sequence = Sequence(
            marker_node.scaleInterval(0.1, 1.5),  # Увеличение
            marker_node.scaleInterval(0.1, 1.0)   # Уменьшение
        )
        scale_sequence.start()
        
        return marker_node

    def setup_targets(self):
        """Создание манекенов"""
        # Очищаем существующие манекены
        for target in self.targets:
            target.cleanup()
        self.targets.clear()

        # Получаем количество манекенов из настроек (по умолчанию 10)
        target_count = self.settings.get('target_count', 10)
        
        # Параметры зоны спавна
        min_distance = 15  # Минимальная дистанция от игрока
        max_distance = 35  # Максимальная дистанция от игрока
        arena_width = 30   # Ширина арены
        
        # Создаем новые манекены
        for _ in range(target_count):
            # Генерируем случайную позицию
            x = random.uniform(-arena_width/2, arena_width/2)
            y = random.uniform(min_distance, max_distance)
            z = 1  # Высота манекена над землей
            
            # Создаем манекен на случайной позиции
            target = Target(self, Point3(x, y, z))
            self.targets.append(target)

    def setup_weapon(self):
        # Создаем контейнер для всего оружия
        self.weapon = NodePath("weapon")
        self.weapon.reparentTo(self.camera)
        
        # Создаем модели для каждого оружия
        self.weapon_models = {}
        
        # Создаем пистолет
        pistol = NodePath("pistol")
        pistol.reparentTo(self.weapon)
        
        # Дуло пистолета (короткий прямоугольник)
        barrel = self.loader.loadModel("models/box")
        barrel.setScale(0.08, 0.4, 0.08)  # Тонкое и длинное
        barrel.setPos(0, 1.0, -0.1)  # Выдвигаем вперед
        barrel.setColor(0.2, 0.2, 0.2)  # Тёмно-серый цвет
        barrel.reparentTo(pistol)
        
        # Рукоять пистолета
        grip = self.loader.loadModel("models/box")
        grip.setScale(0.1, 0.1, 0.25)  # Размер рукояти
        grip.setPos(0, 0.8, -0.3)  # Располагаем под дулом
        grip.setColor(0.3, 0.3, 0.3)  # Чуть светлее серый
        grip.reparentTo(pistol)
        
        self.weapon_models["pistol"] = pistol
        
        # Создаем винтовку
        rifle = NodePath("rifle")
        rifle.reparentTo(self.weapon)
        
        # Дуло винтовки (длинный прямоугольник)
        barrel = self.loader.loadModel("models/box")
        barrel.setScale(0.06, 0.8, 0.06)  # Более длинное и тонкое
        barrel.setPos(0, 1.2, -0.1)  # Выдвигаем дальше вперед
        barrel.setColor(0.2, 0.2, 0.2)  # Тёмно-серый цвет
        barrel.reparentTo(rifle)
        
        # Основная часть винтовки
        body = self.loader.loadModel("models/box")
        body.setScale(0.1, 0.4, 0.12)  # Шире и длиннее
        body.setPos(0, 0.8, -0.1)  # Позиция тела
        body.setColor(0.25, 0.25, 0.25)  # Серый цвет
        body.reparentTo(rifle)
        
        # Приклад винтовки
        stock = self.loader.loadModel("models/box")
        stock.setScale(0.08, 0.3, 0.15)  # Размер приклада
        stock.setPos(0, 0.4, -0.15)  # Позиция приклада
        stock.setColor(0.3, 0.3, 0.3)  # Чуть светлее серый
        stock.reparentTo(rifle)
        
        # Рукоять винтовки
        grip = self.loader.loadModel("models/box")
        grip.setScale(0.08, 0.1, 0.2)  # Размер рукояти
        grip.setPos(0, 0.7, -0.3)  # Позиция рукояти
        grip.setColor(0.3, 0.3, 0.3)  # Чуть светлее серый
        grip.reparentTo(rifle)
        
        self.weapon_models["rifle"] = rifle
        
        # Скрываем все оружия кроме текущего
        for weapon_name, model in self.weapon_models.items():
            if weapon_name == self.current_weapon:
                model.show()
            else:
                model.hide()
        
        # Apply weapon position from settings
        self.update_weapon_position()
        
        # Сохраняем начальную позицию для анимации отдачи
        self.original_weapon_pos = self.weapon.getPos()
        self.original_weapon_hpr = self.weapon.getHpr()

    def update_weapon_position(self):
        """Обновляет позицию оружия на основе настроек"""
        if not hasattr(self, 'weapon') or self.weapon.isEmpty():
            return
            
        # Убеждаемся что структура weapon_position существует
        if 'weapon_position' not in self.settings:
            self.settings['weapon_position'] = self.DEFAULT_SETTINGS['weapon_position'].copy()
            
        x = self.settings['weapon_position'].get('x', self.DEFAULT_SETTINGS['weapon_position']['x'])
        y = self.settings['weapon_position'].get('y', self.DEFAULT_SETTINGS['weapon_position']['y'])
        z = self.settings['weapon_position'].get('z', self.DEFAULT_SETTINGS['weapon_position']['z'])
        
        self.weapon.setPos(x, y, z)
        # Сохраняем новую позицию как оригинальную для анимации отдачи
        self.original_weapon_pos = self.weapon.getPos()
        self.original_weapon_hpr = self.weapon.getHpr()
        
        # Сохраняем настройки
        self.save_settings()
        
    def animate_weapon_recoil(self):
        # Сохраняем текущую позицию
        if not self.original_weapon_pos:
            self.original_weapon_pos = self.weapon.getPos()
            self.original_weapon_hpr = self.weapon.getHpr()
        
        start_pos = self.weapon.getPos()
        start_hpr = self.weapon.getHpr()
        
        # Создаем отдачу (назад и вверх)
        recoil_pos = Point3(
            start_pos.getX(),  # X остается тем же
            start_pos.getY() - 0.2,  # Сильнее назад
            start_pos.getZ() + 0.1   # Сильнее вверх
        )
        
        # Отдача в повороте оружия
        recoil_hpr = Vec3(
            start_hpr.getX(),     # Поворот влево-вправо
            start_hpr.getY() + 15, # Поворот вверх
            start_hpr.getZ() + random.uniform(-5, 5)  # Случайный наклон
        )
        
        # Создаем последовательность анимации
        recoil_sequence = Sequence(
            Parallel(
                # Быстрое движение назад и вверх
                self.weapon.posInterval(
                    0.05,  # Длительность движения назад
                    recoil_pos,
                    start_pos,
                    blendType='easeOut'
                ),
                # Поворот оружия
                self.weapon.hprInterval(
                    0.05,
                    recoil_hpr,
                    start_hpr,
                    blendType='easeOut'
                )
            ),
            # Медленное возвращение в исходную позицию
            Parallel(
                self.weapon.posInterval(
                    0.15,  # Длительность возврата
                    self.original_weapon_pos,
                    recoil_pos,
                    blendType='easeIn'
                ),
                self.weapon.hprInterval(
                    0.15,
                    self.original_weapon_hpr,
                    recoil_hpr,
                    blendType='easeIn'
                )
            )
        )
        
        recoil_sequence.start()

    def updateKeyMap(self, key, value):
        self.keyMap[key] = value

    def start_jump(self):
        """Начинает прыжок и обновляет комбо прыжков"""
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
                # Если распрыжка выключена, всегда используем базовую скорость
                self.jump_combo_multiplier = 1.0
                self.current_combo_jumps = 0
            
            # Применяем базовую силу прыжка (без множителя)
            self.vertical_velocity = self.jump_power
            
            # Добавляем горизонтальный импульс с учетом множителя комбо
            move_vec = Vec3(0, 0, 0)
            if self.keyMap["w"]: move_vec.setY(move_vec.getY() + 1)
            if self.keyMap["s"]: move_vec.setY(move_vec.getY() - 1)
            if self.keyMap["a"]: move_vec.setX(move_vec.getX() - 1)
            if self.keyMap["d"]: move_vec.setX(move_vec.getX() + 1)
            
            if move_vec.length() > 0:
                move_vec.normalize()
                # Применяем множитель комбо к горизонтальной скорости
                base_speed = self.sprint_speed if self.keyMap["shift"] else self.move_speed
                self.horizontal_velocity = move_vec * base_speed * self.jump_combo_multiplier
            else:
                self.horizontal_velocity = Vec3(0, 0, 0)
            
            self.is_jumping = True
            self.last_jump_time = current_time
            
            # Запускаем таймер для сброса комбо
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
        if not self.can_shoot:
            return
            
        self.can_shoot = False
        
        # Play shooting sound
        self.shot_sound.play()
        
        # Устанавливаем таймер на возможность следующего выстрела
        self.taskMgr.doMethodLater(
            self.shoot_cooldown,
            self.reset_shoot,
            'reset_shoot'
        )
        
        # Получаем параметры текущего оружия
        weapon_params = self.weapons[self.current_weapon]
        
        # Применяем отдачу только если она включена в настройках
        if self.settings.get('recoil_enabled', True):
            # Применяем отдачу к камере с параметрами текущего оружия
            recoil_pitch_range = weapon_params["recoil"]["pitch"]
            recoil_yaw_range = weapon_params["recoil"]["yaw"]
            
            recoil_pitch = random.uniform(recoil_pitch_range[0], recoil_pitch_range[1])
            recoil_yaw = random.uniform(recoil_yaw_range[0], recoil_yaw_range[1])
            
            self.recoil_pitch += recoil_pitch
            self.recoil_yaw += recoil_yaw
            
            # Ограничиваем максимальную отдачу
            self.recoil_pitch = min(self.recoil_pitch, self.max_recoil_pitch)
            self.recoil_yaw = max(min(self.recoil_yaw, self.max_recoil_yaw), -self.max_recoil_yaw)
            
            # Применяем отдачу к камере
            self.camera_pitch += recoil_pitch
            self.camera_heading += recoil_yaw
            
            # Обновляем время последнего выстрела
            self.last_shot_time = globalClock.getFrameTime()
            
            # Анимация отдачи оружия
            self.animate_weapon_recoil()
        
        if not self.mouseWatcherNode.hasMouse():
            return
            
        # Получаем позицию мыши
        mouse_pos = self.mouseWatcherNode.getMouse()
        
        # Создаем луч от камеры
        from_pos = Point3(0, 0, 0)
        from_pos = self.render.getRelativePoint(self.camera, from_pos)
        
        to_pos = Point3(mouse_pos.getX(), 1.0, mouse_pos.getY())
        to_pos = self.render.getRelativePoint(self.camera, Point3(to_pos.getX() * 100, 100, to_pos.getZ() * 100))
        
        # Создаем CollisionRay для определения попадания
        self.ray.setFromLens(self.camNode, mouse_pos.getX(), mouse_pos.getY())
        
        self.cTrav.traverse(self.render)
        
        if self.cQueue.getNumEntries() > 0:
            # Сортируем попадания по расстоянию
            self.cQueue.sortEntries()
            hit = self.cQueue.getEntry(0)
            
            # Вызываем handle_collision для подсчета очков
            self.handle_collision(hit)
            
            hit_pos = hit.getSurfacePoint(self.render)
            
            # Генерируем уникальное имя для задачи
            task_name = f"remove_effect_{len(self.shot_effects)}"
            
            # Создаем задачу для удаления эффекта через 6 секунд
            remove_task = self.taskMgr.doMethodLater(
                6.0,
                self.remove_specific_effect,
                task_name,
                extraArgs=[len(self.shot_effects)],
                appendTask=True
            )
            
            # Добавляем эффект в список
            self.shot_effects.append((None, self.create_hit_marker(hit_pos), remove_task))

    def remove_specific_effect(self, effect_index, task):
        if 0 <= effect_index < len(self.shot_effects):
            _, marker_node, _ = self.shot_effects[effect_index]
            if marker_node:
                marker_node.removeNode()
            self.shot_effects[effect_index] = (None, None, None)
        return task.done

    def show_damage(self, position, damage):
        # Создаем текст с уроном
        damage_text = TextNode('damage')
        damage_text.setText(f"{damage}")
        damage_text.setAlign(TextNode.ACenter)
        
        # Создаем узел для текста и прикрепляем к aspect2d (2D слой)
        text_node_path = self.aspect2d.attachNewNode(damage_text)
        
        # Генерируем случайное смещение от центра
        offset_x = random.uniform(-0.15, 0.15)
        offset_y = random.uniform(-0.15, 0.15)
        
        # Располагаем текст со случайным смещением от центра
        text_node_path.setPos(offset_x, 0, offset_y)
        
        # Устанавливаем размер текста
        text_node_path.setScale(0.07)
        
        # Устанавливаем цвет в зависимости от урона
        if damage >= 100:  # Хедшот
            text_node_path.setColor(1, 0, 0, 1)  # Красный
        elif damage >= 60:  # Высокий урон
            text_node_path.setColor(1, 0.5, 0, 1)  # Оранжевый
        else:  # Обычный урон
            text_node_path.setColor(1, 1, 1, 1)  # Белый
        
        # Создаем анимацию движения вверх и исчезновения
        fade_interval = LerpColorScaleInterval(
            text_node_path,
            0.5,  # Длительность
            Vec4(1, 1, 1, 0),  # Конечное значение (прозрачный)
            Vec4(1, 1, 1, 1)   # Начальное значение (непрозрачный)
        )
        
        # Конечная позиция будет немного выше начальной, сохраняя случайное X-смещение
        pos_interval = text_node_path.posInterval(
            0.5,  # Длительность
            Point3(offset_x, 0, offset_y + 0.2),  # Конечная позиция
            Point3(offset_x, 0, offset_y)         # Начальная позиция
        )
        
        # Запускаем обе анимации одновременно
        Parallel(fade_interval, pos_interval).start()
        
        # Удаляем текст через 0.5 секунды
        self.taskMgr.doMethodLater(
            0.5,
            lambda task: text_node_path.removeNode(),
            'remove_damage_text'
        )

    def update_damage_texts(self, task):
        current_time = globalClock.getFrameTime()
        
        # Обновляем каждый текст
        for i in range(len(self.damage_texts) - 1, -1, -1):
            text_node, start_time, start_pos = self.damage_texts[i]
            age = current_time - start_time
            
            if age > 1.0:  # Текст живет 1 секунду
                text_node.removeNode()
                self.damage_texts.pop(i)
            else:
                # Поднимаем текст вверх и делаем его прозрачным
                alpha = 1.0 - age
                z_offset = age * 2  # Поднимаем на 2 единицы за секунду
                text_node.setPos(start_pos + Point3(0, 0, z_offset))
                text_node.setAlphaScale(alpha)
        
        return task.cont

    def cleanup(self, window=None):
        # Очищаем все эффекты
        for line_node, marker_node, task in self.shot_effects:
            if line_node:
                line_node.removeNode()
            if marker_node:
                marker_node.removeNode()
            if task:
                self.taskMgr.remove(task)
        self.shot_effects.clear()
        
        # Очищаем все тексты урона
        for text_node, _, _ in self.damage_texts:
            text_node.removeNode()
        self.damage_texts.clear()

    def return_to_menu(self):
        # Скрываем UI элементы
        self.score_text.hide()
        self.timer_text.hide()
        self.taskMgr.remove("timer_task")
        
        # Отключаем игровые компоненты
        self.taskMgr.remove("update")
        self.ignore("mouse1")
        
        # Очищаем старые цели
        for target in self.targets:
            target.destroy()
        self.targets.clear()
        
        # Очищаем оружие если оно есть
        if hasattr(self, 'weapon'):
            self.weapon.removeNode()
        
        # Показываем меню
        self.main_menu.show()

    def start_game(self):
        # Настраиваем окно для игры
        props = WindowProperties()
        props.setCursorHidden(True)
        self.win.requestProperties(props)
        
        # Очищаем старые цели если они есть
        for target in self.targets:
            target.destroy()
        self.targets.clear()
        
        # Включаем игровые компоненты
        self.setup_targets()
        self.setup_weapon()
        
        # Включаем управление
        self.taskMgr.add(self.update, "update")
        self.accept("mouse1", self.on_mouse_press)
        self.accept("mouse1-up", self.on_mouse_release)
        
        # Сбрасываем и показываем счет и таймер
        self.score = 0
        self.start_time = time.time()
        self.update_score_display()
        self.update_timer_display()
        
        if self.show_score:
            self.score_text.show()
        if self.show_timer:
            self.timer_text.show()
            self.taskMgr.add(self.update_timer_task, "timer_task")
        
        # Setup audio
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
        # Получаем целевой объект и проверяем, что это действительно цель
        hit_node = entry.getIntoNode()
        if not hit_node.getName().startswith('target_'):
            return
            
        target = entry.getIntoNodePath().getParent()
        while target.getName() != "target_root":
            target = target.getParent()
            if target is None:
                return
        
        # Получаем часть тела, в которую попали
        damage = self.get_damage_for_part(hit_node.getName())
        
        if damage <= 0:  # Если попали не в валидную часть тела
            return
            
        # Активируем эффекты при попадании
        self.activate_hit_effects()
        
        # Воспроизводим звук попадания
        self.hit_sound.play()
        
        # Обновляем комбо
        current_time = time.time()
        if current_time - self.last_hit_time < self.combo_window:
            self.combo_multiplier = min(2.0, self.combo_multiplier + 0.2)  # Максимум x2
        else:
            self.combo_multiplier = 1.0
        self.last_hit_time = current_time
        
        # Вычисляем очки с учетом комбо
        points = int(damage * self.combo_multiplier)
        
        # Добавляем очки
        self.score += points
        
        # Обновляем отображение счета
        if hasattr(self, 'score_text') and self.show_score:
            self.score_text.setText(f"Score: {self.score}")
        
        # Получаем точку попадания
        hit_pos = entry.getSurfacePoint(self.render)
        
        # Показываем текст с очками
        if self.settings.get('damage_numbers', True):
            self.spawn_damage_text(f"+{points}", hit_pos)
        
        # Удаляем старый манекен
        target.removeNode()
        
        # Создаем новый манекен через случайное время
        delay = random.uniform(0.5, 2.0)
        taskMgr.doMethodLater(delay, self.spawn_target, 'spawn_target')
        
        # Добавляем сообщение в килфид
        if self.settings.get('killfeed', True):
            self.create_killfeed_message("Training Bot")

    def get_damage_for_part(self, part_name):
        """Возвращает урон в зависимости от части тела"""
        base_damage = self.weapons[self.current_weapon]["damage"]
        
        # Множители урона для разных частей тела
        damage_multipliers = {
            "head": 2.0,    # Двойной урон в голову
            "body": 1.0,    # Обычный урон в тело
            "limb": 0.75    # Уменьшенный урон в конечность
        }
        
        # Получаем множитель урона для части тела или 1.0 если часть неизвестна
        multiplier = damage_multipliers.get(part_name, 1.0)
        
        # Возвращаем урон с учетом множителя
        return int(base_damage * multiplier)

    def spawn_damage_text(self, text, pos):
        # Создаем текст с уроном
        damage_text = TextNode('damage')
        damage_text.setText(text)
        damage_text.setAlign(TextNode.ACenter)
        
        # Создаем узел для текста и прикрепляем к aspect2d (2D слой)
        text_node_path = self.aspect2d.attachNewNode(damage_text)
        
        # Генерируем случайное смещение от центра
        offset_x = random.uniform(-0.15, 0.15)
        offset_y = random.uniform(-0.15, 0.15)
        
        # Располагаем текст со случайным смещением от центра
        text_node_path.setPos(offset_x, 0, offset_y)
        
        # Устанавливаем размер текста
        text_node_path.setScale(0.07)
        
        # Устанавливаем цвет в зависимости от урона
        if int(text) >= 100:  # Хедшот
            text_node_path.setColor(1, 0, 0, 1)  # Красный
        elif int(text) >= 60:  # Высокий урон
            text_node_path.setColor(1, 0.5, 0, 1)  # Оранжевый
        else:  # Обычный урон
            text_node_path.setColor(1, 1, 1, 1)  # Белый
        
        # Создаем анимацию движения вверх и исчезновения
        fade_interval = LerpColorScaleInterval(
            text_node_path,
            0.5,  # Длительность
            Vec4(1, 1, 1, 0),  # Конечное значение (прозрачный)
            Vec4(1, 1, 1, 1)   # Начальное значение (непрозрачный)
        )
        
        # Конечная позиция будет немного выше начальной, сохраняя случайное X-смещение
        pos_interval = text_node_path.posInterval(
            0.5,  # Длительность
            Point3(offset_x, 0, offset_y + 0.2),  # Конечная позиция
            Point3(offset_x, 0, offset_y)         # Начальная позиция
        )
        
        # Запускаем обе анимации одновременно
        Parallel(fade_interval, pos_interval).start()
        
        # Удаляем текст через 0.5 секунды
        self.taskMgr.doMethodLater(
            0.5,
            lambda task: text_node_path.removeNode(),
            'remove_damage_text'
        )

    def spawn_target(self, task):
        # Генерируем случайную позицию для нового манекена
        x = random.uniform(-10, 10)
        y = random.uniform(20, 30)
        
        # Создаем новый манекен
        target = Target(self, Point3(x, y, 1))
        self.targets.append(target)
        
        return task.done

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

    def on_target_hit(self, target, hit_pos):
        # Активируем эффекты при попадании
        self.activate_hit_effects()
        
        # Существующая логика обработки попадания
        self.hit_sound.play()
        self.score += 10 * self.combo_multiplier
        
        # Обновляем комбо
        current_time = time.time()
        if current_time - self.last_hit_time < self.combo_window:
            self.combo_multiplier += 0.5
        else:
            self.combo_multiplier = 1.0
        self.last_hit_time = current_time
        
        # Обновляем текст счета
        if self.show_score:
            self.score_text.setText(f"Score: {int(self.score)}")
        
        # Создаем текст с уроном
        damage_text = OnscreenText(
            text=f"+{int(10 * self.combo_multiplier)}",
            pos=(0, 0),
            scale=0.05,
            fg=(1, 1, 0, 1),
            align=TextNode.ACenter
        )
        
        # Получаем позицию попадания в пространстве экрана
        p3 = Point3()
        p2 = Point2()
        self.camera.getRelativePoint(self.render, hit_pos).projectOnScreen(self.win, p2)
        screen_pos = (p2.getX(), p2.getZ())
        
        # Добавляем текст урона в список для анимации
        self.damage_texts.append((damage_text, time.time(), screen_pos))
        
        # Удаляем цель и создаем новую
        self.targets.remove(target)
        target.cleanup()
        self.spawn_target()

    def create_killfeed_message(self, target_name="Target"):
        """Создает новое сообщение в килфиде"""
        y_pos = 0.9 - len(self.killfeed_messages) * 0.06
        x_pos = 1.3 + self.killfeed_slide_distance  # Начальная позиция справа
        
        # Создаем текст сообщения с начальной прозрачностью 0
        message = OnscreenText(
            text=f"You killed {target_name}",
            fg=(0.3, 0.6, 1, 0),
            shadow=(0, 0, 0, 0),
            pos=(x_pos, y_pos),
            align=TextNode.ARight,
            scale=0.04
        )
        message.setBin('gui-popup', 0)

        # Создаем узел для группировки фона и границ
        frame_root = aspect2d.attachNewNode("frame_root")
        frame_root.setPos(x_pos, 0, y_pos)  # Устанавливаем начальную позицию
        
        # Создаем фон для сообщения с начальной прозрачностью 0
        cm = CardMaker('killfeed_bg')
        cm.setFrame(-0.5, 0.05, -0.015, 0.025)  # Относительные координаты
        bg = frame_root.attachNewNode(cm.generate())
        bg.setTransparency(TransparencyAttrib.MAlpha)
        bg.setColor(0, 0, 0, 0)
        bg.setBin('background', 10)
        
        # Создаем белые границы с начальной прозрачностью 0
        border_thickness = 0.002
        borders = []
        
        # Верхняя граница
        cm_top = CardMaker('border_top')
        cm_top.setFrame(-0.5, 0.05, 0.025, 0.025 + border_thickness)
        border_top = frame_root.attachNewNode(cm_top.generate())
        border_top.setColor(1, 1, 1, 0)
        border_top.setTransparency(TransparencyAttrib.MAlpha)
        border_top.setBin('background', 11)
        borders.append(border_top)
        
        # Нижняя граница
        cm_bottom = CardMaker('border_bottom')
        cm_bottom.setFrame(-0.5, 0.05, -0.015 - border_thickness, -0.015)
        border_bottom = frame_root.attachNewNode(cm_bottom.generate())
        border_bottom.setColor(1, 1, 1, 0)
        border_bottom.setTransparency(TransparencyAttrib.MAlpha)
        border_bottom.setBin('background', 11)
        borders.append(border_bottom)
        
        # Левая граница
        cm_left = CardMaker('border_left')
        cm_left.setFrame(-0.5 - border_thickness, -0.5, -0.015, 0.025)
        border_left = frame_root.attachNewNode(cm_left.generate())
        border_left.setColor(1, 1, 1, 0)
        border_left.setTransparency(TransparencyAttrib.MAlpha)
        border_left.setBin('background', 11)
        borders.append(border_left)
        
        # Правая граница
        cm_right = CardMaker('border_right')
        cm_right.setFrame(0.05, 0.05 + border_thickness, -0.015, 0.025)
        border_right = frame_root.attachNewNode(cm_right.generate())
        border_right.setColor(1, 1, 1, 0)
        border_right.setTransparency(TransparencyAttrib.MAlpha)
        border_right.setBin('background', 11)
        borders.append(border_right)
        
        # Добавляем сообщение в список с временем создания
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
        
        # Удаляем старые сообщения, если их больше 5
        if len(self.killfeed_messages) > 5:
            oldest = self.killfeed_messages[0]
            oldest['target_alpha'] = 0

    def update_killfeed_positions(self):
        """Обновляет позиции всех сообщений в килфиде"""
        current_time = globalClock.getFrameTime()
        messages_to_remove = []
        
        for i, msg_data in enumerate(self.killfeed_messages):
            # Вычисляем время жизни сообщения
            age = current_time - msg_data['creation_time']
            
            # Обновляем альфа и позицию X
            if msg_data['alpha'] != msg_data['target_alpha']:
                # Плавное изменение прозрачности
                alpha_change = globalClock.getDt() / self.killfeed_fade_time
                if msg_data['target_alpha'] > msg_data['alpha']:
                    msg_data['alpha'] = min(msg_data['target_alpha'], msg_data['alpha'] + alpha_change)
                else:
                    msg_data['alpha'] = max(msg_data['target_alpha'], msg_data['alpha'] - alpha_change)
                
                # Обновляем прозрачность всех элементов
                msg_data['message'].setFg((0.3, 0.6, 1, msg_data['alpha']))
                msg_data['message'].setShadow((0, 0, 0, msg_data['alpha']))
                msg_data['background'].setColor(0, 0, 0, msg_data['alpha'] * 0.3)
                for border in msg_data['borders']:
                    border.setColor(1, 1, 1, msg_data['alpha'] * 0.8)
            
            # Анимация скольжения
            if msg_data['x_offset'] > 0:
                slide_speed = self.killfeed_slide_distance / self.killfeed_fade_time
                msg_data['x_offset'] = max(0, msg_data['x_offset'] - slide_speed * globalClock.getDt())
                new_x = 1.3 + msg_data['x_offset']
                
                # Обновляем позицию текста и рамки
                msg_data['message'].setPos(new_x, msg_data['y_pos'])
                msg_data['frame_root'].setPos(new_x, 0, msg_data['y_pos'])
                msg_data['x_pos'] = new_x
            
            # Запускаем исчезновение через 5 секунд
            if age > 5.0 and msg_data['target_alpha'] == 1:
                msg_data['target_alpha'] = 0
            
            # Удаляем полностью прозрачные сообщения
            if msg_data['alpha'] <= 0 and msg_data['target_alpha'] == 0:
                messages_to_remove.append(msg_data)
            
            # Обновляем позицию Y для всех сообщений
            target_y = 0.9 - i * 0.06
            if msg_data['y_pos'] != target_y:
                msg_data['y_pos'] = target_y
                msg_data['message'].setPos(msg_data['x_pos'], target_y)
                msg_data['frame_root'].setPos(msg_data['x_pos'], 0, target_y)
        
        # Удаляем сообщения
        for msg_data in messages_to_remove:
            msg_data['message'].removeNode()
            msg_data['frame_root'].removeNode()  # Удаляем весь узел с рамкой
            self.killfeed_messages.remove(msg_data)

    def update(self, task):
        """Обновление состояния игры"""
        dt = globalClock.getDt()
        
        # Обновляем FPS
        self.fps = int(globalClock.getAverageFrameRate())
        
        # Плавное изменение масштаба времени
        if self.current_time_scale != self.target_time_scale:
            diff = self.target_time_scale - self.current_time_scale
            change = min(abs(diff), dt * self.time_scale_speed) * (1 if diff > 0 else -1)
            self.current_time_scale += change
        
        # Применяем текущий масштаб времени к dt
        scaled_dt = dt * self.current_time_scale
        
        # Обновляем все, что зависит от времени
        self.update_score_display()
        
        # Обновляем информационные тексты
        self.fps_text.setText(f"FPS: {self.fps}")
        self.pos_text.setText(f"Pos: ({self.camera.getX():.1f}, {self.camera.getY():.1f}, {self.camera.getZ():.1f})")
        
        # Обновление отдачи
        current_time = globalClock.getFrameTime()
        if current_time - self.last_shot_time > self.recoil_recovery_delay:
            # Восстановление от отдачи
            if self.recoil_pitch > 0:
                old_pitch = self.recoil_pitch
                self.recoil_pitch = max(0, self.recoil_pitch - self.recoil_recovery_speed * dt)
                # Применяем разницу к камере
                self.camera_pitch -= (old_pitch - self.recoil_pitch)
            
            if self.recoil_yaw != 0:
                old_yaw = self.recoil_yaw
                if self.recoil_yaw > 0:
                    self.recoil_yaw = max(0, self.recoil_yaw - self.recoil_recovery_speed * dt)
                else:
                    self.recoil_yaw = min(0, self.recoil_yaw + self.recoil_recovery_speed * dt)
                # Применяем разницу к камере
                self.camera_heading -= (old_yaw - self.recoil_yaw)
            
            # Обновляем положение камеры
            self.camera.setHpr(self.camera_heading, self.camera_pitch, 0)
        
        # Обработка движения
        move_vec = Vec3(0, 0, 0)
        
        # Получаем текущие нажатые клавиши для движения
        if self.keyMap["w"]: move_vec.addY(1)
        if self.keyMap["s"]: move_vec.addY(-1)
        if self.keyMap["a"]: move_vec.addX(-1)
        if self.keyMap["d"]: move_vec.addX(1)
            
        # Нормализуем вектор движения, если он не нулевой
        if move_vec.length() > 0:
            move_vec.normalize()
            
            # Применяем поворот камеры к вектору движения
            heading = self.camera.getH() * (pi / 180.0)
            move_vec = Vec3(
                move_vec.getX() * cos(heading) - move_vec.getY() * sin(heading),
                move_vec.getX() * sin(heading) + move_vec.getY() * cos(heading),
                0
            )
        
        # Применяем скорость движения с учетом замедления времени
        speed = (self.sprint_speed if self.is_sprinting else self.move_speed) * self.current_time_scale
        if self.is_jumping:
            # Применяем множитель скорости от комбо прыжков
            speed *= self.jump_combo_multiplier
            
        # Если есть активное движение, обновляем горизонтальную скорость
        if move_vec.length() > 0:
            self.horizontal_velocity = move_vec * speed
        elif not self.is_jumping:
            # Если на земле и нет движения, обнуляем горизонтальную скорость
            self.horizontal_velocity = Vec3(0, 0, 0)
            
        # Применяем горизонтальное движение с учетом замедления времени
        if self.horizontal_velocity.length() > 0:
            self.camera.setPos(
                self.camera.getX() + self.horizontal_velocity.getX() * scaled_dt,
                self.camera.getY() + self.horizontal_velocity.getY() * scaled_dt,
                self.camera.getZ()
            )
        
        # Обработка прыжка и гравитации с учетом замедления времени
        if self.is_jumping:
            self.vertical_velocity += self.gravity * scaled_dt
            new_z = self.camera.getZ() + self.vertical_velocity * scaled_dt
            
            if new_z <= self.camera_height:
                new_z = self.camera_height
                self.vertical_velocity = 0
                self.is_jumping = False
                self.jump_speed_boost = 1.0
                # Сбрасываем горизонтальную скорость при приземлении если нет активного движения
                if move_vec.length() == 0:
                    self.horizontal_velocity = Vec3(0, 0, 0)
            
            self.camera.setZ(new_z)
            
        # Обновляем поворот камеры с учетом замедления времени
        if self.mouseWatcherNode.hasMouse():
            mouse_x = self.mouseWatcherNode.getMouseX()
            mouse_y = self.mouseWatcherNode.getMouseY()
            
            # Применяем замедление к чувствительности мыши
            sensitivity = self.mouse_sensitivity * self.current_time_scale
            
            self.camera_heading -= mouse_x * sensitivity
            self.camera_pitch += mouse_y * sensitivity
            
            # Ограничиваем угол подъема/спуска камеры
            self.camera_pitch = min(89, max(-89, self.camera_pitch))
            
            self.camera.setHpr(self.camera_heading, self.camera_pitch, 0)
            
            # Возвращаем курсор в центр экрана
            self.win.movePointer(0,
                int(self.win.getProperties().getXSize() / 2),
                int(self.win.getProperties().getYSize() / 2))
        
        # Вычисляем текущую скорость движения
        current_speed = math.sqrt(self.horizontal_velocity.getX()**2 + self.horizontal_velocity.getY()**2)
        self.speed_text.setText(f"Speed: {current_speed:.1f}")
        
        # Обработка стрельбы при нажатии левой кнопки мыши
        if self.mouse_pressed and self.current_weapon == "rifle":
            current_time = time.time()
            if current_time - self.last_shot_time >= self.weapons[self.current_weapon]["cooldown"]:
                self.shoot()
        
        # Обновляем килфид
        self.update_killfeed_positions()
        
        return task.cont

    def apply_settings(self, new_settings):
        # Обновляем настройки
        self.settings.update(new_settings)
        
        # Применяем настройки
        if 'sensitivity' in new_settings:
            self.mouse_sensitivity = new_settings['sensitivity']
        if 'fov' in new_settings:
            lens = self.cam.node().getLens()
            lens.setFov(new_settings['fov'])
        if 'show_score' in new_settings:
            self.show_score = new_settings['show_score']
        if 'show_timer' in new_settings:
            self.show_timer = new_settings['show_timer']
            
        # Сохраняем все настройки
        self.save_settings()

    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                return json.load(f)
        except:
            return self.DEFAULT_SETTINGS.copy()

    def save_settings(self):
        """Сохраняет текущие настройки в файл"""
        # Обновляем значение чувствительности в настройках перед сохранением
        self.settings['sensitivity'] = self.mouse_sensitivity
        
        try:
            with open('settings.json', 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def update_mouse_sensitivity(self):
        """Обновляет чувствительность мыши на основе настроек"""
        self.mouse_sensitivity = self.settings.get('sensitivity', self.DEFAULT_SETTINGS['sensitivity'])

    def setup_mouse(self):
        """Настраивает управление мышью"""
        # Скрываем курсор мыши
        props = WindowProperties()
        props.setCursorHidden(True)
        # Устанавливаем курсор в центр экрана
        props.setMouseMode(WindowProperties.M_relative)
        base.win.requestProperties(props)
        
        # Отключаем стандартное управление камерой
        base.disableMouse()
        
        # Настраиваем чувствительность мыши
        self.mouse_sensitivity = self.settings.get('sensitivity', self.DEFAULT_SETTINGS['sensitivity'])
        
        # Добавляем обработчик движения мыши
        self.accept("mouse1", self.on_mouse_press)
        self.accept("mouse1-up", self.on_mouse_release)
        
        # Устанавливаем задачу для обработки движения мыши
        taskMgr.add(self.mouseTask, 'mouseTask')
        
    def mouseTask(self, task):
        """Обрабатывает движение мыши"""
        if task.time < 0.05:  # Пропускаем первый кадр
            return Task.cont
            
        # Получаем изменение позиции мыши
        md = base.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        
        if base.win.movePointer(0, base.win.getXSize()//2, base.win.getYSize()//2):
            # Рассчитываем изменение положения
            deltaX = x - base.win.getXSize()//2
            deltaY = y - base.win.getYSize()//2
            
            # Применяем чувствительность
            sensitivity_factor = 25.0  # Увеличено с 10.0 до 25.0
            deltaX *= self.mouse_sensitivity * sensitivity_factor
            deltaY *= self.mouse_sensitivity * sensitivity_factor
            
            # Обновляем поворот камеры
            heading = self.camera.getH() - deltaX * 0.3  # Увеличено с 0.2 до 0.3
            pitch = self.camera.getP() + deltaY * 0.3
            
            # Ограничиваем угол обзора по вертикали
            pitch = min(90, max(-90, pitch))
            
            self.camera.setH(heading)
            self.camera.setP(pitch)
            
            # Поворачиваем оружие вместе с камерой
            if hasattr(self, 'weapon'):
                self.weapon.setH(heading)
                self.weapon.setP(pitch)
        
        return Task.cont

    def setup_audio(self):
        """Setup and start background music"""
        audio_settings = self.settings.get('audio', self.DEFAULT_SETTINGS['audio'])
        
        if audio_settings['music_enabled']:
            self.play_music(audio_settings['current_track'], audio_settings['music_volume'])

    def play_music(self, track_name, volume=0.5):
        """Play background music with specified volume"""
        if self.music:
            self.music.stop()
        
        # Get the music file path
        music_path = f"music/{track_name}"
        
        try:
            self.music = loader.loadSfx(music_path)
            if self.music:
                self.music.setLoop(True)
                self.music.setVolume(volume)
                self.music.play()
                self.current_music_path = music_path
        except Exception as e:
            print(f"Error loading music: {e}")

    def update_music_volume(self, volume):
        """Update the volume of currently playing music"""
        if self.music:
            self.music.setVolume(volume)
            
        # Update settings
        if 'audio' not in self.settings:
            self.settings['audio'] = self.DEFAULT_SETTINGS['audio'].copy()
        self.settings['audio']['music_volume'] = volume
        self.save_settings()

    def change_music_track(self, track_name):
        """Change the current music track"""
        if 'audio' not in self.settings:
            self.settings['audio'] = self.DEFAULT_SETTINGS['audio'].copy()
            
        self.settings['audio']['current_track'] = track_name
        self.save_settings()
        
        if self.settings['audio']['music_enabled']:
            self.play_music(track_name, self.settings['audio']['music_volume'])

    def toggle_music(self, enabled):
        """Toggle background music on/off"""
        if 'audio' not in self.settings:
            self.settings['audio'] = self.DEFAULT_SETTINGS['audio'].copy()
            
        self.settings['audio']['music_enabled'] = enabled
        self.save_settings()
        
        if enabled:
            self.play_music(self.settings['audio']['current_track'], self.settings['audio']['music_volume'])
        elif self.music:
            self.music.stop()

    def switch_weapon(self, weapon_name):
        """Переключает оружие"""
        if weapon_name in self.weapons and hasattr(self, 'weapon_models'):
            # Обновляем текущее оружие
            self.current_weapon = weapon_name
            self.shoot_cooldown = self.weapons[weapon_name]["cooldown"]
            
            # Переключаем видимость моделей
            for name, model in self.weapon_models.items():
                if name == weapon_name:
                    model.show()
                else:
                    model.hide()

    def on_mouse_press(self):
        """Обработчик нажатия кнопки мыши"""
        self.mouse_pressed = True
        # Сразу производим первый выстрел
        self.shoot()

    def on_mouse_release(self):
        """Обработчик отпускания кнопки мыши"""
        self.mouse_pressed = False

if __name__ == "__main__":
    game = Game()
    game.run()
