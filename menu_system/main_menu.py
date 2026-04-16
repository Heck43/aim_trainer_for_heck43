"""
Главное меню игры с модульной системой настроек
минималистичный дизайн~~
"""
from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel, DGG
from panda3d.core import TextNode, WindowProperties, Vec3, Point3, NodePath
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpScaleInterval, LerpPosInterval, Wait, LerpColorScaleInterval, Func
import random

from .graphics_tab import GraphicsTab
from .controls_tab import ControlsTab
from .weapon_tab import WeaponTab
from .game_tab import GameTab
from .audio_tab import AudioTab
from .ui_helpers import get_resolution_ui_scale
from .gradient_bg import GradientBackground

# цвета
DARK_BG = (0.11, 0.11, 0.12, 0.95)
DARKER_BG = (0.17, 0.17, 0.18, 0.98)
TEXT_PRIMARY = (0.90, 0.90, 0.91, 1.0)
TEXT_SECONDARY = (0.68, 0.68, 0.70, 1.0)
BORDER_LIGHT = (0.3, 0.3, 0.3, 0.5)
BUTTON_NORMAL = (0.2, 0.2, 0.21, 0.9)
BUTTON_PRIMARY = (1.0, 0.58, 0.0, 0.9)

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
        self.ui_root = self.game.aspect2d.attachNewNode("main_menu_ui_root")
        self._layout_task_name = "main_menu_refresh_layout"
        
        self.current_resolution = self.game.settings.get('resolution', '1280x720')
        self.resolutions = self.get_supported_resolutions()

        self.gradient_bg = GradientBackground(self.game)
        self.create_menu()
        self.create_settings_menu()
        self.update_layout()

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
            self.game.settings_manager.save_settings()
        
        return resolutions if resolutions else ['1280x720']

    def update_layout(self):
        """Recomputes menu scale for the current window size."""
        if not self.ui_root or self.ui_root.isEmpty():
            return
        self.ui_root.setScale(get_resolution_ui_scale(self.game))

    def schedule_layout_refresh(self, delay=0.05):
        """Refresh layout after Panda3D applies new window properties."""
        try:
            self.game.taskMgr.remove(self._layout_task_name)
        except Exception:
            pass
        self.game.taskMgr.doMethodLater(delay, self._deferred_layout_refresh, self._layout_task_name)

    def _deferred_layout_refresh(self, task):
        self.update_layout()
        if hasattr(self.game, "pause_menu") and self.game.pause_menu:
            self.game.pause_menu.update_layout()
        return task.done
    
        
    def create_menu(self):
        """создаёт главное меню в минималистичном стиле~~"""
        print("DEBUG: создаём меню...")

        self.dark_bg = DirectFrame(
            frameColor=DARK_BG,
            frameSize=(-2, 2, -2, 2),
            relief=DGG.FLAT,
            parent=self.game.render2d
        )
        print("DEBUG: dark_bg создан")

        self.frame = DirectFrame(
            frameColor=DARKER_BG,
            frameSize=(-0.5, 0.5, -0.55, 0.55),
            relief=DGG.FLAT,
            borderWidth=(0, 0),
            pos=(0, 0, 0),
            parent=self.ui_root
        )
        print("DEBUG: frame создан")

        # заголовок
        self.title = DirectLabel(
            text="AIM TRAINER",
            scale=0.1,
            pos=(0, 0, 0.4),
            parent=self.frame,
            text_fg=TEXT_PRIMARY,
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            relief=None
        )
        print("DEBUG: title создан")

        # тонкая линия под заголовком
        self.title_line = DirectFrame(
            frameColor=BORDER_LIGHT,
            frameSize=(-0.3, 0.3, -0.001, 0.001),
            relief=DGG.FLAT,
            pos=(0, 0, 0.32),
            parent=self.frame
        )
        print("DEBUG: title_line создан")

        # стиль кнопок
        button_style = {
            'relief': DGG.FLAT,
            'borderWidth': (0, 0),
            'frameSize': (-0.35, 0.35, -0.05, 0.05),
            'text_scale': 0.045,
            'text_fg': TEXT_PRIMARY,
            'pressEffect': 0
        }

        # кнопки обычным способом
        self.play_button = DirectButton(
            text="PLAY",
            command=self.start_game,
            pos=(0, 0, 0.15),
            parent=self.frame,
            frameColor=(1.0, 0.58, 0.0, 0.9),  # оранжевая
            **button_style
        )
        self.menu_buttons.append(self.play_button)
        print("DEBUG: play_button создан")

        self.multiplayer_button = DirectButton(
            text="MULTIPLAYER",
            command=self.show_multiplayer,
            pos=(0, 0, 0.0),
            parent=self.frame,
            frameColor=(0.2, 0.2, 0.21, 0.9),  # серая
            **button_style
        )
        self.menu_buttons.append(self.multiplayer_button)
        print("DEBUG: multiplayer_button создан")

        self.settings_button = DirectButton(
            text="SETTINGS",
            command=self.toggle_settings,
            pos=(0, 0, -0.15),
            parent=self.frame,
            frameColor=(0.2, 0.2, 0.21, 0.9),  # серая
            **button_style
        )
        self.menu_buttons.append(self.settings_button)
        print("DEBUG: settings_button создан")

        self.exit_button = DirectButton(
            text="EXIT",
            command=self.exit_game,
            pos=(0, 0, -0.30),
            parent=self.frame,
            frameColor=(1.0, 0.23, 0.19, 0.9),  # красная
            **button_style
        )
        self.menu_buttons.append(self.exit_button)
        print("DEBUG: exit_button создан")

        # привязываем hover эффекты
        for button in self.menu_buttons:
            button.bind(DGG.ENTER, self.button_hover_start, [button])
            button.bind(DGG.EXIT, self.button_hover_end, [button])

        # версия
        self.version_label = DirectLabel(
            text="v2.3.2",
            scale=0.035,
            pos=(0.42, 0, -0.48),
            parent=self.frame,
            text_fg=TEXT_SECONDARY,
            text_align=TextNode.ARight,
            frameColor=(0, 0, 0, 0),
            relief=None
        )
        print("DEBUG: version_label создан")
        print(f"DEBUG: всего кнопок создано: {len(self.menu_buttons)}")
    
    def create_settings_menu(self):
        """создаёт меню настроек с модульными вкладками~~"""
        self.settings_frame = DirectFrame(
            frameColor=DARKER_BG,
            frameSize=(-0.9, 0.9, -0.65, 0.65),
            relief=DGG.FLAT,
            borderWidth=(0, 0),
            pos=(0, 0, 0),
            parent=self.ui_root
        )
        self.settings_frame.hide()

        self.settings_title = DirectLabel(
            text="SETTINGS",
            scale=0.08,
            pos=(0, 0, 0.55),
            parent=self.settings_frame,
            text_fg=TEXT_PRIMARY,
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            relief=None
        )

        # линия под заголовком
        self.settings_title_line = DirectFrame(
            frameColor=BORDER_LIGHT,
            frameSize=(-0.3, 0.3, -0.001, 0.001),
            relief=DGG.FLAT,
            pos=(0, 0, 0.48),
            parent=self.settings_frame
        )

        self.categories_container = DirectFrame(
            frameColor=(0, 0, 0, 0),
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
        ]

        category_button_style = {
            'relief': DGG.FLAT,
            'borderWidth': (0, 0),
            'frameSize': (-0.18, 0.18, -0.045, 0.045),
            'text_scale': 0.045,
            'text_fg': TEXT_PRIMARY,
            'frameColor': (0.2, 0.2, 0.21, 0.9),
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
            frameColor=BUTTON_PRIMARY,
            relief=DGG.FLAT,
            borderWidth=(0, 0),
            frameSize=(-0.25, 0.25, -0.04, 0.04),
            text_scale=0.045,
            text_fg=TEXT_PRIMARY,
            pressEffect=0
        )
        self.back_button.bind(DGG.ENTER, self.button_hover_start, [self.back_button])
        self.back_button.bind(DGG.EXIT, self.button_hover_end, [self.back_button])
    
    def on_tab_changed(self, tab_name):
        """обработчик смены вкладки~~"""
        category_data = [
            ('Graphics', 'graphics'),
            ('Controls', 'controls'),
            ('Weapon', 'weapon'),
            ('Game', 'game'),
            ('Audio', 'audio'),
        ]

        for i, button in enumerate(self.tab_buttons):
            if i < len(category_data) and category_data[i][1] == tab_name:
                button['frameColor'] = (1.0, 0.58, 0.0, 0.9)  # оранжевая для активной
            else:
                button['frameColor'] = (0.2, 0.2, 0.21, 0.9)  # серая для неактивной

        for tab in self.tabs.values():
            tab.hide()

        if tab_name in self.tabs:
            self.tabs[tab_name].show()
    
    def button_hover_start(self, button, event):
        """эффект при наведении (для старых кнопок в настройках)~~"""
        if self.hover_sound:
            self.hover_sound.play()

        Parallel(
            LerpColorScaleInterval(button, 0.15, (1.1, 1.1, 1.1, 1), blendType='easeOut'),
            LerpScaleInterval(button, 0.15, 1.02, blendType='easeOut')
        ).start()

    def button_hover_end(self, button, event):
        """эффект при отведении курсора (для старых кнопок в настройках)~~"""
        Parallel(
            LerpColorScaleInterval(button, 0.15, (1, 1, 1, 1), blendType='easeIn'),
            LerpScaleInterval(button, 0.15, 1.0, blendType='easeIn')
        ).start()
    
    def toggle_settings(self):
        """Переключает видимость настроек"""
        if self.click_sound:
            self.click_sound.play()
        
        if not self.settings_visible:
            self.update_layout()
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
            
            self.game.settings_manager.save_settings()
    
    def initial_hide(self):
        """Скрываем меню при создании (без анимации)"""
        if hasattr(self, 'dark_bg'):
            self.dark_bg.hide()
        if hasattr(self, 'frame'):
            self.frame.hide()
    
    def show(self):
        """показать меню~~"""
        self.update_layout()
        self.gradient_bg.show()
        self.dark_bg.show()
        self.frame.show()

        # показываем все кнопки явно
        for button in self.menu_buttons:
            button.show()
        if hasattr(self, 'title'):
            self.title.show()
        if hasattr(self, 'title_line'):
            self.title_line.show()
        if hasattr(self, 'version_label'):
            self.version_label.show()

        props = WindowProperties()
        props.setCursorHidden(False)
        self.game.win.requestProperties(props)

        self.frame.setColorScale(1, 1, 1, 0)
        self.dark_bg.setColorScale(1, 1, 1, 0)
        Parallel(
            LerpColorScaleInterval(self.frame, 0.3, (1, 1, 1, 1)),
            LerpColorScaleInterval(self.dark_bg, 0.3, (1, 1, 1, 1))
        ).start()

    def hide(self):
        """скрыть меню~~"""
        hide_sequence = Sequence(
            Parallel(
                LerpColorScaleInterval(self.frame, 0.2, (1, 1, 1, 0)),
                LerpColorScaleInterval(self.dark_bg, 0.2, (1, 1, 1, 0))
            ),
            Func(self.frame.hide),
            Func(self.dark_bg.hide),
            Func(self.gradient_bg.hide)
        )
        hide_sequence.start()
    
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
        """очистить ресурсы меню~~"""
        try:
            self.game.taskMgr.remove(self._layout_task_name)
        except Exception:
            pass

        if hasattr(self, 'gradient_bg'):
            self.gradient_bg.cleanup()

        if self.frame:
            self.frame.destroy()

        for tab in self.tabs.values():
            tab.cleanup()

        if self.ui_root and not self.ui_root.isEmpty():
            self.ui_root.removeNode()
