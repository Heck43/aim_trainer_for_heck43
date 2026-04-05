from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel, DGG
from panda3d.core import TextNode, WindowProperties
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpScaleInterval, LerpColorScaleInterval, Func
from menu_system.ui_helpers import get_resolution_ui_scale

class PauseMenu:
    def __init__(self, game):
        self.game = game
        self.is_paused = False
        self.frame = None
        self.buttons = []
        self.ui_root = self.game.aspect2d.attachNewNode("pause_menu_ui_root")
        
        self.create_menu()
        self.update_layout()

    def update_layout(self):
        if not self.ui_root or self.ui_root.isEmpty():
            return
        self.ui_root.setScale(get_resolution_ui_scale(self.game))
        
    def create_menu(self):
        """Создает меню паузы"""
        self.dark_bg = DirectFrame(
            frameColor=(0.05, 0.05, 0.05, 0.85),
            frameSize=(-2, 2, -2, 2),
            relief=DGG.FLAT,
            parent=self.game.render2d
        )
        self.dark_bg.hide()
        
        self.frame = DirectFrame(
            frameColor=(0.08, 0.08, 0.12, 0.98),
            frameSize=(-0.5, 0.5, -0.4, 0.4),
            relief=DGG.FLAT,
            borderWidth=(0.005, 0.005),
            pos=(0, 0, 0),
            parent=self.ui_root
        )
        self.frame.hide()
        
        self.top_line = DirectFrame(
            frameColor=(0.3, 0.5, 1, 0.8),
            frameSize=(-0.45, 0.45, -0.002, 0.002),
            relief=DGG.FLAT,
            pos=(0, 0, 0.38),
            parent=self.frame
        )
        
        self.bottom_line = DirectFrame(
            frameColor=(0.3, 0.5, 1, 0.8),
            frameSize=(-0.45, 0.45, -0.002, 0.002),
            relief=DGG.FLAT,
            pos=(0, 0, -0.38),
            parent=self.frame
        )
        
        self.title = DirectLabel(
            text="PAUSED",
            scale=0.1,
            pos=(0, 0, 0.25),
            parent=self.frame,
            text_fg=(0.9, 0.95, 1, 1),
            text_align=TextNode.ACenter,
            text_shadow=(0.2, 0.4, 0.8, 0.8),
            text_shadowOffset=(0.003, -0.003),
            frameColor=(0, 0, 0, 0)
        )
        
        button_style = {
            'relief': DGG.FLAT,
            'borderWidth': (0, 0),
            'frameSize': (-0.25, 0.25, -0.04, 0.04),
            'text_scale': 0.045,
            'text_fg': (0.95, 0.95, 0.95, 1),
            'pressEffect': 0
        }
        
        self.resume_button = DirectButton(
            text="RESUME",
            command=self.hide,
            pos=(0, 0, 0.08),
            parent=self.frame,
            frameColor=(0.2, 0.4, 0.9, 0.9),
            **button_style
        )
        self.buttons.append(self.resume_button)
        
        self.settings_button = DirectButton(
            text="SETTINGS",
            command=self.show_settings,
            pos=(0, 0, -0.05),
            parent=self.frame,
            frameColor=(0.15, 0.15, 0.2, 0.9),
            **button_style
        )
        self.buttons.append(self.settings_button)
        
        self.menu_button = DirectButton(
            text="MAIN MENU",
            command=self.return_to_menu,
            pos=(0, 0, -0.18),
            parent=self.frame,
            frameColor=(0.15, 0.15, 0.2, 0.9),
            **button_style
        )
        self.buttons.append(self.menu_button)
        
        for button in self.buttons:
            button.bind(DGG.ENTER, self.button_hover_start, [button])
            button.bind(DGG.EXIT, self.button_hover_end, [button])
    
    def button_hover_start(self, button, event):
        """Эффект при наведении на кнопку"""
        Parallel(
            LerpColorScaleInterval(button, 0.2, (1.2, 1.2, 1.2, 1), blendType='easeOut'),
            LerpScaleInterval(button, 0.2, 1.08, blendType='easeOut')
        ).start()
        
        if button == self.resume_button:
            button['frameColor'] = (0.3, 0.5, 1, 1)
        else:
            button['frameColor'] = (0.25, 0.3, 0.4, 1)
    
    def button_hover_end(self, button, event):
        """Эффект при отведении курсора от кнопки"""
        Parallel(
            LerpColorScaleInterval(button, 0.2, (1, 1, 1, 1), blendType='easeOut'),
            LerpScaleInterval(button, 0.2, 1.0, blendType='easeOut')
        ).start()
        
        if button == self.resume_button:
            button['frameColor'] = (0.2, 0.4, 0.9, 0.9)
        else:
            button['frameColor'] = (0.15, 0.15, 0.2, 0.9)
    
    def show(self):
        """Показывает меню паузы"""
        self.is_paused = True
        self.update_layout()
        self.dark_bg.show()
        self.frame.show()
        
        props = WindowProperties()
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
        self.game.win.requestProperties(props)
        
        self.frame.setColorScale(1, 1, 1, 0)
        self.dark_bg.setColorScale(1, 1, 1, 0)
        Parallel(
            LerpColorScaleInterval(self.frame, 0.3, (1, 1, 1, 1)),
            LerpColorScaleInterval(self.dark_bg, 0.3, (1, 1, 1, 1))
        ).start()
    
    def hide(self):
        """Скрывает меню паузы"""
        self.is_paused = False
        
        hide_sequence = Sequence(
            Parallel(
                LerpColorScaleInterval(self.frame, 0.2, (1, 1, 1, 0)),
                LerpColorScaleInterval(self.dark_bg, 0.2, (1, 1, 1, 0))
            ),
            Func(self.frame.hide),
            Func(self.dark_bg.hide),
            Func(self.restore_game_controls)
        )
        hide_sequence.start()
    
    def restore_game_controls(self):
        """Восстанавливает игровые контролы"""
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)
        self.game.win.requestProperties(props)
    
    def show_settings(self):
        """Открывает настройки из паузы"""
        self.frame.hide()
        self.dark_bg.hide()
        
        if hasattr(self.game, 'menu') and self.game.menu:
            self.game.menu.update_layout()
            self.game.menu.settings_frame.show()
            self.game.menu.settings_visible = True
    
    def return_to_menu(self):
        """Возвращает в главное меню"""
        self.is_paused = False
        self.frame.hide()
        self.dark_bg.hide()
        self.game.return_to_menu()
    
    def cleanup(self):
        """Очищает ресурсы меню паузы"""
        if self.frame:
            self.frame.destroy()
        if self.dark_bg:
            self.dark_bg.destroy()
        if self.ui_root and not self.ui_root.isEmpty():
            self.ui_root.removeNode()
