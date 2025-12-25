"""
Главное меню игры с модульной системой настроек
"""
from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel, DGG
from panda3d.core import TextNode, WindowProperties, Vec3, Point3, NodePath
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpScaleInterval, LerpPosInterval, Wait, LerpColorScaleInterval, Func
from direct.filter.CommonFilters import CommonFilters
import random

from .graphics_tab import GraphicsTab
from .controls_tab import ControlsTab
from .weapon_tab import WeaponTab
from .game_tab import GameTab
from .audio_tab import AudioTab
from .postprocess_tab import PostProcessTab

class MainMenu:
    def __init__(self, game):
        self.game = game
        self.frame = None
        self.settings_frame = None
        self.settings_visible = False
        self.menu_buttons = []
        self.background_objects = []
        
        self.hover_sound = None
        self.click_sound = None
        
        self.current_resolution = self.game.settings.get('resolution', '1280x720')
        self.resolutions = self.get_supported_resolutions()
        
        self.create_dynamic_background()
        self.create_menu()
        self.create_settings_menu()
        
        self.initial_hide()
    
    def get_supported_resolutions(self):
        """Получает список поддерживаемых разрешений"""
        all_resolutions = [
            # 4:3
            "640x480", "800x600", "1024x768", "1280x960", "1600x1200",
            # 16:9
            "640x360", "854x480", "1024x576", "1280x720", "1366x768",
            "1600x900", "1920x1080", "2560x1440", "3840x2160",
            # 16:10
            "1280x800", "1440x900", "1680x1050", "1920x1200", "2560x1600",
            # 5:4
            "1280x1024",
            # 21:9
            "2560x1080", "3440x1440", "5120x2160"
        ]
        
        resolutions = []
        display_info = self.game.pipe.getDisplayInformation()
        
        max_width = 0
        max_height = 0
        
        for i in range(display_info.getTotalDisplayModes()):
            display_mode = display_info.getDisplayMode(i)
            width = display_mode.width
            height = display_mode.height
            if width > max_width:
                max_width = width
            if height > max_height:
                max_height = height
        
        if max_width == 0 or max_height == 0:
            max_width = 1920
            max_height = 1080
        
        for res in all_resolutions:
            width, height = map(int, res.split('x'))
            if width <= max_width and height <= max_height:
                resolutions.append(res)
        
        if self.current_resolution not in resolutions and resolutions:
            current_width, current_height = map(int, self.current_resolution.split('x'))
            min_diff = float('inf')
            best_res = '1280x720'
            
            for res in resolutions:
                w, h = map(int, res.split('x'))
                diff = abs(w - current_width) + abs(h - current_height)
                if diff < min_diff:
                    min_diff = diff
                    best_res = res
            
            self.current_resolution = best_res
            self.game.settings['resolution'] = best_res
            self.game.settings['windowed_resolution'] = best_res
            self.game.save_settings()
        
        return resolutions if resolutions else ['1280x720']
    
    def create_dynamic_background(self):
        """Создает динамический 3D фон"""
        self.bg_root = self.game.render.attachNewNode("menu_background")
        self.bg_root.setPos(0, 50, 0)
        
        for i in range(8):
            obj = self.game.safe_load_model("models/box")
            obj.reparentTo(self.bg_root)
            
            x = random.uniform(-20, 20)
            y = random.uniform(-10, 30)
            z = random.uniform(-10, 10)
            obj.setPos(x, y, z)
            
            scale = random.uniform(0.5, 2.0)
            obj.setScale(scale)
            
            r = random.uniform(0.1, 0.3)
            g = random.uniform(0.2, 0.4)
            b = random.uniform(0.3, 0.6)
            obj.setColor(r, g, b, 0.6)
            
            obj.setTransparency(1)
            
            duration = random.uniform(15, 30)
            rotation_hpr = Vec3(
                random.uniform(0, 360),
                random.uniform(0, 360),
                random.uniform(0, 360)
            )
            
            rotation_interval = obj.hprInterval(
                duration,
                obj.getHpr() + rotation_hpr,
                blendType='noBlend'
            )
            
            move_duration = random.uniform(20, 40)
            start_pos = obj.getPos()
            end_pos = Point3(
                start_pos.x + random.uniform(-5, 5),
                start_pos.y + random.uniform(-5, 5),
                start_pos.z + random.uniform(-3, 3)
            )
            
            move_interval = Sequence(
                obj.posInterval(move_duration, end_pos, start_pos, blendType='easeInOut'),
                obj.posInterval(move_duration, start_pos, end_pos, blendType='easeInOut')
            )
            
            rotation_interval.loop()
            move_interval.loop()
            
            self.background_objects.append(obj)
        
        self.bg_filters = CommonFilters(self.game.win, self.game.cam)
        self.bg_filters.setBloom(blend=(0.3, 0.4, 0.5, 0.0), desat=-0.5, intensity=1.0, size="small")
    
    def create_menu(self):
        """Создает главное меню"""
        self.dark_bg = DirectFrame(
            frameColor=(0.05, 0.05, 0.05, 0.9),
            frameSize=(-2, 2, -2, 2),
            relief=DGG.FLAT,
            parent=self.game.render2d
        )
        
        self.frame = DirectFrame(
            frameColor=(0.08, 0.08, 0.12, 0.98),
            frameSize=(-0.6, 0.6, -0.5, 0.5),
            relief=DGG.FLAT,
            borderWidth=(0.005, 0.005),
            pos=(0, 0, 0)
        )
        
        self.top_line = DirectFrame(
            frameColor=(0.3, 0.5, 1, 0.8),
            frameSize=(-0.55, 0.55, -0.002, 0.002),
            relief=DGG.FLAT,
            pos=(0, 0, 0.48),
            parent=self.frame
        )
        
        self.bottom_line = DirectFrame(
            frameColor=(0.3, 0.5, 1, 0.8),
            frameSize=(-0.55, 0.55, -0.002, 0.002),
            relief=DGG.FLAT,
            pos=(0, 0, -0.48),
            parent=self.frame
        )
        
        self.title = DirectLabel(
            text="AIM TRAINER",
            scale=0.12,
            pos=(0, 0, 0.35),
            parent=self.frame,
            text_fg=(0.9, 0.95, 1, 1),
            text_align=TextNode.ACenter,
            text_shadow=(0.2, 0.4, 0.8, 0.8),
            text_shadowOffset=(0.003, -0.003),
            frameColor=(0, 0, 0, 0)
        )
        
        self.subtitle = DirectLabel(
            text="TRAIN YOUR PRECISION",
            scale=0.04,
            pos=(0, 0, 0.24),
            parent=self.frame,
            text_fg=(0.5, 0.6, 0.8, 1),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0)
        )
        
        self.title_animation = Sequence(
            LerpScaleInterval(self.title, 2.0, 0.13, blendType='easeInOut'),
            LerpScaleInterval(self.title, 2.0, 0.12, blendType='easeInOut'),
        )
        self.title_animation.loop()
        
        button_style = {
            'relief': DGG.FLAT,
            'borderWidth': (0, 0),
            'frameSize': (-0.3, 0.3, -0.045, 0.045),
            'text_scale': 0.05,
            'text_fg': (0.95, 0.95, 0.95, 1),
            'pressEffect': 0
        }
        
        self.play_button = DirectButton(
            text="PLAY",
            command=self.start_game,
            pos=(0, 0, 0.12),
            parent=self.frame,
            frameColor=(0.2, 0.4, 0.9, 0.9),
            **button_style
        )
        self.menu_buttons.append(self.play_button)
        
        self.multiplayer_button = DirectButton(
            text="MULTIPLAYER",
            command=self.show_multiplayer,
            pos=(0, 0, 0.0),
            parent=self.frame,
            frameColor=(0.3, 0.5, 0.2, 0.9),
            **button_style
        )
        self.menu_buttons.append(self.multiplayer_button)
        
        self.settings_button = DirectButton(
            text="SETTINGS",
            command=self.toggle_settings,
            pos=(0, 0, -0.12),
            parent=self.frame,
            frameColor=(0.15, 0.15, 0.2, 0.9),
            **button_style
        )
        self.menu_buttons.append(self.settings_button)
        
        self.exit_button = DirectButton(
            text="EXIT",
            command=self.exit_game,
            pos=(0, 0, -0.24),
            parent=self.frame,
            frameColor=(0.15, 0.15, 0.2, 0.9),
            **button_style
        )
        self.menu_buttons.append(self.exit_button)
        
        for button in self.menu_buttons:
            button.bind(DGG.ENTER, self.button_hover_start, [button])
            button.bind(DGG.EXIT, self.button_hover_end, [button])
        
        self.version_label = DirectLabel(
            text="v1.0",
            scale=0.04,
            pos=(0.5, 0, -0.43),
            parent=self.frame,
            text_fg=(0.4, 0.4, 0.5, 1),
            text_align=TextNode.ARight,
            frameColor=(0, 0, 0, 0)
        )
    
    def create_settings_menu(self):
        """Создает меню настроек с модульными вкладками"""
        self.settings_frame = DirectFrame(
            frameColor=(0.08, 0.08, 0.12, 0.95),
            frameSize=(-0.9, 0.9, -0.65, 0.65),
            relief=DGG.FLAT,
            borderWidth=(0, 0),
            pos=(0, 0, 0)
        )
        self.settings_frame.hide()
        
        self.settings_title = DirectLabel(
            text="SETTINGS",
            scale=0.08,
            pos=(0, 0, 0.55),
            parent=self.settings_frame,
            text_fg=(0.9, 0.95, 1, 1),
            text_align=TextNode.ACenter,
            text_shadow=(0.2, 0.4, 0.8, 0.8),
            text_shadowOffset=(0.003, -0.003),
            frameColor=(0, 0, 0, 0),
            relief=None
        )
        
        self.categories_container = DirectFrame(
            frameColor=(0.12, 0.14, 0.17, 0),
            frameSize=(-0.2, 0.2, -0.6, 0.6),
            pos=(-0.65, 0, 0.1),
            parent=self.settings_frame
        )
        
        self.tabs = {
            'graphics': GraphicsTab(self.game, self.settings_frame, self.resolutions),
            'controls': ControlsTab(self.game, self.settings_frame),
            'weapon': WeaponTab(self.game, self.settings_frame),
            'game': GameTab(self.game, self.settings_frame),
            'audio': AudioTab(self.game, self.settings_frame),
            'postprocess': PostProcessTab(self.game, self.settings_frame, self.bg_filters)
        }
        
        for key, tab in self.tabs.items():
            tab.hide()
        self.tabs['graphics'].show()
        
        self.tab_buttons = []
        category_data = [
            ('Graphics', 'graphics'),
            ('Controls', 'controls'),
            ('Weapon', 'weapon'),
            ('Game', 'game'),
            ('Audio', 'audio'),
            ('Post-Processing', 'postprocess')
        ]
        
        category_button_style = {
            'relief': DGG.FLAT,
            'borderWidth': (0, 0),
            'frameSize': (-0.18, 0.18, -0.045, 0.045),
            'text_scale': 0.045,
            'text_fg': (0.95, 0.95, 0.95, 1),
            'frameColor': (0.15, 0.15, 0.2, 0.9),
            'pressEffect': 0
        }
        
        for i, (display_name, frame_key) in enumerate(category_data):
            button = DirectButton(
                text=display_name,
                parent=self.categories_container,
                pos=(0, 0, 0.3 - i * 0.11),
                command=self.on_tab_changed,
                extraArgs=[frame_key],
                **category_button_style
            )
            self.tab_buttons.append(button)
        
        self.on_tab_changed('graphics')
        
        self.back_button = DirectButton(
            text="Back",
            pos=(0, 0, -0.82),
            parent=self.settings_frame,
            command=self.toggle_settings,
            frameColor=(0.2, 0.4, 0.9, 0.9),
            relief=DGG.FLAT,
            borderWidth=(0, 0),
            frameSize=(-0.25, 0.25, -0.04, 0.04),
            text_scale=0.045,
            text_fg=(0.9, 0.9, 0.9, 1),
            pressEffect=0
        )
        self.back_button.bind(DGG.ENTER, self.button_hover_start, [self.back_button])
        self.back_button.bind(DGG.EXIT, self.button_hover_end, [self.back_button])
    
    def on_tab_changed(self, tab_name):
        """Обработчик смены вкладки"""
        category_data = [
            ('Graphics', 'graphics'),
            ('Controls', 'controls'),
            ('Weapon', 'weapon'),
            ('Game', 'game'),
            ('Audio', 'audio'),
            ('Post-Processing', 'postprocess')
        ]
        
        for i, button in enumerate(self.tab_buttons):
            if i < len(category_data) and category_data[i][1] == tab_name:
                button['frameColor'] = (0.2, 0.4, 0.9, 0.9)
            else:
                button['frameColor'] = (0.15, 0.15, 0.2, 0.9)
        
        for tab in self.tabs.values():
            tab.hide()
        
        if tab_name in self.tabs:
            self.tabs[tab_name].show()
    
    def button_hover_start(self, button, event):
        """Эффект при наведении"""
        if self.hover_sound:
            self.hover_sound.play()
        
        Parallel(
            LerpColorScaleInterval(button, 0.2, (1.2, 1.2, 1.2, 1), blendType='easeOut'),
            LerpScaleInterval(button, 0.2, 1.08, blendType='easeOut')
        ).start()
        
        if button == self.play_button:
            button['frameColor'] = (0.3, 0.5, 1, 1)
        else:
            button['frameColor'] = (0.25, 0.3, 0.4, 1)
    
    def button_hover_end(self, button, event):
        """Эффект при отведении курсора"""
        Parallel(
            LerpColorScaleInterval(button, 0.2, (1, 1, 1, 1), blendType='easeIn'),
            LerpScaleInterval(button, 0.2, 1.0, blendType='easeIn')
        ).start()
        
        if button == self.play_button:
            button['frameColor'] = (0.2, 0.4, 0.9, 0.9)
        else:
            button['frameColor'] = (0.15, 0.15, 0.2, 0.9)
    
    def toggle_settings(self):
        """Переключает видимость настроек"""
        if self.click_sound:
            self.click_sound.play()
        
        if not self.settings_visible:
            self.settings_frame.show()
            self.frame.hide()
            self.title.hide()
            for button in self.menu_buttons:
                button.hide()
            self.settings_visible = True
        else:
            self.settings_frame.hide()
            self.settings_visible = False
            
            if hasattr(self.game, 'pause_menu') and self.game.pause_menu and self.game.pause_menu.is_paused:
                self.game.pause_menu.show()
            else:
                self.frame.show()
                self.title.show()
                for button in self.menu_buttons:
                    button.show()
            
            self.game.save_settings()
    
    def initial_hide(self):
        """Скрываем меню при создании (без анимации)"""
        if hasattr(self, 'dark_bg'):
            self.dark_bg.hide()
        if hasattr(self, 'frame'):
            self.frame.hide()
    
    def show(self):
        """Показать меню"""
        self.dark_bg.show()
        self.frame.show()
        
        props = WindowProperties()
        props.setCursorHidden(False)
        self.game.win.requestProperties(props)
        
        self.frame.setColorScale(1, 1, 1, 0)
        self.dark_bg.setColorScale(1, 1, 1, 0)
        Parallel(
            LerpColorScaleInterval(self.frame, 0.4, (1, 1, 1, 1)),
            LerpColorScaleInterval(self.dark_bg, 0.4, (1, 1, 1, 1))
        ).start()
    
    def hide(self):
        """Скрыть меню"""
        hide_sequence = Sequence(
            Parallel(
                LerpColorScaleInterval(self.frame, 0.3, (1, 1, 1, 0)),
                LerpColorScaleInterval(self.dark_bg, 0.3, (1, 1, 1, 0))
            ),
            Func(self.frame.hide),
            Func(self.dark_bg.hide)
        )
        hide_sequence.start()
        self.title_animation.pause()
    
    def show_multiplayer(self):
        """Открыть меню мультиплеера"""
        if self.click_sound:
            self.click_sound.play()
        
        self.game.show_multiplayer_menu()
    
    def start_game(self):
        """Запустить игру"""
        if self.click_sound:
            self.click_sound.play()
        
        self.hide()
        taskMgr.doMethodLater(0.3, self._start_game_delayed, 'start_game_delayed')
    
    def _start_game_delayed(self, task):
        """Отложенный запуск игры"""
        self.frame.hide()
        self.game.start_game()
        return task.done
    
    def exit_game(self):
        """Выйти из игры"""
        if self.click_sound:
            self.click_sound.play()
        
        self.game.userExit()
    
    def cleanup(self):
        """Очистить ресурсы меню"""
        for obj in self.background_objects:
            obj.removeNode()
        self.background_objects.clear()
        
        if hasattr(self, 'bg_root'):
            self.bg_root.removeNode()
        
        if hasattr(self, 'bg_filters'):
            self.bg_filters.delBloom()
        
        if self.frame:
            self.title_animation.pause()
            self.frame.destroy()
        
        for tab in self.tabs.values():
            tab.cleanup()

