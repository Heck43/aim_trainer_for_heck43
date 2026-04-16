from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel, DGG
from panda3d.core import TextNode, WindowProperties
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpScaleInterval, LerpColorScaleInterval, Func
from menu_system.ui_helpers import get_resolution_ui_scale

# минималистичные цвета
DARK_BG = (0.11, 0.11, 0.12, 0.85)
DARKER_BG = (0.17, 0.17, 0.18, 0.98)
TEXT_PRIMARY = (0.90, 0.90, 0.91, 1.0)
TEXT_SECONDARY = (0.68, 0.68, 0.70, 1.0)
BORDER_LIGHT = (0.3, 0.3, 0.3, 0.5)
BUTTON_NORMAL = (0.2, 0.2, 0.21, 0.9)
BUTTON_HOVER = (0.25, 0.25, 0.26, 0.95)
BUTTON_PRIMARY = (1.0, 0.58, 0.0, 0.9)
BUTTON_PRIMARY_HOVER = (1.0, 0.65, 0.1, 0.95)

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
        """создаёт меню паузы в минималистичном стиле~~"""
        self.dark_bg = DirectFrame(
            frameColor=DARK_BG,
            frameSize=(-2, 2, -2, 2),
            relief=DGG.FLAT,
            parent=self.game.render2d
        )
        self.dark_bg.hide()

        self.frame = DirectFrame(
            frameColor=DARKER_BG,
            frameSize=(-0.45, 0.45, -0.35, 0.35),
            relief=DGG.FLAT,
            borderWidth=(0, 0),
            pos=(0, 0, 0),
            parent=self.ui_root
        )
        self.frame.hide()

        # заголовок
        self.title = DirectLabel(
            text="PAUSED",
            scale=0.09,
            pos=(0, 0, 0.22),
            parent=self.frame,
            text_fg=TEXT_PRIMARY,
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            relief=None
        )

        # тонкая линия под заголовком
        self.title_line = DirectFrame(
            frameColor=BORDER_LIGHT,
            frameSize=(-0.25, 0.25, -0.001, 0.001),
            relief=DGG.FLAT,
            pos=(0, 0, 0.15),
            parent=self.frame
        )

        button_style = {
            'relief': DGG.FLAT,
            'borderWidth': (0, 0),
            'frameSize': (-0.3, 0.3, -0.045, 0.045),
            'text_scale': 0.045,
            'text_fg': TEXT_PRIMARY,
            'pressEffect': 0
        }

        self.resume_button = DirectButton(
            text="RESUME",
            command=self.hide,
            pos=(0, 0, 0.05),
            parent=self.frame,
            frameColor=BUTTON_PRIMARY,
            **button_style
        )
        self.buttons.append(self.resume_button)

        self.settings_button = DirectButton(
            text="SETTINGS",
            command=self.show_settings,
            pos=(0, 0, -0.08),
            parent=self.frame,
            frameColor=BUTTON_NORMAL,
            **button_style
        )
        self.buttons.append(self.settings_button)

        self.menu_button = DirectButton(
            text="MAIN MENU",
            command=self.return_to_menu,
            pos=(0, 0, -0.21),
            parent=self.frame,
            frameColor=BUTTON_NORMAL,
            **button_style
        )
        self.buttons.append(self.menu_button)

        for button in self.buttons:
            button.bind(DGG.ENTER, self.button_hover_start, [button])
            button.bind(DGG.EXIT, self.button_hover_end, [button])
    
    def button_hover_start(self, button, event):
        """эффект при наведении~~"""
        Parallel(
            LerpColorScaleInterval(button, 0.15, (1.1, 1.1, 1.1, 1), blendType='easeOut'),
            LerpScaleInterval(button, 0.15, 1.02, blendType='easeOut')
        ).start()

        if button == self.resume_button:
            button['frameColor'] = BUTTON_PRIMARY_HOVER
        else:
            button['frameColor'] = BUTTON_HOVER

    def button_hover_end(self, button, event):
        """эффект при отведении курсора~~"""
        Parallel(
            LerpColorScaleInterval(button, 0.15, (1, 1, 1, 1), blendType='easeOut'),
            LerpScaleInterval(button, 0.15, 1.0, blendType='easeOut')
        ).start()

        if button == self.resume_button:
            button['frameColor'] = BUTTON_PRIMARY
        else:
            button['frameColor'] = BUTTON_NORMAL
    
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
