from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpColorScaleInterval, Wait, Func, LerpScaleInterval, LerpPosInterval
from panda3d.core import TextNode, TransparencyAttrib, Vec4, NodePath, Vec3, WindowProperties, CardMaker
from direct.gui.DirectFrame import DirectFrame
import random
from menu_system.ui_helpers import get_resolution_ui_scale

class SplashScreen:
    def __init__(self, game):
        self.game = game
        self.ui_root = game.a2dBackground.attachNewNode("splash_ui_root")
        
        # Set up window properties for splash screen
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.MRelative)
        game.win.requestProperties(props)
        
        # Center the mouse
        game.win.movePointer(0,
                          int(game.win.getProperties().getXSize() / 2),
                          int(game.win.getProperties().getYSize() / 2))
        
        # Add mouse watcher task
        self.mouse_task = game.taskMgr.add(self.mouse_task, 'splash_mouse_task')
        
        # Создаем градиентный фон (темно-синий -> фиолетовый)
        self.background = DirectFrame(
            frameColor=(0.08, 0.08, 0.15, 1),  # Глубокий темно-синий
            frameSize=(-2, 2, -2, 2),
            parent=game.render2d
        )
        
        # Создаем снежинки
        self.snowflakes = []
        self.create_snowflakes(30)  # 30 снежинок
        
        # Логотип автора
        self.author_logo = OnscreenImage(
            image="assets/author_logo.jpg",
            pos=(0, 0, 0.15),
            scale=0.25,
            parent=self.ui_root
        )
        self.author_logo.setTransparency(TransparencyAttrib.MAlpha)
        self.author_logo.setColorScale(1, 1, 1, 0)
        
        # Имя автора под логотипом
        self.author_name = OnscreenText(
            text="heck43",
            pos=(0, -0.2),
            scale=0.08,
            fg=(0.9, 0.9, 0.95, 1),  # Светло-серый, почти белый
            align=TextNode.ACenter,
            mayChange=False,
            parent=self.ui_root,
            font=None  # Используем стандартный шрифт
        )
        self.author_name.setTransparency(TransparencyAttrib.MAlpha)
        self.author_name.setColorScale(0.9, 0.9, 0.95, 0)
        
        # Название игры
        self.game_title = OnscreenText(
            text="AIM TRAINER",
            pos=(0, 0.05),
            scale=0.25,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=False,
            parent=self.ui_root,
            font=None
        )
        self.game_title.setTransparency(TransparencyAttrib.MAlpha)
        self.game_title.setColorScale(1, 1, 1, 0)
        
        # Подзаголовок
        self.subtitle = OnscreenText(
            text="— precision & focus —",
            pos=(0, -0.1),
            scale=0.055,
            fg=(0.7, 0.7, 0.8, 1),
            align=TextNode.ACenter,
            mayChange=False,
            parent=self.ui_root,
            font=None
        )
        self.subtitle.setTransparency(TransparencyAttrib.MAlpha)
        self.subtitle.setColorScale(0.7, 0.7, 0.8, 0)
        
        # Текст загрузки
        self.loading_text = OnscreenText(
            text="loading",
            pos=(0, -0.35),
            scale=0.06,
            fg=(0.8, 0.8, 0.9, 1),
            align=TextNode.ACenter,
            mayChange=True,
            parent=self.ui_root
        )
        self.loading_text.setTransparency(TransparencyAttrib.MAlpha)
        self.loading_text.setColorScale(0.8, 0.8, 0.9, 0)
        
        # Прогресс бар - минималистичный
        # Фон прогресс бара
        self.progress_bg = DirectFrame(
            frameColor=(0.15, 0.15, 0.25, 0.3),  # Полупрозрачный
            frameSize=(-0.4, 0.4, -0.008, 0.008),
            pos=(0, 0, -0.45),
            parent=self.ui_root
        )
        self.progress_bg.setTransparency(TransparencyAttrib.MAlpha)
        self.progress_bg.setColorScale(0.15, 0.15, 0.25, 0)
        
        # Прогресс бар - активная часть
        self.progress_fill = DirectFrame(
            frameColor=(0.85, 0.85, 0.95, 1),  # Светлый, элегантный
            frameSize=(0, 0.8, -0.006, 0.006),
            pos=(-0.4, 0, -0.45),
            parent=self.ui_root
        )
        self.progress_fill.setTransparency(TransparencyAttrib.MAlpha)
        self.progress_fill.setColorScale(0.85, 0.85, 0.95, 0)
        self.progress_fill.setScale(0.01, 1.0, 1.0)  # Начинаем с нулевого размера

        # Store all elements
        self.elements = [
            self.background,
            self.author_logo,
            self.author_name,
            self.game_title,
            self.subtitle,
            self.loading_text,
            self.progress_bg,
            self.progress_fill
        ] + self.snowflakes
        
        # Запускаем анимацию снега
        self.update_layout()
        self.snow_task = game.taskMgr.add(self.update_snow, 'snow_task')

    def get_splash_ui_scale(self):
        return get_resolution_ui_scale(self.game, base_width=1024, base_height=576, min_scale=0.42, max_scale=1.0)

    def update_layout(self):
        if self.ui_root and not self.ui_root.isEmpty():
            self.ui_root.setScale(self.get_splash_ui_scale())

    def create_snowflakes(self, count):
        """Создаем падающие снежинки"""
        for i in range(count):
            # Создаем простую снежинку как маленький круг
            cm = CardMaker(f'snowflake_{i}')
            cm.setFrame(-0.01, 0.01, -0.01, 0.01)
            
            snowflake = self.game.aspect2d.attachNewNode(cm.generate())
            snowflake.setTransparency(TransparencyAttrib.MAlpha)
            
            # Случайная позиция
            x = random.uniform(-1.5, 1.5)
            y = random.uniform(-1.2, 1.2)
            snowflake.setPos(x, 0, y)
            
            # Случайная прозрачность и размер
            opacity = random.uniform(0.2, 0.6)
            size = random.uniform(0.8, 1.5)
            snowflake.setScale(size)
            snowflake.setColor(1, 1, 1, opacity)
            
            # Сохраняем скорость падения
            snowflake.setPythonTag('speed', random.uniform(0.1, 0.3))
            snowflake.setPythonTag('drift', random.uniform(-0.05, 0.05))
            
            self.snowflakes.append(snowflake)

    def update_snow(self, task):
        """Обновляем позицию снежинок"""
        dt = globalClock.getDt()
        
        for snowflake in self.snowflakes:
            if snowflake.isEmpty():
                continue
                
            current_pos = snowflake.getPos()
            speed = snowflake.getPythonTag('speed')
            drift = snowflake.getPythonTag('drift')
            
            # Двигаем снежинку вниз и немного в сторону
            new_z = current_pos.z - speed * dt
            new_x = current_pos.x + drift * dt
            
            # Если снежинка вышла за экран, возвращаем наверх
            if new_z < -1.2:
                new_z = 1.2
                new_x = random.uniform(-1.5, 1.5)
            
            snowflake.setPos(new_x, 0, new_z)
        
        return task.cont

    def start(self):
        """Запускаем анимацию загрузки"""
        # Инициализация прогресса
        self.current_progress = 0.0
        self.loading_complete = False
        
        self.sequence = Sequence(
            # Фаза 1: Показываем логотип автора
            Parallel(
                LerpColorScaleInterval(self.author_logo, 1.2, Vec4(1, 1, 1, 1), Vec4(1, 1, 1, 0), blendType='easeOut'),
                LerpColorScaleInterval(self.author_name, 1.2, Vec4(0.9, 0.9, 0.95, 1), Vec4(0.9, 0.9, 0.95, 0), blendType='easeOut')
            ),
            Wait(1.3),
            
            # Фаза 2: Убираем логотип автора
            Parallel(
                LerpColorScaleInterval(self.author_logo, 0.8, Vec4(1, 1, 1, 0), Vec4(1, 1, 1, 1), blendType='easeIn'),
                LerpColorScaleInterval(self.author_name, 0.8, Vec4(0.9, 0.9, 0.95, 0), Vec4(0.9, 0.9, 0.95, 1), blendType='easeIn')
            ),
            Wait(0.3),
            
            # Фаза 3: Показываем название игры и подзаголовок
            Parallel(
                LerpColorScaleInterval(self.game_title, 1.5, Vec4(1, 1, 1, 1), Vec4(1, 1, 1, 0), blendType='easeOut'),
                LerpScaleInterval(self.game_title, 1.5, 0.25, startScale=0.20, blendType='easeOut'),
                Sequence(
                    Wait(0.3),
                    LerpColorScaleInterval(self.subtitle, 1.2, Vec4(0.7, 0.7, 0.8, 1), Vec4(0.7, 0.7, 0.8, 0), blendType='easeOut')
                )
            ),
            Wait(0.8),
            
            # Фаза 4: Показываем прогресс бар и начинаем загрузку
            Parallel(
                LerpColorScaleInterval(self.loading_text, 0.6, Vec4(0.8, 0.8, 0.9, 1), Vec4(0.8, 0.8, 0.9, 0), blendType='easeOut'),
                LerpColorScaleInterval(self.progress_bg, 0.6, Vec4(0.15, 0.15, 0.25, 0.3), Vec4(0.15, 0.15, 0.25, 0), blendType='easeOut'),
                LerpColorScaleInterval(self.progress_fill, 0.6, Vec4(0.85, 0.85, 0.95, 1), Vec4(0.85, 0.85, 0.95, 0), blendType='easeOut')
            ),
            Func(self.start_loading),  # Начинаем реальную загрузку
            
            # Фаза 5: Ждем пока всё загрузится (будет управляться из start_loading)
        )
        self.sequence.start()

    def start_loading(self):
        """Начинаем реальную загрузку ресурсов"""
        self.loading_text.setText("loading resources")
        
        # Список ресурсов для загрузки
        self.resources_to_load = [
            ("Loading map", self.load_map),
            ("Loading fonts", self.load_fonts),
            ("Loading sounds", self.load_sounds),
            ("Loading textures", self.load_textures),
            ("Initializing game", self.init_game),
            ("Preparing menu", self.prepare_menu)
        ]
        
        self.total_resources = len(self.resources_to_load)
        self.current_resource = 0
        
        # Запускаем загрузку первого ресурса
        self.load_next_resource()

    def load_next_resource(self):
        """Загружаем следующий ресурс"""
        if self.current_resource >= self.total_resources:
            # Все загружено - завершаем
            self.finish_loading()
            return
        
        # Получаем текущий ресурс
        resource_name, resource_func = self.resources_to_load[self.current_resource]
        
        # Обновляем текст
        self.loading_text.setText(resource_name.lower())
        print(f"Loading {resource_name}...")

        # Загружаем ресурс
        try:
            resource_func()
        except Exception as e:
            print(f"Warning: Error loading {resource_name}: {e}")
        
        # Обновляем прогресс
        self.current_resource += 1
        new_progress = self.current_resource / self.total_resources
        
        # Анимируем прогресс бар с задержкой чтобы видеть процесс
        duration = 0.5  # Увеличили до 0.5 сек
        Sequence(
            Wait(0.2),  # Небольшая задержка чтобы видеть что грузится
            LerpScaleInterval(
                self.progress_fill, 
                duration,
                Vec3(new_progress, 1.0, 1.0),
                blendType='easeOut'
            ),
            Func(self.load_next_resource)  # После анимации - загружаем следующий
        ).start()

    def load_map(self):
        """Загружаем карту (уже загружена в main.py, просто имитируем)"""
        pass

    def load_fonts(self):
        """Прегружаем все кастомные шрифты"""
        import os
        try:
            # Создаем кэш для шрифтов
            if not hasattr(self.game, 'font_cache'):
                self.game.font_cache = {}
            
            fonts_dir = 'fonts'
            if os.path.exists(fonts_dir):
                font_files = [f for f in os.listdir(fonts_dir) if f.endswith('.ttf')]
                
                for font_file in font_files:
                    try:
                        font_path = os.path.join(fonts_dir, font_file).replace('\\', '/')
                        font = self.game.loader.loadFont(font_path)
                        if font:
                            # Сохраняем шрифт по имени (без расширения)
                            font_name = font_file.replace('.ttf', '')
                            self.game.font_cache[font_name] = font
                            print(f"OK: Загружен шрифт: {font_name}")
                    except Exception as e:
                        print(f"Warning: Не удалось загрузить {font_file}: {e}")
                
                # Список доступных шрифтов для настроек
                self.game.available_fonts = ['Default'] + list(self.game.font_cache.keys())
                print(f"OK: Всего шрифтов загружено: {len(self.game.font_cache)}")
            else:
                print("Warning: Папка fonts не найдена")
                self.game.available_fonts = ['Default']
                
        except Exception as e:
            print(f"Warning: Ошибка загрузки шрифтов: {e}")
            self.game.available_fonts = ['Default']

    def load_sounds(self):
        """Прегружаем все звуки"""
        try:
            # Кэш для звуков
            if not hasattr(self.game, 'sound_cache'):
                self.game.sound_cache = {}
            
            # Звуки оружия (убрали ui_click и ui_hover так как файлы отсутствуют)
            weapon_sounds = [
                "sounds/pistol_shot.wav",
                "sounds/rifle_shot.wav", 
                "sounds/sniper_shot.wav"
            ]
            
            for sound_path in weapon_sounds:
                try:
                    sound = self.game.loader.loadSfx(sound_path)
                    if sound:
                        self.game.sound_cache[sound_path] = sound
                        print(f"OK: Загружен звук: {sound_path}")
                except Exception as e:
                    print(f"Warning: Не удалось загрузить {sound_path}: {e}")
                    
        except Exception as e:
            print(f"Warning: Ошибка загрузки звуков: {e}")

    def load_textures(self):
        """Прегружаем текстуры если включен NSFW режим"""
        try:
            if self.game.settings.get('show_target_images', False):
                from managers.target import Target
                category = self.game.settings.get('nsfw_category', 'furry')
                Target.preload_category(self.game, category)
            from multiplayer.player_model import RemotePlayerModel
            RemotePlayerModel.preload_main_model(self.game)
        except Exception as e:
            print(f"Warning: Ошибка загрузки текстур: {e}")

    def init_game(self):
        """Инициализация игровых компонентов"""
        # Здесь можно добавить дополнительную инициализацию если нужно
        pass

    def prepare_menu(self):
        """Подготовка меню - создаем его здесь!"""
        try:
            print("Info: Создаем главное меню...")
            from menu_system.main_menu import MainMenu
            
            # Создаем меню заранее
            if self.game.menu is None:
                self.game.menu = MainMenu(self.game)
                print("OK: Главное меню создано!")
        except Exception as e:
            print(f"Warning: Ошибка создания меню: {e}")

    def finish_loading(self):
        """Завершаем загрузку и переходим к меню"""
        self.loading_text.setText("complete")
        
        # Финальная анимация fade out
        Sequence(
            Wait(0.3),
            Parallel(
                LerpColorScaleInterval(self.game_title, 1.0, Vec4(1, 1, 1, 0), Vec4(1, 1, 1, 1), blendType='easeIn'),
                LerpColorScaleInterval(self.subtitle, 1.0, Vec4(0.7, 0.7, 0.8, 0), Vec4(0.7, 0.7, 0.8, 1), blendType='easeIn'),
                LerpColorScaleInterval(self.loading_text, 1.0, Vec4(0.8, 0.8, 0.9, 0), Vec4(0.8, 0.8, 0.9, 1), blendType='easeIn'),
                LerpColorScaleInterval(self.progress_bg, 1.0, Vec4(0.15, 0.15, 0.25, 0), Vec4(0.15, 0.15, 0.25, 0.3), blendType='easeIn'),
                LerpColorScaleInterval(self.progress_fill, 1.0, Vec4(0.85, 0.85, 0.95, 0), Vec4(0.85, 0.85, 0.95, 1), blendType='easeIn')
            ),
            Func(self.cleanup),
            Func(self.show_main_menu)
        ).start()

    def mouse_task(self, task):
        """Keep mouse centered during splash screen"""
        if self.game.is_splash_screen_active:
            mw = self.game.mouseWatcherNode
            if mw.hasMouse():
                self.game.win.movePointer(0,
                                      int(self.game.win.getProperties().getXSize() / 2),
                                      int(self.game.win.getProperties().getYSize() / 2))
        return task.cont

    def cleanup(self):
        """Clean up splash screen resources"""
        if hasattr(self, 'mouse_task'):
            self.game.taskMgr.remove(self.mouse_task)
        if hasattr(self, 'snow_task'):
            self.game.taskMgr.remove(self.snow_task)
        
        for element in self.elements:
            if not element.isEmpty():
                element.removeNode()
        self.elements.clear()
        if hasattr(self, 'ui_root') and self.ui_root and not self.ui_root.isEmpty():
            self.ui_root.removeNode()

    def show_main_menu(self):
        """Show the main menu after splash screen"""
        if hasattr(self, 'mouse_task'):
            self.game.taskMgr.remove(self.mouse_task)
            
        if hasattr(self.game, 'show_main_menu'):
            self.game.is_splash_screen_active = False
            
            # Reset window properties for main menu
            props = WindowProperties()
            props.setCursorHidden(False)
            props.setMouseMode(WindowProperties.MAbsolute)
            self.game.win.requestProperties(props)
            
            self.game.show_main_menu()
            self.game.splash = None
