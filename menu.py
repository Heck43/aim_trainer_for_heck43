from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel, DGG, DirectSlider, DirectCheckButton, DirectOptionMenu
from panda3d.core import TextNode, WindowProperties
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpScaleInterval, LerpPosInterval, Wait
from direct.task import Task
import os

class MainMenu:
    def __init__(self, game):
        self.game = game
        self.frame = None
        self.settings_frame = None
        self.settings_visible = False
        self.menu_buttons = []  # Список для хранения кнопок меню
        
        # Получаем поддерживаемые разрешения от системы
        display_info = self.game.pipe.getDisplayInformation()
        
        # Стандартные разрешения и их широкоэкранные варианты
        standard_resolutions = {
            # 4:3 и их широкоэкранные варианты
            "640x480",    # VGA
            "800x600",    # SVGA
            "960x600",    # Широкий SVGA
            "1024x768",   # XGA
            "1280x768",   # Широкий XGA
            
            # Стандартные широкоэкранные
            "1280x720",   # HD
            "1360x768",   # HD
            "1366x768",   # HD
            "1600x900",   # HD+
            "1920x1080",  # Full HD
            
            # 16:10
            "1280x800",
            "1440x900",
            "1680x1050",
            
            # 5:4
            "1280x1024"
        }
        
        # Получаем поддерживаемые разрешения от системы
        supported_modes = set()
        for i in range(display_info.getTotalDisplayModes()):
            mode = display_info.getDisplayMode(i)
            supported_modes.add(f"{mode.width}x{mode.height}")
        
        # Объединяем стандартные разрешения с поддерживаемыми системой
        self.resolutions = sorted(list(standard_resolutions.union(supported_modes)),
                                key=lambda x: (int(x.split('x')[1]), int(x.split('x')[0])))
        
        # Если текущее разрешение не поддерживается, используем ближайшее поддерживаемое
        self.current_resolution = self.game.settings.get('resolution', '1280x720')
        if self.current_resolution not in self.resolutions:
            # Находим ближайшее поддерживаемое разрешение
            current_width, current_height = map(int, self.current_resolution.split('x'))
            min_diff = float('inf')
            best_res = '1280x720'  # значение по умолчанию
            
            for res in self.resolutions:
                w, h = map(int, res.split('x'))
                diff = abs(w - current_width) + abs(h - current_height)
                if diff < min_diff:
                    min_diff = diff
                    best_res = res
            
            self.current_resolution = best_res
            self.game.settings['resolution'] = best_res
            self.game.settings['windowed_resolution'] = best_res
            self.game.save_settings()
            
        # Загружаем текущую чувствительность мыши
        self.current_sensitivity = self.game.settings.get('sensitivity', self.game.DEFAULT_SETTINGS['sensitivity'])
        
        self.create_menu()
        self.create_settings_menu()
        
    def create_menu(self):
        # Создаем основной фрейм меню
        self.frame = DirectFrame(
            frameColor=(0.1, 0.1, 0.1, 0.8),
            frameSize=(-0.7, 0.7, -0.7, 0.7),
            pos=(0, 0, 2)  # Начальная позиция выше экрана для анимации
        )
        
        # Заголовок
        self.title = DirectLabel(
            text="Aim Training",
            scale=0.15,
            pos=(0, 0, 0.4),
            parent=self.frame,
            text_fg=(1, 1, 1, 1),
            text_align=TextNode.ACenter
        )
        
        # Анимация заголовка
        self.title_animation = Sequence(
            LerpScaleInterval(self.title, 1.0, 0.17),
            LerpScaleInterval(self.title, 1.0, 0.13),
        )
        self.title_animation.loop()
        
        # Кнопка "Play"
        button_style = {
            'frameColor': (0.1, 0.1, 0.1, 0.8),  # Темный фон
            'relief': DGG.RIDGE,  # Рельефный стиль для границ
            'borderWidth': (0.02, 0.02),  # Толщина границ
            'frameSize': (-0.3, 0.3, -0.05, 0.05),  # Размер кнопки
            'text_scale': 0.05,  # Размер текста
            'text_fg': (1, 1, 1, 1),  # Белый текст
            'text_align': TextNode.ACenter,  # Центрирование текста
            'pressEffect': 1  # Эффект нажатия
        }
        self.play_button = DirectButton(
            text="Play",
            command=self.start_game,
            pos=(0, 0, 0.1),
            parent=self.frame,
            **button_style
        )
        self.menu_buttons.append(self.play_button)

        # Кнопка "Settings"
        self.settings_button = DirectButton(
            text="Settings",
            command=self.toggle_settings,
            pos=(0, 0, 0),
            parent=self.frame,
            **button_style
        )
        self.menu_buttons.append(self.settings_button)

        # Кнопка "Exit"
        self.exit_button = DirectButton(
            text="Exit",
            command=self.exit_game,
            pos=(0, 0, -0.1),
            parent=self.frame,
            **button_style
        )
        self.menu_buttons.append(self.exit_button)

        # Добавляем эффекты при наведении для всех кнопок
        for button in self.menu_buttons:
            button.bind(DGG.ENTER, self.button_hover_on, [button])
            button.bind(DGG.EXIT, self.button_hover_off, [button])

    def button_hover_on(self, button, event):
        """Эффект при наведении на кнопку"""
        button['frameColor'] = (0.15, 0.15, 0.15, 0.9)  # Немного светлее при наведении

    def button_hover_off(self, button, event):
        """Эффект при отведении курсора от кнопки"""
        button['frameColor'] = (0.1, 0.1, 0.1, 0.8)  # Возврат к исходному цвету

    def create_settings_menu(self):
        # Стили для элементов настроек
        self.settings_style = {
            'frameColor': (0.1, 0.1, 0.1, 0.8),
            'relief': DGG.RIDGE,
            'borderWidth': (0.02, 0.02),
            'text_fg': (1, 1, 1, 1),
            'text_scale': 0.05,
            'text_align': TextNode.ALeft
        }
        
        self.slider_style = {
            'frameColor': (0.15, 0.15, 0.15, 0.9),
            'relief': DGG.RIDGE,
            'borderWidth': (0.02, 0.02),
            'thumb_frameColor': (0.3, 0.3, 0.3, 1),
            'thumb_relief': DGG.RAISED,
            'scale': 0.5,
            'text_fg': (1, 1, 1, 1)
        }
        
        self.button_style = {
            'frameColor': (0.1, 0.1, 0.1, 0.8),
            'relief': DGG.RIDGE,
            'borderWidth': (0.02, 0.02),
            'frameSize': (-0.3, 0.3, -0.05, 0.05),
            'text_scale': 0.05,
            'text_fg': (1, 1, 1, 1),
            'text_align': TextNode.ACenter,
            'pressEffect': 1
        }

        # Создаем фрейм настроек с темным фоном и белыми границами
        self.settings_frame = DirectFrame(
            frameColor=(0.08, 0.08, 0.08, 0.9),
            frameSize=(-0.8, 0.8, -0.6, 0.6),
            relief=DGG.RIDGE,
            borderWidth=(0.02, 0.02),
            pos=(0, 0, 0)
        )
        self.settings_frame.hide()

        # Create notebook (tabbed interface)
        self.notebook = DirectNotebook(
            pos=(0, 0, 0),
            scale=1.0,
            parent=self.settings_frame,
            frameSize=(-0.7, 0.7, -0.5, 0.5)  # Adding explicit frameSize
        )

        # Create tabs
        graphics_tab = DirectTab(
            parent=self.notebook,
            relief=None,
            frameColor=(0.1, 0.1, 0.1, 0.9),
            frameSize=(-0.7, 0.7, -0.5, 0.5)
        )
        controls_tab = DirectTab(
            parent=self.notebook,
            relief=None,
            frameColor=(0.1, 0.1, 0.1, 0.9),
            frameSize=(-0.7, 0.7, -0.5, 0.5)
        )
        weapon_tab = DirectTab(
            parent=self.notebook,
            relief=None,
            frameColor=(0.1, 0.1, 0.1, 0.9),
            frameSize=(-0.7, 0.7, -0.5, 0.5)
        )
        game_tab = DirectTab(
            parent=self.notebook,
            relief=None,
            frameColor=(0.1, 0.1, 0.1, 0.9),
            frameSize=(-0.7, 0.7, -0.5, 0.5)
        )
        audio_tab = DirectTab(
            parent=self.notebook,
            relief=None,
            frameColor=(0.1, 0.1, 0.1, 0.9),
            frameSize=(-0.7, 0.7, -0.5, 0.5)
        )
        
        self.notebook.addPage("Graphics", graphics_tab)
        self.notebook.addPage("Controls", controls_tab)
        self.notebook.addPage("Weapon", weapon_tab)
        self.notebook.addPage("Game", game_tab)
        self.notebook.addPage("Audio", audio_tab)  # Add audio tab

        # Настройки графики
        resolution_label = DirectLabel(
            text="Resolution",
            pos=(-0.6, 0, 0.3),  # Moved more to the left
            parent=graphics_tab,
            **self.settings_style
        )

        self.resolution_menu = DirectOptionMenu(
            text="Resolution",
            scale=0.05,
            pos=(0.0, 0, 0.3),
            items=self.resolutions,
            initialitem=self.resolutions.index(self.current_resolution) if self.current_resolution in self.resolutions else 3,
            parent=graphics_tab,
            frameColor=(0.15, 0.15, 0.15, 0.9),
            relief=DGG.RIDGE,
            borderWidth=(0.02, 0.02),
            text_fg=(1, 1, 1, 1),
            highlightColor=(0.2, 0.2, 0.2, 1),
            item_frameColor=(0.15, 0.15, 0.15, 0.95),
            popupMenu_frameColor=(0.15, 0.15, 0.15, 0.95),
            command=self.update_resolution
        )
        
        # Настраиваем меню разрешений
        self.setup_resolution_menu()

        # FOV slider
        fov_label = DirectLabel(
            text="FOV",
            pos=(-0.6, 0, 0.15),
            parent=graphics_tab,
            **self.settings_style
        )

        self.fov_slider = DirectSlider(
            range=(60, 120),
            value=self.game.settings.get('fov', 90),
            pageSize=1,
            pos=(0.1, 0, 0.15),  # Moved right by 0.1
            parent=graphics_tab,
            command=self.update_fov,
            **self.slider_style
        )

        # Fullscreen checkbox
        fullscreen_label = DirectLabel(
            text="Fullscreen",
            pos=(-0.6, 0, -0.15),
            parent=graphics_tab,
            **self.settings_style
        )

        self.fullscreen_checkbox = DirectCheckButton(
            text="Enable",
            scale=0.05,
            pos=(0.2, 0, -0.15),
            command=self.toggle_fullscreen,
            parent=graphics_tab,
            frameColor=(0.15, 0.15, 0.15, 0.9),
            relief=DGG.RIDGE,
            borderWidth=(0.02, 0.02),
            text_fg=(1, 1, 1, 1)
        )
        self.fullscreen_checkbox['indicatorValue'] = self.game.settings.get('fullscreen', False)

        # Show Images checkbox
        show_images_label = DirectLabel(
            text="NSFW mode",
            pos=(-0.6, 0, 0),
            parent=graphics_tab,
            **self.settings_style
        )

        self.show_images_checkbox = DirectCheckButton(
            text="Enable",
            scale=0.05,
            pos=(0.2, 0, 0),  # Moved right by 0.2
            command=self.toggle_show_images,
            parent=graphics_tab,
            frameColor=(0.15, 0.15, 0.15, 0.9),
            relief=DGG.RIDGE,
            borderWidth=(0.02, 0.02),
            text_fg=(1, 1, 1, 1)
        )
        self.show_images_checkbox['indicatorValue'] = self.game.settings.get('show_target_images', True)

        # Настройки управления
        sensitivity_label = DirectLabel(
            text="Mouse Sensitivity",
            pos=(-0.75, 0, 0.3),  # Reduced by 0.05 from -0.8
            parent=controls_tab,
            **self.settings_style
        )

        self.sensitivity_slider = DirectSlider(
            range=(0.1, 150.0),
            value=self.current_sensitivity,
            pageSize=1.0,
            pos=(0.25, 0, 0.3),  # Reduced by 0.05 from 0.3
            parent=controls_tab,
            command=self.update_sensitivity,
            **self.slider_style
        )

        # Настройки оружия
        weapon_pos_label = DirectLabel(
            text="Weapon Position",
            pos=(-0.7, 0, 0.3),  # Moved even more to the left
            parent=weapon_tab,
            **self.settings_style
        )

        # X position
        x_label = DirectLabel(
            text="X Position",
            pos=(-0.7, 0, 0.2),  # Moved even more to the left
            parent=weapon_tab,
            **self.settings_style
        )
        
        self.x_slider = DirectSlider(
            range=(-1.0, 1.0),
            value=self.game.settings.get('weapon_position', {}).get('x', self.game.DEFAULT_SETTINGS['weapon_position']['x']),
            pageSize=0.1,
            pos=(0.2, 0, 0.2),  # Moved more to the right
            parent=weapon_tab,
            command=self.update_x_position,
            **self.slider_style
        )

        # Y position
        y_label = DirectLabel(
            text="Y Position",
            pos=(-0.7, 0, 0.1),  # Moved even more to the left
            parent=weapon_tab,
            **self.settings_style
        )
        
        self.y_slider = DirectSlider(
            range=(-1.0, 2.0),
            value=self.game.settings.get('weapon_position', {}).get('y', self.game.DEFAULT_SETTINGS['weapon_position']['y']),
            pageSize=0.1,
            pos=(0.2, 0, 0.1),  # Moved more to the right
            parent=weapon_tab,
            command=self.update_y_position,
            **self.slider_style
        )

        # Z position
        z_label = DirectLabel(
            text="Z Position",
            pos=(-0.7, 0, 0.0),  # Moved even more to the left
            parent=weapon_tab,
            **self.settings_style
        )
        
        self.z_slider = DirectSlider(
            range=(-1.0, 1.0),
            value=self.game.settings.get('weapon_position', {}).get('z', self.game.DEFAULT_SETTINGS['weapon_position']['z']),
            pageSize=0.1,
            pos=(0.2, 0, 0.0),  # Moved more to the right
            parent=weapon_tab,
            command=self.update_z_position,
            **self.slider_style
        )

        # Reset position button
        self.reset_pos_button = DirectButton(
            text="Reset Position",
            command=self.reset_position,
            pos=(0, 0, -0.2),
            parent=weapon_tab,
            **self.button_style
        )

        # Настройки игры
        bhop_label = DirectLabel(
            text="Bunny Hop",
            pos=(-0.6, 0, 0.3),  # Moved more to the left
            parent=game_tab,
            **self.settings_style
        )

        self.bhop_checkbox = DirectCheckButton(
            text="Enable",
            scale=0.05,
            pos=(0.0, 0, 0.3),  # Adjusted position
            command=self.toggle_bhop,
            parent=game_tab,
            frameColor=(0.15, 0.15, 0.15, 0.9),
            relief=DGG.RIDGE,
            borderWidth=(0.02, 0.02),
            text_fg=(1, 1, 1, 1)
        )
        self.bhop_checkbox['indicatorValue'] = self.game.settings.get('bhop_enabled', True)

        # Recoil toggle
        recoil_label = DirectLabel(
            text="Recoil",
            pos=(-0.6, 0, 0.2),  # Moved more to the left
            parent=game_tab,
            **self.settings_style
        )

        self.recoil_checkbox = DirectCheckButton(
            text="Enable",
            scale=0.05,
            pos=(0.0, 0, 0.2),  # Adjusted position
            command=self.toggle_recoil,
            parent=game_tab,
            frameColor=(0.15, 0.15, 0.15, 0.9),
            relief=DGG.RIDGE,
            borderWidth=(0.02, 0.02),
            text_fg=(1, 1, 1, 1)
        )
        self.recoil_checkbox['indicatorValue'] = self.game.settings.get('recoil_enabled', True)

        # Spread toggle
        spread_label = DirectLabel(
            text="Spread",
            pos=(-0.6, 0, 0.1),  # Moved more to the left
            parent=game_tab,
            **self.settings_style
        )

        self.spread_checkbox = DirectCheckButton(
            text="Enable",
            scale=0.05,
            pos=(0.0, 0, 0.1),  # Adjusted position
            command=self.toggle_spread,
            parent=game_tab,
            frameColor=(0.15, 0.15, 0.15, 0.9),
            relief=DGG.RIDGE,
            borderWidth=(0.02, 0.02),
            text_fg=(1, 1, 1, 1)
        )
        self.spread_checkbox['indicatorValue'] = self.game.settings.get('spread_enabled', True)

        # Target count setting
        target_count_label = DirectLabel(
            text="Target Count",
            pos=(-0.6, 0, 0),
            parent=game_tab,
            **self.settings_style
        )

        self.target_count_options = ["5", "10", "15", "20", "25", "30"]
        current_target_count = str(self.game.settings.get('target_count', 10))
        
        self.target_count_menu = DirectOptionMenu(
            text="",
            text_scale=0.05,
            scale=0.1,
            items=self.target_count_options,
            initialitem=self.target_count_options.index(current_target_count) if current_target_count in self.target_count_options else 1,
            highlightColor=(0.65, 0.65, 0.65, 1),
            parent=game_tab,
            pos=(0.0, 0, 0),
            command=self.set_target_count
        )

        # Audio Settings
        # Music Enable/Disable
        music_enabled_label = DirectLabel(
            text="Background Music",
            pos=(-0.6, 0, 0.3),
            parent=audio_tab,
            **self.settings_style
        )

        self.music_enabled_checkbox = DirectCheckButton(
            text="Enable",
            scale=0.05,
            pos=(0.2, 0, 0.3),
            command=self.toggle_music,
            parent=audio_tab,
            frameColor=(0.15, 0.15, 0.15, 0.9),
            relief=DGG.RIDGE,
            borderWidth=(0.02, 0.02),
            text_fg=(1, 1, 1, 1)
        )
        self.music_enabled_checkbox['indicatorValue'] = self.game.settings.get('audio', {}).get('music_enabled', True)

        # Volume Control
        volume_label = DirectLabel(
            text="Music Volume",
            pos=(-0.6, 0, 0.15),
            parent=audio_tab,
            **self.settings_style
        )

        self.volume_slider = DirectSlider(
            range=(0, 1.0),
            value=self.game.settings.get('audio', {}).get('music_volume', 0.5),
            pageSize=0.1,
            pos=(0.2, 0, 0.15),
            parent=audio_tab,
            command=self.update_music_volume,
            **self.slider_style
        )

        # Track Selection
        track_label = DirectLabel(
            text="Music Track",
            pos=(-0.6, 0, 0.0),
            parent=audio_tab,
            **self.settings_style
        )

        # Get list of available tracks
        self.available_tracks = self.get_available_tracks()
        current_track = self.game.settings.get('audio', {}).get('current_track', 'default_track.mp3')
        
        self.track_menu = DirectOptionMenu(
            text="Track",
            scale=0.05,
            pos=(0.2, 0, 0.0),
            items=self.available_tracks,
            initialitem=self.available_tracks.index(current_track) if current_track in self.available_tracks else 0,
            command=self.change_music_track,
            parent=audio_tab,
            frameColor=(0.15, 0.15, 0.15, 0.9),
            relief=DGG.RIDGE,
            borderWidth=(0.02, 0.02),
            text_fg=(1, 1, 1, 1)
        )

        # Кнопка "Back"
        self.back_button = DirectButton(
            text="Back",
            pos=(0, 0, -0.5),
            parent=self.settings_frame,
            command=self.toggle_settings,
            **self.button_style
        )

        # Добавляем эффекты при наведении для кнопки
        self.back_button.bind(DGG.ENTER, self.button_hover_on, [self.back_button])
        self.back_button.bind(DGG.EXIT, self.button_hover_off, [self.back_button])

    def setup_resolution_menu(self):
        if hasattr(self.resolution_menu, 'popupMenu'):
            # Настраиваем размер и позицию меню
            menu = self.resolution_menu.popupMenu
            menu['frameSize'] = (-0.5, 0.5, -0.6, 0.6)
            
            # Добавляем обработку колеса мыши для прокрутки
            def scroll_menu(up):
                if not menu.isHidden():
                    current_index = self.resolutions.index(self.current_resolution)
                    new_index = max(0, min(len(self.resolutions) - 1,
                                         current_index + (-1 if up else 1)))
                    if new_index != current_index:
                        self.current_resolution = self.resolutions[new_index]
                        self.resolution_menu.set(new_index)
                        self.update_resolution(self.current_resolution)
            
            # Привязываем обработчики событий колеса мыши
            menu.bind('wheel_up', lambda x: scroll_menu(True))
            menu.bind('wheel_down', lambda x: scroll_menu(False))

    def toggle_settings(self):
        """Переключает видимость меню настроек"""
        if not self.settings_visible:
            # Показываем настройки и скрываем главное меню
            self.settings_frame.show()
            self.frame.hide()  # Скрываем главное меню
            self.title.hide()  # Скрываем заголовок
            for button in self.menu_buttons:
                button.hide()
            self.settings_visible = True
        else:
            # Скрываем настройки и показываем главное меню
            self.settings_frame.hide()
            self.frame.show()  # Показываем главное меню
            self.title.show()  # Показываем заголовок
            for button in self.menu_buttons:
                button.show()
            self.settings_visible = False
            # Сохраняем настройки при закрытии меню
            self.game.save_settings()

    def update_sensitivity(self):
        """Обновляет чувствительность мыши и сохраняет настройки"""
        value = self.sensitivity_slider['value']
        self.game.mouse_sensitivity = value
        self.game.save_settings()  # Сохраняем настройки сразу после изменения

    def update_resolution(self, resolution):
        # Сохраняем текущее состояние полноэкранного режима
        was_fullscreen = self.game.settings.get('fullscreen', False)
        
        # Сначала выходим из полноэкранного режима
        if was_fullscreen:
            props = WindowProperties()
            props.setFullscreen(False)
            self.game.win.requestProperties(props)
        
        # Сохраняем новое разрешение
        self.game.settings['resolution'] = resolution
        self.game.settings['windowed_resolution'] = resolution
        width, height = map(int, resolution.split('x'))
        
        # Применяем новое разрешение
        props = WindowProperties()
        props.setSize(width, height)
        self.game.win.requestProperties(props)
        
        # Если был полноэкранный режим, возвращаем его
        if was_fullscreen:
            props = WindowProperties()
            props.setFullscreen(True)
            self.game.win.requestProperties(props)
        
        self.game.save_settings()

    def toggle_score(self, status):
        self.game.show_score = status
        self.game.apply_settings({'show_score': status})

    def toggle_timer(self, status):
        self.game.show_timer = status
        self.game.apply_settings({'show_timer': status})

    def toggle_show_images(self, status):
        self.game.settings['show_target_images'] = status
        self.game.save_settings()
        # Обновляем видимость всех существующих манекенов
        if hasattr(self.game, 'targets'):
            for target in self.game.targets:
                target.update_visibility()

    def toggle_bhop(self, status):
        self.game.settings['bhop_enabled'] = status
        self.game.save_settings()

    def update_fov(self):
        new_fov = int(self.fov_slider['value'])
        self.game.settings['fov'] = new_fov
        self.game.save_settings()  # Сохраняем настройки
        base.camLens.setFov(new_fov)  # Применяем новый FOV
        
    def update_x_position(self):
        """Обновляет X позицию оружия"""
        if 'weapon_position' not in self.game.settings:
            self.game.settings['weapon_position'] = self.game.DEFAULT_SETTINGS['weapon_position'].copy()
        
        self.game.settings['weapon_position']['x'] = self.x_slider['value']
        messenger.send('update_weapon_position')
        self.game.save_settings()

    def update_y_position(self):
        """Обновляет Y позицию оружия"""
        if 'weapon_position' not in self.game.settings:
            self.game.settings['weapon_position'] = self.game.DEFAULT_SETTINGS['weapon_position'].copy()
        
        self.game.settings['weapon_position']['y'] = self.y_slider['value']
        messenger.send('update_weapon_position')
        self.game.save_settings()

    def update_z_position(self):
        """Обновляет Z позицию оружия"""
        if 'weapon_position' not in self.game.settings:
            self.game.settings['weapon_position'] = self.game.DEFAULT_SETTINGS['weapon_position'].copy()
        
        self.game.settings['weapon_position']['z'] = self.z_slider['value']
        messenger.send('update_weapon_position')
        self.game.save_settings()

    def reset_position(self):
        """Сбрасывает позицию оружия на значения по умолчанию"""
        self.game.settings['weapon_position'] = self.game.DEFAULT_SETTINGS['weapon_position'].copy()
        
        # Update sliders
        self.x_slider['value'] = self.game.settings['weapon_position']['x']
        self.y_slider['value'] = self.game.settings['weapon_position']['y']
        self.z_slider['value'] = self.game.settings['weapon_position']['z']
        
        messenger.send('update_weapon_position')
        self.game.save_settings()
        
    def button_hover_start(self, button, event):
        # Увеличиваем кнопку при наведении
        original_scale = float(button.getTag('original_scale'))
        Sequence(
            LerpScaleInterval(button, 0.1, original_scale * 1.2)
        ).start()
        
    def button_hover_end(self, button, event):
        # Возвращаем оригинальный размер кнопки
        original_scale = float(button.getTag('original_scale'))
        Sequence(
            LerpScaleInterval(button, 0.1, original_scale)
        ).start()
        
    def show(self):
        self.frame.show()
        # Показываем курсор мыши в меню
        props = WindowProperties()
        props.setCursorHidden(False)
        self.game.win.requestProperties(props)
        
        # Анимация появления меню
        Sequence(
            LerpPosInterval(self.frame, 0.5, (0, 0, 0), (0, 0, 2), blendType='easeOut')
        ).start()
        
    def hide(self):
        # Анимация исчезновения меню
        hide_sequence = Sequence(
            LerpPosInterval(self.frame, 0.3, (0, 0, -2), (0, 0, 0), blendType='easeIn'),
            Wait(0.3)  # Ждем окончания анимации
        )
        hide_sequence.start()
        
        # Останавливаем анимацию заголовка
        self.title_animation.pause()
        
    def start_game(self):
        self.hide()
        # Запускаем игру после окончания анимации
        taskMgr.doMethodLater(0.3, self._start_game_delayed, 'start_game_delayed')
        
    def _start_game_delayed(self, task):
        self.frame.hide()
        self.game.start_game()
        return task.done
        
    def exit_game(self):
        self.game.userExit()
        
    def cleanup(self):
        if self.frame:
            # Останавливаем все анимации
            self.title_animation.pause()
            self.frame.destroy()
            
    def get_available_tracks(self):
        """Get list of available music tracks"""
        try:
            # Сначала пробуем найти файлы в папке music
            music_dir = "music"
            if os.path.exists(music_dir):
                tracks = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
                if tracks:
                    return tracks

            # Если папки нет или она пуста, возвращаем список доступных треков
            return ['default_track1.mp3', 'default_track2.mp3', 'xz_ 111.mp3']
        except Exception as e:
            print(f"Error getting music tracks: {e}")
            return ['default_track1.mp3']  # Возвращаем хотя бы один трек

    def toggle_music(self, enabled):
        """Toggle background music"""
        self.game.toggle_music(enabled)

    def update_music_volume(self):
        """Update music volume"""
        volume = self.volume_slider['value']
        self.game.update_music_volume(volume)

    def change_music_track(self, track_name):
        """Change the current music track"""
        self.game.change_music_track(track_name)

    def toggle_recoil(self, status):
        """Включает/выключает отдачу"""
        self.game.settings['recoil_enabled'] = status

    def toggle_spread(self, status):
        """Включает/выключает разброс"""
        self.game.settings['spread_enabled'] = status
        self.game.save_settings()

    def set_target_count(self, count):
        """Установка количества манекенов"""
        self.game.settings['target_count'] = int(count)
        self.game.save_settings()

    def toggle_fullscreen(self, status):
        self.game.settings['fullscreen'] = status
        props = WindowProperties()
        
        if status:
            # Сохраняем текущее разрешение перед включением полноэкранного режима
            self.game.settings['windowed_resolution'] = self.game.settings['resolution']
            props.setFullscreen(True)
        else:
            # Возвращаемся к оконному режиму с предыдущим разрешением
            props.setFullscreen(False)
            width, height = map(int, self.game.settings.get('windowed_resolution', '1280x720').split('x'))
            props.setSize(width, height)
        
        self.game.win.requestProperties(props)
        self.game.save_settings()

class DirectTab(DirectFrame):
    def __init__(self, parent=None, **kw):
        # Set default options
        optiondefs = (
            ('relief', None, None),
            ('frameColor', (0.1, 0.1, 0.1, 0.9), None),
            ('frameSize', (-0.7, 0.7, -0.5, 0.5), None),
            ('borderWidth', (0, 0), None)
        )
        # Update options with user-provided values
        self.defineoptions(kw, optiondefs)
        
        # Initialize the parent class
        DirectFrame.__init__(self, parent)
        
        # Initialize options
        self.initialiseoptions(DirectTab)

class DirectNotebook(DirectFrame):
    def __init__(self, parent=None, **kw):
        # Set default options
        optiondefs = (
            ('relief', DGG.SUNKEN, None),
            ('frameColor', (0.1, 0.1, 0.1, 0.9), None),
            ('frameSize', (-0.7, 0.7, -0.5, 0.5), None),
            ('borderWidth', (0.02, 0.02), None)
        )
        # Update options with user-provided values
        self.defineoptions(kw, optiondefs)
        
        # Initialize the parent class
        DirectFrame.__init__(self, parent)
        
        # Initialize options
        self.initialiseoptions(DirectNotebook)
        
        # Initialize lists for tabs and pages
        self.tabs = []
        self.pages = []
        self.current_page = None
        
        # Create frame for tab buttons at the top
        self.tab_frame = DirectFrame(
            parent=self,
            pos=(0, 0, self['frameSize'][3]),
            frameSize=(self['frameSize'][0], self['frameSize'][1], 0, 0.1),
            frameColor=(0.15, 0.15, 0.15, 0.9)
        )
        
    def addPage(self, text, page):
        """Add a new page with a tab button"""
        index = len(self.tabs)
        tab_width = 0.28  # Increased width for tab buttons
        
        # Create tab button with adjusted starting position (moved left)
        tab = DirectButton(
            parent=self.tab_frame,
            text=text,
            text_scale=0.05,
            text_fg=(1, 1, 1, 1),
            frameSize=(-tab_width/2, tab_width/2, -0.05, 0.05),
            pos=(index * tab_width - self['frameSize'][1]/2 + tab_width/2 - 0.4, 0, 0),  # Increased left offset to 0.4
            command=self.selectPage,
            extraArgs=[index],
            relief=DGG.RAISED,
            frameColor=(0.2, 0.2, 0.2, 0.9) if not self.tabs else (0.15, 0.15, 0.15, 0.9)
        )
        
        # Add tab and page to lists
        self.tabs.append(tab)
        self.pages.append(page)
        
        # Reparent the page to the notebook
        page.reparentTo(self)
        
        # Show first page by default
        if not self.current_page:
            page.show()
            self.current_page = page
        else:
            page.hide()
            
    def selectPage(self, index):
        """Switch to the selected tab/page"""
        # Hide current page
        if self.current_page:
            self.current_page.hide()
        
        # Update tab colors
        for i, tab in enumerate(self.tabs):
            if i == index:
                tab['frameColor'] = (0.2, 0.2, 0.2, 0.9)
            else:
                tab['frameColor'] = (0.15, 0.15, 0.15, 0.9)
        
        # Show selected page
        self.pages[index].show()
        self.current_page = self.pages[index]
