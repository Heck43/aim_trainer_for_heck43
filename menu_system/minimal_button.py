"""
минималистичная кнопка с плавными анимациями~~
"""
from direct.gui.DirectGui import DirectButton, DGG
from direct.interval.IntervalGlobal import Parallel, LerpColorScaleInterval, LerpScaleInterval
from panda3d.core import TextNode

# цвета прямо тут
TEXT_PRIMARY = (0.90, 0.90, 0.91, 1.0)
BUTTON_NORMAL = (0.2, 0.2, 0.21, 0.9)
BUTTON_HOVER = (0.25, 0.25, 0.26, 0.95)
BUTTON_PRIMARY = (1.0, 0.58, 0.0, 0.9)
BUTTON_PRIMARY_HOVER = (1.0, 0.65, 0.1, 0.95)
BUTTON_DANGER = (1.0, 0.23, 0.19, 0.9)
BUTTON_DANGER_HOVER = (1.0, 0.3, 0.25, 0.95)


class MinimalButton(DirectButton):
    def __init__(self, parent=None, text="", command=None, pos=(0, 0, 0), button_type="normal", **kwargs):
        """
        button_type: "normal", "primary", "danger"
        """
        self.button_type = button_type

        # выбираем цвета в зависимости от типа
        if button_type == "primary":
            frame_color = BUTTON_PRIMARY
            hover_color = BUTTON_PRIMARY_HOVER
            text_color = TEXT_PRIMARY
        elif button_type == "danger":
            frame_color = BUTTON_DANGER
            hover_color = BUTTON_DANGER_HOVER
            text_color = TEXT_PRIMARY
        else:
            frame_color = BUTTON_NORMAL
            hover_color = BUTTON_HOVER
            text_color = TEXT_PRIMARY

        self.normal_color = frame_color
        self.hover_color = hover_color

        # вызываем конструктор родителя с правильными параметрами
        DirectButton.__init__(
            self,
            parent=parent,
            text=text,
            command=command,
            pos=pos,
            relief=DGG.FLAT,
            borderWidth=(0.002, 0.002),
            frameSize=(-0.35, 0.35, -0.05, 0.05),
            text_scale=0.045,
            text_fg=text_color,
            text_align=TextNode.ACenter,
            frameColor=frame_color,
            pressEffect=0,
            **kwargs
        )

        # привязываем события
        self.bind(DGG.ENTER, self._on_hover_start)
        self.bind(DGG.EXIT, self._on_hover_end)

    def _on_hover_start(self, event):
        """плавная анимация при наведении~~"""
        Parallel(
            LerpColorScaleInterval(self, 0.15, (1.1, 1.1, 1.1, 1), blendType='easeOut'),
            LerpScaleInterval(self, 0.15, 1.02, blendType='easeOut')
        ).start()
        self['frameColor'] = self.hover_color

    def _on_hover_end(self, event):
        """возврат в нормальное состояние~~"""
        Parallel(
            LerpColorScaleInterval(self, 0.15, (1, 1, 1, 1), blendType='easeIn'),
            LerpScaleInterval(self, 0.15, 1.0, blendType='easeIn')
        ).start()
        self['frameColor'] = self.normal_color
